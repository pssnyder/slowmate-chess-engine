#!/usr/bin/env python3
"""
Comprehensive captures system demo

Tests all aspects of the captures evaluation system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def demo_comprehensive_captures():
    """Demonstrate comprehensive captures functionality."""
    print("=" * 60)
    print("SlowMate Chess Engine - Comprehensive Captures Demo")
    print("=" * 60)
    
    engine = IntelligentSlowMateEngine()
    
    # Test 1: Simple winning capture
    print("\n1. Testing Winning Capture (Black to move):")
    board = chess.Board("4k3/8/8/8/4p3/3Q4/8/4K3 b - - 0 1")
    engine.board = board
    print(f"   {board.unicode()}")
    
    try:
        # Test individual components
        print("   Testing black captures score...")
        black_captures_score = engine.intelligence._calculate_captures_score(chess.BLACK)
        print(f"   Black captures score: {black_captures_score}")
        
        print("   Testing white captures score...")
        white_captures_score = engine.intelligence._calculate_captures_score(chess.WHITE)
        print(f"   White captures score: {white_captures_score}")
        
        print("   Testing black captures analysis...")
        black_analysis = engine.intelligence._get_captures_analysis(chess.BLACK)
        print(f"   Black analysis: {black_analysis}")
        
    except Exception as e:
        print(f"   Error in captures calculation: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Position evaluation
    print("\n2. Testing Position Evaluation Integration:")
    try:
        eval_details = engine.get_evaluation_details()
        print(f"   Evaluation completed successfully")
        print(f"   Black captures: {eval_details.get('black_captures', 'Missing')}")
        print(f"   White captures: {eval_details.get('white_captures', 'Missing')}")
        print(f"   Black winning captures: {eval_details.get('black_winning_captures', 'Missing')}")
    except Exception as e:
        print(f"   Error in position evaluation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_comprehensive_captures()
