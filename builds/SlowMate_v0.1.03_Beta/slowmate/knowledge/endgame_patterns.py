"""
Endgame pattern recognition for decisive checkmate patterns.

This module provides strategic guidance for converting material advantage
into decisive checkmates, focusing on basic and advanced mating techniques.
"""

import json
import os
from typing import Dict, List, Optional, Any
import chess
from chess import Board, Move


class EndgamePatterns:
    """Endgame pattern recognition and strategic move generation."""
    
    def __init__(self, data_dir: str = "data/endgames"):
        """
        Initialize endgame patterns.
        
        Args:
            data_dir: Directory containing endgame pattern JSON files
        """
        self.data_dir = data_dir
        self.mate_patterns: Dict[str, Any] = {}
        self.pawn_endings: Dict[str, Any] = {}
        self.tactical_setups: Dict[str, Any] = {}
        self.is_loaded = False
        
        # Automatically load patterns on initialization
        self.load_patterns()
    
    def load_patterns(self) -> bool:
        """
        Load endgame patterns from JSON files.
        
        Returns:
            True if patterns loaded successfully, False otherwise
        """
        try:
            # Load mate patterns
            mate_file = os.path.join(self.data_dir, "mate_patterns.json")
            if os.path.exists(mate_file):
                with open(mate_file, 'r') as f:
                    self.mate_patterns = json.load(f)
            
            # Load pawn endings
            pawn_file = os.path.join(self.data_dir, "pawn_endings.json")
            if os.path.exists(pawn_file):
                with open(pawn_file, 'r') as f:
                    self.pawn_endings = json.load(f)
            
            # Load tactical setups
            tactical_file = os.path.join(self.data_dir, "tactical_setups.json")
            if os.path.exists(tactical_file):
                with open(tactical_file, 'r') as f:
                    self.tactical_setups = json.load(f)
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading endgame patterns: {e}")
            self.is_loaded = False
            return False
    
    def get_strategic_move(self, board: Board) -> Optional[Move]:
        """
        Get strategic endgame move for current position.
        
        Args:
            board: Current chess position
            
        Returns:
            Strategic move if position matches endgame pattern, None otherwise
        """
        if not self.is_loaded or not self._is_endgame_position(board):
            return None
        
        # Check for basic checkmate patterns first
        mate_move = self._get_basic_mate_move(board)
        if mate_move:
            return mate_move
        
        # Check for general strategic improvements
        strategic_move = self._get_general_strategic_move(board)
        if strategic_move:
            return strategic_move
        
        return None
    
    def _get_basic_mate_move(self, board: Board) -> Optional[Move]:
        """Get move for basic checkmate patterns."""
        material_sig = self._get_material_signature(board)
        
        if material_sig == "KQ_vs_K":
            return self._queen_king_mate_move(board)
        elif material_sig == "KR_vs_K":
            return self._rook_king_mate_move(board)
        elif material_sig == "KRR_vs_K":
            return self._two_rook_mate_move(board)
        
        return None
    
    def _get_general_strategic_move(self, board: Board) -> Optional[Move]:
        """Get general strategic improvement move."""
        # Look for moves that improve king position
        king_move = self._get_king_improvement_move(board)
        if king_move:
            return king_move
        
        # Look for moves that advance passed pawns
        pawn_advance = self._get_passed_pawn_advance(board)
        if pawn_advance:
            return pawn_advance
        
        # Look for piece activation moves
        piece_activation = self._get_piece_activation_move(board)
        if piece_activation:
            return piece_activation
        
        return None
    
    def _queen_king_mate_move(self, board: Board) -> Optional[Move]:
        """Generate move for Queen + King vs King mate."""
        my_king = board.king(board.turn)
        enemy_king = board.king(not board.turn)
        my_queen = self._find_piece(board, chess.QUEEN, board.turn)
        
        # Safety check: all pieces must exist
        if my_king is None or enemy_king is None or my_queen is None:
            return None
        
        # Priority 1: Check if we can give checkmate in one
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.QUEEN:
                board.push(move)
                if board.is_checkmate():
                    board.pop()
                    return move
                board.pop()
        
        # Priority 2: Drive enemy king toward edge
        edge_distance = self._distance_to_edge(enemy_king)
        best_move = None
        best_improvement = 0
        
        for move in board.legal_moves:
            board.push(move)
            new_enemy_king = board.king(not board.turn)
            if new_enemy_king is not None:
                new_edge_distance = self._distance_to_edge(new_enemy_king)
                improvement = edge_distance - new_edge_distance
                
                # Bonus for moves that also bring our king closer
                piece = board.piece_at(move.from_square)
                if piece and piece.piece_type == chess.KING:
                    new_my_king = move.to_square
                    king_distance_improvement = chess.square_distance(my_king, enemy_king) - chess.square_distance(new_my_king, new_enemy_king)
                    improvement += king_distance_improvement * 0.5
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_move = move
            board.pop()
        
        return best_move
    
    def _rook_king_mate_move(self, board: Board) -> Optional[Move]:
        """Generate move for Rook + King vs King mate."""
        my_king = board.king(board.turn)
        enemy_king = board.king(not board.turn)
        my_rook = self._find_piece(board, chess.ROOK, board.turn)
        
        # Safety check
        if my_king is None or enemy_king is None or my_rook is None:
            return None
        
        # Priority 1: Checkmate in one
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.ROOK:
                board.push(move)
                if board.is_checkmate():
                    board.pop()
                    return move
                board.pop()
        
        # Priority 2: Cut off enemy king with rook
        enemy_rank = chess.square_rank(enemy_king)
        enemy_file = chess.square_file(enemy_king)
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.ROOK:
                to_rank = chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                
                # Good if rook cuts off king on rank or file
                if to_rank == enemy_rank or to_file == enemy_file:
                    # Make sure we're not moving too close to enemy king
                    if chess.square_distance(move.to_square, enemy_king) >= 2:
                        return move
        
        # Priority 3: Bring king closer for support
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KING:
                current_distance = chess.square_distance(my_king, enemy_king)
                new_distance = chess.square_distance(move.to_square, enemy_king)
                if new_distance < current_distance and new_distance >= 2:  # Don't get too close
                    return move
        
        return None
    
    def _two_rook_mate_move(self, board: Board) -> Optional[Move]:
        """Generate move for two rooks 'closing the box' mate."""
        my_rooks = []
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type == chess.ROOK and piece.color == board.turn:
                my_rooks.append(sq)
        
        if len(my_rooks) < 2:
            return None
        
        enemy_king = board.king(not board.turn)
        if enemy_king is None:
            return None
        
        # Priority 1: Immediate checkmate
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.ROOK:
                board.push(move)
                if board.is_checkmate():
                    board.pop()
                    return move
                board.pop()
        
        # Priority 2: Coordinate rooks to reduce king's space
        enemy_rank = chess.square_rank(enemy_king)
        enemy_file = chess.square_file(enemy_king)
        
        # Look for moves that put rooks on adjacent ranks/files
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.ROOK:
                to_rank = chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                
                # Good if this creates a "box" around enemy king
                if abs(to_rank - enemy_rank) <= 2 or abs(to_file - enemy_file) <= 2:
                    return move
        
        return None
    
    def _get_king_improvement_move(self, board: Board) -> Optional[Move]:
        """Get move that improves king position."""
        my_king = board.king(board.turn)
        enemy_king = board.king(not board.turn)
        
        if my_king is None or enemy_king is None:
            return None
        
        best_move = None
        best_improvement = 0
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KING:
                # Prefer moves that bring king closer to center or enemy king
                current_center_distance = self._distance_to_center(my_king)
                new_center_distance = self._distance_to_center(move.to_square)
                center_improvement = current_center_distance - new_center_distance
                
                # Also consider distance to enemy king
                current_king_distance = chess.square_distance(my_king, enemy_king)
                new_king_distance = chess.square_distance(move.to_square, enemy_king)
                king_improvement = current_king_distance - new_king_distance
                
                total_improvement = center_improvement + king_improvement * 0.5
                
                if total_improvement > best_improvement:
                    best_improvement = total_improvement
                    best_move = move
        
        return best_move
    
    def _get_passed_pawn_advance(self, board: Board) -> Optional[Move]:
        """Get move that advances a passed pawn."""
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                # Simple heuristic: advance pawn toward promotion
                if board.turn == chess.WHITE:
                    if chess.square_rank(move.to_square) > chess.square_rank(move.from_square):
                        return move
                else:
                    if chess.square_rank(move.to_square) < chess.square_rank(move.from_square):
                        return move
        return None
    
    def _get_piece_activation_move(self, board: Board) -> Optional[Move]:
        """Get move that activates a piece (moves it to a more central square)."""
        best_move = None
        best_improvement = 0
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT]:
                # Prefer moves toward center
                current_center_distance = self._distance_to_center(move.from_square)
                new_center_distance = self._distance_to_center(move.to_square)
                improvement = current_center_distance - new_center_distance
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_move = move
        
        return best_move
    
    def _get_material_signature(self, board: Board) -> str:
        """Get simplified material signature for pattern matching."""
        white_pieces = []
        black_pieces = []
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_char = piece.symbol().upper()
                if piece.color == chess.WHITE:
                    white_pieces.append(piece_char)
                else:
                    black_pieces.append(piece_char)
        
        white_material = ''.join(sorted(white_pieces))
        black_material = ''.join(sorted(black_pieces))
        
        return f"{white_material}_vs_{black_material}"
    
    def _find_piece(self, board: Board, piece_type: int, color: bool) -> Optional[int]:
        """Find first piece of given type and color."""
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == piece_type and piece.color == color:
                return square
        return None
    
    def _distance_to_edge(self, square: int) -> int:
        """Calculate distance from square to nearest board edge."""
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        return min(rank, 7 - rank, file, 7 - file)
    
    def _distance_to_center(self, square: int) -> int:
        """Calculate distance from square to center of board."""
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        center_rank = 3.5
        center_file = 3.5
        return int(abs(rank - center_rank) + abs(file - center_file))
    
    def _is_endgame_position(self, board: Board) -> bool:
        """
        Determine if current position is an endgame.
        
        Simple heuristic: Total material < threshold
        """
        total_material = 0
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                total_material += piece_values[piece.piece_type]
        
        return total_material <= 20  # Endgame threshold
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get endgame pattern statistics."""
        return {
            'mate_patterns': len(self.mate_patterns),
            'pawn_endings': len(self.pawn_endings),
            'tactical_setups': len(self.tactical_setups),
            'is_loaded': self.is_loaded
        }
