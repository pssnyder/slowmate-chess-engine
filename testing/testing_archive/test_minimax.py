#!/usr/bin/env python3
"""Quick test for unified minimax implementation."""

from slowmate.depth_search import DepthIntelligentSlowMateEngine

def test_unified_minimax():
    """Test unified minimax with and without alpha-beta."""
    
    print("=== Testing Unified Minimax Implementation ===")
    
    # Test 1: With alpha-beta pruning (default)
    print("\n--- Test 1: Alpha-Beta Enabled ---")
    engine_ab = DepthIntelligentSlowMateEngine()
    engine_ab.configure_search(enable_alpha_beta=True, max_depth=3)
    
    best_move_ab, score_ab, pv_ab = engine_ab.search_best_move()
    stats_ab = engine_ab.get_search_stats()
    
    print(f"✅ Alpha-beta search completed")
    print(f"Best move: {best_move_ab}, Score: {score_ab}")
    print(f"Nodes: {stats_ab['nodes_evaluated']}")
    print(f"Alpha-beta cutoffs: {stats_ab['alpha_beta_cutoffs']}")
    print(f"Max depth reached: {stats_ab['max_depth_reached']}")
    
    # Test 2: Without alpha-beta pruning
    print("\n--- Test 2: Alpha-Beta Disabled ---")
    engine_basic = DepthIntelligentSlowMateEngine()
    engine_basic.configure_search(enable_alpha_beta=False, max_depth=3)
    
    best_move_basic, score_basic, pv_basic = engine_basic.search_best_move()
    stats_basic = engine_basic.get_search_stats()
    
    print(f"✅ Basic minimax search completed")
    print(f"Best move: {best_move_basic}, Score: {score_basic}")
    print(f"Nodes: {stats_basic['nodes_evaluated']}")
    print(f"Alpha-beta cutoffs: {stats_basic['alpha_beta_cutoffs']} (should be 0)")
    print(f"Max depth reached: {stats_basic['max_depth_reached']}")
    
    # Test 3: Compare node counts (alpha-beta should be more efficient)
    print("\n--- Performance Comparison ---")
    print(f"Alpha-beta nodes: {stats_ab['nodes_evaluated']}")
    print(f"Basic minimax nodes: {stats_basic['nodes_evaluated']}")
    
    if stats_ab['nodes_evaluated'] <= stats_basic['nodes_evaluated']:
        print("✅ Alpha-beta pruning is working (fewer or equal nodes)")
    else:
        print("⚠️ Alpha-beta used more nodes than basic minimax")
    
    # Test 4: Verify same best move (should be identical for same position)
    if best_move_ab == best_move_basic:
        print("✅ Both algorithms found the same best move")
    else:
        print(f"⚠️ Different moves: AB={best_move_ab}, Basic={best_move_basic}")
    
    return True

if __name__ == "__main__":
    test_unified_minimax()
    print("\n✅ Unified minimax implementation test completed!")
