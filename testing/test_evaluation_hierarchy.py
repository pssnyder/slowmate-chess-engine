"""
Test suite for SlowMate's evaluation hierarchy and UCI output.
Tests material evaluation, checkmate detection, and position evaluation.
"""

import chess
import unittest
from slowmate.core.evaluate import Evaluator
from slowmate.uci_enhanced import EnhancedUCIInterface
import io
import sys
from contextlib import contextmanager
from typing import List

@contextmanager
def capture_output():
    """Capture stdout for testing UCI output."""
    new_out = io.StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield new_out
    finally:
        sys.stdout = old_out

class MockEngine:
    """Mock engine class for testing UCI interface."""
    def __init__(self):
        from slowmate.core.board import Board
        self.board = Board()
        self.evaluator = Evaluator()
        self.search_engine = self  # For UCI compatibility
        
    def evaluate_position(self, board):
        """Evaluate current position."""
        return self.evaluator.evaluate(board)

class TestEvaluationHierarchy(unittest.TestCase):
    def setUp(self):
        self.evaluator = Evaluator()
        self.mock_engine = MockEngine()
        self.uci = EnhancedUCIInterface(self.mock_engine)
        
    def test_material_values(self):
        """Test basic material evaluation."""
        board = chess.Board()
        
        # Clear the board
        board.clear()
        
        # Test each piece value
        pieces = [
            (chess.PAWN, 100),
            (chess.KNIGHT, 325),
            (chess.BISHOP, 325),
            (chess.ROOK, 500),
            (chess.QUEEN, 975),
        ]
        
        for piece, expected_value in pieces:
            board.clear()
            # Add one white piece
            board.set_piece_at(chess.E4, chess.Piece(piece, chess.WHITE))
            white_score = self.evaluator.evaluate(board, material_only=True)
            self.assertAlmostEqual(white_score, expected_value, delta=1,
                                 msg=f"White {chess.piece_name(piece)} value incorrect")
            
            # Test black piece (material_only mode always gives White's perspective)
            board.clear()
            board.set_piece_at(chess.E4, chess.Piece(piece, chess.BLACK))
            material_score = self.evaluator.evaluate(board, material_only=True)      
            self.assertAlmostEqual(material_score, -expected_value, delta=1,
                                 msg=f"Black {chess.piece_name(piece)} material value incorrect (should be negative because it's always from White's perspective)")
                                 
    def test_checkmate_detection(self):
        """Test checkmate evaluation and UCI output."""
        # Fool's mate position
        board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        score = self.evaluator.evaluate(board)

        # Verify checkmate score is correctly scaled by ply count
        # Add 1 to match evaluator's ply count adjustment
        expected_mate_score = -(self.evaluator.CHECKMATE_SCORE - (len(board.move_stack) + 1))
        self.assertEqual(score, expected_mate_score)
        
        # Test UCI output format
        with capture_output() as output:
            self.uci.send_search_info(depth=1, score=int(score), pv=[])
            uci_output = output.getvalue().strip()
            self.assertIn("score mate -1", uci_output)
            
    def test_evaluation_hierarchy(self):
        """Test that evaluation priorities are correctly ordered."""
        board = chess.Board()
        
        # Material should outweigh position
        # Black has extra pawn but worse position
        fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2"
        board.set_fen(fen)
        score = self.evaluator.evaluate(board)
        self.assertLess(score, 0, "Material advantage should outweigh positional disadvantage")
        
        # King safety should be important
        # White has material but exposed king
        fen = "rnbqk1nr/pppp1ppp/8/4p3/4P1b1/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
        board.set_fen(fen)
        score = self.evaluator.evaluate(board)
        self.assertLess(abs(score), 300, "King safety should reduce positional advantage")
        
    def test_uci_output_format(self):
        """Test UCI info output formatting."""
        test_positions = [
            # Regular position
            (100, "score cp 100"),
            # Mate in 3
            (29700, "score mate 1"),
            # Mate in -2
            (-29800, "score mate -1"),
            # Deep position evaluation
            (450, "score cp 450")
        ]
        
        for score, expected in test_positions:
            with capture_output() as output:
                self.uci.send_search_info(
                    depth=1,
                    score=score,
                    pv=[],
                    nodes=1000,
                    time_ms=100
                )
                uci_output = output.getvalue().strip()
                self.assertIn(expected, uci_output)
                self.assertIn("depth 1", uci_output)
                self.assertIn("nodes 1000", uci_output)

if __name__ == '__main__':
    unittest.main()
