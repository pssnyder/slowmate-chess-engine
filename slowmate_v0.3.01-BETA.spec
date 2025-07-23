# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['slowmate_uci.py'],
    pathex=[],
    binaries=[],
    datas=[('slowmate', 'slowmate')],
    hiddenimports=['slowmate.engine', 'slowmate.intelligence', 'slowmate.depth_search', 'slowmate.search', 'slowmate.search.move_ordering', 'slowmate.search.see_evaluation', 'slowmate.search.transposition_table', 'slowmate.search.zobrist_hashing', 'slowmate.search.killer_moves', 'slowmate.search.history_heuristic', 'slowmate.search.counter_moves', 'slowmate.search.late_move_reduction', 'slowmate.search.null_move_pruning', 'slowmate.search.futility_pruning', 'slowmate.search.integration', 'slowmate.time_management', 'slowmate.time_management.time_control', 'slowmate.time_management.time_allocation', 'slowmate.time_management.search_timeout', 'slowmate.time_management.time_tracking', 'slowmate.time_management.iterative_deepening', 'slowmate.time_management.aspiration_windows', 'slowmate.time_management.search_controller', 'slowmate.time_management.dynamic_allocation', 'slowmate.time_management.emergency_mode', 'slowmate.time_management.search_extensions', 'slowmate.time_management.move_overhead', 'chess'],
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
    name='slowmate_v0.3.01-BETA',
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
