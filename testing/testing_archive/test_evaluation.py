#!/usr/bin/env python3
"""
Test script for SlowMate Chess Engine evaluation system.

This script tests the position evaluation and move selection with material scoring.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def test_basic_evaluation():
    """Test basic position evaluation."""
    print("=== Testing Basic Position Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test starting position
    print(f"Starting position evaluation: {engine.get_current_evaluation()}")
    details = engine.get_evaluation_details()
    print(f"White material: {details['white_material']}")
    print(f"Black material: {details['black_material']}")
    print(f"Material difference: {details['material_difference']}")
    print(f"Current player advantage: {details['current_player_advantage']}")
    print()


def test_material_advantage():
    """Test evaluation with material advantage."""
    print("=== Testing Material Advantage Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up a position where white has captured a pawn
    # 1.e4 e5 2.Nf3 Nc6 3.Bc4 f5 4.exf5 (white up a pawn)
    moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f7f5", "e4f5"]
    
    for move in moves:
        engine.make_move(chess.Move.from_uci(move))
    
    print(f"Position after white captures pawn:")
    details = engine.get_evaluation_details()
    print(f"White material: {details['white_material']}")
    print(f"Black material: {details['black_material']}")
    print(f"Material difference: {details['material_difference']} (should be +100)")
    print(f"Current player advantage: {details['current_player_advantage']} (black to move)")
    print()


def test_piece_exchanges():
    """Test evaluation after piece exchanges."""
    print("=== Testing Piece Exchange Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up position with queen vs rook+rook (queen = 900, 2 rooks = 1000)
    # This is a simplified test position
    engine.board.set_fen("8/8/8/8/8/8/q7/Q7 w - - 0 1")
    
    print(f"Queen vs Queen position:")
    details = engine.get_evaluation_details()
    print(f"White material: {details['white_material']}")
    print(f"Black material: {details['black_material']}")
    print(f"Material difference: {details['material_difference']}")
    
    # Now test rook vs rook + pawn
    engine.board.set_fen("8/8/8/8/8/8/rp6/R7 w - - 0 1")
    
    print(f"Rook vs Rook+Pawn position:")
    details = engine.get_evaluation_details()
    print(f"White material: {details['white_material']}")
    print(f"Black material: {details['black_material']}")
    print(f"Material difference: {details['material_difference']} (should be -100)")
    print()


def test_intelligent_move_selection():
    """Test move selection with evaluation."""
    print("=== Testing Intelligent Move Selection with Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test a position where the engine can capture material
    # Set up position where black queen is hanging
    engine.board.set_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    engine.board.push(chess.Move.from_uci("d1h5"))  # Attack f7 and h7
    engine.board.push(chess.Move.from_uci("b8c6"))  # Random move
    engine.board.push(chess.Move.from_uci("h5f7"))  # Checkmate threat
    
    print(f"Position before black's move (queen can be captured):")
    print(f"Current evaluation: {engine.get_current_evaluation()}")
    
    # Test several moves to see evaluation-based selection
    for i in range(3):
        if not engine.is_game_over():
            move = engine.play_intelligent_move()
            if move:
                eval_score = engine.get_current_evaluation()
                print(f"Move {i+1}: {move} (evaluation: {eval_score:+d})")
                
                # Show last evaluation details
                if engine.evaluation_history:
                    last_eval = engine.evaluation_history[-1]
                    print(f"  Reasoning: {last_eval['reasoning']}")
                    print(f"  Move score: {last_eval['score']:+d}")
            else:
                print("Game over!")
                break
    print()


def test_capture_vs_quiet_moves():
    """Test that engine prefers capturing moves when beneficial."""
    print("=== Testing Capture vs Quiet Move Preferences ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up a position where white can capture a piece or make a quiet move
    # Position with a hanging black knight on e5
    engine.board.set_fen("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3")
    
    print("Position with hanging black knight on e5:")
    print(f"Current evaluation: {engine.get_current_evaluation()}")
    
    # Get all legal moves and their evaluations
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    for move in legal_moves[:10]:  # Test first 10 moves to avoid too much output
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score))
    
    # Sort by evaluation score
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("Top evaluated moves:")
    for i, (move_san, score) in enumerate(move_evaluations[:5]):
        print(f"  {i+1}. {move_san}: {score:+d}")
    
    # Make the engine's choice
    selected_move = engine.play_intelligent_move()
    if selected_move:
        print(f"Engine selected: {selected_move}")
        if engine.evaluation_history:
            last_eval = engine.evaluation_history[-1]
            print(f"Reasoning: {last_eval['reasoning']}")
    print()


def main():
    """Run all evaluation tests."""
    print("SlowMate Chess Engine - Evaluation System Tests")
    print("=" * 50)
    
    test_basic_evaluation()
    test_material_advantage()
    test_piece_exchanges()
    test_intelligent_move_selection()
    test_capture_vs_quiet_moves()
    
    print("All evaluation tests completed!")


if __name__ == "__main__":
    main()
