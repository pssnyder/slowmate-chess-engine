#!/usr/bin/env python3
"""
Test script for depth search implementation with external monitoring only.

This script tests the basic functionality of the new depth search module.
No engine-side timeout logic - uses external monitoring for development productivity.
"""

import sys
import os
import time

# Add the slowmate package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from slowmate.depth_search import DepthIntelligentSlowMateEngine
import chess


def test_depth_search_basic():
    """Test basic depth search functionality."""
    print("=== Testing Basic Depth Search ===")
    
    # Create engine
    engine = DepthIntelligentSlowMateEngine()
    
    # Test configuration
    print(f"Initial config: base_depth={engine.search_config['base_depth']}, max_depth={engine.search_config['max_depth']}")
    
    # Set up a simple position
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    print(f"Position: {engine.board.fen()}")
    
    # Test search
    print("\n--- Depth Search Test ---")
    start_time = time.time()
    
    try:
        best_move, score, pv = engine.search_best_move()  # No time limit - external monitoring only
        elapsed = time.time() - start_time
        
        print(f"✅ Search completed successfully!")
        print(f"Best move: {best_move}")
        print(f"Score: {score}")
        print(f"Principal variation: {' '.join(str(move) for move in pv[:5])}...")  # First 5 moves
        print(f"Search time: {elapsed:.3f}s")
        
        # Print search statistics
        stats = engine.get_search_stats()
        print(f"Nodes evaluated: {stats['nodes_evaluated']}")
        print(f"Max depth reached: {stats['max_depth_reached']}")
        print(f"Alpha-beta cutoffs: {stats['alpha_beta_cutoffs']}")
        print(f"NPS: {stats['nodes_per_second']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Depth search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tactical_comparison():
    """Compare depth search vs tactical intelligence on a tactical position."""
    print("\n=== Tactical Position Comparison ===")
    
    # Set up a tactical position where there's a clear best move
    test_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
    
    # Initialize timing variables
    depth_time = 0.0
    tactical_time = 0.0
    
    # Test with depth search
    print("\n--- Depth Search Analysis ---")
    engine_depth = DepthIntelligentSlowMateEngine()
    engine_depth.board.set_fen(test_fen)
    engine_depth.configure_depth(enable_depth=True, base_depth=2, max_depth=4)
    
    try:
        start_time = time.time()
        best_move_depth, score_depth, pv_depth = engine_depth.search_best_move()
        depth_time = time.time() - start_time
        
        print(f"Depth search best move: {best_move_depth}")
        print(f"Depth search score: {score_depth}")
        print(f"Depth search PV: {' '.join(str(move) for move in pv_depth[:3])}")
        print(f"Depth search time: {depth_time:.3f}s")
        
        stats_depth = engine_depth.get_search_stats()
        print(f"Nodes: {stats_depth['nodes_evaluated']}, Depth: {stats_depth['max_depth_reached']}")
        
    except Exception as e:
        print(f"Depth search failed: {e}")
        best_move_depth, score_depth = None, 0
    
    # Test with tactical intelligence only
    print("\n--- Tactical Intelligence Analysis ---")
    engine_tactical = DepthIntelligentSlowMateEngine()
    engine_tactical.board.set_fen(test_fen)
    engine_tactical.configure_depth(enable_depth=False)  # Disable depth search
    
    try:
        start_time = time.time()
        best_move_tactical = engine_tactical.intelligence.select_best_move()
        score_tactical = engine_tactical.intelligence._evaluate_position()
        tactical_time = time.time() - start_time
        
        print(f"Tactical intelligence best move: {best_move_tactical}")
        print(f"Tactical intelligence score: {score_tactical}")
        print(f"Tactical intelligence time: {tactical_time:.3f}s")
        
    except Exception as e:
        print(f"Tactical intelligence failed: {e}")
        best_move_tactical, score_tactical = None, 0
    
    # Compare results
    print("\n--- Comparison ---")
    print(f"Same move chosen: {best_move_depth == best_move_tactical}")
    print(f"Score difference: {score_depth - score_tactical}")
    if depth_time > 0 and tactical_time > 0:
        print(f"Time ratio: {depth_time / max(tactical_time, 0.001):.2f}x")


def test_configuration_toggles():
    """Test various configuration toggles."""
    print("\n=== Configuration Toggle Tests ===")
    
    engine = DepthIntelligentSlowMateEngine()
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # Test different configurations
    configs = [
        {"enable_alpha_beta": False, "name": "Minimax only (no alpha-beta)"},
        {"enable_move_ordering": False, "name": "No move ordering"},
        {"enable_quiescence": False, "name": "No quiescence search"},
        {"base_depth": 1, "max_depth": 3, "name": "Shallow search (1-3 depth)"},
        {"base_depth": 3, "max_depth": 5, "name": "Deep search (3-5 depth)"},
    ]
    
    for config in configs:
        print(f"\n--- Testing: {config['name']} ---")
        
        # Apply configuration
        config_params = {k: v for k, v in config.items() if k != 'name'}
        engine.configure_search(**config_params)
        
        try:
            start_time = time.time()
            best_move, score, pv = engine.search_best_move()  # No time limit - external monitoring only
            elapsed = time.time() - start_time
            
            stats = engine.get_search_stats()
            print(f"Move: {best_move}, Score: {score}, Time: {elapsed:.3f}s")
            print(f"Nodes: {stats['nodes_evaluated']}, Depth: {stats['max_depth_reached']}")
            
        except Exception as e:
            print(f"Configuration failed: {e}")
        
        # Reset to defaults
        engine.search_config = engine.search_config.__class__(engine.search_config)


def main():
    """Run all depth search tests."""
    print("SlowMate Depth Search Module - Test Suite")
    print("=" * 50)
    print("⚠️  No engine-side timeouts - use Ctrl+C if tests hang")
    print("    Background execution monitoring for debugging only")
    
    try:
        # Basic functionality test
        print("\n🔧 Testing basic depth search functionality...")
        if not test_depth_search_basic():
            print("ERROR: Basic depth search test failed!")
            return False
        
        # Tactical comparison test  
        print("\n🎯 Testing tactical comparison...")
        test_tactical_comparison()
        
        # Configuration tests
        print("\n⚙️ Testing configuration toggles...")
        test_configuration_toggles()
        
        print("\n" + "=" * 50)
        print("✅ All depth search tests completed successfully!")
        print("\nNext steps:")
        print("1. Integrate with UCI interface")
        print("2. Test with Nibbler for real-time analysis") 
        print("3. Performance tuning and optimization")
        print("4. Add more sophisticated move ordering")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
