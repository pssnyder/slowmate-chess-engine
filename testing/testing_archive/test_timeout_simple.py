#!/usr/bin/env python3
"""
Simple timeout test for depth search - verify timeout mechanisms work.
"""

import sys
import os
import time

# Add the slowmate package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess

def test_timeout_mechanism():
    """Test that timeout actually works."""
    print("=== Testing Timeout Mechanism ===")
    
    engine = DepthIntelligentSlowMateEngine()
    
    # Use a simpler position first
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # Test with very short timeout
    print("Testing 1-second timeout...")
    start_time = time.time()
    
    try:
        best_move, score, pv = engine.search_best_move(time_limit=1.0)
        elapsed = time.time() - start_time
        
        print(f"✅ Completed in {elapsed:.3f}s")
        print(f"Move: {best_move}, Score: {score}")
        
        stats = engine.get_search_stats()
        print(f"Nodes: {stats['nodes_evaluated']}, Depth: {stats['max_depth_reached']}")
        
        if elapsed > 1.5:  # Allow some margin
            print("❌ TIMEOUT NOT WORKING - took too long!")
            return False
        else:
            print("✅ Timeout mechanism working")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("SlowMate Timeout Test")
    print("=" * 30)
    
    success = test_timeout_mechanism()
    
    if success:
        print("\n✅ Timeout test passed!")
    else:
        print("\n❌ Timeout test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
