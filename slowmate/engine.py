"""
SlowMate Chess Engine - Core Engine (v0.1.0 Baseline)

Basic chess engine with move generation and position management.
This is the tournament-winning baseline version.
"""

import chess
from typing import Optional, List

class SlowMateEngine:
    """Core chess engine class."""
    
    def __init__(self):
        """Initialize the engine."""
        self.board = chess.Board()
        self.version = "0.1.0"
        self.name = "SlowMate"
    
    def set_position(self, fen: str = None):
        """Set board position from FEN."""
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()
    
    def make_move(self, move_uci: str):
        """Make a move in UCI format."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
        except:
            pass
        return False
    
    def get_legal_moves(self) -> List[chess.Move]:
        """Get all legal moves in current position."""
        return list(self.board.legal_moves)
    
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.board.is_game_over()
    
    def get_result(self) -> Optional[str]:
        """Get game result if game is over."""
        if self.board.is_checkmate():
            return "1-0" if self.board.turn == chess.BLACK else "0-1"
        elif self.board.is_stalemate() or self.board.is_insufficient_material():
            return "1/2-1/2"
        return None
