"""
Servicio nativo de Windows para el cliente de Proyecto DAM.

Utiliza pywin32 para registrarse como un servicio real del sistema operativo.
El servicio ejecuta client.py como subproceso y lo gestiona correctamente
(inicio, parada, reinicio automatico si el proceso muere).

Requisitos:
    pip install pywin32
    python -m pywin32_postinstall -install

No ejecutar directamente; usar install_service.py para gestionar.
"""

import subprocess
import sys
from pathlib import Path

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("ERROR: pywin32 no esta instalado.")
    print("  pip install pywin32")
    print("  python -m pywin32_postinstall -install")
    sys.exit(1)


CLIENT_DIR = Path(__file__).parent.resolve()
CLIENT_SCRIPT = str(CLIENT_DIR / "client.py")
SERVICE_LOG = str(CLIENT_DIR / "service_wrapper.log")


class ProyectoDAMClientService(win32serviceutil.ServiceFramework):
    """Servicio de Windows que ejecuta el cliente de monitorizacion."""

    _svc_name_ = "ProyectoDAMClient"
    _svc_display_name_ = "Proyecto DAM - Cliente de dispositivo"
    _svc_description_ = (
        "Cliente de monitorizacion de dispositivo. "
        "Reporta estado del equipo al servidor central via WebSocket."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        """Detiene el servicio."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self._terminate_process()

    def SvcDoRun(self):
        """Punto de entrada principal del servicio."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self._run_client()

    # ------------------------------------------------------------------

    def _run_client(self):
        """Lanza client.py y espera hasta recibir senal de parada."""
        python_exe = sys.executable

        while True:
            # Lanzar el proceso del cliente
            with open(SERVICE_LOG, "a", encoding="utf-8") as log_fh:
                self.process = subprocess.Popen(
                    [python_exe, CLIENT_SCRIPT],
                    cwd=str(CLIENT_DIR),
                    stdout=log_fh,
                    stderr=log_fh,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

            # Esperar: senal de parada o muerte del proceso
            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Senal de parada recibida
                    self._terminate_process()
                    return

                # Si el proceso termino inesperadamente, reiniciarlo
                if self.process and self.process.poll() is not None:
                    break  # Sale del bucle interno para reiniciar

            # Pausa antes de reiniciar (permite capturar stop signal)
            rc = win32event.WaitForSingleObject(self.stop_event, 3000)
            if rc == win32event.WAIT_OBJECT_0:
                return

    def _terminate_process(self):
        """Termina el subproceso limpiamente."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Ejecutado por el SCM (Service Control Manager de Windows)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ProyectoDAMClientService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Ejecutado desde linea de comandos (install, start, stop, remove)
        win32serviceutil.HandleCommandLine(ProyectoDAMClientService)
