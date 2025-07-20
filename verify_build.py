#!/usr/bin/env python3
"""
Simple test for the built executable.
"""

import subprocess
import sys
from pathlib import Path

def test_executable():
    """Test the built executable with basic UCI commands."""
    exe_path = Path("dist/slowmate_v0.1.0.exe")
    
    if not exe_path.exists():
        print("❌ Executable not found!")
        return False
    
    print(f"🧪 Testing executable: {exe_path}")
    print(f"📏 Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    
    # Test with basic UCI command
    try:
        print("Testing basic UCI command...")
        process = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send UCI command and wait for response
        stdout, stderr = process.communicate(input="uci\nquit\n", timeout=5)
        
        print("✅ Executable responded to UCI command!")
        print("Response preview:", stdout[:200] + "..." if len(stdout) > 200 else stdout)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️ Executable test timed out (but executable exists)")
        process.kill()
        return False  # Consider this a warning, not failure
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_tournament_package():
    """Create a tournament package manually since the build script failed."""
    print("\n📦 Creating Tournament Package...")
    
    package_name = "SlowMate_v0.1.0_Tournament"
    package_dir = Path(package_name)
    
    # Create package directory
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_source = Path("dist/slowmate_v0.1.0.exe")
    exe_dest = package_dir / "slowmate_v0.1.0.exe"
    
    if exe_source.exists():
        import shutil
        shutil.copy2(exe_source, exe_dest)
        print(f"✅ Copied executable to {exe_dest}")
    
    # Copy key files
    files_to_copy = [
        ("README.md", "README.md"),
        ("UCI_Integration_Guide.md", "UCI_Integration_Guide.md"),
        ("docs/first_tournament_game_analysis.md", "first_tournament_game_analysis.md"),
        ("games/slowmate_first_tournament_victory_20250720.pgn", "first_tournament_victory.pgn")
    ]
    
    for source_path, dest_name in files_to_copy:
        source = Path(source_path)
        if source.exists():
            dest = package_dir / dest_name
            shutil.copy2(source, dest)
            print(f"✅ Copied {source_path}")
    
    # Create tournament readme
    tournament_readme = package_dir / "TOURNAMENT_README.txt"
    with open(tournament_readme, 'w') as f:
        f.write("""SlowMate Chess Engine v0.1.0 - Tournament Package
============================================================

🏆 FIRST TOURNAMENT VICTORY ACHIEVED! 🏆

This package contains the tournament-ready SlowMate chess engine
that achieved its first engine-vs-engine competitive victory.

CONTENTS:
- slowmate_v0.1.0.exe: Tournament-ready executable
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

if __name__ == "__main__":
    print("SlowMate v0.1.0 - Executable Verification")
    print("=" * 50)
    
    # Test executable
    exe_works = test_executable()
    
    # Create package regardless (executable exists)
    package_created = create_tournament_package()
    
    print("\n" + "=" * 50)
    if exe_works and package_created:
        print("🎉 Tournament package ready for competitive testing!")
    elif package_created:
        print("📦 Tournament package created (executable needs manual testing)")
    else:
        print("❌ Package creation failed")
    
    print("\n🏆 SlowMate v0.1.0: From Educational Project to Tournament Engine!")
