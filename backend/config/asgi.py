# Configuracion ASGI del proyecto con soporte para HTTP y WebSockets

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Inicializa Django antes de importar los consumers y rutas
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.devices.routing import websocket_urlpatterns

# Enrutador que separa conexiones HTTP de WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
