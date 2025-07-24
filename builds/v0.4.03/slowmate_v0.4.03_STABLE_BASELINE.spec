# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['slowmate_uci.py'],
    pathex=[],
    binaries=[],
    datas=[('slowmate', 'slowmate')],
    hiddenimports=['slowmate.engine', 'slowmate.intelligence', 'slowmate.uci', 'chess'],
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
    name='slowmate_v0.4.03_STABLE_BASELINE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
