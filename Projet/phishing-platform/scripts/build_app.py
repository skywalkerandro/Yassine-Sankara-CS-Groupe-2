"""
Construit l'application native du CLIENT avec PyInstaller.

A LANCER SUR LA MACHINE CIBLE (macOS ou Windows).
PyInstaller ne fait pas de cross-compilation.

Usage : python scripts/build_app.py

Pre-requis : pip install pyinstaller PySide6 Pillow
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "client" / "__main__.py"
ICON_PNG = ROOT / "icon.png"


def make_icns(png_path: Path) -> Path:
    """
    Convertit le PNG en .icns (format icone macOS).
    Utilise la commande 'iconutil' native de macOS.
    """
    iconset = Path("/tmp/PhishingClient.iconset")
    iconset.mkdir(exist_ok=True)

    from PIL import Image
    img = Image.open(png_path)

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        img.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
        if s <= 512:
            img.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")

    icns_path = ROOT / "icon.icns"
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)], check=True)
    print(f"  Icone .icns generee : {icns_path}")
    return icns_path


def main():
    system = platform.system()
    print(f"Construction du client pour : {system}\n")

    name = "PhishingClient"

    # Icone selon la plateforme
    icon_arg = []
    if system == "Darwin" and ICON_PNG.exists():
        try:
            icns = make_icns(ICON_PNG)
            icon_arg = ["--icon", str(icns)]
        except Exception as e:
            print(f"  Avertissement icone : {e} (on continue sans icone)")
    elif system == "Windows" and ICON_PNG.exists():
        # Sur Windows PyInstaller accepte directement le PNG ou un .ico
        icon_arg = ["--icon", str(ICON_PNG)]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", name,
        "--windowed",
        "--onedir",
        "--paths", str(ROOT),
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        *icon_arg,
        str(ENTRY),
    ]

    print("Lancement de PyInstaller...")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("\nEchec de la construction.")
        return result.returncode

    print("\nConstruction terminee !")
    if system == "Darwin":
        app_path = ROOT / "dist" / (name + ".app")
        print(f"  Application : {app_path}")
        print("\n  Pour l'ouvrir la premiere fois :")
        print("  -> Clic droit sur l'icone -> Ouvrir -> Ouvrir quand meme")
        print("  (macOS bloque les applis non signees par Apple)")
    elif system == "Windows":
        exe_path = ROOT / "dist" / name / (name + ".exe")
        print(f"  Executable : {exe_path}")

    print("\n  N'oubliez pas de lancer les services avant d'ouvrir l'appli :")
    print("  python scripts/run_all.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())