from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html
from .models import Player, Team, AuctionStatus, Settings, SportsType

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_profile_photo', 'player_type',
                    'base_price', 'is_sold', 'sold_to_team', 'final_price']
    change_list_template = 'admin/player_changelist.html'
    change_form_template = "admin/player_change_form.html"

    fields = ['name', 'phone_number', 'photo', 'get_profile_photo', 'player_type',
              'base_price', 'is_sold', 'sold_to_team', 'final_price',
              'random_row', 'auction_round']
    readonly_fields = ['get_profile_photo', 'random_row', 'auction_round']
    search_fields = ['name',]

    def get_urls(self):
            urls = super().get_urls()
            custom = [
                path('reset-all-players/', self.admin_site.admin_view(self.reset_all_players_view),
                    name='reset_all_players'),
                path('reset-player/<int:pk>/', self.admin_site.admin_view(self.reset_player_view),
                    name='reset_player'), 
            ]
            return custom + urls
    
    def reset_all_players_view(self, request):
        """View to handle reset all players"""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can reset players.', level='error')
            return redirect('admin:auction_player_changelist')
        
        if request.method == 'POST' and request.POST.get('confirm') == 'yes':
            updated = Player.objects.all().update(
                random_row=0.0,
                auction_round=1,
                final_price=None,
                is_sold=False,
                sold_to_team=None
            )
            self.message_user(request, f'✓ All {updated} players have been reset successfully.')
            return redirect('admin:auction_player_changelist')
        
        # Show confirmation page
        return redirect('admin:auction_player_changelist')
    

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            extra_context["reset_url"] = reverse("admin:reset_player", args=[object_id])
        extra_context["user"] = request.user
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def changelist_view(self, request, extra_context=None):
        """Add custom button to changelist"""
        extra_context = extra_context or {}
        extra_context['show_reset_button'] = request.user.is_superuser
        return super().changelist_view(request, extra_context)
    
    def get_profile_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;">',
                obj.photo.url
            )
        return format_html(
            '<div style="width:50px;height:50px;background:#ccc;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#666;">N/A</div>'
        )
    get_profile_photo.short_description = 'Photo'
    get_profile_photo.allow_tags = True


    def reset_player_view(self, request, pk):
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can reset players.', level=messages.ERROR)
            return redirect('admin:auction_player_changelist')
        player = get_object_or_404(Player, pk=pk)
        print(player)
        print(request.method, request.POST)
        if request.method == 'GET':
            player.random_row = 0.0
            player.auction_round = 1
            player.final_price = None
            player.is_sold = False
            player.sold_to_team = None
            player.save()
            self.message_user(request, f'✓ {player.name} has been reset.')
            return redirect('admin:auction_player_change', player.pk)
        
        return redirect('admin:auction_player_change', player.pk)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'purse_remaining']

@admin.register(AuctionStatus)
class AuctionStatusAdmin(admin.ModelAdmin):
    list_display = ['current_player', 'current_bid_amount', 'current_bid_team', 'is_active']

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['title', 'auction_type', 'base_price', 'team_capacity']

@admin.register(SportsType)
class SportsTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
