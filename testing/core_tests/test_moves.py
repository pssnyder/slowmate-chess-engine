"""
SlowMate Chess Engine - Move Generation Tests
Version: 1.0.0-BETA
"""

import unittest
import chess
from slowmate.core.board import Board
from slowmate.core.moves import MoveGenerator

class TestMoveGenerator(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        
    def test_initial_moves(self):
        """Test move generation in starting position."""
        moves = self.move_generator.get_legal_moves()
        self.assertEqual(len(moves), 20)  # Standard number of initial moves
        
        # Verify presence of common opening moves
        move_ucis = [move.uci() for move in moves]
        self.assertIn("e2e4", move_ucis)  # e4
        self.assertIn("d2d4", move_ucis)  # d4
        self.assertIn("g1f3", move_ucis)  # Nf3
        
    def test_move_ordering(self):
        """Test basic move ordering."""
        # Set up a position with an obvious queen capture by pawn
        pos = "rnbqkbnr/ppp2ppp/8/4p3/4P3/3P4/PPPqPPPP/RNBQKBNR w KQkq - 0 1"
        self.board.set_fen(pos)
        self.move_generator.board.board = chess.Board(pos)
        
        # Get ordered moves
        ordered_moves = self.move_generator.get_ordered_moves()
        
        # Print debug info to help diagnose issues
        if not ordered_moves:
            print("\nNo legal moves found!")
            return
            
        first_move = ordered_moves[0]
        print("\nTesting position:")
        print(self.board.board)
        print("\nLegal moves (in order):")
        for move in ordered_moves[:5]:
            print(f"- {move.uci()}")
            
        self.assertEqual(first_move.uci(), "f2d2", "Pawn should capture queen")
        
    def test_check_ordering(self):
        """Test that check moves are prioritized."""
        # Set up a position with an obvious queen check
        self.board.set_fen("rnbqkb1r/pppp1ppp/5n2/4p3/2B5/4P3/PPPP1PPP/RNBQK1NR w KQkq - 2 3")
        self.move_generator.board.board = chess.Board(self.board.board.fen())
        
        ordered_moves = self.move_generator.get_ordered_moves()
        check_moves = [(move, self.board.board.gives_check(move)) 
                      for move in ordered_moves]
        
        # Should find at least one check
        self.assertTrue(any(is_check for _, is_check in check_moves))
        
        # Queen to h5 (giving check) should be among first few moves
        high_priority_checks = [move.uci() for move in ordered_moves[:5] 
                              if self.board.board.gives_check(move)]
        self.assertTrue(high_priority_checks)  # Should have at least one check in top 5
        
    def test_promotion_ordering(self):
        """Test that promotion moves are prioritized."""
        # Position with possible pawn promotion
        self.board.set_fen("8/4P3/8/8/8/8/8/k6K w - - 0 1")
        
        ordered_moves = self.move_generator.get_ordered_moves()
        first_move = ordered_moves[0]
        
        # Queen promotion should be first
        self.assertEqual(first_move.uci(), "e7e8q")
        
    def is_check_move(self, move):
        """Helper to test if a move gives check."""
        self.board.make_move(move)
        is_check = self.board.is_check()
        self.board.unmake_move()
        return is_check
        
if __name__ == '__main__':
    unittest.main()
