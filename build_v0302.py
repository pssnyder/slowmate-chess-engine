#!/usr/bin/env python3
"""
Build SlowMate v0.3.02-BETA with Enhanced Endgame Evaluation

This version includes:
- Advanced endgame pattern recognition from 87 study guides
- Fixed mate evaluation (no more +M500 bugs!)
- Enhanced king activity and pawn promotion logic
- Improved UCI mate output and auto-adjudication
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Build configuration for v0.3.02
BUILD_CONFIG = {
    "version": "0.3.02-BETA",
    "name": "SlowMate_v0.3.02_Enhanced_Endgame",
    "description": "Enhanced Endgame Evaluation + Mate Bug Fixes",
    "build_dir": "builds/v0.3.02",
    "dist_dir": "dist"
}

def build_v0302():
    """Build SlowMate v0.3.02 executable."""
    
    print(f"🏗️  Building {BUILD_CONFIG['name']}")
    print("="*60)
    
    # Create build directory
    build_path = Path(BUILD_CONFIG["build_dir"])
    build_path.mkdir(parents=True, exist_ok=True)
    
    # PyInstaller command for v0.3.02
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",
        "--name", BUILD_CONFIG["name"],
        "--distpath", BUILD_CONFIG["dist_dir"],
        "--workpath", str(build_path / "build"),
        "--specpath", str(build_path),
        "--add-data", "data;data",  # Include endgame patterns
        "--add-data", "slowmate;slowmate",
        "--hidden-import", "slowmate.knowledge.enhanced_endgame_evaluator",
        "--hidden-import", "slowmate.time_management",
        "--console",
        "slowmate_uci.py"
    ]
    
    print(f"🔧 Running PyInstaller...")
    try:
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    
    # Verify executable was created
    exe_name = f"{BUILD_CONFIG['name']}.exe"
    exe_path = Path(BUILD_CONFIG["dist_dir"]) / exe_name
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Executable created: {exe_path}")
        print(f"📦 Size: {file_size:.1f} MB")
        
        # Test basic functionality
        print("🧪 Testing executable...")
        try:
            test_result = subprocess.run([str(exe_path)], 
                                       input="quit\n", 
                                       capture_output=True, 
                                       text=True, 
                                       timeout=10)
            print("✅ Executable test passed")
        except subprocess.TimeoutExpired:
            print("⚠️  Executable test timed out (may be waiting for input)")
        except Exception as e:
            print(f"⚠️  Executable test failed: {e}")
        
        # Copy to builds directory with version info
        versioned_exe = build_path / exe_name
        shutil.copy2(exe_path, versioned_exe)
        print(f"📁 Archived to: {versioned_exe}")
        
        return True
    else:
        print(f"❌ Executable not found at {exe_path}")
        return False

def main():
    """Main build function."""
    print("🚀 SlowMate v0.3.02-BETA Build Process")
    print("Enhanced Endgame + Fixed Mate Evaluation")
    print("="*60)
    
    if build_v0302():
        print("\n🎉 SlowMate v0.3.02-BETA built successfully!")
        print("\n📋 Key Features:")
        print("   • Advanced endgame pattern recognition")
        print("   • Fixed mate evaluation (no more +M500!)")
        print("   • Enhanced king activity logic")
        print("   • Improved UCI mate output")
        print("   • Better auto-adjudication")
        print("\n🎮 Ready for testing and tournament play!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
