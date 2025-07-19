#!/usr/bin/env python3
"""
Test Phase 1: Base Piece-Square Table Implementation

This script tests the basic PST functionality with the universal base table.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def print_pst_visualization():
    """Print the BASE_PST for visual verification."""
    engine = IntelligentSlowMateEngine()
    pst = engine.intelligence.BASE_PST
    
    print("Base PST Visualization (White's perspective):")
    print("Values: -1=avoid, 0=neutral, +1=good, +2=excellent")
    print()
    
    # Print rank by rank (8 to 1)
    for rank in range(7, -1, -1):  # 7 down to 0
        rank_str = f"Rank {rank + 1}: "
        for file in range(8):  # 0 to 7 (a to h)
            square_index = rank * 8 + file
            value = pst[square_index]
            rank_str += f"{value:+2d} "
        print(rank_str)
    
    print("\nFiles:    a  b  c  d  e  f  g  h")
    print()


def test_starting_position():
    """Test PST evaluation of starting position."""
    print("=== Testing Starting Position PST ===")
    
    engine = IntelligentSlowMateEngine()
    details = engine.get_evaluation_details()
    
    print(f"White PST score: {details['white_pst']}")
    print(f"Black PST score: {details['black_pst']}")
    print(f"PST difference: {details['pst_difference']}")
    print(f"Total evaluation: {details['total_evaluation']}")
    
    # Expected: Should be equal since position is symmetrical
    expected_symmetry = details['white_pst'] == details['black_pst']
    print(f"Symmetry check: {'✅' if expected_symmetry else '❌'} (White PST should equal Black PST)")
    print()


def test_piece_development():
    """Test that developing pieces to center improves evaluation."""
    print("=== Testing Piece Development Preferences ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Knight development
    print("1. Knight Development Test:")
    
    # Starting position evaluation
    start_eval = engine.get_current_evaluation()
    print(f"   Starting evaluation: {start_eval}")
    
    # Develop knight to f3 (should be positive PST contribution)
    engine.make_move(chess.Move.from_uci("g1f3"))
    after_nf3 = engine.get_current_evaluation()
    details = engine.get_evaluation_details()
    
    print(f"   After Nf3: {after_nf3}")
    print(f"   PST improvement: {after_nf3 - start_eval}")
    print(f"   White PST: {details['white_pst']}, Black PST: {details['black_pst']}")
    
    # Test 2: Knight to edge vs center
    engine.reset_game()
    
    print("\n2. Edge vs Center Preference:")
    
    # Test knight on edge (Nh3) vs center development
    edge_moves = ["g1h3"]  # Knight to edge
    center_moves = ["g1f3", "b1c3"]  # Knight to better squares
    
    for desc, moves in [("Edge (Nh3)", edge_moves), ("Center (Nf3)", center_moves)]:
        engine.reset_game()
        total_eval = engine.get_current_evaluation()
        
        for move_uci in moves:
            if move_uci in [m.uci() for m in engine.board.legal_moves]:
                engine.make_move(chess.Move.from_uci(move_uci))
                total_eval = engine.get_current_evaluation()
        
        details = engine.get_evaluation_details()
        print(f"   {desc}: Total={total_eval}, PST={details['pst_difference']}")
    
    print()


def test_center_control():
    """Test that center squares are preferred."""
    print("=== Testing Center Control Preferences ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test different pawn moves
    moves_to_test = [
        ("e2e4", "Center pawn to e4"),
        ("d2d4", "Center pawn to d4"), 
        ("a2a4", "Edge pawn to a4"),
        ("h2h4", "Edge pawn to h4")
    ]
    
    evaluations = []
    
    for move_uci, description in moves_to_test:
        engine.reset_game()
        start_eval = engine.get_current_evaluation()
        
        engine.make_move(chess.Move.from_uci(move_uci))
        after_eval = engine.get_current_evaluation()
        improvement = after_eval - start_eval
        
        details = engine.get_evaluation_details()
        evaluations.append((description, improvement, details['pst_difference']))
        
        print(f"{description}: Improvement={improvement:+d}, PST diff={details['pst_difference']:+d}")
    
    # Center moves should generally be better than edge moves
    center_avg = (evaluations[0][1] + evaluations[1][1]) / 2
    edge_avg = (evaluations[2][1] + evaluations[3][1]) / 2
    
    print(f"\nCenter moves average improvement: {center_avg:+.1f}")
    print(f"Edge moves average improvement: {edge_avg:+.1f}")
    print(f"Center preference: {'✅' if center_avg > edge_avg else '❌'}")
    print()


def test_move_selection_with_pst():
    """Test that PST influences move selection."""
    print("=== Testing PST-Influenced Move Selection ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test in a position where material is equal but positional factors matter
    print("Position: Starting position, testing first move selection")
    
    # Get all legal moves and their evaluations
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    for move in legal_moves[:10]:  # Test first 10 moves to avoid too much output
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score))
    
    # Sort by evaluation score
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("Top evaluated moves (material + PST):")
    for i, (move_san, score) in enumerate(move_evaluations[:5]):
        print(f"  {i+1}. {move_san}: {score:+d}")
    
    # Make the engine's choice
    selected_move = engine.play_intelligent_move()
    if selected_move and engine.evaluation_history:
        last_eval = engine.evaluation_history[-1]
        print(f"\nEngine selected: {selected_move}")
        print(f"Reasoning: {last_eval['reasoning']}")
        print(f"Score breakdown: {last_eval['score']:+d}")
    
    print()


def test_pst_accuracy():
    """Verify PST values match specifications."""
    print("=== Testing PST Accuracy Against Specifications ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test specific squares according to specifications
    test_cases = [
        # Opponent starting squares (rank 8) = 0
        (chess.A8, "a8 (black rook start)", 0),
        (chess.E8, "e8 (black king start)", 0),
        (chess.H7, "h7 (black pawn start)", 0),
        
        # Own pawn starting squares (rank 2) = 0
        (chess.A2, "a2 (white pawn start)", 0),
        (chess.E2, "e2 (white pawn start)", 0),
        
        # Minor piece starting squares = -1
        (chess.B1, "b1 (knight start)", -1),
        (chess.G1, "g1 (knight start)", -1),
        (chess.C1, "c1 (bishop start)", 0),  # Actually should be 0 based on spec
        
        # Rook and queen starting squares = 0
        (chess.A1, "a1 (rook start)", -1),  # Wait, spec says -1 for A/H files
        (chess.D1, "d1 (queen start)", 0),
        
        # King starting square = +1
        (chess.E1, "e1 (king start)", 1),
        
        # Center squares = +2
        (chess.D4, "d4 (center)", 2),
        (chess.E4, "e4 (center)", 2),
        (chess.D5, "d5 (center)", 2),
        (chess.E5, "e5 (center)", 2),
        
        # A/H files (non-starting) = -1
        (chess.A4, "a4 (A file)", -1),
        (chess.H5, "h5 (H file)", -1),
        
        # Other internal squares = +1
        (chess.C3, "c3 (internal)", 1),
        (chess.F6, "f6 (internal)", 1),
    ]
    
    errors = 0
    for square, description, expected in test_cases:
        # Test for white perspective
        actual = intelligence._get_pst_value(square, chess.PAWN, chess.WHITE)
        status = "✅" if actual == expected else "❌"
        if actual != expected:
            errors += 1
        print(f"{status} {description}: expected {expected:+d}, got {actual:+d}")
    
    print(f"\nPST Accuracy: {len(test_cases) - errors}/{len(test_cases)} correct")
    if errors > 0:
        print("❌ Some PST values don't match specifications - please review")
    else:
        print("✅ All PST values match specifications")
    
    print()


def main():
    """Run all Phase 1 PST tests."""
    print("SlowMate Chess Engine - Phase 1 PST Tests")
    print("=" * 50)
    
    print_pst_visualization()
    test_pst_accuracy()
    test_starting_position()
    test_piece_development()
    test_center_control()
    test_move_selection_with_pst()
    
    print("Phase 1 PST testing completed!")
    print("Ready for review and Phase 2 implementation.")


if __name__ == "__main__":
    main()
