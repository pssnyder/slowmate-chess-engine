#!/usr/bin/env python3
"""
Investigate Move 20 Issue - Missing Rook Capture (Fixed)

Analyzing why the engine chose Bb7 instead of capturing a rook.
Position after move 19: ...Ne3, White to move on move 20.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def analyze_move_20_issue_fixed():
    """Analyze the specific position where engine missed rook capture."""
    print("=" * 70)
    print("MOVE 20 ANALYSIS - Missing Rook Capture Investigation (Fixed)")
    print("=" * 70)
    
    engine = IntelligentSlowMateEngine()
    
    # Start from standard position and play the game
    board = chess.Board()
    
    moves = [
        "Nc3", "b5", "Ne4", "f5", "Nc5", "e6", "Nb7", "Qe7", 
        "a3", "d6", "h4", "g5", "hxg5", "Qf7", "g6", "Qd7", 
        "gxh7", "Rxh7", "Rxh7", "Qxh7", "Nh3", "Nh6", "Ng5", "Qd7", 
        "Nc5", "Qd8", "Ncxe6", "Bxe6", "Nxe6", "Qc8", "g4", "Kd7", 
        "Nxc7", "Kxc7", "gxf5", "Nxf5", "Bg2", "Ne3"
    ]
    
    print("🔍 RECONSTRUCTING POSITION...")
    for move_str in moves:
        move = board.parse_san(move_str)
        board.push(move)
    
    engine.board = board
    print(f"   Position after 19...Ne3 (White to move):")
    print(f"   FEN: {board.fen()}")
    print(f"   {board.unicode()}")
    
    # Analyze the position carefully
    print(f"\n📊 DETAILED ANALYSIS:")
    
    # Get all legal moves
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    
    print(f"   Total legal moves: {len(legal_moves)}")
    print(f"   Capture moves: {len(capture_moves)}")
    
    # Analyze each capture move
    print(f"\n   🎯 CAPTURE ANALYSIS:")
    for move in capture_moves:
        move_san = board.san(move)
        captured_piece = board.piece_at(move.to_square)
        capture_eval = engine.intelligence._evaluate_capture_move(move)
        move_score = engine.intelligence._evaluate_move(move)
        
        print(f"     {move_san}: captures {captured_piece.symbol() if captured_piece else '?'}, "
              f"eval {capture_eval['net_score']}, move score {move_score}")
    
    # Test specifically what the engine chooses
    print(f"\n🤖 ENGINE DECISION TEST:")
    eval_details = engine.get_evaluation_details()
    print(f"   Current position evaluation: {eval_details['total_evaluation']}")
    
    # Let's manually test the top scoring moves
    print(f"\n   📈 SCORING TOP MOVES:")
    move_scores = []
    
    for move in legal_moves[:15]:  # Test first 15 moves
        try:
            move_san = board.san(move)
            move_score = engine.intelligence._evaluate_move(move)
            move_scores.append((move, move_san, move_score))
        except Exception as e:
            print(f"   Error evaluating move {move}: {e}")
    
    # Sort by score (highest first)
    move_scores.sort(key=lambda x: x[2], reverse=True)
    
    print(f"   Top 10 moves by evaluation score:")
    for i, (move, move_san, score) in enumerate(move_scores[:10]):
        is_capture = board.is_capture(move)
        capture_info = ""
        if is_capture:
            captured = board.piece_at(move.to_square)
            capture_info = f" (captures {captured.symbol() if captured else '?'})"
        
        print(f"     {i+1}. {move_san}: {score}{capture_info}")
    
    # Check specifically for Bxa8 (rook capture) and Bb7
    rook_capture_move = None
    bb7_move = None
    
    for move in legal_moves:
        move_san = board.san(move)
        if move_san == "Bxa8":
            rook_capture_move = move
        elif move_san == "Bb7":
            bb7_move = move
    
    if rook_capture_move and bb7_move:
        print(f"\n   🔍 SPECIFIC COMPARISON:")
        
        rook_score = engine.intelligence._evaluate_move(rook_capture_move)
        bb7_score = engine.intelligence._evaluate_move(bb7_move)
        
        print(f"   Bxa8 (rook capture) score: {rook_score}")
        print(f"   Bb7 (bishop development) score: {bb7_score}")
        print(f"   Difference: {bb7_score - rook_score} (positive means Bb7 is preferred)")
        
        # Check what happens after Bb7 - is the bishop threatened?
        print(f"\n   🚨 CHECKING THREATS AFTER BB7:")
        engine.board.push(bb7_move)
        
        bb7_square = bb7_move.to_square
        bishop_under_threat = engine.intelligence._is_piece_under_threat(bb7_square, chess.WHITE)
        
        # Get threat details
        eval_after_bb7 = engine.get_evaluation_details()
        
        engine.board.pop()
        
        print(f"   Bishop on b7 under threat: {bishop_under_threat}")
        print(f"   White threat penalty after Bb7: {eval_after_bb7['white_threat_penalty']}")
        
        if bishop_under_threat:
            print(f"   ❌ THREATS SYSTEM FAILED: Bb7 puts bishop under threat!")
            print(f"   This violates our threat evaluation expectations.")
    
    # Let engine actually choose
    selected_move = engine.play_intelligent_move()
    print(f"\n   Final engine choice: {selected_move}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    analyze_move_20_issue_fixed()
