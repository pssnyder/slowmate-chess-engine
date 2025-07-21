"""
SlowMate Chess Engine - Modern Search Module

This module implements a high-performance, modular search system with:
- Advanced move ordering (SEE-based, MVV-LVA, killer moves, history heuristics)
- Transposition tables with hash moves
- Configurable search parameters via UCI
- Clean separation of concerns for easy extension

Architecture: Modern, accuracy-first approach optimized for tournament play.
"""

from typing import Optional, List, Dict, Any, Tuple
import chess
from dataclasses import dataclass, field
from enum import Enum


class MoveOrderingDebug(Enum):
    """Debug levels for move ordering - removed in production."""
    NONE = 0
    BASIC = 1
    DETAILED = 2


@dataclass
class SearchConfig:
    """Modern search configuration with UCI integration."""
    
    # Move ordering configuration
    enable_move_ordering: bool = True
    enable_see_evaluation: bool = True
    enable_mvv_lva: bool = True
    enable_killer_moves: bool = True
    enable_history_heuristic: bool = True
    enable_counter_moves: bool = True
    
    # Transposition table configuration
    enable_transposition_table: bool = True
    transposition_table_mb: int = 64
    enable_hash_moves: bool = True
    
    # SEE configuration
    see_max_depth: int = 10  # Until no more captures by default
    see_time_limit_ms: Optional[int] = None  # Time control override
    
    # Search depth and performance
    base_depth: int = 6
    max_depth: int = 12
    quiescence_depth: int = 8
    
    # Killer move configuration
    killer_move_slots: int = 2
    killer_max_age: int = 4
    enable_killer_aging: bool = True
    
    # History heuristic configuration
    history_aging_threshold: int = 32768
    history_aging_factor: int = 2
    history_min_significant: int = 4
    
    # Counter move configuration
    counter_min_confidence: int = 3
    counter_max_confidence: int = 100
    counter_decay_factor: float = 0.95
    enable_counter_aging: bool = True
    counter_age_frequency: int = 50
    
    # Memory configuration
    max_search_depth: int = 64  # For killer move table sizing
    
    # Knowledge base integration
    knowledge_base_priority: int = 100  # Lower than heuristics, higher than random
    
    # Debug configuration (removed in production)
    debug_move_ordering: MoveOrderingDebug = MoveOrderingDebug.NONE
    
    def to_uci_options(self) -> Dict[str, Any]:
        """Convert configuration to UCI option format."""
        return {
            'MoveOrdering': {'type': 'check', 'default': self.enable_move_ordering},
            'SEEEvaluation': {'type': 'check', 'default': self.enable_see_evaluation},
            'SEEMaxDepth': {'type': 'spin', 'default': self.see_max_depth, 'min': 1, 'max': 20},
            'TranspositionTable': {'type': 'check', 'default': self.enable_transposition_table},
            'TranspositionTableMB': {'type': 'spin', 'default': self.transposition_table_mb, 'min': 1, 'max': 1024},
            'HashMoves': {'type': 'check', 'default': self.enable_hash_moves},
            'KillerMoves': {'type': 'check', 'default': self.enable_killer_moves},
            'KillerMaxAge': {'type': 'spin', 'default': self.killer_max_age, 'min': 1, 'max': 10},
            'HistoryHeuristic': {'type': 'check', 'default': self.enable_history_heuristic},
            'HistoryAgingThreshold': {'type': 'spin', 'default': self.history_aging_threshold, 'min': 1000, 'max': 100000},
            'CounterMoves': {'type': 'check', 'default': self.enable_counter_moves},
            'CounterMinConfidence': {'type': 'spin', 'default': self.counter_min_confidence, 'min': 1, 'max': 10},
            'BaseDepth': {'type': 'spin', 'default': self.base_depth, 'min': 1, 'max': 20},
            'MaxDepth': {'type': 'spin', 'default': self.max_depth, 'min': 1, 'max': 30},
        }


@dataclass 
class MoveOrderingStats:
    """Statistics for move ordering effectiveness."""
    
    moves_ordered: int = 0
    see_evaluations: int = 0
    killer_hits: int = 0
    history_hits: int = 0
    counter_hits: int = 0
    hash_hits: int = 0
    knowledge_base_hits: int = 0
    
    # Performance metrics
    ordering_time_ms: float = 0.0
    see_time_ms: float = 0.0
    
    # Heuristic effectiveness
    killer_cutoffs: int = 0
    history_cutoffs: int = 0
    counter_cutoffs: int = 0
    
    # Search efficiency
    beta_cutoffs_total: int = 0
    first_move_cutoffs: int = 0  # Cutoffs on first move (perfect ordering)
    
    # Effectiveness metrics
    first_move_cutoffs: int = 0
    total_cutoffs: int = 0
    
    def reset(self):
        """Reset statistics for new search."""
        self.__init__()
    
    @property
    def cutoff_rate(self) -> float:
        """Percentage of first-move beta cutoffs."""
        return (self.first_move_cutoffs / max(self.total_cutoffs, 1)) * 100
    
    @property
    def hash_hit_rate(self) -> float:
        """Percentage of positions found in transposition table."""
        return (self.hash_hits / max(self.moves_ordered, 1)) * 100


class MovePriority(Enum):
    """Move priority levels for ordering."""
    
    # Hash moves from transposition table
    HASH_MOVE = 10000
    
    # Captures (SEE-evaluated)
    WINNING_CAPTURE = 9000
    EQUAL_CAPTURE = 8000
    PROMOTION = 7500
    
    # Tactical moves
    CHECK = 7000
    KILLER_MOVE_1 = 6000
    KILLER_MOVE_2 = 5500
    COUNTER_MOVE = 5000
    
    # History and knowledge
    HISTORY_GOOD = 4000
    KNOWLEDGE_BASE = 100  # Low priority to avoid recursion
    
    # Quiet moves
    QUIET_MOVE = 0
    
    # Bad moves (searched last)
    LOSING_CAPTURE = -1000


@dataclass
class OrderedMove:
    """A move with its ordering priority and metadata."""
    
    move: chess.Move
    priority: int
    source: str  # For debugging and statistics
    see_score: Optional[int] = None
    history_score: Optional[int] = None
    
    def __lt__(self, other: 'OrderedMove') -> bool:
        """Enable sorting by priority (highest first)."""
        return self.priority > other.priority
