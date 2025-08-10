#!/usr/bin/env python3
"""
Simple UCI output test - focused on basic depth search without tactical intelligence.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.depth_search import DepthSearchEngine

def test_simple_uci():
    """Test basic UCI output without tactical intelligence complexity."""
    print("=== Simple UCI Output Test ===\n")
    
    # Create basic depth search engine
    engine = DepthSearchEngine()
    
    # Configure for speed
    engine.configure_search(
        max_depth=2,  # Very shallow for speed
        enable_alpha_beta=True,
        enable_move_ordering=True,
        enable_quiescence=False,  # Disable quiescence for simplicity
        enable_iterative_deepening=False  # Disable for speed
    )
    
    # Test from starting position
    print("--- Starting Position (Depth 2) ---")
    best_move, score, pv = engine.search_best_move()
    
    print(f"\nSearch Results:")
    print(f"  Best Move: {best_move}")
    print(f"  Score: {score}")
    print(f"  Principal Variation: {' '.join(str(m) for m in pv)}")
    
    # Get and display search statistics
    stats = engine.get_search_stats()
    print(f"\nSearch Statistics:")
    print(f"  Nodes Evaluated: {stats['nodes_evaluated']:,}")
    print(f"  Max Depth: {stats['max_depth_reached']}")
    print(f"  Alpha-Beta Cutoffs: {stats['alpha_beta_cutoffs']}")
    print(f"  Search Time: {stats['search_time_seconds']:.3f}s")
    print(f"  Nodes/Second: {stats['nodes_per_second']:,}")
    print(f"  Pruning Efficiency: {stats['pruning_efficiency_percent']:.1f}%")
    
    # Test engine info
    engine_info = engine.get_engine_info()
    print(f"\nEngine Info:")
    print(f"  Name: {engine_info['name']}")
    print(f"  Version: {engine_info['version']}")
    print(f"  Description: {engine_info['description']}")
    
    # Test search summary
    print("\n--- Search Summary ---")
    engine.print_search_summary()
    
    print("\n=== Simple UCI Test Complete ===")

if __name__ == "__main__":
    test_simple_uci()
