"""
SlowMate Chess Engine - Enhanced Engine Core (v0.5.0)

Enhanced engine with advanced NegaScout search architecture and comprehensive features.
"""

import chess
from typing import Optional, List, Dict, Any
from .game_rules import GameRulesManager
from .negascout_search import AdvancedSearchEngine

class SlowMateEngine:
    """Enhanced chess engine with professional features."""
    
    def __init__(self):
        """Initialize the enhanced engine."""
        self.board = chess.Board()
        self.version = "0.5.0"
        self.name = "SlowMate"
        
        # Advanced search engine with NegaScout
        self.search_engine = AdvancedSearchEngine(hash_size_mb=64)  # 64MB default
        
        # Game rules and draw detection
        self.game_rules = GameRulesManager()
        
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
    
    def set_position(self, fen: Optional[str] = None):
        """Set board position from FEN."""
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()
        
        # Update game statistics
        self._update_game_stats()
        
        # Clear position history for new position
        self.position_history = [self.board.fen()]
        
        # Add to game rules manager
        self.game_rules.reset_game()
        self.game_rules.add_position(self.board)
    
    def make_move(self, move_uci: str):
        """Make a move in UCI format."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.game_stats['moves_played'] += 1
                
                # Add position to game rules tracking
                self.game_rules.add_position(self.board, move)
                
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
            'legal_moves': len(list(self.board.legal_moves)),
            'game_phase': self.get_game_phase(),
            'material_balance': self.get_material_balance(),
            'is_check': self.board.is_check(),
            'is_repetition': self.is_repetition(),
            'halfmove_clock': self.board.halfmove_clock,
            'fullmove_number': self.board.fullmove_number,
            'castling_rights': str(self.board.castling_rights),
            'game_rules_status': self.game_rules.get_game_status(self.board)
        }
    
    def set_hash_size(self, size_mb: int):
        """Set hash table size."""
        self.search_engine.set_hash_size(size_mb)
    
    def clear_hash(self):
        """Clear the hash table."""
        self.search_engine.clear_hash()
    
    def get_hash_stats(self) -> Dict[str, int]:
        """Get hash table statistics."""
        return self.search_engine.get_stats()
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return self.search_engine.get_stats()
    
    def set_contempt(self, contempt: int):
        """Set contempt factor in centipawns."""
        self.search_engine.set_contempt(contempt)
    
    def search_position(self, depth: int = 6, max_time: int = 5000) -> tuple[int, Optional[chess.Move]]:
        """Search current position using advanced NegaScout algorithm."""
        self.search_engine.reset_stats()
        self.search_engine.max_search_time = max_time
        return self.search_engine.negascout_search(self.board, depth, -50000, 50000)
    
    def _update_game_stats(self):
        """Update internal game statistics."""
        self.game_stats['game_phase'] = self.get_game_phase()
        self.game_stats['material_balance'] = self.get_material_balance()
        self.game_stats['positions_evaluated'] += 1
