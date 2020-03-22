# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import ctypes

block_cipher = None


spec_root = Path(SPECPATH).resolve()
cairo_lib = ctypes.util.find_library("cairo")


if(sys.platform.startswith("linux")):
    icon = None
    cairo_lib = str(Path("/usr/lib") / cairo_lib)
elif(sys.platform.startswith("darwin")):
    icon = str(spec_root / "icon_mac.icns")
elif(sys.platform.startswith("win32")):
    icon = str(spec_root / "icon_windows.ico")
else:
    raise ValueError("Spec file doesn't support " + sys.platform)


import cairocffi
import cairosvg
import cssselect2
import tinycss2

def get_version_file(pkg):
    return str((Path(pkg.__file__).resolve().parent) / "VERSION")

datas = [
    (get_version_file(cairocffi), "cairocffi"),
    (get_version_file(cairosvg), "."),
    (get_version_file(cssselect2), "cssselect2"),
    (get_version_file(tinycss2), "tinycss2")
]

binaries = [
    (cairo_lib, "."),
]

a = Analysis(
    ['cursorcreate.py'],
    pathex = [str(spec_root)],
    binaries = binaries,
    datas = datas,
    hiddenimports = ["pkg_resources.py2_warn"],
    hookspath = [],
    runtime_hooks = [],
    excludes = [],
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
