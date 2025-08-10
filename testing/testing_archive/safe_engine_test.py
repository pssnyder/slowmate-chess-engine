#!/usr/bin/env python3
"""
Safe Engine Testing Script

This script tests the SlowMate engine safely with proper timeouts
to prevent terminal lockups.
"""

import subprocess
import sys
import time
from pathlib import Path

def safe_engine_test(exe_path, timeout_seconds=10):
    """Safely test engine with timeout to prevent lockups"""
    
    print(f"🧪 Safe Testing: {exe_path}")
    print(f"⏰ Timeout: {timeout_seconds} seconds")
    
    try:
        # Start engine process
        process = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Test commands with timeout
        test_commands = [
            "uci",
            "position startpos",
            "go depth 1",
            "quit"
        ]
        
        print("📤 Sending commands...")
        for cmd in test_commands:
            print(f"   > {cmd}")
            if process.stdin:
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
            time.sleep(0.2)  # Brief pause between commands
        
        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            print(f"✅ Engine completed within {timeout_seconds}s")
            
            # Analyze output
            lines = stdout.split('\n')
            info_lines = [line for line in lines if line.startswith('info')]
            
            print(f"📊 Found {len(info_lines)} info lines")
            
            for line in info_lines[:3]:  # Show first 3 info lines
                if line.strip():
                    print(f"   {line.strip()}")
            
            # Check for reasonable scores
            for line in info_lines:
                if "score cp" in line:
                    try:
                        score_part = line.split("score cp")[1].split()[0]
                        score = int(score_part)
                        if abs(score) > 1000:
                            print(f"⚠️  High score detected: {score} centipawns")
                        else:
                            print(f"✅ Reasonable score: {score} centipawns")
                        break
                    except:
                        pass
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Engine timed out after {timeout_seconds}s - KILLING PROCESS")
            process.kill()
            process.communicate()  # Clean up
            print("❌ Engine test failed due to timeout")
            return False
            
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False

def test_available_executables():
    """Test all available executables safely"""
    
    print("🔍 SAFE ENGINE TESTING")
    print("=" * 40)
    
    # List of potential executables
    exe_candidates = [
        "slowmate_v0.3.03_eval_fix.exe",
        "dist/slowmate_v0.3.01-BETA.exe",
        "builds/v0.3.02/SlowMate_v0.3.02_Enhanced_Endgame.exe"
    ]
    
    tested_count = 0
    successful_tests = 0
    
    for exe_name in exe_candidates:
        exe_path = Path(exe_name)
        if exe_path.exists():
            print(f"\n--- Testing {exe_name} ---")
            tested_count += 1
            
            # Test with 8-second timeout
            success = safe_engine_test(exe_path, timeout_seconds=8)
            if success:
                successful_tests += 1
        else:
            print(f"⏭️  Skipping {exe_name} (not found)")
    
    print(f"\n📋 SUMMARY: {successful_tests}/{tested_count} executables passed")
    
    if successful_tests == 0 and tested_count > 0:
        print("🚨 ALL TESTS FAILED - Engine has critical issues!")
        return False
    elif tested_count == 0:
        print("❌ NO EXECUTABLES FOUND - Need to build first!")
        return False
    else:
        print("✅ At least one executable working")
        return True

if __name__ == "__main__":
    success = test_available_executables()
    sys.exit(0 if success else 1)
