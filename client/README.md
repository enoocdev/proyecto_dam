# Cliente de Dispositivo

Programa que se instala en cada equipo cliente y se comunica con el servidor backend vía **WebSocket**.

## Funcionalidades

| Función | Descripción |
|---|---|
| **Reporte de encendido** | Al iniciarse, envía al servidor: MAC, IP, hostname, SO, CPU, RAM y disco. |
| **Heartbeat** | Envía un latido periódico para que el servidor sepa que sigue activo. |
| **Recepción de comandos** | Escucha comandos del servidor y los ejecuta localmente. |
| **Desconexión limpia** | Notifica al servidor cuando el equipo se apaga. |

## Comandos soportados

| Comando | Descripción | Parámetros |
|---|---|---|
| `shutdown` | Apaga el equipo | `delay` (segundos, default: 0) |
| `restart` | Reinicia el equipo | `delay` (segundos, default: 0) |
| `cancel_shutdown` | Cancela apagado/reinicio programado | — |
| `lock_screen` | Bloquea la pantalla | — |
| `execute` | Ejecuta un comando del sistema | `command` (string) |
| `ping` | Comprueba que el cliente responde | — |
| `get_info` | Devuelve info actualizada del sistema | — |
| `message` | Muestra un mensaje al usuario | `text` (string) |

## Protocolo de mensajes (JSON por WebSocket)

### Cliente → Servidor

```json
// Al encender
{
    "type": "startup",
    "timestamp": "2026-02-23T10:00:00",
    "data": {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "192.168.1.50",
        "hostname": "PC-AULA1-01",
        "os": "Windows 10 (AMD64)",
        "cpu_percent": 15.2,
        "memory": {"total_gb": 8.0, "used_gb": 3.5, "percent": 43.8},
        "disk": {"total_gb": 256.0, "used_gb": 120.0, "percent": 46.9}
    }
}

// Heartbeat periódico
{
    "type": "heartbeat",
    "timestamp": "...",
    "data": {"mac": "AA:BB:CC:DD:EE:FF", "ip": "192.168.1.50"}
}

// Resultado de un comando
{
    "type": "command_result",
    "timestamp": "...",
    "data": {"status": "ok", "command": "shutdown", "result": "Apagado programado en 0s."}
}

// Notificación de apagado
{
    "type": "shutdown_notice",
    "timestamp": "...",
    "data": {"mac": "AA:BB:CC:DD:EE:FF", "message": "El equipo se está apagando."}
}
```

### Servidor → Cliente

```json
// Enviar un comando
{
    "type": "command",
    "command": "shutdown",
    "params": {"delay": 60}
}

// Ping
{
    "type": "ping"
}
```

## Instalación

```bash
cd client
pip install -r requirements.txt
```

## Uso

```bash
python client.py
```

## Configuración

Se puede configurar editando `client_config.json` o con variables de entorno:

| Variable de entorno | Configuración | Default |
|---|---|---|
| `CLIENT_SERVER_URL` | URL del backend REST | `http://127.0.0.1:8000` |
| `CLIENT_WS_URL` | URL del WebSocket | `ws://127.0.0.1:8000/ws/client/` |
| `CLIENT_HEARTBEAT_INTERVAL` | Intervalo heartbeat (seg) | `30` |
| `CLIENT_RECONNECT_DELAY` | Delay reconexión (seg) | `5` |
| `CLIENT_MAX_RECONNECT_ATTEMPTS` | Máx reintentos (0=∞) | `0` |
| `CLIENT_LOG_LEVEL` | Nivel de log | `INFO` |

## Instalar como servicio (Windows)

```bash
python install_service.py install
```

Para desinstalar:
```bash
python install_service.py remove
```

## Estructura

```
client/
├── client.py           # Cliente principal (WebSocket + lógica)
├── commands.py          # Manejadores de comandos remotos
├── config.py            # Configuración (JSON + env vars)
├── system_info.py       # Recopilación de info del sistema
├── install_service.py   # Instalador como servicio de Windows
├── requirements.txt     # Dependencias Python
└── README.md            # Esta documentación
```
