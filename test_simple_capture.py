#!/usr/bin/env python3
"""
Simple single test for captures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def test_simple_capture():
    """Test simple capture detection."""
    print("Testing simple capture detection...")
    
    engine = IntelligentSlowMateEngine()
    board = chess.Board("4k3/8/8/8/4p3/3Q4/8/4K3 b - - 0 1")
    engine.board = board
    
    print(f"Board: {board.fen()}")
    print(f"Turn: {'Black' if board.turn == chess.BLACK else 'White'}")
    
    # Test the capture evaluation directly
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    
    print(f"Legal moves: {[board.san(m) for m in legal_moves]}")
    print(f"Capture moves: {[board.san(m) for m in capture_moves]}")
    
    if capture_moves:
        capture = capture_moves[0]
        print(f"Testing capture: {board.san(capture)}")
        
        try:
            capture_eval = engine.intelligence._evaluate_capture_move(capture)
            print(f"Capture evaluation: {capture_eval}")
        except Exception as e:
            print(f"Error evaluating capture: {e}")
    
    print("Done!")

if __name__ == "__main__":
    test_simple_capture()
