"""
Script para instalar/desinstalar el cliente como servicio del sistema.

Uso:
    python install_service.py install   -> Instala y arranca el servicio
    python install_service.py remove    -> Detiene y elimina el servicio
    python install_service.py status    -> Muestra el estado del servicio y logs recientes
    python install_service.py test      -> Prueba que el cliente arranque correctamente

Soporta:
  - Windows: Servicio nativo del SO (pywin32) — se ejecuta en segundo plano
             sin ventana de consola.
  - Linux:   Servicio systemd — se ejecuta como daemon del sistema.
"""
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

SERVICE_NAME = "ProyectoDAMClient"
SERVICE_DISPLAY = "Proyecto DAM - Cliente de dispositivo"
CLIENT_DIR = Path(__file__).parent.resolve()
CLIENT_SCRIPT = str(CLIENT_DIR / "client.py")
SERVICE_LOG = CLIENT_DIR / "service_wrapper.log"
CLIENT_LOG = CLIENT_DIR / "client_errors.log"
WINDOWS_SERVICE_SCRIPT = str(CLIENT_DIR / "windows_service.py")

# Nombre del servicio systemd (minusculas)
SYSTEMD_SERVICE = SERVICE_NAME.lower()
SYSTEMD_UNIT_PATH = Path(f"/etc/systemd/system/{SYSTEMD_SERVICE}.service")


def _get_python_exe() -> str:
    """
    Devuelve la ruta del interprete Python a usar.
    Prioridad:
      1. .venv dentro del directorio del cliente (recomendado)
      2. sys.executable (el Python con el que se ejecuto este script)
    """
    # Buscar venv del cliente
    if platform.system() == "Windows":
        venv_python = CLIENT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = CLIENT_DIR / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)

    return sys.executable


PYTHON_EXE = _get_python_exe()


def is_admin() -> bool:
    """Comprueba si se ejecuta con privilegios de administrador/root."""
    if platform.system() != "Windows":
        return os.geteuid() == 0
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


# ─── Windows: Servicio nativo con pywin32 ────────────────────────────────────

def _check_pywin32():
    """Verifica que pywin32 esta instalado."""
    try:
        import win32serviceutil  # noqa: F401
        return True
    except ImportError:
        print("ERROR: pywin32 no esta instalado.")
        print(f"  {PYTHON_EXE} -m pip install pywin32")
        print(f"  {PYTHON_EXE} -m pywin32_postinstall -install")
        return False


def install_windows():
    """Instala el cliente como servicio nativo de Windows (sin ventana de consola)."""
    if not _check_pywin32():
        sys.exit(1)

    print(f"Instalando servicio nativo '{SERVICE_NAME}'...")

    # Instalar el servicio usando windows_service.py
    result = subprocess.run(
        [PYTHON_EXE, WINDOWS_SERVICE_SCRIPT, "install"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error al instalar el servicio: {result.stderr}")
        sys.exit(1)

    # Configurar inicio automatico
    subprocess.run(
        [PYTHON_EXE, WINDOWS_SERVICE_SCRIPT, "--startup", "auto", "update"],
        capture_output=True, text=True,
    )

    # Iniciar el servicio
    result = subprocess.run(
        [PYTHON_EXE, WINDOWS_SERVICE_SCRIPT, "start"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  Servicio instalado e iniciado correctamente.")
    else:
        print(f"  Servicio instalado. Inicio: {result.stderr.strip() or result.stdout.strip()}")

    print(f"  Logs del wrapper  -> {SERVICE_LOG}")
    print(f"  Logs del cliente  -> {CLIENT_LOG}")
    print()
    print("  El servicio se ejecuta en segundo plano sin ventana de consola.")
    print("  Se iniciara automaticamente al encender el equipo.")


def remove_windows():
    """Detiene y elimina el servicio nativo de Windows."""
    if not _check_pywin32():
        sys.exit(1)

    print(f"Eliminando servicio '{SERVICE_NAME}'...")

    # Detener
    subprocess.run(
        [PYTHON_EXE, WINDOWS_SERVICE_SCRIPT, "stop"],
        capture_output=True, text=True,
    )
    time.sleep(2)

    # Eliminar
    result = subprocess.run(
        [PYTHON_EXE, WINDOWS_SERVICE_SCRIPT, "remove"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode == 0:
        print("  Servicio eliminado correctamente.")
    else:
        print(f"  Error: {result.stderr}")


def status_windows():
    """Muestra el estado del servicio de Windows y logs recientes."""
    print("=" * 64)
    print(f"  Estado del servicio: {SERVICE_NAME}")
    print("=" * 64)

    # Estado del servicio via sc query
    print("\n[Servicio de Windows]")
    result = subprocess.run(
        ["sc", "query", SERVICE_NAME],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                print(f"  {line}")
    else:
        print(f"  El servicio '{SERVICE_NAME}' NO esta instalado.")

    # Logs recientes
    print("\n[Logs recientes]")
    _show_recent_logs(SERVICE_LOG, "Wrapper log (errores de arranque)")
    print()
    _show_recent_logs(CLIENT_LOG, "Client log (actividad del cliente)")
    print()


# ─── Linux: Servicio systemd ─────────────────────────────────────────────────

def _verify_python_deps():
    """Verifica que el Python seleccionado tiene websockets y psutil instalados."""
    print(f"  Verificando dependencias con: {PYTHON_EXE}")
    result = subprocess.run(
        [PYTHON_EXE, "-c", "import websockets, psutil"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("  [ERROR] El interprete Python NO tiene las dependencias instaladas.")
        print(f"          Python: {PYTHON_EXE}")
        print(f"          Error:  {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'desconocido'}")
        print()
        print("  Solucion: Crea un virtualenv e instala las dependencias:")
        print(f"    cd {CLIENT_DIR}")
        print(f"    python3 -m venv .venv")
        print(f"    .venv/bin/pip install -r requirements.txt")
        print()
        print("  Luego vuelve a ejecutar este script.")
        sys.exit(1)
    print("  [OK] Dependencias verificadas (websockets, psutil).")


def install_linux():
    """Crea e inicia un servicio systemd en Linux."""
    print(f"Instalando servicio systemd '{SYSTEMD_SERVICE}'...")

    # Determinar el usuario que ejecuta el script
    user = os.environ.get("SUDO_USER", "root")
    group = user

    # Verificar que el Python elegido tiene las dependencias
    _verify_python_deps()

    service_content = f"""[Unit]
Description={SERVICE_DISPLAY}
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
ExecStart={PYTHON_EXE} {CLIENT_SCRIPT}
Restart=on-failure
RestartSec=15
WorkingDirectory={CLIENT_DIR}
StandardOutput=append:{SERVICE_LOG}
StandardError=append:{SERVICE_LOG}
User={user}
Group={group}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    SYSTEMD_UNIT_PATH.write_text(service_content, encoding="utf-8")
    print(f"  Unidad systemd creada: {SYSTEMD_UNIT_PATH}")

    # Recargar, habilitar e iniciar
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", SYSTEMD_SERVICE], check=True)
    subprocess.run(["systemctl", "start", SYSTEMD_SERVICE], check=True)

    print(f"  Servicio '{SYSTEMD_SERVICE}' habilitado e iniciado.")
    print(f"  Logs del wrapper  -> {SERVICE_LOG}")
    print(f"  Logs del cliente  -> {CLIENT_LOG}")
    print()
    print("  Comandos utiles:")
    print(f"    sudo systemctl status  {SYSTEMD_SERVICE}")
    print(f"    sudo systemctl stop    {SYSTEMD_SERVICE}")
    print(f"    sudo systemctl restart {SYSTEMD_SERVICE}")
    print(f"    sudo journalctl -u {SYSTEMD_SERVICE} -f")


def remove_linux():
    """Detiene y elimina el servicio systemd en Linux."""
    print(f"Eliminando servicio '{SYSTEMD_SERVICE}'...")

    subprocess.run(["systemctl", "stop", SYSTEMD_SERVICE], capture_output=True)
    subprocess.run(["systemctl", "disable", SYSTEMD_SERVICE], capture_output=True)

    if SYSTEMD_UNIT_PATH.exists():
        SYSTEMD_UNIT_PATH.unlink()
        print(f"  Unidad eliminada: {SYSTEMD_UNIT_PATH}")

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    print("  Servicio eliminado correctamente.")


def status_linux():
    """Muestra el estado del servicio systemd y logs recientes."""
    print("=" * 64)
    print(f"  Estado del servicio: {SYSTEMD_SERVICE}")
    print("=" * 64)

    # Estado de systemd
    print("\n[Servicio systemd]")
    result = subprocess.run(
        ["systemctl", "is-active", SYSTEMD_SERVICE],
        capture_output=True, text=True,
    )
    state = result.stdout.strip()
    print(f"  Estado: {state}")

    subprocess.run(["systemctl", "status", SYSTEMD_SERVICE, "--no-pager", "-l"])

    # Logs recientes
    print("\n[Logs recientes]")
    _show_recent_logs(SERVICE_LOG, "Wrapper log")
    print()
    _show_recent_logs(CLIENT_LOG, "Client log (actividad del cliente)")
    print()


# ─── Comunes ─────────────────────────────────────────────────────────────────

def _show_recent_logs(log_file: Path, label: str, lines: int = 15):
    """Muestra las ultimas N lineas de un fichero de log."""
    if not log_file.exists():
        print(f"  {label}: (no existe) {log_file}")
        return
    try:
        text = log_file.read_text(encoding="utf-8", errors="replace")
        all_lines = text.strip().splitlines()
        if not all_lines:
            print(f"  {label}: (archivo vacio) {log_file}")
            return
        tail = all_lines[-lines:]
        print(f"  {label} (ultimas {len(tail)} lineas de {log_file}):")
        print("  " + "-" * 60)
        for line in tail:
            print(f"    {line}")
        print("  " + "-" * 60)
    except OSError as e:
        print(f"  {label}: error al leer: {e}")


def test_client():
    """
    Ejecuta client.py durante unos segundos para verificar que arranca
    correctamente (imports, config, conexion...). Util para diagnosticar
    antes de instalar como servicio.
    """
    print("Ejecutando prueba del cliente (5 segundos)...")
    print(f"  Python:  {PYTHON_EXE}")
    print(f"  Script:  {CLIENT_SCRIPT}")
    print(f"  WorkDir: {CLIENT_DIR}")
    print()

    try:
        proc = subprocess.Popen(
            [PYTHON_EXE, CLIENT_SCRIPT],
            cwd=str(CLIENT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        import threading
        output_lines = []

        def reader():
            for line in proc.stdout:
                output_lines.append(line.rstrip())
                print(f"  | {line.rstrip()}")

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        t.join(timeout=5)

        proc.terminate()
        proc.wait(timeout=3)

        if not output_lines:
            print("  [!!] El cliente no produjo ninguna salida.")
            print("       Posible error silencioso. Revisa que websockets y psutil esten instalados:")
            print(f"       {PYTHON_EXE} -m pip install websockets psutil")
        else:
            print(f"\n  [OK] El cliente produjo {len(output_lines)} lineas de salida.")

        if CLIENT_LOG.exists() and CLIENT_LOG.stat().st_size > 0:
            print(f"  [OK] Log creado correctamente: {CLIENT_LOG}")
        else:
            print(f"  [!!] Log NO creado: {CLIENT_LOG}")

    except FileNotFoundError:
        print(f"  [ERROR] No se encontro Python: {PYTHON_EXE}")
    except Exception as e:
        print(f"  [ERROR] {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python install_service.py [install|remove|status|test]")
        print()
        print("  install  - Instala y arranca el servicio del sistema")
        print("  remove   - Detiene y elimina el servicio")
        print("  status   - Muestra estado y logs recientes")
        print("  test     - Ejecuta el cliente 5s para verificar que funciona")
        print()
        print(f"  Python detectado: {PYTHON_EXE}")
        print()
        if platform.system() == "Windows":
            print("  Windows: Se instala como servicio nativo (sin ventana de consola).")
            print("           Requiere: pip install pywin32")
        else:
            print("  Linux:   Se instala como servicio systemd.")
            print("           Requiere: sudo")
            print("           Recomendado: crear .venv con dependencias en el directorio del cliente.")
        sys.exit(1)

    action = sys.argv[1].lower()

    # 'test' no necesita privilegios de admin
    if action == "test":
        test_client()
        return

    if not is_admin():
        print("ERROR: Este script necesita permisos de administrador.")
        print("  Windows: Ejecutar como Administrador")
        print("  Linux:   sudo python install_service.py ...")
        sys.exit(1)

    system = platform.system()
    actions = {
        "Windows": {"install": install_windows, "remove": remove_windows, "status": status_windows},
        "Linux":   {"install": install_linux,   "remove": remove_linux,   "status": status_linux},
    }

    if system not in actions:
        print(f"Sistema '{system}' no soportado. Solo Windows y Linux.")
        sys.exit(1)

    handler = actions[system].get(action)
    if handler is None:
        print(f"Accion '{action}' no reconocida. Usa: install, remove, status, test")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
