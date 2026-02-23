from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This regex MUST match the URL being requested by the frontend.
    re_path(r'ws/auction/$', consumers.AuctionConsumer.as_asgi()),
    # OR if you prefer the path function:
    # path('ws/auction/', consumers.AuctionConsumer.as_asgi()),
]