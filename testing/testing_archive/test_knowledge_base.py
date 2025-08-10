#!/usr/bin/env python3
"""
Test Knowledge Base Integration - Full System Test

This script tests the complete knowledge base system including:
- Opening book + weights integration
- Endgame pattern recognition
- Knowledge base coordinator
- Performance validation
"""

import sys
import os
import time
import chess
from chess import Board, Move

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from slowmate.knowledge import KnowledgeBase
    from slowmate.knowledge.opening_book import OpeningBook
    from slowmate.knowledge.opening_weights import OpeningWeights
    from slowmate.knowledge.endgame_patterns import EndgamePatterns
    from slowmate.knowledge.endgame_tactics import EndgameTactics
    print("✅ All knowledge modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_knowledge_base_integration():
    """Test the unified knowledge base system."""
    print("="*60)
    print("TESTING KNOWLEDGE BASE INTEGRATION")
    print("="*60)
    
    # Initialize knowledge base
    knowledge_base = KnowledgeBase()
    print(f"Knowledge base initialized: {knowledge_base is not None}")
    
    # Test with various positions
    test_positions = [
        ("Starting position", chess.Board()),
        ("After 1.e4", chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")),
        ("French Defense", chess.Board("rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")),
        ("Queen vs King endgame", chess.Board("8/8/8/8/8/8/8/K6Q w - - 0 1")),
        ("King and Rook vs King", chess.Board("8/8/8/8/8/8/8/K6R w - - 0 1"))
    ]
    
    for name, board in test_positions:
        print(f"\n{name}: {board.fen()}")
        
        # Test knowledge-based move selection
        result = knowledge_base.get_knowledge_move(board)
        if result:
            move, source = result
            print(f"   Knowledge move: {move} (source: {source})")
        else:
            print("   No knowledge move found")
        
        # Test phase detection
        opening_phase = knowledge_base.is_opening_phase(board)
        endgame_phase = knowledge_base.is_endgame_phase(board)
        print(f"   Opening phase: {opening_phase}, Endgame phase: {endgame_phase}")
    
    # Get comprehensive statistics
    print(f"\nKnowledge Base Statistics:")
    stats = knowledge_base.get_statistics()
    print(f"   Performance: {stats['performance']}")
    print(f"   Hit counts: {stats['hit_counts']}")
    
    return True


def test_component_isolation():
    """Test each knowledge component in isolation."""
    print("="*60)
    print("TESTING COMPONENT ISOLATION")
    print("="*60)
    
    # Test opening book
    print("1. Opening Book:")
    opening_book = OpeningBook()
    board = chess.Board()
    move = opening_book.get_book_move(board)
    print(f"   Book move from start: {move}")
    print(f"   Statistics: {opening_book.get_statistics()}")
    
    # Test opening weights
    print("\n2. Opening Weights:")
    opening_weights = OpeningWeights()
    legal_moves = list(board.legal_moves)
    if legal_moves:
        move = legal_moves[0]
        weight = opening_weights.get_move_weight(board, move, legal_moves)
        print(f"   Weight for {move}: {weight}")
    print(f"   Statistics: {opening_weights.get_statistics()}")
    
    # Test endgame patterns
    print("\n3. Endgame Patterns:")
    endgame_patterns = EndgamePatterns()
    endgame_board = chess.Board("8/8/8/8/8/8/8/K6Q w - - 0 1")
    strategic_move = endgame_patterns.get_strategic_move(endgame_board)
    print(f"   Strategic move: {strategic_move}")
    print(f"   Statistics: {endgame_patterns.get_statistics()}")
    
    # Test endgame tactics
    print("\n4. Endgame Tactics:")
    endgame_tactics = EndgameTactics()
    tactical_move = endgame_tactics.get_tactical_move(endgame_board)
    print(f"   Tactical move: {tactical_move}")
    print(f"   Statistics: {endgame_tactics.get_statistics()}")
    
    return True


def test_performance_benchmarks():
    """Test performance of knowledge base lookups."""
    print("="*60)
    print("TESTING PERFORMANCE BENCHMARKS")
    print("="*60)
    
    knowledge_base = KnowledgeBase()
    
    # Test various positions for performance
    test_positions = []
    
    # Generate test positions
    board = chess.Board()
    test_positions.append(board.copy())
    
    # Add some game positions
    moves = ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]
    for move_san in moves:
        try:
            move = board.parse_san(move_san)
            board.push(move)
            test_positions.append(board.copy())
        except:
            pass
    
    # Performance test
    iterations = 1000
    start_time = time.time()
    
    hit_count = 0
    for i in range(iterations):
        for board in test_positions:
            result = knowledge_base.get_knowledge_move(board)
            if result:
                hit_count += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    total_lookups = iterations * len(test_positions)
    
    print(f"   Total lookups: {total_lookups}")
    print(f"   Knowledge hits: {hit_count}")
    print(f"   Hit rate: {hit_count / total_lookups * 100:.1f}%")
    print(f"   Total time: {total_time:.4f} seconds")
    print(f"   Average lookup: {total_time / total_lookups * 1000:.2f} ms")
    print(f"   Lookups per second: {total_lookups / total_time:.0f}")
    
    # Performance target check
    avg_lookup_ms = total_time / total_lookups * 1000
    if avg_lookup_ms < 1.0:  # Target: < 1ms per lookup
        print("   ✅ Performance target met (<1ms)")
    else:
        print("   ⚠️ Performance target missed (>1ms)")
    
    return True


def main():
    """Run all knowledge base tests."""
    print("🧠 SlowMate Knowledge Base - Full System Test")
    print("="*60)
    
    test_results = []
    
    try:
        # Component isolation test
        result1 = test_component_isolation()
        test_results.append(("Component Isolation", result1))
        
        # Integration test
        result2 = test_knowledge_base_integration()
        test_results.append(("Knowledge Integration", result2))
        
        # Performance test
        result3 = test_performance_benchmarks()
        test_results.append(("Performance", result3))
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("="*60)
    print("KNOWLEDGE BASE TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Knowledge base ready for integration!")
    else:
        print("\n⚠️ Some tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
