#!/usr/bin/env python3
"""
SlowMate v0.4.0 - Simple Baseline Build Script

Simplified build process for the restored v0.1.0 baseline.
Only builds what we actually have, no complex dependencies.
"""

import os
import subprocess
import json
from build_config import get_build_info

def build_baseline_executable():
    """Build the v0.4.0 baseline executable."""
    
    print("SlowMate v0.4.0 Baseline - Simple Build Process")
    print("=" * 50)
    
    # Get build info
    build_info = get_build_info()
    print(f"🔧 Building {build_info['full_name']}")
    print(f"📝 Description: {build_info['description']}")
    print(f"🎯 Features: {build_info['features']}")
    
    # Change to parent directory where slowmate_uci.py is located
    os.chdir('..')
    
    # Simple PyInstaller command for baseline
    cmd = [
        'python', '-m', 'PyInstaller',
        '--onefile',
        '--name', build_info['executable_name'].replace('.exe', ''),
        '--add-data', 'slowmate;slowmate',
        '--hidden-import', 'slowmate.engine',
        '--hidden-import', 'slowmate.intelligence', 
        '--hidden-import', 'slowmate.uci',
        '--hidden-import', 'chess',
        '--console',
        '--clean',
        'slowmate_uci.py'
    ]
    
    print(f"🚀 Starting PyInstaller build...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            
            # Move executable to builds/dist
            exe_name = build_info['executable_name']
            src_exe = f"dist/{build_info['executable_name'].replace('.exe', '')}.exe"
            dst_exe = f"builds/dist/{exe_name}"
            
            # Ensure builds/dist exists
            os.makedirs("builds/dist", exist_ok=True)
            
            if os.path.exists(src_exe):
                import shutil
                shutil.copy2(src_exe, dst_exe)
                print(f"📦 Executable copied to: {dst_exe}")
                
                # Create tournament folder
                tournament_folder = f"builds/{build_info['tournament_name']}"
                os.makedirs(tournament_folder, exist_ok=True)
                shutil.copy2(dst_exe, tournament_folder)
                
                # Create simple readme
                readme_content = f"""# {build_info['full_name']}

## Description
{build_info['description']}

## Features
{build_info['features']}

## Usage
1. Copy `{exe_name}` to your chess GUI directory
2. Add engine to your GUI (Arena, ChessBase, etc.)
3. Engine will appear as "{build_info['full_name']}"

## Version
{build_info['version_string']} - Restored tournament-winning baseline

## Build Date
{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                with open(f"{tournament_folder}/README.txt", 'w') as f:
                    f.write(readme_content)
                
                print(f"🏆 Tournament package created: {tournament_folder}")
                return True
                
            else:
                print(f"❌ Executable not found at: {src_exe}")
                return False
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def test_executable():
    """Test the built executable."""
    
    build_info = get_build_info()
    exe_path = f"builds/dist/{build_info['executable_name']}"
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found: {exe_path}")
        return False
    
    print(f"🧪 Testing executable: {build_info['executable_name']}")
    
    try:
        # Test that executable starts and responds to uci command
        result = subprocess.run([exe_path], 
                              input="uci\nquit\n", 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if "uciok" in result.stdout:
            print("✅ Executable responds to UCI commands")
            return True
        else:
            print("❌ Executable does not respond properly to UCI")
            print("Output:", result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Executable test timed out")
        return False
    except Exception as e:
        print(f"❌ Executable test failed: {e}")
        return False

def main():
    """Build and test the baseline executable."""
    
    print("🚀 Starting v0.4.0 baseline build process...")
    
    if build_baseline_executable():
        print("\n🧪 Testing built executable...")
        if test_executable():
            print("\n🎯 BUILD AND TEST SUCCESSFUL!")
            print("✅ v0.4.0 baseline executable created and verified")
            print("✅ Tournament package ready for deployment")
            print("✅ Ready to proceed to Phase 1: Infrastructure Enhancement")
            return True
        else:
            print("\n⚠️  BUILD SUCCESSFUL BUT TEST FAILED")
            print("Executable was created but may have issues")
            return False
    else:
        print("\n❌ BUILD FAILED")
        print("Manual intervention required")
        return False

if __name__ == "__main__":
    main()
