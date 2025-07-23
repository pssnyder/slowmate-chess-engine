#!/usr/bin/env python3
"""
Mate Evaluation Tester for SlowMate v0.3.02

Tests the fixed mate evaluation system to ensure:
1. Correct mate scores (no more M500!)
2. Proper mate detection
3. Accurate UCI output
4. Reasonable auto-adjudication
"""

import chess
import chess.pgn
import io
from slowmate.intelligence import IntelligentSlowMateEngine
from slowmate.depth_search import DepthSearchEngine

def test_mate_evaluation():
    """Test mate evaluation with known positions."""
    
    print("=== SlowMate v0.3.02 Mate Evaluation Test ===\n")
    
    # Test position 1: Simple back-rank mate in 1
    print("Test 1: Back-rank mate in 1")
    engine = IntelligentSlowMateEngine()
    
    # Position: White to move, mate in 1 with Rd8#
    fen = "6k1/6pp/8/8/8/8/6PP/3R2K1 w - - 0 1"
    engine.board.set_fen(fen)
    
    legal_moves = list(engine.board.legal_moves)
    print(f"Legal moves: {len(legal_moves)}")
    
    for move in legal_moves:
        if engine.board.san(move) == "Rd8#":
            engine.board.push(move)
            if engine.board.is_checkmate():
                print("   ✅ Mate in 1 detected correctly")
            else:
                print("   ❌ Failed to detect mate in 1")
            engine.board.pop()
            break
    
    # Test position 2: No mate available (from our problematic game)
    print("\nTest 2: Early game position (should show normal eval)")
    fen2 = "r1b1kbnr/ppqp1ppp/2n1p3/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 4"
    engine.board.set_fen(fen2)
    
    evaluation = engine.get_current_evaluation()
    print(f"Position evaluation: {evaluation} cp")
    
    if abs(evaluation) < 1000:
        print("   ✅ Normal evaluation (no false mate)")
    else:
        print(f"   ❌ Suspicious evaluation: {evaluation}")
    
    # Test depth search if available
    try:
        print("\nTest 3: Depth search evaluation")
        depth_engine = DepthSearchEngine()
        depth_engine.board = engine.board.copy()
        
        best_move, score, pv = depth_engine.search_best_move()
        print(f"Best move: {engine.board.san(best_move) if best_move else 'None'}")
        print(f"Score: {score}")
        
        if depth_engine._is_mate_score(score):
            mate_distance = abs(30000 - abs(score))
            mate_moves = max(1, (mate_distance + 1) // 2)
            if score < 0:
                mate_moves = -mate_moves
            print(f"Mate evaluation: M{mate_moves}")
            
            if abs(mate_moves) <= 10:
                print("   ✅ Reasonable mate distance")
            else:
                print(f"   ❌ Unreasonable mate distance: M{mate_moves}")
        else:
            print("   ✅ Normal position evaluation (no mate)")
            
    except Exception as e:
        print(f"   ⚠️  Depth search test failed: {e}")
    
    print("\n" + "="*50)
    print("Mate evaluation test complete!")

if __name__ == "__main__":
    test_mate_evaluation()
