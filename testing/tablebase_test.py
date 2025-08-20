"""
Test suite for the endgame tablebase feature in SlowMate Chess Engine.
"""
import unittest
import chess
from slowmate.core.tablebase import Tablebase

class TestTablebase(unittest.TestCase):
    def setUp(self):
        self.tb = Tablebase()

    def test_basic_kk_white(self):
        fen = "8/8/8/8/8/8/5K2/6k1 w - - 0 1"
        moves = self.tb.get_tablebase_moves(fen)
        self.assertIn("f2f3", moves)
        move = self.tb.select_tablebase_move(fen)
        self.assertEqual(move, "f2f3")

    def test_basic_kk_black(self):
        fen = "8/8/8/8/8/8/5K2/6k1 b - - 0 1"
        moves = self.tb.get_tablebase_moves(fen)
        self.assertIn("g1h1", moves)
        move = self.tb.select_tablebase_move(fen)
        self.assertEqual(move, "g1h1")

    def test_out_of_tablebase(self):
        board = chess.Board()
        board.push_uci("e2e4")
        out_fen = board.fen()
        self.assertFalse(self.tb.in_tablebase(out_fen))
        self.assertIsNone(self.tb.select_tablebase_move(out_fen))

if __name__ == "__main__":
    unittest.main()
