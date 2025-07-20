#!/usr/bin/env python3
"""
Test for engine-vs-engine compatibility with enhanced UCI output.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.depth_search import DepthSearchEngine

def test_nibbler_compatibility():
    """Test engine compatibility for Nibbler GUI and engine-vs-engine tournaments."""
    print("=== Nibbler/Engine-vs-Engine Compatibility Test ===\n")
    
    # Create depth search engine with enhanced UCI
    engine = DepthSearchEngine()
    
    # Configure for realistic depth with enhanced output
    engine.configure_search(
        max_depth=4,
        enable_alpha_beta=True,
        enable_move_ordering=True,
        enable_quiescence=False,  # Keep simple for testing
        enable_iterative_deepening=True,
        enable_debug_info=True  # Enhanced UCI output
    )
    
    print("--- Test Position: Starting Position ---")
    print("Engine Configuration:")
    print(f"  Max Depth: {engine.search_config['max_depth']}")
    print(f"  Alpha-Beta: {engine.search_config['enable_alpha_beta']}")
    print(f"  Move Ordering: {engine.search_config['enable_move_ordering']}")
    print(f"  Iterative Deepening: {engine.search_config['enable_iterative_deepening']}")
    print(f"  Debug UCI Info: {engine.search_config['enable_debug_info']}")
    
    # Perform search with rich UCI output
    print("\n--- Search with Enhanced UCI Output ---")
    best_move, score, pv = engine.search_best_move()
    
    print(f"\nFinal Results:")
    print(f"  Best Move: {best_move}")
    print(f"  Score: {score}")
    print(f"  Principal Variation: {' '.join(str(m) for m in pv)}")
    
    # Display engine identification
    engine_info = engine.get_engine_info()
    print(f"\n--- Engine Identification ---")
    print(f"Name: {engine_info['name']}")
    print(f"Version: {engine_info['version']}")
    print(f"Features: {', '.join(engine_info['features'])}")
    
    # Test different position
    print("\n--- Test Position: Sicilian Defense ---")
    engine.board.push(chess.Move.from_uci("e2e4"))
    engine.board.push(chess.Move.from_uci("c7c5"))
    
    best_move, score, pv = engine.search_best_move()
    print(f"Best Move: {best_move}")
    print(f"Score: {score}")
    
    print("\n=== Nibbler Compatibility Test Complete ===")

if __name__ == "__main__":
    test_nibbler_compatibility()
