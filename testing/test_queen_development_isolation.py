#!/usr/bin/env python3
"""
SlowMate Chess Engine v0.1.01 - Isolation Testing for Queen Development

Test suite using the debug configuration system to isolate different evaluation
components and identify why early queen moves are still being preferred.

This script will:
1. Test queen development penalties in isolation
2. Test minor piece development bonuses in isolation  
3. Test different combinations to find the optimal configuration
4. Analyze the specific game position where Qf4 was played
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence, DEBUG_CONFIG


def set_debug_config(config_updates):
    """Update the debug configuration temporarily"""
    original_config = DEBUG_CONFIG.copy()
    DEBUG_CONFIG.update(config_updates)
    return original_config


def restore_debug_config(original_config):
    """Restore the original debug configuration"""
    DEBUG_CONFIG.clear()
    DEBUG_CONFIG.update(original_config)


def test_queen_development_isolation():
    """Test queen development penalties in complete isolation"""
    
    print("="*70)
    print("🔬 QUEEN DEVELOPMENT ISOLATION TEST")
    print("="*70)
    
    # Save original config
    original_config = DEBUG_CONFIG.copy()
    
    # Disable everything except queen development
    isolation_config = {key: False for key in DEBUG_CONFIG.keys()}
    isolation_config.update({
        'queen_development': True,
        'material_calculation': True,  # Keep basic material for reference
        'checkmate_detection': True,   # Keep critical game states
        'stalemate_detection': True,
        'draw_prevention': True,
    })
    
    DEBUG_CONFIG.clear()
    DEBUG_CONFIG.update(isolation_config)
    
    try:
        engine = SlowMateEngine()
        intelligence = MoveIntelligence(engine)
        
        print("\n📊 ISOLATED QUEEN DEVELOPMENT TEST:")
        print("   Only queen development penalties active")
        
        # Test starting position
        engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        # Test queen vs other moves
        test_moves = [
            ("g1f3", "Knight to f3"),
            ("b1c3", "Knight to c3"),
            ("e2e4", "Pawn to e4"),
            ("d2d4", "Pawn to d4")
        ]
        
        print(f"\n   Move evaluations (queen development only):")
        for move_uci, description in test_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                if move in engine.board.legal_moves:
                    score = intelligence._evaluate_move(move)
                    print(f"   {move_uci} ({description}): {score} cp")
            except Exception as e:
                print(f"   {move_uci}: Error - {e}")
                
        # Test direct queen development penalty
        print(f"\n   Direct queen development scores:")
        white_queen_dev = intelligence._calculate_queen_development_score(chess.WHITE)
        print(f"   White queen (starting position): {white_queen_dev} cp")
        
        # Test queen move after opening the diagonal
        engine.board.push_uci("e2e4")  # Open diagonal
        engine.board.push_uci("e7e5")  # Black response
        
        qh5_score = -9999  # Default to very negative if not legal
        nf3_score = -9999  # Default to very negative if not legal
        
        # Now test queen moves
        if chess.Move.from_uci("d1h5") in engine.board.legal_moves:
            qh5_score = intelligence._evaluate_move(chess.Move.from_uci("d1h5"))
            print(f"   Qh5 (after e4 e5): {qh5_score} cp")
        else:
            print(f"   Qh5: Not legal in this position")
            
        # Test knight development  
        if chess.Move.from_uci("g1f3") in engine.board.legal_moves:
            nf3_score = intelligence._evaluate_move(chess.Move.from_uci("g1f3"))
            print(f"   Nf3 (after e4 e5): {nf3_score} cp")
        else:
            print(f"   Nf3: Not legal in this position")
            
        # Compare preferences (only if both moves are legal)
        if qh5_score > -9999 and nf3_score > -9999:
            print(f"\n   COMPARISON:")
            print(f"   Preference: {'Qh5' if qh5_score > nf3_score else 'Nf3'} by {abs(qh5_score - nf3_score)} cp")
            
            if qh5_score > nf3_score:
                print(f"   ❌ PROBLEM: Queen moves still preferred!")
                print(f"   Need to increase penalties or reduce tactical bonuses")
            else:
                print(f"   ✅ SUCCESS: Proper development preferred!")
            
        # Test penalty after the queen move
        if chess.Move.from_uci("d1h5") in engine.board.legal_moves:
            # Apply the move to test penalty
            engine.board.push_uci("d1h5")
            white_queen_dev_after = intelligence._calculate_queen_development_score(chess.WHITE)
            print(f"   White queen (after Qh5): {white_queen_dev_after} cp")
            print(f"   Penalty applied: {white_queen_dev_after - white_queen_dev} cp")
        
    finally:
        # Restore original config
        DEBUG_CONFIG.clear()
        DEBUG_CONFIG.update(original_config)


def test_minor_piece_development_isolation():
    """Test minor piece development bonuses in isolation"""
    
    print("\n" + "="*70)
    print("♞ MINOR PIECE DEVELOPMENT ISOLATION TEST")
    print("="*70)
    
    original_config = DEBUG_CONFIG.copy()
    
    # Isolate minor piece development
    isolation_config = {key: False for key in DEBUG_CONFIG.keys()}
    isolation_config.update({
        'minor_piece_development': True,
        'material_calculation': True,
        'checkmate_detection': True,
        'stalemate_detection': True,
        'draw_prevention': True,
    })
    
    DEBUG_CONFIG.clear()
    DEBUG_CONFIG.update(isolation_config)
    
    try:
        engine = SlowMateEngine()
        intelligence = MoveIntelligence(engine)
        
        print("\n📊 ISOLATED MINOR PIECE DEVELOPMENT TEST:")
        print("   Only minor piece development bonuses active")
        
        # Test starting position
        engine.board.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        # Test minor piece development
        minor_dev_start = intelligence._calculate_minor_piece_development_bonus(chess.WHITE)
        print(f"   Minor piece bonus (starting): {minor_dev_start} cp")
        
        # Develop one knight
        engine.board.push_uci("g1f3")
        minor_dev_one = intelligence._calculate_minor_piece_development_bonus(chess.WHITE)
        print(f"   Minor piece bonus (after Nf3): {minor_dev_one} cp")
        
        # Develop second piece
        engine.board.push_uci("g8f6")  # Black move
        engine.board.push_uci("b1c3")  # Second white knight
        minor_dev_two = intelligence._calculate_minor_piece_development_bonus(chess.WHITE)
        print(f"   Minor piece bonus (after Nc3): {minor_dev_two} cp")
        
        print(f"\n   Development progression:")
        print(f"   0 pieces: {minor_dev_start} cp")
        print(f"   1 piece:  {minor_dev_one} cp (+{minor_dev_one - minor_dev_start})")
        print(f"   2 pieces: {minor_dev_two} cp (+{minor_dev_two - minor_dev_one})")
        
    finally:
        DEBUG_CONFIG.clear()
        DEBUG_CONFIG.update(original_config)


def test_combined_development_system():
    """Test queen and minor piece development working together"""
    
    print("\n" + "="*70)
    print("🤝 COMBINED DEVELOPMENT SYSTEM TEST")
    print("="*70)
    
    original_config = DEBUG_CONFIG.copy()
    
    # Enable both development systems plus minimal others
    combined_config = {key: False for key in DEBUG_CONFIG.keys()}
    combined_config.update({
        'queen_development': True,
        'minor_piece_development': True,
        'material_calculation': True,
        'positional_evaluation': True,  # Include PST for more realistic comparison
        'checkmate_detection': True,
        'stalemate_detection': True,
        'draw_prevention': True,
    })
    
    DEBUG_CONFIG.clear()
    DEBUG_CONFIG.update(combined_config)
    
    try:
        engine = SlowMateEngine()
        intelligence = MoveIntelligence(engine)
        
        print("\n📊 COMBINED DEVELOPMENT SYSTEM TEST:")
        print("   Queen penalties + Minor piece bonuses + PST + Material")
        
        # Test the problematic game position
        print("\n🎯 Testing problematic position from actual game:")
        
        # Position after 1.Nc3 Nc6 2.Nd5 e6 3.Nxc7+ Qxc7
        engine.board.set_fen("r1bqkb1r/ppq1pppp/4p3/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 4")
        
        test_moves = [
            ("h2h4", "h4 (actual move played)"),
            ("d1h5", "Qh5 (early queen)"),
            ("g1f3", "Nf3 (knight development)"),
            ("f1c4", "Bc4 (bishop development)"),
            ("e2e4", "e4 (center pawn)"),
            ("d2d4", "d4 (center pawn)")
        ]
        
        scored_moves = []
        for move_uci, description in test_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                if move in engine.board.legal_moves:
                    score = intelligence._evaluate_move(move)
                    scored_moves.append((move_uci, description, score))
                    print(f"   {move_uci} ({description}): {score} cp")
            except Exception as e:
                print(f"   {move_uci}: Error - {e}")
                
        # Now test Black's response after h4
        engine.board.push_uci("h2h4")
        print(f"\n   Black responses after h4:")
        
        black_moves = [
            ("d8f4", "Qf4 (early queen - actual move)"),
            ("g8f6", "Nf6 (knight development)"),
            ("f8c5", "Bc5 (bishop development)"),
            ("c7c5", "Qc5 (queen retreat)"),
            ("d7d6", "d6 (pawn development)")
        ]
        
        for move_uci, description in black_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                if move in engine.board.legal_moves:
                    score = intelligence._evaluate_move(move)
                    print(f"   {move_uci} ({description}): {score} cp")
            except Exception as e:
                print(f"   {move_uci}: Error - {e}")
                
    finally:
        DEBUG_CONFIG.clear()
        DEBUG_CONFIG.update(original_config)


def test_increasing_queen_penalties():
    """Test with dramatically increased queen penalties"""
    
    print("\n" + "="*70)
    print("💪 MAXIMUM QUEEN PENALTY TEST")
    print("="*70)
    
    original_config = DEBUG_CONFIG.copy()
    
    # Enable key systems
    max_penalty_config = {key: False for key in DEBUG_CONFIG.keys()}
    max_penalty_config.update({
        'queen_development': True,
        'minor_piece_development': True,
        'material_calculation': True,
        'positional_evaluation': True,
        'checkmate_detection': True,
        'stalemate_detection': True,
        'draw_prevention': True,
    })
    
    DEBUG_CONFIG.clear()
    DEBUG_CONFIG.update(max_penalty_config)
    
    try:
        engine = SlowMateEngine()
        intelligence = MoveIntelligence(engine)
        
        print("\n📊 Testing with current queen penalties:")
        
        # Test starting position queen moves vs development
        engine.board.set_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")  # After e4
        
        # Now test if Qh5 is available for white
        engine.board = chess.Board()  # Reset
        engine.board.push_uci("e2e4")  # e4
        engine.board.push_uci("e7e5")  # e5
        
        if chess.Move.from_uci("d1h5") in engine.board.legal_moves:
            qh5_score = intelligence._evaluate_move(chess.Move.from_uci("d1h5"))
            print(f"   Qh5 (after e4 e5): {qh5_score} cp")
        else:
            print(f"   Qh5: Not legal in this position")
            
        if chess.Move.from_uci("g1f3") in engine.board.legal_moves:
            nf3_score = intelligence._evaluate_move(chess.Move.from_uci("g1f3"))
            print(f"   Nf3 (after e4 e5): {nf3_score} cp")
        else:
            print(f"   Nf3: Not legal in this position")
        print(f"   Preference: {'Qh5' if qh5_score > nf3_score else 'Nf3'} by {abs(qh5_score - nf3_score)} cp")
        
        if qh5_score > nf3_score:
            print(f"\n❌ PROBLEM: Queen moves still preferred!")
            print(f"   Need to increase penalties or reduce tactical bonuses")
        else:
            print(f"\n✅ SUCCESS: Proper development preferred!")
            
    finally:
        DEBUG_CONFIG.clear()
        DEBUG_CONFIG.update(original_config)


def run_isolation_tests():
    """Run all isolation tests"""
    
    print("🔬 SlowMate v0.1.01 - Queen Development Isolation Testing")
    print("🎯 Using debug configuration system to isolate evaluation components")
    print("📅 Testing why early queen moves are still being preferred")
    print()
    
    try:
        # Test individual components
        test_queen_development_isolation()
        test_minor_piece_development_isolation()
        test_combined_development_system()
        test_increasing_queen_penalties()
        
        print("\n" + "="*70)
        print("🏁 ISOLATION TESTING COMPLETE")
        print("="*70)
        print("✅ All isolation tests completed")
        print("📊 Results should show which components need adjustment")
        print("🎯 Focus on components that allow early queen moves to score highly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ISOLATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_isolation_tests()
    exit(0 if success else 1)
