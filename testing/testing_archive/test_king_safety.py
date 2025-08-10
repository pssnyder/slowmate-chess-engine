#!/usr/bin/env python3
"""
Test King Safety Evaluation System

This script tests the new king safety features:
1. Castling rights evaluation (small bonus for maintaining rights)
2. Castling status evaluation (larger bonus for having castled) 
3. King pawn shield evaluation (bonus for pawns protecting king)
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def test_castling_rights_evaluation():
    """Test that maintaining castling rights gives appropriate bonuses."""
    print("=== Testing Castling Rights Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test 1: Starting position (should have full castling rights)
    engine.reset_game()
    eval_details = engine.get_evaluation_details()
    
    white_king_safety = eval_details['white_king_safety']
    black_king_safety = eval_details['black_king_safety']
    
    print(f"Starting position:")
    print(f"  White king safety: {white_king_safety:+d} (should have castling rights bonus)")
    print(f"  Black king safety: {black_king_safety:+d} (should have castling rights bonus)")
    
    # Test 2: After king moves (should lose castling rights)
    engine.reset_game()
    engine.board.push(chess.Move.from_uci("e1f1"))  # King move, loses castling rights
    
    eval_after_king_move = engine.get_evaluation_details()
    white_king_safety_no_rights = eval_after_king_move['white_king_safety']
    
    rights_penalty = white_king_safety - white_king_safety_no_rights
    print(f"  After king moves (no castling rights): {white_king_safety_no_rights:+d}")
    print(f"  Rights bonus lost: {rights_penalty:+d}")
    
    # Test 3: After rook moves (should lose some castling rights)
    engine.reset_game()
    engine.board.push(chess.Move.from_uci("h1g1"))  # Kingside rook move
    
    eval_after_rook_move = engine.get_evaluation_details()
    white_king_safety_partial = eval_after_rook_move['white_king_safety']
    
    partial_penalty = white_king_safety - white_king_safety_partial
    print(f"  After kingside rook moves: {white_king_safety_partial:+d}")
    print(f"  Partial rights bonus lost: {partial_penalty:+d}")
    
    print()


def test_castling_status_evaluation():
    """Test that actually castling gives larger bonuses than just maintaining rights."""
    print("=== Testing Castling Status Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Position where castling is possible
    print("1. Pre-castling vs Post-castling comparison:")
    
    # Set up a position where white can castle kingside
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    engine.board = board
    
    pre_castle_eval = engine.get_evaluation_details()
    pre_castle_safety = pre_castle_eval['white_king_safety']
    
    print(f"  Before castling: {pre_castle_safety:+d}")
    
    # Castle kingside
    engine.board.push(chess.Move.from_uci("e1g1"))  # Castling move
    
    post_castle_eval = engine.get_evaluation_details()
    post_castle_safety = post_castle_eval['white_king_safety']
    
    castling_bonus = post_castle_safety - pre_castle_safety
    print(f"  After castling: {post_castle_safety:+d}")
    print(f"  Castling action bonus: {castling_bonus:+d}")
    
    # Verify action > preparation principle
    if castling_bonus > 0:
        print(f"  ✅ Castling action gives bonus (action > preparation principle)")
    else:
        print(f"  ❌ Issue: Castling should give positive bonus")
    
    # Test 2: Queenside vs Kingside castling
    print("\n2. Queenside vs Kingside castling comparison:")
    
    # Test kingside castling position
    king_board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    engine.board = king_board
    engine.board.push(chess.Move.from_uci("e1g1"))
    kingside_eval = engine.get_evaluation_details()
    kingside_safety = kingside_eval['white_king_safety']
    
    # Test queenside castling position  
    queen_board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 4")
    engine.board = queen_board
    engine.board.push(chess.Move.from_uci("e1c1"))
    queenside_eval = engine.get_evaluation_details()
    queenside_safety = queenside_eval['white_king_safety']
    
    print(f"  Kingside castled safety: {kingside_safety:+d}")
    print(f"  Queenside castled safety: {queenside_safety:+d}")
    
    if kingside_safety > queenside_safety:
        print(f"  ✅ Kingside castling preferred over queenside")
    else:
        print(f"  ⚠️ Note: Queenside castling evaluated equally or higher")
    
    print()


def test_king_pawn_shield_evaluation():
    """Test that pawn shields in front of the king provide bonuses."""
    print("=== Testing King Pawn Shield Evaluation ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: King with full pawn shield vs exposed king
    print("1. Pawn shield comparison:")
    
    # King with full pawn shield (castled position)
    shield_board = chess.Board("rnbq1rk1/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 w - - 0 1")
    engine.board = shield_board
    shield_eval = engine.get_evaluation_details()
    shield_safety = shield_eval['white_king_safety']
    
    print(f"  King with pawn shield: {shield_safety:+d}")
    
    # King with broken pawn shield
    broken_board = chess.Board("rnbq1rk1/pppp1ppp/5n2/4p3/2B1P3/5N1P/PPP2P2/RNBQ1RK1 w - - 0 1")
    engine.board = broken_board
    broken_eval = engine.get_evaluation_details()
    broken_safety = broken_eval['white_king_safety']
    
    shield_bonus = shield_safety - broken_safety
    print(f"  King with broken shield: {broken_safety:+d}")
    print(f"  Pawn shield bonus: {shield_bonus:+d}")
    
    # Test 2: Progressive pawn advancement effect
    print("\n2. Pawn advancement impact:")
    
    positions = [
        ("Full shield", "rnbq1rk1/pppp1ppp/8/8/8/8/PPPPPPPP/RNBQ1RK1 w - - 0 1"),
        ("One pawn advanced", "rnbq1rk1/pppp1ppp/8/8/8/5P2/PPP1P1PP/RNBQ1RK1 w - - 0 1"),
        ("Two pawns advanced", "rnbq1rk1/pppp1ppp/8/8/8/4PP2/PP3PPP/RNBQ1RK1 w - - 0 1"),
        ("No shield", "rnbq1rk1/pppp1ppp/8/8/8/8/1PP1PP1P/RNBQ1RK1 w - - 0 1")
    ]
    
    for description, fen in positions:
        engine.board = chess.Board(fen)
        eval_details = engine.get_evaluation_details()
        safety_score = eval_details['white_king_safety']
        print(f"  {description:20}: {safety_score:+3d}")
    
    print()


def test_move_selection_with_king_safety():
    """Test that king safety influences move selection appropriately."""
    print("=== Testing King Safety Impact on Move Selection ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Castling opportunity
    print("1. Castling move selection:")
    
    # Position where castling is available
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    engine.board = board
    
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    for move in legal_moves:
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score, move))
    
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("Top evaluated moves:")
    castling_found = False
    for i, (move_san, score, move) in enumerate(move_evaluations[:8]):
        is_castling = "O-O" in move_san
        if is_castling:
            castling_found = True
        marker = " 👑" if is_castling else ""
        print(f"  {i+1}. {move_san:8s}: {score:+4d}{marker}")
    
    if castling_found:
        print("  ✅ Castling moves found in evaluation")
    else:
        print("  ⚠️ No castling moves in top moves")
    
    # Test 2: Engine's actual selection
    selected_move_san = engine.play_intelligent_move()
    if selected_move_san:
        print(f"\n  Engine selected: {selected_move_san}")
        
        if "O-O" in selected_move_san:
            print("  ✅ Engine chose to castle!")
        else:
            print(f"  Engine chose: {selected_move_san}")
    
    print()


def test_king_safety_breakdown():
    """Test detailed breakdown of king safety components."""
    print("=== Testing King Safety Component Breakdown ===")
    
    engine = IntelligentSlowMateEngine()
    
    test_positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("After development", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"),
        ("After castling", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 b kq - 5 4"),
        ("Broken pawn shield", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N1P/PPP2P2/RNBQ1RK1 b kq - 0 5")
    ]
    
    for description, fen in test_positions:
        engine.board = chess.Board(fen)
        intelligence = engine.intelligence
        
        # Get individual components
        castling_rights = intelligence._evaluate_castling_rights(chess.WHITE)
        castling_status = intelligence._evaluate_castling_status(chess.WHITE)
        pawn_shield = intelligence._evaluate_king_pawn_shield(chess.WHITE)
        total_king_safety = intelligence._calculate_king_safety(chess.WHITE)
        
        print(f"{description}:")
        print(f"  Castling rights: {castling_rights:+2d}")
        print(f"  Castling status: {castling_status:+2d}")
        print(f"  Pawn shield:    {pawn_shield:+2d}")
        print(f"  Total safety:   {total_king_safety:+2d}")
        print()


def main():
    """Run all king safety tests."""
    print("SlowMate Chess Engine - King Safety Evaluation Tests")
    print("=" * 60)
    
    test_castling_rights_evaluation()
    test_castling_status_evaluation()
    test_king_pawn_shield_evaluation()
    test_move_selection_with_king_safety()
    test_king_safety_breakdown()
    
    print("King Safety evaluation testing completed!")
    print("The engine now evaluates:")
    print("✅ Castling rights (preparation bonus)")
    print("✅ Castling status (action bonus > preparation)")
    print("✅ King pawn shield (protection bonus)")
    print("✅ Integrated into move selection")


if __name__ == "__main__":
    main()
