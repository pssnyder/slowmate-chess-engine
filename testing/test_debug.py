#!/usr/bin/env python3
"""Debug the hanging issue by testing specific components."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess

def test_debug_hanging():
    """Debug what's causing the hanging."""
    print("=== Debug Hanging Issue ===")
    
    engine = DepthIntelligentSlowMateEngine()
    engine.configure_search(max_depth=1, enable_iterative_deepening=False)
    
    # Test 1: Simple position
    print("\n--- Test 1: Simple Position (depth 1) ---")
    engine.board.set_fen("8/8/8/8/8/k7/8/K7 w - - 0 1")
    try:
        best_move, score, pv = engine.search_best_move()
        print(f"✅ Simple position: {best_move}, score: {score}")
        stats = engine.get_search_stats()
        print(f"Nodes: {stats['nodes_evaluated']}, Depth: {stats['max_depth_reached']}")
    except Exception as e:
        print(f"❌ Simple position failed: {e}")
    
    # Test 2: Starting position with depth 1
    print("\n--- Test 2: Starting Position (depth 1) ---")
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    engine.stats.reset()  # Reset stats for clear reading
    
    try:
        print("Starting search on full board...")
        best_move, score, pv = engine.search_best_move()
        print(f"✅ Starting position: {best_move}, score: {score}")
        stats = engine.get_search_stats()
        print(f"Nodes: {stats['nodes_evaluated']}, Depth: {stats['max_depth_reached']}")
    except Exception as e:
        print(f"❌ Starting position failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test the _minimax method directly
    print("\n--- Test 3: Direct _minimax call ---")
    engine.board.set_fen("8/8/8/8/8/k7/8/K7 w - - 0 1")
    engine.stats.reset()
    
    try:
        print("Testing direct _minimax call...")
        score, pv = engine._minimax(1, float('-inf'), float('inf'), True)
        print(f"✅ Direct minimax: score: {score}, pv: {pv}")
        print(f"Nodes: {engine.stats.nodes_evaluated}")
    except Exception as e:
        print(f"❌ Direct minimax failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_hanging()
