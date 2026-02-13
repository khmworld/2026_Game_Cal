# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import shutil

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("ui_style.qss", "."),
        ("calendar.md", "."),
        ("assets/app_icon.png", "assets"),
        ("assets/app_icon.ico", "assets"),
    ],
    hiddenimports=[],
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
    name="GameCalendar_onedir",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/app_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GameCalendar_onedir",
)

# Keep a user-editable assets folder at dist/GameCalendar_onedir/assets as well.
dist_assets = Path(coll.name) / "assets"
dist_assets.mkdir(parents=True, exist_ok=True)
for src in (Path("assets") / "app_icon.png", Path("assets") / "app_icon.ico"):
    if src.exists():
        shutil.copy2(src, dist_assets / src.name)
