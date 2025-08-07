#!/usr/bin/env python3
"""
Test SlowMate v0.4.05 - Game Rules & Draw Detection
Test the newly implemented game rules and draw detection features.
"""

import subprocess
import sys
import time

def test_v0405_features():
    """Test v0.4.05 game rules features."""
    print("🧪 TESTING SlowMate v0.4.05 - Game Rules & Draw Detection")
    print("=" * 60)
    
    tests = [
        {
            "name": "🔧 Basic Engine Start",
            "commands": ["uci", "quit"],
            "expected": ["SlowMate 0.4.05", "uciok"]
        },
        {
            "name": "📊 Enhanced Eval Command",
            "commands": ["position startpos", "eval", "quit"],
            "expected": ["Total evaluation:", "Material:", "Position:"]
        },
        {
            "name": "🔄 Threefold Repetition Setup",
            "commands": [
                "position startpos moves g1f3 b8c6 f3g1 c6b8 g1f3 b8c6 f3g1 c6b8 g1f3",
                "eval",
                "quit"
            ],
            "expected": ["Threefold repetition: YES", "count: 3"]
        },
        {
            "name": "⏰ 50-Move Rule Display",
            "commands": [
                "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 95 50",
                "eval", 
                "quit"
            ],
            "expected": ["Approaching 50-move:", "moves left"]
        },
        {
            "name": "🎯 Mate Score Detection",
            "commands": [
                "position fen rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
                "go depth 2",
                "quit"
            ],
            "expected": ["score mate", "bestmove"]
        }
    ]
    
    passed = 0
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 40)
        
        try:
            # Run test
            process = subprocess.Popen(
                [sys.executable, "slowmate_uci.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="."
            )
            
            input_text = "\n".join(test['commands']) + "\n"
            stdout, stderr, = process.communicate(input=input_text, timeout=10)
            
            # Check results
            success = True
            for expected in test['expected']:
                if expected not in stdout:
                    success = False
                    print(f"❌ Missing: {expected}")
            
            if success:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED")
                print(f"Output: {stdout[:200]}...")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n📊 RESULTS: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("🎉 All v0.4.05 features working correctly!")
    else:
        print("⚠️  Some features need attention.")

if __name__ == "__main__":
    test_v0405_features()
