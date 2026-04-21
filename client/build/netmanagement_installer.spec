# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para NetManagement Installer
# Empaqueta install_service.py con todos los archivos del cliente necesarios
# en tiempo de ejecucion: client.py, config.py, system_info.py y requirements.txt

import sys
from pathlib import Path

# Directorio raiz del cliente (un nivel arriba del directorio build/)
CLIENT_DIR = Path(SPECPATH).parent

a = Analysis(
    [str(CLIENT_DIR / "install_service.py")],
    pathex=[str(CLIENT_DIR)],
    binaries=[],
    # Archivos de datos que el instalador necesita en ejecucion:
    # - client.py          → script principal del agente
    # - config.py          → modulo de configuracion
    # - system_info.py     → informacion del sistema
    # - requirements.txt   → lista de dependencias para pip install
    datas=[
        (str(CLIENT_DIR / "client.py"),       "."),
        (str(CLIENT_DIR / "config.py"),        "."),
        (str(CLIENT_DIR / "system_info.py"),   "."),
        (str(CLIENT_DIR / "requirements.txt"), "."),
    ],
    hiddenimports=[
        "psutil",
        "mss",
        "PIL",
        "websockets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    # Nombre del ejecutable final (sin extension; PyInstaller añade .exe en Windows)
    name="NetManagement-Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # Un unico binario autocontenido
    onefile=True,
    # Solicita elevacion de administrador en Windows (UAC prompt)
    # En Linux el usuario debe ejecutar con sudo
    uac_admin=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
