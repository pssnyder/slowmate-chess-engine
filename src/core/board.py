"""
SlowMate Chess Engine - Board Module
Handles chess board representation and basic operations
Version: 1.0.0-BETA
"""

import chess
import chess.polyglot


class Board:
    """Chess board representation with enhanced functionality."""
    
    def __init__(self):
        """Initialize a new chess board with starting position."""
        self.board = chess.Board()
        self._position_cache = {}  # Cache for evaluated positions
        self._phase = None  # Current game phase
        
    def get_legal_moves(self):
        """Return list of legal moves in current position."""
        return list(self.board.legal_moves)
    
    def make_move(self, move):
        """Make a move on the board."""
        self.board.push(move)
        self._phase = None  # Reset phase cache
        self._position_cache = {}  # Reset evaluation cache
        
    def unmake_move(self):
        """Take back the last move."""
        self.board.pop()
        self._phase = None  # Reset phase cache
        self._position_cache = {}  # Reset evaluation cache
        
    def is_game_over(self):
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_result(self):
        """Get the game result if the game is over."""
        if not self.is_game_over():
            return None
        return self.board.result()
    
    def get_fen(self):
        """Get FEN string of current position."""
        return self.board.fen()
    
    def set_fen(self, fen):
        """Set the board position from FEN string."""
        self.board.set_fen(fen)
        self._phase = None  # Reset phase cache
        self._position_cache = {}  # Reset evaluation cache
    
    def get_phase(self):
        """Get the current game phase."""
        if self._phase is not None:
            return self._phase
            
        # Simple phase detection based on material
        pawns = len(self.board.pieces(chess.PAWN, chess.WHITE)) + \
                len(self.board.pieces(chess.PAWN, chess.BLACK))
        pieces = len(self.board.piece_map()) - pawns
        
        if pawns >= 12 and pieces >= 12:  # Opening
            self._phase = 'opening'
        elif pawns <= 4 or pieces <= 6:  # Endgame
            self._phase = 'endgame'
        else:  # Middlegame
            self._phase = 'middlegame'
            
        return self._phase
    
    def get_material_count(self):
        """Get material count for both sides in centipawns."""
        piece_values = {
            chess.PAWN: 100,    # Base unit
            chess.KNIGHT: 325,  # Equal to bishop but different strengths
            chess.BISHOP: 325,  # Equal to knight but different strengths
            chess.ROOK: 500,    # Worth 5 pawns
            chess.QUEEN: 975,   # Slightly less than 2 rooks
            chess.KING: 20000   # Effectively infinite
        }
        
        white_material = sum(len(self.board.pieces(piece, chess.WHITE)) * value 
                           for piece, value in piece_values.items())
        black_material = sum(len(self.board.pieces(piece, chess.BLACK)) * value 
                           for piece, value in piece_values.items())
                           
        return white_material, black_material
    
    def is_check(self):
        """Check if current position is check."""
        return self.board.is_check()
    
    def is_checkmate(self):
        """Check if current position is checkmate."""
        return self.board.is_checkmate()
    
    def is_stalemate(self):
        """Check if current position is stalemate."""
        return self.board.is_stalemate()
    
    def is_insufficient_material(self):
        """Check if position has insufficient material to mate."""
        return self.board.is_insufficient_material()
    
    def __str__(self):
        """String representation of the board."""
        return str(self.board)
