"""
SlowMate Chess Engine - Board Tests
Version: 1.0.0-BETA
"""

import unittest
import chess
from slowmate.core.board import Board

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        
    def test_initial_position(self):
        """Test initial board position."""
        self.assertEqual(self.board.get_fen().split()[0], 
                        chess.STARTING_FEN.split()[0])
        
    def test_legal_moves(self):
        """Test legal moves generation in starting position."""
        moves = self.board.get_legal_moves()
        self.assertEqual(len(moves), 20)  # Standard number of initial moves
        
    def test_make_unmake_move(self):
        """Test making and unmaking moves."""
        initial_fen = self.board.get_fen()
        
        # Make a move
        e4 = chess.Move.from_uci("e2e4")
        self.board.make_move(e4)
        
        # Verify position changed
        self.assertNotEqual(self.board.get_fen(), initial_fen)
        
        # Unmake move
        self.board.unmake_move()
        
        # Verify position restored
        self.assertEqual(self.board.get_fen(), initial_fen)
        
    def test_game_phase_detection(self):
        """Test game phase detection."""
        # Initial position should be opening
        self.assertEqual(self.board.get_phase(), 'opening')
        
        # Set up an endgame position
        self.board.set_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        self.assertEqual(self.board.get_phase(), 'endgame')
        
    def test_material_count(self):
        """Test material counting."""
        # Initial position
        white_material, black_material = self.board.get_material_count()
        self.assertEqual(white_material, black_material)  # Equal material
        
        # Position with material advantage
        self.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1")
        white_material, black_material = self.board.get_material_count()
        self.assertTrue(black_material > white_material)  # Black has extra rook
        
    def test_game_status(self):
        """Test game status detection."""
        # Regular position
        self.assertFalse(self.board.is_game_over())
        
        # Checkmate position
        self.board.set_fen("rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 0 1")
        self.assertTrue(self.board.is_game_over())
        self.assertTrue(self.board.is_checkmate())
        
        # Stalemate position
        self.board.set_fen("k7/8/1Q6/8/8/8/8/K7 b - - 0 1")
        self.assertTrue(self.board.is_game_over())
        self.assertTrue(self.board.is_stalemate())
        
        # Insufficient material
        self.board.set_fen("k7/8/8/8/8/8/8/K7 w - - 0 1")
        self.assertTrue(self.board.is_insufficient_material())
        
if __name__ == '__main__':
    unittest.main()
