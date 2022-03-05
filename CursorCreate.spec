# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None
spec_root = Path(SPECPATH).resolve()

if(sys.platform.startswith("win")):
    icon = str(spec_root / "icon_windows.ico")
else:
    icon = None

if(sys.platform.startswith("darwin")):
    from glob import glob

    resource_folder = Path(glob(str(spec_root / "venv/lib/python*/site-packages/PySide6/Qt/lib/QtWebEngineCore.framework/Resources"))[0])

    datas = [
        (str(resource_folder / "icudtl.dat"), "PySide6/Qt/"),
        (str(resource_folder / "qtwebengine_resources.pak"), "PySide6/Qt/")
    ]
else:
    datas = None

a = Analysis(
    ['CursorCreate/cursorcreate.py'],
    pathex = [str(spec_root)],
    hiddenimports = [],
    datas=datas,
    hookspath = [],
    runtime_hooks = [],
    excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = block_cipher,
    noarchive = False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name = 'CursorCreate',
    debug = False,
    bootloader_ignore_signals = False,
    strip = False,
    upx = True,
    upx_exclude = [],
    runtime_tmpdir = None,
    console = False,
    icon=icon
)

if(sys.platform.startswith("darwin")):
    app = BUNDLE(
        exe,
        name="CursorCreate.app",
        icon=str(spec_root / "icon_mac.icns"),
        bundle_identifier=None
    )

    
