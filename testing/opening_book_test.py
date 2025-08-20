"""
Test suite for the enhanced opening book feature in SlowMate Chess Engine.
"""
import unittest
import chess
from slowmate.core.opening_book import OpeningBook

class TestOpeningBook(unittest.TestCase):
    def setUp(self):
        self.book = OpeningBook()

    def test_initial_position_white(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        moves = self.book.get_book_moves(fen)
        self.assertIn("e2e4", moves)
        self.assertIn("d2d4", moves)
        move = self.book.select_book_move(fen)
        self.assertIn(move, moves)

    def test_initial_position_black(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        moves = self.book.get_book_moves(fen)
        self.assertIn("c7c5", moves)
        move = self.book.select_book_move(fen)
        self.assertIn(move, moves)

    def test_out_of_book(self):
        fen = chess.Board().fen()
        # Make a non-book move
        board = chess.Board()
        board.push_uci("e2e4")
        board.push_uci("c7c6")
        out_fen = board.fen()
        self.assertFalse(self.book.in_book(out_fen))
        self.assertIsNone(self.book.select_book_move(out_fen))

if __name__ == "__main__":
    unittest.main()
