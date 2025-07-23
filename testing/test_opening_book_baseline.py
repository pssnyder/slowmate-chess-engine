#!/usr/bin/env python3
"""
Opening Book Baseli        # Get move from engine
        if book_enabled:
            # Use knowledge base (includes opening book)
            knowledge_result = engine.knowledge_base.get_knowledge_move(board, engine.game_moves)
            if knowledge_result:
                selected_move, source = knowledge_result
                print(f"Move {move_count + 1}: {board.san(selected_move)} ({source})")
            else:
                # Fall back to intelligence if no knowledge move
                selected_move = engine.select_move()
                print(f"Move {move_count + 1}: {board.san(selected_move)} (intelligence)")
        else:
            # Use only intelligence (no opening book)
            selected_move = engine.select_move()
            print(f"Move {move_count + 1}: {board.san(selected_move)} (intelligence only)")est for v0.3.01

This test performs a baseline comparison by:
1. Testing engine with opening book DISABLED - recording first 10 moves per color
2. Testing engine with opening book ENABLED - recording first 10 moves per color  
3. Comparing results to identify impact of opening book on move selection

This helps identify:
- How much the opening book influences natural move selection
- Whether engine's natural evaluation aligns with accepted openings
- Opportunities to tune evaluation to naturally favor preferred openings
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine

def simulate_game_moves(engine, max_moves_per_color=10, book_enabled=True):
    """
    Simulate game moves and record them.
    
    Args:
        engine: Chess engine instance
        max_moves_per_color: Maximum moves to record per color
        book_enabled: Whether opening book is enabled
        
    Returns:
        Dictionary with white_moves and black_moves lists
    """
    board = chess.Board()
    white_moves = []
    black_moves = []
    
    move_count = 0
    max_total_moves = max_moves_per_color * 2
    
    print(f"🎮 Simulating game with book {'ENABLED' if book_enabled else 'DISABLED'}")
    print("=" * 60)
    
    while move_count < max_total_moves and not board.is_game_over():
        # Set engine board to current position  
        engine.board = board.copy()
        
        # Get move from engine
        if book_enabled:
            # Use knowledge base (includes opening book)
            move = engine.knowledge_base.get_knowledge_move(board, engine.game_moves)
            if move:
                selected_move, source = move
                print(f"Move {move_count + 1}: {board.san(selected_move)} ({source})")
            else:
                # Fall back to intelligence if no knowledge move
                selected_move = engine.select_move()
                print(f"Move {move_count + 1}: {board.san(selected_move)} (intelligence)")
        else:
            # Use only intelligence (no opening book)
            selected_move = engine.select_move()
            print(f"Move {move_count + 1}: {board.san(selected_move)} (intelligence only)")
        
        if selected_move is None:
            break
            
        # Record move by color
        if board.turn == chess.WHITE:
            white_moves.append(board.san(selected_move))
        else:
            black_moves.append(board.san(selected_move))
            
        # Make the move
        board.push(selected_move)
        engine.game_moves.append(selected_move)
        move_count += 1
        
        # Stop if we have enough moves for both colors
        if len(white_moves) >= max_moves_per_color and len(black_moves) >= max_moves_per_color:
            break
    
    print(f"\n📊 Recorded {len(white_moves)} white moves, {len(black_moves)} black moves")
    print("=" * 60)
    
    return {
        'white_moves': white_moves,
        'black_moves': black_moves,
        'final_position': board.fen()
    }

def compare_move_sequences(book_disabled_result, book_enabled_result):
    """Compare the two move sequences and analyze differences."""
    print("\n🔍 MOVE SEQUENCE COMPARISON")
    print("=" * 80)
    
    # Compare white moves
    print("\n🔸 WHITE MOVES:")
    print(f"{'Move #':<8} {'No Book':<15} {'With Book':<15} {'Match':<8} {'Analysis'}")
    print("-" * 70)
    
    white_matches = 0
    max_white = max(len(book_disabled_result['white_moves']), len(book_enabled_result['white_moves']))
    
    for i in range(max_white):
        no_book_move = book_disabled_result['white_moves'][i] if i < len(book_disabled_result['white_moves']) else "---"
        with_book_move = book_enabled_result['white_moves'][i] if i < len(book_enabled_result['white_moves']) else "---"
        
        match = "✅" if no_book_move == with_book_move else "❌"
        if no_book_move == with_book_move and no_book_move != "---":
            white_matches += 1
            
        analysis = ""
        if match == "❌" and no_book_move != "---" and with_book_move != "---":
            analysis = "Book influenced"
        elif match == "✅":
            analysis = "Natural choice"
            
        print(f"{i+1:<8} {no_book_move:<15} {with_book_move:<15} {match:<8} {analysis}")
    
    # Compare black moves  
    print("\n🔹 BLACK MOVES:")
    print(f"{'Move #':<8} {'No Book':<15} {'With Book':<15} {'Match':<8} {'Analysis'}")
    print("-" * 70)
    
    black_matches = 0
    max_black = max(len(book_disabled_result['black_moves']), len(book_enabled_result['black_moves']))
    
    for i in range(max_black):
        no_book_move = book_disabled_result['black_moves'][i] if i < len(book_disabled_result['black_moves']) else "---"
        with_book_move = book_enabled_result['black_moves'][i] if i < len(book_enabled_result['black_moves']) else "---"
        
        match = "✅" if no_book_move == with_book_move else "❌"
        if no_book_move == with_book_move and no_book_move != "---":
            black_matches += 1
            
        analysis = ""
        if match == "❌" and no_book_move != "---" and with_book_move != "---":
            analysis = "Book influenced"
        elif match == "✅":
            analysis = "Natural choice"
            
        print(f"{i+1:<8} {no_book_move:<15} {with_book_move:<15} {match:<8} {analysis}")
    
    # Summary statistics
    total_white_moves = min(len(book_disabled_result['white_moves']), len(book_enabled_result['white_moves']))
    total_black_moves = min(len(book_disabled_result['black_moves']), len(book_enabled_result['black_moves']))
    
    white_match_rate = (white_matches / total_white_moves * 100) if total_white_moves > 0 else 0
    black_match_rate = (black_matches / total_black_moves * 100) if total_black_moves > 0 else 0
    overall_match_rate = ((white_matches + black_matches) / (total_white_moves + total_black_moves) * 100) if (total_white_moves + total_black_moves) > 0 else 0
    
    print(f"\n📈 ANALYSIS SUMMARY:")
    print("=" * 50)
    print(f"White moves matching: {white_matches}/{total_white_moves} ({white_match_rate:.1f}%)")
    print(f"Black moves matching: {black_matches}/{total_black_moves} ({black_match_rate:.1f}%)")
    print(f"Overall match rate: {white_matches + black_matches}/{total_white_moves + total_black_moves} ({overall_match_rate:.1f}%)")
    
    # Interpretation
    print(f"\n🎯 INTERPRETATION:")
    if overall_match_rate > 70:
        print("• HIGH ALIGNMENT: Engine naturally selects moves similar to book recommendations")
        print("• Opening book provides refinement rather than major direction changes")
    elif overall_match_rate > 40:
        print("• MODERATE ALIGNMENT: Engine has some natural tendency toward book moves")  
        print("• Opening book provides valuable guidance and course correction")
    else:
        print("• LOW ALIGNMENT: Engine's natural evaluation differs significantly from book")
        print("• Opening book is essential for proper opening play")
        print("• Consider tuning evaluation to naturally favor opening principles")
    
    return {
        'white_match_rate': white_match_rate,
        'black_match_rate': black_match_rate,  
        'overall_match_rate': overall_match_rate,
        'white_matches': white_matches,
        'black_matches': black_matches
    }

def main():
    """Run the baseline comparison test."""
    print("🧪 SlowMate v0.3.01 - Opening Book Baseline Comparison")
    print("=" * 80)
    print("Purpose: Compare engine behavior with/without opening book")
    print("Goal: Identify alignment between natural evaluation and opening theory")
    print("=" * 80)
    
    # Initialize engines
    print("\n🔧 Initializing engines...")
    
    # Test 1: Opening book DISABLED 
    print("\n" + "="*60)
    print("TEST 1: OPENING BOOK DISABLED")
    print("="*60)
    
    engine_no_book = IntelligentSlowMateEngine()
    # Disable opening book by clearing its data
    engine_no_book.knowledge_base.opening_book.mainlines = {}
    engine_no_book.knowledge_base.opening_book.sidelines = {}
    engine_no_book.knowledge_base.opening_book.edge_cases = {}
    engine_no_book.knowledge_base.opening_book.is_loaded = False
    
    no_book_result = simulate_game_moves(engine_no_book, max_moves_per_color=10, book_enabled=False)
    
    # Test 2: Opening book ENABLED
    print("\n" + "="*60)  
    print("TEST 2: OPENING BOOK ENABLED")
    print("="*60)
    
    engine_with_book = IntelligentSlowMateEngine()
    # Book should be loaded automatically
    
    with_book_result = simulate_game_moves(engine_with_book, max_moves_per_color=10, book_enabled=True)
    
    # Compare results
    comparison_stats = compare_move_sequences(no_book_result, with_book_result)
    
    # Generate game notation for analysis
    print(f"\n📝 GAME SEQUENCES FOR ANALYSIS:")
    print("=" * 60)
    
    print(f"\n🚫 Without Opening Book:")
    white_moves_no_book = " ".join([f"{i//2+1}.{move}" if i%2==0 else f"{move}" 
                                   for i, move in enumerate(no_book_result['white_moves'] + no_book_result['black_moves'])])
    print(f"   {white_moves_no_book}")
    
    print(f"\n📚 With Opening Book:")  
    white_moves_with_book = " ".join([f"{i//2+1}.{move}" if i%2==0 else f"{move}"
                                     for i, move in enumerate(with_book_result['white_moves'] + with_book_result['black_moves'])])
    print(f"   {white_moves_with_book}")
    
    print(f"\n✅ BASELINE COMPARISON COMPLETE!")
    print("=" * 60)
    print("Use this data to:")
    print("• Identify where opening book provides most value")
    print("• Tune evaluation to naturally favor opening principles") 
    print("• Verify opening book selections align with engine strengths")

if __name__ == "__main__":
    main()
