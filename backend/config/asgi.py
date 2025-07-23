"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup() 


from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from config.middleware import JWTAuthMiddlewareStack

from chat_app import routing as chat_routing 
from notifications import routing as notification_routing 



django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {

        "http": django_asgi_app, 

        "websocket": JWTAuthMiddlewareStack(
            URLRouter(
                chat_routing.websocket_urlpatterns+
                notification_routing.websocket_urlpatterns 
            )
        ),
    }
)