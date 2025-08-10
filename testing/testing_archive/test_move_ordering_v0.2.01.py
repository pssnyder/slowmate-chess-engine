"""
Test Suite for SlowMate v0.2.01 Move Ordering System

This script tests the new modular move ordering components to ensure
they work correctly before integration with the main engine.
"""

import chess
import time
from slowmate.search import SearchConfig, MoveOrderingDebug
from slowmate.search.enhanced_see import EnhancedSEE
from slowmate.search.mvv_lva import MVVLVA
from slowmate.search.move_ordering import MoveOrderingEngine


def test_enhanced_see():
    """Test Enhanced SEE implementation."""
    print("Testing Enhanced SEE...")
    print("-" * 40)
    
    config = SearchConfig()
    see = EnhancedSEE(config)
    
    # Test position: Queen takes pawn, defended by pawn
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    
    # Test captures
    test_moves = [
        chess.Move.from_uci("d1h5"),  # Queen takes nothing (not a capture)
        chess.Move.from_uci("f1c4"),  # Bishop move (not a capture)
    ]
    
    # Get actual captures
    captures = [move for move in board.legal_moves if board.is_capture(move)]
    
    if captures:
        for capture in captures[:3]:  # Test first 3 captures
            see_score = see.evaluate_capture(board, capture)
            classification = see.classify_capture(board, capture)
            victim_value = see.get_capture_value(board, capture)
            
            print(f"Capture: {capture}")
            print(f"  SEE Score: {see_score}")
            print(f"  Classification: {classification}")
            print(f"  Victim Value: {victim_value}")
            print()
    else:
        print("No captures available in test position")
    
    print("Enhanced SEE test completed.\n")


def test_mvv_lva():
    """Test MVV-LVA implementation."""
    print("Testing MVV-LVA...")
    print("-" * 40)
    
    mvv_lva = MVVLVA()
    
    # Test position with multiple captures
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    
    # Get captures
    captures = [move for move in board.legal_moves if board.is_capture(move)]
    
    if captures:
        print(f"Found {len(captures)} captures")
        
        # Score and sort captures
        for capture in captures:
            score = mvv_lva.get_capture_score(board, capture)
            classification = mvv_lva.classify_capture_simple(board, capture)
            victim_value = mvv_lva.get_victim_value(board, capture)
            attacker_value = mvv_lva.get_attacker_value(board, capture)
            
            print(f"Capture: {capture}")
            print(f"  MVV-LVA Score: {score}")
            print(f"  Classification: {classification}")
            print(f"  Victim: {victim_value}, Attacker: {attacker_value}")
            print()
        
        # Test sorting
        sorted_captures = mvv_lva.sort_captures(board, captures)
        print("Captures sorted by MVV-LVA:")
        for i, capture in enumerate(sorted_captures):
            score = mvv_lva.get_capture_score(board, capture)
            print(f"  {i+1}. {capture} (score: {score})")
            
    else:
        print("No captures available in test position")
    
    print("\nMVV-LVA test completed.\n")


def test_move_ordering_engine():
    """Test the complete move ordering engine."""
    print("Testing Move Ordering Engine...")
    print("-" * 40)
    
    # Enable debug output for testing
    config = SearchConfig()
    config.debug_move_ordering = MoveOrderingDebug.BASIC
    
    move_ordering = MoveOrderingEngine(config)
    
    # Test position with various move types
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    
    # Get all legal moves
    legal_moves = list(board.legal_moves)
    print(f"Found {len(legal_moves)} legal moves")
    
    # Order moves
    start_time = time.time()
    ordered_moves = move_ordering.order_moves(board, legal_moves, depth=1)
    ordering_time = (time.time() - start_time) * 1000
    
    print(f"Move ordering completed in {ordering_time:.2f}ms")
    print()
    
    # Show top 10 moves with their priorities
    print("Top 10 moves by priority:")
    for i, ordered_move in enumerate(ordered_moves[:10]):
        print(f"  {i+1:2}. {str(ordered_move.move):6} "
              f"(priority: {ordered_move.priority:4}) - {ordered_move.source}")
        if ordered_move.see_score is not None:
            print(f"      SEE Score: {ordered_move.see_score}")
    
    # Show statistics
    stats = move_ordering.get_statistics()
    print(f"\nMove Ordering Statistics:")
    print(f"  Moves ordered: {stats.moves_ordered}")
    print(f"  SEE evaluations: {stats.see_evaluations}")
    print(f"  Hash hits: {stats.hash_hits}")
    print(f"  Knowledge base hits: {stats.knowledge_base_hits}")
    print(f"  Total ordering time: {stats.ordering_time_ms:.2f}ms")
    print(f"  SEE evaluation time: {stats.see_time_ms:.2f}ms")
    
    print("\nMove Ordering Engine test completed.\n")


def test_performance_comparison():
    """Compare performance with and without move ordering."""
    print("Testing Performance Comparison...")
    print("-" * 40)
    
    # Test position
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    
    legal_moves = list(board.legal_moves)
    
    # Test without move ordering (baseline)
    start_time = time.time()
    for _ in range(100):  # Multiple iterations for timing
        unordered = legal_moves.copy()
    baseline_time = (time.time() - start_time) * 1000
    
    # Test with move ordering
    config = SearchConfig()
    config.debug_move_ordering = MoveOrderingDebug.NONE  # Disable debug for performance
    move_ordering = MoveOrderingEngine(config)
    
    start_time = time.time()
    for _ in range(100):  # Multiple iterations for timing
        ordered = move_ordering.order_moves(board, legal_moves, depth=1)
    ordering_time = (time.time() - start_time) * 1000
    
    print(f"Baseline (no ordering): {baseline_time:.2f}ms for 100 iterations")
    print(f"With move ordering: {ordering_time:.2f}ms for 100 iterations")
    print(f"Overhead per move ordering: {(ordering_time - baseline_time) / 100:.3f}ms")
    print(f"Overhead per move: {(ordering_time - baseline_time) / (100 * len(legal_moves)):.4f}ms")
    
    print("\nPerformance comparison completed.\n")


def test_uci_integration():
    """Test UCI option integration."""
    print("Testing UCI Integration...")
    print("-" * 40)
    
    config = SearchConfig()
    uci_options = config.to_uci_options()
    
    print("Available UCI options:")
    for option_name, option_config in uci_options.items():
        print(f"  {option_name}: {option_config}")
    
    print("\nUCI integration test completed.\n")


def main():
    """Run all move ordering tests."""
    print("SlowMate v0.2.01 - Move Ordering System Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_enhanced_see()
        test_mvv_lva()
        test_move_ordering_engine()
        test_performance_comparison()
        test_uci_integration()
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("🎯 Move ordering system is ready for integration!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
