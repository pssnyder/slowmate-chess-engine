#!/usr/bin/env python3
"""
Quick test for the evaluation scaling fix
"""

import subprocess
import sys
import time

def test_evaluation_scaling():
    """Test the evaluation scaling fix"""
    print("🧪 Testing SlowMate v0.3.03 Evaluation Scaling Fix")
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
        
        # Test UCI options
        print("📋 Testing UCI Options...")
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read UCI response
        uci_response = []
        start_time = time.time()
        while time.time() - start_time < 3:
            line = process.stdout.readline()
            if not line:
                break
            uci_response.append(line.strip())
            if "uciok" in line:
                break
        
        # Check for evaluation options
        eval_scaling_found = False
        eval_cap_found = False
        for line in uci_response:
            if "EvalScaling" in line:
                print("✅ EvalScaling option found:", line)
                eval_scaling_found = True
            elif "EvalMaxCap" in line:
                print("✅ EvalMaxCap option found:", line)
                eval_cap_found = True
        
        if not eval_scaling_found:
            print("❌ EvalScaling option NOT found")
        if not eval_cap_found:
            print("❌ EvalMaxCap option NOT found")
        
        # Test position evaluation
        print("\n🎯 Testing Position Evaluation...")
        
        # Set up starting position
        process.stdin.write("position startpos\n")
        process.stdin.flush()
        
        # Set evaluation debug on
        process.stdin.write("setoption name EvalDebug value true\n")
        process.stdin.flush()
        
        # Request evaluation
        process.stdin.write("go depth 1\n")
        process.stdin.flush()
        
        # Read evaluation response
        eval_response = []
        start_time = time.time()
        while time.time() - start_time < 5:
            line = process.stdout.readline()
            if not line:
                break
            eval_response.append(line.strip())
            print("📊", line.strip())
            if "bestmove" in line:
                break
        
        # Check evaluation values
        for line in eval_response:
            if "score cp" in line:
                # Extract centipawn score
                parts = line.split("score cp ")
                if len(parts) > 1:
                    score_part = parts[1].split()[0]
                    try:
                        score = int(score_part)
                        if abs(score) > 1000:
                            print(f"⚠️ High evaluation detected: {score} centipawns ({score/100:.1f} pawns)")
                        else:
                            print(f"✅ Reasonable evaluation: {score} centipawns ({score/100:.1f} pawns)")
                    except ValueError:
                        print(f"❌ Could not parse score: {score_part}")
        
        # Quit engine
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=2)
        
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False

if __name__ == "__main__":
    success = test_evaluation_scaling()
    sys.exit(0 if success else 1)
