# Modulo de configuracion del cliente
# Fusiona valores por defecto con fichero JSON y variables de entorno
# La prioridad es variables de entorno sobre JSON sobre valores por defecto
import os
import json
from pathlib import Path

# Rutas base del fichero de configuracion
CONFIG_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = CONFIG_DIR / "client_config.json"

# Valores por defecto del agente
DEFAULTS = {
    # URL del WebSocket del backend Django Channels
    "WS_URL": "ws://127.0.0.1:8000/ws/client/",

    # Segundos entre cada heartbeat
    "HEARTBEAT_INTERVAL": 30,

    # Segundos antes de reintentar la conexion
    "RECONNECT_DELAY": 5,

    # Maximo de reintentos de conexion donde cero es infinito
    "MAX_RECONNECT_ATTEMPTS": 0,

    # Nivel de log del agente
    "LOG_LEVEL": "INFO",

    # Ruta del fichero de log
    "LOG_FILE": str(CONFIG_DIR / "client_errors.log"),

    # Segundos entre cada captura de pantalla (600 = 10 minutos)
    "SCREENSHOT_INTERVAL": 600,
}

# Mapeo de clave interna a variable de entorno
_ENV_MAP = {
    "WS_URL":                "CLIENT_WS_URL",
    "HEARTBEAT_INTERVAL":    "CLIENT_HEARTBEAT_INTERVAL",
    "RECONNECT_DELAY":       "CLIENT_RECONNECT_DELAY",
    "MAX_RECONNECT_ATTEMPTS":"CLIENT_MAX_RECONNECT_ATTEMPTS",
    "LOG_LEVEL":             "CLIENT_LOG_LEVEL",
    "LOG_FILE":              "CLIENT_LOG_FILE",
    "SCREENSHOT_INTERVAL":   "CLIENT_SCREENSHOT_INTERVAL",
}


# Carga la configuracion fusionando valores por defecto JSON y variables de entorno
def load_config() -> dict:
    config = dict(DEFAULTS)

    # Carga el fichero JSON si existe
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config.update(user_config)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] No se pudo leer {CONFIG_FILE}: {e}. Usando defaults.")

    # Sobreescribe con variables de entorno que tengan mayor prioridad
    for key, env_key in _ENV_MAP.items():
        value = os.getenv(env_key)
        if value is not None:
            default = DEFAULTS.get(key)
            if isinstance(default, int):
                config[key] = int(value)
            else:
                config[key] = value

    return config
