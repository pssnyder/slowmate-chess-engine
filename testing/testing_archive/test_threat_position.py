#!/usr/bin/env python3
"""Test the specific threat position where Black's queen attacks f2"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence

def test_threat_position():
    """Test the position: rnb1kbnr/pppp1ppp/4pq2/8/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 3"""
    
    print("🎯 Testing Threat Position Analysis")
    print("=" * 60)
    print("Position: rnb1kbnr/pppp1ppp/4pq2/8/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 3")
    print("Black queen on f6 threatens f2 pawn!")
    print()
    
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Set the specific position
    fen = "rnb1kbnr/pppp1ppp/4pq2/8/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 3"
    engine.board.set_fen(fen)
    
    print("🔍 ANALYZING CURRENT SITUATION:")
    print(f"White to move: {engine.board.turn == chess.WHITE}")
    
    # Check if f2 is under attack
    f2_square = chess.F2
    f2_under_attack = engine.board.is_attacked_by(chess.BLACK, f2_square)
    print(f"f2 pawn under attack: {f2_under_attack}")
    
    # Show what piece is attacking f2
    for square in chess.SQUARES:
        piece = engine.board.piece_at(square)
        if piece and piece.color == chess.BLACK:
            if engine.board.is_attacked_by(chess.BLACK, f2_square):
                # Check if this specific piece attacks f2
                attacks = engine.board.attacks(square)
                if f2_square in attacks:
                    print(f"   {piece.symbol()} on {chess.square_name(square)} attacks f2")
    
    print("\n📊 EVALUATING DEFENSIVE MOVES:")
    
    # Test defensive moves
    defensive_moves = [
        ("d1e2", "Qe2 (defend f2)"),
        ("f2f3", "f3 (advance pawn, defend)"),
        ("g1f3", "Nf3 (develop knight)"),
        ("d2d4", "d4 (center pawn)"),
        ("f1e2", "Be2 (develop bishop)")
    ]
    
    move_scores = []
    for move_uci, description in defensive_moves:
        try:
            move = chess.Move.from_uci(move_uci)
            if move in engine.board.legal_moves:
                score = intelligence._evaluate_move(move)
                move_scores.append((move_uci, description, score))
                print(f"   {move_uci} ({description}): {score} cp")
            else:
                print(f"   {move_uci} ({description}): ILLEGAL MOVE")
        except Exception as e:
            print(f"   {move_uci}: ERROR - {e}")
    
    print("\n🎯 MOVE PRIORITY RANKING:")
    move_scores.sort(key=lambda x: x[2], reverse=True)
    for i, (move_uci, description, score) in enumerate(move_scores, 1):
        print(f"   {i}. {move_uci} ({description}): {score} cp")
    
    print("\n✅ EXPECTED BEHAVIOR:")
    print("   1. Qe2 or f3 should be top choices (defend f2)")
    print("   2. f3 gets bonus for pawn advancement + center support")
    print("   3. Random queen moves should be heavily penalized")
    
    # Test the engine's actual move selection
    print("\n🤖 ENGINE MOVE SELECTION:")
    selected_move = intelligence.select_best_move()
    if selected_move:
        selected_score = intelligence._evaluate_move(selected_move)
        print(f"   Engine selected: {selected_move} ({selected_score} cp)")
        
        # Check if it's a good defensive move
        defensive_move_ucis = [move[0] for move in defensive_moves]
        if str(selected_move) in defensive_move_ucis:
            print("   ✅ ENGINE CORRECTLY CHOSE DEFENSIVE MOVE!")
        else:
            print("   ❌ Engine chose non-defensive move - needs improvement")
    else:
        print("   ERROR: Engine returned no move")

if __name__ == "__main__":
    test_threat_position()
