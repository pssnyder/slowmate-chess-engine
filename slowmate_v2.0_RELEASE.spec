# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['slowmate\\uci_main.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data')],
    hiddenimports=['slowmate.engine', 'slowmate.uci.protocol', 'slowmate.core.board', 'slowmate.core.moves', 'slowmate.core.evaluate', 'slowmate.core.time_manager', 'slowmate.core.opening_book', 'slowmate.core.tablebase', 'slowmate.search.enhanced', 'chess'],
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
    name='slowmate_v2.0_RELEASE',
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
