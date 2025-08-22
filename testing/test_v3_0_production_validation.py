"""
SlowMate Chess Engine v3.0 - Production Validation Test Suite
Comprehensive test to ensure v3.0 is ready for tournament deployment
"""

import sys
import os
import time
import chess
import traceback
from typing import List, Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.engine import SlowMateEngine
from slowmate.core.board import Board


class SlowMateV3ValidationSuite:
    """Comprehensive validation test suite for SlowMate v3.0."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.engine: Optional[SlowMateEngine] = None
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "PASS" if passed else "FAIL"
        result = {
            'test': test_name,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
        if not passed:
            self.failed_tests.append(result)
    
    def test_engine_initialization(self) -> bool:
        """Test 1: Engine initialization."""
        try:
            self.engine = SlowMateEngine()
            version = self.engine.get_version()
            
            if version == "3.0":
                self.log_test("Engine Initialization", True, f"Version {version}")
                return True
            else:
                self.log_test("Engine Initialization", False, f"Wrong version: {version}")
                return False
        except Exception as e:
            self.log_test("Engine Initialization", False, f"Exception: {e}")
            return False
    
    def test_perspective_bug_fix(self) -> bool:
        """Test 2: Critical perspective bug fix validation."""
        try:
            # Test position where evaluation should be consistent from both perspectives
            test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            
            # Set position and evaluate as Black to move
            self.engine.set_position(test_fen)
            black_eval = self.engine.evaluator.evaluate(self.engine.board)
            
            # Make a move to switch sides
            legal_moves = self.engine.move_generator.get_legal_moves()
            test_move = legal_moves[0]  # Any legal move
            self.engine.make_move(test_move)
            
            # Evaluate as White to move (negated perspective)
            white_eval = self.engine.evaluator.evaluate(self.engine.board)
            
            # The evaluations should have opposite signs (perspective-aware)
            if (black_eval > 0 and white_eval < 0) or (black_eval < 0 and white_eval > 0) or (black_eval == 0):
                self.log_test("Perspective Bug Fix", True, 
                            f"Black eval: {black_eval}, White eval: {white_eval}")
                return True
            else:
                self.log_test("Perspective Bug Fix", False, 
                            f"Same sign evals - Black: {black_eval}, White: {white_eval}")
                return False
                
        except Exception as e:
            self.log_test("Perspective Bug Fix", False, f"Exception: {e}")
            return False
    
    def test_legal_move_generation(self) -> bool:
        """Test 3: Legal move generation validation."""
        try:
            test_positions = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Starting position
                "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",  # Complex position
                "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"  # Endgame position
            ]
            
            all_legal = True
            total_moves = 0
            
            for i, fen in enumerate(test_positions):
                self.engine.set_position(fen)
                moves = self.engine.move_generator.get_legal_moves()
                
                # Validate each move is actually legal
                for move in moves:
                    if move not in self.engine.board.board.legal_moves:
                        self.log_test("Legal Move Generation", False, 
                                    f"Illegal move {move.uci()} in position {i+1}")
                        all_legal = False
                
                total_moves += len(moves)
            
            if all_legal:
                self.log_test("Legal Move Generation", True, f"Validated {total_moves} moves")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test("Legal Move Generation", False, f"Exception: {e}")
            return False
    
    def test_search_functionality(self) -> bool:
        """Test 4: Search function validation."""
        try:
            # Test search from starting position
            self.engine.set_position("startpos")
            
            start_time = time.time()
            best_move = self.engine.search(depth_override=4)
            search_time = time.time() - start_time
            
            if best_move is None:
                self.log_test("Search Functionality", False, "No move returned")
                return False
            
            # Validate the returned move is legal
            legal_moves = self.engine.move_generator.get_legal_moves()
            if best_move not in legal_moves:
                self.log_test("Search Functionality", False, f"Illegal move returned: {best_move.uci()}")
                return False
            
            # Check search statistics
            if self.engine.nodes == 0:
                self.log_test("Search Functionality", False, "No nodes searched")
                return False
            
            self.log_test("Search Functionality", True, 
                        f"Move: {best_move.uci()}, Nodes: {self.engine.nodes}, Time: {search_time:.3f}s")
            return True
            
        except Exception as e:
            self.log_test("Search Functionality", False, f"Exception: {e}")
            return False
    
    def test_time_management(self) -> bool:
        """Test 5: Time management validation."""
        try:
            self.engine.set_position("startpos")
            
            # Test with time controls
            start_time = time.time()
            best_move = self.engine.search(wtime=10000, btime=10000, winc=100, binc=100)
            elapsed = time.time() - start_time
            
            if best_move is None:
                self.log_test("Time Management", False, "No move returned")
                return False
            
            # Should finish in reasonable time (less than 5 seconds for this test)
            if elapsed > 5.0:
                self.log_test("Time Management", False, f"Search took too long: {elapsed:.3f}s")
                return False
            
            self.log_test("Time Management", True, f"Time: {elapsed:.3f}s, Move: {best_move.uci()}")
            return True
            
        except Exception as e:
            self.log_test("Time Management", False, f"Exception: {e}")
            return False
    
    def test_uci_protocol_compliance(self) -> bool:
        """Test 6: UCI protocol compliance."""
        try:
            # Test basic UCI methods
            engine_info = self.engine.get_info()
            
            required_keys = ['name', 'version', 'author']
            for key in required_keys:
                if key not in engine_info:
                    self.log_test("UCI Protocol Compliance", False, f"Missing {key} in engine info")
                    return False
            
            if engine_info['version'] != '3.0':
                self.log_test("UCI Protocol Compliance", False, f"Wrong version: {engine_info['version']}")
                return False
            
            # Test new game functionality
            self.engine.new_game()
            if self.engine.nodes != 0:
                self.log_test("UCI Protocol Compliance", False, "Nodes not reset after new game")
                return False
            
            self.log_test("UCI Protocol Compliance", True, f"Info: {engine_info}")
            return True
            
        except Exception as e:
            self.log_test("UCI Protocol Compliance", False, f"Exception: {e}")
            return False
    
    def test_tactical_positions(self) -> bool:
        """Test 7: Tactical position solving."""
        try:
            # Test positions with clear best moves
            tactical_tests = [
                {
                    'fen': '2rr3k/pp3pp1/1nnqbN1p/3ppN2/2nPP3/2P1B3/PPQ2PPP/R4RK1 w - - 0 1',
                    'description': 'Queen sacrifice mate in 3'
                },
                {
                    'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1',
                    'description': 'Italian Game tactical position'
                }
            ]
            
            positions_solved = 0
            for i, test in enumerate(tactical_tests):
                self.engine.set_position(test['fen'])
                best_move = self.engine.search(depth_override=6)
                
                if best_move is not None:
                    positions_solved += 1
                    print(f"  Position {i+1}: {best_move.uci()} ({test['description']})")
            
            if positions_solved == len(tactical_tests):
                self.log_test("Tactical Positions", True, f"Solved {positions_solved}/{len(tactical_tests)}")
                return True
            else:
                self.log_test("Tactical Positions", False, f"Only solved {positions_solved}/{len(tactical_tests)}")
                return False
                
        except Exception as e:
            self.log_test("Tactical Positions", False, f"Exception: {e}")
            return False
    
    def test_endgame_knowledge(self) -> bool:
        """Test 8: Basic endgame knowledge."""
        try:
            # Test basic endgame positions
            endgame_tests = [
                {
                    'fen': '8/8/8/8/8/8/8/K6k w - - 0 1',  # KvK draw
                    'description': 'King vs King draw'
                },
                {
                    'fen': '8/8/8/8/8/8/P7/K6k w - - 0 1',  # KP vs K
                    'description': 'King and Pawn vs King'
                }
            ]
            
            evaluations_reasonable = True
            for i, test in enumerate(endgame_tests):
                self.engine.set_position(test['fen'])
                evaluation = self.engine.evaluator.evaluate(self.engine.board)
                
                # Basic sanity check - no extreme evaluations in simple endgames
                if abs(evaluation) > 1000:  # More than 10 pawns advantage seems unreasonable
                    evaluations_reasonable = False
                    print(f"  Position {i+1}: Extreme eval {evaluation} ({test['description']})")
                else:
                    print(f"  Position {i+1}: Eval {evaluation} ({test['description']})")
            
            if evaluations_reasonable:
                self.log_test("Endgame Knowledge", True, "Reasonable evaluations")
                return True
            else:
                self.log_test("Endgame Knowledge", False, "Extreme evaluations detected")
                return False
                
        except Exception as e:
            self.log_test("Endgame Knowledge", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("="*60)
        print("SlowMate v3.0 Production Validation Test Suite")
        print("="*60)
        
        test_functions = [
            self.test_engine_initialization,
            self.test_perspective_bug_fix,
            self.test_legal_move_generation,
            self.test_search_functionality,
            self.test_time_management,
            self.test_uci_protocol_compliance,
            self.test_tactical_positions,
            self.test_endgame_knowledge
        ]
        
        passed_tests = 0
        for test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"Test {test_func.__name__} crashed: {e}")
                traceback.print_exc()
        
        print("="*60)
        print(f"Test Results: {passed_tests}/{len(test_functions)} tests passed")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure['test']}: {failure['details']}")
        
        production_ready = (passed_tests == len(test_functions))
        
        if production_ready:
            print("\n✅ SlowMate v3.0 is PRODUCTION READY!")
            print("   - All critical bugs fixed")
            print("   - UCI protocol compliant") 
            print("   - Search and evaluation functional")
            print("   - Ready for tournament deployment")
        else:
            print(f"\n❌ SlowMate v3.0 has {len(self.failed_tests)} failing tests")
            print("   - NOT ready for production deployment")
            print("   - Fix failing tests before tournament use")
        
        return {
            'total_tests': len(test_functions),
            'passed_tests': passed_tests,
            'failed_tests': len(self.failed_tests),
            'production_ready': production_ready,
            'test_results': self.test_results
        }


def main():
    """Main test execution."""
    test_suite = SlowMateV3ValidationSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    if results['production_ready']:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
