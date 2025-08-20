"""
A/B Blunder Test: Compare SlowMate_v1.0 blunder positions to SlowMate_v1.5 recommendations.
"""
import chess
import unittest
from slowmate.engine import SlowMateEngine

class TestBlunderPrevention(unittest.TestCase):
    def setUp(self):
        self.engine = SlowMateEngine()

    def test_blunder_position_1(self):
        # After 6...Qxb2, White to move
        fen = "rnbqkbnr/pppp1ppp/4p3/8/8/5N2/BBPPPPPP/RN1QK2R w KQkq - 0 7"
        self.engine.board.board.set_fen(fen)
        best_move = self.engine.search(time_limit_ms=2000)
        print(f"Blunder Test 1: FEN={fen}")
        print(f"SlowMate_v1.5 best move: {best_move.uci() if best_move else None}")
        # The blunder move in v1.0 was f4, leading to Qxa1
        self.assertNotEqual(best_move.uci(), "f2f4", "Engine should avoid blunder f4 in this position.")

    def test_blunder_position_2(self):
        # After 7...Qxa1, White to move
        fen = "rnbqkbnr/pppp1ppp/4p3/8/8/5N2/BBPPPPPP/RN1QK2R w KQkq - 0 8"
        self.engine.board.board.set_fen(fen)
        best_move = self.engine.search(time_limit_ms=2000)
        print(f"Blunder Test 2: FEN={fen}")
        print(f"SlowMate_v1.5 best move: {best_move.uci() if best_move else None}")
        # The blunder move in v1.0 was c4, leading to Qxa2
        self.assertNotEqual(best_move.uci(), "c2c4", "Engine should avoid blunder c4 in this position.")

if __name__ == "__main__":
    unittest.main()
