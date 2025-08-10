#!/usr/bin/env python3
"""
Test SlowMate v0.4.03 FIXED - Verify iterative deepening works
"""

import subprocess
import threading
import time

def test_fixed_version():
    print("🧪 Testing SlowMate v0.4.03 STABLE BASELINE FIXED")
    print("=" * 50)
    print("🎯 Verifying iterative deepening shows all depths 1->5")
    
    try:
        engine = subprocess.Popen(
            ["slowmate_v0.4.03_STABLE_BASELINE_FIXED.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        depths_seen = []
        
        def read_output():
            try:
                while True:
                    line = engine.stdout.readline()
                    if not line:
                        break
                    print(f"ENGINE: {line.strip()}")
                    # Track depths
                    if "info depth" in line:
                        parts = line.split()
                        try:
                            depth_idx = parts.index("depth") + 1
                            if depth_idx < len(parts):
                                depth = int(parts[depth_idx])
                                if depth not in depths_seen:
                                    depths_seen.append(depth)
                        except:
                            pass
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
        
        engine.stdin.write("position startpos\n")
        engine.stdin.flush()
        time.sleep(0.5)
        
        print("📤 Starting search depth 5...")
        engine.stdin.write("go depth 5\n")
        engine.stdin.flush()
        
        # Wait for search to complete
        time.sleep(8)
        
        print("📤 Stopping engine...")
        engine.stdin.write("quit\n")
        engine.stdin.flush()
        
        engine.wait(timeout=3)
        
        print(f"\n🎯 DEPTHS SEEN: {sorted(depths_seen)}")
        if len(depths_seen) >= 5:
            print("✅ SUCCESS: Engine shows iterative deepening!")
        else:
            print("❌ PROBLEM: Engine not showing all depths")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        if engine:
            engine.kill()

if __name__ == "__main__":
    test_fixed_version()
