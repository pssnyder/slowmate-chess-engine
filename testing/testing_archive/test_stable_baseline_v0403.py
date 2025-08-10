#!/usr/bin/env python3
"""
Test SlowMate v0.4.03 STABLE BASELINE 
Verify that the search depth issue is fixed and engine reaches consistent depths
"""

import subprocess
import threading
import time

def test_stable_baseline():
    print("🧪 Testing SlowMate v0.4.03 STABLE BASELINE")
    print("=" * 50)
    print("🎯 Verifying fixed depth search and consistent UCI output")
    
    try:
        engine = subprocess.Popen(
            ["slowmate_v0.4.03_STABLE_BASELINE.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        def read_output():
            try:
                while True:
                    line = engine.stdout.readline()
                    if not line:
                        break
                    print(f"ENGINE: {line.strip()}")
            except:
                pass
        
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        print("📤 Initializing engine...")
        engine.stdin.write("uci\n")
        engine.stdin.flush()
        time.sleep(1)
        
        engine.stdin.write("isready\n")
        engine.stdin.flush()
        time.sleep(1)
        
        engine.stdin.write("ucinewgame\n")
        engine.stdin.flush()
        time.sleep(0.5)
        
        engine.stdin.write("position startpos\n")
        engine.stdin.flush()
        time.sleep(0.5)
        
        print("📤 Testing search depth 8 (should reach depth 8 consistently)...")
        engine.stdin.write("go depth 8\n")
        engine.stdin.flush()
        
        # Wait for search to complete
        time.sleep(15)
        
        print("📤 Stopping engine...")
        engine.stdin.write("quit\n")
        engine.stdin.flush()
        
        engine.wait(timeout=5)
        
        print("✅ Stable baseline test completed!")
        print("🎯 Check above output to verify engine reaches depth 8 consistently")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        if engine:
            engine.kill()

if __name__ == "__main__":
    test_stable_baseline()
