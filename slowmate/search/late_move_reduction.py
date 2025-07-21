"""
Late Move Reduction (LMR) for SlowMate v0.2.01 Phase 4
Reduces search depth for moves ordered later in the move list.

Late Move Reduction is based on the observation that moves ordered later
are less likely to be best. We search them at reduced depth, and if they
exceed expectations (cause an alpha improvement), we re-search at full depth.

Architecture: Conservative, tournament-tested approach with configurable parameters.
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class LMRStats:
    """Statistics for Late Move Reduction effectiveness."""
    
    reductions_attempted: int = 0
    reductions_applied: int = 0
    re_searches_triggered: int = 0
    re_searches_improved: int = 0
    nodes_saved: int = 0
    
    # Performance tracking
    total_move_searches: int = 0
    full_depth_searches: int = 0
    
    def get_reduction_rate(self) -> float:
        """Get percentage of moves that were reduced."""
        if self.total_move_searches == 0:
            return 0.0
        return (self.reductions_applied / self.total_move_searches) * 100.0
    
    def get_re_search_rate(self) -> float:
        """Get percentage of reductions that triggered re-search."""
        if self.reductions_applied == 0:
            return 0.0
        return (self.re_searches_triggered / self.reductions_applied) * 100.0
    
    def get_re_search_success_rate(self) -> float:
        """Get percentage of re-searches that improved alpha."""
        if self.re_searches_triggered == 0:
            return 0.0
        return (self.re_searches_improved / self.re_searches_triggered) * 100.0
    
    def get_efficiency(self) -> float:
        """Get efficiency as nodes saved per reduction."""
        if self.reductions_applied == 0:
            return 0.0
        return self.nodes_saved / self.reductions_applied
    
    def reset(self):
        """Reset all statistics."""
        self.reductions_attempted = 0
        self.reductions_applied = 0
        self.re_searches_triggered = 0
        self.re_searches_improved = 0
        self.nodes_saved = 0
        self.total_move_searches = 0
        self.full_depth_searches = 0


class LateMoveReduction:
    """
    Late Move Reduction implementation.
    
    Reduces search depth for moves that appear later in the move ordering,
    based on the assumption that well-ordered moves place the best moves first.
    """
    
    def __init__(self):
        """Initialize LMR with conservative parameters."""
        
        # LMR Configuration
        self.min_depth = 3           # Minimum depth to apply LMR
        self.min_move_number = 4     # Start LMR after this many moves
        self.max_reduction = 3       # Maximum depth reduction
        self.pv_reduction_limit = 1  # Reduced reduction in PV nodes
        
        # Conditions where LMR is not applied
        self.no_lmr_in_check = True        # Don't reduce when in check
        self.no_lmr_captures = True        # Don't reduce captures
        self.no_lmr_promotions = True      # Don't reduce promotions
        self.no_lmr_killers = True         # Don't reduce killer moves
        self.no_lmr_hash_moves = True      # Don't reduce hash moves
        
        # Adaptive parameters
        self.history_reduction_bonus = True  # Reduce less for good history moves
        self.fail_high_reduction = True     # Reduce more after fail-highs
        
        # Statistics
        self.stats = LMRStats()
        
        # Current search state
        self.search_depth = 0
        self.current_move_count = 0
        self.fail_high_count = 0
    
    def should_reduce(self, move: chess.Move, board: chess.Board, depth: int, 
                     move_number: int, is_pv_node: bool = False,
                     is_killer: bool = False, is_hash_move: bool = False,
                     history_score: int = 0) -> bool:
        """
        Determine if a move should be searched with reduced depth.
        
        Args:
            move: Move to evaluate
            board: Current board position
            depth: Current search depth
            move_number: Move's position in the ordered list (1-based)
            is_pv_node: Whether this is a PV (principal variation) node
            is_killer: Whether this is a killer move
            is_hash_move: Whether this is a hash move
            history_score: History heuristic score for this move
            
        Returns:
            True if move should be reduced
        """
        self.stats.total_move_searches += 1
        
        # Basic requirements for LMR
        if depth < self.min_depth:
            return False
        
        if move_number < self.min_move_number:
            return False
        
        # Never reduce in check
        if self.no_lmr_in_check and board.is_check():
            return False
        
        # Never reduce important move types
        if self.no_lmr_captures and board.is_capture(move):
            return False
        
        if self.no_lmr_promotions and move.promotion is not None:
            return False
        
        if self.no_lmr_killers and is_killer:
            return False
        
        if self.no_lmr_hash_moves and is_hash_move:
            return False
        
        # Don't reduce moves with very good history scores
        if self.history_reduction_bonus and history_score > 800:
            return False
        
        self.stats.reductions_attempted += 1
        return True
    
    def calculate_reduction(self, depth: int, move_number: int, 
                          is_pv_node: bool = False, history_score: int = 0,
                          expected_node_type: str = "cut") -> int:
        """
        Calculate depth reduction for a move.
        
        Args:
            depth: Current search depth
            move_number: Move's position in ordered list
            is_pv_node: Whether this is a PV node
            history_score: History score for move
            expected_node_type: Expected node type (cut/all/pv)
            
        Returns:
            Depth reduction (1-3)
        """
        # Base reduction using logarithmic formula
        # This is a common approach in modern engines
        base_reduction = int(math.log(depth) * math.log(move_number) / 3.0)
        base_reduction = max(1, min(base_reduction, self.max_reduction))
        
        # Reduce reduction in PV nodes
        if is_pv_node:
            base_reduction = min(base_reduction, self.pv_reduction_limit)
        
        # Adjust based on history score
        if self.history_reduction_bonus:
            if history_score > 400:
                base_reduction = max(1, base_reduction - 1)
            elif history_score < 100:
                base_reduction = min(self.max_reduction, base_reduction + 1)
        
        # Increase reduction after fail-highs (moves are less likely to be good)
        if self.fail_high_reduction and self.fail_high_count > 2:
            base_reduction = min(self.max_reduction, base_reduction + 1)
        
        # Ensure minimum reduction of 1
        return max(1, base_reduction)
    
    def apply_reduction(self, original_depth: int, reduction: int) -> int:
        """
        Apply reduction to depth, ensuring minimum depth.
        
        Args:
            original_depth: Original search depth
            reduction: Reduction amount
            
        Returns:
            Reduced depth (at least 1)
        """
        reduced_depth = max(1, original_depth - reduction)
        
        if reduced_depth < original_depth:
            self.stats.reductions_applied += 1
            # Estimate nodes saved (very rough approximation)
            branching_factor = 35  # Average chess branching factor
            nodes_saved = pow(branching_factor, reduction) - pow(branching_factor, 0)
            self.stats.nodes_saved += int(nodes_saved)
        else:
            self.stats.full_depth_searches += 1
        
        return reduced_depth
    
    def should_re_search(self, score: int, alpha: int, beta: int, 
                        was_reduced: bool, original_depth: int, 
                        reduced_depth: int) -> bool:
        """
        Determine if a reduced move should be re-searched at full depth.
        
        Args:
            score: Score returned from reduced search
            alpha: Current alpha value
            beta: Current beta value
            was_reduced: Whether the move was actually reduced
            original_depth: Original search depth
            reduced_depth: Depth used for reduced search
            
        Returns:
            True if re-search is needed
        """
        if not was_reduced:
            return False
        
        # Re-search if the reduced search improved alpha
        # (indicating the move might be better than expected)
        if score > alpha:
            self.stats.re_searches_triggered += 1
            return True
        
        return False
    
    def record_re_search_result(self, score: int, alpha: int, improved_alpha: bool):
        """
        Record the result of a re-search.
        
        Args:
            score: Score from re-search
            alpha: Alpha value before re-search
            improved_alpha: Whether re-search improved alpha further
        """
        if improved_alpha:
            self.stats.re_searches_improved += 1
    
    def start_new_search(self, depth: int):
        """Start a new search at the given depth."""
        self.search_depth = depth
        self.current_move_count = 0
        self.fail_high_count = 0
    
    def record_fail_high(self):
        """Record that a fail-high occurred (beta cutoff)."""
        self.fail_high_count += 1
    
    def reset_fail_highs(self):
        """Reset fail-high count (e.g., when entering new node)."""
        self.fail_high_count = 0
    
    def get_statistics(self) -> Dict[str, float]:
        """Get LMR statistics."""
        return {
            'reductions_attempted': self.stats.reductions_attempted,
            'reductions_applied': self.stats.reductions_applied,
            're_searches_triggered': self.stats.re_searches_triggered,
            're_searches_improved': self.stats.re_searches_improved,
            'nodes_saved': self.stats.nodes_saved,
            'total_move_searches': self.stats.total_move_searches,
            'full_depth_searches': self.stats.full_depth_searches,
            'reduction_rate': self.stats.get_reduction_rate(),
            're_search_rate': self.stats.get_re_search_rate(),
            're_search_success_rate': self.stats.get_re_search_success_rate(),
            'efficiency': self.stats.get_efficiency(),
            'min_depth': self.min_depth,
            'min_move_number': self.min_move_number,
            'max_reduction': self.max_reduction
        }
    
    def configure(self, min_depth: int = 3, min_move_number: int = 4,
                 max_reduction: int = 3, pv_reduction_limit: int = 1):
        """
        Configure LMR parameters.
        
        Args:
            min_depth: Minimum depth to apply LMR
            min_move_number: Start LMR after this many moves
            max_reduction: Maximum depth reduction
            pv_reduction_limit: Maximum reduction in PV nodes
        """
        self.min_depth = min_depth
        self.min_move_number = min_move_number
        self.max_reduction = max_reduction
        self.pv_reduction_limit = pv_reduction_limit
    
    def configure_conditions(self, no_lmr_in_check: bool = True,
                           no_lmr_captures: bool = True,
                           no_lmr_promotions: bool = True,
                           no_lmr_killers: bool = True,
                           no_lmr_hash_moves: bool = True):
        """
        Configure conditions where LMR is not applied.
        
        Args:
            no_lmr_in_check: Don't reduce when in check
            no_lmr_captures: Don't reduce captures
            no_lmr_promotions: Don't reduce promotions
            no_lmr_killers: Don't reduce killer moves
            no_lmr_hash_moves: Don't reduce hash moves
        """
        self.no_lmr_in_check = no_lmr_in_check
        self.no_lmr_captures = no_lmr_captures
        self.no_lmr_promotions = no_lmr_promotions
        self.no_lmr_killers = no_lmr_killers
        self.no_lmr_hash_moves = no_lmr_hash_moves


def get_lmr_move_classification(move: chess.Move, board: chess.Board,
                              move_number: int, is_killer: bool = False,
                              is_hash_move: bool = False, 
                              history_score: int = 0) -> str:
    """
    Classify a move for LMR purposes.
    
    Args:
        move: Move to classify
        board: Current board position
        move_number: Position in move ordering
        is_killer: Whether this is a killer move
        is_hash_move: Whether this is a hash move
        history_score: History score
        
    Returns:
        Classification string
    """
    if is_hash_move:
        return "hash_move"
    elif is_killer:
        return "killer_move"
    elif board.is_capture(move):
        return "capture"
    elif move.promotion is not None:
        return "promotion"
    elif history_score > 600:
        return "good_history"
    elif history_score > 200:
        return "average_history"
    elif move_number <= 4:
        return "early_move"
    else:
        return "late_quiet"
