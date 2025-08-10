#!/usr/bin/env python3
"""
SlowMate Evaluation Debug - Isolate the Component Causing Huge Scores

The engine is outputting cp 37200 (372 pawns) which is insane.
This script tests each evaluation component individually to find the culprit.
"""

import chess
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'slowmate'))

from slowmate.intelligence import IntelligentMoveSelector
from slowmate.engine import SlowMateEngine

def debug_evaluation_components():
    """Test each evaluation component to find which one is giving crazy scores."""
    
    print("🔍 DEBUGGING EVALUATION COMPONENTS")
    print("=" * 50)
    
    # Test position that showed cp 37200 
    fen = "r1bqkbnr/ppNp1ppp/2n1p3/8/8/8/PPPPPPPP/R1BQKBNR b KQkq - 0 3"
    
    # Create engine and selector
    engine = SlowMateEngine()
    engine.set_position_from_fen(fen)
    
    selector = IntelligentMoveSelector(engine)
    
    print(f"🎯 Testing position: {fen}")
    print(f"Turn: {'Black' if engine.board.turn == chess.BLACK else 'White'}")
    
    # Test each component individually
    components = {}
    
    try:
        # Material scores
        white_material = selector._calculate_material(chess.WHITE)
        black_material = selector._calculate_material(chess.BLACK)
        components['Material (White)'] = white_material
        components['Material (Black)'] = black_material
        components['Material Diff'] = (black_material - white_material) if engine.board.turn == chess.BLACK else (white_material - black_material)
        
        # PST scores
        white_pst = selector._calculate_pst_score(chess.WHITE)
        black_pst = selector._calculate_pst_score(chess.BLACK)
        components['PST (White)'] = white_pst
        components['PST (Black)'] = black_pst
        components['PST Diff'] = (black_pst - white_pst) if engine.board.turn == chess.BLACK else (white_pst - black_pst)
        
        # King safety
        white_king = selector._calculate_king_safety(chess.WHITE)
        black_king = selector._calculate_king_safety(chess.BLACK)
        components['King Safety (White)'] = white_king
        components['King Safety (Black)'] = black_king
        components['King Safety Diff'] = (black_king - white_king) if engine.board.turn == chess.BLACK else (white_king - black_king)
        
        # Captures
        white_captures = selector._calculate_captures_score(chess.WHITE)
        black_captures = selector._calculate_captures_score(chess.BLACK)
        components['Captures (White)'] = white_captures
        components['Captures (Black)'] = black_captures
        components['Captures Diff'] = (black_captures - white_captures) if engine.board.turn == chess.BLACK else (white_captures - black_captures)
        
        # Attacks
        white_attacks = selector._calculate_attack_patterns_score(chess.WHITE)
        black_attacks = selector._calculate_attack_patterns_score(chess.BLACK)
        components['Attacks (White)'] = white_attacks
        components['Attacks (Black)'] = black_attacks  
        components['Attacks Diff'] = (black_attacks - white_attacks) if engine.board.turn == chess.BLACK else (white_attacks - black_attacks)
        
        # Total evaluation
        total_eval = selector._calculate_basic_position_evaluation()
        components['TOTAL EVALUATION'] = total_eval
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        return False
    
    # Display results
    print("\n📊 EVALUATION BREAKDOWN:")
    print("=" * 40)
    
    total_sum = 0
    for component, score in components.items():
        if component == 'TOTAL EVALUATION':
            print("-" * 40)
            print(f"🎯 {component:<25} = {score:>8}")
            print("-" * 40)
        elif 'Diff' in component:
            total_sum += score
            if abs(score) > 1000:  # Highlight huge scores
                print(f"🚨 {component:<25} = {score:>8} ← HUGE!")
            else:
                print(f"✅ {component:<25} = {score:>8}")
        else:
            if abs(score) > 10000:  # Highlight individual huge scores
                print(f"⚠️  {component:<25} = {score:>8} ← Very high!")
            else:
                print(f"   {component:<25} = {score:>8}")
    
    print(f"\n🧮 Sum of diffs: {total_sum}")
    print(f"🎯 Total evaluation: {components.get('TOTAL EVALUATION', 'N/A')}")
    
    if abs(components.get('TOTAL EVALUATION', 0)) > 5000:
        print("\n🚨 FOUND THE PROBLEM!")
        print("The evaluation is WAY too high - should be ~100-500cp, not 37,000+")
        
        # Find the biggest culprit
        biggest_issue = None
        biggest_value = 0
        for component, score in components.items():
            if 'Diff' in component and abs(score) > biggest_value:
                biggest_value = abs(score)
                biggest_issue = component
        
        if biggest_issue:
            print(f"🎯 Biggest culprit: {biggest_issue} = {components[biggest_issue]}")
    
    return True

def test_normal_position():
    """Test a normal opening position for comparison."""
    
    print("\n🔍 TESTING NORMAL POSITION FOR COMPARISON")
    print("=" * 50)
    
    # Normal starting position after 1.e4
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    engine = SlowMateEngine()
    engine.set_position_from_fen(fen)
    
    selector = IntelligentMoveSelector(engine)
    
    print(f"🎯 Normal position: {fen}")
    
    try:
        total_eval = selector._calculate_basic_position_evaluation()
        print(f"📊 Normal evaluation: {total_eval}")
        
        if abs(total_eval) < 500:
            print("✅ Normal evaluation looks reasonable")
        else:
            print("❌ Even normal position has crazy evaluation!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main debug function."""
    
    print("🔍 SlowMate Evaluation Component Analysis")
    print("Finding why evaluation shows cp 37200 instead of reasonable values")
    print("=" * 70)
    
    # Test the problematic position
    success = debug_evaluation_components()
    
    if success:
        # Test normal position for comparison
        test_normal_position()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Identify which evaluation component is giving huge values")
        print("2. Scale or cap that component to reasonable ranges") 
        print("3. Test that total evaluation becomes reasonable (100-500cp)")
        print("4. Rebuild and test that Arena shows normal evaluations")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
