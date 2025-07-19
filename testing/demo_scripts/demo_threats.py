#!/usr/bin/env python3
"""
Threats Detection System Demo

Demonstrates the threats detection component of the SlowMate engine.
Shows how threat awareness affects piece values and move selection.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def demo_threat_detection():
    """Demonstrate basic threat detection functionality."""
    print("=" * 60)
    print("SlowMate Chess Engine - Threats Detection Demo")
    print("=" * 60)
    
    engine = IntelligentSlowMateEngine()
    
    # Demo 1: Safe starting position
    print("\n1. Starting Position (Safe):")
    engine.reset_game()
    print(f"   {engine.board.unicode()}")
    
    eval_details = engine.get_evaluation_details()
    print(f"   White pieces under threat: {eval_details['white_pieces_under_threat']}")
    print(f"   Black pieces under threat: {eval_details['black_pieces_under_threat']}")
    print(f"   White material: {eval_details['white_material']} (no threat penalty)")
    print(f"   Black material: {eval_details['black_material']} (no threat penalty)")
    
    # Demo 2: Hanging piece scenario
    print("\n2. Hanging Queen Scenario:")
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/3Q4/8/PPPPPPPP/RNB1KBNR b KQkq - 1 2")
    engine.board = board
    print(f"   {engine.board.unicode()}")
    
    eval_details = engine.get_evaluation_details()
    print(f"   White pieces under threat: {eval_details['white_pieces_under_threat']}")
    print(f"   Black pieces under threat: {eval_details['black_pieces_under_threat']}")
    print(f"   White material: {eval_details['white_material']} (queen at risk!)")
    print(f"   Black material: {eval_details['black_material']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    
    # Demo 3: Show how engine responds to threats
    print("\n3. Engine Response to Threats:")
    print("   Engine will try to move the threatened queen...")
    
    move = engine.play_intelligent_move()
    print(f"   Engine selected: {move}")
    print(f"   {engine.board.unicode()}")
    
    # Check if threat was resolved
    eval_after = engine.get_evaluation_details()
    print(f"   White pieces under threat after move: {eval_after['white_pieces_under_threat']}")
    print(f"   White threat penalty after move: {eval_after['white_threat_penalty']}")
    
    # Demo 4: Multiple threats scenario
    print("\n4. Multiple Pieces Under Attack:")
    board = chess.Board("r1b1k2r/pppp1ppp/2n2n2/2b1p1q1/2B1P1Q1/2N2N2/PPPP1PPP/R1B1K2R w KQkq - 4 6")
    engine.board = board
    print(f"   {engine.board.unicode()}")
    
    eval_details = engine.get_evaluation_details()
    print(f"   White pieces under threat: {eval_details['white_pieces_under_threat']}")
    print(f"   Black pieces under threat: {eval_details['black_pieces_under_threat']}")
    print(f"   White threat penalty: {eval_details['white_threat_penalty']}")
    print(f"   Black threat penalty: {eval_details['black_threat_penalty']}")
    
    # Get detailed threat analysis
    white_threats = engine.intelligence._get_threat_analysis(chess.WHITE)
    black_threats = engine.intelligence._get_threat_analysis(chess.BLACK)
    
    if white_threats['threatened_pieces']:
        print(f"   White threatened pieces:")
        for piece_info in white_threats['threatened_pieces']:
            print(f"     {piece_info['piece']} on {piece_info['square']}: {piece_info['base_value']} -> {piece_info['effective_value']}")
    
    if black_threats['threatened_pieces']:
        print(f"   Black threatened pieces:")
        for piece_info in black_threats['threatened_pieces']:
            print(f"     {piece_info['piece']} on {piece_info['square']}: {piece_info['base_value']} -> {piece_info['effective_value']}")
    
    print(f"\n5. Key Threat System Features:")
    print(f"   ✅ Automatic threat detection using python-chess")
    print(f"   ✅ 50% value penalty for threatened pieces")
    print(f"   ✅ Escape move incentivization")
    print(f"   ✅ Integration with material evaluation")
    print(f"   ✅ No victim/attacker exchange logic (handled by captures)")
    
    print("\n" + "=" * 60)
    print("Threats detection system successfully implemented!")
    print("Version 0.0.10 - Phase 1 (Threats) Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_threat_detection()
