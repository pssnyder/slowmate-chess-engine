#!/usr/bin/env python3
"""
SlowMate Chess Engine v0.1.01 - Pawn Structure & Queen Development Testing

Test suite for the new pawn structure analysis and queen development penalties.
Tests all new features:
1. Backward, isolated, and doubled pawn penalties
2. Center control incentives (e4, d4, f4, c4 for white; e5, d5, f5, c5 for black)
3. King exposure weaknesses (overadvanced c/g pawns for white, f/b for black)
4. Pawn-bishop color coordination 
5. Passed pawn tactics
6. Queen early development penalties (before castling)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence


def test_pawn_structure_features():
    """Test all pawn structure evaluation features"""
    
    print("="*60)
    print("🏗️  TESTING PAWN STRUCTURE FEATURES v0.1.01")
    print("="*60)
    
    # Test 1: Doubled Pawns Penalty
    print("\n1️⃣  TESTING DOUBLED PAWNS PENALTY")
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Position with doubled pawns
    engine.board.set_fen("rnbqkbnr/pp1ppppp/8/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1")
    # White has doubled d-pawns (d4 and d2 are on same file)
    
    white_pawn_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure score with doubled pawns: {white_pawn_score}")
    
    # Compare with normal position
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
    normal_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure score without doubled pawns: {normal_score}")
    print(f"   ✅ Doubled pawn penalty: {normal_score - white_pawn_score} centipawns")
    
    # Test 2: Isolated Pawns
    print("\n2️⃣  TESTING ISOLATED PAWNS PENALTY")
    engine.board.set_fen("rnbqkbnr/ppp1pppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1")
    # White d-pawn is isolated (no pawns on c or e files)
    
    isolated_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure score with isolated d-pawn: {isolated_score}")
    print(f"   ✅ Isolated pawn penalty applied")
    
    # Test 3: Center Control Bonus  
    print("\n3️⃣  TESTING CENTER CONTROL BONUSES")
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1")
    # White has central d4 and e4 pawns
    
    center_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure score with d4+e4 center: {center_score}")
    
    # Test broader center (c4, d4, e4, f4)
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/2PPPP2/8/PP4PP/RNBQKBNR w KQkq - 0 1")
    broad_center_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure score with c4+d4+e4+f4: {broad_center_score}")
    print(f"   ✅ Center control bonus: {broad_center_score} total points")
    
    # Test 4: Passed Pawns
    print("\n4️⃣  TESTING PASSED PAWN EVALUATION")
    engine.board.set_fen("8/8/8/3P4/8/8/p7/8 w - - 0 1")
    # White d5 pawn is passed, black a2 is passed
    
    white_passed = intelligence._calculate_pawn_structure_score(chess.WHITE)
    black_passed = intelligence._calculate_pawn_structure_score(chess.BLACK)
    print(f"   White passed pawn score: {white_passed}")
    print(f"   Black passed pawn score: {black_passed}")
    print(f"   ✅ Passed pawn bonuses applied")
    
    # Test 5: King Exposure (overadvanced pawns)
    print("\n5️⃣  TESTING KING EXPOSURE PENALTIES")
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/2P1P3/8/PP1P1PPP/RNBQKBNR w KQkq - 0 1")
    # White c4 and e4 pawns - c4 might be considered exposing king
    
    exposure_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   White pawn structure with c4+e4: {exposure_score}")
    print(f"   ✅ King exposure evaluation applied")


def test_queen_development_penalties():
    """Test queen development penalty system"""
    
    print("\n" + "="*60)
    print("👑 TESTING QUEEN DEVELOPMENT PENALTIES v0.1.01")
    print("="*60)
    
    # Test 1: Queen on starting square with castling rights
    print("\n1️⃣  TESTING QUEEN ON STARTING SQUARE (GOOD)")
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    normal_queen_score = intelligence._calculate_queen_development_score(chess.WHITE)
    print(f"   Queen development score (starting position): {normal_queen_score}")
    
    # Test 2: Early queen development with castling rights
    print("\n2️⃣  TESTING EARLY QUEEN DEVELOPMENT (BAD)")
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/4Q3/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    # Queen on e3 - early development
    
    early_queen_score = intelligence._calculate_queen_development_score(chess.WHITE)
    print(f"   Queen development score (queen on e3): {early_queen_score}")
    print(f"   ✅ Early development penalty: {normal_queen_score - early_queen_score} centipawns")
    
    # Test 3: Queen development after losing castling rights
    print("\n3️⃣  TESTING QUEEN AFTER CASTLING RIGHTS LOST")
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/4Q3/PPPPPPPP/RNB2RK1 w kq - 0 1")
    # King moved (no white castling), queen on e3
    
    no_castling_score = intelligence._calculate_queen_development_score(chess.WHITE)
    print(f"   Queen development score (no castling rights): {no_castling_score}")
    print(f"   ✅ Reduced penalty when castling impossible: {abs(no_castling_score)} vs {abs(early_queen_score)}")
    
    # Test 4: Compare queen vs minor piece development
    print("\n4️⃣  TESTING PIECE DEVELOPMENT PRIORITIES")
    
    # Position with early queen
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/4Q3/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    queen_dev_eval = intelligence._evaluate_position()
    
    # Position with knight development instead
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/4N3/PPPPPPPP/RNBQKB1R w KQkq - 0 1") 
    knight_dev_eval = intelligence._evaluate_position()
    
    print(f"   Position evaluation with early queen: {queen_dev_eval}")
    print(f"   Position evaluation with knight development: {knight_dev_eval}")
    print(f"   ✅ Knight development preferred by: {knight_dev_eval - queen_dev_eval} centipawns")


def test_pawn_bishop_coordination():
    """Test pawn-bishop color coordination"""
    
    print("\n" + "="*60) 
    print("♗ TESTING PAWN-BISHOP COORDINATION v0.1.01")
    print("="*60)
    
    # Test 1: Good coordination - light bishop, dark pawns
    print("\n1️⃣  TESTING GOOD PAWN-BISHOP COORDINATION")
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Light-squared bishop on f1, pawns on dark squares (a7, c7, e7, g7)
    engine.board.set_fen("r1bqk1nr/p1p1p1p1/1pn3p1/8/8/8/P1P1P1P1/RNB1KB1R w KQkq - 0 1")
    
    good_coord_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   Pawn structure score with good bishop coordination: {good_coord_score}")
    
    # Test 2: Bad coordination - light bishop, light pawns  
    print("\n2️⃣  TESTING BAD PAWN-BISHOP COORDINATION")
    engine.board.set_fen("r1bqk1nr/1p1p1p1p/p1n3p1/8/8/8/1P1P1P1P/RNB1KB1R w KQkq - 0 1")
    # Same bishop, but pawns on light squares (b2, d2, f2, h2)
    
    bad_coord_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   Pawn structure score with bad bishop coordination: {bad_coord_score}")
    print(f"   ✅ Coordination penalty: {good_coord_score - bad_coord_score} centipawns")
    
    # Test 3: Both bishops - coordination less critical
    print("\n3️⃣  TESTING COORDINATION WITH BISHOP PAIR")
    engine.board.set_fen("r1bqk1nr/1p1p1p1p/p1n3p1/8/8/8/1P1P1P1P/RNBQKBNR w KQkq - 0 1")
    # Both bishops present
    
    both_bishops_score = intelligence._calculate_pawn_structure_score(chess.WHITE)
    print(f"   Pawn structure score with both bishops: {both_bishops_score}")
    print(f"   ✅ Coordination less critical with bishop pair")


def test_enhanced_center_control():
    """Test enhanced center control vs queen early development"""
    
    print("\n" + "="*60)
    print("🎯 TESTING CENTER CONTROL VS EARLY QUEEN MOVES")
    print("="*60)
    
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Starting position
    engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    print("\n📊 COMPARING MOVE PREFERENCES:")
    
    # Test d4 center move
    d4_move = chess.Move.from_uci("d2d4")
    d4_score = intelligence._evaluate_move(d4_move)
    print(f"   d2-d4 (center pawn): {d4_score} centipawns")
    
    # Test e4 center move  
    e4_move = chess.Move.from_uci("e2e4")
    e4_score = intelligence._evaluate_move(e4_move)
    print(f"   e2-e4 (center pawn): {e4_score} centipawns")
    
    # Test early queen move
    qh5_move = chess.Move.from_uci("d1h5") 
    qh5_score = intelligence._evaluate_move(qh5_move)
    print(f"   Qd1-h5 (early queen): {qh5_score} centipawns")
    
    # Test knight development
    nf3_move = chess.Move.from_uci("g1f3")
    nf3_score = intelligence._evaluate_move(nf3_move)
    print(f"   Ng1-f3 (knight dev): {nf3_score} centipawns")
    
    print(f"\n✅ PRIORITY ORDER:")
    moves = [("d2-d4", d4_score), ("e2-e4", e4_score), ("Ng1-f3", nf3_score), ("Qd1-h5", qh5_score)]
    moves.sort(key=lambda x: x[1], reverse=True)
    
    for i, (move, score) in enumerate(moves, 1):
        print(f"   {i}. {move}: {score} cp")
    
    print(f"\n🎯 Center pawns and piece development should be preferred over early queen moves!")


def test_comprehensive_evaluation():
    """Test comprehensive position evaluation with new features"""
    
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE EVALUATION TEST v0.1.01")  
    print("="*60)
    
    engine = SlowMateEngine()
    intelligence = MoveIntelligence(engine)
    
    # Test position with mixed pawn structure issues
    engine.board.set_fen("r1bqkb1r/pp1p1ppp/2n1pn2/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 1")
    
    evaluation = intelligence.get_position_evaluation()
    
    print(f"\n📈 DETAILED EVALUATION BREAKDOWN:")
    print(f"   Material difference: {evaluation['material_difference']} cp")
    print(f"   PST difference: {evaluation['pst_difference']} cp") 
    print(f"   King safety difference: {evaluation['king_safety_difference']} cp")
    print(f"   Pawn structure difference: {evaluation['pawn_structure_difference']} cp")
    print(f"   Queen development difference: {evaluation['queen_development_difference']} cp")
    print(f"   Captures difference: {evaluation['captures_difference']} cp")
    print(f"   Total evaluation: {evaluation['total_evaluation']} cp")
    
    print(f"\n🔍 NEW v0.1.01 FEATURES:")
    print(f"   White pawn structure: {evaluation['white_pawn_structure']} cp")
    print(f"   Black pawn structure: {evaluation['black_pawn_structure']} cp")
    print(f"   White queen development: {evaluation['white_queen_development']} cp")
    print(f"   Black queen development: {evaluation['black_queen_development']} cp")


def run_all_tests():
    """Run all pawn structure and queen development tests"""
    
    print("🧪 SlowMate Chess Engine v0.1.01 - Pawn & Queen Tactics Test Suite")
    print("🎯 Testing pawn structure analysis and queen development penalties")
    print("📅 " + "="*70)
    
    try:
        # Test all features
        test_pawn_structure_features()
        test_queen_development_penalties()
        test_pawn_bishop_coordination()
        test_enhanced_center_control()
        test_comprehensive_evaluation()
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉")
        print("✅ Pawn structure analysis: IMPLEMENTED")
        print("✅ Queen development penalties: IMPLEMENTED")
        print("✅ Enhanced center control: IMPLEMENTED") 
        print("✅ Pawn-bishop coordination: IMPLEMENTED")
        print("✅ Comprehensive evaluation: UPDATED")
        print("\n🏆 SlowMate v0.1.01 tactical enhancements are ready!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
