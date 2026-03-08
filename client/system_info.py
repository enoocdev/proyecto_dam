# Modulo que recopila informacion del hardware y sistema operativo
# Obtiene MAC IP hostname SO CPU RAM y disco
import logging
import platform
import socket
import uuid

import psutil

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


if __name__ == "__main__":
    import json
    info = collect_system_info()
    print(json.dumps(info, indent=2))
