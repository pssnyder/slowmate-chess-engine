#!/usr/bin/env python3
"""
Test SlowMate v0.4.06 - Search Intelligence & Hash Tables
Test the alpha-beta search and hash table functionality.
"""

import subprocess
import sys
import time

def test_v0406_features():
    """Test v0.4.06 search intelligence features."""
    print("🧪 TESTING SlowMate v0.4.06 - Search Intelligence & Hash Tables")
    print("=" * 65)
    
    tests = [
        {
            "name": "🔧 Version Check",
            "commands": ["uci", "quit"],
            "expected": ["SlowMate 0.4.06", "uciok"]
        },
        {
            "name": "🧠 Alpha-Beta Search",
            "commands": ["position startpos", "go depth 3", "quit"],
            "expected": ["info depth", "hashfull", "bestmove"]
        },
        {
            "name": "🗂️ Hash Table Usage",
            "commands": ["setoption name Hash value 32", "isready", "position startpos", "go depth 2", "quit"],
            "expected": ["readyok", "hashfull"]
        },
        {
            "name": "🧹 Clear Hash Command", 
            "commands": ["position startpos", "go depth 2", "clearhash", "quit"],
            "expected": ["hashfull", "bestmove"]
        },
        {
            "name": "⚡ Performance Comparison",
            "commands": ["position startpos", "go depth 4", "quit"],
            "expected": ["info depth 4", "nodes", "nps"]
        }
    ]
    
    passed = 0
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 45)
        
        try:
            # Run test
            start_time = time.time()
            process = subprocess.Popen(
                [sys.executable, "slowmate_uci.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="."
            )
            
            input_text = "\n".join(test['commands']) + "\n"
            stdout, stderr = process.communicate(input=input_text, timeout=15)
            test_time = time.time() - start_time
            
            # Check results
            success = True
            for expected in test['expected']:
                if expected not in stdout:
                    success = False
                    print(f"❌ Missing: {expected}")
            
            if success:
                print("✅ PASSED")
                if "depth 4" in test['name']:
                    # Extract performance info
                    lines = stdout.split('\n')
                    for line in lines:
                        if "info depth 4" in line and "nodes" in line:
                            print(f"   Performance: {line}")
                            break
                passed += 1
            else:
                print("❌ FAILED")
                print(f"Output sample: {stdout[:300]}...")
                
            print(f"   Test time: {test_time:.2f}s")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n📊 RESULTS: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("🎉 All v0.4.06 features working correctly!")
        print("✅ Alpha-beta search and hash tables implemented!")
    else:
        print("⚠️  Some features need attention.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = test_v0406_features()
    if success:
        print("\n🚀 Ready for Phase 3: Advanced Search & Pruning!")
    else:
        print("\n🔧 Phase 2 needs refinement before proceeding.")
