#!/usr/bin/env python3
"""Quick debug test for UCI integration."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slowmate.engine import SlowMateEngine
import chess

def test_search_integration():
    print("🔧 Testing NegaScout Integration")
    print("=" * 40)
    
    # Create engine
    engine = SlowMateEngine()
    
    # Test position
    board = chess.Board()
    print(f"Position: {board.fen()}")
    print(f"Legal moves: {len(list(board.legal_moves))}")
    
    # Test search
    try:
        score, best_move = engine.search_engine.negascout_search(board, 3, -1000, 1000)
        print(f"Score: {score}")
        print(f"Best move: {best_move}")
        print(f"Move valid: {best_move in board.legal_moves if best_move else False}")
        
        # Test PV
        pv = engine.search_engine.get_pv()
        print(f"PV: {pv}")
        
        # Test stats
        stats = engine.get_search_stats()
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_integration()
