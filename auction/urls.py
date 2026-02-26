from django.urls import path
from . import views

urlpatterns = [
    # Public view for displaying the live auction
    path('', views.audience_view, name='audience_view'),
    # Admin view for controlling the auction
    path('control/', views.admin_auction_control, name='admin_auction_control'),
    path('team/', views.team_profile, name='team_profile'),
    path('export/players/<team_id>/', views.export_players_csv,
         name='export_players_csv'),
    path('team/<int:team_id>/players/', views.team_players, name='team_players'),
    path('remove_player/<int:player_id>/', views.remove_player, name='remove_player')
]