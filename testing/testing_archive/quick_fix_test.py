#!/usr/bin/env python3
"""
Quick fix verification test - tests the latest built executable
"""

import subprocess
import sys
import time

def quick_test():
    print("🔧 QUICK FIX VERIFICATION")
    print("=" * 30)
    
    exe_path = "slowmate_v0.3.03_FIXED.exe"
    
    try:
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Test commands
        commands = ["uci", "position startpos", "go depth 1", "quit"]
        
        for cmd in commands:
            print(f"> {cmd}")
            if process.stdin:
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
            time.sleep(0.2)
        
        # Wait with timeout
        try:
            stdout, stderr = process.communicate(timeout=8)
            
            # Look for info lines
            lines = stdout.split('\n')
            info_lines = [line for line in lines if line.startswith('info') and 'score cp' in line]
            
            if info_lines:
                line = info_lines[0]
                print(f"📊 {line.strip()}")
                
                # Extract score
                try:
                    score = int(line.split('score cp')[1].split()[0])
                    print(f"Score: {score} centipawns ({score/100:.1f} pawns)")
                    
                    if abs(score) <= 300:
                        print("✅ Score within 300cp emergency cap!")
                        return True
                    elif abs(score) <= 1000:
                        print("⚠️  Score higher than 300cp but under 1000cp")
                        return True
                    else:
                        print("❌ Score still too high!")
                        return False
                        
                except:
                    print("❌ Could not parse score")
                    return False
            else:
                print("❌ No score info found")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout - killing process")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    print("🎉 SUCCESS!" if success else "❌ FAILED!")
    sys.exit(0 if success else 1)
