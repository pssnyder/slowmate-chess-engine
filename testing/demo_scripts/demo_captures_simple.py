#!/usr/bin/env python3
"""
Simple demo to test captures system

Let's test the captures system with a simple scenario.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def demo_basic_captures():
    """Demonstrate basic captures functionality."""
    print("=" * 60)
    print("SlowMate Chess Engine - Captures System Test")
    print("=" * 60)
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Simple winning capture position
    print("\n1. Testing Winning Capture:")
    # Black pawn on e4 can capture white queen on d3 diagonally
    board = chess.Board("4k3/8/8/8/4p3/3Q4/8/4K3 b - - 0 1")
    engine.board = board
    print(f"   Position: {board.fen()}")
    print(f"   {board.unicode()}")
    
    # Find capture moves
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    
    print(f"   Legal moves: {[board.san(m) for m in legal_moves]}")
    print(f"   Capture moves: {[board.san(m) for m in capture_moves]}")
    
    if capture_moves:
        capture = capture_moves[0]
        capture_eval = engine.intelligence._evaluate_capture_move(capture)
        print(f"   Capture evaluation: {capture_eval}")
    
    # Test 2: Get captures analysis
    print("\n2. Testing Captures Analysis:")
    captures_analysis = engine.intelligence._get_captures_analysis(chess.BLACK)
    print(f"   Black captures analysis: {captures_analysis}")
    
    # Test 3: Position evaluation with captures
    print("\n3. Testing Position Evaluation:")
    eval_details = engine.get_evaluation_details()
    print(f"   Black captures score: {eval_details.get('black_captures', 'Not found')}")
    print(f"   Black winning captures: {eval_details.get('black_winning_captures', 'Not found')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_basic_captures()
