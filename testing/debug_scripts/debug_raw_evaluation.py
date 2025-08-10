#!/usr/bin/env python3
"""
Direct evaluation debugging - check raw scores before scaling
"""

import sys
import os
sys.path.append('slowmate')

import chess
from intelligence import MoveIntelligence
from engine import SlowMateEngine

def test_raw_evaluation():
    print("🔍 DIRECT EVALUATION DEBUGGING")
    print("=" * 40)
    
    try:
        # Create engine and intelligence
        engine = SlowMateEngine()
        intel = MoveIntelligence(engine)
        
        # Test starting position
        board = chess.Board()
        engine.board = board
        
        print("Testing starting position:")
        print(f"FEN: {board.fen()}")
        
        # Get raw evaluation
        raw_eval = intel._evaluate_position()
        print(f"Raw evaluation: {raw_eval} centipawns")
        
        # Check if scaling is being applied
        print(f"Raw evaluation in pawns: {raw_eval/100:.1f}")
        
        if abs(raw_eval) > 10000:
            print("🚨 RAW EVALUATION IS MASSIVE!")
            print("This explains why even 1% scaling gives huge values")
        elif abs(raw_eval) > 1000:
            print("⚠️  Raw evaluation is high but not extreme")
        else:
            print("✅ Raw evaluation seems reasonable")
            
        # Check scaling config
        from intelligence import get_debug_config
        scaling = get_debug_config('eval_scaling', 1)
        cap = get_debug_config('eval_max_cap', 2000)
        
        print(f"\nScaling config:")
        print(f"  eval_scaling: {scaling}")
        print(f"  eval_max_cap: {cap}")
        
        # Manual scaling test
        scaled = int(raw_eval * (scaling / 100.0))
        print(f"  Manually scaled: {scaled}")
        
        if abs(scaled) <= 300:
            print("✅ Manual scaling would work")
        else:
            print("❌ Even manual scaling fails")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_raw_evaluation()
