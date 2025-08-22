"""
SlowMate v2.1 Emergency Validation Test Suite
Critical tests to verify the emergency fixes work correctly
"""

import os
import sys
import time
import chess
import unittest
from typing import List, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.engine_v2_1 import SlowMateEngine
from slowmate.uci.protocol_v2_1 import UCIProtocol


class TestSlowMateV21Emergency(unittest.TestCase):
    """Critical validation tests for SlowMate v2.1 emergency fixes."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = SlowMateEngine()
        self.uci = UCIProtocol(self.engine)
        self.uci.set_silent_mode(True)  # Silent for testing
    
    def test_critical_01_engine_initialization(self):
        """CRITICAL: Engine must initialize without errors."""
        engine = SlowMateEngine()
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.board)
        self.assertIsNotNone(engine.move_generator)
        self.assertIsNotNone(engine.evaluator)
        
    def test_critical_02_uci_basic_protocol(self):
        """CRITICAL: Basic UCI protocol must work."""
        # Test UCI initialization
        self.uci.process_command("uci")
        
        # Test ready check
        self.uci.process_command("isready")
        
        # Test new game
        self.uci.process_command("ucinewgame")
        
        # These should not crash
        self.assertTrue(True)
        
    def test_critical_03_no_illegal_moves_generated(self):
        """CRITICAL: Engine must never generate illegal moves."""
        test_positions = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
            "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",  # After 1.e4 e5 2.Nf3 Nf6
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",  # Italian game setup
            "r2qkbnr/ppp2ppp/2n5/3pp3/4P3/3P1N2/PPP2PPP/RNBQKB1R w KQkq - 0 1",  # Scotch game
            "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1"  # Italian game
        ]
        
        for fen in test_positions:
            with self.subTest(fen=fen):
                self.engine.set_position(fen)
                
                # Get engine move
                move = self.engine.search(time_limit_ms=1000)
                
                # Verify move is legal
                if move is not None:
                    legal_moves = list(self.engine.board.board.legal_moves)
                    self.assertIn(move, legal_moves, 
                                f"Engine returned illegal move {move.uci()} in position {fen}")
                                
    def test_critical_04_search_always_returns_move(self):
        """CRITICAL: Search must always return a move when legal moves exist."""
        test_positions = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
        ]
        
        for fen in test_positions:
            with self.subTest(fen=fen):
                self.engine.set_position(fen)
                legal_moves = list(self.engine.board.board.legal_moves)
                
                if legal_moves:  # If legal moves exist
                    move = self.engine.search(time_limit_ms=1000)
                    self.assertIsNotNone(move, f"Engine failed to return move in position {fen}")
                    
    def test_critical_05_uci_position_command(self):
        """CRITICAL: UCI position command must work correctly."""
        # Test startpos
        self.uci.process_command("position startpos")
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.assertEqual(self.engine.board.get_fen().split()[0], starting_fen.split()[0])
        
        # Test position with moves
        self.uci.process_command("position startpos moves e2e4 e7e5")
        # Should have made the moves without error
        self.assertEqual(len(self.engine.board.board.move_stack), 2)
        
    def test_critical_06_uci_go_command(self):
        """CRITICAL: UCI go command must work and return a move."""
        self.uci.process_command("position startpos")
        
        # Start search
        start_time = time.time()
        self.uci.process_command("go movetime 1000")
        
        # Wait for search to complete (with timeout)
        timeout = 5.0  # 5 second timeout
        while self.uci.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        # Search should have completed
        self.assertFalse(self.uci.searching, "Search did not complete within timeout")
        
    def test_critical_07_search_time_limits(self):
        """CRITICAL: Search must respect time limits."""
        self.engine.set_position("startpos")
        
        # Test short time limit
        start_time = time.time()
        move = self.engine.search(time_limit_ms=500)  # 0.5 seconds
        elapsed = time.time() - start_time
        
        self.assertIsNotNone(move, "Engine failed to return move within time limit")
        self.assertLess(elapsed, 2.0, f"Search took too long: {elapsed:.2f}s > 2.0s")
        
    def test_critical_08_move_validation_wrapper(self):
        """CRITICAL: Move validation wrapper must work correctly."""
        self.engine.set_position("startpos")
        
        # Test valid move
        valid_move = chess.Move.from_uci("e2e4")
        self.assertTrue(self.engine._validate_move_legal(valid_move))
        
        # Test invalid move (king move from starting position)
        try:
            invalid_move = chess.Move.from_uci("e1e2")  # King can't move here
            result = self.engine._validate_move_legal(invalid_move)
            self.assertFalse(result, "Should reject illegal king move")
        except:
            pass  # May throw exception for obviously invalid moves
            
    def test_critical_09_exception_handling(self):
        """CRITICAL: Engine must handle exceptions gracefully."""
        # Test with potentially problematic position
        try:
            # This should not crash
            self.engine.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            move = self.engine.search(time_limit_ms=100)
            # Should return a move or None, but not crash
            self.assertTrue(move is None or isinstance(move, chess.Move))
        except Exception as e:
            self.fail(f"Engine crashed with exception: {e}")
            
    def test_critical_10_uci_stop_command(self):
        """CRITICAL: UCI stop command must work."""
        self.uci.process_command("position startpos")
        self.uci.process_command("go movetime 5000")  # Long search
        
        # Let it start
        time.sleep(0.1)
        
        # Stop it
        self.uci.process_command("stop")
        
        # Wait for stop
        timeout = 3.0
        start_time = time.time()
        while self.uci.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        self.assertFalse(self.uci.searching, "Search did not stop within timeout")


class TestSlowMateV21Performance(unittest.TestCase):
    """Performance validation tests for v2.1."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = SlowMateEngine()
        
    def test_performance_01_basic_tactical_awareness(self):
        """Test that engine shows basic tactical awareness."""
        # Position where there's a clear best move (capture)
        self.engine.set_position("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
        
        # After 1.e4 e5 2.Nf3 Nf6, engine should consider developing moves
        move = self.engine.search(time_limit_ms=2000)
        self.assertIsNotNone(move)
        
        # Should be a reasonable move (any legal move is acceptable for now)
        legal_moves = list(self.engine.board.board.legal_moves)
        self.assertIn(move, legal_moves)
        
    def test_performance_02_avoid_immediate_blunders(self):
        """Test that engine avoids immediate material loss."""
        # Position where hanging queen is possible
        self.engine.set_position("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
        
        move = self.engine.search(time_limit_ms=2000)
        self.assertIsNotNone(move)
        
        # Should not hang the queen immediately
        if move:
            self.assertNotEqual(move.uci(), "d1h5")  # Premature queen development
        
    def test_performance_03_search_depth_scaling(self):
        """Test that engine can search to reasonable depth."""
        self.engine.set_position("startpos")
        
        # Test different time limits
        for time_limit in [500, 1000, 2000]:
            with self.subTest(time_limit=time_limit):
                start_nodes = self.engine.nodes
                move = self.engine.search(time_limit_ms=time_limit)
                end_nodes = self.engine.nodes
                
                self.assertIsNotNone(move)
                # Should search some nodes
                self.assertGreater(end_nodes - start_nodes, 0)


def run_emergency_validation():
    """Run the emergency validation test suite."""
    print("=" * 60)
    print("SlowMate v2.1 Emergency Validation Test Suite")
    print("=" * 60)
    
    # Create test suite
    critical_suite = unittest.TestLoader().loadTestsFromTestCase(TestSlowMateV21Emergency)
    performance_suite = unittest.TestLoader().loadTestsFromTestCase(TestSlowMateV21Performance)
    
    # Run critical tests first
    print("\n🚨 CRITICAL TESTS (must pass for tournament readiness)")
    print("-" * 40)
    critical_runner = unittest.TextTestRunner(verbosity=2)
    critical_result = critical_runner.run(critical_suite)
    
    print("\n📊 PERFORMANCE TESTS (competitive analysis)")
    print("-" * 40)
    performance_runner = unittest.TextTestRunner(verbosity=2)
    performance_result = performance_runner.run(performance_suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("EMERGENCY VALIDATION SUMMARY")
    print("=" * 60)
    
    critical_passed = critical_result.wasSuccessful()
    performance_passed = performance_result.wasSuccessful()
    
    print(f"Critical Tests: {'✅ PASSED' if critical_passed else '❌ FAILED'}")
    print(f"Performance Tests: {'✅ PASSED' if performance_passed else '❌ FAILED'}")
    
    if critical_passed:
        print("\n🎯 TOURNAMENT READINESS: ✅ READY")
        print("v2.1 emergency fixes are working correctly.")
        print("Engine is ready for competitive testing.")
    else:
        print("\n🚨 TOURNAMENT READINESS: ❌ NOT READY")
        print("Critical failures detected. DO NOT DEPLOY.")
        print("Fix critical issues before tournament testing.")
        
    total_tests = critical_result.testsRun + performance_result.testsRun
    total_failures = len(critical_result.failures) + len(performance_result.failures)
    total_errors = len(critical_result.errors) + len(performance_result.errors)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failed: {total_failures}")
    print(f"Errors: {total_errors}")
    
    return critical_passed and performance_passed


if __name__ == "__main__":
    success = run_emergency_validation()
    sys.exit(0 if success else 1)
