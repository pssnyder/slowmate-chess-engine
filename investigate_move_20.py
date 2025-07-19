#!/usr/bin/env python3
"""
Investigate Move 20 Issue - Missing Rook Capture

Analyzing why the engine chose Bb7 instead of capturing a rook.
Position after move 19: ...Ne3, White to move on move 20.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
from slowmate.intelligence import IntelligentSlowMateEngine


def analyze_move_20_issue():
    """Analyze the specific position where engine missed rook capture."""
    print("=" * 70)
    print("MOVE 20 ANALYSIS - Missing Rook Capture Investigation")
    print("=" * 70)
    
    # Let me reconstruct the position after move 19: ...Ne3
    # From the game: 1. Nc3 b5 2. Ne4 f5 3. Nc5 e6 4. Nb7 Qe7 5. a3 d6 
    # 6. h4 g5 7. hxg5 Qf7 8. g6 Qd7 9. gxh7 Rxh7 10. Rxh7 Qxh7 
    # 11. Nh3 Nh6 12. Ng5 Qd7 13. Nc5 Qd8 14. Ncxe6 Bxe6 15. Nxe6 Qc8 
    # 16. g4 Kd7 17. Nxc7 Kxc7 18. gxf5 Nxf5 19. Bg2 Ne3
    
    engine = IntelligentSlowMateEngine()
    
    # Let me create the position step by step to be accurate
    print("🔍 RECONSTRUCTING POSITION AFTER MOVE 19...")
    
    # Start from standard position and play the game
    board = chess.Board()
    
    moves = [
        "Nc3", "b5", "Ne4", "f5", "Nc5", "e6", "Nb7", "Qe7", 
        "a3", "d6", "h4", "g5", "hxg5", "Qf7", "g6", "Qd7", 
        "gxh7", "Rxh7", "Rxh7", "Qxh7", "Nh3", "Nh6", "Ng5", "Qd7", 
        "Nc5", "Qd8", "Ncxe6", "Bxe6", "Nxe6", "Qc8", "g4", "Kd7", 
        "Nxc7", "Kxc7", "gxf5", "Nxf5", "Bg2", "Ne3"
    ]
    
    print("   Playing moves to reach position...")
    for i, move_str in enumerate(moves):
        try:
            move = board.parse_san(move_str)
            board.push(move)
            print(f"   {i//2 + 1}{'.' if i % 2 == 0 else '...'} {move_str}")
        except Exception as e:
            print(f"   Error with move {move_str}: {e}")
            break
    
    engine.board = board
    print(f"\n   Final position (White to move, move 20):")
    print(f"   FEN: {board.fen()}")
    print(f"   {board.unicode()}")
    
    # Analyze the position
    print(f"\n📊 POSITION ANALYSIS:")
    
    # Check what legal moves are available
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    
    print(f"   Legal moves ({len(legal_moves)}): {[board.san(m) for m in legal_moves[:10]]}")
    if len(legal_moves) > 10:
        print(f"   ... and {len(legal_moves) - 10} more")
    
    print(f"   Capture moves ({len(capture_moves)}): {[board.san(m) for m in capture_moves]}")
    
    # Look for the rook capture specifically
    rook_captures = []
    for move in capture_moves:
        captured_piece = board.piece_at(move.to_square)
        if captured_piece and captured_piece.piece_type == chess.ROOK:
            rook_captures.append(move)
    
    if rook_captures:
        print(f"   🎯 ROOK CAPTURE AVAILABLE: {[board.san(m) for m in rook_captures]}")
        
        # Analyze the rook capture
        rook_capture = rook_captures[0]
        print(f"\n   Analyzing rook capture: {board.san(rook_capture)}")
        
        # Evaluate this specific move
        capture_eval = engine.intelligence._evaluate_capture_move(rook_capture)
        print(f"   Capture evaluation: {capture_eval}")
        
        # Check the move evaluation score
        move_score = engine.intelligence._evaluate_move(rook_capture)
        print(f"   Move evaluation score: {move_score}")
        
    else:
        print(f"   ❌ NO ROOK CAPTURES FOUND - checking for rooks on board...")
        
        # Check if there are any black rooks on the board
        black_rooks = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == chess.BLACK and piece.piece_type == chess.ROOK:
                black_rooks.append((square, chess.square_name(square)))
        
        print(f"   Black rooks on board: {[pos for square, pos in black_rooks]}")
        
        # Check what can attack those squares
        for square, pos in black_rooks:
            attackers = board.attackers(chess.WHITE, square)
            if attackers:
                print(f"   Rook on {pos} can be attacked by: {[chess.square_name(sq) for sq in attackers]}")
    
    # Test what the engine actually chooses
    print(f"\n🤖 ENGINE DECISION:")
    
    # Get evaluation details
    eval_details = engine.get_evaluation_details()
    print(f"   Current evaluation: {eval_details['total_evaluation']} centipawns")
    print(f"   White captures score: {eval_details['white_captures']}")
    print(f"   White winning captures: {eval_details['white_winning_captures']}")
    
    # Let engine choose move
    selected_move = engine.play_intelligent_move()
    print(f"   Engine selected: {selected_move}")
    
    # Check if it's the problematic Bb7
    if selected_move and "b7" in selected_move.lower():
        print(f"   ❌ CONFIRMED: Engine chose Bb7 move!")
        
        # Let's analyze why Bb7 was chosen over rook capture
        print(f"\n🔍 COMPARING MOVE OPTIONS:")
        
        # Find the Bb7 move
        bb7_moves = [move for move in legal_moves if "b7" in board.san(move).lower()]
        if bb7_moves:
            bb7_move = bb7_moves[0]
            bb7_score = engine.intelligence._evaluate_move(bb7_move)
            print(f"   Bb7 move score: {bb7_score}")
            
            # Check if Bb7 puts bishop under threat
            engine.board.push(bb7_move)
            bishop_square = bb7_move.to_square
            bishop_under_threat = engine.intelligence._is_piece_under_threat(bishop_square, chess.WHITE)
            engine.board.pop()
            
            print(f"   Bb7 puts bishop under threat: {bishop_under_threat}")
            
            if rook_captures:
                rook_score = engine.intelligence._evaluate_move(rook_captures[0])
                print(f"   Rook capture score: {rook_score}")
                print(f"   Score difference: {bb7_score - rook_score} (positive means Bb7 scored higher)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    analyze_move_20_issue()
