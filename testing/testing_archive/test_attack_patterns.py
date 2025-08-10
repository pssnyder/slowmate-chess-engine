#!/usr/bin/env python3
"""
Test attack patterns system - pins, forks, discovered attacks, etc.
"""

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def test_attack_patterns():
    """Test the attack patterns evaluation system."""
    
    print("================================================================================")
    print("ATTACK PATTERNS TESTING")
    print("================================================================================")
    
    # Test position with potential pins and forks
    # This position has tactical opportunities for attack patterns
    test_positions = [
        {
            'name': 'Original Tactical Bug Position',
            'fen': 'rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20',
            'description': 'Tests tactical combinations with attack patterns'
        },
        {
            'name': 'Pin Setup Position', 
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
            'description': 'Tests pin detection with bishop vs knight'
        },
        {
            'name': 'Fork Opportunity Position',
            'fen': 'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2',
            'description': 'Tests fork opportunities'
        }
    ]
    
    for pos_info in test_positions:
        print(f"\n🎯 TESTING: {pos_info['name']}")
        print(f"   {pos_info['description']}")
        print(f"   FEN: {pos_info['fen']}")
        
        engine = IntelligentSlowMateEngine()
        engine.board = chess.Board(pos_info['fen'])
        
        # Get attack patterns scores
        white_attacks = engine.intelligence._calculate_attack_patterns_score(chess.WHITE)
        black_attacks = engine.intelligence._calculate_attack_patterns_score(chess.BLACK)
        
        print(f"   White attack patterns score: {white_attacks}")
        print(f"   Black attack patterns score: {black_attacks}")
        print(f"   Attack patterns difference: {white_attacks - black_attacks:+d}")
        
        # Test specific pattern detection
        white_pins = engine.intelligence._detect_pins(chess.WHITE)
        white_forks = engine.intelligence._detect_forks(chess.WHITE)
        
        print(f"   White pins score: {white_pins}")
        print(f"   White forks score: {white_forks}")
        
        # Show some legal moves with attack pattern considerations
        legal_moves = list(engine.board.legal_moves)
        if legal_moves:
            print("   📊 Sample move evaluations:")
            for i, move in enumerate(legal_moves[:5]):  # Test first 5 moves
                score = engine.intelligence._evaluate_move(move)
                print(f"      {move}: {score:+d}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_attack_patterns()
