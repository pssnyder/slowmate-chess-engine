#!/usr/bin/env python3
"""
Detailed score breakdown to understand the evaluation components
"""
import chess
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slowmate.intelligence import MoveIntelligence
from slowmate.engine import SlowMateEngine

def detailed_move_analysis():
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
    print("DETAILED MOVE SCORE BREAKDOWN")
    print("================================================================================")
    print(f"Position: {fen}")
    print()
    
    for move in moves_to_test:
        print(f"🎯 ANALYZING MOVE: {move}")
        
        # Make the move to evaluate the resulting position
        board.push(move)
        
        try:
            # Get detailed evaluation components
            current_player = board.turn
            material_score = intelligence._calculate_material_with_threats(current_player) - intelligence._calculate_material_with_threats(not current_player)
            positional_score = intelligence._calculate_pst_score(current_player) - intelligence._calculate_pst_score(not current_player)
            king_safety_score = intelligence._calculate_king_safety(current_player) - intelligence._calculate_king_safety(not current_player)
            captures_score = intelligence._calculate_captures_score(current_player) - intelligence._calculate_captures_score(not current_player)
            
            print(f"  Material score (with threats): {material_score}")
            print(f"  Positional score (PST): {positional_score}")
            print(f"  King safety score: {king_safety_score}")
            print(f"  Captures score: {captures_score}")
            
            base_total = material_score + positional_score + king_safety_score + captures_score
            print(f"  Base total: {base_total}")
            
            # Get threat analysis
            threat_analysis = intelligence._get_threat_analysis(current_player)
            print(f"  Pieces under threat: {threat_analysis['pieces_under_threat']}")
            print(f"  Total threat penalty: {threat_analysis['total_threat_penalty']}")
            
            # Get captures analysis  
            captures_analysis = intelligence._get_captures_analysis(current_player)
            print(f"  Winning captures: {len(captures_analysis['winning_captures'])}")
            print(f"  Total captures score: {captures_analysis['total_score']}")
            
        finally:
            board.pop()
        
        # Get tactical combination bonus
        combo_bonus = intelligence._calculate_tactical_combination_bonus(move, chess.WHITE)
        print(f"  Tactical combination bonus: {combo_bonus}")
        
        # Get total evaluation score
        total_score = intelligence._evaluate_move(move)
        print(f"  TOTAL MOVE SCORE: {total_score}")
        print()

if __name__ == "__main__":
    detailed_move_analysis()
