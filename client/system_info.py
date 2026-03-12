# Modulo que recopila informacion del hardware y sistema operativo
# Obtiene MAC IP hostname SO CPU RAM y disco
import base64
import io
import logging
import platform
import socket
import uuid

import psutil

try:
    import mss
    from PIL import Image
    _HAS_SCREENSHOT = True
except ImportError:
    _HAS_SCREENSHOT = False

logger = logging.getLogger("client.system_info")


# Obtiene la direccion MAC principal del equipo
def get_mac_address() -> str:
    mac_int = uuid.getnode()
    return ":".join(
        f"{(mac_int >> (8 * (5 - i))) & 0xFF:02X}" for i in range(6)
    )


# Obtiene la IP local que usa el equipo para salir a la red
def get_ip_address() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        logger.warning("No se pudo determinar la IP local, usando 127.0.0.1")
        return "127.0.0.1"


# Obtiene el nombre del equipo en la red
def get_hostname() -> str:
    return socket.gethostname()


# Obtiene el nombre y version del sistema operativo
def get_os_info() -> str:
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


# Devuelve el porcentaje de uso de la CPU
def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=1)


# Devuelve informacion de la memoria RAM total usada y porcentaje
def get_memory_usage() -> dict:
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent": mem.percent,
    }


# Devuelve informacion del disco principal total usado y porcentaje
def get_disk_usage() -> dict:
    root = "C:\\" if platform.system() == "Windows" else "/"
    disk = psutil.disk_usage(root)
    return {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "percent": disk.percent,
    }


# Recopila toda la informacion del sistema incluyendo CPU que bloquea brevemente
def collect_system_info() -> dict:
    return {
        "mac": get_mac_address(),
        "ip": get_ip_address(),
        "hostname": get_hostname(),
        "os": get_os_info(),
        "cpu_percent": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
    }


# Version ligera que solo recoge MAC IP y hostname sin bloqueo
def collect_basic_info() -> dict:
    return {
        "mac": get_mac_address(),
        "ip": get_ip_address(),
        "hostname": get_hostname(),
    }


# Captura la pantalla principal y la devuelve como string base64 JPEG
# Redimensiona la imagen para reducir el peso del mensaje WebSocket
def capture_screenshot_base64(max_width: int = 800, quality: int = 50) -> str | None:
    if not _HAS_SCREENSHOT:
        logger.warning("mss o Pillow no disponibles, captura deshabilitada")
        return None
    try:
        with mss.mss() as sct:
            # Captura el monitor principal (indice 1)
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        # Redimensiona manteniendo la proporcion
        w, h = img.size
        if w > max_width:
            ratio = max_width / w
            img = img.resize((max_width, int(h * ratio)), Image.LANCZOS)

        # Codifica a JPEG en memoria y convierte a base64
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    except Exception as exc:
        logger.error("Error al capturar pantalla: %s", exc)
        return None


if __name__ == "__main__":
    import json
    info = collect_system_info()
    print(json.dumps(info, indent=2))
