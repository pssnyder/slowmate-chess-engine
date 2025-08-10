#!/usr/bin/env python3
"""
Test complete tactical intelligence - attack patterns + coordination
"""

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def test_complete_tactical_intelligence():
    """Test the complete tactical intelligence system."""
    
    print("================================================================================")
    print("COMPLETE TACTICAL INTELLIGENCE TESTING")
    print("================================================================================")
    
    # Test positions with various tactical elements
    test_positions = [
        {
            'name': 'Original Tactical Bug Position',
            'fen': 'rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20',
            'description': 'Threats + Captures + Tactical Combinations'
        },
        {
            'name': 'Rook Coordination Position', 
            'fen': 'r3k3/8/8/8/8/8/8/R3K2R w KQ - 0 1',
            'description': 'Tests rook stacking and coordination'
        },
        {
            'name': 'Bishop Pair Position',
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'description': 'Tests bishop pairing bonus'
        },
        {
            'name': 'Queen Battery Position',
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4',
            'description': 'Tests queen-bishop battery potential'
        }
    ]
    
    for pos_info in test_positions:
        print(f"\n🎯 TESTING: {pos_info['name']}")
        print(f"   {pos_info['description']}")
        print(f"   FEN: {pos_info['fen']}")
        
        engine = IntelligentSlowMateEngine()
        engine.board = chess.Board(pos_info['fen'])
        
        # Get complete evaluation breakdown
        evaluation = engine.intelligence.get_position_evaluation()
        
        print(f"   📊 EVALUATION BREAKDOWN:")
        print(f"      Material: {evaluation['material_difference']:+d}")
        print(f"      Position: {evaluation['pst_difference']:+d}")
        print(f"      King Safety: {evaluation['king_safety_difference']:+d}")
        print(f"      Captures: {evaluation['captures_difference']:+d}")
        
        # Get individual tactical scores
        white_attacks = engine.intelligence._calculate_attack_patterns_score(chess.WHITE)
        black_attacks = engine.intelligence._calculate_attack_patterns_score(chess.BLACK)
        white_coordination = engine.intelligence._calculate_piece_coordination_score(chess.WHITE)
        black_coordination = engine.intelligence._calculate_piece_coordination_score(chess.BLACK)
        
        print(f"      Attack Patterns: {white_attacks - black_attacks:+d} (W:{white_attacks}, B:{black_attacks})")
        print(f"      Coordination: {white_coordination - black_coordination:+d} (W:{white_coordination}, B:{black_coordination})")
        print(f"      TOTAL: {evaluation['current_player_advantage']:+d}")
        
        # Test key moves
        legal_moves = list(engine.board.legal_moves)
        if legal_moves:
            print(f"   🔍 TOP MOVES:")
            move_scores = [(move, engine.intelligence._evaluate_move(move)) for move in legal_moves]
            move_scores.sort(key=lambda x: x[1], reverse=True)
            
            for i, (move, score) in enumerate(move_scores[:3]):  # Top 3 moves
                print(f"      {i+1}. {move}: {score:+d}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_complete_tactical_intelligence()
