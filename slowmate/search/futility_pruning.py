"""
Futility Pruning for SlowMate v0.2.01 Phase 4
Prunes moves that cannot improve alpha by a sufficient margin.

Futility Pruning uses static evaluation to predict that certain moves
cannot possibly improve the position enough to matter. It's applied
at low depths where the evaluation is more reliable.

Architecture: Multi-level futility with margins and move-dependent pruning.
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FutilityStats:
    """Statistics for Futility Pruning effectiveness."""
    
    futility_attempts: int = 0
    futility_prunes: int = 0
    extended_futility_prunes: int = 0
    move_count_prunes: int = 0
    
    # By depth
    depth_1_prunes: int = 0
    depth_2_prunes: int = 0
    depth_3_prunes: int = 0
    
    # By move type
    quiet_move_prunes: int = 0
    bad_capture_prunes: int = 0
    
    # Accuracy tracking
    saved_evaluations: int = 0
    nodes_saved_estimate: int = 0
    
    def get_prune_rate(self) -> float:
        """Get percentage of moves that were pruned."""
        if self.futility_attempts == 0:
            return 0.0
        return (self.futility_prunes / self.futility_attempts) * 100.0
    
    def get_efficiency(self) -> float:
        """Get estimated nodes saved per prune."""
        if self.futility_prunes == 0:
            return 0.0
        return self.nodes_saved_estimate / self.futility_prunes
    
    def reset(self):
        """Reset all statistics."""
        self.futility_attempts = 0
        self.futility_prunes = 0
        self.extended_futility_prunes = 0
        self.move_count_prunes = 0
        self.depth_1_prunes = 0
        self.depth_2_prunes = 0
        self.depth_3_prunes = 0
        self.quiet_move_prunes = 0
        self.bad_capture_prunes = 0
        self.saved_evaluations = 0
        self.nodes_saved_estimate = 0


class FutilityPruning:
    """
    Futility Pruning implementation.
    
    At low depths, uses static evaluation to determine if a move
    can possibly improve alpha by enough to matter. If not, prunes the move.
    """
    
    def __init__(self):
        """Initialize Futility Pruning with standard parameters."""
        
        # Basic configuration
        self.max_depth = 3           # Maximum depth to apply futility pruning
        self.base_margin = 100       # Base futility margin
        self.depth_margin = 150      # Additional margin per depth
        
        # Extended futility (deeper, more aggressive)
        self.extended_max_depth = 6
        self.extended_margin = 300
        
        # Move count pruning (prune late moves in non-PV nodes)
        self.move_count_pruning = True
        self.move_count_base = 3     # Base move count
        self.move_count_multiplier = 2  # Multiplier per depth
        
        # Conditions where futility is not applied
        self.no_futility_in_check = True    # Don't prune when in check
        self.no_futility_pv_nodes = True    # Don't prune in PV nodes
        self.no_futility_captures = False   # Can prune bad captures
        self.no_futility_promotions = True  # Don't prune promotions
        self.no_futility_checks = True     # Don't prune checking moves
        
        # Adaptive margins
        self.tactical_position_margin = 50  # Extra margin in tactical positions
        self.endgame_margin_reduction = 25  # Reduce margin in endgames
        
        # Statistics
        self.stats = FutilityStats()
    
    def can_prune_move(self, move: chess.Move, board: chess.Board, 
                      depth: int, alpha: int, beta: int, static_eval: int,
                      move_number: int, is_pv_node: bool = False,
                      improving: bool = False) -> bool:
        """
        Determine if a move can be pruned by futility pruning.
        
        Args:
            move: Move to evaluate
            board: Current board position
            depth: Current search depth
            alpha: Current alpha value
            beta: Current beta value
            static_eval: Static evaluation of current position
            move_number: Move's position in the ordered list
            is_pv_node: Whether this is a PV node
            improving: Whether position is improving
            
        Returns:
            True if move can be pruned
        """
        self.stats.futility_attempts += 1
        
        # Don't prune in PV nodes
        if self.no_futility_pv_nodes and is_pv_node:
            return False
        
        # Don't prune when in check
        if self.no_futility_in_check and board.is_check():
            return False
        
        # Don't prune promotions
        if self.no_futility_promotions and move.promotion is not None:
            return False
        
        # Don't prune checking moves
        if self.no_futility_checks:
            board.push(move)
            gives_check = board.is_check()
            board.pop()
            if gives_check:
                return False
        
        # Try different futility pruning levels
        if self._can_prune_basic_futility(depth, alpha, static_eval, move, board):
            return True
        
        if self._can_prune_extended_futility(depth, alpha, static_eval, move, board, improving):
            return True
        
        if self._can_prune_move_count(depth, move_number, is_pv_node, alpha, static_eval):
            return True
        
        return False
    
    def _can_prune_basic_futility(self, depth: int, alpha: int, static_eval: int,
                                 move: chess.Move, board: chess.Board) -> bool:
        """
        Check basic futility pruning at very low depths.
        
        Args:
            depth: Current search depth
            alpha: Alpha value
            static_eval: Static evaluation
            move: Move to check
            board: Board position
            
        Returns:
            True if move can be pruned
        """
        if depth > self.max_depth:
            return False
        
        # Calculate futility margin for this depth
        margin = self.base_margin + (depth * self.depth_margin)
        
        # Adjust margin for position type
        margin = self._adjust_margin_for_position(margin, board)
        
        # For captures, we need to consider the material gain
        if board.is_capture(move):
            if not self.no_futility_captures:
                # Get the value of captured piece
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    piece_values = {
                        chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
                        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
                    }
                    capture_value = piece_values.get(captured_piece.piece_type, 0)
                    
                    # Can prune if even after capture, still below alpha + margin
                    if static_eval + capture_value + margin <= alpha:
                        self.stats.bad_capture_prunes += 1
                        self._record_prune(depth)
                        return True
            return False
        
        # For quiet moves, check if position + margin <= alpha
        if static_eval + margin <= alpha:
            self.stats.quiet_move_prunes += 1
            self._record_prune(depth)
            return True
        
        return False
    
    def _can_prune_extended_futility(self, depth: int, alpha: int, static_eval: int,
                                   move: chess.Move, board: chess.Board, 
                                   improving: bool) -> bool:
        """
        Check extended futility pruning at medium depths.
        
        Args:
            depth: Current search depth
            alpha: Alpha value
            static_eval: Static evaluation
            move: Move to check
            board: Board position
            improving: Whether position is improving
            
        Returns:
            True if move can be pruned
        """
        if depth > self.extended_max_depth or depth <= self.max_depth:
            return False
        
        # Only apply to quiet moves
        if board.is_capture(move) or move.promotion is not None:
            return False
        
        # Use larger margin for extended futility
        margin = self.extended_margin
        
        # Reduce margin if position is improving
        if improving:
            margin = int(margin * 0.75)
        
        # Adjust for position type
        margin = self._adjust_margin_for_position(margin, board)
        
        if static_eval + margin <= alpha:
            self.stats.extended_futility_prunes += 1
            self._record_prune(depth)
            return True
        
        return False
    
    def _can_prune_move_count(self, depth: int, move_number: int, 
                             is_pv_node: bool, alpha: int, static_eval: int) -> bool:
        """
        Check move count pruning (late move pruning).
        
        Args:
            depth: Current search depth
            move_number: Position in move list
            is_pv_node: Whether this is PV node
            alpha: Alpha value
            static_eval: Static evaluation
            
        Returns:
            True if move can be pruned
        """
        if not self.move_count_pruning:
            return False
        
        if is_pv_node or depth <= 1:
            return False
        
        # Calculate move count threshold
        threshold = self.move_count_base + (depth * self.move_count_multiplier)
        
        # Only prune if we've tried enough moves and position isn't great
        if move_number > threshold and static_eval + 50 <= alpha:
            self.stats.move_count_prunes += 1
            self._record_prune(depth)
            return True
        
        return False
    
    def _adjust_margin_for_position(self, base_margin: int, board: chess.Board) -> int:
        """
        Adjust futility margin based on position characteristics.
        
        Args:
            base_margin: Base margin to adjust
            board: Board position
            
        Returns:
            Adjusted margin
        """
        margin = base_margin
        
        # Increase margin in tactical positions
        if self._is_tactical_position(board):
            margin += self.tactical_position_margin
        
        # Decrease margin in endgames (evaluation more reliable)
        if self._is_endgame_position(board):
            margin -= self.endgame_margin_reduction
        
        return max(50, margin)  # Minimum margin
    
    def _is_tactical_position(self, board: chess.Board) -> bool:
        """Check if position is tactical (many captures/checks available)."""
        tactical_moves = 0
        total_moves = 0
        
        for move in board.legal_moves:
            total_moves += 1
            if board.is_capture(move):
                tactical_moves += 1
            else:
                # Check if move gives check
                board.push(move)
                if board.is_check():
                    tactical_moves += 1
                board.pop()
        
        if total_moves == 0:
            return False
        
        return (tactical_moves / total_moves) > 0.25
    
    def _is_endgame_position(self, board: chess.Board) -> bool:
        """Check if position is in endgame."""
        piece_count = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None and piece.piece_type != chess.KING:
                piece_count += 1
        
        return piece_count <= 10
    
    def _record_prune(self, depth: int):
        """Record a successful prune."""
        self.stats.futility_prunes += 1
        self.stats.saved_evaluations += 1
        
        # Track by depth
        if depth == 1:
            self.stats.depth_1_prunes += 1
        elif depth == 2:
            self.stats.depth_2_prunes += 1
        elif depth == 3:
            self.stats.depth_3_prunes += 1
        
        # Estimate nodes saved (very rough)
        self.stats.nodes_saved_estimate += depth * 5
    
    def should_prune_all_remaining(self, depth: int, move_number: int, 
                                  alpha: int, static_eval: int, 
                                  is_pv_node: bool) -> bool:
        """
        Check if all remaining moves can be pruned.
        
        Args:
            depth: Current search depth
            move_number: Current move number
            alpha: Alpha value
            static_eval: Static evaluation
            is_pv_node: Whether this is PV node
            
        Returns:
            True if all remaining moves can be pruned
        """
        if is_pv_node or depth > 2:
            return False
        
        # If we've tried several moves and are well below alpha
        if move_number >= 8 and static_eval + self.base_margin * 2 <= alpha:
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, float]:
        """Get futility pruning statistics."""
        return {
            'futility_attempts': self.stats.futility_attempts,
            'futility_prunes': self.stats.futility_prunes,
            'extended_futility_prunes': self.stats.extended_futility_prunes,
            'move_count_prunes': self.stats.move_count_prunes,
            'depth_1_prunes': self.stats.depth_1_prunes,
            'depth_2_prunes': self.stats.depth_2_prunes,
            'depth_3_prunes': self.stats.depth_3_prunes,
            'quiet_move_prunes': self.stats.quiet_move_prunes,
            'bad_capture_prunes': self.stats.bad_capture_prunes,
            'saved_evaluations': self.stats.saved_evaluations,
            'nodes_saved_estimate': self.stats.nodes_saved_estimate,
            'prune_rate': self.stats.get_prune_rate(),
            'efficiency': self.stats.get_efficiency(),
            'max_depth': self.max_depth,
            'base_margin': self.base_margin,
            'extended_max_depth': self.extended_max_depth
        }
    
    def configure(self, max_depth: int = 3, base_margin: int = 100,
                 depth_margin: int = 150, extended_max_depth: int = 6,
                 extended_margin: int = 300):
        """
        Configure futility pruning parameters.
        
        Args:
            max_depth: Maximum depth for basic futility
            base_margin: Base futility margin
            depth_margin: Additional margin per depth
            extended_max_depth: Maximum depth for extended futility
            extended_margin: Margin for extended futility
        """
        self.max_depth = max_depth
        self.base_margin = base_margin
        self.depth_margin = depth_margin
        self.extended_max_depth = extended_max_depth
        self.extended_margin = extended_margin
    
    def configure_move_count(self, enable: bool = True, base: int = 3, 
                           multiplier: int = 2):
        """
        Configure move count pruning.
        
        Args:
            enable: Whether to enable move count pruning
            base: Base move count
            multiplier: Multiplier per depth
        """
        self.move_count_pruning = enable
        self.move_count_base = base
        self.move_count_multiplier = multiplier
