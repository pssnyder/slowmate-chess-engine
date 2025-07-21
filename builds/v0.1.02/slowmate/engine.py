"""
SlowMate Chess Engine - Core Engine Module

This module contains the main chess engine logic, now enhanced with
knowledge-based move selection including opening book and endgame patterns.
"""

import random
from typing import Optional, List
import chess
from .knowledge import KnowledgeBase


class SlowMateEngine:
    """
    SlowMate Chess Engine - Knowledge-Enhanced Move Selection
    
    Enhanced implementation featuring:
    - Legal move generation (via python-chess)
    - Knowledge-based move selection (opening book, endgame patterns)
    - Fallback to random selection when no knowledge available
    - Basic game state management
    
    Future phases will add:
    - Advanced search algorithms  
    - Position evaluation
    - Endgame tablebase integration
    """
    
    def __init__(self):
        """Initialize the engine with a new chess board and knowledge base."""
        self.board = chess.Board()
        self.move_count = 0
        self.game_moves: List[chess.Move] = []
        
        # Initialize knowledge base with correct data path
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_dir)  # Go up one level from slowmate/
        data_dir = os.path.join(project_dir, "data")
        
        self.knowledge_base = KnowledgeBase(data_dir)
        print(f"SlowMate engine initialized with knowledge base (data: {data_dir})")
        
        # Show initialization status
        self._show_initialization_status()
    
    def _show_initialization_status(self):
        """Display the status of knowledge base initialization."""
        stats = self.knowledge_base.get_statistics()
        components = stats['components']
        
        print(f"Opening book: {components['opening_book']['is_loaded']}")
        print(f"Endgame patterns: {components['endgame_patterns']['is_loaded']} " +
              f"({components['endgame_patterns']['mate_patterns']} mate patterns)")
        print(f"Endgame tactics: {components['endgame_tactics']['is_loaded']}")
        print("Knowledge base ready")
        
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
        Select a move using knowledge base or fallback to random selection.
        
        Priority order:
        1. Endgame tactics (immediate tactical wins)
        2. Opening book moves (if in opening phase)
        3. Endgame patterns (strategic endgame play)
        4. Random selection (fallback)
        
        Returns:
            chess.Move: Selected move, or None if no legal moves available
        """
        legal_moves = self.get_legal_moves()
        
        if not legal_moves:
            return None
        
        # Try knowledge-based move selection
        knowledge_result = self.knowledge_base.get_knowledge_move(self.board, self.game_moves)
        if knowledge_result:
            knowledge_move, source = knowledge_result
            print(f"SlowMate: Using {source} move: {self.board.san(knowledge_move)}")
            return knowledge_move
        
        # Fallback: Random selection
        selected_move = random.choice(legal_moves)
        print(f"SlowMate: Random move: {self.board.san(selected_move)}")
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
            self.game_moves.append(move)
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
        self.game_moves.clear()
    
    def get_engine_statistics(self) -> dict:
        """Get engine and knowledge base statistics."""
        return {
            'move_count': self.move_count,
            'current_phase': self._get_game_phase(),
            'knowledge_stats': self.knowledge_base.get_statistics()
        }
    
    def _get_game_phase(self) -> str:
        """Determine current game phase."""
        if self.knowledge_base.is_opening_phase(self.board, self.move_count):
            return "opening"
        elif self.knowledge_base.is_endgame_phase(self.board):
            return "endgame"
        else:
            return "middlegame"
