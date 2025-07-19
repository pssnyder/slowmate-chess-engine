#!/usr/bin/env python3
"""
Test script demonstrating the feature toggle system for debugging tactical issues.
This script shows how to isolate different evaluation components.
"""
import chess
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slowmate.intelligence import MoveIntelligence, DEBUG_CONFIG, is_feature_enabled
from slowmate.engine import SlowMateEngine

def test_feature_isolation():
    """Test the tactical bug with different feature combinations."""
    
    # Setup the position from the bug
    fen = "rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20"
    board = chess.Board(fen)
    
    engine = SlowMateEngine()
    engine.board = board
    intelligence = MoveIntelligence(engine)
    
    # Test moves
    bxa8 = chess.Move.from_uci("g2a8")  # Capture rook
    bb7 = chess.Move.from_uci("g2b7")   # Retreat
    
    print("================================================================================")
    print("FEATURE ISOLATION TESTING")
    print("================================================================================")
    print(f"Position: {fen}")
    print()
    
    # Show current configuration
    print("🔧 CURRENT FEATURE CONFIGURATION:")
    for feature, enabled in DEBUG_CONFIG.items():
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        print(f"  {feature}: {status}")
    print()
    
    # Test both moves with current configuration
    print("📊 MOVE EVALUATION WITH CURRENT CONFIG:")
    for move in [bxa8, bb7]:
        score = intelligence._evaluate_move(move)
        combo_bonus = intelligence._calculate_tactical_combination_bonus(move, chess.WHITE)
        print(f"  {move}: Total={score}, TacticalBonus={combo_bonus}")
    
    print()
    print("💡 ISOLATION TESTING EXAMPLES:")
    print("To isolate specific features, modify DEBUG_CONFIG in intelligence.py:")
    print()
    
    print("1️⃣ Test ONLY material + captures (disable threats):")
    print("   DEBUG_CONFIG['threat_awareness'] = False")
    print("   DEBUG_CONFIG['tactical_combinations'] = False")
    print()
    
    print("2️⃣ Test ONLY threats + tactical combinations (disable captures):")
    print("   DEBUG_CONFIG['capture_calculation'] = False")
    print()
    
    print("3️⃣ Test WITHOUT tactical combinations (threats + captures separate):")
    print("   DEBUG_CONFIG['tactical_combinations'] = False")
    print()
    
    print("4️⃣ Test MINIMAL engine (only material and position):")
    print("   DEBUG_CONFIG['threat_awareness'] = False")
    print("   DEBUG_CONFIG['capture_calculation'] = False")
    print("   DEBUG_CONFIG['tactical_combinations'] = False")
    print("   DEBUG_CONFIG['king_safety'] = False")
    
    print()
    print("🚀 To test different configurations:")
    print("   1. Edit the DEBUG_CONFIG dictionary in intelligence.py")
    print("   2. Re-run this script or analyze_tactical_bug.py")
    print("   3. Compare move scores to isolate the problematic feature")

if __name__ == "__main__":
    test_feature_isolation()
