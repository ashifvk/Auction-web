from django.contrib import admin
from .models import Settings, SportsType, Team, Player, AuctionStatus
from django.utils.html import format_html


class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'get_profile_photo', 'phone_number', 'player_type',
        'base_price', 'is_sold', 'sold_to_team', 'final_price'
    )
    search_fields = ('name',)


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

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'purse_remaining')

class SettingsAdmin(admin.ModelAdmin):
    list_display = ('title', 'auction_type')

class SportsTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Settings, SettingsAdmin)
admin.site.register(SportsType, SportsTypeAdmin)
admin.site.register(AuctionStatus)
admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)
