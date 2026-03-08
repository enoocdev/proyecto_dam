# Rutas WebSocket de la aplicacion de dispositivos
from django.urls import path
from .consumers import AgentConsumer, DashboardConsumer

websocket_urlpatterns = [
    # Ruta donde se conectan los agentes instalados en los equipos
    path("ws/client/", AgentConsumer.as_asgi()),

    # Ruta donde se conecta el frontend para recibir actualizaciones
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
]
