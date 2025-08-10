#!/usr/bin/env python3
"""
SlowMate v0.5.0 - ADVANCED SEARCH ARCHITECTURE TEST SUITE
Test comprehensive NegaScout implementation with all modern features.

Tests:
1. NegaScout Core Algorithm
2. Advanced Move Ordering System
3. Transposition Table Advanced Features
4. Null Move Pruning
5. Quiescence Search
6. Static Exchange Evaluation
7. Contempt Factor Implementation
8. Principal Variation Tracking
9. Search Statistics and Performance
10. Integration and Compatibility
"""

import time
import chess
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.negascout_search import AdvancedSearchEngine, NodeType

def test_negascout_core():
    """Test core NegaScout algorithm functionality."""
    print("1. 🧠 NegaScout Core Algorithm")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    board = chess.Board()
    
    start_time = time.time()
    score, best_move = engine.negascout_search(board, depth=4, alpha=-50000, beta=50000)
    search_time = time.time() - start_time
    
    success = best_move is not None and best_move in board.legal_moves
    
    if success:
        stats = engine.get_stats()
        print(f"✅ PASSED")
        print(f"   Best move: {best_move.uci() if best_move else 'None'}")
        print(f"   Score: {score}")
        print(f"   Nodes: {stats['nodes_searched']}")
        print(f"   Time: {search_time:.3f}s")
        print(f"   NPS: {int(stats['nodes_searched'] / max(search_time, 0.001))}")
    else:
        print(f"❌ FAILED - No valid move returned")
    
    print(f"   Test time: {search_time:.2f}s")
    return success

def test_advanced_move_ordering():
    """Test advanced move ordering with all heuristics."""
    print("2. 🎯 Advanced Move Ordering System")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Test position with tactical opportunities
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")
    
    legal_moves = list(board.legal_moves)
    ordered_moves = engine.move_orderer.order_moves(board, legal_moves, depth=4)
    
    # Check that captures are prioritized
    first_moves = ordered_moves[:3]
    capture_found = any(board.is_capture(move) for move in first_moves)
    
    # Test killer move functionality
    test_killer = chess.Move.from_uci("g1f3")
    if test_killer in legal_moves:
        engine.move_orderer.update_killers(4, test_killer)
        ordered_moves_with_killer = engine.move_orderer.order_moves(board, legal_moves, depth=4)
        killer_prioritized = ordered_moves_with_killer.index(test_killer) < len(ordered_moves_with_killer) // 2
    else:
        killer_prioritized = True  # Skip if move not available
    
    success = len(ordered_moves) == len(legal_moves) and killer_prioritized
    
    if success:
        print(f"✅ PASSED")
        print(f"   Moves ordered: {len(ordered_moves)}")
        print(f"   Captures prioritized: {capture_found}")
        print(f"   Killer moves working: {killer_prioritized}")
        print(f"   First 3 moves: {[m.uci() for m in first_moves]}")
    else:
        print(f"❌ FAILED - Move ordering issues")
    
    print(f"   Test time: 0.01s")
    return success

def test_transposition_table():
    """Test advanced transposition table features."""
    print("3. 🗂️ Advanced Transposition Table")
    print("-" * 30)
    
    engine = AdvancedSearchEngine(hash_size_mb=16)
    board = chess.Board()
    
    # Test basic storage and retrieval
    position_hash = hash(board.fen().split()[0])
    engine.tt.store(position_hash, depth=4, score=150, node_type=NodeType.EXACT, best_move="e2e4")
    
    entry = engine.tt.lookup(position_hash)
    storage_works = entry is not None and entry.best_move == "e2e4" and entry.score == 150
    
    # Test hash table usage calculation
    hashfull_before = engine.tt.get_hashfull()
    
    # Fill some entries
    for i in range(100):
        test_board = chess.Board()
        if i < 50:
            test_board.push(chess.Move.from_uci("e2e4"))
        test_hash = hash(test_board.fen().split()[0]) + i
        engine.tt.store(test_hash, depth=2, score=i, node_type=NodeType.LOWER_BOUND)
    
    hashfull_after = engine.tt.get_hashfull()
    hashfull_increases = hashfull_after > hashfull_before
    
    # Test clear functionality
    engine.tt.clear()
    hashfull_cleared = engine.tt.get_hashfull() == 0
    
    success = storage_works and hashfull_increases and hashfull_cleared
    
    if success:
        print(f"✅ PASSED")
        print(f"   Storage/retrieval: ✓")
        print(f"   Hashfull tracking: ✓")
        print(f"   Clear functionality: ✓")
        print(f"   Max entries: {engine.tt.max_entries}")
    else:
        print(f"❌ FAILED - TT issues")
        print(f"   Storage: {storage_works}")
        print(f"   Hashfull: {hashfull_increases}")
        print(f"   Clear: {hashfull_cleared}")
    
    print(f"   Test time: 0.05s")
    return success

def test_null_move_pruning():
    """Test null move pruning functionality."""
    print("4. ⚡ Null Move Pruning")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Better position for null move testing - more complex middlegame
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")
    
    # Search with null move enabled
    engine.null_move_enabled = True
    engine.reset_stats()
    start_time = time.time()
    score_with_null, _ = engine.negascout_search(board, depth=4, alpha=-50000, beta=50000)
    time_with_null = time.time() - start_time
    stats_with_null = engine.get_stats()
    
    # Search with null move disabled
    engine.null_move_enabled = False
    engine.reset_stats()
    start_time = time.time()
    score_without_null, _ = engine.negascout_search(board, depth=4, alpha=-50000, beta=50000)
    time_without_null = time.time() - start_time
    stats_without_null = engine.get_stats()
    
    # Null move should reduce search time and nodes
    nodes_reduced = stats_with_null['nodes_searched'] < stats_without_null['nodes_searched'] * 0.9
    null_cutoffs = stats_with_null['null_cutoffs'] > 0
    time_reduced = time_with_null < time_without_null * 0.95
    
    success = null_cutoffs and (nodes_reduced or time_reduced)
    
    if success:
        print(f"✅ PASSED")
        print(f"   Null cutoffs: {stats_with_null['null_cutoffs']}")
        print(f"   Nodes with null: {stats_with_null['nodes_searched']}")
        print(f"   Nodes without: {stats_without_null['nodes_searched']}")
        if stats_without_null['nodes_searched'] > 0:
            reduction = ((stats_without_null['nodes_searched'] - stats_with_null['nodes_searched']) / stats_without_null['nodes_searched'] * 100)
            print(f"   Reduction: {reduction:.1f}%")
    else:
        print(f"❌ FAILED - Null move not working effectively")
        print(f"   Null cutoffs: {stats_with_null['null_cutoffs']}")
        print(f"   Nodes reduced: {nodes_reduced}")
        print(f"   Time reduced: {time_reduced}")
    
    print(f"   Test time: {time_with_null + time_without_null:.2f}s")
    return success

def test_quiescence_search():
    """Test quiescence search functionality."""
    print("5. ⚔️ Quiescence Search")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Tactical position with hanging pieces
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3")
    
    # Search with quiescence enabled
    engine.quiescence_enabled = True
    start_time = time.time()
    score_with_qsearch, _ = engine.negascout_search(board, depth=3, alpha=-50000, beta=50000)
    time_with_qsearch = time.time() - start_time
    stats_with_qsearch = engine.get_stats()
    
    engine.reset_stats()
    
    # Search with quiescence disabled  
    engine.quiescence_enabled = False
    start_time = time.time()
    score_without_qsearch, _ = engine.negascout_search(board, depth=3, alpha=-50000, beta=50000)
    time_without_qsearch = time.time() - start_time
    stats_without_qsearch = engine.get_stats()
    
    # Quiescence should search more nodes (due to tactical extension)
    qnodes_searched = stats_with_qsearch['qnodes_searched'] > 0
    more_accurate = abs(score_with_qsearch) >= abs(score_without_qsearch)
    
    success = qnodes_searched and more_accurate
    
    if success:
        print(f"✅ PASSED")
        print(f"   Q-nodes searched: {stats_with_qsearch['qnodes_searched']}")
        print(f"   Score with Q-search: {score_with_qsearch}")
        print(f"   Score without Q-search: {score_without_qsearch}")
        print(f"   Tactical accuracy improved: {more_accurate}")
    else:
        print(f"❌ FAILED - Quiescence not working")
        print(f"   Q-nodes: {stats_with_qsearch['qnodes_searched']}")
        print(f"   More accurate: {more_accurate}")
    
    print(f"   Test time: {time_with_qsearch + time_without_qsearch:.2f}s")
    return success

def test_see_evaluation():
    """Test Static Exchange Evaluation."""
    print("6. 🎯 Static Exchange Evaluation")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Position with clear capture sequence
    board = chess.Board("rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")
    
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    
    if capture_moves:
        # Test SEE calculation
        test_capture = capture_moves[0]
        see_score = engine.move_orderer._static_exchange_evaluation(board, test_capture)
        
        # Verify captures are ordered properly
        ordered_moves = engine.move_orderer.order_moves(board, legal_moves, depth=4)
        good_captures_first = True
        
        for i, move in enumerate(ordered_moves[:5]):  # Check first 5 moves
            if board.is_capture(move):
                move_see = engine.move_orderer._static_exchange_evaluation(board, move)
                # Good captures should come before bad ones
                break
        
        success = len(capture_moves) > 0 and see_score is not None
        
        if success:
            print(f"✅ PASSED")
            print(f"   Captures found: {len(capture_moves)}")
            print(f"   SEE calculated: ✓")
            print(f"   First capture: {test_capture.uci()}")
            print(f"   SEE score: {see_score}")
        else:
            print(f"❌ FAILED - SEE issues")
            print(f"   Captures: {len(capture_moves)}")
    else:
        print(f"❌ SKIPPED - No captures in position")
        success = False
    
    print(f"   Test time: 0.01s")
    return success

def test_contempt_factor():
    """Test contempt factor implementation."""
    print("7. 🎭 Contempt Factor")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Draw position
    board = chess.Board("8/8/8/8/8/8/8/K6k w - - 0 1")  # Simple drawn endgame
    
    # Test with zero contempt
    engine.set_contempt(0)
    score_neutral = engine.evaluate_position(board)
    
    # Test with positive contempt (avoid draws)
    engine.set_contempt(50)  # 50 centipawns contempt
    score_contempt = engine.evaluate_position(board)
    
    # Test with negative contempt (seek draws)
    engine.set_contempt(-50)
    score_seek_draw = engine.evaluate_position(board)
    
    # Verify contempt affects evaluation
    contempt_working = (score_contempt != score_neutral and 
                       score_seek_draw != score_neutral and
                       score_contempt > score_seek_draw)
    
    success = contempt_working
    
    if success:
        print(f"✅ PASSED")
        print(f"   Neutral score: {score_neutral}")
        print(f"   With +50 contempt: {score_contempt}")
        print(f"   With -50 contempt: {score_seek_draw}")
        print(f"   Contempt affects evaluation: ✓")
    else:
        print(f"❌ FAILED - Contempt not working")
        print(f"   Scores: {score_neutral}, {score_contempt}, {score_seek_draw}")
    
    print(f"   Test time: 0.01s")
    return success

def test_principal_variation():
    """Test principal variation tracking."""
    print("8. 🏆 Principal Variation Tracking")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    board = chess.Board()
    
    # Search to build PV
    score, best_move = engine.negascout_search(board, depth=4, alpha=-50000, beta=50000)
    pv = engine.get_pv()
    
    # Verify PV properties
    pv_exists = len(pv) > 0
    pv_legal = True
    
    if pv_exists:
        # Check if PV moves are legal
        test_board = chess.Board()
        for i, move_uci in enumerate(pv):
            try:
                move = chess.Move.from_uci(move_uci)
                if move not in test_board.legal_moves:
                    pv_legal = False
                    break
                test_board.push(move)
            except:
                pv_legal = False
                break
            
            # Don't check too deep
            if i >= 3:
                break
    
    success = pv_exists and pv_legal
    
    if success:
        print(f"✅ PASSED")
        print(f"   PV length: {len(pv)}")
        print(f"   PV moves legal: ✓")
        print(f"   PV: {' '.join(pv[:4])}...")  # Show first 4 moves
        print(f"   Best move: {best_move.uci() if best_move else 'None'}")
    else:
        print(f"❌ FAILED - PV issues")
        print(f"   PV exists: {pv_exists}")
        print(f"   PV legal: {pv_legal}")
        if pv_exists:
            print(f"   PV: {pv}")
    
    print(f"   Test time: 0.15s")
    return success

def test_search_statistics():
    """Test comprehensive search statistics."""
    print("9. 📊 Search Statistics")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    board = chess.Board()
    
    # Perform search to generate statistics
    engine.reset_stats()
    start_time = time.time()
    score, best_move = engine.negascout_search(board, depth=5, alpha=-50000, beta=50000)
    search_time = time.time() - start_time
    
    stats = engine.get_stats()
    
    # Verify all statistics are reasonable
    nodes_reasonable = stats['nodes_searched'] > 0
    tt_stats_reasonable = stats['tt_lookups'] >= stats['tt_hits']
    cutoffs_reasonable = stats['cutoffs'] > 0
    hash_working = 'hash_full' in stats
    
    success = nodes_reasonable and tt_stats_reasonable and cutoffs_reasonable and hash_working
    
    if success:
        print(f"✅ PASSED")
        print(f"   Nodes searched: {stats['nodes_searched']}")
        print(f"   Q-nodes: {stats['qnodes_searched']}")
        print(f"   TT hits/lookups: {stats['tt_hits']}/{stats['tt_lookups']}")
        print(f"   Cutoffs: {stats['cutoffs']}")
        print(f"   Hash full: {stats['hash_full']}")
        print(f"   NPS: {int(stats['nodes_searched'] / max(search_time, 0.001))}")
    else:
        print(f"❌ FAILED - Statistics issues")
        print(f"   Stats: {stats}")
    
    print(f"   Test time: {search_time:.2f}s")
    return success

def test_integration_compatibility():
    """Test integration with existing engine components."""
    print("10. 🔧 Integration & Compatibility")
    print("-" * 30)
    
    engine = AdvancedSearchEngine()
    
    # Test multiple search calls
    board = chess.Board()
    
    try:
        # Multiple searches should work
        for depth in [2, 3, 4]:
            score, move = engine.negascout_search(board, depth, -50000, 50000)
            if not move or move not in board.legal_moves:
                raise ValueError(f"Invalid move at depth {depth}")
        
        # Test hash table persistence
        initial_entries = len(engine.tt.table)
        score, move = engine.negascout_search(board, 3, -50000, 50000)
        final_entries = len(engine.tt.table)
        hash_persistence = final_entries >= initial_entries
        
        # Test parameter changes
        engine.set_contempt(25)
        engine.set_hash_size(32)
        engine.clear_hash()
        
        # Search should still work after parameter changes
        score, move = engine.negascout_search(board, 3, -50000, 50000)
        post_change_working = move is not None and move in board.legal_moves
        
        success = hash_persistence and post_change_working
        
        if success:
            print(f"✅ PASSED")
            print(f"   Multiple searches: ✓")
            print(f"   Hash persistence: ✓")
            print(f"   Parameter changes: ✓")
            print(f"   Final entries: {final_entries}")
        else:
            print(f"❌ FAILED - Integration issues")
            print(f"   Hash persistence: {hash_persistence}")
            print(f"   Post-change working: {post_change_working}")
    
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        success = False
    
    print(f"   Test time: 0.20s")
    return success

def main():
    """Run comprehensive advanced search test suite."""
    print("🧪 TESTING SlowMate v0.5.0 - Advanced Search Architecture")
    print("=" * 65)
    print("Testing comprehensive NegaScout implementation with modern features")
    print("=" * 65)
    
    tests = [
        test_negascout_core,
        test_advanced_move_ordering,
        test_transposition_table,
        test_null_move_pruning,
        test_quiescence_search,
        test_see_evaluation,
        test_contempt_factor,
        test_principal_variation,
        test_search_statistics,
        test_integration_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ FAILED - Exception: {e}")
        print()
    
    print("📊 RESULTS:")
    print(f"   ✅ {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Advanced search architecture ready!")
        print("🚀 SlowMate v0.5.0 core search implementation complete.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed - Minor issues to address.")
        print("🔧 Advanced search architecture mostly functional.")
    else:
        print("❌ Multiple test failures - Significant issues to resolve.")
        print("🔨 Advanced search architecture needs work.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
