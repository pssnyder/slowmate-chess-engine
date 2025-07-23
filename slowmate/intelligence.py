"""
SlowMate Chess Engine - Minimal Intelligence (v0.4.03 STABLE)

SIMPLIFIED move selection to avoid bugs and focus on UCI compliance.
Complex intelligence features stubbed out for later re-implementation.
"""

import random
from typing import List, Optional
import chess

def select_best_move_simple(board: chess.Board) -> Optional[chess.Move]:
    """
    SIMPLIFIED move selection for stable baseline.
    
    TODO: Re-implement advanced features once UCI baseline is solid.
    """
    
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    
    # SIMPLIFIED: Just check for obvious checkmate
    for move in legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return move
        board.pop()
    
    # SIMPLIFIED: Basic capture preference
    captures = [move for move in legal_moves if board.is_capture(move)]
    if captures:
        return random.choice(captures)
    
    # SIMPLIFIED: Random move (avoid complex evaluation bugs)
    return random.choice(legal_moves)

# Keep legacy function for compatibility
def select_best_move(board: chess.Board) -> Optional[chess.Move]:
    """Legacy function - redirect to simplified version."""
    return select_best_move_simple(board)

# TODO: Re-implement these features once baseline is stable
def _evaluate_position(board: chess.Board) -> float:
    """TODO: Implement proper evaluation."""
    pass

def _is_winning_position(board: chess.Board) -> bool:
    """TODO: Implement winning position detection."""  
    pass
