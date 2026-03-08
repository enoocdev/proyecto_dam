# Servicio nativo de Windows para el cliente del proyecto
# Usa pywin32 para registrarse como servicio del sistema operativo
# Ejecuta client py como subproceso y lo reinicia si se cae
# Para instalar y gestionar el servicio usar install service py

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


# Clase del servicio de Windows que ejecuta el cliente de monitorizacion
class ProyectoDAMClientService(win32serviceutil.ServiceFramework):

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

    # Detiene el servicio cuando el sistema lo solicita
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self._terminate_process()

    # Punto de entrada principal cuando el sistema arranca el servicio
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self._run_client()

    # Lanza client py y espera hasta recibir senal de parada
    # Si el proceso muere lo reinicia automaticamente
    def _run_client(self):
        python_exe = sys.executable

        while True:
            # Lanza el proceso del cliente redirigiendo la salida al log
            with open(SERVICE_LOG, "a", encoding="utf-8") as log_fh:
                self.process = subprocess.Popen(
                    [python_exe, CLIENT_SCRIPT],
                    cwd=str(CLIENT_DIR),
                    stdout=log_fh,
                    stderr=log_fh,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

            # Espera senal de parada o fin inesperado del proceso
            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Se recibio la orden de parar
                    self._terminate_process()
                    return

                # Si el proceso termino se sale del bucle para reiniciarlo
                if self.process and self.process.poll() is not None:
                    break  # Sale del bucle interno para reiniciar

            # Pausa breve antes de reiniciar para capturar posible parada
            rc = win32event.WaitForSingleObject(self.stop_event, 3000)
            if rc == win32event.WAIT_OBJECT_0:
                return

    # Termina el subproceso del cliente de forma limpia
    def _terminate_process(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Ejecutado por el Service Control Manager de Windows
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ProyectoDAMClientService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Ejecutado desde linea de comandos para instalar iniciar o parar
        win32serviceutil.HandleCommandLine(ProyectoDAMClientService)
