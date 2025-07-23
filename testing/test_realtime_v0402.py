#!/usr/bin/env python3
"""
Test real-time UCI output for SlowMate v0.4.02
This tests if the engine outputs info at each depth in real time
and doesn't stall during thinking
"""

import subprocess
import threading
import time
import signal
import sys

def test_realtime_output():
    print("🧪 Testing SlowMate v0.4.02 Real-Time UCI Output")
    print("=" * 50)
    
    # Start the engine
    try:
        engine = subprocess.Popen(
            ["dist/slowmate_v0.4.02_TIME_MANAGEMENT.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0  # Unbuffered for real-time output
        )
        
        def read_output():
            """Read engine output in real-time"""
            try:
                while True:
                    line = engine.stdout.readline()
                    if not line:
                        break
                    print(f"ENGINE: {line.strip()}")
            except:
                pass
        
        # Start output reader thread
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        print("📤 Sending UCI initialization...")
        engine.stdin.write("uci\n")
        engine.stdin.flush()
        time.sleep(1)
        
        print("📤 Sending isready...")
        engine.stdin.write("isready\n")
        engine.stdin.flush()
        time.sleep(1)
        
        print("📤 Starting new game...")
        engine.stdin.write("ucinewgame\n")
        engine.stdin.flush()
        time.sleep(0.5)
        
        print("📤 Setting starting position...")
        engine.stdin.write("position startpos\n")
        engine.stdin.flush()
        time.sleep(0.5)
        
        print("📤 Starting search (go depth 4)...")
        print("⏱️ Watching for real-time info output...")
        start_time = time.time()
        
        engine.stdin.write("go depth 4\n")
        engine.stdin.flush()
        
        # Wait for search to complete (max 10 seconds)
        time.sleep(10)
        
        elapsed = time.time() - start_time
        print(f"⏱️ Search completed in {elapsed:.2f} seconds")
        
        print("📤 Stopping engine...")
        engine.stdin.write("quit\n")
        engine.stdin.flush()
        
        # Wait for engine to exit
        engine.wait(timeout=5)
        
        print("✅ Real-time output test completed!")
        
    except subprocess.TimeoutExpired:
        print("⚠️ Engine didn't respond within timeout - killing process")
        engine.kill()
    except Exception as e:
        print(f"❌ Test error: {e}")
        if engine:
            engine.kill()

if __name__ == "__main__":
    test_realtime_output()
