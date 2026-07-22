"""
ASGI config for chatcom project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# 1. Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatcom.settings')

# 2. Initialize the Django ASGI application early.
# This must happen BEFORE importing any code that references your models/consumers.
django_asgi_app = get_asgi_application()

# 3. NOW import your Channels-specific modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from chatapp import routing

# application = ProtocolTypeRouter({
#     # Use the pre-initialized django_asgi_app here
#     "http": django_asgi_app,
    
#     "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             URLRouter(routing.websocket_urlpatterns)
#         ), 
#         ["https://chatapp-front-eight.vercel.app"]
#     )
# })


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": OriginValidator(
        AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        ),
        ["https://chatapp-front-eight.vercel.app",
         "http://localhost:5173",
         "http://127.0.0.1:5173"]
    ),
})