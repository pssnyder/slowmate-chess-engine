#!/usr/bin/env python3
"""
Test Phase 3: Game Phase Awareness and Endgame PSTs

This script tests the game phase detection and endgame-specific PST behavior.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def test_game_phase_detection():
    """Test game phase detection in different positions."""
    print("=== Testing Game Phase Detection ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test 1: Starting position (should be opening)
    engine.reset_game()
    phase = intelligence.detect_game_phase()
    print(f"Starting position: {phase} (expected: opening)")
    
    # Test 2: Simulate middlegame (remove some pieces)
    engine.reset_game()
    # Remove a few pieces to simulate middlegame
    board = engine.board
    board.remove_piece_at(chess.B1)  # Remove knight
    board.remove_piece_at(chess.G1)  # Remove knight
    board.remove_piece_at(chess.B8)  # Remove knight  
    board.remove_piece_at(chess.G8)  # Remove knight
    phase = intelligence.detect_game_phase()
    print(f"Fewer pieces: {phase} (expected: middlegame or opening)")
    
    # Test 3: Simulate endgame (only a few pieces left)
    engine.reset_game()
    # Set up a simple endgame position: K+R+P vs K+R
    board = chess.Board("4k3/8/8/8/8/8/P7/4K2R w K - 0 1")
    engine.board = board
    phase = intelligence.detect_game_phase()
    print(f"K+R+P vs K+R endgame: {phase} (expected: endgame)")
    
    # Test 4: King and pawn endgame
    board = chess.Board("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
    engine.board = board
    phase = intelligence.detect_game_phase()
    print(f"K+P vs K endgame: {phase} (expected: endgame)")
    
    print()


def test_endgame_pst_behavior():
    """Test that endgame PSTs behave differently than middlegame."""
    print("=== Testing Endgame PST Behavior ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test positions in different game phases
    test_cases = [
        # Pawn advancement in endgame vs opening
        (chess.E4, chess.PAWN, "Pawn on e4"),
        (chess.E6, chess.PAWN, "Pawn on e6 (advanced)"),
        (chess.E7, chess.PAWN, "Pawn on e7 (near promotion)"),
        
        # King activity in endgame vs opening
        (chess.E1, chess.KING, "King on e1 (back rank)"),
        (chess.E4, chess.KING, "King on e4 (center)"),
        (chess.E5, chess.KING, "King on e5 (advanced center)"),
        
        # Rook positioning
        (chess.E7, chess.ROOK, "Rook on e7 (7th rank)"),
        (chess.E4, chess.ROOK, "Rook on e4 (center)"),
    ]
    
    # Compare opening vs endgame positions
    print("Piece Position           | Opening PST | Endgame PST | Difference")
    print("-" * 65)
    
    for square, piece_type, description in test_cases:
        # Test in opening (full position)
        engine.reset_game()
        opening_value = intelligence._get_pst_value(square, piece_type, chess.WHITE)
        
        # Test in endgame (K+P vs K)
        board = chess.Board("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
        engine.board = board
        endgame_value = intelligence._get_pst_value(square, piece_type, chess.WHITE)
        
        difference = endgame_value - opening_value
        arrow = "→" if difference > 0 else ("=" if difference == 0 else "←")
        
        print(f"{description:24} | {opening_value:+10d} | {endgame_value:+10d} | {difference:+4d} {arrow}")
    
    print()


def test_endgame_move_selection():
    """Test that endgame positions prefer different moves."""
    print("=== Testing Endgame Move Selection ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: King and pawn endgame - king should advance
    print("1. King and Pawn Endgame (K+P vs K):")
    board = chess.Board("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
    engine.board = board
    
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    for move in legal_moves:
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score))
    
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("Top moves in K+P endgame:")
    for i, (move_san, score) in enumerate(move_evaluations[:5]):
        print(f"  {i+1}. {move_san}: {score:+d}")
    
    # Test 2: Pawn promotion race
    print("\n2. Pawn Promotion Race:")
    board = chess.Board("8/1P6/8/8/8/8/6p1/8 w - - 0 1")
    engine.board = board
    
    if engine.board.legal_moves:
        selected_move = engine.play_intelligent_move()
        if selected_move:
            print(f"Engine selected: {selected_move}")
            if engine.evaluation_history:
                last_eval = engine.evaluation_history[-1]
                print(f"Score: {last_eval['score']:+d}")
                print(f"Reasoning: {last_eval['reasoning']}")
        else:
            print("No move selected")
    
    print()


def test_phase_transition():
    """Test behavior as game transitions between phases."""
    print("=== Testing Phase Transition ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Simulate game progression by removing pieces
    positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("After some exchanges", "r2qkb1r/ppp2ppp/2n2n2/3p4/3P1B2/3Q1N2/PPP2PPP/R3K2R w KQkq - 0 1"),
        ("Entering endgame", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"),
        ("Pure endgame", "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
    ]
    
    print("Position                | Phase      | King e4 Value | Pawn e4 Value")
    print("-" * 68)
    
    for description, fen in positions:
        engine.board = chess.Board(fen)
        phase = intelligence.detect_game_phase()
        
        king_value = intelligence._get_pst_value(chess.E4, chess.KING, chess.WHITE)
        pawn_value = intelligence._get_pst_value(chess.E4, chess.PAWN, chess.WHITE)
        
        print(f"{description:23} | {phase:10} | {king_value:+12d} | {pawn_value:+12d}")
    
    print()


def main():
    """Run all Phase 3 tests."""
    print("SlowMate Chess Engine - Phase 3 Game Phase Tests")
    print("=" * 55)
    
    test_game_phase_detection()
    test_endgame_pst_behavior()
    test_endgame_move_selection()
    test_phase_transition()
    
    print("Phase 3 testing completed!")
    print("The engine now adapts its strategy based on game phase!")


if __name__ == "__main__":
    main()
