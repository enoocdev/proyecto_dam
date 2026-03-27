# Agente de monitorizacion que se instala en cada equipo

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Necesario para 
if sys.platform.startswith("linux"):
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"

        # NOTA: Si tras esto te da un error de "Access denied" o "Connection refused",
        # descomenta la siguiente linea y cambia 'tu_usuario' por el usuario de Arch Linux:
        # os.environ["XAUTHORITY"] = "/home/tu_usuario/.Xauthority"

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
    import ssl

    import websockets
    from config import load_config
    from system_info import (
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

                # Ignorar SSL estricto (Metodo a prueba de balas)
                ssl_context = None
                if url.startswith("wss://"):
                    ssl_context = ssl._create_unverified_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

                async with websockets.connect(url, ssl=ssl_context) as ws:
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

                logger.info(
                    "RECIBIDO del servidor -> type=%s  contenido=%s",
                    msg_type, json.dumps(msg, ensure_ascii=False)[:300],
                )

                if msg_type == "ping":
                    await self._send({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    })
                elif msg_type == "command":
                    await self._handle_command(msg)

            except json.JSONDecodeError:
                logger.error("Mensaje recibido NO es JSON valido: %s", str(raw)[:200])

    # Envia un heartbeat periodico al servidor con la MAC y la IP
    async def _heartbeat_loop(self):
        interval = self.config["HEARTBEAT_INTERVAL"]
        while self.running:
            await asyncio.sleep(interval)
            try:
                self._ip = get_ip_address()
                await self._send({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"mac": self._mac, "ip": self._ip},
                })
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Conexion cerrada durante heartbeat.")
                break

    # Captura y envia una captura de pantalla periodicamente
    async def _screenshot_loop(self):
        interval = self.config["SCREENSHOT_INTERVAL"]
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
                "data": {"mac": self._mac, "image": img_b64},
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
        await self._send({
            "type": "command_result",
            "data": {"command": "shutdown", "success": True, "message": "Apagado iniciado."},
        })
        await self.disconnect()

        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.Popen(["shutdown", "/s", "/t", "5"])
            elif system == "linux":
                shutdown_cmds = [
                    ["busctl", "call", "org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager", "PowerOff", "b", "true"],
                    ["systemctl", "poweroff"],
                ]
                apagado_ok = False
                for cmd in shutdown_cmds:
                    try:
                        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                        if r.returncode == 0:
                            logger.info("Apagado ejecutado con: %s", " ".join(cmd))
                            apagado_ok = True
                            break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        pass
                if not apagado_ok:
                    logger.error("No se pudo apagar el equipo.")
            elif system == "darwin": 
                subprocess.Popen(["sudo", "shutdown", "-h", "now"])
        except Exception as exc:
            logger.error("Error al ejecutar shutdown: %s", exc)

    # Serializa los datos a JSON y los envia por WebSocket
    async def _send(self, data: dict):
        if not self.ws:
            return
        payload = json.dumps(data)
        await self.ws.send(payload)
        logger.info("ENVIADO al servidor   -> type=%s  contenido=%s", data.get("type", "?"), payload[:300])

    # Avisa al servidor del apagado y cierra la conexion limpiamente
    async def disconnect(self):
        self.running = False
        if self.ws:
            try:
                await self._send({
                    "type": "shutdown_notice",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"mac": self._mac, "message": "El equipo se esta apagando."},
                })
                await self.ws.close()
                logger.info("Desconexion limpia completada.")
            except Exception as exc:
                logger.error("Error durante desconexion: %s", exc)


# Punto de entrada principal del agente
async def _main():
    client = DeviceClient()
    loop = asyncio.get_event_loop()

    def handle_signal():
        logger.info("Senal de cierre recibida.")
        asyncio.ensure_future(client.disconnect())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass 

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