# In auction_project/asgi.py
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from auction import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(), # Standard Django handling
    "websocket": AuthMiddlewareStack( # Channels handling
        URLRouter(
            # This points to your app's specific WebSocket URL patterns
            routing.websocket_urlpatterns
        )
    ),
})