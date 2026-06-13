# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/yassine/Downloads/phishing-platform/client/__main__.py'],
    pathex=['/Users/yassine/Downloads/phishing-platform'],
    binaries=[],
    datas=[],
    hiddenimports=['PySide6.QtWidgets', 'PySide6.QtCore', 'PySide6.QtGui'],
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
    [],
    exclude_binaries=True,
    name='PhishingClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/yassine/Downloads/phishing-platform/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhishingClient',
)
app = BUNDLE(
    coll,
    name='PhishingClient.app',
    icon='/Users/yassine/Downloads/phishing-platform/icon.icns',
    bundle_identifier=None,
)
