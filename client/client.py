"""
Agente PC  -  Cliente basico de monitorizacion.

Version inicial con las siguientes funcionalidades:
  1. Conexion asincrona al backend via WebSocket con reconexion automatica.
  2. Envio de informacion del equipo (startup) y heartbeat periodico.
  3. Logging integral a  client_errors.log  — registra CADA mensaje
     enviado y recibido con fecha, hora y nivel.

Protocolo compatible con AgentConsumer del backend Django Channels.
Ruta del WebSocket: ws://<host>/ws/client/
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


#  Fijar directorio de trabajo al de este script.
#  Critico cuando se ejecuta como tarea programada (cwd = System32).

_CLIENT_DIR = str(Path(__file__).parent.resolve())
if _CLIENT_DIR not in sys.path:
    sys.path.insert(0, _CLIENT_DIR)
os.chdir(_CLIENT_DIR)

# Log de emergencia: si algo falla en los imports de abajo, al menos
# queda registrado en el fichero de log para poder diagnosticarlo.

_EMERGENCY_LOG = os.path.join(_CLIENT_DIR, "client_errors.log")

def _setup_emergency_log():
    """Configura un logging minimo antes de importar dependencias externas."""
    log_path = Path(_EMERGENCY_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(_EMERGENCY_LOG, encoding="utf-8"),
        ],
    )

_setup_emergency_log()
_boot_logger = logging.getLogger("client.boot")
_boot_logger.info("=== Cliente iniciando (PID %d, cwd=%s) ===", os.getpid(), os.getcwd())
_boot_logger.info("Python: %s", sys.executable)


#  Importar dependencias externas con captura de errores

try:
    import asyncio
    import json
    import signal

    import websockets                    # noqa: E402
    from config import load_config       # noqa: E402
    from system_info import (            # noqa: E402
        collect_system_info,
        get_mac_address,
        get_ip_address,
    )
except ImportError as exc:
    _boot_logger.critical(
        "ERROR FATAL: No se pudo importar una dependencia: %s\n"
        "Asegurate de tener instalados los paquetes: pip install websockets psutil",
        exc,
    )
    sys.exit(1)
except Exception as exc:
    _boot_logger.critical("ERROR FATAL durante imports: %s", exc, exc_info=True)
    sys.exit(1)


#  Configuracion y logger 
try:
    config = load_config()
except Exception as exc:
    _boot_logger.critical("ERROR FATAL al cargar configuracion: %s", exc, exc_info=True)
    sys.exit(1)

# Reconfigurar el logger con el nivel del config (el fichero ya esta abierto)
log_path = Path(config["LOG_FILE"])
log_path.parent.mkdir(parents=True, exist_ok=True)

# Limpiar handlers previos del emergency log y reconfigurar
for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)

logging.basicConfig(
    level=getattr(logging, config["LOG_LEVEL"], logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config["LOG_FILE"], encoding="utf-8"),
    ],
)
logger = logging.getLogger("client")
logger.info("Configuracion cargada correctamente. Log level=%s", config["LOG_LEVEL"])


# DeviceClient

class DeviceClient:
    """
    Cliente WebSocket basico.
    Se conecta al servidor, envia la info del equipo (startup),
    mantiene un heartbeat periodico y se reconecta automaticamente.
    """

    def __init__(self):
        self.config = config
        self.ws = None
        self.running = True
        self.reconnect_attempts = 0

        # Datos del equipo (cacheados para no recalcular en cada heartbeat)
        self._mac = get_mac_address()
        self._ip = get_ip_address()

    #Bucle principal de conexion 
    async def run(self):
        """Conectar -> startup -> (listen + heartbeat) -> reconectar."""
        while self.running:
            try:
                url = self.config["WS_URL"]
                logger.info("Conectando a %s ...", url)

                async with websockets.connect(url) as ws:
                    self.ws = ws
                    self.reconnect_attempts = 0
                    logger.info("Conexion WebSocket establecida con %s", url)

                    # 1) Enviar reporte de encendido
                    await self._send_startup()

                    # 2) Escuchar mensajes del servidor + heartbeat en paralelo
                    await asyncio.gather(
                        self._listen(),
                        self._heartbeat_loop(),
                    )

            # Errores de conexion 
            except (
                websockets.exceptions.ConnectionClosed,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.InvalidStatusCode,
                ConnectionRefusedError,
                OSError,
            ) as exc:
                self.ws = None
                self.reconnect_attempts += 1
                max_att = self.config["MAX_RECONNECT_ATTEMPTS"]

                # Si hay limite de reintentos y lo alcanzamos, parar
                if max_att and self.reconnect_attempts >= max_att:
                    logger.error(
                        "Maximo de reintentos alcanzado (%d). Deteniendo cliente.",
                        max_att,
                    )
                    self.running = False
                    break

                delay = self.config["RECONNECT_DELAY"]
                logger.warning(
                    "Error de conexion: %s  |  Reintento %d en %ds...",
                    exc, self.reconnect_attempts, delay,
                )
                await asyncio.sleep(delay)

            except asyncio.CancelledError:
                logger.info("Tarea cancelada, cerrando cliente...")
                break

    # Startup: enviar info completa del equipo

    async def _send_startup(self):
        """Recopila info del sistema y la envia como mensaje 'startup'."""
        # collect_system_info bloquea ~1s (cpu_percent), lanzar en thread
        info = await asyncio.to_thread(collect_system_info)
        self._mac = info["mac"]
        self._ip = info["ip"]

        await self._send({
            "type": "startup",
            "timestamp": datetime.now().isoformat(),
            "data": info,
        })

    # Escucha de mensajes del servidor

    async def _listen(self):
        """Lee cada mensaje del servidor y lo registra en el log."""
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type", "desconocido")

                # Log de CADA mensaje recibido 
                logger.info(
                    "RECIBIDO del servidor -> type=%s  contenido=%s",
                    msg_type, json.dumps(msg, ensure_ascii=False)[:300],
                )

                # Por ahora solo respondemos a pings del servidor
                if msg_type == "ping":
                    await self._send({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    })

            except json.JSONDecodeError:
                logger.error(
                    "Mensaje recibido NO es JSON valido: %s", str(raw)[:200]
                )

    # Heartbeat periodico

    async def _heartbeat_loop(self):
        """Envia un heartbeat cada HEARTBEAT_INTERVAL segundos."""
        interval = self.config["HEARTBEAT_INTERVAL"]
        while self.running:
            await asyncio.sleep(interval)
            try:
                # Actualizar IP por si cambio
                self._ip = get_ip_address()

                await self._send({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "mac": self._mac,
                        "ip": self._ip,
                    },
                })

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Conexion cerrada durante heartbeat.")
                break

    # Envio de mensajes

    async def _send(self, data: dict):
        """
        Serializa 'data' a JSON y lo envia por WebSocket.
        Registra un log INFO con la fecha/hora y tipo de cada envio.
        """
        if not self.ws:
            return

        payload = json.dumps(data)
        await self.ws.send(payload)

        # Log de CADA mensaje enviado (requisito)
        logger.info(
            "ENVIADO al servidor   -> type=%s  contenido=%s",
            data.get("type", "?"), payload[:300],
        )

    # ── Desconexion limpia ───────────────────────────────────────────────

    async def disconnect(self):
        """Avisa al servidor de apagado y cierra la conexion."""
        self.running = False
        if self.ws:
            try:
                await self._send({
                    "type": "shutdown_notice",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "mac": self._mac,
                        "message": "El equipo se esta apagando.",
                    },
                })
                await self.ws.close()
                logger.info("Desconexion limpia completada.")
            except Exception as exc:
                logger.error("Error durante desconexion: %s", exc)



#  Punto de entrada
async def _main():
    client = DeviceClient()
    loop = asyncio.get_event_loop()

    # Intentar capturar senales de cierre para desconexion limpia
    def handle_signal():
        logger.info("Senal de cierre recibida.")
        asyncio.ensure_future(client.disconnect())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass  # Windows no soporta add_signal_handler

    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Interrupcion de teclado, cerrando...")
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logging.getLogger("client").info("Cliente detenido.")
