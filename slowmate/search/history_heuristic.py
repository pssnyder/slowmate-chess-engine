"""
History Heuristic for SlowMate v0.2.01 Phase 3
Tracks move success rates using butterfly boards for improved move ordering.

The history heuristic maintains statistics about how often moves work well
throughout the search tree. Moves that frequently cause cutoffs get higher
priority in move ordering. Uses the "butterfly board" approach where we
track from_square -> to_square combinations for both colors.

Architecture: Modern approach with aging and normalization for tournament play.
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class HistoryStats:
    """Statistics for history heuristic effectiveness."""
    
    history_moves_recorded: int = 0
    history_moves_applied: int = 0
    history_hits: int = 0
    beta_cutoffs_from_history: int = 0
    
    # Aging and normalization
    aging_cycles: int = 0
    max_history_value: int = 0
    
    # Performance tracking
    total_lookups: int = 0
    successful_lookups: int = 0
    
    def get_hit_rate(self) -> float:
        """Get history move hit rate."""
        if self.total_lookups == 0:
            return 0.0
        return (self.successful_lookups / self.total_lookups) * 100.0
    
    def get_effectiveness(self) -> float:
        """Get history move effectiveness (cutoffs per hit)."""
        if self.history_hits == 0:
            return 0.0
        return (self.beta_cutoffs_from_history / self.history_hits) * 100.0
    
    def reset(self):
        """Reset all statistics."""
        self.history_moves_recorded = 0
        self.history_moves_applied = 0
        self.history_hits = 0
        self.beta_cutoffs_from_history = 0
        self.aging_cycles = 0
        self.max_history_value = 0
        self.total_lookups = 0
        self.successful_lookups = 0


class HistoryTable:
    """
    History heuristic using butterfly boards.
    
    Maintains two 64x64 tables (one for each color) tracking move success rates.
    Each entry represents moves from one square to another. The values are
    incremented when moves cause beta cutoffs and aged periodically.
    """
    
    def __init__(self):
        """Initialize history tables."""
        
        # Butterfly boards: [color][from_square][to_square]
        # White = True (1), Black = False (0)
        self.history: List[List[List[int]]] = [
            [[0 for _ in range(64)] for _ in range(64)] for _ in range(2)
        ]
        
        # Statistics
        self.stats = HistoryStats()
        
        # Configuration
        self.max_history_value = 16384  # Maximum value before aging
        self.aging_threshold = 32768    # Trigger aging when max exceeds this
        self.aging_factor = 2           # Divide by this during aging
        self.min_significant_value = 4  # Minimum value to be considered significant
        
        # Current maximum value for normalization
        self.current_max = 0
    
    def record_move(self, move: chess.Move, color: bool, depth: int, caused_cutoff: bool = False):
        """
        Record a move in the history table.
        
        Args:
            move: The move to record
            color: True for white, False for black
            depth: Search depth where move was played
            caused_cutoff: Whether this move caused a beta cutoff
        """
        from_sq = move.from_square
        to_sq = move.to_square
        color_index = 1 if color else 0
        
        # Calculate increment based on depth - deeper moves get higher bonus
        increment = depth * depth if caused_cutoff else 1
        
        # Record the move
        self.history[color_index][from_sq][to_sq] += increment
        self.stats.history_moves_recorded += 1
        
        if caused_cutoff:
            self.stats.beta_cutoffs_from_history += 1
        
        # Update maximum value tracking
        new_value = self.history[color_index][from_sq][to_sq]
        self.current_max = max(self.current_max, new_value)
        self.stats.max_history_value = self.current_max
        
        # Check if aging is needed
        if self.current_max > self.aging_threshold:
            self._age_history()
    
    def get_history_score(self, move: chess.Move, color: bool) -> int:
        """
        Get history score for a move.
        
        Args:
            move: Move to evaluate
            color: True for white, False for black
            
        Returns:
            History score (higher = better)
        """
        from_sq = move.from_square
        to_sq = move.to_square
        color_index = 1 if color else 0
        
        self.stats.total_lookups += 1
        
        score = self.history[color_index][from_sq][to_sq]
        
        if score > self.min_significant_value:
            self.stats.successful_lookups += 1
            self.stats.history_hits += 1
        
        return score
    
    def get_normalized_score(self, move: chess.Move, color: bool) -> int:
        """
        Get normalized history score (0-1000 range).
        
        Args:
            move: Move to evaluate
            color: True for white, False for black
            
        Returns:
            Normalized score for move ordering
        """
        raw_score = self.get_history_score(move, color)
        
        if self.current_max == 0:
            return 0
        
        # Normalize to 0-1000 range for move ordering
        normalized = int((raw_score / self.current_max) * 1000)
        return min(normalized, 1000)
    
    def get_move_priority(self, move: chess.Move, color: bool) -> int:
        """
        Get priority value for move ordering.
        
        Args:
            move: Move to evaluate
            color: True for white, False for black
            
        Returns:
            Priority value for move ordering (6000-6999 range)
        """
        normalized = self.get_normalized_score(move, color)
        
        # History moves get priority in 6000-6999 range
        # (below killers 7000+, above quiet moves 0-5999)
        if normalized > 0:
            return 6000 + min(normalized, 999)
        
        return 0
    
    def _age_history(self):
        """Age all history values by dividing by aging factor."""
        self.stats.aging_cycles += 1
        
        new_max = 0
        for color in range(2):
            for from_sq in range(64):
                for to_sq in range(64):
                    self.history[color][from_sq][to_sq] //= self.aging_factor
                    new_max = max(new_max, self.history[color][from_sq][to_sq])
        
        self.current_max = new_max
        self.stats.max_history_value = new_max
    
    def clear(self):
        """Clear all history data."""
        for color in range(2):
            for from_sq in range(64):
                for to_sq in range(64):
                    self.history[color][from_sq][to_sq] = 0
        
        self.current_max = 0
        self.stats.reset()
    
    def get_best_moves(self, color: bool, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the best moves by history score for analysis.
        
        Args:
            color: True for white, False for black
            limit: Maximum number of moves to return
            
        Returns:
            List of (move_string, score) tuples
        """
        color_index = 1 if color else 0
        moves = []
        
        for from_sq in range(64):
            for to_sq in range(64):
                score = self.history[color_index][from_sq][to_sq]
                if score > self.min_significant_value:
                    from_name = chess.square_name(from_sq)
                    to_name = chess.square_name(to_sq)
                    move_str = f"{from_name}{to_name}"
                    moves.append((move_str, score))
        
        # Sort by score and return top moves
        moves.sort(key=lambda x: x[1], reverse=True)
        return moves[:limit]
    
    def get_statistics(self) -> Dict[str, float]:
        """Get history heuristic statistics."""
        return {
            'history_moves_recorded': self.stats.history_moves_recorded,
            'history_moves_applied': self.stats.history_moves_applied,
            'history_hits': self.stats.history_hits,
            'beta_cutoffs_from_history': self.stats.beta_cutoffs_from_history,
            'aging_cycles': self.stats.aging_cycles,
            'max_history_value': self.stats.max_history_value,
            'current_max_value': self.current_max,
            'total_lookups': self.stats.total_lookups,
            'successful_lookups': self.stats.successful_lookups,
            'hit_rate': self.stats.get_hit_rate(),
            'effectiveness': self.stats.get_effectiveness(),
            'aging_threshold': self.aging_threshold,
            'min_significant_value': self.min_significant_value
        }
    
    def configure(self, max_history_value: int = 16384, aging_threshold: int = 32768, 
                 aging_factor: int = 2, min_significant_value: int = 4):
        """
        Configure history heuristic parameters.
        
        Args:
            max_history_value: Target maximum value before aging
            aging_threshold: Value that triggers aging
            aging_factor: Factor to divide by during aging
            min_significant_value: Minimum value to be considered significant
        """
        self.max_history_value = max_history_value
        self.aging_threshold = aging_threshold
        self.aging_factor = aging_factor
        self.min_significant_value = min_significant_value


def classify_move_by_history(move: chess.Move, history_table: HistoryTable, 
                           color: bool) -> str:
    """
    Classify a move based on its history score.
    
    Args:
        move: Move to classify
        history_table: History table to query
        color: Player color
        
    Returns:
        Classification string ('excellent', 'good', 'average', 'poor', 'unknown')
    """
    score = history_table.get_normalized_score(move, color)
    
    if score >= 800:
        return 'excellent'
    elif score >= 600:
        return 'good'
    elif score >= 300:
        return 'average'
    elif score >= 100:
        return 'poor'
    else:
        return 'unknown'


def get_counter_move_signature(last_move: Optional[chess.Move]) -> Optional[Tuple[int, int]]:
    """
    Get signature for counter move tracking.
    
    Args:
        last_move: Opponent's last move
        
    Returns:
        Tuple of (from_square, to_square) or None
    """
    if last_move is None:
        return None
    
    return (last_move.from_square, last_move.to_square)
