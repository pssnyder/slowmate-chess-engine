"""
Null Move Pruning for SlowMate v0.2.01 Phase 4
Prunes positions where giving the opponent an extra move still doesn't help them.

Null Move Pruning is based on the null move observation: if we can afford to
"pass" (give opponent a free move) and still maintain a good position, then
the current position is probably too good and we can prune this branch.

Architecture: Adaptive depth reduction with zugzwang detection and verification.
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NullMoveStats:
    """Statistics for Null Move Pruning effectiveness."""
    
    null_moves_attempted: int = 0
    null_moves_applied: int = 0
    cutoffs_achieved: int = 0
    verification_searches: int = 0
    verification_cutoffs: int = 0
    
    # Zugzwang detection
    zugzwang_detected: int = 0
    zugzwang_avoided: int = 0
    
    # Depth tracking
    total_depth_reduced: int = 0
    nodes_saved_estimate: int = 0
    
    def get_cutoff_rate(self) -> float:
        """Get percentage of null moves that achieved cutoffs."""
        if self.null_moves_applied == 0:
            return 0.0
        return (self.cutoffs_achieved / self.null_moves_applied) * 100.0
    
    def get_verification_rate(self) -> float:
        """Get percentage that required verification search."""
        if self.null_moves_applied == 0:
            return 0.0
        return (self.verification_searches / self.null_moves_applied) * 100.0
    
    def get_average_reduction(self) -> float:
        """Get average depth reduction per null move."""
        if self.null_moves_applied == 0:
            return 0.0
        return self.total_depth_reduced / self.null_moves_applied
    
    def get_efficiency(self) -> float:
        """Get estimated nodes saved per cutoff."""
        if self.cutoffs_achieved == 0:
            return 0.0
        return self.nodes_saved_estimate / self.cutoffs_achieved
    
    def reset(self):
        """Reset all statistics."""
        self.null_moves_attempted = 0
        self.null_moves_applied = 0
        self.cutoffs_achieved = 0
        self.verification_searches = 0
        self.verification_cutoffs = 0
        self.zugzwang_detected = 0
        self.zugzwang_avoided = 0
        self.total_depth_reduced = 0
        self.nodes_saved_estimate = 0


class NullMovePruning:
    """
    Null Move Pruning implementation.
    
    Makes a "null move" (pass turn to opponent) and searches at reduced depth.
    If the reduced search still fails high (score >= beta), we can prune
    because the opponent gets an extra move and still can't improve their position.
    """
    
    def __init__(self):
        """Initialize Null Move Pruning with standard parameters."""
        
        # Basic configuration
        self.min_depth = 2           # Minimum depth to try null move
        self.reduction = 3           # Base depth reduction for null move search
        self.adaptive_reduction = True  # Use adaptive reduction based on depth
        
        # Conditions where null move is not allowed
        self.no_null_in_check = True      # Don't try null move when in check
        self.no_consecutive_nulls = True   # Don't do null move after null move
        self.no_null_in_endgame = True    # Don't try in obvious endgames
        
        # Zugzwang detection
        self.zugzwang_verification = True  # Verify in potential zugzwang positions
        self.endgame_piece_threshold = 8   # Piece count for endgame detection
        
        # Material thresholds
        self.min_material_advantage = 0    # Minimum advantage to try null move
        self.max_material_disadvantage = -200  # Don't try when too far behind
        
        # Adaptive parameters
        self.depth_based_reduction = True  # Increase reduction with depth
        self.beta_margin_adjustment = True # Adjust based on beta margin
        
        # Statistics
        self.stats = NullMoveStats()
        
        # Search state
        self.current_ply = 0
        self.null_move_ply = -1  # Ply where last null move was made
    
    def can_try_null_move(self, board: chess.Board, depth: int, ply: int,
                         beta: int, static_eval: Optional[int] = None) -> bool:
        """
        Determine if null move pruning can be attempted.
        
        Args:
            board: Current board position
            depth: Current search depth
            ply: Current ply from root
            beta: Beta value for this node
            static_eval: Static evaluation of position (optional)
            
        Returns:
            True if null move can be attempted
        """
        self.stats.null_moves_attempted += 1
        
        # Basic requirements
        if depth < self.min_depth:
            return False
        
        # Never try null move when in check
        if self.no_null_in_check and board.is_check():
            return False
        
        # Don't do consecutive null moves
        if self.no_consecutive_nulls and ply == self.null_move_ply + 1:
            return False
        
        # Detect obvious endgames where zugzwang is more likely
        if self.no_null_in_endgame and self._is_obvious_endgame(board):
            return False
        
        # Check material balance
        if static_eval is not None:
            # Don't try null move when significantly behind
            if static_eval < self.max_material_disadvantage:
                return False
            
            # In some positions, we need a material advantage
            if static_eval < self.min_material_advantage and self._is_risky_position(board):
                return False
        
        return True
    
    def calculate_reduction(self, depth: int, beta: int, static_eval: Optional[int] = None) -> int:
        """
        Calculate depth reduction for null move search.
        
        Args:
            depth: Current search depth
            beta: Beta value
            static_eval: Static evaluation (optional)
            
        Returns:
            Depth reduction for null move search
        """
        base_reduction = self.reduction
        
        # Adaptive reduction based on depth
        if self.adaptive_reduction and self.depth_based_reduction:
            if depth >= 6:
                base_reduction += 1
            if depth >= 12:
                base_reduction += 1
        
        # Adjust based on how much we're ahead
        if static_eval is not None and self.beta_margin_adjustment:
            margin = static_eval - beta
            if margin > 200:  # Well ahead
                base_reduction += 1
            elif margin < -100:  # Behind
                base_reduction = max(2, base_reduction - 1)
        
        return base_reduction
    
    def should_verify(self, board: chess.Board, depth: int, 
                     null_move_score: int, beta: int) -> bool:
        """
        Determine if we need verification search for zugzwang detection.
        
        Args:
            board: Current board position
            depth: Current search depth
            null_move_score: Score from null move search
            beta: Beta value
            
        Returns:
            True if verification search is needed
        """
        if not self.zugzwang_verification:
            return False
        
        # Only verify if null move search failed high (would cause cutoff)
        if null_move_score < beta:
            return False
        
        # Verify in endgame positions where zugzwang is more likely
        if self._is_potential_zugzwang_position(board):
            self.stats.zugzwang_detected += 1
            return True
        
        # Verify in very tactical positions
        if self._is_tactical_position(board):
            return True
        
        return False
    
    def make_null_move(self, board: chess.Board, ply: int) -> chess.Board:
        """
        Make a null move (switch sides without moving).
        
        Args:
            board: Current board position
            ply: Current ply
            
        Returns:
            Board position after null move
        """
        # Create a copy and switch turns
        null_board = board.copy()
        null_board.turn = not null_board.turn
        
        # Reset en passant (can't capture en passant after null move)
        null_board.ep_square = None
        
        # Record that we made a null move at this ply
        self.null_move_ply = ply
        
        return null_board
    
    def record_null_move_result(self, depth: int, reduction: int, 
                              score: int, beta: int, cutoff: bool,
                              verification_used: bool = False,
                              verification_cutoff: bool = False):
        """
        Record the result of a null move attempt.
        
        Args:
            depth: Original depth
            reduction: Depth reduction used
            score: Score from null move search
            beta: Beta value
            cutoff: Whether null move achieved cutoff
            verification_used: Whether verification search was performed
            verification_cutoff: Whether verification also achieved cutoff
        """
        self.stats.null_moves_applied += 1
        self.stats.total_depth_reduced += reduction
        
        if cutoff:
            self.stats.cutoffs_achieved += 1
            # Estimate nodes saved
            branching_factor = 35
            nodes_saved = pow(branching_factor, depth - 1)
            self.stats.nodes_saved_estimate += int(nodes_saved)
        
        if verification_used:
            self.stats.verification_searches += 1
            if verification_cutoff:
                self.stats.verification_cutoffs += 1
            else:
                # Zugzwang was avoided by verification
                self.stats.zugzwang_avoided += 1
    
    def _is_obvious_endgame(self, board: chess.Board) -> bool:
        """Check if this is an obvious endgame where zugzwang is likely."""
        # Count total pieces
        piece_count = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None and piece.piece_type != chess.KING:
                piece_count += 1
        
        return piece_count <= self.endgame_piece_threshold
    
    def _is_potential_zugzwang_position(self, board: chess.Board) -> bool:
        """Check if this position might be zugzwang-prone."""
        # Endgame positions
        if self._is_obvious_endgame(board):
            return True
        
        # Pawn endgames
        piece_types = set()
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None and piece.piece_type != chess.KING:
                piece_types.add(piece.piece_type)
        
        # Only pawns besides kings
        if piece_types == {chess.PAWN}:
            return True
        
        # King and pawn vs king
        if len(piece_types) <= 1 and chess.PAWN in piece_types:
            return True
        
        return False
    
    def _is_risky_position(self, board: chess.Board) -> bool:
        """Check if position is risky for null move (tactical, under attack)."""
        # Simple heuristic: if we're in check or have hanging pieces
        if board.is_check():
            return True
        
        # This is a simplified check - in practice, you'd want more
        # sophisticated detection of hanging pieces, tactical shots, etc.
        return False
    
    def _is_tactical_position(self, board: chess.Board) -> bool:
        """Check if position is highly tactical."""
        # Count captures and checks available
        tactical_moves = 0
        for move in board.legal_moves:
            if board.is_capture(move) or board.gives_check(move):
                tactical_moves += 1
        
        # If more than 30% of moves are tactical, consider it tactical
        total_moves = board.legal_moves.count()
        if total_moves == 0:
            return False
        
        return (tactical_moves / total_moves) > 0.3
    
    def get_statistics(self) -> Dict[str, float]:
        """Get null move pruning statistics."""
        return {
            'null_moves_attempted': self.stats.null_moves_attempted,
            'null_moves_applied': self.stats.null_moves_applied,
            'cutoffs_achieved': self.stats.cutoffs_achieved,
            'verification_searches': self.stats.verification_searches,
            'verification_cutoffs': self.stats.verification_cutoffs,
            'zugzwang_detected': self.stats.zugzwang_detected,
            'zugzwang_avoided': self.stats.zugzwang_avoided,
            'total_depth_reduced': self.stats.total_depth_reduced,
            'nodes_saved_estimate': self.stats.nodes_saved_estimate,
            'cutoff_rate': self.stats.get_cutoff_rate(),
            'verification_rate': self.stats.get_verification_rate(),
            'average_reduction': self.stats.get_average_reduction(),
            'efficiency': self.stats.get_efficiency(),
            'min_depth': self.min_depth,
            'base_reduction': self.reduction
        }
    
    def configure(self, min_depth: int = 2, reduction: int = 3,
                 adaptive_reduction: bool = True,
                 zugzwang_verification: bool = True):
        """
        Configure null move pruning parameters.
        
        Args:
            min_depth: Minimum depth to try null move
            reduction: Base depth reduction
            adaptive_reduction: Use adaptive reduction
            zugzwang_verification: Enable zugzwang verification
        """
        self.min_depth = min_depth
        self.reduction = reduction
        self.adaptive_reduction = adaptive_reduction
        self.zugzwang_verification = zugzwang_verification
    
    def configure_conditions(self, no_null_in_check: bool = True,
                           no_consecutive_nulls: bool = True,
                           no_null_in_endgame: bool = True,
                           endgame_piece_threshold: int = 8):
        """
        Configure conditions where null move is not allowed.
        
        Args:
            no_null_in_check: Don't try null move when in check
            no_consecutive_nulls: Don't do consecutive null moves
            no_null_in_endgame: Don't try in endgames
            endgame_piece_threshold: Piece count threshold for endgame
        """
        self.no_null_in_check = no_null_in_check
        self.no_consecutive_nulls = no_consecutive_nulls
        self.no_null_in_endgame = no_null_in_endgame
        self.endgame_piece_threshold = endgame_piece_threshold
