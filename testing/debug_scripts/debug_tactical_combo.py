#!/usr/bin/env python3
"""
Debug the tactical combination bonus calculation.
"""

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def debug_tactical_combo():
    """Debug the tactical combination bonus for specific moves."""
    
    # Set up the critical position
    fen = "rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20"
    
    engine = IntelligentSlowMateEngine()
    engine.board = chess.Board(fen)
    
    print("================================================================================")
    print("TACTICAL COMBINATION BONUS DEBUG")
    print("================================================================================")
    print(f"Position: {fen}")
    print()
    
    # Test the two key moves
    moves_to_test = [
        chess.Move.from_uci("g2a8"),  # Bishop captures rook
        chess.Move.from_uci("g2b7"),  # Bishop retreats
    ]
    
    for move in moves_to_test:
        print(f"🎯 TESTING MOVE: {move}")
        
        # Check if bishop is under threat before move
        bishop_threatened = engine.intelligence._is_piece_under_threat(move.from_square, chess.WHITE)
        print(f"   Bishop under threat before move: {bishop_threatened}")
        
        # Check if this is a capture
        captured_piece = engine.board.piece_at(move.to_square)
        is_capture = captured_piece is not None
        print(f"   Is capture: {is_capture}")
        if captured_piece:
            print(f"   Captured piece: {captured_piece.symbol()}")
        
        # Get the tactical combination bonus
        combo_bonus = engine.intelligence._calculate_tactical_combination_bonus(move, chess.WHITE)
        print(f"   Tactical combination bonus: {combo_bonus}")
        
        # Get the total move score
        total_score = engine.intelligence._evaluate_move(move)
        print(f"   Total move score: {total_score}")
        print()

if __name__ == "__main__":
    debug_tactical_combo()
