# Agente de monitorizacion que se instala en cada equipo
# Se conecta al backend por WebSocket y envia informacion del sistema
# Incluye reconexion automatica y heartbeat periodico
# Registra toda la actividad en un fichero de log

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


# Fija el directorio de trabajo al del propio script
# Necesario cuando se ejecuta como tarea programada del sistema

_CLIENT_DIR = str(Path(__file__).parent.resolve())
if _CLIENT_DIR not in sys.path:
    sys.path.insert(0, _CLIENT_DIR)
os.chdir(_CLIENT_DIR)

# Log de emergencia para registrar fallos durante la carga inicial

_EMERGENCY_LOG = os.path.join(_CLIENT_DIR, "client_errors.log")

def _setup_emergency_log():
    # Configura un logging minimo antes de importar dependencias externas
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


# Importa dependencias externas y captura errores de importacion

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
        capture_screenshot_base64,
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


# Carga la configuracion y reconfigura el logger
try:
    config = load_config()
except Exception as exc:
    _boot_logger.critical("ERROR FATAL al cargar configuracion: %s", exc, exc_info=True)
    sys.exit(1)

# Reconfigura el logger con el nivel definido en la configuracion
log_path = Path(config["LOG_FILE"])
log_path.parent.mkdir(parents=True, exist_ok=True)

# Limpia los handlers del log de emergencia y reconfigura
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


# Clase principal del agente que gestiona la conexion WebSocket
# Envia la informacion del equipo al conectarse y mantiene un heartbeat
# Se reconecta automaticamente si se pierde la conexion
class DeviceClient:

    def __init__(self):
        self.config = config
        self.ws = None
        self.running = True
        self.reconnect_attempts = 0

        # Datos del equipo cacheados para evitar recalcularlos en cada heartbeat
        self._mac = get_mac_address()
        self._ip = get_ip_address()

    # Bucle principal que conecta envia startup escucha y reconecta
    async def run(self):
        while self.running:
            try:
                url = self.config["WS_URL"]
                logger.info("Conectando a %s ...", url)

                async with websockets.connect(url) as ws:
                    self.ws = ws
                    self.reconnect_attempts = 0
                    logger.info("Conexion WebSocket establecida con %s", url)

                    # Envia el reporte de encendido con la informacion del sistema
                    await self._send_startup()

                    # Ejecuta en paralelo la escucha de mensajes y el heartbeat
                    await asyncio.gather(
                        self._listen(),
                        self._heartbeat_loop(),
                        self._screenshot_loop(),
                    )

            # Manejo de errores de conexion y reconexion automatica
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

                # Detiene el cliente si alcanza el maximo de reintentos
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

    # Recopila la informacion completa del sistema y la envia al servidor
    async def _send_startup(self):
        # Ejecuta la recopilacion en un hilo aparte porque bloquea brevemente
        info = await asyncio.to_thread(collect_system_info)
        self._mac = info["mac"]
        self._ip = info["ip"]

        await self._send({
            "type": "startup",
            "timestamp": datetime.now().isoformat(),
            "data": info,
        })

    # Escucha mensajes del servidor y los registra en el log
    async def _listen(self):
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type", "desconocido")

                # Registra cada mensaje recibido en el log
                logger.info(
                    "RECIBIDO del servidor -> type=%s  contenido=%s",
                    msg_type, json.dumps(msg, ensure_ascii=False)[:300],
                )

                # Responde a pings del servidor con un pong
                if msg_type == "ping":
                    await self._send({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    })

                # Procesa comandos enviados desde el servidor
                elif msg_type == "command":
                    await self._handle_command(msg)

            except json.JSONDecodeError:
                logger.error(
                    "Mensaje recibido NO es JSON valido: %s", str(raw)[:200]
                )

    # Envia un heartbeat periodico al servidor con la MAC y la IP
    async def _heartbeat_loop(self):
        interval = self.config["HEARTBEAT_INTERVAL"]
        while self.running:
            await asyncio.sleep(interval)
            try:
                # Actualiza la IP por si ha cambiado desde el ultimo envio
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

    # Captura y envia una captura de pantalla periodicamente
    async def _screenshot_loop(self):
        interval = self.config["SCREENSHOT_INTERVAL"]
        # Espera un poco antes de la primera captura para que el sistema se estabilice
        await asyncio.sleep(min(30, interval))
        while self.running:
            try:
                await self._send_screenshot()
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Conexion cerrada durante envio de screenshot.")
                break
            except Exception as exc:
                logger.error("Error en screenshot_loop: %s", exc)
            await asyncio.sleep(interval)

    # Captura la pantalla y la envia al servidor como base64
    async def _send_screenshot(self):
        img_b64 = await asyncio.to_thread(capture_screenshot_base64)
        if img_b64:
            await self._send({
                "type": "screenshot",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "mac": self._mac,
                    "image": img_b64,
                },
            })
            logger.info("Captura de pantalla enviada (%d KB)", len(img_b64) // 1024)
        else:
            logger.debug("No se pudo capturar la pantalla.")

    # Procesa los comandos recibidos del servidor
    async def _handle_command(self, msg: dict):
        command = msg.get("command", "")
        params = msg.get("params", {})
        logger.info("Comando recibido: %s  params=%s", command, params)

        if command == "shutdown":
            await self._execute_shutdown()
        elif command == "request_screenshot":
            logger.info("Captura de pantalla solicitada por el servidor.")
            await self._send_screenshot()
        else:
            logger.warning("Comando desconocido: %s", command)
            await self._send({
                "type": "command_result",
                "data": {
                    "command": command,
                    "success": False,
                    "error": f"Comando no soportado: {command}",
                },
            })

    # Ejecuta el apagado del equipo segun el sistema operativo
    async def _execute_shutdown(self):
        import platform
        import subprocess

        logger.info("Ejecutando orden de apagado del equipo...")

        # Notifica al servidor que se va a apagar antes de ejecutar
        await self._send({
            "type": "command_result",
            "data": {
                "command": "shutdown",
                "success": True,
                "message": "Apagado iniciado.",
            },
        })

        # Envia aviso de apagado y cierra la conexion limpiamente
        await self.disconnect()

        # Determina el comando de apagado segun el SO
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.Popen(["shutdown", "/s", "/t", "5"])
            elif system == "linux":
                subprocess.Popen(["shutdown", "-h", "+0"])
            elif system == "darwin":  # macOS inecesario
                subprocess.Popen(["sudo", "shutdown", "-h", "now"])
            else:
                logger.error("Sistema operativo no soportado para apagado: %s", system)
        except Exception as exc:
            logger.error("Error al ejecutar shutdown del SO: %s", exc)

    # Serializa los datos a JSON y los envia por WebSocket
    # Registra cada envio en el log con el tipo de mensaje
    async def _send(self, data: dict):
        if not self.ws:
            return

        payload = json.dumps(data)
        await self.ws.send(payload)

        # Registra cada mensaje enviado en el log
        logger.info(
            "ENVIADO al servidor   -> type=%s  contenido=%s",
            data.get("type", "?"), payload[:300],
        )

    # Avisa al servidor del apagado y cierra la conexion limpiamente
    async def disconnect(self):
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



# Punto de entrada principal del agente
async def _main():
    client = DeviceClient()
    loop = asyncio.get_event_loop()

    # Captura senales de cierre del sistema para desconexion limpia
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
