"""
Script para instalar/desinstalar el cliente como servicio de Windows.
Uso:
    python install_service.py install   -> Instala y arranca el servicio
    python install_service.py remove    -> Detiene y elimina el servicio
    python install_service.py status    -> Muestra el estado del servicio y logs recientes
    python install_service.py test      -> Prueba que el cliente arranque correctamente

En Linux se puede usar systemd (ver instrucciones en README).
"""
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

SERVICE_NAME = "ProyectoDAMClient"
SERVICE_DISPLAY = "Proyecto DAM - Cliente de dispositivo"
PYTHON_EXE = sys.executable
CLIENT_DIR = Path(__file__).parent.resolve()
CLIENT_SCRIPT = str(CLIENT_DIR / "client.py")
WRAPPER_BAT = CLIENT_DIR / "_run_client.bat"
SERVICE_LOG = CLIENT_DIR / "service_wrapper.log"
CLIENT_LOG = CLIENT_DIR / "client_errors.log"


def is_admin() -> bool:
    """Comprueba si se ejecuta con privilegios de administrador."""
    if platform.system() != "Windows":
        return os.geteuid() == 0
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


def _create_wrapper_bat():
    """
    Crea un fichero .bat que:
      1. Establece el directorio de trabajo correcto.
      2. Redirige stdout y stderr a service_wrapper.log.
    Esto garantiza que CUALQUIER error (imports, permisos, etc.) quede registrado.
    """
    content = f"""@echo off
cd /d "{CLIENT_DIR}"
echo ===== Inicio del cliente: %DATE% %TIME% ===== >> "{SERVICE_LOG}"
"{PYTHON_EXE}" "{CLIENT_SCRIPT}" >> "{SERVICE_LOG}" 2>&1
echo ===== Fin del cliente: %DATE% %TIME% (exit code: %ERRORLEVEL%) ===== >> "{SERVICE_LOG}"
"""
    WRAPPER_BAT.write_text(content, encoding="utf-8")
    print(f"  Wrapper creado: {WRAPPER_BAT}")


def install_windows():
    """Crea una tarea programada en Windows que se ejecuta al iniciar el sistema."""
    print(f"Instalando servicio '{SERVICE_NAME}'...")

    # 1) Crear el wrapper .bat para que stdout/stderr queden en un log
    _create_wrapper_bat()

    # 2) Crear la tarea programada apuntando al .bat
    cmd = [
        "schtasks", "/Create",
        "/TN", SERVICE_NAME,
        "/TR", f'"{WRAPPER_BAT}"',
        "/SC", "ONSTART",      # Se ejecuta al arrancar el sistema
        "/RU", "SYSTEM",       # Ejecutar como SYSTEM
        "/RL", "HIGHEST",      # Privilegios elevados
        "/F",                  # Forzar creacion si ya existe
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("  Tarea programada creada correctamente.")
        print("  El cliente se ejecutara automaticamente al encender el equipo.")
        print(f"  Logs del wrapper  -> {SERVICE_LOG}")
        print(f"  Logs del cliente  -> {CLIENT_LOG}")

        # 3) Ejecutar ahora tambien
        run_cmd = ["schtasks", "/Run", "/TN", SERVICE_NAME]
        run_result = subprocess.run(run_cmd, capture_output=True, text=True)
        if run_result.returncode == 0:
            print("  Cliente iniciado.")
            # Esperar un poco y verificar que siga corriendo
            time.sleep(3)
            _check_running()
        else:
            print(f"  AVISO: No se pudo iniciar la tarea ahora: {run_result.stderr.strip()}")
    else:
        print(f"Error al crear la tarea: {result.stderr}")
        sys.exit(1)


def remove_windows():
    """Elimina la tarea programada de Windows y limpia el wrapper."""
    print(f"Eliminando servicio '{SERVICE_NAME}'...")

    # Detener si esta ejecutandose
    subprocess.run(
        ["schtasks", "/End", "/TN", SERVICE_NAME],
        capture_output=True, text=True
    )

    # Eliminar tarea
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", SERVICE_NAME, "/F"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print("  Tarea programada eliminada correctamente.")
        # Limpiar wrapper
        if WRAPPER_BAT.exists():
            WRAPPER_BAT.unlink()
            print("  Wrapper .bat eliminado.")
    else:
        print(f"  Error: {result.stderr}")


def _check_running():
    """Verifica si el proceso client.py esta actualmente en ejecucion."""
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True
    )
    # Tambien probar pythonw.exe
    result2 = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True
    )
    combined = result.stdout + result2.stdout
    running = "python" in combined.lower()
    if running:
        print("  [OK] Proceso Python detectado en ejecucion.")
    else:
        print("  [!!] No se detecto ningun proceso Python corriendo.")
        print("       Revisar logs para mas detalles.")
    return running


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


def status_windows():
    """Muestra el estado completo: tarea programada, proceso y logs."""
    print("=" * 64)
    print(f"  Estado del servicio: {SERVICE_NAME}")
    print("=" * 64)

    # 1) Estado de la tarea programada
    print("\n[Tarea programada]")
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", SERVICE_NAME, "/FO", "LIST", "/V"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        # Mostrar solo las lineas relevantes
        for line in result.stdout.splitlines():
            line = line.strip()
            if any(k in line for k in ["Estado", "Status", "Ultima", "Last", "Siguiente", "Next", "Resultado", "Result"]):
                print(f"  {line}")
    else:
        print(f"  La tarea '{SERVICE_NAME}' NO esta instalada.")

    # 2) Proceso en ejecucion
    print("\n[Proceso]")
    _check_running()

    # 3) Logs recientes
    print("\n[Logs recientes]")
    _show_recent_logs(SERVICE_LOG, "Wrapper log (errores de arranque)")
    print()
    _show_recent_logs(CLIENT_LOG, "Client log (actividad del cliente)")
    print()


def install_linux():
    """Crea un servicio systemd en Linux."""
    service_content = f"""[Unit]
Description={SERVICE_DISPLAY}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={PYTHON_EXE} {CLIENT_SCRIPT}
Restart=always
RestartSec=10
WorkingDirectory={Path(__file__).parent}

[Install]
WantedBy=multi-user.target
"""
    service_path = Path(f"/etc/systemd/system/{SERVICE_NAME.lower()}.service")
    service_path.write_text(service_content)
    print(f"Servicio creado en {service_path}")

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", SERVICE_NAME.lower()])
    subprocess.run(["systemctl", "start", SERVICE_NAME.lower()])
    print("Servicio habilitado e iniciado.")


def remove_linux():
    """Elimina el servicio systemd en Linux."""
    subprocess.run(["systemctl", "stop", SERVICE_NAME.lower()])
    subprocess.run(["systemctl", "disable", SERVICE_NAME.lower()])
    service_path = Path(f"/etc/systemd/system/{SERVICE_NAME.lower()}.service")
    if service_path.exists():
        service_path.unlink()
    subprocess.run(["systemctl", "daemon-reload"])
    print("Servicio eliminado.")


def status_linux():
    """Muestra el estado del servicio systemd."""
    subprocess.run(["systemctl", "status", SERVICE_NAME.lower()])


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
        # Leer salida durante 5 segundos
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

        # Verificar si se creo el log
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
        print("  install  - Instala y arranca el servicio")
        print("  remove   - Detiene y elimina el servicio")
        print("  status   - Muestra estado, proceso y logs recientes")
        print("  test     - Ejecuta el cliente 5s para verificar que funciona")
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
        "Linux": {"install": install_linux, "remove": remove_linux, "status": status_linux},
    }

    if system not in actions:
        print(f"Sistema '{system}' no soportado.")
        sys.exit(1)

    handler = actions[system].get(action)
    if handler is None:
        print(f"Accion '{action}' no reconocida. Usa: install, remove, status, test")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
