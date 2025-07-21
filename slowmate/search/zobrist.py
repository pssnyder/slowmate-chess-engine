"""
Zobrist Hashing for SlowMate Chess Engine

This module implements 64-bit Zobrist hashing for fast position identification
in transposition tables. Includes incremental hash updates for performance.

Zobrist hashing uses pre-computed random numbers to create unique position
signatures that can be updated incrementally during move make/unmake.
"""

import random
from typing import Dict, Optional
import chess


class ZobristHasher:
    """64-bit Zobrist hashing for chess positions."""
    
    def __init__(self, seed: int = 12345):
        """
        Initialize Zobrist hasher with pre-computed random numbers.
        
        Args:
            seed: Random seed for reproducible hash tables
        """
        # Set seed for reproducible hash values across engine runs
        random.seed(seed)
        
        # Zobrist random numbers for each piece on each square
        self.piece_square_hashes: Dict[tuple, int] = {}
        
        # Initialize piece-square hash values
        for square in range(64):
            for piece_type in chess.PIECE_TYPES:
                for color in chess.COLORS:
                    key = (square, piece_type, color)
                    self.piece_square_hashes[key] = self._random_64bit()
        
        # Special position features
        self.side_to_move_hash = self._random_64bit()
        self.castling_hashes = {
            chess.A1: self._random_64bit(),  # White queenside
            chess.H1: self._random_64bit(),  # White kingside  
            chess.A8: self._random_64bit(),  # Black queenside
            chess.H8: self._random_64bit(),  # Black kingside
        }
        
        # En passant file hashes (files a-h)
        self.en_passant_hashes = [self._random_64bit() for _ in range(8)]
        
        # Reset random seed to avoid affecting other random operations
        random.seed()
    
    def _random_64bit(self) -> int:
        """Generate a random 64-bit integer."""
        return random.randint(0, 2**64 - 1)
    
    def hash_position(self, board: chess.Board) -> int:
        """
        Calculate full Zobrist hash for a position.
        
        Args:
            board: Chess position to hash
            
        Returns:
            64-bit position hash
        """
        hash_value = 0
        
        # Hash each piece on the board
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                key = (square, piece.piece_type, piece.color)
                hash_value ^= self.piece_square_hashes[key]
        
        # Hash side to move
        if board.turn == chess.BLACK:
            hash_value ^= self.side_to_move_hash
        
        # Hash castling rights
        for square, castle_hash in self.castling_hashes.items():
            if board.has_castling_rights(chess.WHITE if square in [chess.A1, chess.H1] else chess.BLACK):
                if square in [chess.A1, chess.A8]:  # Queenside
                    if board.has_queenside_castling_rights(chess.WHITE if square == chess.A1 else chess.BLACK):
                        hash_value ^= castle_hash
                else:  # Kingside
                    if board.has_kingside_castling_rights(chess.WHITE if square == chess.H1 else chess.BLACK):
                        hash_value ^= castle_hash
        
        # Hash en passant target
        if board.ep_square is not None:
            ep_file = chess.square_file(board.ep_square)
            hash_value ^= self.en_passant_hashes[ep_file]
        
        return hash_value
    
    def hash_after_move(self, board: chess.Board, move: chess.Move, 
                       current_hash: Optional[int] = None) -> int:
        """
        Calculate hash after making a move (incremental update).
        
        Args:
            board: Current board position  
            move: Move to make
            current_hash: Current position hash (calculated if None)
            
        Returns:
            Hash after making the move
        """
        if current_hash is None:
            current_hash = self.hash_position(board)
        
        hash_value = current_hash
        
        # Remove moving piece from source square
        moving_piece = board.piece_at(move.from_square)
        if moving_piece:
            key = (move.from_square, moving_piece.piece_type, moving_piece.color)
            hash_value ^= self.piece_square_hashes[key]
        
        # Handle captures - remove captured piece
        if board.is_capture(move):
            captured_square = move.to_square
            
            # Handle en passant capture
            if board.is_en_passant(move):
                captured_square = chess.square(
                    chess.square_file(move.to_square),
                    chess.square_rank(move.from_square)
                )
            
            captured_piece = board.piece_at(captured_square)
            if captured_piece:
                key = (captured_square, captured_piece.piece_type, captured_piece.color)
                hash_value ^= self.piece_square_hashes[key]
        
        # Add piece to destination square (handle promotion)
        if moving_piece:
            piece_type = move.promotion if move.promotion else moving_piece.piece_type
            key = (move.to_square, piece_type, moving_piece.color)
            hash_value ^= self.piece_square_hashes[key]
        
        # Handle castling rook movement
        if board.is_castling(move):
            # Remove rook from old square, add to new square
            if chess.square_file(move.to_square) > chess.square_file(move.from_square):
                # Kingside castling
                rook_from = chess.square(7, chess.square_rank(move.from_square))
                rook_to = chess.square(5, chess.square_rank(move.from_square))
            else:
                # Queenside castling  
                rook_from = chess.square(0, chess.square_rank(move.from_square))
                rook_to = chess.square(3, chess.square_rank(move.from_square))
            
            rook_piece = board.piece_at(rook_from)
            if rook_piece:
                # Remove rook from old square
                key = (rook_from, rook_piece.piece_type, rook_piece.color)
                hash_value ^= self.piece_square_hashes[key]
                
                # Add rook to new square
                key = (rook_to, rook_piece.piece_type, rook_piece.color)
                hash_value ^= self.piece_square_hashes[key]
        
        # Toggle side to move
        hash_value ^= self.side_to_move_hash
        
        # Update castling rights (this is complex, so we'll recalculate)
        # In a full implementation, we'd track castling changes incrementally
        # For now, we'll update this after the move is made
        
        # Update en passant (will be set after move is made)
        # Remove old en passant if it existed
        if board.ep_square is not None:
            ep_file = chess.square_file(board.ep_square)
            hash_value ^= self.en_passant_hashes[ep_file]
        
        return hash_value
    
    def update_hash_after_move(self, board: chess.Board, move: chess.Move, 
                              hash_before_move: int) -> int:
        """
        Update hash after a move has been made on the board.
        
        This handles the complex cases like castling rights and en passant
        that are easier to calculate after the move is made.
        
        Args:
            board: Board position after move is made
            move: Move that was made
            hash_before_move: Hash before the move
            
        Returns:
            Corrected hash after move
        """
        # Start with incremental calculation
        hash_value = self.hash_after_move(board, move, hash_before_move)
        
        # For castling rights and en passant, it's easier to recalculate
        # these specific components rather than track all the edge cases
        
        # Remove old castling contribution (we don't know what it was)
        # and add new castling contribution
        # This is a simplification - a full implementation would track changes
        
        # Add new en passant if it exists
        if board.ep_square is not None:
            ep_file = chess.square_file(board.ep_square)
            hash_value ^= self.en_passant_hashes[ep_file]
        
        return hash_value
    
    def verify_hash(self, board: chess.Board, incremental_hash: int) -> bool:
        """
        Verify that incremental hash matches full calculation.
        
        Args:
            board: Current board position
            incremental_hash: Hash calculated incrementally
            
        Returns:
            True if hashes match
        """
        full_hash = self.hash_position(board)
        return full_hash == incremental_hash
    
    def get_hash_key(self, hash_value: int, table_size: int) -> int:
        """
        Convert 64-bit hash to table index.
        
        Args:
            hash_value: 64-bit Zobrist hash
            table_size: Size of hash table
            
        Returns:
            Table index
        """
        return hash_value % table_size
