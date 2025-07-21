"""
Killer Move Heuristic for SlowMate v0.2.01 Phase 3
Tracks moves that cause beta cutoffs for improved move ordering.

The killer move heuristic is based on the observation that moves which cause
beta cutoffs (refutations) at a given depth often work well at the same depth
in other positions. We store up to 2 killer moves per ply.

Architecture: Modern, tournament-tested approach optimized for accuracy.
"""

import chess
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class KillerMoveStats:
    """Statistics for killer move effectiveness."""
    
    killer_moves_stored: int = 0
    killer_moves_tried: int = 0
    killer_moves_hit: int = 0
    beta_cutoffs_from_killers: int = 0
    
    # Performance metrics
    total_lookups: int = 0
    successful_lookups: int = 0
    
    def get_hit_rate(self) -> float:
        """Get killer move hit rate."""
        if self.total_lookups == 0:
            return 0.0
        return (self.successful_lookups / self.total_lookups) * 100.0
    
    def get_effectiveness(self) -> float:
        """Get killer move effectiveness (cutoffs per hit)."""
        if self.killer_moves_hit == 0:
            return 0.0
        return (self.beta_cutoffs_from_killers / self.killer_moves_hit) * 100.0
    
    def reset(self):
        """Reset all statistics."""
        self.killer_moves_stored = 0
        self.killer_moves_tried = 0
        self.killer_moves_hit = 0
        self.beta_cutoffs_from_killers = 0
        self.total_lookups = 0
        self.successful_lookups = 0


class KillerMoveTable:
    """
    Killer move table storing up to 2 killer moves per ply.
    
    The killer move heuristic works by storing moves that cause beta cutoffs
    at each depth level. These moves are given high priority in move ordering
    since they often work well at the same depth in similar positions.
    """
    
    def __init__(self, max_depth: int = 64):
        """
        Initialize killer move table.
        
        Args:
            max_depth: Maximum search depth to support
        """
        self.max_depth = max_depth
        
        # Two killer moves per ply - primary and secondary
        self.killers: List[List[Optional[chess.Move]]] = [
            [None, None] for _ in range(max_depth)
        ]
        
        # Track move frequency for aging
        self.killer_ages: List[List[int]] = [
            [0, 0] for _ in range(max_depth)
        ]
        
        # Current search age for aging killer moves
        self.current_age = 0
        
        # Statistics
        self.stats = KillerMoveStats()
        
        # Configuration
        self.max_age_threshold = 4  # Age out killers after 4 searches
        self.enable_aging = True
    
    def store_killer(self, move: chess.Move, ply: int):
        """
        Store a killer move at the given ply.
        
        Args:
            move: The move that caused a beta cutoff
            ply: The search ply (depth from root)
        """
        if ply >= self.max_depth:
            return
        
        # Don't store captures as killers (they're handled by SEE/MVV-LVA)
        # This is a design choice - some engines include captures
        if move is None:
            return
        
        killers = self.killers[ply]
        ages = self.killer_ages[ply]
        
        # If this move is already the primary killer, don't duplicate
        if killers[0] == move:
            ages[0] = self.current_age
            return
        
        # If this move is the secondary killer, promote it to primary
        if killers[1] == move:
            # Swap primary and secondary
            killers[0], killers[1] = killers[1], killers[0]
            ages[0], ages[1] = ages[1], ages[0]
            ages[0] = self.current_age
            return
        
        # Store as new killer - shift existing killers down
        killers[1] = killers[0]
        killers[0] = move
        ages[1] = ages[0]
        ages[0] = self.current_age
        
        self.stats.killer_moves_stored += 1
    
    def get_killers(self, ply: int) -> List[chess.Move]:
        """
        Get killer moves for the given ply.
        
        Args:
            ply: The search ply
            
        Returns:
            List of killer moves (0-2 moves)
        """
        if ply >= self.max_depth:
            return []
        
        self.stats.total_lookups += 1
        
        killers = []
        killer_moves = self.killers[ply]
        ages = self.killer_ages[ply]
        
        for i, (killer, age) in enumerate(zip(killer_moves, ages)):
            if killer is None:
                continue
            
            # Check if killer is too old
            if self.enable_aging and (self.current_age - age) > self.max_age_threshold:
                # Age out old killer
                self.killers[ply][i] = None
                self.killer_ages[ply][i] = 0
                continue
            
            killers.append(killer)
        
        if killers:
            self.stats.successful_lookups += 1
        
        return killers
    
    def is_killer(self, move: chess.Move, ply: int) -> bool:
        """
        Check if a move is a killer at the given ply.
        
        Args:
            move: Move to check
            ply: Search ply
            
        Returns:
            True if the move is a killer move
        """
        if ply >= self.max_depth:
            return False
        
        killers = self.killers[ply]
        return move == killers[0] or move == killers[1]
    
    def record_killer_try(self, move: chess.Move, ply: int):
        """
        Record that a killer move was tried.
        
        Args:
            move: The killer move that was tried
            ply: Search ply
        """
        if self.is_killer(move, ply):
            self.stats.killer_moves_tried += 1
    
    def record_killer_hit(self, move: chess.Move, ply: int, caused_cutoff: bool = False):
        """
        Record that a killer move was successful.
        
        Args:
            move: The killer move that was successful
            ply: Search ply
            caused_cutoff: Whether this killer caused a beta cutoff
        """
        if self.is_killer(move, ply):
            self.stats.killer_moves_hit += 1
            if caused_cutoff:
                self.stats.beta_cutoffs_from_killers += 1
    
    def new_search(self):
        """Start a new search - increment age for killer move management."""
        self.current_age += 1
        
        # Prevent overflow - reset ages if we get too high
        if self.current_age > 1000:
            self.current_age = 0
            for ply in range(self.max_depth):
                self.killer_ages[ply] = [0, 0]
    
    def clear(self):
        """Clear all killer moves."""
        for ply in range(self.max_depth):
            self.killers[ply] = [None, None]
            self.killer_ages[ply] = [0, 0]
        self.current_age = 0
        self.stats.reset()
    
    def get_statistics(self) -> Dict[str, float]:
        """Get killer move statistics."""
        return {
            'killer_moves_stored': self.stats.killer_moves_stored,
            'killer_moves_tried': self.stats.killer_moves_tried,
            'killer_moves_hit': self.stats.killer_moves_hit,
            'beta_cutoffs_from_killers': self.stats.beta_cutoffs_from_killers,
            'total_lookups': self.stats.total_lookups,
            'successful_lookups': self.stats.successful_lookups,
            'hit_rate': self.stats.get_hit_rate(),
            'effectiveness': self.stats.get_effectiveness(),
            'current_age': self.current_age,
            'max_depth': self.max_depth
        }
    
    def configure(self, max_age_threshold: int = 4, enable_aging: bool = True):
        """
        Configure killer move behavior.
        
        Args:
            max_age_threshold: Maximum age before killers are discarded
            enable_aging: Whether to age out old killer moves
        """
        self.max_age_threshold = max_age_threshold
        self.enable_aging = enable_aging


def filter_legal_killers(killers: List[chess.Move], board: chess.Board) -> List[chess.Move]:
    """
    Filter killer moves to only include legal moves in the current position.
    
    Args:
        killers: List of potential killer moves
        board: Current board position
        
    Returns:
        List of legal killer moves
    """
    legal_moves = set(board.legal_moves)
    return [killer for killer in killers if killer in legal_moves]


def get_killer_priority(move: chess.Move, killers: List[chess.Move]) -> int:
    """
    Get priority value for a killer move.
    
    Args:
        move: Move to check
        killers: List of killer moves (ordered by preference)
        
    Returns:
        Priority value (higher = better), 0 if not a killer
    """
    if not killers:
        return 0
    
    try:
        # Primary killer gets higher priority than secondary
        index = killers.index(move)
        return 7000 - (index * 100)  # 7000 for primary, 6900 for secondary
    except ValueError:
        return 0
