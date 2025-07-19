#!/usr/bin/env python3
"""Debug material counting"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

engine = IntelligentSlowMateEngine()

# Debug the "white up a pawn" position
print("=== Debugging White Up A Pawn ===")
engine.board.set_fen("rnbqkbnr/ppp1pppp/8/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3")

print("Board state:")
print(engine.board)
print()

details = engine.get_evaluation_details()
print(f"White material: {details['white_material']}")
print(f"Black material: {details['black_material']}")
print(f"Material difference: {details['material_difference']}")
print(f"Current player advantage: {details['current_player_advantage']}")

# Count pieces manually
print("\nManual piece count:")
for color in [chess.WHITE, chess.BLACK]:
    color_name = "White" if color == chess.WHITE else "Black"
    print(f"{color_name}:")
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        pieces = engine.board.pieces(piece_type, color)
        count = len(pieces)
        piece_name = chess.piece_name(piece_type)
        if count > 0:
            print(f"  {piece_name.capitalize()}s: {count}")
