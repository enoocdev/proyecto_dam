# Consumers WebSocket para la aplicacion de dispositivos
# AgentConsumer recibe conexiones de los agentes instalados en los equipos
# DashboardConsumer envia actualizaciones en tiempo real al frontend React
import json
import logging
from datetime import datetime

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Device

logger = logging.getLogger("devices.consumers")

# Nombre del grupo de canales al que se suscriben los navegadores
DASHBOARD_GROUP = "dashboard_updates"


# Consumer que atiende a cada agente instalado en un equipo
# Recibe mensajes de tipo startup heartbeat shutdown y command result
class AgentConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.mac = None
        await self.accept()
        logger.info("Agente WebSocket conectado (channel=%s)", self.channel_name)

    # Recepcion de mensajes del agente

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type", "")
        data = content.get("data", {})

        if msg_type == "startup":
            await self._handle_startup(data)

        elif msg_type == "heartbeat":
            await self._handle_heartbeat(data)

        elif msg_type == "shutdown_notice":
            await self._handle_shutdown_notice(data)

        elif msg_type == "command_result":
            logger.info("Resultado de comando recibido: %s", data)

        else:
            logger.warning("Tipo de mensaje desconocido del agente: %s", msg_type)

    async def disconnect(self, close_code):
        logger.info("Agente desconectado (mac=%s, code=%s)", self.mac, close_code)
        if self.mac:
            device_data = await self._set_device_offline(self.mac)
            if device_data:
                await self._notify_dashboard("offline", device_data)

    # Handlers internos para cada tipo de mensaje

    # Procesa el mensaje de encendido del agente y lo registra como online
    async def _handle_startup(self, data: dict):
        self.mac = data.get("mac")
        device_data = await self._set_device_online(
            mac=self.mac,
            ip=data.get("ip"),
            hostname=data.get("hostname"),
        )
        await self._notify_dashboard("online", device_data)
        logger.info("Agente online: %s (%s)", self.mac, data.get("hostname"))

    # Actualiza la IP del dispositivo si ha cambiado en el heartbeat
    async def _handle_heartbeat(self, data: dict):
        mac = data.get("mac")
        if mac:
            await self._update_heartbeat(mac, data.get("ip"))

    # Procesa el aviso de apagado del agente y lo marca como offline
    async def _handle_shutdown_notice(self, data: dict):
        mac = data.get("mac")
        if mac:
            device_data = await self._set_device_offline(mac)
            if device_data:
                await self._notify_dashboard("offline", device_data)
            logger.info("Agente avisó de apagado: %s", mac)

    # Envia un comando al agente conectado por WebSocket
    async def send_command(self, command_name: str, params: dict = None):
        await self.send_json({
            "type": "command",
            "command": command_name,
            "params": params or {},
        })

    # Operaciones de base de datos convertidas de sincrono a asincrono

    @database_sync_to_async
    def _set_device_online(self, mac, ip=None, hostname=None):
        device, _ = Device.objects.get_or_create(
            mac=mac,
            defaults={
                "ip": ip or "0.0.0.0",
                "hostname": hostname or mac,
            },
        )
        if ip:
            device.ip = ip
        if hostname:
            device.hostname = hostname
        device.is_online = True
        device.save()
        return self._device_to_dict(device)

    @database_sync_to_async
    def _set_device_offline(self, mac):
        try:
            device = Device.objects.get(mac=mac)
            device.is_online = False
            device.save()
            return self._device_to_dict(device)
        except Device.DoesNotExist:
            return None

    @database_sync_to_async
    def _update_heartbeat(self, mac, ip=None):
        try:
            device = Device.objects.get(mac=mac)
            if ip and str(device.ip) != ip:
                device.ip = ip
                device.save()
        except Device.DoesNotExist:
            pass

    @staticmethod
    def _device_to_dict(device):
        return {
            "id": device.id,
            "mac": device.mac,
            "ip": str(device.ip),
            "hostname": device.hostname,
            "is_online": device.is_online,
            "is_internet_blocked": device.is_internet_blocked,
            "classroom_id": device.classroom_id,
        }

    # Notifica al grupo del dashboard sobre cambios en el estado del dispositivo

    async def _notify_dashboard(self, event: str, device_data: dict):
        await self.channel_layer.group_send(
            DASHBOARD_GROUP,
            {
                "type": "device.status",
                "payload": {
                    "event": event,
                    "device": device_data,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )


# Consumer para el frontend React
# Se suscribe al grupo del dashboard y reenvia los eventos al navegador
class DashboardConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add(DASHBOARD_GROUP, self.channel_name)
        await self.accept()
        logger.info("Dashboard conectado (channel=%s)", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(DASHBOARD_GROUP, self.channel_name)
        logger.info("Dashboard desconectado (channel=%s)", self.channel_name)

    # Recibe eventos del grupo del dashboard y los envia al navegador
    async def device_status(self, event):
        await self.send_json(event["payload"])
