import json
import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

from .models import Player, AuctionStatus, Settings, Team

minimum_players = 7


# --- Utility Function for Real-Time Push ---
def push_auction_update(update_type, *args):
    """Pushes data to the WebSocket group using the Channel Layer."""
    channel_layer = get_channel_layer()
    data = {}

    if update_type == 'new_player':
        player = args[0]
        data = {
            'id': player.id,
            'name': player.name,
            'type': player.get_player_type_display(),
            'base_price': str(player.base_price),
            'photo_url': player.photo.url if player.photo else '',
            'bid_amount': str(player.base_price),
            'bid_team': 'N/A',
            'is_active': True,
        }

    elif update_type == 'bid_update':
        status = args[0]
        data = {
            'max_bid_amount': str(status.current_bid_amount),
            'bid_amount': str(status.current_bid_amount),
            'bid_team': status.current_bid_team.name if status.current_bid_team else 'N/A'
        }

    elif update_type == 'player_sold':
        player, team, price = args
        data = {
            'player_name': player.name,
            'sold_to': team.name,
            'price': str(price),
            'is_active': False,
        }

    elif update_type == 'unsold':
        player = args[0]
        data = {
            'player_name': player.name,
            'is_active': False,
            'message': f"{player.name} went UNSOLD!"
        }

    async_to_sync(channel_layer.group_send)(
        'auction_updates',
        {
            'type': 'auction_update',
            'action': update_type,
            'data': data,
        }
    )


# --- Views ---
def audience_view(request):
    """The public facing view displaying the auction in real-time."""
    status = AuctionStatus.get_instance()

    current_status_data = None
    if status.current_player:
        # Prepare the current player data to initialize the page for JavaScript
        current_status_data = {
            'name': status.current_player.name,
            'type': status.current_player.get_player_type_display(),
            'base_price': str(status.current_player.base_price),
            'photo_url': status.current_player.photo.url if status.current_player.photo else '',
            'bid_amount': str(status.current_bid_amount),
            'bid_team': status.current_bid_team.name if status.current_bid_team else 'N/A',
            'is_active': status.is_active,
        }
    settings = Settings.get_instance()

    context = {
        'settings': settings,
        'current_status_json': json.dumps(current_status_data),
    }
    # Ensure your template path matches your setup (e.g., 'auction/audience_view.html')
    return render(request, 'audience_view.html', context)


def is_admin(user):
    return user.is_superuser


def team_profile(request):
    """
    Public or admin view to see team compositions.
    """
    teams = Team.objects.prefetch_related('players').all()
    return render(request, 'team_profile.html', {'teams': teams})

@user_passes_test(is_admin, login_url='/admin/login/')
def team_players(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    players = team.players.all()
    return render(request, 'team_players.html', {'team': team, 'players': players})

@user_passes_test(is_admin, login_url='/admin/login/')
def remove_player(request, player_id):
    try:
        player = get_object_or_404(Player, id=player_id)
        team = player.sold_to_team
        if team:
            team.purse_remaining += player.final_price or Decimal('0.00')
            team.save()
        player.is_sold = False
        player.sold_to_team = None
        player.final_price = None
        player.save()
        data = {
            'success': True,
            'message': f"{player.name} has been removed from {team.name} and is now available for auction again."
        }
    except Player.DoesNotExist:
        data = {
            'success': False,
            'message': "Player not found."
        }
    except Exception as e:
        data = {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }
    return JsonResponse(data)


def bid_validation(amount, bid_team):
    message = None
    is_valid = True
    if bid_team and not bid_team.can_bid(amount):
        is_valid = False
        message = f"Bid exceeds the maximum allowed for {bid_team.name} (Max: {bid_team.get_max_bid_amount()})."
    elif bid_team and not bid_team.can_acquire_player():
        is_valid = False
        message = f"Team {bid_team.name} has reached its player capacity."
    return is_valid, message


@user_passes_test(is_admin, login_url='/admin/login/')
def admin_auction_control(request):
    """Admin interface to start/control the bidding process."""
    status = AuctionStatus.get_instance()
    # Order by ID to ensure a consistent list, or order by a relevant auction sequence field
    players_unsold = Player.objects.filter(is_sold=False).order_by('id')
    teams = Team.objects.prefetch_related('players').all()
    message = None

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- START NEXT PLAYER ---
        if action == 'start_auction':
            player_id = request.POST.get('player_id')
            # Fetch the player and ensure they are unsold
            next_player = get_object_or_404(Player, id=player_id,
                                            is_sold=False)

            # Set the initial auction state
            status.current_player = next_player
            status.current_bid_amount = next_player.base_price
            status.current_bid_team = None
            status.is_active = True
            status.save()

            # Notify frontend
            push_auction_update('new_player', next_player)

        # --- REVERT BID ---
        elif action == 'revert_bid' and status.is_active:
            if status.previous_bid_amount is not None:
                status.current_bid_amount = status.previous_bid_amount
                status.current_bid_team = status.previous_bid_team
                # Clear previous after revert to prevent double revert to same state if not intended
                # Or keep it if you want to support one level of undo.
                # For now, let's just revert.
                status.save()
                push_auction_update('bid_update', status)
                message = "Bid reverted to previous bid."
            else:
                message = "No previous bid to revert to."

        # --- MANUAL EDIT BID ---
        elif action == 'manual_edit_bid' and status.is_active:
            team_id = request.POST.get('team_id')
            new_bid_amount = request.POST.get('current_bid_amount')
            
            try:
                new_bid = Decimal(new_bid_amount)
                if team_id:
                    bid_team = Team.objects.get(id=team_id)
                else:
                    bid_team = None
                is_valid, message = bid_validation(new_bid, bid_team)
                if not is_valid:
                    return render(request, 'admin_control.html', locals())
                # Save current state as previous before updating
                status.previous_bid_amount = status.current_bid_amount
                status.previous_bid_team = status.current_bid_team
                
                status.current_bid_amount = new_bid
                status.current_bid_team = bid_team
                status.save()
                push_auction_update('bid_update', status)
                message = "Bid updated manually."
            except (ValueError, Decimal.InvalidOperation):
                message = "Invalid bid amount."
            except Team.DoesNotExist:
                message = "Selected team does not exist."

        # --- UPDATE BID ---
        elif action == 'update_bid' and status.is_active:
            team_id = request.POST.get('team_id')
            bid_amount = Decimal(request.POST.get('bid_amount'))
            current_bid = status.current_bid_amount

            # Save current state as previous before updating
            status.previous_bid_amount = current_bid
            status.previous_bid_team = status.current_bid_team

            new_bid_str = current_bid + bid_amount

            try:
                new_bid = Decimal(new_bid_str)
                bid_team = Team.objects.get(id=team_id)
            except (ValueError, Team.DoesNotExist):
                message = "Invalid bid amount or team selected."
                # Assuming 'admin_control.html' is in the same directory as 'audience_view.html'
                return render(request, 'admin_control.html', locals())
            is_valid, message = bid_validation(new_bid, bid_team)
            if not is_valid:
                    return render(request, 'admin_control.html', locals())
            is_valid_bid = (
                    status.current_bid_amount < new_bid
                    <= bid_team.get_max_bid_amount()
            )
            if is_valid_bid:
                status.current_bid_amount = new_bid
                status.current_bid_team = bid_team
                status.save()
                # Notify frontend
                push_auction_update('bid_update', status)
            elif new_bid > bid_team.get_max_bid_amount():
                message = f"Bid exceeds the maximum allowed for {bid_team.name} (Max: {bid_team.get_max_bid_amount()})."
            elif bid_team.purse_remaining < new_bid:
                message = f"{bid_team.name} does not have enough purse remaining (Need: {new_bid})."
            else:
                message = "Bid must be strictly higher than the current bid."

        # --- SELL PLAYER ---
        elif action == 'sell_player' and status.current_player:
            player = status.current_player
            team = status.current_bid_team
            team_id = request.POST.get('team_id', None)
            if team:
                # team exists from the current bid
                pass
            else:
                try:
                    team = Team.objects.get(id=team_id)
                except:
                    team = None
            price = status.current_bid_amount
            if team is None:
                message = "No Team has placed a valid bid. Cannot sell player."
                return render(request, 'admin_control.html', locals())
            is_valid, message = bid_validation(price, team)
            if not is_valid:
                return render(request, 'admin_control.html', locals())
            # Finalize player sale details
            player.is_sold = True
            player.sold_to_team = team
            player.final_price = price
            player.save()

            # Deduct from team purse
            team.purse_remaining -= price
            team.save()

            # Notify frontend before clearing status
            push_auction_update('player_sold', player, team, price)

            # Clear current auction state
            status.current_player = None
            status.current_bid_amount = Decimal('0.00')
            status.current_bid_team = None
            status.is_active = False
            status.save()
            message = f"{player.name} sold to {team.name} for {price}."

            # --- UNSOLD PLAYER ---
        elif action == 'unsold_player' and status.current_player:
            player = status.current_player

            # Notify frontend before clearing status
            push_auction_update('unsold', player)

            # Clear current auction state
            status.current_player = None
            status.current_bid_amount = Decimal('0.00')
            status.current_bid_team = None
            status.is_active = False
            status.save()
            message = f"{player.name} went UNSOLD!"

    context = {
        'status': status,
        'players_unsold': players_unsold,
        'teams': teams,
        'message': message,
    }
    # Assuming 'admin_control.html' is in the same directory as 'audience_view.html'
    return render(request, 'admin_control.html', context)

@user_passes_test(is_admin)
def export_players_csv(request, team_id):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="auction_players_report.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['Name', 'Type', 'Base Price', 'Status', 'Sold To', 'Final Price'])

    # Query the data
    players = Player.objects.filter(sold_to_team__id=team_id).order_by('name')

    for player in players:
        writer.writerow([
            player.name,
            player.get_player_type_display(),
            player.base_price,
            'Sold' if player.is_sold else 'Unsold',
            player.sold_to_team.name if player.sold_to_team else 'N/A',
            player.final_price if player.final_price else '0.00',
        ])

    return response



@csrf_exempt
def salla_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process the webhook data as needed
            print("Received Salla Webhook:", data)
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON", status=400)
    else:
        return HttpResponse("Method Not Allowed", status=405)
