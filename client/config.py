"""
Configuracion del cliente (Agente PC).

Prioridad de valores (de menor a mayor):
  1. DEFAULTS definidos en este archivo.
  2. Archivo  client_config.json  (junto a este script).
  3. Variables de entorno con prefijo CLIENT_.
"""
import os
import json
from pathlib import Path

# Rutas base 
CONFIG_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = CONFIG_DIR / "client_config.json"

# Valores por defecto
DEFAULTS = {
    # URL del WebSocket del backend (Django Channels - AgentConsumer)
    "WS_URL": "ws://127.0.0.1:8000/ws/client/",

    # Intervalo en segundos entre heartbeats
    "HEARTBEAT_INTERVAL": 30,

    # Tiempo en segundos antes de reintentar la conexion WebSocket
    "RECONNECT_DELAY": 5,

    # Maximo de reintentos de conexion (0 = infinito)
    "MAX_RECONNECT_ATTEMPTS": 0,

    # Nivel de log: DEBUG, INFO, WARNING, ERROR
    "LOG_LEVEL": "INFO",

    # Ruta del archivo de log
    "LOG_FILE": str(CONFIG_DIR / "client_errors.log"),
}

# Mapa: clave interna -> variable de entorno
_ENV_MAP = {
    "WS_URL":                "CLIENT_WS_URL",
    "HEARTBEAT_INTERVAL":    "CLIENT_HEARTBEAT_INTERVAL",
    "RECONNECT_DELAY":       "CLIENT_RECONNECT_DELAY",
    "MAX_RECONNECT_ATTEMPTS":"CLIENT_MAX_RECONNECT_ATTEMPTS",
    "LOG_LEVEL":             "CLIENT_LOG_LEVEL",
    "LOG_FILE":              "CLIENT_LOG_FILE",
}


def load_config() -> dict:
    """Carga la configuracion fusionando defaults, JSON y env-vars."""
    config = dict(DEFAULTS)

    # 1) Archivo JSON (si existe)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config.update(user_config)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] No se pudo leer {CONFIG_FILE}: {e}. Usando defaults.")

    # 2) Variables de entorno (prioridad maxima)
    for key, env_key in _ENV_MAP.items():
        value = os.getenv(env_key)
        if value is not None:
            default = DEFAULTS.get(key)
            if isinstance(default, int):
                config[key] = int(value)
            else:
                config[key] = value

    return config
