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


class MoveOrderingEngine:
    """Core move ordering engine with modular heuristics."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.stats = MoveOrderingStats()
        
        # Initialize move ordering components
        self.see_evaluator = EnhancedSEE(config) if config.enable_see_evaluation else None
        self.mvv_lva = MVVLVA() if config.enable_mvv_lva else None
        
        # Future heuristics will be initialized here
        self.killer_moves: Dict[int, List[chess.Move]] = {}  # depth -> killer moves
        self.history_table: Dict[Tuple[int, int], int] = {}  # (from, to) -> success count
        self.counter_moves: Dict[chess.Move, chess.Move] = {}  # opponent_move -> counter
        
    def reset_for_search(self):
        """Reset move ordering state for new search."""
        self.stats.reset()
        if self.see_evaluator:
            self.see_evaluator.clear_cache()
    
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
        
        # 7. History heuristic (future implementation)
        history_score = self._get_history_score(move)
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
        if not self.config.enable_killer_moves or depth not in self.killer_moves:
            return 0
            
        killers = self.killer_moves[depth]
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
        if not self.config.enable_counter_moves:
            return False
            
        return self.counter_moves.get(last_move) == move
    
    def _get_history_score(self, move: chess.Move) -> int:
        """
        Get history heuristic score for a move.
        
        Args:
            move: Move to score
            
        Returns:
            History score (0 if no history)
        """
        if not self.config.enable_history_heuristic:
            return 0
            
        key = (move.from_square, move.to_square)
        score = self.history_table.get(key, 0)
        
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
        if not self.config.enable_killer_moves or board.is_capture(move):
            return  # Only store quiet moves as killers
            
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
            
        killers = self.killer_moves[depth]
        
        # Don't store duplicates
        if move in killers:
            return
            
        # Add to front, keep only configured number of slots
        killers.insert(0, move)
        if len(killers) > self.config.killer_move_slots:
            killers.pop()
    
    def update_history(self, move: chess.Move, depth: int, success: bool):
        """
        Update history heuristic for a move.
        
        Args:
            move: Move to update
            depth: Search depth
            success: Whether move was successful (caused cutoff)
        """
        if not self.config.enable_history_heuristic:
            return
            
        key = (move.from_square, move.to_square)
        current = self.history_table.get(key, 0)
        
        if success:
            # Increase history score, weighted by depth
            self.history_table[key] = current + depth * depth
        else:
            # Decrease history score slightly
            self.history_table[key] = max(0, current - 1)
    
    def store_counter_move(self, opponent_move: chess.Move, counter_move: chess.Move):
        """
        Store a counter move for opponent's move.
        
        Args:
            opponent_move: Opponent's move
            counter_move: Our best response
        """
        if self.config.enable_counter_moves:
            self.counter_moves[opponent_move] = counter_move
    
    def _debug_move_ordering(self, ordered_moves: List[OrderedMove]):
        """Debug output for move ordering (removed in production)."""
        print("Top moves by priority:")
        for i, ordered_move in enumerate(ordered_moves):
            print(f"  {i+1}. {ordered_move.move} ({ordered_move.priority}) - {ordered_move.source}")
    
    def get_statistics(self) -> MoveOrderingStats:
        """Get current move ordering statistics."""
        return self.stats
