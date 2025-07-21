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
        if 'TranspositionTable' in options:
            self.config.enable_transposition_table = options['TranspositionTable']
        if 'TranspositionTableMB' in options:
            self.config.transposition_table_mb = options['TranspositionTableMB']
        if 'HashMoves' in options:
            self.config.enable_hash_moves = options['HashMoves']
        if 'BaseDepth' in options:
            self.config.base_depth = options['BaseDepth']
        if 'MaxDepth' in options:
            self.config.max_depth = options['MaxDepth']
        
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
        
        # Get hash move from transposition table
        hash_move = None
        if self.config.enable_transposition_table and self.config.enable_hash_moves:
            hash_move = self.move_ordering.get_hash_move(board)
        
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
    
    def update_history(self, move: chess.Move, depth: int, color: bool, success: bool):
        """
        Update history heuristic.
        
        Args:
            move: Move to update
            depth: Search depth
            color: Player color
            success: Whether move caused cutoff
        """
        self.move_ordering.update_history(move, depth, color, success)
    
    def store_counter_move(self, opponent_move: chess.Move, counter_move: chess.Move):
        """
        Store a counter move.
        
        Args:
            opponent_move: Opponent's move
            counter_move: Our best response
        """
        self.move_ordering.store_counter_move(opponent_move, counter_move)
    
    def get_move_ordering_stats(self) -> Dict[str, Any]:
        """Get move ordering statistics as dictionary."""
        stats = self.move_ordering.get_statistics()
        return {
            'moves_ordered': stats.moves_ordered,
            'see_evaluations': stats.see_evaluations,
            'killer_hits': stats.killer_hits,
            'history_hits': stats.history_hits,
            'counter_hits': stats.counter_hits,
            'hash_hits': stats.hash_hits,
            'knowledge_base_hits': stats.knowledge_base_hits,
            'ordering_time_ms': stats.ordering_time_ms,
            'see_time_ms': stats.see_time_ms,
            'killer_cutoffs': stats.killer_cutoffs,
            'history_cutoffs': stats.history_cutoffs,
            'counter_cutoffs': stats.counter_cutoffs,
            'beta_cutoffs_total': stats.beta_cutoffs_total,
            'first_move_cutoffs': stats.first_move_cutoffs
        }
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        stats = self.integration_stats.copy()
        
        # Calculate averages
        if stats['ordered_positions'] > 0:
            move_ordering_stats = self.get_move_ordering_stats()
            stats['average_ordering_time_ms'] = (
                move_ordering_stats['ordering_time_ms'] / stats['ordered_positions']
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
    
    def store_transposition(self, board: chess.Board, depth: int, score: int, 
                           bound_type: str, best_move: Optional[chess.Move] = None):
        """
        Store position in transposition table.
        
        Args:
            board: Current board position
            depth: Search depth
            score: Position evaluation  
            bound_type: 'exact', 'lower', or 'upper'
            best_move: Best move found
        """
        if not self.move_ordering.transposition_table:
            return
            
        # Convert bound type string to enum
        from slowmate.search.transposition_table import BoundType
        bound_map = {
            'exact': BoundType.EXACT,
            'lower': BoundType.LOWER_BOUND,
            'upper': BoundType.UPPER_BOUND
        }
        
        bound_enum = bound_map.get(bound_type, BoundType.EXACT)
        self.move_ordering.transposition_table.store(board, depth, score, bound_enum, best_move)
    
    def lookup_transposition(self, board: chess.Board, depth: int, alpha: int, beta: int):
        """
        Look up position in transposition table.
        
        Args:
            board: Current board position
            depth: Required search depth
            alpha: Current alpha value
            beta: Current beta value
            
        Returns:
            Tuple of (score, best_move, hit_type)
        """
        if not self.move_ordering.transposition_table:
            return None, None, 'miss'
            
        return self.move_ordering.transposition_table.lookup(board, depth, alpha, beta)
    
    def get_principal_variation(self, board: chess.Board, max_depth: int = 10) -> List[chess.Move]:
        """
        Get principal variation from transposition table.
        
        Args:
            board: Starting board position
            max_depth: Maximum PV depth
            
        Returns:
            List of moves in principal variation
        """
        if not self.move_ordering.transposition_table:
            return []
            
        return self.move_ordering.transposition_table.get_principal_variation(board, max_depth)
    
    def record_search_result(self, move: chess.Move, board: chess.Board, depth: int, 
                           caused_cutoff: bool = False, last_opponent_move: Optional[chess.Move] = None):
        """
        Record search result for learning heuristics.
        
        Args:
            move: Move that was played
            board: Board position after move
            depth: Search depth
            caused_cutoff: Whether this move caused a beta cutoff
            last_opponent_move: Opponent's last move (for counter moves)
        """
        # Record killer move if it caused a cutoff
        if caused_cutoff and not board.is_capture(move):
            self.move_ordering.store_killer_move(move, depth, board)
        
        # Update history heuristic
        color = not board.turn  # Color of the player who made the move
        self.move_ordering.update_history(move, depth, color, caused_cutoff)
        
        # Store counter move if we have opponent's last move
        if last_opponent_move and caused_cutoff:
            self.move_ordering.store_counter_move(last_opponent_move, move, success=True)
    
    def start_new_search(self):
        """Start a new search - reset state and age heuristics."""
        self.move_ordering.reset_for_search()
    
    def clear_transposition_table(self):
        """Clear the transposition table."""
        self.move_ordering.clear_transposition_table()
    
    def get_transposition_stats(self) -> Dict[str, Any]:
        """Get transposition table statistics."""
        if self.move_ordering.transposition_table:
            return self.move_ordering.transposition_table.get_statistics()
        return {}
    
    def get_killer_statistics(self) -> Dict[str, Any]:
        """Get killer move statistics."""
        return self.move_ordering.get_killer_statistics() or {}
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """Get history heuristic statistics."""
        return self.move_ordering.get_history_statistics() or {}
    
    def get_counter_statistics(self) -> Dict[str, Any]:
        """Get counter move statistics."""
        return self.move_ordering.get_counter_statistics() or {}
    
    def get_all_heuristic_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all heuristics."""
        return {
            'move_ordering': self.get_move_ordering_stats(),
            'transposition_table': self.get_transposition_stats(),
            'killer_moves': self.get_killer_statistics(),
            'history_heuristic': self.get_history_statistics(),
            'counter_moves': self.get_counter_statistics()
        }
