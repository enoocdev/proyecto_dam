# Directorio de compilación — NetManagement Installer

Este directorio contiene los recursos necesarios para compilar el instalador
del agente cliente como ejecutable nativo con **PyInstaller**.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `netmanagement_installer.spec` | Spec de PyInstaller: define qué archivos empaquetar y las opciones de compilación |
| `build.py` | Script helper para compilar en local en la plataforma actual |
| `dist/` | Generado automáticamente — contiene los ejecutables compilados |
| `work/` | Generado automáticamente — archivos temporales de PyInstaller |

## Compilación automática (GitHub Actions)

El workflow [`.github/workflows/build-client.yml`](../../.github/workflows/build-client.yml)
compila automáticamente los binarios para **Windows** y **Linux** en paralelo.

### Cuándo se ejecuta

- **Al crear un tag** de versión (p. ej., `git tag v1.0 && git push --tags`):
  genera un Release de GitHub con ambos binarios adjuntos.
- **Manualmente** desde la pestaña *Actions* de GitHub (workflow_dispatch).

### Artefactos generados

| Plataforma | Archivo |
|------------|---------|
| Windows | `NetManagement-Installer-windows.exe` |
| Linux | `NetManagement-Installer-linux` |

## Compilación local

```bash
# Desde el directorio client/
pip install pyinstaller
pip install -r requirements.txt

python build/build.py
```

El ejecutable se genera en `build/dist/<plataforma>/NetManagement-Installer[.exe]`.

## Uso del instalador generado

**Windows** (como Administrador — el UAC lo solicita automáticamente):
```
NetManagement-Installer-windows.exe
```

**Linux** (requiere sudo para crear el servicio systemd):
```bash
sudo ./NetManagement-Installer-linux
```

El instalador:
1. Crea un entorno virtual Python en el directorio del agente.
2. Instala las dependencias (`websockets`, `psutil`, `mss`, `Pillow`).
3. Registra el agente como servicio del sistema (Task Scheduler en Windows, systemd en Linux).
4. Arranca el servicio.
