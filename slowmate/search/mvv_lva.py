"""
MVV-LVA (Most Valuable Victim - Least Valuable Attacker) Implementation

Traditional move ordering heuristic for captures. Used as a fast alternative
to SEE when time is limited, or as a secondary ordering criterion.
"""

from typing import Dict, List, Tuple
import chess


class MVVLVA:
    """Most Valuable Victim - Least Valuable Attacker implementation."""
    
    def __init__(self):
        # Traditional piece values for MVV-LVA
        self.PIECE_VALUES = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 100  # Should never capture king, but high value for safety
        }
        
        # Pre-computed MVV-LVA lookup table for performance
        self._mvv_lva_scores = self._build_mvv_lva_table()
    
    def _build_mvv_lva_table(self) -> Dict[Tuple[chess.PieceType, chess.PieceType], int]:
        """Build lookup table for MVV-LVA scores."""
        scores = {}
        
        for victim_type in chess.PIECE_TYPES:
            for attacker_type in chess.PIECE_TYPES:
                # Score = Victim Value * 100 + (10 - Attacker Value)
                # This prioritizes valuable victims and cheap attackers
                victim_value = self.PIECE_VALUES[victim_type]
                attacker_value = self.PIECE_VALUES[attacker_type]
                
                # Scale victim value and invert attacker value
                score = (victim_value * 100) + (10 - attacker_value)
                scores[(victim_type, attacker_type)] = score
                
        return scores
    
    def get_capture_score(self, board: chess.Board, move: chess.Move) -> int:
        """
        Get MVV-LVA score for a capture move.
        
        Args:
            board: Current board position
            move: Capture move to score
            
        Returns:
            MVV-LVA score (higher = better capture)
        """
        if not board.is_capture(move):
            return 0
            
        attacker = board.piece_at(move.from_square)
        victim = board.piece_at(move.to_square)
        
        if not attacker or not victim:
            return 0
            
        return self._mvv_lva_scores.get(
            (victim.piece_type, attacker.piece_type), 0
        )
    
    def sort_captures(self, board: chess.Board, captures: List[chess.Move]) -> List[chess.Move]:
        """
        Sort capture moves by MVV-LVA score.
        
        Args:
            board: Current board position
            captures: List of capture moves
            
        Returns:
            Captures sorted by MVV-LVA (best first)
        """
        return sorted(captures, 
                     key=lambda move: self.get_capture_score(board, move), 
                     reverse=True)
    
    def get_best_captures(self, board: chess.Board, moves: List[chess.Move], 
                         count: int = 5) -> List[chess.Move]:
        """
        Get the best N captures by MVV-LVA.
        
        Args:
            board: Current board position
            moves: All legal moves
            count: Number of best captures to return
            
        Returns:
            Best captures by MVV-LVA
        """
        captures = [move for move in moves if board.is_capture(move)]
        sorted_captures = self.sort_captures(board, captures)
        return sorted_captures[:count]
    
    def classify_capture_simple(self, board: chess.Board, move: chess.Move) -> str:
        """
        Simple capture classification based on piece values only.
        
        Args:
            board: Current board position
            move: Capture move
            
        Returns:
            'winning', 'equal', or 'neutral' (can't determine losing without SEE)
        """
        if not board.is_capture(move):
            return 'neutral'
            
        attacker = board.piece_at(move.from_square)
        victim = board.piece_at(move.to_square)
        
        if not attacker or not victim:
            return 'neutral'
            
        victim_value = self.PIECE_VALUES[victim.piece_type]
        attacker_value = self.PIECE_VALUES[attacker.piece_type]
        
        if victim_value > attacker_value:
            return 'winning'
        elif victim_value == attacker_value:
            return 'equal'
        else:
            return 'neutral'  # Could be losing, but need SEE to confirm
    
    def get_victim_value(self, board: chess.Board, move: chess.Move) -> int:
        """
        Get the value of the captured piece.
        
        Args:
            board: Current board position
            move: Capture move
            
        Returns:
            Value of captured piece
        """
        if not board.is_capture(move):
            return 0
            
        victim = board.piece_at(move.to_square)
        if victim:
            return self.PIECE_VALUES[victim.piece_type]
        return 0
    
    def get_attacker_value(self, board: chess.Board, move: chess.Move) -> int:
        """
        Get the value of the attacking piece.
        
        Args:
            board: Current board position
            move: Capture move
            
        Returns:
            Value of attacking piece
        """
        attacker = board.piece_at(move.from_square)
        if attacker:
            return self.PIECE_VALUES[attacker.piece_type]
        return 0
