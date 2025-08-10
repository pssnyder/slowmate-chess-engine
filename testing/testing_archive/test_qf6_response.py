#!/usr/bin/env python3
"""Test the opening position where Black plays Qf6 and White should respond with development, not Qf3"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence

def test_qf6_response():
    """Test position after 1.Nc3 e6 2.e4 Qf6 - should White play Qf3?"""
    
    print("🎯 Testing Opening Queen Trade Decision")
    print("=" * 60)
    print("Position: 1.Nc3 e6 2.e4 Qf6")
    print("Should White offer queen trade with Qf3, or develop normally?")
    print()
    
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Set up the position: 1.Nc3 e6 2.e4 Qf6
    engine.board.push_uci("b1c3")  # Nc3
    engine.board.push_uci("e7e6")  # e6
    engine.board.push_uci("e2e4")  # e4
    engine.board.push_uci("d8f6")  # Qf6
    
    print("🔍 CURRENT POSITION:")
    print(f"FEN: {engine.board.fen()}")
    print(f"White to move: {engine.board.turn == chess.WHITE}")
    print()
    
    print("🎭 ANALYZING BLACK'S EARLY QUEEN:")
    f6_queen = engine.board.piece_at(chess.F6)
    print(f"Black queen on f6: {f6_queen}")
    
    # Check what the queen attacks
    queen_attacks = list(engine.board.attacks(chess.F6))
    important_targets = []
    for square in queen_attacks:
        piece = engine.board.piece_at(square)
        if piece and piece.color == chess.WHITE:
            important_targets.append(f"{piece.symbol()} on {chess.square_name(square)}")
    
    print(f"Queen attacks: {[chess.square_name(sq) for sq in queen_attacks[:8]]}...")
    if important_targets:
        print(f"Threatens: {', '.join(important_targets)}")
    print()
    
    print("📊 EVALUATING WHITE'S RESPONSE OPTIONS:")
    
    # Test various responses
    response_moves = [
        ("d1f3", "Qf3 (offer queen trade)"),
        ("g1f3", "Nf3 (develop knight)"),
        ("d2d3", "d3 (support e4, prepare development)"),
        ("f1e2", "Be2 (develop bishop)"),
        ("f2f3", "f3 (defend f2, but weakening)"),
        ("d2d4", "d4 (advance center)"),
        ("f1c4", "Bc4 (develop bishop aggressively)")
    ]
    
    move_scores = []
    for move_uci, description in response_moves:
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
    
    print("\n🏆 MOVE RANKING:")
    move_scores.sort(key=lambda x: x[2], reverse=True)
    for i, (move_uci, description, score) in enumerate(move_scores, 1):
        print(f"   {i}. {move_uci} ({description}): {score} cp")
    
    print("\n✅ EXPECTED BEHAVIOR (v0.1.01):")
    print("   1. Normal development (Nf3, Be2, d3) should rank higher")
    print("   2. Qf3 should be penalized for early queen development")
    print("   3. Engine should prefer piece development over queen trades")
    
    # Test what the engine actually chooses
    print("\n🤖 ENGINE MOVE SELECTION:")
    selected_move = intelligence.select_best_move()
    if selected_move:
        selected_score = intelligence._evaluate_move(selected_move)
        print(f"   Engine selected: {selected_move} ({selected_score} cp)")
        
        if str(selected_move) == "d1f3":
            print("   ❌ ENGINE STILL CHOOSING Qf3 - needs improvement")
            print("   This suggests queen development penalty is insufficient")
        elif str(selected_move) in ["g1f3", "f1e2", "d2d3"]:
            print("   ✅ ENGINE CORRECTLY CHOSE DEVELOPMENT!")
        else:
            print(f"   ? Engine chose {selected_move} - analyzing...")
    else:
        print("   ERROR: Engine returned no move")
    
    print("\n🔬 DETAILED EVALUATION ANALYSIS:")
    # Test the specific components for Qf3 vs Nf3
    if chess.Move.from_uci("d1f3") in engine.board.legal_moves:
        qf3_move = chess.Move.from_uci("d1f3")
        print(f"\n   Qf3 detailed analysis:")
        
        # Queen development penalty
        engine.board.push(qf3_move)
        queen_dev_penalty = intelligence._calculate_queen_development_score(chess.WHITE)
        engine.board.pop()
        print(f"   - Queen development penalty: {queen_dev_penalty} cp")
        
    if chess.Move.from_uci("g1f3") in engine.board.legal_moves:
        nf3_move = chess.Move.from_uci("g1f3")
        print(f"\n   Nf3 detailed analysis:")
        
        # Minor piece development bonus
        engine.board.push(nf3_move)
        minor_dev_bonus = intelligence._calculate_minor_piece_development_bonus(chess.WHITE)
        engine.board.pop()
        print(f"   - Minor piece development bonus: {minor_dev_bonus} cp")

if __name__ == "__main__":
    test_qf6_response()
