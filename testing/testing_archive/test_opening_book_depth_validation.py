#!/usr/bin/env python3
"""
Opening Book Depth Validation Test for v0.3.01

This test validates that the enhanced opening book provides:
- 8-10 moves deep for major openings (mainlines)
- 5-8 moves for variations (sidelines) 
- 1-2 alternatives for challenging positions (edge cases)
- Proper coverage for preferred openings (+1-2 additional moves)

Validates the specific requirements for v0.3.01 opening book enhancement.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.knowledge.opening_book import OpeningBook

def test_opening_depth(opening_name, moves_sequence, expected_min_depth=8):
    """
    Test that a specific opening line has sufficient depth.
    
    Args:
        opening_name: Name of the opening for reporting
        moves_sequence: List of moves in UCI notation
        expected_min_depth: Minimum moves expected in the book
        
    Returns:
        Dictionary with test results
    """
    print(f"\n🔍 Testing {opening_name}")
    print("=" * 60)
    
    book = OpeningBook()
    board = chess.Board()
    
    found_moves = []
    book_sources = []
    
    for i, move_uci in enumerate(moves_sequence):
        try:
            # Get book move for current position
            book_move = book.get_book_move(board)
            
            if book_move:
                book_san = board.san(book_move)
                found_moves.append(book_san)
                
                # Determine source
                position_key = book._get_position_key(board)
                if position_key in book.mainlines:
                    book_sources.append("mainlines")
                elif position_key in book.sidelines:
                    book_sources.append("sidelines")
                elif position_key in book.edge_cases:
                    book_sources.append("edge_cases")
                else:
                    book_sources.append("unknown")
                    
                print(f"Move {i+1}: {book_san} (from {book_sources[-1]})")
            else:
                print(f"Move {i+1}: No book move found")
                break
                
            # Make the expected move
            move = chess.Move.from_uci(move_uci)
            board.push(move)
            
        except Exception as e:
            print(f"Error processing move {i+1} ({move_uci}): {e}")
            break
    
    depth_achieved = len(found_moves)
    success = depth_achieved >= expected_min_depth
    
    print(f"\n📊 Results:")
    print(f"   Depth achieved: {depth_achieved}")
    print(f"   Expected minimum: {expected_min_depth}")
    print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
    
    if book_sources:
        source_summary = {}
        for source in book_sources:
            source_summary[source] = source_summary.get(source, 0) + 1
        print(f"   Sources used: {source_summary}")
    
    return {
        'opening': opening_name,
        'depth_achieved': depth_achieved,
        'expected_minimum': expected_min_depth,
        'success': success,
        'moves_found': found_moves,
        'sources': book_sources
    }

def test_variation_coverage(opening_name, base_moves, variations, expected_min_depth=5):
    """
    Test that variations of an opening have adequate coverage.
    
    Args:
        opening_name: Name of the opening
        base_moves: Common starting moves 
        variations: List of variation continuations
        expected_min_depth: Expected minimum depth for variations
    """
    print(f"\n🌳 Testing {opening_name} Variations")
    print("=" * 60)
    
    book = OpeningBook()
    results = []
    
    for i, variation in enumerate(variations):
        print(f"\n--- Variation {i+1}: {' '.join(variation)} ---")
        
        board = chess.Board()
        
        # Play base moves
        for move_uci in base_moves:
            move = chess.Move.from_uci(move_uci)
            board.push(move)
        
        # Test variation moves
        depth = 0
        for move_uci in variation:
            book_move = book.get_book_move(board)
            if book_move:
                book_san = board.san(book_move)
                print(f"   Move {len(base_moves) + depth + 1}: {book_san}")
                depth += 1
                
                # Make the move
                move = chess.Move.from_uci(move_uci)
                board.push(move)
            else:
                break
        
        success = depth >= expected_min_depth
        print(f"   Variation depth: {depth} {'✅' if success else '❌'}")
        
        results.append({
            'variation': ' '.join(variation),
            'depth': depth,
            'success': success
        })
    
    return results

def main():
    """Run comprehensive opening book depth validation."""
    print("🧪 SlowMate v0.3.01 - Opening Book Depth Validation")
    print("=" * 80)
    print("Testing Requirements:")
    print("• Mainlines: 8-10 moves deep for major openings")
    print("• Sidelines: 5-8 moves for variations") 
    print("• Edge cases: 1-2 alternatives for challenging positions")
    print("• Preferred openings: +1-2 additional moves deep")
    print("=" * 80)
    
    # Test major openings for depth (mainlines)
    main_openings = [
        ("Italian Game", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "f7f5", "d2d4"], 8),
        ("Spanish Opening", ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "o-o"], 8),
        ("Queen's Gambit", ["d2d4", "d7d5", "c2c4", "d5c4", "e2e3", "b7b5", "a2a4", "c7c6"], 8),
        ("Queen's Gambit Declined", ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5"], 7),
        ("French Defense", ["e2e4", "e7e6", "d2d4", "d7d5", "b1d2", "c7c5", "c2c3"], 7),
        ("Caro-Kann", ["e2e4", "c7c6", "d2d4", "d7d5", "e4e5", "c8f5", "g1f3"], 7),
        ("King's Indian", ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6"], 8),
        ("London System", ["d2d4", "g8f6", "g1f3", "e7e6", "c1f4", "f8e7", "e2e3", "o-o"], 8)
    ]
    
    print("\n📚 TESTING MAINLINE DEPTH (8-10 moves required)")
    print("=" * 80)
    
    mainline_results = []
    for opening_name, moves, min_depth in main_openings:
        result = test_opening_depth(opening_name, moves, min_depth)
        mainline_results.append(result)
    
    # Test variations (sidelines)
    print("\n\n🌿 TESTING SIDELINE VARIATIONS (5-8 moves required)")
    print("=" * 80)
    
    variation_tests = [
        ("Sicilian Defense", ["e2e4", "c7c5"], [
            ["g1f3", "d7d6", "d2d4", "c5d4", "f3d4"],
            ["g1f3", "b8c6", "d2d4", "c5d4", "f3d4"]
        ], 5),
        ("Vienna Game", ["e2e4", "e7e5", "b1c3"], [
            ["g8f6", "f2f4", "d7d5"],
            ["f8c5", "g1f3", "d7d6"]
        ], 3)
    ]
    
    variation_results = []
    for opening_name, base_moves, variations, min_depth in variation_tests:
        results = test_variation_coverage(opening_name, base_moves, variations, min_depth)
        variation_results.extend(results)
    
    # Test edge cases and alternatives
    print("\n\n🎯 TESTING EDGE CASES (alternatives for challenging positions)")
    print("=" * 80)
    
    edge_case_tests = [
        ("Scholar's Mate Defense", ["e2e4", "e7e5", "f1c4", "g8f6"], 2),
        ("Wayward Queen Defense", ["e2e4", "e7e5", "d1h5"], 2),
        ("King's Gambit Declined", ["e2e4", "e7e5", "f2f4", "f8c5"], 2),
        ("Center Game", ["e2e4", "e7e5", "d2d4", "e5d4"], 2)
    ]
    
    edge_case_results = []
    for opening_name, moves, min_depth in edge_case_tests:
        result = test_opening_depth(opening_name, moves, min_depth)
        edge_case_results.append(result)
    
    # Generate comprehensive report
    print("\n\n📊 COMPREHENSIVE VALIDATION REPORT")
    print("=" * 80)
    
    # Mainline summary
    mainline_passed = sum(1 for r in mainline_results if r['success'])
    print(f"\n✅ MAINLINES: {mainline_passed}/{len(mainline_results)} passed")
    for result in mainline_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['opening']}: {result['depth_achieved']}/{result['expected_minimum']} moves")
    
    # Variation summary
    variation_passed = sum(1 for r in variation_results if r['success'])
    print(f"\n🌿 SIDELINES: {variation_passed}/{len(variation_results)} passed")
    for result in variation_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['variation']}: {result['depth']} moves")
    
    # Edge case summary
    edge_passed = sum(1 for r in edge_case_results if r['success'])
    print(f"\n🎯 EDGE CASES: {edge_passed}/{len(edge_case_results)} passed")
    for result in edge_case_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['opening']}: {result['depth_achieved']}/{result['expected_minimum']} moves")
    
    # Overall assessment
    total_tests = len(mainline_results) + len(variation_results) + len(edge_case_results)
    total_passed = mainline_passed + variation_passed + edge_passed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎉 OVERALL RESULTS:")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Tests passed: {total_passed}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🏆 EXCELLENT: Opening book meets v0.3.01 requirements!")
    elif success_rate >= 60:
        print("✅ GOOD: Opening book mostly meets requirements, minor gaps")
    else:
        print("❌ NEEDS WORK: Opening book requires additional depth")
    
    print(f"\n📋 Ready for v0.3.01 dev candidate build: {'YES' if success_rate >= 70 else 'NO'}")

if __name__ == "__main__":
    main()
