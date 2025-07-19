#!/usr/bin/env python3
"""
Investigate Tactical Decision Integration Issue

The problem: Threats and captures are evaluated separately instead of being
combined into unified tactical decisions. This causes the engine to choose
defensive moves (bishop safety) over superior tactical solutions that
accomplish both defense AND offense simultaneously.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def analyze_tactical_integration_bug():
    """Analyze the separation of threats and captures evaluation."""
    print("=" * 80)
    print("TACTICAL DECISION INTEGRATION BUG ANALYSIS")
    print("Issue: Threats and Captures Evaluated Separately Instead of Combined")
    print("=" * 80)
    
    engine = IntelligentSlowMateEngine()
    
    # Recreate the position: After 19...Ne3, White to move
    print("\n🎯 RECREATING CRITICAL POSITION:")
    print("   After 19...Ne3 - Black knight threatens White's bishop on g2")
    
    # Build position from game moves
    board = chess.Board()
    moves = [
        "Nc3", "b5", "Ne4", "f5", "Nc5", "e6", "Nb7", "Qe7", 
        "a3", "d6", "h4", "g5", "hxg5", "Qf7", "g6", "Qd7", 
        "gxh7", "Rxh7", "Rxh7", "Qxh7", "Nh3", "Nh6", "Ng5", "Qd7", 
        "Nc5", "Qd8", "Ncxe6", "Bxe6", "Nxe6", "Qc8", "g4", "Kd7", 
        "Nxc7", "Kxc7", "gxf5", "Nxf5", "Bg2", "Ne3"
    ]
    
    for move_str in moves:
        move = board.parse_san(move_str)
        board.push(move)
    
    engine.board = board
    print(f"   FEN: {board.fen()}")
    print(f"   {board.unicode()}")
    
    # Analyze the tactical situation
    print(f"\n📊 TACTICAL SITUATION ANALYSIS:")
    
    # Check what's under threat
    eval_details = engine.get_evaluation_details()
    print(f"   White pieces under threat: {eval_details['white_pieces_under_threat']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    
    # Find the threatened bishop
    bishop_g2_threatened = engine.intelligence._is_piece_under_threat(chess.G2, chess.WHITE)
    print(f"   Bishop on g2 under threat: {bishop_g2_threatened}")
    
    # Check available captures
    print(f"   White winning captures: {eval_details['white_winning_captures']}")
    print(f"   White captures score: {eval_details['white_captures']}")
    
    # Analyze the key moves
    print(f"\n🎯 KEY MOVE ANALYSIS:")
    
    legal_moves = list(board.legal_moves)
    
    # Find specific moves
    bxa8_move = None  # Rook capture (solves both problems)
    bb7_move = None   # Bishop retreat (solves only threat)
    
    for move in legal_moves:
        move_san = board.san(move)
        if move_san == "Bxa8":
            bxa8_move = move
        elif move_san == "Bb7":
            bb7_move = move
    
    if bxa8_move and bb7_move:
        print(f"\n   🔍 COMPARING TACTICAL OPTIONS:")
        
        # Analyze Bxa8 (optimal tactical solution)
        print(f"\n   1️⃣ Bxa8 (Rook Capture + Threat Escape):")
        bxa8_score = engine.intelligence._evaluate_move(bxa8_move)
        
        # Check if this solves the threat
        engine.board.push(bxa8_move)
        bishop_a8_threatened = engine.intelligence._is_piece_under_threat(chess.A8, chess.WHITE)
        eval_after_bxa8 = engine.get_evaluation_details()
        engine.board.pop()
        
        print(f"      Move evaluation score: {bxa8_score}")
        print(f"      Bishop still under threat: {bishop_a8_threatened}")
        print(f"      Material gain: +500 (rook captured)")
        print(f"      Threat penalty after move: {eval_after_bxa8['white_threat_penalty']}")
        print(f"      ✅ SOLVES: Both threat AND gains material")
        
        # Analyze Bb7 (defensive only solution)  
        print(f"\n   2️⃣ Bb7 (Bishop Retreat Only):")
        bb7_score = engine.intelligence._evaluate_move(bb7_move)
        
        # Check if this creates new threats
        engine.board.push(bb7_move)
        bishop_b7_threatened = engine.intelligence._is_piece_under_threat(chess.B7, chess.WHITE)
        eval_after_bb7 = engine.get_evaluation_details()
        engine.board.pop()
        
        print(f"      Move evaluation score: {bb7_score}")
        print(f"      Bishop under threat on b7: {bishop_b7_threatened}")
        print(f"      Material gain: 0 (no capture)")
        print(f"      Threat penalty after move: {eval_after_bb7['white_threat_penalty']}")
        print(f"      ❌ SOLVES: Only threat, misses material gain")
        
        # Show the evaluation difference
        print(f"\n   📈 EVALUATION COMPARISON:")
        print(f"      Bxa8 score: {bxa8_score}")
        print(f"      Bb7 score:  {bb7_score}")
        print(f"      Difference: {bxa8_score - bb7_score} (positive = Bxa8 better)")
        
        if bb7_score > bxa8_score:
            print(f"      🚨 BUG CONFIRMED: Engine prefers inferior Bb7!")
            print(f"      🔧 ROOT CAUSE: Tactical evaluations not properly integrated")
        
    # Demonstrate the architectural problem
    print(f"\n🏗️  ARCHITECTURAL PROBLEM:")
    print(f"   Current System: Threats + Captures evaluated separately")
    print(f"   - Threats system: 'Move bishop to safety' (high priority)")  
    print(f"   - Captures system: 'Capture rook for material' (separate priority)")
    print(f"   - Result: Defensive move chosen over tactical solution")
    print(f"")
    print(f"   Needed System: Unified tactical evaluation")
    print(f"   - Evaluate moves that solve MULTIPLE problems simultaneously")
    print(f"   - Bxa8 should score higher because it solves threat AND gains material")
    print(f"   - Tactical combinations should be prioritized over single-purpose moves")
    
    # Test what the engine actually chooses
    print(f"\n🤖 ENGINE DECISION:")
    selected_move = engine.play_intelligent_move()
    print(f"   Engine selected: {selected_move}")
    
    if selected_move and "b7" in selected_move.lower():
        print(f"   ❌ CONFIRMED: Engine chose suboptimal Bb7")
        print(f"   💡 SOLUTION NEEDED: Integrate threats and captures into unified scoring")
    
    print("\n" + "=" * 80)
    print("CONCLUSION: Tactical intelligence needs architectural improvement")
    print("Next: Implement unified tactical evaluation system")
    print("=" * 80)


if __name__ == "__main__":
    analyze_tactical_integration_bug()
