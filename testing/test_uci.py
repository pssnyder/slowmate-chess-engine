#!/usr/bin/env python3
"""
Test script for SlowMate UCI interface
"""

import subprocess
import sys
import os

def test_uci_engine():
    """Test the SlowMate UCI engine with various commands."""
    
    # Path to the engine
    engine_path = "S:/Maker Stuff/Programming/SlowMate Chess Engine/slowmate_chess_engine/.venv/Scripts/python.exe"
    script_path = "slowmate_uci.py"
    
    print("Testing SlowMate UCI Interface")
    print("=" * 40)
    
    # Test commands
    test_commands = [
        "uci",
        "debug on", 
        "isready",
        "position startpos",
        "go",
        "stop",
        "position startpos moves e2e4 e7e5",
        "go", 
        "quit"
    ]
    
    try:
        # Start the engine process
        process = subprocess.Popen(
            [engine_path, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        # Send commands and collect responses
        input_text = "\n".join(test_commands)
        stdout, stderr = process.communicate(input=input_text, timeout=10)
        
        print("Engine Output:")
        print("-" * 20)
        print(stdout)
        
        if stderr:
            print("Error Output:")
            print("-" * 20)
            print(stderr)
        
        print(f"Engine exit code: {process.returncode}")
        
    except subprocess.TimeoutExpired:
        print("Engine test timed out")
        process.kill()
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_uci_engine()
