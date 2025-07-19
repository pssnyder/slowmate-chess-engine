#!/usr/bin/env python3
"""
Test Phase 2: Piece-Specific Piece-Square Tables

This script tests the individual PST tables for each piece type.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def print_piece_pst_visualization(piece_type):
    """Print a specific piece's PST for visual verification."""
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Get the PST table for this piece
    pst_map = {
        chess.PAWN: intelligence.PAWN_PST,
        chess.KNIGHT: intelligence.KNIGHT_PST,
        chess.BISHOP: intelligence.BISHOP_PST,
        chess.ROOK: intelligence.ROOK_PST,
        chess.QUEEN: intelligence.QUEEN_PST,
        chess.KING: intelligence.KING_PST
    }
    
    piece_name = chess.piece_name(piece_type).capitalize()
    pst = pst_map[piece_type]
    
    print(f"{piece_name} PST Visualization (White's perspective):")
    print()
    
    # Print rank by rank (8 to 1)
    for rank in range(7, -1, -1):  # 7 down to 0
        rank_str = f"Rank {rank + 1}: "
        for file in range(8):  # 0 to 7 (a to h)
            square_index = rank * 8 + file
            value = pst[square_index]
            rank_str += f"{value:+3d} "
        print(rank_str)
    
    print("Files:     a   b   c   d   e   f   g   h")
    print()


def test_piece_specific_preferences():
    """Test that each piece type has appropriate positional preferences."""
    print("=== Testing Piece-Specific Positional Preferences ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test key squares for each piece type
    test_cases = [
        # Pawns - should prefer advancement and center
        ("Pawn on e2 (start)", chess.E2, chess.PAWN, "neutral starting position"),
        ("Pawn on e4 (center)", chess.E4, chess.PAWN, "should be positive for center control"),
        ("Pawn on e7 (near promotion)", chess.E7, chess.PAWN, "should be very positive near promotion"),
        
        # Knights - should prefer center, avoid edges
        ("Knight on a1 (corner)", chess.A1, chess.KNIGHT, "should be very negative"),
        ("Knight on e4 (center)", chess.E4, chess.KNIGHT, "should be positive"),
        ("Knight on f3 (developed)", chess.F3, chess.KNIGHT, "should be positive"),
        
        # Bishops - should prefer long diagonals
        ("Bishop on c1 (start)", chess.C1, chess.BISHOP, "should be negative (undeveloped)"),
        ("Bishop on e4 (center)", chess.E4, chess.BISHOP, "should be positive"),
        ("Bishop on a1 (corner)", chess.A1, chess.BISHOP, "should be negative (corner)"),
        
        # Rooks - should prefer open files and 7th rank
        ("Rook on a1 (start)", chess.A1, chess.ROOK, "starting position neutral"),
        ("Rook on e7 (7th rank)", chess.E7, chess.ROOK, "should be positive on 7th rank"),
        ("Rook on e4 (center)", chess.E4, chess.ROOK, "center should be neutral/negative"),
        
        # Queen - flexible, slight center preference
        ("Queen on d1 (start)", chess.D1, chess.QUEEN, "starting position should be negative"),
        ("Queen on d4 (center)", chess.D4, chess.QUEEN, "center should be positive"),
        ("Queen on a1 (corner)", chess.A1, chess.QUEEN, "corner should be negative"),
        
        # King - should prefer safety (back rank in middlegame)
        ("King on e1 (start)", chess.E1, chess.KING, "back rank should be positive"),
        ("King on e4 (center)", chess.E4, chess.KING, "center should be very negative (unsafe)"),
        ("King on g1 (castled)", chess.G1, chess.KING, "castled position should be positive")
    ]
    
    for description, square, piece_type, expectation in test_cases:
        pst_value = intelligence._get_pst_value(square, piece_type, chess.WHITE)
        print(f"{description}: {pst_value:+3d} - {expectation}")
    
    print()


def test_development_incentives():
    """Test that PST encourages proper piece development."""
    print("=== Testing Development Incentives ===")
    
    engine = IntelligentSlowMateEngine()
    
    development_tests = [
        # Knight development
        ("Knight Nf3 development", ["g1f3"], "Should improve PST score"),
        ("Knight Nc3 development", ["b1c3"], "Should improve PST score"),
        ("Bad knight Nh3", ["g1h3"], "Should worsen PST score"),
        
        # Bishop development
        ("Bishop Be2 development", ["f1e2"], "Should improve PST score"),
        ("Bishop Bc4 development", ["f1c4"], "Should improve PST score"),
        
        # Pawn advancement
        ("Center pawn e4", ["e2e4"], "Should improve PST score"),
        ("Center pawn d4", ["d2d4"], "Should improve PST score"),
    ]
    
    for description, moves, expectation in development_tests:
        engine.reset_game()
        start_eval = engine.get_evaluation_details()
        start_pst = start_eval['pst_difference']
        
        # Make the moves
        for move_uci in moves:
            if chess.Move.from_uci(move_uci) in engine.board.legal_moves:
                engine.make_move(chess.Move.from_uci(move_uci))
        
        after_eval = engine.get_evaluation_details()
        after_pst = after_eval['pst_difference']
        improvement = after_pst - start_pst
        
        status = "✅" if improvement > 0 else ("⚠️" if improvement == 0 else "❌")
        print(f"{status} {description}: PST change {improvement:+d} - {expectation}")
    
    print()


def test_piece_specific_move_selection():
    """Test that piece-specific PSTs influence move selection."""
    print("=== Testing Piece-Specific Move Selection ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Opening move selection should favor good development
    print("1. Opening Move Selection:")
    
    legal_moves = list(engine.board.legal_moves)
    move_evaluations = []
    
    for move in legal_moves:
        score = engine.intelligence._evaluate_move(move)
        move_san = engine.board.san(move)
        move_evaluations.append((move_san, score))
    
    # Sort by evaluation score
    move_evaluations.sort(key=lambda x: x[1], reverse=True)
    
    print("Top evaluated opening moves (material + piece-specific PST):")
    for i, (move_san, score) in enumerate(move_evaluations[:8]):
        print(f"  {i+1}. {move_san}: {score:+d}")
    
    # Check if good development moves are preferred
    good_moves = ['e4', 'd4', 'Nf3', 'Nc3']
    top_moves = [move for move, _ in move_evaluations[:6]]
    good_in_top = sum(1 for move in good_moves if move in top_moves)
    
    print(f"Good development moves in top 6: {good_in_top}/4")
    print()
    
    # Test 2: Engine selection
    selected_move = engine.play_intelligent_move()
    if selected_move and engine.evaluation_history:
        last_eval = engine.evaluation_history[-1]
        print(f"2. Engine Selected: {selected_move}")
        print(f"   Score: {last_eval['score']:+d}")
        print(f"   Reasoning: {last_eval['reasoning']}")
    
    print()


def test_comparison_with_phase1():
    """Compare Phase 2 behavior with Phase 1 base PST."""
    print("=== Comparing Phase 2 vs Phase 1 PST ===")
    
    engine = IntelligentSlowMateEngine()
    intelligence = engine.intelligence
    
    # Test specific positions to see how different pieces are evaluated
    comparison_tests = [
        # Knight placement comparison
        (chess.E4, chess.KNIGHT, "Knight on e4"),
        (chess.A1, chess.KNIGHT, "Knight on a1"),
        
        # Bishop placement comparison  
        (chess.E4, chess.BISHOP, "Bishop on e4"),
        (chess.C1, chess.BISHOP, "Bishop on c1"),
        
        # Pawn advancement comparison
        (chess.E4, chess.PAWN, "Pawn on e4"),
        (chess.E7, chess.PAWN, "Pawn on e7"),
        
        # King safety comparison
        (chess.E1, chess.KING, "King on e1"),
        (chess.E4, chess.KING, "King on e4")
    ]
    
    print("Position                 | Base PST | Piece PST | Difference")
    print("-" * 60)
    
    for square, piece_type, description in comparison_tests:
        # Phase 1 (base PST) value
        base_value = intelligence.BASE_PST[square]
        
        # Phase 2 (piece-specific PST) value
        piece_value = intelligence._get_pst_value(square, piece_type, chess.WHITE)
        
        difference = piece_value - base_value
        arrow = "→" if difference > 0 else ("=" if difference == 0 else "←")
        
        print(f"{description:24} | {base_value:+8d} | {piece_value:+9d} | {difference:+4d} {arrow}")
    
    print()


def main():
    """Run all Phase 2 PST tests."""
    print("SlowMate Chess Engine - Phase 2 PST Tests")
    print("=" * 50)
    
    # Show individual piece PST tables
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        print_piece_pst_visualization(piece_type)
    
    test_piece_specific_preferences()
    test_development_incentives()
    test_piece_specific_move_selection()
    test_comparison_with_phase1()
    
    print("Phase 2 PST testing completed!")
    print("Ready for Phase 3 (game phase awareness) when you give approval.")


if __name__ == "__main__":
    main()
