"""
UCI Blunder Test: Compare SlowMate_v1.0 blunder positions to SlowMate_v1.5 recommendations using UCI protocol.
"""
import subprocess
import sys
import time
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.uci_main import UCIMain

BLUNDER_TESTS = [
    {
        "fen": "rnbqkbnr/pppp1ppp/4p3/8/8/5N2/BBPPPPPP/RN1QK2R w KQkq - 0 7",
        "v1_0_move": "f2f4",
        "desc": "After 6...Qxb2, White to move (v1.0 blunder: f4)"
    },
    {
        "fen": "rnbqkbnr/pppp1ppp/4p3/8/8/5N2/BBPPPPPP/RN1QK2R w KQkq - 0 8",
        "v1_0_move": "c2c4",
        "desc": "After 7...Qxa1, White to move (v1.0 blunder: c4)"
    },
    {
        "fen": "r1bqkbnr/pppp1ppp/2n1p3/8/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4",
        "v1_0_move": "d2d3",
        "desc": "Italian Game position, White to move (v1.0 suboptimal: d3)"
    },
    {
        "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4",
        "v1_0_move": "f8e7",
        "desc": "Italian Game, Black to move (v1.0 passive: Be7)"
    },
    {
        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 6",
        "v1_0_move": "b1d2",
        "desc": "Italian Game development, White to move (v1.0 slow: Nd2)"
    }
]

ENGINE_CMD = [sys.executable, "-m", "slowmate.uci_main"]


def run_uci_test_subprocess(fen, movetime=3000):
    """Run UCI test using subprocess (traditional method)."""
    try:
        proc = subprocess.Popen(
            ENGINE_CMD, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            bufsize=0
        )
        
        if proc.stdin is None or proc.stdout is None:
            print("Failed to create subprocess pipes")
            return None
        
        # Send UCI initialization
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        time.sleep(0.1)
        
        # Set position
        proc.stdin.write(f"position fen {fen}\n")
        proc.stdin.flush()
        time.sleep(0.1)
        
        # Start search
        proc.stdin.write(f"go movetime {movetime}\n")
        proc.stdin.flush()
        
        # Read until we get bestmove
        bestmove = None
        start_time = time.time()
        timeout = (movetime / 1000) + 5  # Add 5 seconds buffer
        
        while time.time() - start_time < timeout:
            try:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("bestmove"):
                    parts = line.split()
                    if len(parts) > 1:
                        bestmove = parts[1]
                    break
            except Exception as e:
                print(f"Error reading from subprocess: {e}")
                break
        
        # Clean shutdown
        try:
            if proc.stdin:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
            proc.wait(timeout=2)
        except:
            proc.terminate()
            
        return bestmove
        
    except Exception as e:
        print(f"Subprocess error: {e}")
        return None


def run_uci_test_direct(fen, movetime=3000):
    """Run UCI test using direct UCI interface (faster for testing)."""
    try:
        uci_main = UCIMain(debug_mode=False)
        if not uci_main.initialize_engine():
            return None
            
        # Set silent mode for cleaner output
        if uci_main.uci:
            uci_main.uci.set_silent_mode(True)
            
            # Capture the best move
            captured_move = None
            
            def move_callback(move, ponder=None):
                nonlocal captured_move
                captured_move = move.uci() if move else None
                
            uci_main.uci.set_move_callback(move_callback)
            
            # Run UCI commands
            commands = [
                "uci",
                f"position fen {fen}",
                f"go movetime {movetime}"
            ]
            
            for command in commands:
                uci_main.uci.process_command(command)
                if command.startswith("go"):
                    # Wait for search to complete
                    start_time = time.time()
                    timeout = (movetime / 1000) + 2
                    while uci_main.uci.searching and time.time() - start_time < timeout:
                        time.sleep(0.01)
                        
            return captured_move
            
    except Exception as e:
        print(f"Direct UCI error: {e}")
        return None


def main():
    print("=== SlowMate Blunder Prevention A/B Test ===\n")
    
    print("Testing method: Direct UCI interface (faster)")
    print("Movetime: 3000ms per position\n")
    
    avoided_blunders = 0
    total_tests = len(BLUNDER_TESTS)
    
    for i, test in enumerate(BLUNDER_TESTS, 1):
        print(f"Test {i}/{total_tests}: {test['desc']}")
        print(f"FEN: {test['fen']}")
        print(f"v1.0 move: {test['v1_0_move']}")
        
        # Try direct method first, fall back to subprocess if needed
        bestmove = run_uci_test_direct(test['fen'])
        if bestmove is None:
            print("  Direct method failed, trying subprocess...")
            bestmove = run_uci_test_subprocess(test['fen'])
            
        print(f"v1.5 move: {bestmove}")
        
        if bestmove is None:
            print("  Result: ERROR - No move returned!")
        elif bestmove == test['v1_0_move']:
            print("  Result: ❌ REPEATED BLUNDER")
        elif bestmove == "0000" or bestmove == "(none)":
            print("  Result: ERROR - Invalid move returned!")
        else:
            print("  Result: ✅ BLUNDER AVOIDED")
            avoided_blunders += 1
            
        print()
    
    print("=== SUMMARY ===")
    print(f"Blunders avoided: {avoided_blunders}/{total_tests}")
    print(f"Success rate: {(avoided_blunders/total_tests)*100:.1f}%")
    
    if avoided_blunders == total_tests:
        print("🎉 ALL BLUNDERS AVOIDED! Engine improvement confirmed.")
    elif avoided_blunders >= total_tests * 0.8:
        print("✅ Good improvement - most blunders avoided.")
    elif avoided_blunders >= total_tests * 0.5:
        print("⚠️  Some improvement - still room for enhancement.")
    else:
        print("❌ Limited improvement - further tuning needed.")


if __name__ == "__main__":
    main()
