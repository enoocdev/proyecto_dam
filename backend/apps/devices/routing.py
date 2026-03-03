"""
Rutas WebSocket de la app devices.
"""
from django.urls import path
from .consumers import AgentConsumer, DashboardConsumer

websocket_urlpatterns = [
    # Los agentes (client.py) se conectan aquí
    path("ws/client/", AgentConsumer.as_asgi()),

    # El frontend React se conecta aquí para recibir actualizaciones
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
]
