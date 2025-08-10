"""
SlowMate Chess Engine - Evaluation Tests
Version: 1.0.0-BETA
"""

import unittest
import chess
from slowmate.core.board import Board
from slowmate.core.evaluate import Evaluator

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.evaluator = Evaluator()
        
    def test_material_balance(self):
        """Test basic material evaluation."""
        # Equal position
        score = self.evaluator.evaluate(self.board)
        self.assertEqual(score, 0)  # Starting position is equal
        
        # Position with material advantage
        self.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertTrue(score < -450)  # Black is up a rook
        
    def test_piece_square_tables(self):
        """Test piece-square table evaluation."""
        # Test central pawn advantage
        self.board.set_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertTrue(score > 1000)  # Central pawn should be worth more (centipawn scale)
        
        # Test knight on the rim
        self.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNH w KQkq - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertTrue(score < -100)  # Knight on rim is worse (centipawn scale)
        
    def test_checkmate_evaluation(self):
        """Test checkmate position evaluation."""
        # Black is checkmated
        self.board.set_fen("k7/8/8/8/8/5Q2/8/7K b - - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertEqual(score, -20000)  # Black to move and is checkmated
        
        # White is checkmated
        self.board.set_fen("7k/8/8/8/8/5q2/8/K7 w - - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertEqual(score, -20000)  # White to move and is checkmated
        
    def test_stalemate_evaluation(self):
        """Test stalemate position evaluation."""
        # Stalemate position
        self.board.set_fen("k7/8/1Q6/8/8/8/8/K7 b - - 0 1")
        score = self.evaluator.evaluate(self.board)
        self.assertEqual(score, 0)  # Stalemate should evaluate to 0
        
    def test_mobility_evaluation(self):
        """Test mobility evaluation component."""
        # Position where white has clear mobility advantage
        self.board.set_fen("rnbqkb1r/pppppppp/5n2/8/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1")
        score = self.evaluator.evaluate(self.board)
        
        # White should have more mobility due to developed pieces and center control
        self.assertTrue(score > 1000)  # At least +1 pawn worth of advantage
        
if __name__ == '__main__':
    unittest.main()
