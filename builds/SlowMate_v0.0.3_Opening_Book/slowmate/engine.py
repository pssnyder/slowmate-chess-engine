"""
SlowMate Chess Engine - Core Engine Module

This module contains the main chess engine logic.
Current implementation: Random move selection from legal moves.
"""

import random
from typing import Optional
import chess


class SlowMateEngine:
    """
    SlowMate Chess Engine - Random Move Selection Implementation
    
    This is the initial implementation focusing on basic functionality:
    - Legal move generation (via python-chess)
    - Random move selection 
    - Basic game state management
    
    Future phases will add:
    - Move evaluation
    - Search algorithms  
    - Opening book
    - Endgame tablebase
    """
    
    def __init__(self):
        """Initialize the engine with a new chess board."""
        self.board = chess.Board()
        self.move_count = 0
        
    def get_board_state(self) -> str:
        """
        Return current board state in a readable format.
        Uses python-chess's string representation for now.
        """
        return str(self.board)
    
    def get_legal_moves(self) -> list:
        """
        Get all legal moves in the current position.
        Returns list of chess.Move objects.
        """
        return list(self.board.legal_moves)
    
    def select_move(self) -> Optional[chess.Move]:
        """
        Select a move using current algorithm (random selection).
        
        Returns:
            chess.Move: Selected move, or None if no legal moves available
        """
        legal_moves = self.get_legal_moves()
        
        if not legal_moves:
            return None
            
        # Current algorithm: Random selection
        selected_move = random.choice(legal_moves)
        return selected_move
    
    def make_move(self, move: chess.Move) -> bool:
        """
        Make a move on the board.
        
        Args:
            move: The move to make
            
        Returns:
            bool: True if move was legal and made, False otherwise
        """
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_count += 1
            return True
        return False
    
    def play_random_move(self) -> Optional[str]:
        """
        Select and play a random legal move.
        
        Returns:
            str: Algebraic notation of the move played, or None if game over
        """
        move = self.select_move()
        if move is None:
            return None
            
        # Convert to algebraic notation before making the move
        move_notation = self.board.san(move)
        
        self.make_move(move)
        return move_notation
    
    def is_game_over(self) -> bool:
        """Check if the current game is over."""
        return self.board.is_game_over()
    
    def get_game_result(self) -> str:
        """
        Get the result of the game if it's over.
        
        Returns:
            str: Game result ("1-0", "0-1", "1/2-1/2", or "ongoing")
        """
        if not self.is_game_over():
            return "ongoing"
            
        result = self.board.result()
        return result
    
    def get_game_status(self) -> str:
        """
        Get human-readable game status.
        
        Returns:
            str: Description of current game state
        """
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            return f"Checkmate! {winner} wins."
        elif self.board.is_stalemate():
            return "Stalemate! Draw."
        elif self.board.is_insufficient_material():
            return "Insufficient material! Draw."
        elif self.board.is_seventyfive_moves():
            return "75-move rule! Draw."
        elif self.board.is_fivefold_repetition():
            return "Fivefold repetition! Draw."
        else:
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            check_status = " (in check)" if self.board.is_check() else ""
            return f"{turn} to move{check_status}. Move #{self.move_count + 1}"
    
    def reset_game(self):
        """Reset the engine to a new game."""
        self.board.reset()
        self.move_count = 0
