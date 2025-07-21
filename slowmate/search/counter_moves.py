"""
Counter Move Heuristic for SlowMate v0.2.01 Phase 3
Tracks effective responses to opponent moves for context-aware move ordering.

The counter move heuristic stores the best response to each opponent move.
When the opponent plays a move, we prioritize the stored counter move in
our move ordering. This helps with tactical refutations and positional responses.

Architecture: Context-aware move suggestions with aging for tournament optimization.
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CounterMoveStats:
    """Statistics for counter move effectiveness."""
    
    counter_moves_stored: int = 0
    counter_moves_tried: int = 0
    counter_moves_hit: int = 0
    beta_cutoffs_from_counters: int = 0
    
    # Context tracking
    total_lookups: int = 0
    successful_lookups: int = 0
    context_matches: int = 0
    
    def get_hit_rate(self) -> float:
        """Get counter move hit rate."""
        if self.total_lookups == 0:
            return 0.0
        return (self.successful_lookups / self.total_lookups) * 100.0
    
    def get_effectiveness(self) -> float:
        """Get counter move effectiveness (cutoffs per hit)."""
        if self.counter_moves_hit == 0:
            return 0.0
        return (self.beta_cutoffs_from_counters / self.counter_moves_hit) * 100.0
    
    def get_context_rate(self) -> float:
        """Get context match rate."""
        if self.total_lookups == 0:
            return 0.0
        return (self.context_matches / self.total_lookups) * 100.0
    
    def reset(self):
        """Reset all statistics."""
        self.counter_moves_stored = 0
        self.counter_moves_tried = 0
        self.counter_moves_hit = 0
        self.beta_cutoffs_from_counters = 0
        self.total_lookups = 0
        self.successful_lookups = 0
        self.context_matches = 0


class CounterMoveTable:
    """
    Counter move table for storing best responses to opponent moves.
    
    Stores the best response to each possible move the opponent can make.
    The table is indexed by (from_square, to_square) of the opponent's move,
    and stores our best counter move along with confidence/success metrics.
    """
    
    def __init__(self):
        """Initialize counter move table."""
        
        # Counter moves: [from_square][to_square] -> (counter_move, confidence)
        self.counters: List[List[Optional[Tuple[chess.Move, int]]]] = [
            [None for _ in range(64)] for _ in range(64)
        ]
        
        # Track move success for confidence building
        self.success_counts: List[List[int]] = [
            [0 for _ in range(64)] for _ in range(64)
        ]
        
        # Track total attempts for each opponent move
        self.attempt_counts: List[List[int]] = [
            [0 for _ in range(64)] for _ in range(64)
        ]
        
        # Statistics
        self.stats = CounterMoveStats()
        
        # Configuration
        self.min_confidence = 3      # Minimum attempts before storing
        self.max_confidence = 100    # Maximum confidence value
        self.decay_factor = 0.95     # Confidence decay for aging
        self.enable_aging = True
        
        # Age tracking
        self.search_count = 0
        self.age_frequency = 50      # Age every N searches
    
    def store_counter(self, opponent_move: chess.Move, counter_move: chess.Move, 
                     success: bool = True):
        """
        Store or update a counter move.
        
        Args:
            opponent_move: The opponent's move
            counter_move: Our response move
            success: Whether this counter was successful (caused cutoff/good result)
        """
        from_sq = opponent_move.from_square
        to_sq = opponent_move.to_square
        
        # Update attempt count
        self.attempt_counts[from_sq][to_sq] += 1
        
        # Update success count if successful
        if success:
            self.success_counts[from_sq][to_sq] += 1
        
        # Calculate confidence (success rate)
        attempts = self.attempt_counts[from_sq][to_sq]
        successes = self.success_counts[from_sq][to_sq]
        
        if attempts < self.min_confidence:
            return  # Not enough data yet
        
        confidence = min(int((successes / attempts) * 100), self.max_confidence)
        
        # Store the counter move
        current = self.counters[from_sq][to_sq]
        
        if current is None or current[0] != counter_move:
            # New counter move or different move
            self.counters[from_sq][to_sq] = (counter_move, confidence)
            self.stats.counter_moves_stored += 1
        else:
            # Update confidence for existing counter move
            old_confidence = current[1]
            new_confidence = (old_confidence + confidence) // 2  # Average with existing
            self.counters[from_sq][to_sq] = (counter_move, new_confidence)
    
    def get_counter(self, opponent_move: chess.Move) -> Optional[Tuple[chess.Move, int]]:
        """
        Get counter move for opponent's move.
        
        Args:
            opponent_move: The opponent's move
            
        Returns:
            Tuple of (counter_move, confidence) or None
        """
        from_sq = opponent_move.from_square
        to_sq = opponent_move.to_square
        
        self.stats.total_lookups += 1
        
        counter = self.counters[from_sq][to_sq]
        
        if counter is not None:
            self.stats.successful_lookups += 1
            self.stats.context_matches += 1
            return counter
        
        return None
    
    def is_counter_move(self, move: chess.Move, opponent_move: chess.Move) -> bool:
        """
        Check if a move is a stored counter to the opponent's move.
        
        Args:
            move: Our move to check
            opponent_move: Opponent's move
            
        Returns:
            True if move is a stored counter
        """
        counter = self.get_counter(opponent_move)
        return counter is not None and counter[0] == move
    
    def record_counter_try(self, move: chess.Move, opponent_move: chess.Move):
        """
        Record that a counter move was tried.
        
        Args:
            move: Counter move that was tried
            opponent_move: Opponent's move being countered
        """
        if self.is_counter_move(move, opponent_move):
            self.stats.counter_moves_tried += 1
    
    def record_counter_success(self, move: chess.Move, opponent_move: chess.Move, 
                              caused_cutoff: bool = False):
        """
        Record that a counter move was successful.
        
        Args:
            move: Counter move that succeeded
            opponent_move: Opponent's move that was countered
            caused_cutoff: Whether this counter caused a beta cutoff
        """
        if self.is_counter_move(move, opponent_move):
            self.stats.counter_moves_hit += 1
            if caused_cutoff:
                self.stats.beta_cutoffs_from_counters += 1
    
    def get_counter_priority(self, move: chess.Move, opponent_move: Optional[chess.Move]) -> int:
        """
        Get priority value for a counter move.
        
        Args:
            move: Move to evaluate
            opponent_move: Opponent's last move
            
        Returns:
            Priority value (higher = better), 0 if not a counter
        """
        if opponent_move is None:
            return 0
        
        counter = self.get_counter(opponent_move)
        if counter is None or counter[0] != move:
            return 0
        
        confidence = counter[1]
        
        # Counter moves get priority in 6500-6999 range
        # (below killers 7000+, above regular history 6000-6499)
        base_priority = 6500
        confidence_bonus = min(confidence * 4, 499)  # Up to 499 bonus
        
        return base_priority + confidence_bonus
    
    def new_search(self):
        """Start new search - handle aging if needed."""
        self.search_count += 1
        
        if self.enable_aging and (self.search_count % self.age_frequency == 0):
            self._age_counters()
    
    def _age_counters(self):
        """Age counter move confidences."""
        for from_sq in range(64):
            for to_sq in range(64):
                counter = self.counters[from_sq][to_sq]
                if counter is not None:
                    move, confidence = counter
                    new_confidence = int(confidence * self.decay_factor)
                    
                    if new_confidence < self.min_confidence:
                        # Remove low-confidence counters
                        self.counters[from_sq][to_sq] = None
                        self.success_counts[from_sq][to_sq] = 0
                        self.attempt_counts[from_sq][to_sq] = 0
                    else:
                        self.counters[from_sq][to_sq] = (move, new_confidence)
    
    def clear(self):
        """Clear all counter moves."""
        for from_sq in range(64):
            for to_sq in range(64):
                self.counters[from_sq][to_sq] = None
                self.success_counts[from_sq][to_sq] = 0
                self.attempt_counts[from_sq][to_sq] = 0
        
        self.search_count = 0
        self.stats.reset()
    
    def get_top_counters(self, limit: int = 10) -> List[Tuple[str, str, int]]:
        """
        Get top counter moves by confidence.
        
        Args:
            limit: Maximum number of counters to return
            
        Returns:
            List of (opponent_move, counter_move, confidence) tuples
        """
        counters = []
        
        for from_sq in range(64):
            for to_sq in range(64):
                counter = self.counters[from_sq][to_sq]
                if counter is not None:
                    move, confidence = counter
                    opp_move = chess.square_name(from_sq) + chess.square_name(to_sq)
                    counter_str = str(move)
                    counters.append((opp_move, counter_str, confidence))
        
        # Sort by confidence and return top counters
        counters.sort(key=lambda x: x[2], reverse=True)
        return counters[:limit]
    
    def get_statistics(self) -> Dict[str, float]:
        """Get counter move statistics."""
        return {
            'counter_moves_stored': self.stats.counter_moves_stored,
            'counter_moves_tried': self.stats.counter_moves_tried,
            'counter_moves_hit': self.stats.counter_moves_hit,
            'beta_cutoffs_from_counters': self.stats.beta_cutoffs_from_counters,
            'total_lookups': self.stats.total_lookups,
            'successful_lookups': self.stats.successful_lookups,
            'context_matches': self.stats.context_matches,
            'hit_rate': self.stats.get_hit_rate(),
            'effectiveness': self.stats.get_effectiveness(),
            'context_rate': self.stats.get_context_rate(),
            'search_count': self.search_count,
            'min_confidence': self.min_confidence,
            'max_confidence': self.max_confidence
        }
    
    def configure(self, min_confidence: int = 3, max_confidence: int = 100,
                 decay_factor: float = 0.95, enable_aging: bool = True,
                 age_frequency: int = 50):
        """
        Configure counter move parameters.
        
        Args:
            min_confidence: Minimum attempts before storing counters
            max_confidence: Maximum confidence value
            decay_factor: Confidence decay factor for aging
            enable_aging: Whether to age old counters
            age_frequency: How often to age (every N searches)
        """
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.decay_factor = decay_factor
        self.enable_aging = enable_aging
        self.age_frequency = age_frequency


def get_move_context(board: chess.Board, last_moves: List[chess.Move], 
                    depth: int = 2) -> str:
    """
    Get tactical context for counter move evaluation.
    
    Args:
        board: Current board position
        last_moves: Recent moves in the game
        depth: Number of recent moves to consider
        
    Returns:
        Context string for analysis
    """
    context_factors = []
    
    # Check if in check
    if board.is_check():
        context_factors.append("check")
    
    # Check recent captures
    recent_moves = last_moves[-depth:] if len(last_moves) >= depth else last_moves
    captures = sum(1 for move in recent_moves if board.is_capture(move))
    
    if captures > 0:
        context_factors.append(f"captures:{captures}")
    
    # Check piece development/centralization in recent moves
    central_squares = {chess.E4, chess.E5, chess.D4, chess.D5}
    central_moves = sum(1 for move in recent_moves if move.to_square in central_squares)
    
    if central_moves > 0:
        context_factors.append("central")
    
    return "_".join(context_factors) if context_factors else "normal"
