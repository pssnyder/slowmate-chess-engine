#!/usr/bin/env python3
"""
Quick debug test for evaluation scaling
"""

import subprocess
import sys
import time

def test_debug_evaluation():
    """Test evaluation with debug output"""
    print("🔍 Debug Testing SlowMate Evaluation Scaling")
    print("=" * 60)
    
    exe_path = "slowmate_v0.3.03_eval_fix.exe"
    
    try:
        # Start the engine
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Initialize UCI
        process.stdin.write("uci\n")
        process.stdin.flush()
        time.sleep(1)
        
        # Clear output buffer
        while True:
            try:
                line = process.stdout.readline()
                if not line or "uciok" in line:
                    break
            except:
                break
        
        # Enable all debug options
        print("🔧 Enabling debug options...")
        process.stdin.write("setoption name EvalDebug value true\n")
        process.stdin.flush()
        process.stdin.write("setoption name EvalScaling value 10\n")
        process.stdin.flush()
        process.stdin.write("setoption name EvalMaxCap value 500\n")
        process.stdin.flush()
        
        # Set up starting position
        process.stdin.write("position startpos\n")
        process.stdin.flush()
        
        print("🎯 Running evaluation with debug...")
        
        # Request evaluation with depth 1
        process.stdin.write("go depth 1\n")
        process.stdin.flush()
        
        # Read all output
        all_output = []
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                line = process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                all_output.append(line)
                print(f"📊 {line}")
                if "bestmove" in line:
                    break
            except:
                break
        
        # Also check stderr for debug output
        print("\n🔍 Checking stderr for debug info...")
        try:
            stderr_line = process.stderr.readline()
            if stderr_line:
                print(f"🐛 {stderr_line.strip()}")
        except:
            pass
        
        # Quit engine
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=2)
        
        print("\n📋 Analysis:")
        for line in all_output:
            if "score cp" in line:
                parts = line.split("score cp ")
                if len(parts) > 1:
                    score_part = parts[1].split()[0]
                    try:
                        score = int(score_part)
                        print(f"   Final Score: {score} centipawns ({score/100:.1f} pawns)")
                        if abs(score) > 500:
                            print(f"   ⚠️ Score exceeds cap of 500!")
                    except ValueError:
                        print(f"   ❌ Could not parse score: {score_part}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False

if __name__ == "__main__":
    test_debug_evaluation()
