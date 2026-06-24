# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../../src/抠图查图处理_mac.py'],
    pathex=[],
    binaries=[],
    datas=[('../../source-info.json', '.')],
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
    icon=['/Users/mini/Desktop/codex项目/koutu_chatu_mac_app/assets/查图.icns'],
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
    icon='/Users/mini/Desktop/codex项目/koutu_chatu_mac_app/assets/查图.icns',
    bundle_identifier='com.local.koutu-chatu',
)
