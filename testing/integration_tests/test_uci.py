"""
SlowMate Chess Engine - UCI Protocol Tests
Version: 1.0.0-BETA
"""

import unittest
import chess
import io
import sys
from contextlib import contextmanager
from slowmate.engine import SlowMateEngine
from slowmate.uci.protocol import UCIProtocol

class TestUCIProtocol(unittest.TestCase):
    def setUp(self):
        self.engine = SlowMateEngine()
        self.uci = UCIProtocol(self.engine)
        
    @contextmanager
    def capture_output(self):
        """Capture stdout for testing."""
        new_out = io.StringIO()
        old_out = sys.stdout
        try:
            sys.stdout = new_out
            yield new_out
        finally:
            sys.stdout = old_out
            
    def test_uci_command(self):
        """Test UCI identification command."""
        with self.capture_output() as output:
            self.uci.process_command("uci")
            
        output_text = output.getvalue()
        self.assertIn("id name SlowMate", output_text)
        self.assertIn("id author Github Copilot", output_text)
        self.assertIn("uciok", output_text)
        
    def test_isready_command(self):
        """Test isready command."""
        with self.capture_output() as output:
            self.uci.process_command("isready")
            
        self.assertIn("readyok", output.getvalue())
        
    def test_position_command(self):
        """Test position command handling."""
        # Test starting position
        self.uci.process_command("position startpos")
        self.assertEqual(self.engine.board.get_fen().split()[0], 
                        chess.STARTING_FEN.split()[0])
        
        # Test position with moves
        self.uci.process_command("position startpos moves e2e4 e7e5")
        board = chess.Board()
        board.push_uci("e2e4")
        board.push_uci("e7e5")
        self.assertEqual(self.engine.board.get_fen().split()[0], 
                        board.fen().split()[0])
        
    def test_go_command(self):
        """Test go command produces a move."""
        import time
        with self.capture_output() as output:
            self.uci.process_command("go movetime 100")
            # Wait for up to 1 second for output
            start_time = time.time()
            while time.time() - start_time < 1:
                output_text = output.getvalue()
                if "bestmove" in output_text:
                    break
                time.sleep(0.1)
                
        output_text = output.getvalue()
        self.assertIn("bestmove", output_text)
        # Verify move format (e.g., "e2e4")
        move_str = output_text.split()[-1]
        self.assertTrue(len(move_str) == 4 or len(move_str) == 5)
        
    def test_debug_command(self):
        """Test debug command."""
        self.uci.process_command("debug on")
        self.assertTrue(self.uci.debug)
        
        self.uci.process_command("debug off")
        self.assertFalse(self.uci.debug)
        
    def test_stop_command(self):
        """Test stop command during search."""
        self.uci.searching = True
        self.uci.process_command("stop")
        self.assertTrue(self.uci.stop_requested)
        
if __name__ == '__main__':
    unittest.main()
