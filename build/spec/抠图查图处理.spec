# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
ENTRY_POINT = PROJECT_ROOT / 'src' / '抠图查图处理_mac.py'
SOURCE_INFO = (
    PROJECT_ROOT / 'release-metadata' / 'source-info.json'
    if os.environ.get('KOUTU_RELEASE_BUILD') == '1'
    else PROJECT_ROOT / 'source-info.json'
)
ICON_PATH = PROJECT_ROOT / 'assets' / '查图.icns'

a = Analysis(
    [str(ENTRY_POINT)],
    pathex=[],
    binaries=[],
    datas=[(str(SOURCE_INFO), '.')],
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
    name='抠图查图处理',
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
    icon=[str(ICON_PATH)],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='抠图查图处理',
)
app = BUNDLE(
    coll,
    name='抠图查图处理.app',
    icon=str(ICON_PATH),
    bundle_identifier='com.local.koutu-chatu',
)
