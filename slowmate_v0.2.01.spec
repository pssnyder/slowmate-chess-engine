# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['slowmate_uci.py'],
    pathex=[],
    binaries=[],
    datas=[('slowmate', 'slowmate')],
    hiddenimports=['slowmate.engine', 'slowmate.intelligence', 'slowmate.depth_search', 'slowmate.search', 'slowmate.search.move_ordering', 'slowmate.search.see_evaluation', 'slowmate.search.transposition_table', 'slowmate.search.zobrist_hashing', 'slowmate.search.killer_moves', 'slowmate.search.history_heuristic', 'slowmate.search.counter_moves', 'slowmate.search.late_move_reduction', 'slowmate.search.null_move_pruning', 'slowmate.search.futility_pruning', 'slowmate.search.integration', 'chess'],
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
    name='slowmate_v0.2.01',
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
