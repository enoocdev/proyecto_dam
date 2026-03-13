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


def _has_pip(python_exe: str) -> bool:
    """Comprueba si pip esta disponible en el interprete dado."""
    r = subprocess.run(
        [python_exe, "-m", "pip", "--version"],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def _bootstrap_pip(venv_python: str):
    """Asegura que pip esta disponible dentro del venv.

    En muchas distribuciones Linux (Arch, Debian, Ubuntu, Fedora...)
    'python -m venv' puede crear el entorno SIN pip porque el modulo
    ensurepip no esta instalado (paquete aparte: python3-ensurepip,
    python3-venv, etc.).

    Estrategia:
      1. Comprobar si pip ya existe → nada que hacer.
      2. Intentar 'python -m ensurepip --upgrade' → rapido y sin red.
      3. Si falla, descargar get-pip.py desde internet y ejecutarlo.
      4. Si nada funciona, indicar que paquete instalar con el gestor
         de paquetes del sistema.
    """
    if _has_pip(venv_python):
        return  # pip ya existe, todo bien

    print("  [WARN] pip no esta disponible en el venv, bootstrapping...")

    # --- Intento 1: ensurepip ---
    print("  Intentando ensurepip...")
    r = subprocess.run(
        [venv_python, "-m", "ensurepip", "--upgrade"],
        capture_output=True, text=True,
    )
    if r.returncode == 0 and _has_pip(venv_python):
        print("  [OK] pip instalado via ensurepip.")
        return

    # --- Intento 2: descargar get-pip.py ---
    print("  ensurepip no disponible. Descargando get-pip.py...")
    get_pip_path = CLIENT_DIR / "_get-pip.py"
    try:
        import urllib.request
        urllib.request.urlretrieve(
            "https://bootstrap.pypa.io/get-pip.py",
            str(get_pip_path),
        )
        r = subprocess.run(
            [venv_python, str(get_pip_path)],
            capture_output=True, text=True,
        )
        get_pip_path.unlink(missing_ok=True)

        if r.returncode == 0 and _has_pip(venv_python):
            print("  [OK] pip instalado via get-pip.py.")
            return

        print(f"  [ERROR] get-pip.py fallo: {r.stderr.strip()}")
    except Exception as e:
        print(f"  [ERROR] No se pudo descargar get-pip.py: {e}")
        get_pip_path.unlink(missing_ok=True)

    # --- Nada funciono: informar al usuario ---
    print()
    print("  [ERROR] No se pudo instalar pip en el venv.")
    print("  Instala el modulo ensurepip con tu gestor de paquetes:")
    print()
    print("    Arch Linux:     sudo pacman -S python")
    print("    Debian/Ubuntu:  sudo apt install python3-venv python3-pip")
    print("    Fedora/RHEL:    sudo dnf install python3-pip")
    print()
    print("  Despues vuelve a ejecutar este instalador.")
    sys.exit(1)


def _ensure_venv() -> str:
    """Crea un virtualenv e instala dependencias.

    Siempre comprueba e instala dependencias aunque el venv ya exista.
    Usa 'python -m pip' en vez de llamar a pip.exe directamente, que es
    mas robusto y evita problemas con rutas o pip corrupto.

    En Linux, tras crear el venv, verifica que pip este disponible y lo
    bootstrappea si es necesario (ensurepip o get-pip.py).
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
            # En Linux, si falla por falta de ensurepip, reintentar
            # con --without-pip y luego bootstrapear pip aparte
            if platform.system() != "Windows" and "ensurepip" in result.stderr:
                print("  [WARN] ensurepip no disponible, creando venv sin pip...")
                result = subprocess.run(
                    [sys.executable, "-m", "venv", "--without-pip", str(venv_dir)],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    print(f"  [ERROR] No se pudo crear el venv: {result.stderr.strip()}")
                    sys.exit(1)
            else:
                print(f"  [ERROR] No se pudo crear el venv: {result.stderr.strip()}")
                sys.exit(1)

        if not venv_python.exists():
            print(f"  [ERROR] venv creado pero no se encuentra: {venv_python}")
            sys.exit(1)

        print(f"  [OK] Entorno virtual creado: {venv_dir}")
    else:
        print(f"  [OK] Entorno virtual ya existe: {venv_dir}")

    # --- En Linux, asegurar que pip esta en el venv ---
    if platform.system() != "Windows":
        _bootstrap_pip(str(venv_python))

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
    """Crea e inicia un servicio systemd en Linux.

    Detalles importantes:
    - Usa el interprete del virtualenv (.venv) para tener las dependencias.
    - Configura VIRTUAL_ENV y PATH en el unit para que el venv funcione
      correctamente dentro del contexto aislado de systemd.
    - Establece HOME para evitar problemas con librerias que lo necesitan.
    - Crea los ficheros de log antes de arrancar para evitar fallos de
      StandardOutput=append cuando el fichero no existe.
    - Verifica que el servicio realmente ha arrancado tras systemctl start.
    """
    global PYTHON_EXE

    print(f"Instalando servicio systemd '{SYSTEMD_SERVICE}'...")
    print()

    # 1. Preparar entorno virtual e instalar dependencias
    print("  Preparando entorno virtual...")
    PYTHON_EXE = _ensure_venv()
    _verify_python(PYTHON_EXE)
    _verify_deps(PYTHON_EXE)

    # 2. Determinar usuario y home
    user = os.environ.get("SUDO_USER", "root")
    group = user
    # Obtener el HOME real del usuario (no el de root con sudo)
    try:
        import pwd
        user_home = pwd.getpwnam(user).pw_dir
    except (KeyError, ImportError):
        user_home = os.path.expanduser(f"~{user}")

    # 3. Rutas del venv para las variables de entorno del servicio
    venv_dir = CLIENT_DIR / ".venv"
    venv_bin = venv_dir / "bin"

    # 4. Crear los ficheros de log antes de arrancar (systemd append: los necesita)
    for log_file in (SERVICE_LOG, CLIENT_LOG):
        log_file.touch(exist_ok=True)
        # Asegurar que el usuario del servicio puede escribir
        subprocess.run(
            ["chown", f"{user}:{group}", str(log_file)],
            capture_output=True,
        )

    # 5. Asegurar permisos del directorio del cliente
    subprocess.run(
        ["chown", "-R", f"{user}:{group}", str(CLIENT_DIR)],
        capture_output=True,
    )

    # 6. Generar el unit de systemd
    service_content = f"""[Unit]
Description={DISPLAY_NAME}
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
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

# Variables de entorno necesarias para que el venv funcione
Environment=PYTHONUNBUFFERED=1
Environment=VIRTUAL_ENV={venv_dir}
Environment=PATH={venv_bin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=HOME={user_home}

[Install]
WantedBy=multi-user.target
"""
    SYSTEMD_UNIT_PATH.write_text(service_content, encoding="utf-8")
    print(f"  [OK] Unidad systemd creada: {SYSTEMD_UNIT_PATH}")

    # 7. Recargar systemd, habilitar y arrancar
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", SYSTEMD_SERVICE], check=True)

    # Parar primero por si habia una instancia anterior rota
    subprocess.run(
        ["systemctl", "stop", SYSTEMD_SERVICE],
        capture_output=True,
    )
    # Resetear contador de fallos para evitar bloqueo por StartLimitBurst
    subprocess.run(
        ["systemctl", "reset-failed", SYSTEMD_SERVICE],
        capture_output=True,
    )

    result = subprocess.run(
        ["systemctl", "start", SYSTEMD_SERVICE],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        print(f"  [ERROR] No se pudo arrancar el servicio: {err}")
        print()
        print("  Diagnostico:")
        subprocess.run(
            ["journalctl", "-u", SYSTEMD_SERVICE, "--no-pager", "-n", "20"],
        )
        sys.exit(1)

    # 8. Verificar que el servicio sigue activo tras unos segundos
    print("  Esperando 3 segundos para verificar estabilidad...")
    time.sleep(3)

    check = subprocess.run(
        ["systemctl", "is-active", SYSTEMD_SERVICE],
        capture_output=True, text=True,
    )
    status = check.stdout.strip()
    if status == "active":
        print(f"  [OK] Servicio '{SYSTEMD_SERVICE}' habilitado y ejecutandose.")
    else:
        print(f"  [ERROR] El servicio no se mantuvo activo (estado: {status}).")
        print()
        print("  Ultimas lineas del journal:")
        subprocess.run(
            ["journalctl", "-u", SYSTEMD_SERVICE, "--no-pager", "-n", "20"],
        )
        print()
        print(f"  Contenido de {SERVICE_LOG}:")
        if SERVICE_LOG.exists():
            print(SERVICE_LOG.read_text(encoding="utf-8", errors="replace")[-2000:])
        sys.exit(1)

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
        print(f"  [OK] Unidad eliminada: {SYSTEMD_UNIT_PATH}")
    else:
        print(f"  [INFO] La unidad no existia: {SYSTEMD_UNIT_PATH}")

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "reset-failed", SYSTEMD_SERVICE],
        capture_output=True,
    )

    # Limpiar logs del wrapper (no el log del cliente por si es util)
    if SERVICE_LOG.exists():
        SERVICE_LOG.unlink()
        print(f"  [OK] Log del wrapper eliminado: {SERVICE_LOG}")

    print("  Servicio eliminado correctamente.")


def status_linux():
    """Muestra el estado del servicio systemd y los logs recientes."""
    print("=" * 64)
    print(f"  Estado: {SYSTEMD_SERVICE}")
    print("=" * 64)

    # Estado del servicio
    print("\n[Servicio systemd]")
    result = subprocess.run(
        ["systemctl", "is-active", SYSTEMD_SERVICE],
        capture_output=True, text=True,
    )
    estado = result.stdout.strip()
    if estado == "active":
        print(f"  Estado: \033[32m{estado}\033[0m (ejecutandose)")
    elif estado == "inactive":
        print(f"  Estado: \033[33m{estado}\033[0m (detenido)")
    else:
        print(f"  Estado: \033[31m{estado}\033[0m")

    subprocess.run(["systemctl", "status", SYSTEMD_SERVICE, "--no-pager", "-l"])

    # Journal de systemd (mas fiable que los ficheros de log)
    print("\n[Journal systemd (ultimas 15 lineas)]")
    subprocess.run(
        ["journalctl", "-u", SYSTEMD_SERVICE, "--no-pager", "-n", "15"],
    )

    # Logs de fichero
    print("\n[Logs de fichero]")
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
