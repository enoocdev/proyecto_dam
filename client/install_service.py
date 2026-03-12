#!/usr/bin/env python3
# ================================================================
# Instalador del cliente como tarea automatica del sistema
#
# Windows: Tarea Programada (Task Scheduler)
#   - Corre bajo el usuario actual (NO bajo SYSTEM)
#   - Sin NSSM, sin servicios, sin problemas de permisos
#   - Ventana de consola oculta mediante un lanzador VBS
#   - Reinicio automatico si el proceso falla
#   - Arranca instantaneamente al iniciar sesion
#
# Linux: Servicio systemd
#   - Requiere sudo
#   - Reinicio automatico si el proceso falla
# ================================================================
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# ── Constantes ─────────────────────────────────────────────────

TASK_NAME = "ProyectoDAMClient"
DISPLAY_NAME = "Proyecto DAM - Cliente de dispositivo"
DESCRIPTION = (
    "Cliente de monitorizacion de dispositivo. "
    "Reporta estado del equipo al servidor central via WebSocket."
)

CLIENT_DIR = Path(__file__).parent.resolve()
CLIENT_SCRIPT = str(CLIENT_DIR / "client.py")
CLIENT_LOG = CLIENT_DIR / "client_errors.log"

# Windows: script VBS que oculta la ventana de consola
LAUNCHER_VBS = CLIENT_DIR / "launch_client.vbs"

# Linux: systemd
SYSTEMD_SERVICE = TASK_NAME.lower()
SYSTEMD_UNIT_PATH = Path(f"/etc/systemd/system/{SYSTEMD_SERVICE}.service")
SERVICE_LOG = CLIENT_DIR / "service_wrapper.log"


# ── Utilidades comunes ─────────────────────────────────────────

def _get_python_exe() -> str:
    """Obtiene la ruta del interprete Python priorizando el venv."""
    if platform.system() == "Windows":
        venv_python = CLIENT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = CLIENT_DIR / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _ensure_venv() -> str:
    """Crea un virtualenv e instala dependencias.

    Siempre comprueba e instala dependencias aunque el venv ya exista.
    Usa 'python -m pip' en vez de llamar a pip.exe directamente, que es
    mas robusto y evita problemas con rutas o pip corrupto.
    """
    venv_dir = CLIENT_DIR / ".venv"
    if platform.system() == "Windows":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    # --- Crear venv si no existe ---
    if not venv_python.exists():
        print("  Creando entorno virtual (.venv)...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  [ERROR] No se pudo crear el venv: {result.stderr.strip()}")
            sys.exit(1)

        if not venv_python.exists():
            print(f"  [ERROR] venv creado pero no se encuentra: {venv_python}")
            sys.exit(1)

        print(f"  [OK] Entorno virtual creado: {venv_dir}")
    else:
        print(f"  [OK] Entorno virtual ya existe: {venv_dir}")

    # --- Instalar/actualizar dependencias siempre ---
    reqs = CLIENT_DIR / "requirements.txt"
    if reqs.exists():
        # Comprobar si ya estan instaladas para no repetir
        check = subprocess.run(
            [str(venv_python), "-c", "import websockets, psutil"],
            capture_output=True, text=True,
        )
        if check.returncode == 0:
            print("  [OK] Dependencias ya instaladas.")
        else:
            print("  Instalando dependencias...")
            # Usar python -m pip es mas fiable que llamar a pip.exe
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(reqs)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                print("  [ERROR] Fallo instalando dependencias:")
                print(f"    {err}")
                # Intentar actualizar pip y reintentar
                print("  Actualizando pip e intentando de nuevo...")
                subprocess.run(
                    [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                    capture_output=True, text=True,
                )
                result = subprocess.run(
                    [str(venv_python), "-m", "pip", "install", "-r", str(reqs)],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    print(f"  [ERROR] Sigue fallando: {result.stderr.strip()}")
                    print()
                    print("  Instalalas manualmente:")
                    print(f"    {venv_python} -m pip install -r {reqs}")
                    sys.exit(1)
            print("  [OK] Dependencias instaladas.")
    else:
        print(f"  [WARN] No se encontro {reqs}.")

    return str(venv_python)


def _verify_python(python_exe: str):
    """Comprueba que el interprete Python arranca correctamente."""
    print("  Verificando interprete Python...")
    try:
        r = subprocess.run(
            [python_exe, "-c", "import sys; print(sys.version)"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            ver = r.stdout.strip().splitlines()[0]
            print(f"  [OK] Python {ver}")
        else:
            print(f"  [ERROR] Python fallo: {r.stderr.strip()}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"  [ERROR] No se encontro: {python_exe}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("  [WARN] Timeout verificando Python.")


def _verify_deps(python_exe: str):
    """Verifica que el interprete tiene websockets y psutil."""
    print(f"  Verificando dependencias con: {python_exe}")
    result = subprocess.run(
        [python_exe, "-c", "import websockets, psutil"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        err_lines = result.stderr.strip().splitlines()
        err_msg = err_lines[-1] if err_lines else "desconocido"
        print(f"  [ERROR] Faltan dependencias: {err_msg}")
        print(f"  Solucion: {python_exe} -m pip install websockets psutil")
        sys.exit(1)
    print("  [OK] Dependencias verificadas (websockets, psutil).")


def is_admin() -> bool:
    """Comprueba si se ejecuta con privilegios de administrador o root."""
    if platform.system() != "Windows":
        return os.geteuid() == 0
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


PYTHON_EXE = _get_python_exe()


# ── Windows: Tarea Programada (Task Scheduler) ────────────────

def _create_launcher_vbs(python_exe: str) -> Path:
    """Crea un script VBS que ejecuta el cliente sin ventana de consola.

    WshShell.Run con intWindowStyle=0 oculta la ventana completamente.
    bWaitOnReturn=True hace que el VBS espere a que termine el proceso,
    permitiendo a Task Scheduler detectar fallos y reiniciar.
    """
    content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{CLIENT_DIR}"\n'
        "cmd = Chr(34) & "
        f'"{python_exe}"'
        " & Chr(34) & "
        '" -u " & Chr(34) & '
        f'"{CLIENT_SCRIPT}"'
        " & Chr(34)\n"
        "WshShell.Run cmd, 0, True\n"
    )
    LAUNCHER_VBS.write_text(content, encoding="utf-8")
    return LAUNCHER_VBS


def _build_task_xml() -> str:
    """Genera el XML de definicion de la tarea programada.

    Configuracion clave:
    - LogonTrigger: arranca instantaneamente al iniciar sesion del usuario
    - InteractiveToken: corre en la sesion del usuario (acceso a pantalla)
    - LeastPrivilege: no necesita permisos de admin para correr
    - ExecutionTimeLimit PT0S: sin limite de tiempo (corre indefinidamente)
    - RestartOnFailure: si el proceso muere, reintenta cada 1 minuto
    - MultipleInstancesPolicy IgnoreNew: evita duplicados
    - DisallowStartIfOnBatteries false: corre aunque este con bateria
    - StartWhenAvailable: arranca si se perdio el trigger (ej: portatil dormido)
    """
    username = os.environ.get("USERNAME", "")
    domain = os.environ.get("USERDOMAIN", "")
    full_user = f"{domain}\\{username}" if domain else username

    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{DESCRIPTION}</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{full_user}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{full_user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>wscript.exe</Command>
      <Arguments>"{LAUNCHER_VBS}"</Arguments>
      <WorkingDirectory>{CLIENT_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''


def install_windows():
    """Instala el cliente como tarea programada de Windows.

    Usa Task Scheduler en vez de un servicio:
    - Corre bajo el usuario actual (NO bajo SYSTEM)
    - El usuario tiene acceso a su propia instalacion de Python
    - Funciona con Python de Microsoft Store, python.org, etc.
    - Un script VBS oculta la ventana de consola
    """
    global PYTHON_EXE

    print(f"Instalando cliente como tarea programada '{TASK_NAME}'...")
    print()

    # 1. Preparar entorno
    print("  Preparando entorno virtual...")
    PYTHON_EXE = _ensure_venv()
    _verify_python(PYTHON_EXE)
    _verify_deps(PYTHON_EXE)

    print()
    print(f"  Python: {PYTHON_EXE}")
    print(f"  Script: {CLIENT_SCRIPT}")
    print()

    # 2. Crear lanzador VBS (oculta ventana de consola)
    print("  Creando lanzador sin ventana de consola...")
    _create_launcher_vbs(PYTHON_EXE)
    print(f"  [OK] {LAUNCHER_VBS}")

    # 3. Eliminar tarea anterior si existe
    subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True, text=True,
    )

    # 4. Generar XML de la tarea y guardar temporalmente
    xml_content = _build_task_xml()
    xml_path = CLIENT_DIR / f"_{TASK_NAME}_task.xml"
    xml_path.write_text(xml_content, encoding="utf-16")

    # 5. Crear la tarea programada
    print("  Registrando tarea programada...")
    result = subprocess.run(
        ["schtasks", "/create", "/tn", TASK_NAME, "/xml", str(xml_path), "/f"],
        capture_output=True, text=True,
    )
    xml_path.unlink(missing_ok=True)

    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        print(f"  [ERROR] No se pudo crear la tarea: {err}")
        print()
        if not is_admin():
            print("  Prueba ejecutando como Administrador.")
        sys.exit(1)

    print("  [OK] Tarea programada creada.")

    # 6. Iniciar ahora
    print("  Iniciando cliente...")
    result = subprocess.run(
        ["schtasks", "/run", "/tn", TASK_NAME],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  [OK] Cliente ejecutandose en segundo plano.")
    else:
        print("  [INFO] Se iniciara en el proximo inicio de sesion.")

    print()
    print(f"  Logs del cliente -> {CLIENT_LOG}")
    print()
    print("  Comportamiento:")
    print("    - Se ejecuta sin ventana de consola.")
    print("    - Arranca automaticamente al iniciar sesion (instantaneo).")
    print("    - Si falla, se reinicia automaticamente cada 1 minuto.")
    print("    - No interfiere con el uso normal del equipo.")
    print()
    print("  Comandos utiles:")
    print(f"    schtasks /query /tn {TASK_NAME}")
    print(f"    schtasks /run   /tn {TASK_NAME}")
    print(f"    schtasks /end   /tn {TASK_NAME}")


def remove_windows():
    """Detiene y elimina la tarea programada y el lanzador VBS."""
    print(f"Eliminando tarea programada '{TASK_NAME}'...")

    # Detener si esta en ejecucion
    subprocess.run(
        ["schtasks", "/end", "/tn", TASK_NAME],
        capture_output=True, text=True,
    )
    time.sleep(1)

    # Eliminar tarea
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  [OK] Tarea eliminada.")
    else:
        err = result.stderr.strip() or result.stdout.strip()
        print(f"  [ERROR] {err}")

    # Eliminar VBS lanzador
    if LAUNCHER_VBS.exists():
        LAUNCHER_VBS.unlink()
        print(f"  [OK] Lanzador eliminado: {LAUNCHER_VBS.name}")

    print("  Desinstalacion completada.")


def status_windows():
    """Muestra el estado de la tarea programada y los logs recientes."""
    print("=" * 64)
    print(f"  Estado: {TASK_NAME}")
    print("=" * 64)

    # Consultar tarea
    print("\n[Tarea Programada]")
    result = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "list"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                print(f"  {line}")
    else:
        print(f"  La tarea '{TASK_NAME}' NO esta instalada.")

    # Logs
    print("\n[Logs recientes]")
    _show_recent_logs(CLIENT_LOG, "Client log")
    print()


# ── Linux: systemd ─────────────────────────────────────────────

def install_linux():
    """Crea e inicia un servicio systemd en Linux."""
    global PYTHON_EXE

    print(f"Instalando servicio systemd '{SYSTEMD_SERVICE}'...")
    print()

    # Preparar entorno
    print("  Preparando entorno virtual...")
    PYTHON_EXE = _ensure_venv()
    _verify_python(PYTHON_EXE)
    _verify_deps(PYTHON_EXE)

    user = os.environ.get("SUDO_USER", "root")
    group = user

    service_content = f"""[Unit]
Description={DISPLAY_NAME}
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
ExecStart={PYTHON_EXE} -u {CLIENT_SCRIPT}
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

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", SYSTEMD_SERVICE], check=True)
    subprocess.run(["systemctl", "start", SYSTEMD_SERVICE], check=True)

    print(f"  [OK] Servicio '{SYSTEMD_SERVICE}' habilitado e iniciado.")
    print()
    print(f"  Logs del wrapper -> {SERVICE_LOG}")
    print(f"  Logs del cliente -> {CLIENT_LOG}")
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
    """Muestra el estado del servicio systemd y los logs recientes."""
    print("=" * 64)
    print(f"  Estado: {SYSTEMD_SERVICE}")
    print("=" * 64)

    print("\n[Servicio systemd]")
    result = subprocess.run(
        ["systemctl", "is-active", SYSTEMD_SERVICE],
        capture_output=True, text=True,
    )
    print(f"  Estado: {result.stdout.strip()}")
    subprocess.run(["systemctl", "status", SYSTEMD_SERVICE, "--no-pager", "-l"])

    print("\n[Logs recientes]")
    _show_recent_logs(SERVICE_LOG, "Service log")
    print()
    _show_recent_logs(CLIENT_LOG, "Client log")
    print()


# ── Funciones comunes ──────────────────────────────────────────

def _show_recent_logs(log_file: Path, label: str, lines: int = 15):
    """Muestra las ultimas lineas de un fichero de log."""
    if not log_file.exists():
        print(f"  {label}: (no existe) {log_file}")
        return
    try:
        text = log_file.read_text(encoding="utf-8", errors="replace")
        all_lines = text.strip().splitlines()
        if not all_lines:
            print(f"  {label}: (vacio) {log_file}")
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
    """Ejecuta el cliente unos segundos para verificar que arranca."""
    print("Ejecutando prueba del cliente (5 segundos)...")
    print(f"  Python:  {PYTHON_EXE}")
    print(f"  Script:  {CLIENT_SCRIPT}")
    print(f"  WorkDir: {CLIENT_DIR}")
    print()

    try:
        proc = subprocess.Popen(
            [PYTHON_EXE, "-u", CLIENT_SCRIPT],
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
            print("  [!!] Sin salida. Revisa dependencias:")
            print(f"       {PYTHON_EXE} -m pip install websockets psutil")
        else:
            print(f"\n  [OK] {len(output_lines)} lineas de salida.")

        if CLIENT_LOG.exists() and CLIENT_LOG.stat().st_size > 0:
            print(f"  [OK] Log creado: {CLIENT_LOG}")
        else:
            print(f"  [!!] Log NO creado: {CLIENT_LOG}")

    except FileNotFoundError:
        print(f"  [ERROR] No se encontro: {PYTHON_EXE}")
    except Exception as e:
        print(f"  [ERROR] {e}")


# ── CLI ────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python install_service.py [install|remove|status|test]")
        print()
        print("  install  - Instala el cliente para ejecucion automatica")
        print("  remove   - Detiene y elimina la instalacion")
        print("  status   - Muestra estado y logs recientes")
        print("  test     - Ejecuta el cliente 5s para verificar")
        print()
        print(f"  Python: {PYTHON_EXE}")
        print()
        if platform.system() == "Windows":
            print("  Windows: Se instala como Tarea Programada (Task Scheduler).")
            print("           Corre bajo tu usuario, sin problemas de permisos.")
            print("           No requiere NSSM ni software adicional.")
        else:
            print("  Linux:   Se instala como servicio systemd.")
            print("           Requiere: sudo")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "test":
        test_client()
        return

    system = platform.system()

    # Linux necesita root para systemd
    if system == "Linux" and action in ("install", "remove") and not is_admin():
        print("ERROR: Necesitas sudo para gestionar servicios systemd.")
        print(f"  sudo python install_service.py {action}")
        sys.exit(1)

    actions = {
        "Windows": {
            "install": install_windows,
            "remove": remove_windows,
            "status": status_windows,
        },
        "Linux": {
            "install": install_linux,
            "remove": remove_linux,
            "status": status_linux,
        },
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
