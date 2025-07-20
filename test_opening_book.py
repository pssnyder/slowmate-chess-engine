#!/usr/bin/env python3
"""
Test Opening Book System

Validates opening book functionality including:
- Position lookup and move selection
- Preference weighting system
- Anti-repetition variety
- Performance benchmarks
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.knowledge.opening_book import OpeningBook
from slowmate.knowledge.opening_weights import OpeningWeights

def test_opening_book_basic():
    """Test basic opening book functionality."""
    print("=" * 60)
    print("TESTING OPENING BOOK - BASIC FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize opening book
    book = OpeningBook()
    print(f"Opening book loaded: {book.is_loaded}")
    print(f"Statistics: {book.get_statistics()}")
    
    # Test starting position
    board = chess.Board()
    print(f"\n1. Starting position: {board.fen()}")
    
    book_move = book.get_book_move(board)
    if book_move:
        print(f"   Book move: {board.san(book_move)}")
        print(f"   Is in book: {book.is_in_opening_book(board)}")
    else:
        print("   No book move found")
    
    # Test after e4
    board.push_san("e4")
    print(f"\n2. After e4: {board.fen()}")
    
    book_move = book.get_book_move(board)
    if book_move:
        print(f"   Book move: {board.san(book_move)}")
        book_info = book.get_book_info(board)
        print(f"   Book info: {book_info}")
    else:
        print("   No book move found")
    
    # Test after e4 e5
    board.push_san("e5")
    print(f"\n3. After e4 e5: {board.fen()}")
    
    book_move = book.get_book_move(board)
    if book_move:
        print(f"   Book move: {board.san(book_move)}")
    else:
        print("   No book move found")

def test_opening_weights():
    """Test opening weights and preferences."""
    print("\n" + "=" * 60)
    print("TESTING OPENING WEIGHTS - PREFERENCE SYSTEM")
    print("=" * 60)
    
    weights = OpeningWeights()
    board = chess.Board()
    
    # Test starting position preferences
    print("\n1. Starting position move weights:")
    legal_moves = list(board.legal_moves)
    
    for move in legal_moves[:8]:  # Test first 8 moves
        move_san = board.san(move)
        weight = weights.get_move_weight(board, move, legal_moves)
        print(f"   {move_san}: {weight:.2f}")
    
    # Test after d4 (should prefer London/Queens Gambit continuations)
    board.push_san("d4")
    board.push_san("Nf6")
    print(f"\n2. After d4 Nf6 - White to move:")
    
    legal_moves = list(board.legal_moves)
    test_moves = ["c4", "Bf4", "Nf3", "Bg5", "e3"]
    
    for move_san in test_moves:
        try:
            move = board.parse_san(move_san)
            if move in legal_moves:
                weight = weights.get_move_weight(board, move, legal_moves)
                print(f"   {move_san}: {weight:.2f}")
        except:
            print(f"   {move_san}: invalid")
    
    # Test preference info
    pref_info = weights.get_preference_info(board)
    print(f"\n3. Preference analysis: {pref_info}")

def test_integration():
    """Test integration between opening book and weights."""
    print("\n" + "=" * 60)
    print("TESTING INTEGRATION - BOOK + WEIGHTS")
    print("=" * 60)
    
    book = OpeningBook()
    weights = OpeningWeights()
    board = chess.Board()
    
    # Test several opening scenarios
    scenarios = [
        ("Starting position", []),
        ("After e4", ["e4"]),
        ("French Defense", ["e4", "e6"]),
        ("Queens Gambit", ["d4", "d5", "c4"]),
        ("Caro-Kann", ["e4", "c6"])
    ]
    
    for scenario_name, moves in scenarios:
        test_board = chess.Board()
        for move_san in moves:
            test_board.push_san(move_san)
            
        print(f"\n{scenario_name}: {test_board.fen()}")
        
        # Get book move
        book_move = book.get_book_move(test_board)
        if book_move:
            book_san = test_board.san(book_move)
            weight = weights.get_move_weight(test_board, book_move, list(test_board.legal_moves))
            print(f"   Book move: {book_san} (weight: {weight:.2f})")
        else:
            print("   No book move")
        
        # Show top legal moves with weights
        legal_moves = list(test_board.legal_moves)
        move_weights = []
        
        for move in legal_moves[:5]:  # Top 5 moves
            move_san = test_board.san(move)
            weight = weights.get_move_weight(test_board, move, legal_moves)
            move_weights.append((move_san, weight))
        
        move_weights.sort(key=lambda x: x[1], reverse=True)
        print(f"   Top moves by weight: {move_weights[:3]}")

def test_performance():
    """Test opening book performance."""
    print("\n" + "=" * 60)
    print("TESTING PERFORMANCE - LOOKUP SPEED")
    print("=" * 60)
    
    import time
    
    book = OpeningBook()
    
    # Test multiple lookups
    positions = []
    for i in range(100):
        board = chess.Board()
        # Make random moves to create diverse positions
        for _ in range(min(i % 8, 6)):  # Up to 6 moves
            legal_moves = list(board.legal_moves)
            if legal_moves:
                move = legal_moves[i % len(legal_moves)]
                board.push(move)
        positions.append(board)
    
    # Time lookups
    start_time = time.time()
    hits = 0
    
    for board in positions:
        move = book.get_book_move(board)
        if move:
            hits += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = (total_time / len(positions)) * 1000  # Convert to milliseconds
    
    print(f"   Tested positions: {len(positions)}")
    print(f"   Book hits: {hits}")
    print(f"   Total time: {total_time:.4f} seconds")
    print(f"   Average lookup: {avg_time:.2f} ms")
    print(f"   Lookups per second: {len(positions) / total_time:.0f}")
    
    # Test cache effectiveness
    print(f"   Cache size: {len(book.position_cache)}")
    
    # Test same positions again (should be faster due to cache)
    start_time = time.time()
    for board in positions:
        book.get_book_move(board)
    end_time = time.time()
    
    cached_time = end_time - start_time
    cached_avg = (cached_time / len(positions)) * 1000
    
    print(f"   Cached lookup time: {cached_avg:.2f} ms")
    print(f"   Cache speedup: {avg_time / cached_avg:.1f}x")

def main():
    """Run all opening book tests."""
    test_opening_book_basic()
    test_opening_weights()
    test_integration()
    test_performance()
    
    print("\n" + "=" * 60)
    print("OPENING BOOK TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
