#!/usr/bin/env python3
"""
Simple test to debug tactical combination bonus
"""
import chess
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slowmate.intelligence import MoveIntelligence
from slowmate.engine import SlowMateEngine

# Test the tactical bug position
def test_tactical_combination():
    # Setup the position from the bug
    fen = "rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20"
    board = chess.Board(fen)
    
    engine = SlowMateEngine()
    engine.board = board
    intelligence = MoveIntelligence(engine)
    
    # Test the two key moves
    moves_to_test = [
        chess.Move.from_uci("g2a8"),  # Bxa8 - capture rook
        chess.Move.from_uci("g2b7"),  # Bb7 - retreat
    ]
    
    print("================================================================================")
    print("TACTICAL COMBINATION BONUS DEBUG")
    print("================================================================================")
    print(f"Position: {fen}")
    print(f"Board state:\n{board}")
    print()
    
    for move in moves_to_test:
        print(f"🎯 TESTING MOVE: {move}")
        
        # Test if bishop is under threat
        from_square = move.from_square
        piece = board.piece_at(from_square)
        if piece:
            print(f"  Piece: {piece.symbol()} on {chess.square_name(from_square)}")
        else:
            print(f"  No piece on {chess.square_name(from_square)}")
            continue
        
        # Test threat detection
        is_threatened = intelligence._is_piece_under_threat(from_square, chess.WHITE)
        print(f"  Is under threat: {is_threatened}")
        
        # Test if it's a capture
        to_square = move.to_square
        captured_piece = board.piece_at(to_square)
        is_capture = captured_piece is not None
        print(f"  Is capture: {is_capture}")
        if is_capture:
            print(f"  Captured piece: {captured_piece.symbol()} on {chess.square_name(to_square)}")
        
        # Test the combination bonus directly
        bonus = intelligence._calculate_tactical_combination_bonus(move, chess.WHITE)
        print(f"  Tactical combination bonus: {bonus}")
        
        print()

if __name__ == "__main__":
    test_tactical_combination()
