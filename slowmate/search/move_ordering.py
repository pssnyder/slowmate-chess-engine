"""
Core Move Ordering System for SlowMate Chess Engine

This module implements the central move ordering logic that combines:
- Enhanced SEE evaluation for captures
- MVV-LVA fallback for fast capture ordering  
- Killer moves and history heuristics (future)
- Knowledge base integration
- UCI-configurable parameters

Architecture: Modular, accuracy-first system designed for easy extension.
"""

import time
from typing import List, Optional, Dict, Tuple
import chess

from slowmate.search import SearchConfig, MoveOrderingStats, MovePriority, OrderedMove, MoveOrderingDebug
from slowmate.search.enhanced_see import EnhancedSEE
from slowmate.search.mvv_lva import MVVLVA
from slowmate.search.transposition_table import TranspositionTable
from slowmate.search.killer_moves import KillerMoveTable
from slowmate.search.history_heuristic import HistoryTable
from slowmate.search.counter_moves import CounterMoveTable


class MoveOrderingEngine:
    """Core move ordering engine with modular heuristics."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.stats = MoveOrderingStats()
        
        # Initialize move ordering components
        self.see_evaluator = EnhancedSEE(config) if config.enable_see_evaluation else None
        self.mvv_lva = MVVLVA() if config.enable_mvv_lva else None
        
        # Initialize transposition table
        self.transposition_table = None
        if config.enable_transposition_table:
            self.transposition_table = TranspositionTable(config.transposition_table_mb)
        
        # Initialize Phase 3 heuristics
        self.killer_moves = None
        if config.enable_killer_moves:
            self.killer_moves = KillerMoveTable(config.max_search_depth)
            self.killer_moves.configure(
                max_age_threshold=config.killer_max_age,
                enable_aging=config.enable_killer_aging
            )
        
        self.history_table = None
        if config.enable_history_heuristic:
            self.history_table = HistoryTable()
            self.history_table.configure(
                aging_threshold=config.history_aging_threshold,
                aging_factor=config.history_aging_factor,
                min_significant_value=config.history_min_significant
            )
        
        self.counter_moves = None
        if config.enable_counter_moves:
            self.counter_moves = CounterMoveTable()
            self.counter_moves.configure(
                min_confidence=config.counter_min_confidence,
                max_confidence=config.counter_max_confidence,
                decay_factor=config.counter_decay_factor,
                enable_aging=config.enable_counter_aging,
                age_frequency=config.counter_age_frequency
            )
        
    def reset_for_search(self):
        """Reset move ordering state for new search."""
        self.stats = MoveOrderingStats()
        if self.see_evaluator:
            self.see_evaluator.clear_cache()
        
        # Start new search for heuristics
        if self.killer_moves:
            self.killer_moves.new_search()
        if self.counter_moves:
            self.counter_moves.new_search()
    
    def clear_transposition_table(self):
        """Clear the transposition table."""
        if self.transposition_table:
            self.transposition_table.clear()
    
    def get_hash_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get hash move from transposition table."""
        if self.transposition_table and self.config.enable_hash_moves:
            return self.transposition_table.get_hash_move(board)
        return None
    
    def order_moves(self, board: chess.Board, moves: List[chess.Move], 
                   depth: int = 0, hash_move: Optional[chess.Move] = None,
                   last_move: Optional[chess.Move] = None) -> List[OrderedMove]:
        """
        Order moves for optimal search efficiency.
        
        Args:
            board: Current board position
            moves: Legal moves to order
            depth: Current search depth
            hash_move: Best move from transposition table
            last_move: Opponent's last move (for counter moves)
            
        Returns:
            Moves ordered by priority with metadata
        """
        start_time = time.time() * 1000
        ordered_moves = []
        
        # Debug output
        if self.config.debug_move_ordering == MoveOrderingDebug.DETAILED:
            print(f"Ordering {len(moves)} moves at depth {depth}")
        
        for move in moves:
            ordered_move = self._evaluate_move(board, move, depth, hash_move, last_move)
            ordered_moves.append(ordered_move)
        
        # Sort by priority (highest first)
        ordered_moves.sort()
        
        # Update statistics
        self.stats.moves_ordered += len(moves)
        self.stats.ordering_time_ms += (time.time() * 1000) - start_time
        
        # Debug output
        if self.config.debug_move_ordering == MoveOrderingDebug.BASIC:
            self._debug_move_ordering(ordered_moves[:5])  # Show top 5
        
        return ordered_moves
    
    def _evaluate_move(self, board: chess.Board, move: chess.Move, depth: int,
                      hash_move: Optional[chess.Move], last_move: Optional[chess.Move]) -> OrderedMove:
        """
        Evaluate a single move and assign priority.
        
        Args:
            board: Current board position
            move: Move to evaluate
            depth: Current search depth
            hash_move: Hash move from transposition table
            last_move: Opponent's last move
            
        Returns:
            OrderedMove with priority and metadata
        """
        # 1. Hash move (highest priority)
        if hash_move and move == hash_move:
            self.stats.hash_hits += 1
            return OrderedMove(
                move=move,
                priority=MovePriority.HASH_MOVE.value,
                source="hash_move"
            )
        
        # 2. Captures (SEE or MVV-LVA evaluated)
        if board.is_capture(move):
            return self._evaluate_capture(board, move)
        
        # 3. Promotions
        if move.promotion:
            priority = MovePriority.PROMOTION.value
            if move.promotion == chess.QUEEN:
                priority += 100  # Queen promotion gets highest
            return OrderedMove(
                move=move,
                priority=priority,
                source="promotion"
            )
        
        # 4. Checks
        if board.gives_check(move):
            return OrderedMove(
                move=move,
                priority=MovePriority.CHECK.value,
                source="check"
            )
        
        # 5. Killer moves (future implementation)
        killer_priority = self._evaluate_killer_move(move, depth)
        if killer_priority > 0:
            return OrderedMove(
                move=move,
                priority=killer_priority,
                source="killer_move"
            )
        
        # 6. Counter moves (future implementation)
        if last_move and self._is_counter_move(move, last_move):
            return OrderedMove(
                move=move,
                priority=MovePriority.COUNTER_MOVE.value,
                source="counter_move"
            )
        
        # 7. History heuristic
        history_score = self._get_history_score(move, board.turn)
        if history_score > 0:
            return OrderedMove(
                move=move,
                priority=MovePriority.HISTORY_GOOD.value + history_score,
                source="history",
                history_score=history_score
            )
        
        # 8. Knowledge base moves (lowest priority to avoid recursion)
        if self._is_knowledge_base_move(board, move):
            self.stats.knowledge_base_hits += 1
            return OrderedMove(
                move=move,
                priority=MovePriority.KNOWLEDGE_BASE.value,
                source="knowledge_base"
            )
        
        # 9. Quiet moves (default priority)
        return OrderedMove(
            move=move,
            priority=MovePriority.QUIET_MOVE.value,
            source="quiet"
        )
    
    def _evaluate_capture(self, board: chess.Board, move: chess.Move) -> OrderedMove:
        """
        Evaluate a capture move using SEE or MVV-LVA.
        
        Args:
            board: Current board position
            move: Capture move to evaluate
            
        Returns:
            OrderedMove with capture evaluation
        """
        see_score = None
        priority = MovePriority.EQUAL_CAPTURE.value  # Default
        source = "capture"
        
        # Try SEE evaluation first (if enabled and time permits)
        if self.see_evaluator and self.config.enable_see_evaluation:
            try:
                start_time = time.time() * 1000
                see_score = self.see_evaluator.evaluate_capture(board, move)
                self.stats.see_time_ms += (time.time() * 1000) - start_time
                self.stats.see_evaluations += 1
                
                # Classify based on SEE score
                if see_score > 0:
                    priority = MovePriority.WINNING_CAPTURE.value + min(see_score, 1000)
                    source = "winning_capture_see"
                elif see_score == 0:
                    priority = MovePriority.EQUAL_CAPTURE.value
                    source = "equal_capture_see"
                else:
                    priority = MovePriority.LOSING_CAPTURE.value
                    source = "losing_capture_see"
                    
            except Exception:
                # Fall back to MVV-LVA if SEE fails
                see_score = None
        
        # Fall back to MVV-LVA if SEE not available or failed
        if see_score is None and self.mvv_lva and self.config.enable_mvv_lva:
            mvv_lva_score = self.mvv_lva.get_capture_score(board, move)
            priority = MovePriority.EQUAL_CAPTURE.value + mvv_lva_score
            source = "capture_mvv_lva"
        
        return OrderedMove(
            move=move,
            priority=priority,
            source=source,
            see_score=see_score
        )
    
    def _evaluate_killer_move(self, move: chess.Move, depth: int) -> int:
        """
        Check if move is a killer move and return priority.
        
        Args:
            move: Move to check
            depth: Current search depth
            
        Returns:
            Priority value (0 if not a killer move)
        """
        if not self.config.enable_killer_moves or not self.killer_moves:
            return 0
        
        killers = self.killer_moves.get_killers(depth)
        if not killers:
            return 0
        
        if len(killers) > 0 and move == killers[0]:
            self.stats.killer_hits += 1
            return MovePriority.KILLER_MOVE_1.value
        elif len(killers) > 1 and move == killers[1]:
            self.stats.killer_hits += 1
            return MovePriority.KILLER_MOVE_2.value
            
        return 0
    
    def _is_counter_move(self, move: chess.Move, last_move: chess.Move) -> bool:
        """
        Check if move is a counter move to opponent's last move.
        
        Args:
            move: Move to check
            last_move: Opponent's last move
            
        Returns:
            True if this is a stored counter move
        """
        if not self.config.enable_counter_moves or not self.counter_moves:
            return False
            
        return self.counter_moves.is_counter_move(move, last_move)
    
    def _get_history_score(self, move: chess.Move, color: bool) -> int:
        """
        Get history heuristic score for a move.
        
        Args:
            move: Move to score
            color: Player color
            
        Returns:
            History score (0 if no history)
        """
        if not self.config.enable_history_heuristic or not self.history_table:
            return 0
            
        score = self.history_table.get_history_score(move, color)
        
        if score > 0:
            self.stats.history_hits += 1
            
        return min(score, 1000)  # Cap history score
    
    def _is_knowledge_base_move(self, board: chess.Board, move: chess.Move) -> bool:
        """
        Check if move comes from knowledge base (placeholder for now).
        
        Args:
            board: Current board position
            move: Move to check
            
        Returns:
            True if move is from knowledge base
        """
        # This will be implemented when we integrate with the existing knowledge base
        # For now, return False to avoid interference
        return False
    
    def store_killer_move(self, move: chess.Move, depth: int, board: chess.Board):
        """
        Store a killer move for the given depth.
        
        Args:
            move: Move that caused beta cutoff
            depth: Search depth where cutoff occurred
            board: Current board position (to check if capture)
        """
        if not self.config.enable_killer_moves or not self.killer_moves:
            return
        
        # Only store quiet moves as killers
        if board.is_capture(move):
            return
            
        self.killer_moves.store_killer(move, depth)
    
    def update_history(self, move: chess.Move, depth: int, color: bool, success: bool):
        """
        Update history heuristic for a move.
        
        Args:
            move: Move to update
            depth: Search depth
            color: Player color
            success: Whether move was successful (caused cutoff)
        """
        if not self.config.enable_history_heuristic or not self.history_table:
            return
            
        self.history_table.record_move(move, color, depth, success)
    
    def store_counter_move(self, opponent_move: chess.Move, counter_move: chess.Move, 
                          success: bool = True):
        """
        Store a counter move for opponent's move.
        
        Args:
            opponent_move: Opponent's move
            counter_move: Our best response
            success: Whether this counter was successful
        """
        if self.config.enable_counter_moves and self.counter_moves:
            self.counter_moves.store_counter(opponent_move, counter_move, success)
    
    def _debug_move_ordering(self, ordered_moves: List[OrderedMove]):
        """Debug output for move ordering (removed in production)."""
        print("Top moves by priority:")
        for i, ordered_move in enumerate(ordered_moves):
            print(f"  {i+1}. {ordered_move.move} ({ordered_move.priority}) - {ordered_move.source}")
    
    def get_statistics(self) -> MoveOrderingStats:
        """Get current move ordering statistics."""
        return self.stats
    
    def get_killer_statistics(self) -> Optional[Dict[str, float]]:
        """Get killer move statistics."""
        if self.killer_moves:
            return self.killer_moves.get_statistics()
        return None
    
    def get_history_statistics(self) -> Optional[Dict[str, float]]:
        """Get history heuristic statistics."""
        if self.history_table:
            return self.history_table.get_statistics()
        return None
    
    def get_counter_statistics(self) -> Optional[Dict[str, float]]:
        """Get counter move statistics."""
        if self.counter_moves:
            return self.counter_moves.get_statistics()
        return None
