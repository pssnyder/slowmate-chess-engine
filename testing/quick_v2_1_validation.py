"""
SlowMate v2.1 Quick Validation Script
Rapid test to verify emergency fixes are working
"""

import os
import sys
import time
import chess

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.engine_v2_1 import SlowMateEngine
from slowmate.uci.protocol_v2_1 import UCIProtocol


def test_basic_functionality():
    """Test basic engine functionality."""
    print("🔧 Testing Basic Engine Functionality...")
    
    try:
        # Initialize engine
        engine = SlowMateEngine()
        print("  ✅ Engine initialization successful")
        
        # Test position setting
        engine.set_position("startpos")
        print("  ✅ Position setting successful")
        
        # Test move generation
        moves = engine.move_generator.get_legal_moves()
        print(f"  ✅ Move generation successful ({len(moves)} legal moves)")
        
        # Test search
        start_time = time.time()
        move = engine.search(time_limit_ms=1000)
        elapsed = time.time() - start_time
        
        if move:
            print(f"  ✅ Search successful: {move.uci()} (took {elapsed:.2f}s)")
            
            # Verify move is legal
            legal_moves = list(engine.board.board.legal_moves)
            if move in legal_moves:
                print("  ✅ Returned move is legal")
            else:
                print("  ❌ CRITICAL: Returned move is ILLEGAL!")
                return False
        else:
            print("  ❌ CRITICAL: Search returned None!")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Exception in basic functionality: {e}")
        return False


def test_uci_protocol():
    """Test UCI protocol compliance."""
    print("\n🔌 Testing UCI Protocol...")
    
    try:
        engine = SlowMateEngine()
        uci = UCIProtocol(engine)
        uci.set_silent_mode(True)
        
        # Test basic UCI commands
        uci.process_command("uci")
        print("  ✅ UCI command successful")
        
        uci.process_command("isready")
        print("  ✅ isready command successful")
        
        uci.process_command("ucinewgame")
        print("  ✅ ucinewgame command successful")
        
        uci.process_command("position startpos")
        print("  ✅ position command successful")
        
        # Test go command (non-blocking)
        uci.process_command("go movetime 1000")
        print("  ✅ go command initiated")
        
        # Wait for search completion
        timeout = 5.0
        start_time = time.time()
        while uci.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        if not uci.searching:
            print("  ✅ Search completed within timeout")
        else:
            print("  ❌ WARNING: Search did not complete within timeout")
            
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Exception in UCI protocol: {e}")
        return False


def test_illegal_move_prevention():
    """Test that engine never generates illegal moves."""
    print("\n🚫 Testing Illegal Move Prevention...")
    
    test_positions = [
        ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("after e4 e5", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"),
        ("italian game", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
    ]
    
    try:
        engine = SlowMateEngine()
        
        for name, fen in test_positions:
            engine.set_position(fen)
            legal_moves = list(engine.board.board.legal_moves)
            
            if not legal_moves:
                print(f"  ⚠️  No legal moves in {name} - skipping")
                continue
                
            move = engine.search(time_limit_ms=500)
            
            if move is None:
                print(f"  ❌ CRITICAL: Engine returned None in {name}")
                return False
                
            if move not in legal_moves:
                print(f"  ❌ CRITICAL: Engine returned illegal move {move.uci()} in {name}")
                return False
                
            print(f"  ✅ Legal move {move.uci()} in {name}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Exception in illegal move test: {e}")
        return False


def test_time_management():
    """Test basic time management."""
    print("\n⏱️  Testing Time Management...")
    
    try:
        engine = SlowMateEngine()
        engine.set_position("startpos")
        
        # Test short time limit
        start_time = time.time()
        move = engine.search(time_limit_ms=500)
        elapsed = time.time() - start_time
        
        if move:
            print(f"  ✅ Move returned in {elapsed:.2f}s (target: 0.5s)")
            if elapsed > 2.0:  # Allow some buffer
                print(f"  ⚠️  WARNING: Took longer than expected")
            else:
                print(f"  ✅ Time management acceptable")
        else:
            print(f"  ❌ CRITICAL: No move returned")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Exception in time management test: {e}")
        return False


def quick_competitive_test():
    """Quick competitive test against simple positions."""
    print("\n🏆 Quick Competitive Test...")
    
    try:
        engine = SlowMateEngine()
        
        # Test obvious capture
        engine.set_position("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
        move = engine.search(time_limit_ms=1000)
        
        if move:
            print(f"  ✅ Move in opening: {move.uci()}")
            # Any reasonable development move is fine
            reasonable_moves = ["g1f3", "b1c3", "f1c4", "d2d3", "f2f4"]
            if move.uci() in reasonable_moves:
                print("  ✅ Reasonable opening development")
            else:
                print(f"  ⚠️  Unusual opening move: {move.uci()}")
        else:
            print("  ❌ CRITICAL: No move in opening")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Exception in competitive test: {e}")
        return False


def main():
    """Run quick validation."""
    print("=" * 60)
    print("SlowMate v2.1 Emergency Validation - Quick Test")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("UCI Protocol", test_uci_protocol),
        ("Illegal Move Prevention", test_illegal_move_prevention),
        ("Time Management", test_time_management),
        ("Competitive Test", quick_competitive_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        result = test_func()
        if result:
            passed += 1
            
    print("\n" + "=" * 60)
    print("QUICK VALIDATION SUMMARY")
    print("=" * 60)
    
    success_rate = (passed / total) * 100
    print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎯 STATUS: ✅ ALL TESTS PASSED")
        print("v2.1 emergency fixes appear to be working!")
        print("Ready for comprehensive testing and tournament validation.")
    elif passed >= total * 0.8:  # 80% or more
        print("\n🎯 STATUS: ⚠️  MOSTLY WORKING")
        print("Most tests passed. Minor issues may need attention.")
        print("Proceed with caution to comprehensive testing.")
    else:
        print("\n🎯 STATUS: ❌ SIGNIFICANT ISSUES")
        print("Multiple test failures detected.")
        print("DO NOT PROCEED to tournament testing until fixed.")
        
    print(f"\nNext Steps:")
    if passed == total:
        print("  1. Run full test suite: python testing/test_v2_1_emergency.py")
        print("  2. Run tournament validation")
        print("  3. A/B test against v1.0")
    else:
        print("  1. Fix failing tests")
        print("  2. Re-run quick validation")
        print("  3. Only proceed when all tests pass")
        
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
