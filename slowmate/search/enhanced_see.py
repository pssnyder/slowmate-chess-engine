"""
Enhanced Static Exchange Evaluation (SEE) for SlowMate Chess Engine

This module provides dynamic, time-controllable SEE evaluation for accurate
capture assessment in move ordering. Designed for accuracy-first approach
with future time management integration.
"""

import time
from typing import List, Optional, Tuple, Dict
import chess
from slowmate.search import SearchConfig


class EnhancedSEE:
    """Enhanced Static Exchange Evaluation with dynamic depth control."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        
        # Modern piece values optimized for SEE evaluation
        self.PIECE_VALUES = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000  # Very high value to avoid king captures
        }
        
        # SEE evaluation cache for position
        self._see_cache: Dict[Tuple[chess.Square, chess.Square], int] = {}
        
    def clear_cache(self):
        """Clear SEE cache for new position."""
        self._see_cache.clear()
    
    def evaluate_capture(self, board: chess.Board, move: chess.Move, 
                        time_limit_ms: Optional[int] = None) -> int:
        """
        Evaluate a capture move using enhanced SEE.
        
        Args:
            board: Current board position
            move: Capture move to evaluate
            time_limit_ms: Optional time limit override
            
        Returns:
            Material balance after all exchanges (positive = good capture)
        """
        if not board.is_capture(move):
            return 0
            
        cache_key = (move.from_square, move.to_square)
        if cache_key in self._see_cache:
            return self._see_cache[cache_key]
            
        start_time = time.time() * 1000 if time_limit_ms else None
        
        # Get time limit (config default or override)
        effective_time_limit = time_limit_ms or self.config.see_time_limit_ms
        
        try:
            see_score = self._see_recursive(
                board, move.to_square, board.turn, 
                self.config.see_max_depth, start_time, effective_time_limit
            )
            
            self._see_cache[cache_key] = see_score
            return see_score
            
        except TimeoutError:
            # If time limit exceeded, return conservative estimate
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if victim and attacker:
                # Simple MVV-LVA estimate
                basic_score = self.PIECE_VALUES[victim.piece_type] - self.PIECE_VALUES[attacker.piece_type]
                self._see_cache[cache_key] = basic_score
                return basic_score
                
            return 0
    
    def _see_recursive(self, board: chess.Board, square: chess.Square, 
                      turn: chess.Color, depth_remaining: int,
                      start_time: Optional[float], time_limit_ms: Optional[int]) -> int:
        """
        Recursive SEE calculation with time control.
        
        Args:
            board: Current board position
            square: Square where exchanges occur
            turn: Whose turn to capture
            depth_remaining: Maximum captures to consider
            start_time: Start time for timeout checking
            time_limit_ms: Time limit in milliseconds
            
        Returns:
            Material balance from this side's perspective
        """
        # Check time limit
        if start_time and time_limit_ms:
            current_time = time.time() * 1000
            if (current_time - start_time) > time_limit_ms:
                raise TimeoutError("SEE evaluation time limit exceeded")
        
        if depth_remaining <= 0:
            return 0
            
        # Find the least valuable attacker for current side
        attacker_square = self._get_least_valuable_attacker(board, square, turn)
        if attacker_square is None:
            return 0  # No more attackers
            
        attacker = board.piece_at(attacker_square)
        victim = board.piece_at(square)
        
        if not attacker or not victim:
            return 0
            
        # Calculate material gained/lost from this capture
        material_gained = self.PIECE_VALUES[victim.piece_type]
        
        # Make the capture temporarily
        board.set_piece_at(square, attacker)
        board.remove_piece_at(attacker_square)
        
        try:
            # Recursively calculate opponent's best response
            opponent_score = self._see_recursive(
                board, square, not turn, depth_remaining - 1,
                start_time, time_limit_ms
            )
            
            # Our score is material gained minus opponent's best response
            our_score = material_gained - opponent_score
            
        finally:
            # Restore the board
            board.set_piece_at(attacker_square, attacker)
            board.set_piece_at(square, victim)
            
        return max(0, our_score)  # Don't make bad captures
    
    def _get_least_valuable_attacker(self, board: chess.Board, 
                                   square: chess.Square, color: chess.Color) -> Optional[chess.Square]:
        """
        Find the least valuable piece attacking a square.
        
        Args:
            board: Current board position
            square: Target square
            color: Color of attacking pieces to find
            
        Returns:
            Square of least valuable attacker, or None if no attackers
        """
        attackers = []
        
        # Check all piece types in value order (cheapest first)
        piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
        
        for piece_type in piece_types:
            # Get all pieces of this type for the attacking color
            pieces = board.pieces(piece_type, color)
            
            for piece_square in pieces:
                # Check if this piece attacks the target square
                if self._piece_attacks_square(board, piece_square, square, piece_type):
                    return piece_square
                    
        return None
    
    def _piece_attacks_square(self, board: chess.Board, from_square: chess.Square, 
                            to_square: chess.Square, piece_type: chess.PieceType) -> bool:
        """
        Check if a piece on from_square attacks to_square.
        
        Args:
            board: Current board position
            from_square: Square with attacking piece
            to_square: Target square
            piece_type: Type of attacking piece
            
        Returns:
            True if piece attacks the square
        """
        # Create a temporary move to test legality
        move = chess.Move(from_square, to_square)
        
        # For captures, the move must be legal
        if piece_type == chess.PAWN:
            # Pawns attack diagonally
            file_diff = abs(chess.square_file(from_square) - chess.square_file(to_square))
            rank_diff = abs(chess.square_rank(from_square) - chess.square_rank(to_square))
            
            # Check if it's a diagonal pawn move
            if file_diff == 1 and rank_diff == 1:
                # Check direction based on pawn color
                piece = board.piece_at(from_square)
                if piece:
                    if piece.color == chess.WHITE:
                        return chess.square_rank(to_square) > chess.square_rank(from_square)
                    else:
                        return chess.square_rank(to_square) < chess.square_rank(from_square)
            return False
            
        # For other pieces, check if square is in attack set
        attacks = board.attacks(from_square)
        return to_square in attacks
    
    def classify_capture(self, board: chess.Board, move: chess.Move) -> str:
        """
        Classify a capture as winning, equal, or losing.
        
        Args:
            board: Current board position
            move: Capture move to classify
            
        Returns:
            'winning', 'equal', or 'losing'
        """
        see_score = self.evaluate_capture(board, move)
        
        if see_score > 0:
            return 'winning'
        elif see_score == 0:
            return 'equal'
        else:
            return 'losing'
    
    def get_capture_value(self, board: chess.Board, move: chess.Move) -> int:
        """
        Get the raw material value of a capture (victim piece value).
        
        Args:
            board: Current board position
            move: Capture move
            
        Returns:
            Material value of captured piece
        """
        if not board.is_capture(move):
            return 0
            
        victim = board.piece_at(move.to_square)
        if victim:
            return self.PIECE_VALUES[victim.piece_type]
        return 0
