#!/usr/bin/env python3
"""
Test enhanced UCI integration for Nibbler compatibility.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess

def uci_callback(info_string):
    """Mock UCI callback to capture engine output."""
    print(f"UCI: {info_string}")

def test_enhanced_uci():
    """Test enhanced UCI output for Nibbler."""
    print("=== Enhanced UCI Integration Test ===")
    
    # Create engine with UCI callback
    engine = DepthIntelligentSlowMateEngine()
    engine.set_uci_callback(uci_callback)
    
    # Configure for testing
    engine.configure_search(
        max_depth=4,
        enable_alpha_beta=True,
        enable_move_ordering=True,
        enable_debug_info=True
    )
    
    print("\n--- Starting Position Analysis ---")
    print("Engine will provide enhanced UCI info...")
    
    # Run search and capture UCI output
    best_move, score, pv = engine.search_best_move()
    
    print(f"\n--- Search Results ---")
    print(f"Best Move: {best_move}")
    print(f"Score: {score}")
    print(f"Principal Variation: {' '.join(str(move) for move in pv[:5])}")
    
    # Show comprehensive stats
    stats = engine.get_search_stats()
    print(f"\n--- Performance Metrics ---")
    print(f"Nodes: {stats['nodes_evaluated']:,}")
    print(f"Time: {stats['search_time_seconds']:.3f}s")
    print(f"NPS: {stats['nodes_per_second']:,}")
    print(f"Pruning Efficiency: {stats['pruning_efficiency_percent']:.1f}%")
    print(f"Branching Factor: {stats['effective_branching_factor']:.2f}")
    
    return True

if __name__ == "__main__":
    try:
        test_enhanced_uci()
        print("\n✅ Enhanced UCI integration test completed!")
        print("\nReady for Nibbler engine vs engine testing!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
