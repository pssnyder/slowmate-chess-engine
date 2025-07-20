#!/usr/bin/env python3
"""
Test Modern Tactical Evaluation System

This script tests the redesigned threat and capture evaluation system
to ensure it works correctly and fixes the original tactical bug.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def test_modern_threat_evaluation():
    """Test the new piece safety evaluation system."""
    print("=" * 70)
    print("TESTING MODERN THREAT EVALUATION")
    print("=" * 70)
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Safe piece (no penalty)
    print("\n1. Safe piece evaluation:")
    engine.reset_game()
    eval_details = engine.get_evaluation_details()
    print(f"   Starting position - White material: {eval_details['white_material']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    
    # Test 2: Hanging piece (reasonable penalty)
    print("\n2. Hanging piece evaluation:")
    board = chess.Board("rnb1k1nr/pppp1ppp/8/3q4/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    engine.board = board
    eval_details = engine.get_evaluation_details()
    print(f"   Hanging queen position - White material: {eval_details['white_material']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    
    # Test 3: Defended piece (small or no penalty)
    print("\n3. Defended piece evaluation:")
    board = chess.Board("rnb1k1nr/pppp1ppp/8/3q4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
    engine.board = board
    eval_details = engine.get_evaluation_details()
    print(f"   Defended queen position - White material: {eval_details['white_material']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    print("   (Queen is defended by pawn, so penalty should be small)")

def test_modern_capture_evaluation():
    """Test the new direct capture evaluation system."""
    print("\n" + "=" * 70)
    print("TESTING MODERN CAPTURE EVALUATION")
    print("=" * 70)
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Good capture (queen takes pawn)
    print("\n1. Good capture evaluation:")
    board = chess.Board("4k3/8/8/8/3Q4/3p4/8/4K3 w - - 0 1")
    engine.board = board
    
    captures_analysis = engine.intelligence._get_captures_analysis(chess.WHITE)
    print(f"   White captures available: {len(captures_analysis['winning_captures'])}")
    if captures_analysis['winning_captures']:
        capture = captures_analysis['winning_captures'][0]
        print(f"   Best capture: {capture['move']} - SEE: {capture['see_score']}")
    
    # Test 2: Bad capture (pawn takes queen)
    print("\n2. Bad capture evaluation:")
    board = chess.Board("4k3/8/8/8/4p3/3Q4/8/4K3 b - - 0 1")
    engine.board = board
    
    captures_analysis = engine.intelligence._get_captures_analysis(chess.BLACK)
    print(f"   Black captures available: {len(captures_analysis['losing_captures'])}")
    if captures_analysis['losing_captures']:
        capture = captures_analysis['losing_captures'][0]
        print(f"   Bad capture: {capture['move']} - SEE: {capture['see_score']}")

def test_tactical_combination():
    """Test the crucial tactical combination scenario."""
    print("\n" + "=" * 70)
    print("TESTING TACTICAL COMBINATION (ORIGINAL BUG SCENARIO)")
    print("=" * 70)
    
    # Recreate the problematic position
    fen = "rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20"
    
    engine = IntelligentSlowMateEngine()
    engine.board = chess.Board(fen)
    
    print(f"\nPosition: {fen}")
    print("White to move. Bishop on g2 is under threat from black knight on e3.")
    print("Options: Bxa8 (capture rook + escape) vs Bb7 (retreat only)")
    
    # Test both key moves
    legal_moves = list(engine.board.legal_moves)
    
    bxa8_move = None
    bb7_move = None
    
    for move in legal_moves:
        move_san = engine.board.san(move)
        if move_san == "Bxa8":
            bxa8_move = move
        elif move_san == "Bb7":
            bb7_move = move
    
    if bxa8_move and bb7_move:
        print("\n🔍 MOVE EVALUATION COMPARISON:")
        
        bxa8_score = engine.intelligence._evaluate_move(bxa8_move)
        bb7_score = engine.intelligence._evaluate_move(bb7_move)
        
        print(f"   Bxa8 (capture + escape): {bxa8_score:+d}")
        print(f"   Bb7 (retreat only):      {bb7_score:+d}")
        print(f"   Difference:              {bxa8_score - bb7_score:+d}")
        
        if bxa8_score > bb7_score:
            print("   ✅ SUCCESS: Engine correctly prefers tactical combination!")
        else:
            print("   ❌ FAILURE: Engine still prefers simple retreat!")
    
    # Test actual engine decision
    print("\n🤖 ENGINE DECISION:")
    selected_move = engine.play_intelligent_move()
    print(f"   Engine selected: {selected_move}")
    
    if selected_move and "xa8" in selected_move:
        print("   ✅ CORRECT: Engine chose the tactical combination!")
    else:
        print("   ❌ INCORRECT: Engine chose defensive move over tactics!")

def main():
    """Run all modern tactical evaluation tests."""
    test_modern_threat_evaluation()
    test_modern_capture_evaluation()
    test_tactical_combination()
    
    print("\n" + "=" * 70)
    print("MODERN TACTICAL EVALUATION TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
