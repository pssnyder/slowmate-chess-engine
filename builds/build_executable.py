#!/usr/bin/env python3
"""
Build script for SlowMate Chess Engine executable.
Creates a standalone executable for tournament use.
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Build the SlowMate executable using PyInstaller."""
    print("🔧 Building SlowMate Chess Engine v0.2.01 Executable")
    print("=" * 60)
    
    # Get version info
    sys.path.insert(0, str(Path(__file__).parent))
    from slowmate import __version__
    
    print(f"Version: {__version__}")
    print(f"Engine: Tournament-Ready SlowMate Depth Engine")
    print()
    
    # Build command
    cmd = [
        "python", "-m", "PyInstaller",
        "--onefile",                    # Single executable
        "--name", f"slowmate_v{__version__}",  # Executable name
        "--add-data", "slowmate;slowmate",     # Include slowmate package
        "--hidden-import", "slowmate.engine",
        "--hidden-import", "slowmate.intelligence", 
        "--hidden-import", "slowmate.depth_search",
        "--hidden-import", "slowmate.search",
        "--hidden-import", "slowmate.search.move_ordering",
        "--hidden-import", "slowmate.search.see_evaluation", 
        "--hidden-import", "slowmate.search.transposition_table",
        "--hidden-import", "slowmate.search.zobrist_hashing",
        "--hidden-import", "slowmate.search.killer_moves",
        "--hidden-import", "slowmate.search.history_heuristic",
        "--hidden-import", "slowmate.search.counter_moves",
        "--hidden-import", "slowmate.search.late_move_reduction",
        "--hidden-import", "slowmate.search.null_move_pruning",
        "--hidden-import", "slowmate.search.futility_pruning",
        "--hidden-import", "slowmate.search.integration",
        "--hidden-import", "chess",
        "--console",                    # Console application
        "--clean",                      # Clean build
        "slowmate_uci.py"              # Main script
    ]
    
    print("🚀 Starting PyInstaller build...")
    print("Command:", " ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Check if executable exists
        exe_path = Path("dist") / f"slowmate_v{__version__}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            
            # Test the executable
            print("\n🧪 Testing executable...")
            test_result = subprocess.run([str(exe_path), "--version"], 
                                       capture_output=True, text=True, timeout=10)
            if test_result.returncode == 0:
                print("✅ Executable test passed!")
            else:
                print("⚠️ Executable test warning - check functionality")
                
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_tournament_package():
    """Create a tournament package with executable and documentation."""
    print("\n📦 Creating Tournament Package...")
    
    from slowmate import __version__
    package_name = f"SlowMate_v{__version__}_Tournament"
    package_dir = Path(package_name)
    
    # Create package directory
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_source = Path("dist") / f"slowmate_v{__version__}.exe"
    exe_dest = package_dir / f"slowmate_v{__version__}.exe"
    
    if exe_source.exists():
        import shutil
        shutil.copy2(exe_source, exe_dest)
        print(f"✅ Copied executable to {exe_dest}")
    
    # Copy documentation
    docs_to_copy = [
        "README.md",
        "UCI_Integration_Guide.md",
        "docs/first_tournament_game_analysis.md"
    ]
    
    for doc in docs_to_copy:
        source = Path(doc)
        if source.exists():
            dest = package_dir / source.name
            shutil.copy2(source, dest)
            print(f"✅ Copied {doc}")
    
    # Copy tournament game
    game_source = Path("games/slowmate_first_tournament_victory_20250720.pgn")
    if game_source.exists():
        game_dest = package_dir / "first_tournament_victory.pgn"
        shutil.copy2(game_source, game_dest)
        print(f"✅ Copied tournament game PGN")
    
    # Create tournament readme
    tournament_readme = package_dir / "TOURNAMENT_README.txt"
    with open(tournament_readme, 'w') as f:
        f.write(f"""SlowMate Chess Engine v{__version__} - Tournament Package
============================================================

🏆 FIRST TOURNAMENT VICTORY ACHIEVED! 🏆

This package contains the tournament-ready SlowMate chess engine
that achieved its first engine-vs-engine competitive victory.

CONTENTS:
- slowmate_v{__version__}.exe: Tournament-ready executable
- README.md: Complete project documentation  
- UCI_Integration_Guide.md: Integration instructions
- first_tournament_game_analysis.md: Victory game analysis
- first_tournament_victory.pgn: Historic game archive

USAGE:
1. Run the executable from command line for UCI protocol
2. Integrate with chess GUIs (Arena, Nibbler, etc.)
3. Use for engine-vs-engine tournaments

FEATURES:
- Minimax search with alpha-beta pruning
- Tactical intelligence with threat detection
- Enhanced UCI protocol support
- Real-time analysis output
- Tournament-validated performance

ENGINE STRENGTH:
- Estimated ELO: 1200-1600 range
- Tournament Status: Competitive
- First Victory: July 20, 2025

For latest updates: https://github.com/pssnyder/slowmate_chess_engine

SlowMate: Transparent • Incremental • Competitive
""")
    
    print(f"✅ Tournament package created: {package_dir}")
    return True

def main():
    """Main build process."""
    print("SlowMate Chess Engine - Build Process")
    print("=" * 40)
    
    success = True
    
    # Build executable
    if not build_executable():
        print("❌ Executable build failed!")
        success = False
    
    # Create tournament package
    if success:
        if not create_tournament_package():
            print("❌ Tournament package creation failed!")
            success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Build process completed successfully!")
        print("\n🏆 SlowMate v0.1.0 Tournament Package Ready!")
        print("Ready for competitive engine-vs-engine testing!")
    else:
        print("❌ Build process failed - check errors above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
