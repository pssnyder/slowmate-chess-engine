"""
Search Integration Module for SlowMate Chess Engine

This module provides integration between the new modular move ordering system
and the existing search infrastructure. Designed for gradual migration and
backward compatibility during development.
"""

from typing import List, Optional, Dict, Any
import chess
from slowmate.search import SearchConfig, MoveOrderingStats
from slowmate.search.move_ordering import MoveOrderingEngine


class SearchIntegration:
    """Integration layer between new move ordering and existing search."""
    
    def __init__(self, engine):
        """
        Initialize search integration.
        
        Args:
            engine: SlowMateEngine instance
        """
        self.engine = engine
        
        # Initialize with default configuration
        self.config = SearchConfig()
        self.move_ordering = MoveOrderingEngine(self.config)
        
        # Track integration statistics
        self.integration_stats = {
            'ordered_positions': 0,
            'total_moves_ordered': 0,
            'average_ordering_time_ms': 0.0
        }
    
    def configure_from_uci(self, options: Dict[str, Any]):
        """
        Configure search parameters from UCI options.
        
        Args:
            options: UCI option values
        """
        # Update configuration based on UCI options
        if 'MoveOrdering' in options:
            self.config.enable_move_ordering = options['MoveOrdering']
        if 'SEEEvaluation' in options:
            self.config.enable_see_evaluation = options['SEEEvaluation']
        if 'SEEMaxDepth' in options:
            self.config.see_max_depth = options['SEEMaxDepth']
        if 'BaseDepth' in options:
            self.config.base_depth = options['BaseDepth']
        if 'MaxDepth' in options:
            self.config.max_depth = options['MaxDepth']
        if 'TranspositionTableMB' in options:
            self.config.transposition_table_mb = options['TranspositionTableMB']
        
        # Recreate move ordering engine with new config
        self.move_ordering = MoveOrderingEngine(self.config)
    
    def get_ordered_moves(self, board: chess.Board, depth: int = 0, 
                         hash_move: Optional[chess.Move] = None,
                         last_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        Get moves ordered by the new move ordering system.
        
        Args:
            board: Current board position
            depth: Current search depth
            hash_move: Best move from transposition table
            last_move: Opponent's last move
            
        Returns:
            List of moves ordered for optimal search
        """
        if not self.config.enable_move_ordering:
            # Return unordered legal moves if move ordering disabled
            return list(board.legal_moves)
        
        # Get all legal moves
        legal_moves = list(board.legal_moves)
        
        if len(legal_moves) <= 1:
            return legal_moves  # No need to order single move
        
        # Order moves using new system
        ordered_move_objects = self.move_ordering.order_moves(
            board, legal_moves, depth, hash_move, last_move
        )
        
        # Extract just the moves
        ordered_moves = [om.move for om in ordered_move_objects]
        
        # Update statistics
        self.integration_stats['ordered_positions'] += 1
        self.integration_stats['total_moves_ordered'] += len(ordered_moves)
        
        return ordered_moves
    
    def reset_for_search(self):
        """Reset move ordering state for new search."""
        self.move_ordering.reset_for_search()
    
    def store_killer_move(self, move: chess.Move, depth: int, board: chess.Board):
        """
        Store a killer move.
        
        Args:
            move: Move that caused beta cutoff
            depth: Search depth
            board: Current board position
        """
        self.move_ordering.store_killer_move(move, depth, board)
    
    def update_history(self, move: chess.Move, depth: int, success: bool):
        """
        Update history heuristic.
        
        Args:
            move: Move to update
            depth: Search depth
            success: Whether move caused cutoff
        """
        self.move_ordering.update_history(move, depth, success)
    
    def store_counter_move(self, opponent_move: chess.Move, counter_move: chess.Move):
        """
        Store a counter move.
        
        Args:
            opponent_move: Opponent's move
            counter_move: Our best response
        """
        self.move_ordering.store_counter_move(opponent_move, counter_move)
    
    def get_move_ordering_stats(self) -> MoveOrderingStats:
        """Get move ordering statistics."""
        return self.move_ordering.get_statistics()
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        stats = self.integration_stats.copy()
        
        # Calculate averages
        if stats['ordered_positions'] > 0:
            move_ordering_stats = self.get_move_ordering_stats()
            stats['average_ordering_time_ms'] = (
                move_ordering_stats.ordering_time_ms / stats['ordered_positions']
            )
            stats['average_moves_per_position'] = (
                stats['total_moves_ordered'] / stats['ordered_positions']
            )
        
        return stats
    
    def get_uci_options(self) -> Dict[str, Dict[str, Any]]:
        """Get UCI options for this search system."""
        return self.config.to_uci_options()
    
    def is_enhanced_move_ordering_enabled(self) -> bool:
        """Check if enhanced move ordering is enabled."""
        return self.config.enable_move_ordering
    
    def get_see_classification(self, board: chess.Board, move: chess.Move) -> str:
        """
        Get SEE classification for a capture move.
        
        Args:
            board: Current board position
            move: Capture move to classify
            
        Returns:
            'winning', 'equal', 'losing', or 'not_capture'
        """
        if not board.is_capture(move):
            return 'not_capture'
            
        if self.move_ordering.see_evaluator:
            return self.move_ordering.see_evaluator.classify_capture(board, move)
        elif self.move_ordering.mvv_lva:
            return self.move_ordering.mvv_lva.classify_capture_simple(board, move)
        else:
            return 'unknown'
