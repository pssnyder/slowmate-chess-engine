#!/usr/bin/env python3
"""Test iterative deepening specifically."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess

def test_iterative_deepening():
    """Test iterative deepening with different configurations."""
    print("=== Test Iterative Deepening ===")
    
    # Test with iterative deepening on simple position
    engine = DepthIntelligentSlowMateEngine()
    engine.configure_search(
        max_depth=3,  # Reasonable depth
        enable_iterative_deepening=True,
        enable_quiescence=False,  # Disable to avoid hanging
        enable_move_ordering=False  # Simplify
    )
    
    engine.board.set_fen("8/8/8/8/8/k7/8/K7 w - - 0 1")
    print("Simple position, max_depth=3, iterative deepening enabled")
    
    try:
        best_move, score, pv = engine.search_best_move()
        print(f"✅ Iterative deepening completed")
        print(f"Best move: {best_move}, Score: {score}")
        
        stats = engine.get_search_stats()
        print(f"Nodes: {stats['nodes_evaluated']}")
        print(f"Max depth reached: {stats['max_depth_reached']}")
        print(f"Alpha-beta cutoffs: {stats['alpha_beta_cutoffs']}")
        
    except Exception as e:
        print(f"❌ Iterative deepening failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_iterative_deepening()
