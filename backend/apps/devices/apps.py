# Configuracion de la aplicacion de dispositivos
from django.apps import AppConfig


class DevicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.devices'

    def ready(self):
        from .heartbeat_monitor import start_monitor
        start_monitor()
