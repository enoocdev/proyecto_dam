#!/usr/bin/env python3
"""
build.py — Script de compilacion local del instalador NetManagement.

Genera el ejecutable para la plataforma actual (Windows o Linux)
usando PyInstaller con el spec incluido en este directorio.

Uso:
    python build/build.py

Requisitos previos:
    pip install pyinstaller
    pip install -r requirements.txt   (desde el directorio client/)
"""

import subprocess
import sys
import shutil
from pathlib import Path

BUILD_DIR  = Path(__file__).parent.resolve()
CLIENT_DIR = BUILD_DIR.parent
SPEC_FILE  = BUILD_DIR / "netmanagement_installer.spec"
DIST_DIR   = BUILD_DIR / "dist"
WORK_DIR   = BUILD_DIR / "work"


def check_pyinstaller():
    if shutil.which("pyinstaller") is None:
        print("[ERROR] PyInstaller no encontrado.")
        print("        Instálalo con:  pip install pyinstaller")
        sys.exit(1)


def build():
    check_pyinstaller()

    platform = "windows" if sys.platform == "win32" else "linux"
    dist_out = DIST_DIR / platform
    work_out = WORK_DIR / platform

    print(f"[INFO] Compilando para: {platform}")
    print(f"[INFO] Spec:  {SPEC_FILE}")
    print(f"[INFO] Salida: {dist_out}")

    cmd = [
        "pyinstaller",
        str(SPEC_FILE),
        "--distpath", str(dist_out),
        "--workpath",  str(work_out),
        "--noconfirm",
    ]

    result = subprocess.run(cmd, cwd=str(CLIENT_DIR))

    if result.returncode != 0:
        print("\n[ERROR] La compilacion ha fallado.")
        sys.exit(result.returncode)

    # Nombre del ejecutable generado
    exe_name = "NetManagement-Installer.exe" if platform == "windows" else "NetManagement-Installer"
    exe_path = dist_out / exe_name

    if exe_path.exists():
        print(f"\n[OK] Ejecutable generado en:\n     {exe_path}")
    else:
        print(f"\n[WARN] No se encontró el ejecutable esperado en {exe_path}")


if __name__ == "__main__":
    build()
