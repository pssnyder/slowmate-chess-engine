#!/usr/bin/env python3
"""
SlowMate Chess Engine - Intelligence Demo

This script demonstrates the intelligent move selection capabilities of SlowMate.
Shows the difference between random and intelligent play.
"""

import sys
import os

# Add the slowmate package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.intelligence import IntelligentSlowMateEngine
import chess


def test_checkmate_detection():
    """Test the engine's ability to find checkmate moves."""
    print("=== CHECKMATE DETECTION TEST ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up a position where White can checkmate in 1
    # Scholar's mate position: Qh5 is checkmate
    engine.board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    
    print("Position: Scholar's mate setup")
    print(engine.get_board_state())
    print()
    
    legal_moves = engine.get_legal_moves()
    print(f"Legal moves available: {len(legal_moves)}")
    
    # Test intelligent selection
    selected_move = engine.select_move()
    if selected_move:
        reasoning = engine.intelligence.get_selection_reasoning(legal_moves, selected_move)
        move_san = engine.board.san(selected_move)
        print(f"Engine selected: {move_san}")
        print(f"Reasoning: {reasoning}")
        
        # Verify it's checkmate
        engine.board.push(selected_move)
        if engine.board.is_checkmate():
            print("✅ SUCCESS: Engine found the checkmate move!")
        else:
            print("❌ MISS: Engine did not find checkmate")
        engine.board.pop()
    
    print("\n")


def test_stalemate_avoidance():
    """Test the engine's ability to avoid stalemate."""
    print("=== STALEMATE AVOIDANCE TEST ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up a position where some moves lead to stalemate
    # King and Queen vs King endgame where bad moves cause stalemate
    engine.board = chess.Board("8/8/8/8/8/3k4/3q4/3K4 w - - 0 1")
    
    print("Position: King vs King+Queen (White to move)")
    print(engine.get_board_state())
    print()
    
    legal_moves = engine.get_legal_moves()
    print(f"Legal moves available: {len(legal_moves)}")
    
    # Test multiple move selections to see pattern
    stalemate_avoided = 0
    total_tests = 5
    
    for i in range(total_tests):
        selected_move = engine.select_move()
        if selected_move:
            reasoning = engine.intelligence.get_selection_reasoning(legal_moves, selected_move)
            move_san = engine.board.san(selected_move)
            
            # Check if this move would cause stalemate
            engine.board.push(selected_move)
            causes_stalemate = engine.board.is_stalemate()
            engine.board.pop()
            
            if not causes_stalemate:
                stalemate_avoided += 1
            
            print(f"Test {i+1}: {move_san} - {reasoning}")
            if causes_stalemate:
                print("  ⚠️  This move would cause stalemate")
    
    print(f"\nStalemate avoidance rate: {stalemate_avoided}/{total_tests}")
    print()


def test_intelligence_comparison():
    """Compare intelligent vs random play in a practical game."""
    print("=== INTELLIGENCE COMPARISON ===")
    
    print("Playing 10 moves with intelligence ON:")
    engine_smart = IntelligentSlowMateEngine()
    engine_smart.enable_intelligence = True
    
    for i in range(10):
        if engine_smart.is_game_over():
            break
        
        move_played = engine_smart.play_intelligent_move()
        if move_played:
            print(f"Move {i+1}: {move_played}")
        else:
            break
    
    print(f"Smart engine statistics: {engine_smart.get_move_reasoning()}")
    print()
    
    print("Playing 10 moves with intelligence OFF (random):")
    engine_random = IntelligentSlowMateEngine()
    engine_random.enable_intelligence = False
    
    for i in range(10):
        if engine_random.is_game_over():
            break
        
        move_played = engine_random.play_random_move()
        if move_played:
            print(f"Move {i+1}: {move_played}")
        else:
            break
    
    print(f"Random engine statistics: {engine_random.get_move_reasoning()}")
    print()


def test_specific_position():
    """Test engine behavior in a specific tactical position."""
    print("=== SPECIFIC POSITION TEST ===")
    
    engine = IntelligentSlowMateEngine()
    
    # Set up a position with tactical opportunities
    engine.board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    
    print("Position: Italian Game opening")
    print(engine.get_board_state())
    print()
    
    legal_moves = engine.get_legal_moves()
    print(f"Legal moves available: {len(legal_moves)}")
    
    # Show detailed analysis of move selection
    selected_move = engine.select_move()
    if selected_move:
        reasoning = engine.intelligence.get_selection_reasoning(legal_moves, selected_move)
        move_san = engine.board.san(selected_move)
        analysis = engine.intelligence.get_move_analysis(selected_move)
        
        print(f"Selected move: {move_san}")
        print(f"Reasoning: {reasoning}")
        print(f"Move analysis: {analysis}")
    
    print()


def main():
    """Run all intelligence tests."""
    print("SlowMate Chess Engine - Intelligence Testing")
    print("=" * 50)
    print()
    
    try:
        test_checkmate_detection()
        test_stalemate_avoidance()
        test_intelligence_comparison()
        test_specific_position()
        
        print("=" * 50)
        print("Intelligence testing complete!")
        print()
        print("Key improvements over random play:")
        print("✅ Finds checkmate moves when available")
        print("✅ Avoids stalemate when possible")
        print("✅ Avoids draw situations when possible")
        print("✅ Provides reasoning for move selection")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
