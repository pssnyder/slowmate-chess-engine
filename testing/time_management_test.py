"""
Time Management Testing Suite for SlowMate Chess Engine
Tests various time control scenarios using UCI protocol
"""

import sys
import time
from pathlib import Path
import chess

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from slowmate.engine import SlowMateEngine
from slowmate.uci.protocol import UCIProtocol

class TimeManagementTester:
    def __init__(self):
        self.engine = SlowMateEngine()
        self.uci = UCIProtocol(self.engine)
        
    def run_position_test(self, fen: str, time_controls: dict, expected_range: tuple[float, float]) -> bool:
        """Test a specific position with given time controls.

        Measures wall-clock time between issuing 'go' and receiving 'bestmove'.
        Also captures the engine-logged allocated time when available.
        """
        # Reset engine and set position
        self.uci.process_command("ucinewgame")
        self.uci.process_command(f"position fen {fen}")

        outputs = []
        search_stats = {"elapsed": 0.0, "allocated": 0.0}
        bestmove = None
        start_time = None

        def capture_output(text: str):
            nonlocal bestmove, start_time
            outputs.append(text)
            # Allocated time logged by engine
            if text.startswith("info string ALLOCATED_TIME"):
                try:
                    search_stats["allocated"] = float(text.split()[2])
                except Exception:
                    pass
            if text == "info string START_SEARCH":
                if start_time is None:
                    start_time = time.time()
            if text.startswith("bestmove"):
                bestmove = text.split()[1]

        # Install capture and issue go
        original_out = self.uci._out
        self.uci._out = capture_output
        try:
            go_params = " ".join(f"{k} {v}" for k, v in time_controls.items())
            cmd_time = time.time()
            self.uci.process_command(f"go {go_params}")

            # Wait for bestmove or timeout
            timeout = cmd_time + 30
            while bestmove is None and time.time() < timeout:
                time.sleep(0.05)
        finally:
            # Restore output
            self.uci._out = original_out
            # Attempt to stop if still searching
            if self.uci.searching:
                self.uci.process_command("stop")
                time.sleep(0.05)

        # Determine start and elapsed times
        if start_time is None:
            start_time = cmd_time
        if bestmove:
            elapsed = time.time() - start_time
            search_stats["elapsed"] = elapsed
        else:
            search_stats["elapsed"] = 0.0

        # Print concise results
        print(f"\nPosition: {fen}")
        print(f"Time controls: {time_controls}")
        if bestmove:
            print(f"Selected move: {bestmove}")
        print(f"Time used: {search_stats['elapsed']:.2f} seconds")
        print(f"Expected range: {expected_range[0]:.2f} - {expected_range[1]:.2f} seconds")
        print(f"Allocated time (engine): {search_stats['allocated']:.2f} seconds")

        within_range = expected_range[0] <= search_stats['elapsed'] <= expected_range[1]
        print(f"Result: {'PASS' if within_range else 'FAIL'}")

        if not bestmove:
            print("Warning: No bestmove captured; last outputs:")
            for out in outputs[-10:]:
                print(f"  {out}")

        return within_range

def main():
    tester = TimeManagementTester()
    
    # Test cases
    test_cases = [
        # Opening position with plenty of time
        {
            "name": "Opening with time",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "controls": {
                "wtime": 300000,  # 5 minutes
                "btime": 300000,
                "winc": 2000,
                "binc": 2000
            },
            "expected": (1.0, 3.0)  # Expect 1-3 seconds in opening
        },
        
        # Middlegame tactical position with moderate time
        {
            "name": "Tactical middlegame",
            "fen": "r1bqk2r/pp1n1ppp/2pbpn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 8",
            "controls": {
                "wtime": 120000,  # 2 minutes
                "btime": 120000,
                "winc": 1000,
                "binc": 1000
            },
            "expected": (3.0, 6.0)  # Expect 3-6 seconds in tactical position
        },
        
        # Endgame position with low time
        {
            "name": "Endgame time pressure",
            "fen": "8/5pk1/7p/3KP3/6P1/8/8/8 w - - 0 45",
            "controls": {
                "wtime": 30000,  # 30 seconds
                "btime": 30000,
                "winc": 500,
                "binc": 500
            },
            "expected": (0.5, 2.0)  # Expect quick decisions under time pressure
        },
        
        # Complex position with specific moves to go
        {
            "name": "Complex with moves to go",
            "fen": "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
            "controls": {
                "wtime": 180000,  # 3 minutes
                "btime": 180000,
                "winc": 0,
                "binc": 0,
                "movestogo": 20
            },
            "expected": (4.0, 8.0)  # Expect careful thought with known moves to go
        },
        
        # Emergency time situation
        {
            "name": "Emergency time",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4",
            "controls": {
                "wtime": 1000,  # 1 second
                "btime": 1000,
                "winc": 100,
                "binc": 100
            },
            "expected": (0.1, 0.3)  # Expect very quick emergency move
        }
    ]
    
    # Run tests
    passed = 0
    total = len(test_cases)
    
    print("Starting Time Management Tests\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}/{total}: {test['name']}")
        print("-" * 50)
        
        if tester.run_position_test(
            test["fen"],
            test["controls"],
            test["expected"]
        ):
            passed += 1
            
    print(f"\nTest Summary: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
