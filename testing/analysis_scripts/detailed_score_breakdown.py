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
        
        # Store whose turn it is BEFORE making the move (same as _evaluate_move)
        current_player = board.turn
        
        # Make the move temporarily
        board.push(move)
        
        try:
            # Get detailed evaluation components (from original player's perspective)
            white_material = intelligence._calculate_material_with_threats(chess.WHITE)
            black_material = intelligence._calculate_material_with_threats(chess.BLACK)
            white_pst = intelligence._calculate_pst_score(chess.WHITE)
            black_pst = intelligence._calculate_pst_score(chess.BLACK)
            white_king_safety = intelligence._calculate_king_safety(chess.WHITE)
            black_king_safety = intelligence._calculate_king_safety(chess.BLACK)
            white_captures = intelligence._calculate_captures_score(chess.WHITE)
            black_captures = intelligence._calculate_captures_score(chess.BLACK)
            
            # Calculate scores from the ORIGINAL player's perspective (same as _evaluate_move)
            if current_player == chess.WHITE:
                material_score = white_material - black_material
                positional_score = white_pst - black_pst
                king_safety_score = white_king_safety - black_king_safety
                captures_score = white_captures - black_captures
            else:
                material_score = black_material - white_material
                positional_score = black_pst - white_pst
                king_safety_score = black_king_safety - white_king_safety
                captures_score = black_captures - white_captures
            
            print(f"  Material score (with threats): {material_score}")
            print(f"  Positional score (PST): {positional_score}")
            print(f"  King safety score: {king_safety_score}")
            print(f"  Captures score: {captures_score}")
            
            base_total = material_score + positional_score + king_safety_score + captures_score
            print(f"  Base total: {base_total}")
            
            # Get threat analysis for the position (now that move is made)
            if current_player == chess.WHITE:
                threat_analysis = intelligence._get_threat_analysis(chess.WHITE)
                captures_analysis = intelligence._get_captures_analysis(chess.WHITE)
            else:
                threat_analysis = intelligence._get_threat_analysis(chess.BLACK)
                captures_analysis = intelligence._get_captures_analysis(chess.BLACK)
                
            print(f"  Pieces under threat: {threat_analysis['pieces_under_threat']}")
            print(f"  Total threat penalty: {threat_analysis['total_threat_penalty']}")
            
            # Updated for new square-centric captures analysis
            print(f"  Significant squares: {len(captures_analysis['significant_squares'])}")
            print(f"  Controlled squares: {captures_analysis['controlled_squares']}")
            print(f"  Threatened pieces: {captures_analysis['threatened_pieces']}")
            print(f"  Total captures score: {captures_analysis['total_score']}")
            
            if captures_analysis['significant_squares']:
                print("  📍 Top significant squares:")
                for i, square_data in enumerate(captures_analysis['significant_squares'][:3]):  # Top 3
                    print(f"    {i+1}. {square_data['square']}: weight={square_data['weight']:+d}, "
                          f"ours={square_data['our_attackers_value']}, theirs={square_data['opponent_attackers_value']}")
                    if square_data['target_piece']:
                        print(f"       Target: {square_data['target_piece']} (value={square_data['target_value']})")
            
        finally:
            board.pop()
        
        # Get tactical combination bonus (this needs the original position)
        combo_bonus = intelligence._calculate_tactical_combination_bonus(move, current_player)
        print(f"  Tactical combination bonus: {combo_bonus}")
        
        # Get total evaluation score
        total_score = intelligence._evaluate_move(move)
        print(f"  TOTAL MOVE SCORE: {total_score}")
        print()

if __name__ == "__main__":
    detailed_move_analysis()
