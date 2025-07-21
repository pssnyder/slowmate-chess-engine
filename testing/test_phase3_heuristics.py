#!/usr/bin/env python3
"""
Phase 3 Test Suite for SlowMate v0.2.01
Tests killer moves, history heuristic, and counter moves.
"""

import chess
import time
from typing import List, Dict, Any
from slowmate.search.integration import SearchIntegration
from slowmate.search import SearchConfig

def test_killer_moves():
    """Test killer move heuristic."""
    print("Testing Killer Move Heuristic...")
    print("-" * 40)
    
    config = SearchConfig()
    config.enable_killer_moves = True
    config.enable_history_heuristic = False
    config.enable_counter_moves = False
    
    integration = SearchIntegration(config)
    
    # Create a test position
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
    
    # Store some killer moves at different depths
    killer1 = chess.Move.from_uci("f3g5")  # Knight move
    killer2 = chess.Move.from_uci("g1f3")  # Another knight move
    
    # Simulate storing killers from search
    integration.move_ordering.store_killer_move(killer1, 3, board)
    integration.move_ordering.store_killer_move(killer2, 3, board)
    
    # Test move ordering with killers
    ordered_moves = integration.get_ordered_moves(board, 3)
    
    print(f"Found {len(ordered_moves)} moves")
    
    # Check if killers are prioritized
    killer_positions = []
    for i, move in enumerate(ordered_moves[:10]):
        if move == killer1 or move == killer2:
            killer_positions.append((move, i))
    
    print("Killer move positions:")
    for move, pos in killer_positions:
        print(f"  {move}: position {pos + 1}")
    
    # Get killer statistics
    killer_stats = integration.get_killer_statistics()
    print(f"Killer statistics: {killer_stats}")
    
    print("Killer move test completed.\n")

def test_history_heuristic():
    """Test history heuristic."""
    print("Testing History Heuristic...")
    print("-" * 40)
    
    config = SearchConfig()
    config.enable_killer_moves = False
    config.enable_history_heuristic = True
    config.enable_counter_moves = False
    
    integration = SearchIntegration(config)
    
    # Create a test position
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
    
    # Simulate successful moves in history
    successful_moves = [
        chess.Move.from_uci("f3g5"),
        chess.Move.from_uci("c4d5"),
        chess.Move.from_uci("e1g1")  # Castling
    ]
    
    # Record successful moves at various depths
    for move in successful_moves:
        for depth in range(1, 6):
            integration.move_ordering.update_history(move, depth, True, success=True)
    
    # Record some unsuccessful moves
    unsuccessful_moves = [
        chess.Move.from_uci("h2h3"),
        chess.Move.from_uci("a2a3")
    ]
    
    for move in unsuccessful_moves:
        integration.move_ordering.update_history(move, 2, True, success=False)
    
    # Test move ordering with history
    ordered_moves = integration.get_ordered_moves(board, 4)
    
    print(f"Found {len(ordered_moves)} moves")
    
    # Check history influence
    history_moves = []
    for i, move in enumerate(ordered_moves[:15]):
        if move in successful_moves:
            history_moves.append((move, i))
    
    print("History-influenced move positions:")
    for move, pos in history_moves:
        print(f"  {move}: position {pos + 1}")
    
    # Get history statistics
    history_stats = integration.get_history_statistics()
    print(f"History statistics: {history_stats}")
    
    print("History heuristic test completed.\n")

def test_counter_moves():
    """Test counter move heuristic."""
    print("Testing Counter Move Heuristic...")
    print("-" * 40)
    
    config = SearchConfig()
    config.enable_killer_moves = False
    config.enable_history_heuristic = False
    config.enable_counter_moves = True
    
    integration = SearchIntegration(config)
    
    # Create a test position
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
    
    # Simulate opponent moves and our counter moves
    opponent_moves = [
        chess.Move.from_uci("c6d4"),  # Knight attack
        chess.Move.from_uci("f6g4"),  # Knight attack
        chess.Move.from_uci("c5b4")   # Bishop move
    ]
    
    counter_moves = [
        chess.Move.from_uci("f3d4"),  # Capture attacking knight
        chess.Move.from_uci("h2h3"),  # Attack knight
        chess.Move.from_uci("a2a3")   # Attack bishop
    ]
    
    # Store counter moves
    for opp_move, counter in zip(opponent_moves, counter_moves):
        for _ in range(3):  # Store multiple times to build confidence
            integration.move_ordering.store_counter_move(opp_move, counter, success=True)
    
    # Test counter move retrieval
    for opp_move, expected_counter in zip(opponent_moves, counter_moves):
        if integration.move_ordering.counter_moves:
            counter_info = integration.move_ordering.counter_moves.get_counter(opp_move)
            if counter_info:
                actual_counter, confidence = counter_info
                print(f"Opponent: {opp_move} -> Counter: {actual_counter} (confidence: {confidence})")
    
    # Get counter move statistics
    counter_stats = integration.get_counter_statistics()
    print(f"Counter move statistics: {counter_stats}")
    
    print("Counter move test completed.\n")

def test_integrated_heuristics():
    """Test all heuristics working together."""
    print("Testing Integrated Heuristics...")
    print("-" * 40)
    
    config = SearchConfig()
    config.enable_killer_moves = True
    config.enable_history_heuristic = True
    config.enable_counter_moves = True
    config.enable_transposition_table = True
    
    integration = SearchIntegration(config)
    
    # Create a tactical position
    board = chess.Board("r1bq1rk1/ppp2ppp/2n5/3P4/2B5/8/PPP2PPP/RNBQK2R w KQ - 0 1")
    
    # Start a new search
    integration.start_new_search()
    
    # Simulate some search activity
    moves_to_test = list(board.legal_moves)[:10]
    
    for move in moves_to_test:
        # Simulate recording search results
        integration.record_search_result(
            move=move,
            board=board,
            depth=4,
            caused_cutoff=(move.to_square in [chess.C6, chess.D6, chess.E6]),  # Simulate some cutoffs
            last_opponent_move=chess.Move.from_uci("g8h8") if move != moves_to_test[0] else None
        )
    
    # Test move ordering with all heuristics
    start_time = time.time()
    ordered_moves = integration.get_ordered_moves(board, 4)
    ordering_time = time.time() - start_time
    
    print(f"Ordered {len(ordered_moves)} moves in {ordering_time*1000:.2f}ms")
    
    # Show top moves
    print("Top 10 moves with all heuristics:")
    for i, move in enumerate(ordered_moves[:10]):
        print(f"  {i+1:2d}. {str(move):5s}")
    
    # Get comprehensive statistics
    all_stats = integration.get_all_heuristic_stats()
    
    print("\nComprehensive Statistics:")
    for category, stats in all_stats.items():
        if stats:
            print(f"  {category.title()}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")
    
    print("Integrated heuristics test completed.\n")

def test_performance_comparison():
    """Compare performance with and without heuristics."""
    print("Testing Performance Impact...")
    print("-" * 40)
    
    # Test without heuristics
    config_basic = SearchConfig()
    config_basic.enable_killer_moves = False
    config_basic.enable_history_heuristic = False
    config_basic.enable_counter_moves = False
    config_basic.enable_transposition_table = False
    
    integration_basic = SearchIntegration(config_basic)
    
    # Test with all heuristics
    config_full = SearchConfig()
    config_full.enable_killer_moves = True
    config_full.enable_history_heuristic = True
    config_full.enable_counter_moves = True
    config_full.enable_transposition_table = True
    
    integration_full = SearchIntegration(config_full)
    
    # Test position
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
    
    # Basic ordering performance
    iterations = 100
    
    start_time = time.time()
    for _ in range(iterations):
        integration_basic.get_ordered_moves(board, 4)
    basic_time = time.time() - start_time
    
    # Full heuristics performance
    start_time = time.time()
    for _ in range(iterations):
        integration_full.get_ordered_moves(board, 4)
    full_time = time.time() - start_time
    
    print(f"Basic ordering: {basic_time*1000:.2f}ms for {iterations} iterations")
    print(f"Full heuristics: {full_time*1000:.2f}ms for {iterations} iterations")
    print(f"Overhead: {((full_time - basic_time) / basic_time * 100):.1f}%")
    print(f"Per-move overhead: {((full_time - basic_time) / iterations)*1000:.3f}ms")
    
    print("Performance comparison completed.\n")

def test_uci_configuration():
    """Test UCI configuration of new heuristics."""
    print("Testing UCI Configuration...")
    print("-" * 40)
    
    config = SearchConfig()
    uci_options = config.to_uci_options()
    
    print("Available UCI options for Phase 3:")
    heuristic_options = {
        k: v for k, v in uci_options.items() 
        if any(term in k.lower() for term in ['killer', 'history', 'counter'])
    }
    
    for option, details in heuristic_options.items():
        print(f"  {option}: {details}")
    
    print("UCI configuration test completed.\n")

if __name__ == "__main__":
    print("SlowMate v0.2.01 - Phase 3 Heuristics Test Suite")
    print("=" * 60)
    
    test_killer_moves()
    test_history_heuristic()
    test_counter_moves()
    test_integrated_heuristics()
    test_performance_comparison()
    test_uci_configuration()
    
    print("=" * 60)
    print("✅ All Phase 3 tests completed successfully!")
    print("🚀 Advanced heuristics are ready for integration!")
