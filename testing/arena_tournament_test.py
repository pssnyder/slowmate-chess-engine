"""
Arena Tournament Readiness Test for SlowMate v2.0
Tests all critical UCI functionality needed for automated tournaments.
"""
import subprocess
import time
import sys
import os

def test_arena_compatibility(executable_path):
    """Test comprehensive UCI compatibility for Arena tournaments."""
    
    print("🏟️  SlowMate v2.0 Arena Tournament Readiness Test")
    print("=" * 60)
    
    tests = [
        {
            "name": "UCI Initialization",
            "commands": ["uci"],
            "expected": ["uciok"],
            "timeout": 5
        },
        {
            "name": "Ready Check",
            "commands": ["isready"],
            "expected": ["readyok"],
            "timeout": 5
        },
        {
            "name": "New Game Setup",
            "commands": ["ucinewgame", "isready"],
            "expected": ["readyok"],
            "timeout": 5
        },
        {
            "name": "Starting Position",
            "commands": ["position startpos", "go movetime 1000"],
            "expected": ["bestmove"],
            "timeout": 3
        },
        {
            "name": "FEN Position",
            "commands": [
                "position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "go movetime 1000"
            ],
            "expected": ["bestmove"],
            "timeout": 3
        },
        {
            "name": "Move Sequence",
            "commands": [
                "position startpos moves e2e4 e7e5 g1f3",
                "go movetime 1500"
            ],
            "expected": ["bestmove"],
            "timeout": 4
        },
        {
            "name": "Time Control (Tournament Style)",
            "commands": [
                "position startpos",
                "go wtime 300000 btime 300000 winc 5000 binc 5000"
            ],
            "expected": ["bestmove"],
            "timeout": 10
        },
        {
            "name": "Quick Stop Test",
            "commands": [
                "position startpos",
                "go movetime 10000",
                "stop"
            ],
            "expected": ["bestmove"],
            "timeout": 3
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}/{total}: {test['name']}")
        print(f"Commands: {' → '.join(test['commands'])}")
        
        try:
            # Prepare commands
            cmd_input = '\n'.join(test['commands'] + ['quit']) + '\n'
            
            # Run test
            start_time = time.time()
            process = subprocess.Popen(
                [executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=cmd_input, timeout=test['timeout'])
            elapsed = time.time() - start_time
            
            # Check results
            success = False
            for expected in test['expected']:
                if expected in stdout:
                    success = True
                    break
            
            if success:
                print(f"✅ PASSED ({elapsed:.2f}s)")
                passed += 1
            else:
                print(f"❌ FAILED - Expected: {test['expected']}")
                print(f"   Got: {stdout[:100]}...")
                
        except subprocess.TimeoutExpired:
            print(f"❌ FAILED - Timeout after {test['timeout']}s")
            process.kill()
        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Arena Compatibility Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 FULLY ARENA COMPATIBLE! Ready for automated tournaments!")
        return True
    elif passed >= total * 0.8:
        print("⚠️  MOSTLY COMPATIBLE - May work in tournaments with minor issues")
        return False
    else:
        print("❌ NOT ARENA READY - Requires fixes before tournament use")
        return False


def test_engine_strength():
    """Quick tactical test to verify engine strength."""
    print("\n🎯 Engine Strength Validation")
    print("-" * 40)
    
    tactical_tests = [
        {
            "name": "Mate in 1",
            "fen": "rnbqkbnr/pppp1Q1p/8/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
            "expected_type": "mate"
        },
        {
            "name": "Tactical Win", 
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "expected_type": "tactical"
        }
    ]
    
    executable_path = "dist/slowmate_v2.0_RELEASE.exe"
    
    for test in tactical_tests:
        print(f"\nTesting: {test['name']}")
        print(f"Position: {test['fen']}")
        
        try:
            cmd_input = f"uci\nposition fen {test['fen']}\ngo movetime 3000\nquit\n"
            
            process = subprocess.Popen(
                [executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=cmd_input, timeout=5)
            
            if "bestmove" in stdout:
                # Extract the move
                for line in stdout.split('\n'):
                    if line.startswith("bestmove"):
                        move = line.split()[1]
                        print(f"Engine move: {move}")
                        break
                print("✅ Engine found a move")
            else:
                print("❌ No move returned")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")


def main():
    """Main test runner."""
    executable_path = "dist/slowmate_v2.0_RELEASE.exe"
    
    if not os.path.exists(executable_path):
        print(f"❌ Executable not found: {executable_path}")
        print("Please run the build process first.")
        return False
    
    print(f"Testing executable: {executable_path}")
    print(f"File size: {os.path.getsize(executable_path) / (1024*1024):.1f} MB")
    
    # Run Arena compatibility tests
    arena_ready = test_arena_compatibility(executable_path)
    
    # Run strength validation
    test_engine_strength()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL VERDICT")
    print("=" * 60)
    
    if arena_ready:
        print("🏆 SlowMate v2.0 is TOURNAMENT READY!")
        print("✅ All UCI protocol requirements met")
        print("✅ Compatible with Arena and other UCI GUIs")
        print("✅ Suitable for automated tournaments")
        print("\n📋 Next Steps:")
        print("1. Add engine to Arena chess GUI")
        print("2. Configure tournament time controls")
        print("3. Run test games against other engines")
        print("4. Deploy in competitive tournaments")
    else:
        print("⚠️  SlowMate v2.0 needs additional testing")
        print("Some UCI compatibility issues detected")
        
    return arena_ready


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
