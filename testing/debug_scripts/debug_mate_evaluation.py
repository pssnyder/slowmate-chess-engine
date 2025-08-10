#!/usr/bin/env python3
"""
Debug script to investigate mate evaluation issues in SlowMate v0.3.01

The engine is showing +M500/8 which is clearly wrong. This script will:
1. Load the game position that shows the bug
2. Test different evaluation methods
3. Identify where the M500 is coming from
4. Fix the mate detection logic
"""

import chess
import chess.pgn
import io
from slowmate.intelligence import IntelligentSlowMateEngine, MoveIntelligence

def debug_mate_evaluation():
    """Debug the mate evaluation issues."""
    
    # Create engine instance
    engine = IntelligentSlowMateEngine()
    
    print("=== SlowMate v0.3.01 Mate Evaluation Debug ===\n")
    
    # Load the problematic game
    pgn_content = """[Event "Computer chess game"]
[Site "MAIN-DESKTOP"]
[Date "2025.07.22"]
[Round "?"]
[White "SlowMate_v0.3.01_Opening_Enhancements"]
[Black "SlowMate_v0.3.0_BETA"]
[Result "*"]

1. Nc3 Nc6 2. Nd5 e6 3. Nxc7+ Qxc7"""
    
    pgn_io = io.StringIO(pgn_content)
    game = chess.pgn.read_game(pgn_io)
    
    if game:
        # Set up the board position after the problematic sequence
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            
        engine.board = board
        print(f"Position after: {board.fen()}")
        print(f"Current turn: {'White' if board.turn else 'Black'}")
        print(f"Legal moves: {len(list(board.legal_moves))}")
        print()
        
        # Test 1: Basic position evaluation
        intelligence = MoveIntelligence(engine)
        position_eval = intelligence._evaluate_position()
        print(f"1. Basic position evaluation: {position_eval}")
        
        # Test 2: Check if this is detected as checkmate
        print(f"2. Is checkmate: {board.is_checkmate()}")
        print(f"   Is stalemate: {board.is_stalemate()}")
        print(f"   Is check: {board.is_check()}")
        print(f"   Is game over: {board.is_game_over()}")
        
        # Test 3: Evaluate specific moves and see their scores
        print("\n3. Move evaluations:")
        legal_moves = list(board.legal_moves)
        for i, move in enumerate(legal_moves[:5]):  # Test first 5 moves
            score = intelligence._evaluate_move(move)
            san_move = board.san(move)
            print(f"   {san_move}: {score}")
            
            # Check for mate in move evaluation
            if abs(score) > 9000:
                print(f"     ^ MATE SCORE DETECTED: {score}")
        
        # Test 4: Check checkmate detection
        print("\n4. Checkmate move detection:")
        checkmate_moves = intelligence._find_checkmate_moves(legal_moves)
        print(f"   Checkmate moves found: {len(checkmate_moves)}")
        for move in checkmate_moves:
            print(f"   - {board.san(move)}")
        
        # Test 5: Check if depth search is being used
        try:
            from slowmate.depth_search import DepthSearchEngine
            depth_engine = DepthSearchEngine()
            depth_engine.board = board.copy()
            
            print("\n5. Depth search evaluation:")
            best_move, score, pv = depth_engine.search_best_move()
            print(f"   Best move: {board.san(best_move) if best_move else 'None'}")
            print(f"   Score: {score}")
            print(f"   Is mate score: {depth_engine._is_mate_score(score)}")
            
            if depth_engine._is_mate_score(score):
                mate_distance = (10000 - abs(score))
                mate_moves = max(1, mate_distance // 2)
                if score < 0:
                    mate_moves = -mate_moves
                print(f"   Mate in: {mate_moves}")
                
        except Exception as e:
            print(f"\n5. Depth search failed: {e}")
        
        # Test 6: Check game phase detection
        print(f"\n6. Game phase: {intelligence.detect_game_phase()}")
        
        # Test 7: Detailed evaluation breakdown
        print("\n7. Detailed evaluation breakdown:")
        eval_details = intelligence.get_position_evaluation()
        for key, value in eval_details.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    debug_mate_evaluation()
