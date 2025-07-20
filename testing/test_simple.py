#!/usr/bin/env python3
"""Very simple test for depth search to identify hanging issues."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess

def test_simple():
    """Test with very simple position and shallow depth."""
    print("=== Simple Depth Search Test ===")
    
    # Create engine with very conservative settings
    engine = DepthIntelligentSlowMateEngine()
    engine.configure_search(
        max_depth=2,  # Very shallow
        enable_iterative_deepening=False,  # Skip iterative deepening
        enable_quiescence=False,  # Skip quiescence
        enable_move_ordering=False  # Skip move ordering
    )
    
    # Set a very simple endgame position
    engine.board.set_fen("8/8/8/8/8/k7/8/K7 w - - 0 1")  # Just two kings
    
    print("Position set: Two kings only")
    print("Max depth: 2, No iterative deepening, No quiescence, No move ordering")
    
    try:
        print("Starting search...")
        best_move, score, pv = engine.search_best_move()
        print(f"✅ Search completed!")
        print(f"Best move: {best_move}")
        print(f"Score: {score}")
        
        stats = engine.get_search_stats()
        print(f"Nodes evaluated: {stats['nodes_evaluated']}")
        print(f"Max depth reached: {stats['max_depth_reached']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple()
