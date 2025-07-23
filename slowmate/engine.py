"""
SlowMate Chess Engine - Enhanced Engine Core (v0.4.01)

Enhanced engine with professional statistics tracking and transparency.
"""

import chess
from typing import Optional, List, Dict, Any

class SlowMateEngine:
    """Enhanced chess engine with professional features."""
    
    def __init__(self):
        """Initialize the enhanced engine."""
        self.board = chess.Board()
        self.version = "0.4.01"
        self.name = "SlowMate"
        
        # Game statistics
        self.game_stats = {
            'moves_played': 0,
            'positions_evaluated': 0,
            'search_nodes': 0,
            'game_phase': 'opening',
            'material_balance': 0
        }
        
        # Position history for repetition detection
        self.position_history = []
    
    def set_position(self, fen: str = None):
        """Set board position from FEN."""
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()
        
        # Update game statistics
        self._update_game_stats()
        
        # Clear position history for new position
        self.position_history = [self.board.fen()]
    
    def make_move(self, move_uci: str):
        """Make a move in UCI format."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.game_stats['moves_played'] += 1
                self.position_history.append(self.board.fen())
                self._update_game_stats()
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
    
    def get_game_phase(self) -> str:
        """Determine current game phase."""
        piece_count = len(self.board.piece_map())
        
        if piece_count >= 28:
            return "opening"
        elif piece_count >= 12:
            return "middlegame"
        else:
            return "endgame"
    
    def get_material_balance(self) -> int:
        """Get material balance in centipawns."""
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        
        balance = 0
        for piece_type in piece_values:
            white_count = len(self.board.pieces(piece_type, chess.WHITE))
            black_count = len(self.board.pieces(piece_type, chess.BLACK))
            balance += (white_count - black_count) * piece_values[piece_type]
        
        return balance
    
    def is_repetition(self) -> bool:
        """Check if current position is a repetition."""
        current_fen = self.board.fen().split(' ')[0]  # Just piece positions
        count = sum(1 for pos in self.position_history if pos.split(' ')[0] == current_fen)
        return count >= 3
    
    def get_position_info(self) -> Dict[str, Any]:
        """Get comprehensive position information."""
        return {
            'fen': self.board.fen(),
            'legal_moves': len(self.board.legal_moves),
            'game_phase': self.get_game_phase(),
            'material_balance': self.get_material_balance(),
            'is_check': self.board.is_check(),
            'is_repetition': self.is_repetition(),
            'halfmove_clock': self.board.halfmove_clock,
            'fullmove_number': self.board.fullmove_number,
            'castling_rights': str(self.board.castling_rights)
        }
    
    def _update_game_stats(self):
        """Update internal game statistics."""
        self.game_stats['game_phase'] = self.get_game_phase()
        self.game_stats['material_balance'] = self.get_material_balance()
        self.game_stats['positions_evaluated'] += 1
