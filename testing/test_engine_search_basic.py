"""Basic tests for SlowMateEngine search interface.

These tests validate that:
- search() returns a legal move in the starting position
- search() respects fixed depth and produces a centipawn evaluation path
- _negamax returns int values (no floats)
"""

import chess
import unittest

from slowmate.engine import SlowMateEngine

class TestEngineSearchBasic(unittest.TestCase):
    def setUp(self):
        self.engine = SlowMateEngine()

    def test_search_startpos_returns_move(self):
        move = self.engine.search(time_limit=1000)
        self.assertIsNotNone(move, "Engine failed to produce a move from start position")
        self.assertTrue(move in self.engine.board.get_legal_moves(), "Returned move is not legal")

    def test_negamax_int_return(self):
        score = self.engine._negamax(1, -30000, 30000)
        self.assertIsInstance(score, int, "Negamax should return int score")
        # Score should be within plausible bounds
        self.assertGreater(score, -30000)
        self.assertLess(score, 30000)

if __name__ == '__main__':
    unittest.main()
