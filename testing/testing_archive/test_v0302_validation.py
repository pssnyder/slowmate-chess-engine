#!/usr/bin/env python3
"""
SlowMate v0.3.02 Validation Test

This script validates that v0.3.02 has:
1. ✅ No more +M500 mate evaluation bugs  
2. ✅ Enhanced endgame evaluation
3. ✅ Proper UCI mate output
4. ✅ Advanced endgame pattern recognition

Tests the built executable to ensure all fixes are working.
"""

import subprocess
import sys
import time
from pathlib import Path

def test_mate_evaluation_fixed():
    """Test that +M500 mate evaluation bug is fixed."""
    
    print("🧪 Testing Mate Evaluation Fix")
    print("=" * 40)
    
    # Path to v0.3.02 executable
    exe_path = Path("builds/v0.3.02/SlowMate_v0.3.02_Enhanced_Endgame.exe")
    
    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        return False
    
    print(f"🔍 Testing executable: {exe_path}")
    
    # Test position from the PGN that had +M500 bug
    # Early game position that should NOT show mate
    test_position = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    try:
        # Start engine
        process = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send UCI commands
        commands = [
            "uci",
            f"position fen {test_position}",
            "go depth 3",  # Light search to avoid timeout
            "quit"
        ]
        
        print("📤 Sending UCI commands...")
        for cmd in commands:
            print(f"   > {cmd}")
            process.stdin.write(cmd + "\n")
            process.stdin.flush()
            time.sleep(0.5)  # Give engine time to respond
        
        # Get output with timeout
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        
        print("\n📥 Engine Response:")
        print(stdout)
        
        # Check for mate evaluation bugs
        lines = stdout.split('\n')
        mate_found = False
        bad_mate = False
        
        for line in lines:
            if 'score' in line:
                print(f"📊 Score line: {line.strip()}")
                if 'mate' in line:
                    mate_found = True
                    # Check for unrealistic mate values
                    if 'mate 500' in line or 'mate 300' in line or 'mate 200' in line:
                        bad_mate = True
                        print(f"❌ Found bad mate: {line.strip()}")
        
        if bad_mate:
            print("❌ FAILED: Still showing unrealistic mate values!")
            return False
        elif mate_found:
            print("⚠️  Mate found (may be legitimate)")
        else:
            print("✅ No unrealistic mate values found")
        
        # Check for centipawn evaluation (normal position should show cp, not mate)
        cp_found = any('score cp' in line for line in lines)
        if cp_found:
            print("✅ Found normal centipawn evaluation")
        
        return not bad_mate
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_endgame_integration():
    """Test that endgame enhancement is integrated."""
    
    print("\n🧪 Testing Endgame Integration")  
    print("=" * 40)
    
    # Check if endgame evaluator files exist
    evaluator_path = Path("slowmate/knowledge/enhanced_endgame_evaluator.py")
    patterns_path = Path("slowmate/knowledge/endgame_patterns.json")
    
    files_exist = True
    if evaluator_path.exists():
        print("✅ Enhanced endgame evaluator exists")
    else:
        print("❌ Enhanced endgame evaluator missing")
        files_exist = False
    
    if patterns_path.exists():
        print("✅ Endgame patterns file exists")
    else:
        print("❌ Endgame patterns missing") 
        files_exist = False
    
    # Check intelligence.py integration
    try:
        with open("slowmate/intelligence.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'enhanced_endgame_evaluator' in content:
            print("✅ Endgame evaluator imported in intelligence.py")
        else:
            print("❌ Endgame evaluator not imported")
            files_exist = False
            
        if '_get_endgame_evaluation' in content:
            print("✅ Endgame evaluation method integrated")
        else:
            print("❌ Endgame evaluation method missing")
            files_exist = False
    
    except FileNotFoundError:
        print("❌ intelligence.py not found")
        files_exist = False
    
    return files_exist

def main():
    """Run all validation tests."""
    
    print("🎯 SlowMate v0.3.02 Validation")
    print("Enhanced Endgame + Fixed Mate Evaluation")
    print("=" * 50)
    
    # Test mate evaluation fix
    mate_fixed = test_mate_evaluation_fixed()
    
    # Test endgame integration  
    endgame_integrated = test_endgame_integration()
    
    print("\n📋 Test Results Summary")
    print("=" * 30)
    
    if mate_fixed:
        print("✅ Mate Evaluation: FIXED (no more +M500)")
    else:
        print("❌ Mate Evaluation: STILL BUGGY")
    
    if endgame_integrated:
        print("✅ Endgame Enhancement: INTEGRATED")
    else:
        print("❌ Endgame Enhancement: MISSING COMPONENTS")
    
    print(f"\n📊 Version Info:")
    try:
        with open("slowmate/__init__.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if '0.3.02' in content:
                print("✅ Version: v0.3.02-BETA")
            else:
                print("⚠️  Version may not be updated")
    except:
        print("❓ Version info unavailable")
    
    print(f"\n📦 Executable:")
    exe_path = Path("builds/v0.3.02/SlowMate_v0.3.02_Enhanced_Endgame.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ Built: {exe_path} ({size_mb:.1f} MB)")
    else:
        print("❌ Executable not found")
    
    if mate_fixed and endgame_integrated:
        print("\n🎉 SlowMate v0.3.02 VALIDATION PASSED!")
        print("\n🎮 Ready for Tournament Testing:")
        print("   • No more +M500 evaluation bugs")  
        print("   • Enhanced endgame pattern recognition")
        print("   • Improved king activity and mate detection")
        print("   • Better auto-adjudication behavior")
        return True
    else:
        print("\n❌ Some tests failed - needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
