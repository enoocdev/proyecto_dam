"""
Modulo para recopilar informacion del sistema:
  - Direccion MAC
  - Direccion IP
  - Hostname
  - Sistema operativo
  - CPU, memoria, disco
"""
import logging
import platform
import socket
import uuid

import psutil

logger = logging.getLogger("client.system_info")


def get_mac_address() -> str:
    """Obtiene la direccion MAC principal en formato XX:XX:XX:XX:XX:XX."""
    mac_int = uuid.getnode()
    return ":".join(
        f"{(mac_int >> (8 * (5 - i))) & 0xFF:02X}" for i in range(6)
    )


def get_ip_address() -> str:
    """Obtiene la IP local (la que usa el equipo para salir a la red)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        logger.warning("No se pudo determinar la IP local, usando 127.0.0.1")
        return "127.0.0.1"


def get_hostname() -> str:
    """Obtiene el nombre del equipo."""
    return socket.gethostname()


def get_os_info() -> str:
    """Obtiene informacion del sistema operativo."""
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


def get_cpu_usage() -> float:
    """Devuelve el porcentaje de uso de CPU (bloquea ~1 s)."""
    return psutil.cpu_percent(interval=1)


def get_memory_usage() -> dict:
    """Devuelve informacion de memoria RAM."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent": mem.percent,
    }


def get_disk_usage() -> dict:
    """Devuelve informacion del disco principal."""
    root = "C:\\" if platform.system() == "Windows" else "/"
    disk = psutil.disk_usage(root)
    return {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "percent": disk.percent,
    }


def collect_system_info() -> dict:
    """Recopila TODA la info del sistema (incluye CPU → bloquea ~1 s)."""
    return {
        "mac": get_mac_address(),
        "ip": get_ip_address(),
        "hostname": get_hostname(),
        "os": get_os_info(),
        "cpu_percent": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
    }


def collect_basic_info() -> dict:
    """Version ligera: solo mac, ip y hostname (sin bloqueo)."""
    return {
        "mac": get_mac_address(),
        "ip": get_ip_address(),
        "hostname": get_hostname(),
    }


if __name__ == "__main__":
    import json
    info = collect_system_info()
    print(json.dumps(info, indent=2))
