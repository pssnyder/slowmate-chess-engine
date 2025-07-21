"""
SlowMate Chess Engine - Knowledge Base Coordinator

Central coordinator for all knowledge base components:
- Opening book integration
- Endgame pattern recognition
- Knowledge source prioritization
- Performance optimization

Features:
- Unified knowledge interface
- Component isolation and testing
- Performance monitoring
- Intelligent source weighting
"""

from typing import Optional, Dict, List, Any, Tuple
import chess
from chess import Board, Move
import time

from .opening_book import OpeningBook
from .opening_weights import OpeningWeights
from .endgame_patterns import EndgamePatterns
from .endgame_tactics import EndgameTactics


class KnowledgeBase:
    """
    Central coordinator for all chess knowledge components.
    
    Provides unified interface for accessing opening book, endgame patterns,
    and other knowledge sources with intelligent prioritization.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize knowledge base with all components.
        
        Args:
            data_dir: Root directory for all knowledge data
        """
        self.data_dir = data_dir
        
        # Initialize knowledge components
        self.opening_book = OpeningBook(f"{data_dir}/openings")
        self.opening_weights = OpeningWeights(f"{data_dir}/openings")
        self.endgame_patterns = EndgamePatterns(f"{data_dir}/endgames")
        self.endgame_tactics = EndgameTactics(f"{data_dir}/endgames")
        
        # Performance tracking
        self.query_count = 0
        self.total_query_time = 0.0
        self.hit_counts = {
            'opening_book': 0,
            'endgame_patterns': 0,
            'endgame_tactics': 0
        }
    
    def get_knowledge_move(self, board: Board, game_moves: Optional[List[Move]] = None) -> Optional[Tuple[Move, str]]:
        """
        Get the best knowledge-based move for current position.
        
        Args:
            board: Current chess position
            game_moves: List of moves played in the game so far
            
        Returns:
            Tuple of (move, source) if found, None otherwise
        """
        start_time = time.time()
        self.query_count += 1
        
        try:
            # Priority 1: Check for immediate endgame tactics
            tactical_move = self.endgame_tactics.get_tactical_move(board)
            if tactical_move:
                self.hit_counts['endgame_tactics'] += 1
                return tactical_move, 'endgame_tactics'
            
            # Priority 2: Check opening book
            opening_move = self.opening_book.get_book_move(board)
            if opening_move:
                # Apply opening weights and preferences
                weight = self.opening_weights.get_move_weight(
                    board, opening_move, [opening_move]
                )
                if weight > 0.5:  # Threshold for accepting move
                    self.hit_counts['opening_book'] += 1
                    return opening_move, 'opening_book'
            
            # Priority 3: Check strategic endgame patterns
            strategic_move = self.endgame_patterns.get_strategic_move(board)
            if strategic_move:
                self.hit_counts['endgame_patterns'] += 1
                return strategic_move, 'endgame_patterns'
            
            return None
            
        finally:
            self.total_query_time += time.time() - start_time
    
    def is_opening_phase(self, board: Board, move_count: int = 0) -> bool:
        """Determine if game is still in opening phase."""
        return move_count < 20 and self.opening_book.is_in_opening_book(board)
    
    def is_endgame_phase(self, board: Board) -> bool:
        """Determine if game has reached endgame phase."""
        return self.endgame_patterns._is_endgame_position(board)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        avg_query_time = (self.total_query_time / self.query_count 
                         if self.query_count > 0 else 0.0)
        
        return {
            'performance': {
                'total_queries': self.query_count,
                'total_time': self.total_query_time,
                'avg_query_time': avg_query_time
            },
            'hit_counts': self.hit_counts.copy(),
            'components': {
                'opening_book': self.opening_book.get_statistics(),
                'opening_weights': self.opening_weights.get_statistics(),
                'endgame_patterns': self.endgame_patterns.get_statistics(),
                'endgame_tactics': self.endgame_tactics.get_statistics()
            }
        }
    
    def reset_statistics(self):
        """Reset all performance statistics."""
        self.query_count = 0
        self.total_query_time = 0.0
        self.hit_counts = {key: 0 for key in self.hit_counts}
