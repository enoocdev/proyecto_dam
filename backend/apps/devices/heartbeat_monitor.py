# Monitor de heartbeat basado en Redis keyspace notifications
# Cada agente conectado renueva una clave en Redis con TTL de 2 minutos
# Cuando la clave expira sin renovarse significa que el agente dejo de
# enviar heartbeats y se marca el dispositivo como offline
# Redis notifica la expiracion via Pub/Sub en el canal __keyevent@0__:expired
# Un hilo demonio escucha estas notificaciones y actua en consecuencia
import logging
import threading
import time
from datetime import datetime

import redis
from django.conf import settings

logger = logging.getLogger("devices.heartbeat")

# Prefijo para las claves de heartbeat en Redis
HEARTBEAT_PREFIX = "monitor:heartbeat:"

# Tiempo de vida de la clave en segundos (2 minutos)
HEARTBEAT_TTL = 120

_redis_pool = None
_monitor_started = False


# Obtiene host y puerto de Redis desde la configuracion de Channel Layers
def _get_redis_config():
    hosts = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"]
    host, port = hosts[0]
    return host, port


# Devuelve un cliente Redis reutilizando el pool de conexiones
def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        host, port = _get_redis_config()
        _redis_pool = redis.ConnectionPool(
            host=host, port=port, decode_responses=True,
        )
    return redis.Redis(connection_pool=_redis_pool)


# Establece o renueva la clave de heartbeat de un dispositivo con TTL
# Se llama desde el consumer en cada startup y heartbeat del agente
def set_heartbeat(mac: str):
    try:
        r = _get_redis()
        r.set(f"{HEARTBEAT_PREFIX}{mac}", "1", ex=HEARTBEAT_TTL)
    except Exception as e:
        logger.warning("Error al establecer heartbeat para %s: %s", mac, e)


# Elimina la clave de heartbeat cuando el agente se desconecta limpiamente
# Evita que el monitor marque offline un dispositivo que ya fue procesado
def delete_heartbeat(mac: str):
    try:
        r = _get_redis()
        r.delete(f"{HEARTBEAT_PREFIX}{mac}")
    except Exception as e:
        logger.warning("Error al eliminar heartbeat de %s: %s", mac, e)


# Convierte un modelo Device a diccionario para enviar por WebSocket
def _device_to_dict(device):
    return {
        "id": device.id,
        "mac": device.mac,
        "ip": str(device.ip),
        "hostname": device.hostname,
        "is_online": device.is_online,
        "is_internet_blocked": device.is_internet_blocked,
        "classroom_id": device.classroom_id,
        "connected_device_id": device.connected_device_id,
        "switch_port": device.switch_port,
    }


# Procesa la expiracion de una clave de heartbeat
# Marca el dispositivo como offline y notifica al dashboard
def _handle_expired_key(mac: str):
    from .models import Device
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    try:
        device = Device.objects.get(mac=mac)

        # Si ya esta offline no hace nada (evita notificaciones duplicadas)
        if not device.is_online:
            return

        device.is_online = False
        device.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "dashboard_updates",
            {
                "type": "device.status",
                "payload": {
                    "event": "offline",
                    "device": _device_to_dict(device),
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )
        logger.info("Heartbeat expirado: %s marcado como offline", mac)

    except Device.DoesNotExist:
        logger.debug("Heartbeat expirado para MAC desconocida: %s", mac)
    except Exception as e:
        logger.error("Error procesando expiracion de heartbeat %s: %s", mac, e)


# Bucle principal del listener de expiraciones de Redis
# Se suscribe al canal de eventos de claves expiradas y procesa las que
# corresponden a heartbeats reconectandose automaticamente si falla
def _listener_loop():
    while True:
        try:
            host, port = _get_redis_config()
            r = redis.Redis(host=host, port=port, decode_responses=True)

            # Activa las notificaciones de expiracion en Redis
            # Si no se puede configurar el usuario debera hacerlo en redis.conf
            try:
                r.config_set("notify-keyspace-events", "Ex")
            except redis.ResponseError:
                logger.warning(
                    "No se pudo configurar notify-keyspace-events en Redis. "
                    "Asegurate de incluir 'notify-keyspace-events Ex' en redis.conf"
                )

            pubsub = r.pubsub()
            pubsub.subscribe("__keyevent@0__:expired")
            logger.info("Monitor de heartbeat suscrito a expiraciones de Redis")

            for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                key = message.get("data", "")
                if not key.startswith(HEARTBEAT_PREFIX):
                    continue

                # Extrae la MAC del nombre de la clave expirada
                mac = key[len(HEARTBEAT_PREFIX):]
                _handle_expired_key(mac)

        except Exception as e:
            logger.error(
                "Error en monitor de heartbeat, reconectando en 5s: %s", e,
            )
            time.sleep(5)


# Inicia el monitor en un hilo demonio que se destruye con el proceso principal
# Solo se inicia una vez aunque ready() se llame varias veces
def start_monitor():
    global _monitor_started
    if _monitor_started:
        return
    _monitor_started = True

    thread = threading.Thread(
        target=_listener_loop,
        daemon=True,
        name="heartbeat-monitor",
    )
    thread.start()
    logger.info("Monitor de heartbeat iniciado")
