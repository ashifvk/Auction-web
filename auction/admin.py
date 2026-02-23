from django.contrib import admin
from .models import Team, Player, AuctionStatus


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'phone_number', 'player_type',
        'base_price', 'is_sold', 'sold_to_team', 'final_price'
    )


@admin.register(Team)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'purse_remaining')


admin.site.register(AuctionStatus) # For admin to manage the overall status
