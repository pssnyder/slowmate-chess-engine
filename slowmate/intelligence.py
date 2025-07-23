"""
SlowMate Chess Engine - Move Selection Intelligence (v0.1.0 Baseline)

Tournament-winning move selection logic with:
- Checkmate detection
- Basic material evaluation  
- Simple position assessment
"""

import random
from typing import List, Tuple
import chess

def select_best_move(board: chess.Board) -> chess.Move:
    """
    Select the best move using v0.1.0 tournament-winning logic.
    
    Priority:
    1. Checkmate in one
    2. Avoid stalemate when winning
    3. Best material/positional evaluation
    4. Random from equal moves
    """
    
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    
    # Check for checkmate in one
    for move in legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return move
        board.pop()
    
    # Avoid stalemate when we're winning
    non_stalemate_moves = []
    for move in legal_moves:
        board.push(move)
        if not (board.is_stalemate() and _is_winning_position(board)):
            non_stalemate_moves.append(move)
        board.pop()
    
    if non_stalemate_moves:
        legal_moves = non_stalemate_moves
    
    # Evaluate all remaining moves
    move_scores = []
    for move in legal_moves:
        board.push(move)
        score = _evaluate_position(board)
        board.pop()
        move_scores.append((move, score))
    
    # Sort by score (best first)
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return best move (or random from tied best)
    best_score = move_scores[0][1]
    best_moves = [move for move, score in move_scores if score == best_score]
    
    return random.choice(best_moves)

def _evaluate_position(board: chess.Board) -> float:
    """Basic position evaluation (v0.1.0 baseline)."""
    
    if board.is_checkmate():
        return -1000 if board.turn == chess.WHITE else 1000
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Simple material count
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3, 
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    
    score = 0
    for piece_type in piece_values:
        white_pieces = len(board.pieces(piece_type, chess.WHITE))
        black_pieces = len(board.pieces(piece_type, chess.BLACK))
        score += (white_pieces - black_pieces) * piece_values[piece_type]
    
    # Adjust for side to move
    return score if board.turn == chess.WHITE else -score

def _is_winning_position(board: chess.Board) -> bool:
    """Check if current position is winning."""
    eval_score = _evaluate_position(board)
    return abs(eval_score) > 2  # Winning if up 2+ points of material
