#!/usr/bin/env python3
"""
Test UCI interface with evaluation scores
"""

import subprocess
import sys
import os

def test_uci_evaluation():
    """Test UCI interface with evaluation information."""
    print("=== Testing UCI Interface with Evaluation ===")
    
    # Start UCI engine
    uci_script = os.path.join(os.path.dirname(__file__), "slowmate_uci.py")
    python_exe = r"S:/Maker Stuff/Programming/SlowMate Chess Engine/slowmate_chess_engine/.venv/Scripts/python.exe"
    
    proc = subprocess.Popen(
        [python_exe, uci_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    def send_command(cmd):
        print(f">>> {cmd}")
        if proc.stdin is None:
            raise RuntimeError("Failed to initialize stdin for the subprocess.")
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
    
    def read_until_ready():
        """Read output until we get 'readyok'."""
        if proc.stdout is None:
            raise RuntimeError("Failed to initialize stdout for the subprocess.")
        lines = []
        while True:
            line = proc.stdout.readline().strip()
            if not line:
                break
            print(f"<<< {line}")
            lines.append(line)
            if line == "readyok":
                break
        return lines
    
    def read_until_bestmove():
        """Read output until we get 'bestmove'."""
        if proc.stdout is None:
            raise RuntimeError("Failed to initialize stdout for the subprocess.")
        lines = []
        while True:
            line = proc.stdout.readline().strip()
            if not line:
                break
            print(f"<<< {line}")
            lines.append(line)
            if line.startswith("bestmove"):
                break
        return lines
    
    try:
        # Initialize engine
        send_command("uci")
        read_until_ready()
        
        send_command("isready")
        read_until_ready()
        
        # Enable debug mode to see reasoning
        send_command("setoption name Debug value true")
        send_command("isready")
        read_until_ready()
        
        # Test evaluation in starting position
        print("\n=== Starting Position ===")
        send_command("position startpos")
        send_command("go")
        output = read_until_bestmove()
        
        # Look for evaluation in output
        for line in output:
            if "score cp" in line:
                score = line.split("score cp")[1].split()[0]
                print(f"Engine evaluation: {score} centipawns")
        
        # Test position after some moves
        print("\n=== After e2e4 e7e5 ===")
        send_command("position startpos moves e2e4 e7e5")
        send_command("go")
        output = read_until_bestmove()
        
        # Look for evaluation in output
        for line in output:
            if "score cp" in line:
                score = line.split("score cp")[1].split()[0]
                print(f"Engine evaluation: {score} centipawns")
        
        # Test position with material imbalance
        print("\n=== Position with material advantage ===")
        send_command("position fen rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        send_command("go")
        output = read_until_bestmove()
        
        # Look for evaluation in output
        for line in output:
            if "score cp" in line:
                score = line.split("score cp")[1].split()[0]
                print(f"Engine evaluation: {score} centipawns")
        
        send_command("quit")
        
    except Exception as e:
        print(f"Error: {e}")
        proc.terminate()
    
    proc.wait()
    print("UCI evaluation test completed!")

if __name__ == "__main__":
    test_uci_evaluation()
