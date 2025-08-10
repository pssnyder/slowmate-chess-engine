#!/usr/bin/env python3
"""
Comprehensive test of evaluation-based move selection
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def test_capture_preference():
    """Test that engine prefers capturing valuable pieces."""
    print("=== Testing Capture Preference ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up position where white can capture black queen with pawn
    # Position: black queen on d5, white pawn on c4
    engine.board.set_fen("rnb1kbnr/pppp1ppp/8/3qp3/2P1P3/8/PP1P1PPP/RNBQKBNR w KQkq - 0 4")
    
    print("Position: Black queen on d5, white can capture with c4 pawn")
    print(f"Current evaluation: {engine.get_current_evaluation()}")
    
    # Test all legal moves and their evaluations
    legal_moves = list(engine.board.legal_moves)
    
    best_moves = []
    best_score = float('-inf')
    
    for move in legal_moves:
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        
        if move.to_square == chess.D5:  # Capturing the queen
            print(f"Capture queen: {move_san} scores {score:+d} (should be +900)")
        
        if score > best_score:
            best_score = score
            best_moves = [move_san]
        elif score == best_score:
            best_moves.append(move_san)
    
    print(f"Best scoring moves ({best_score:+d}): {', '.join(best_moves)}")
    
    # Let engine select move
    selected = engine.play_intelligent_move()
    print(f"Engine selected: {selected}")
    
    if engine.evaluation_history:
        last_eval = engine.evaluation_history[-1]
        print(f"Reasoning: {last_eval['reasoning']}")
    print()


def test_piece_value_differences():
    """Test engine's understanding of piece values."""
    print("=== Testing Piece Value Understanding ===")
    
    # Test 1: Queen vs Rook trade
    engine1 = IntelligentSlowMateEngine()
    engine1.board.set_fen("4k3/8/8/8/4q3/4R3/8/4K3 w - - 0 1")
    
    print("Position 1: White rook can capture black queen")
    capture_score = engine1.intelligence._evaluate_move(chess.Move.from_uci("e3e4"))
    print(f"Rook takes queen score: {capture_score:+d} (should be around +400)")
    
    # Test 2: Pawn vs Queen trade (bad trade)
    engine2 = IntelligentSlowMateEngine()
    engine2.board.set_fen("4k3/8/8/8/3Pq3/8/8/4K3 w - - 0 1")
    
    print("Position 2: Black queen can capture white pawn")
    engine2.board.push(chess.Move.from_uci("d4d5"))  # Move pawn
    capture_score = engine2.intelligence._evaluate_move(chess.Move.from_uci("e4d5"))
    print(f"Queen takes pawn score: {capture_score:+d} (should be around -800)")
    
    print()


def test_material_counting():
    """Test accurate material counting."""
    print("=== Testing Material Counting ===")
    
    engine = IntelligentSlowMateEngine()
    
    positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 0),
        ("White up a queen", "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 900),  # Black queen removed
        ("Black up a rook", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1", -500),  # White rook removed
        ("White up a knight", "rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 320)  # Black knight removed
    ]
    
    for name, fen, expected in positions:
        engine.board.set_fen(fen)
        evaluation = engine.get_current_evaluation()
        details = engine.get_evaluation_details()
        
        print(f"{name}:")
        print(f"  Expected: {expected:+d}, Actual: {evaluation:+d}")
        print(f"  White material: {details['white_material']}, Black material: {details['black_material']}")
        
        if abs(evaluation - expected) <= 10:  # Allow small tolerance
            print(f"  ✓ Correct evaluation")
        else:
            print(f"  ✗ Evaluation mismatch")
        print()


def main():
    """Run all evaluation tests."""
    print("SlowMate Chess Engine - Advanced Evaluation Tests")
    print("=" * 55)
    
    test_capture_preference()
    test_piece_value_differences()
    test_material_counting()
    
    print("All advanced evaluation tests completed!")


if __name__ == "__main__":
    main()
