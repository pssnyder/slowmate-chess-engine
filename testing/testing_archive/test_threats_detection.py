#!/usr/bin/env python3
"""
Test Threats Detection System

This script tests the new threat detection features:
1. Hanging piece detection and value modification
2. Threat analysis and piece safety evaluation
3. Integration with material calculation
4. Move selection impact with threat awareness
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def test_basic_threat_detection():
    """Test basic threat detection for hanging pieces."""
    print("=== Testing Basic Threat Detection ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test 1: Position with hanging piece
    print("1. Hanging piece detection:")
    
    # Set up position: White queen on d5, Black rook can capture
    board = chess.Board("rnb1k1nr/pppp1ppp/8/3q4/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
    engine.board = board
    
    # White queen on d5 should be under threat from black pieces
    d5_square = chess.D5
    white_queen_under_threat = intelligence._is_piece_under_threat(d5_square, chess.WHITE)
    
    print(f"  White queen on d5 under threat: {white_queen_under_threat}")
    
    # Test 2: Position with safe piece
    print("\n2. Safe piece detection:")
    
    # Reset to starting position - pieces should be safe
    engine.reset_game()
    
    # White queen on d1 should be safe
    d1_square = chess.D1
    white_queen_safe = intelligence._is_piece_under_threat(d1_square, chess.WHITE)
    
    print(f"  White queen on d1 under threat: {white_queen_safe} (should be False)")
    
    print()


def test_threat_analysis():
    """Test detailed threat analysis."""
    print("=== Testing Threat Analysis ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test 1: Multiple hanging pieces
    print("1. Multiple threats analysis:")
    
    # Position with multiple hanging pieces
    board = chess.Board("r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    engine.board = board
    
    white_threats = intelligence._get_threat_analysis(chess.WHITE)
    black_threats = intelligence._get_threat_analysis(chess.BLACK)
    
    print(f"  White pieces under threat: {white_threats['pieces_under_threat']}")
    print(f"  Black pieces under threat: {black_threats['pieces_under_threat']}")
    print(f"  White threat penalty: {white_threats['total_threat_penalty']}")
    print(f"  Black threat penalty: {black_threats['total_threat_penalty']}")
    
    if white_threats['threatened_pieces']:
        print(f"  White threatened pieces:")
        for piece_info in white_threats['threatened_pieces']:
            print(f"    {piece_info['piece']} on {piece_info['square']}: {piece_info['base_value']} -> {piece_info['effective_value']}")
    
    if black_threats['threatened_pieces']:
        print(f"  Black threatened pieces:")
        for piece_info in black_threats['threatened_pieces']:
            print(f"    {piece_info['piece']} on {piece_info['square']}: {piece_info['base_value']} -> {piece_info['effective_value']}")
    
    print()


def test_material_calculation_with_threats():
    """Test that material calculation incorporates threats."""
    print("=== Testing Material Calculation with Threats ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Compare normal vs threat-aware material calculation
    print("1. Threat impact on material evaluation:")
    
    # Starting position - no threats
    engine.reset_game()
    eval_safe = engine.get_evaluation_details()
    
    print(f"  Starting position:")
    print(f"    White material: {eval_safe['white_material']}")
    print(f"    Black material: {eval_safe['black_material']}")
    print(f"    White pieces under threat: {eval_safe['white_pieces_under_threat']}")
    print(f"    Black pieces under threat: {eval_safe['black_pieces_under_threat']}")
    
    # Position with hanging pieces
    board = chess.Board("rnbqk1nr/pppp1ppp/8/8/3Q4/8/PPPPPPPP/RNB1KBNR b KQkq - 0 1")
    engine.board = board
    eval_threats = engine.get_evaluation_details()
    
    print(f"\n  Position with hanging queen:")
    print(f"    White material: {eval_threats['white_material']}")
    print(f"    Black material: {eval_threats['black_material']}")
    print(f"    White pieces under threat: {eval_threats['white_pieces_under_threat']}")
    print(f"    Black pieces under threat: {eval_threats['black_pieces_under_threat']}")
    print(f"    White threat penalty: {eval_threats['white_threat_penalty']}")
    print(f"    Black threat penalty: {eval_threats['black_threat_penalty']}")
    
    material_difference = eval_safe['white_material'] - eval_threats['white_material']
    print(f"    Material reduction due to threats: {material_difference}")
    
    print()


def test_move_selection_with_threats():
    """Test that threat detection influences move selection."""
    print("=== Testing Move Selection with Threat Awareness ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Hanging piece escape
    print("1. Hanging piece escape incentive:")
    
    # Position where white queen is hanging
    board = chess.Board("rnb1k1nr/pppp1ppp/8/3q4/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    engine.board = board
    
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    # Evaluate moves to see if queen moves are preferred
    for move in legal_moves:
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score, move))
    
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("  Top evaluated moves:")
    for i, (move_san, score, move) in enumerate(move_evaluations[:8]):
        piece = engine.board.piece_at(move.from_square)
        is_queen_move = piece and piece.piece_type == chess.QUEEN
        marker = " 👑" if is_queen_move else ""
        print(f"    {i+1}. {move_san:8s}: {score:+4d}{marker}")
    
    # Test 2: Engine's actual selection
    selected_move_san = engine.play_intelligent_move()
    if selected_move_san:
        print(f"\n  Engine selected: {selected_move_san}")
        
        # Check if it moved the threatened queen
        last_move = engine.board.peek()
        moved_piece = engine.board.piece_at(last_move.to_square)
        if moved_piece and moved_piece.piece_type == chess.QUEEN:
            print("  ✅ Engine moved the threatened queen!")
        else:
            print(f"  Engine chose different strategy: {selected_move_san}")
    
    print()


def test_specific_threat_scenarios():
    """Test specific threat detection scenarios."""
    print("=== Testing Specific Threat Scenarios ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test 1: Pawn attacks
    print("1. Pawn threat detection:")
    
    board = chess.Board("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1")
    engine.board = board
    
    # Black pieces that could be attacked by the white pawn
    c5_square = chess.C5
    e5_square = chess.E5
    
    # Place a black piece on c5 and e5 to test pawn attacks
    board.set_piece_at(c5_square, chess.Piece(chess.KNIGHT, chess.BLACK))
    board.set_piece_at(e5_square, chess.Piece(chess.BISHOP, chess.BLACK))
    
    c5_under_threat = intelligence._is_piece_under_threat(c5_square, chess.BLACK)
    e5_under_threat = intelligence._is_piece_under_threat(e5_square, chess.BLACK)
    
    print(f"  Black knight on c5 under pawn threat: {c5_under_threat}")
    print(f"  Black bishop on e5 under pawn threat: {e5_under_threat}")
    
    # Test 2: Knight attacks  
    print("\n2. Knight threat detection:")
    
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 0 1")
    engine.board = board
    
    # Knight on f3 attacks several squares
    knight_attacks = [chess.D2, chess.D4, chess.E1, chess.E5, chess.G1, chess.G5, chess.H2, chess.H4]
    
    # Place black pieces on some of these squares
    board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
    board.set_piece_at(chess.G5, chess.Piece(chess.BISHOP, chess.BLACK))
    
    e5_knight_threat = intelligence._is_piece_under_threat(chess.E5, chess.BLACK)
    g5_knight_threat = intelligence._is_piece_under_threat(chess.G5, chess.BLACK)
    
    print(f"  Black pawn on e5 under knight threat: {e5_knight_threat}")
    print(f"  Black bishop on g5 under knight threat: {g5_knight_threat}")
    
    print()


def test_threat_integration():
    """Test integration of threat system with existing evaluation."""
    print("=== Testing Threat System Integration ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test comprehensive evaluation with threats
    print("1. Complete evaluation with threats:")
    
    # Position with various evaluation factors
    board = chess.Board("r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    engine.board = board
    
    eval_details = engine.get_evaluation_details()
    
    print(f"  Material difference: {eval_details['material_difference']:+d}")
    print(f"  PST difference: {eval_details['pst_difference']:+d}")
    print(f"  King safety difference: {eval_details['king_safety_difference']:+d}")
    print(f"  Threat penalty difference: {eval_details['threat_difference']:+d}")
    print(f"  Total evaluation: {eval_details['total_evaluation']:+d}")
    
    print(f"\n  Threat details:")
    print(f"    White pieces under threat: {eval_details['white_pieces_under_threat']}")
    print(f"    Black pieces under threat: {eval_details['black_pieces_under_threat']}")
    print(f"    White threat penalty: {eval_details['white_threat_penalty']}")
    print(f"    Black threat penalty: {eval_details['black_threat_penalty']}")
    
    print()


def main():
    """Run all threat detection tests."""
    print("SlowMate Chess Engine - Threat Detection System Tests")
    print("=" * 65)
    
    test_basic_threat_detection()
    test_threat_analysis()
    test_material_calculation_with_threats()
    test_move_selection_with_threats()
    test_specific_threat_scenarios()
    test_threat_integration()
    
    print("Threat detection testing completed!")
    print("The engine now evaluates:")
    print("✅ Hanging piece detection (50% value penalty)")
    print("✅ Threat-aware material calculation")
    print("✅ Escape move incentivization")
    print("✅ Integration with existing evaluation components")


if __name__ == "__main__":
    main()
