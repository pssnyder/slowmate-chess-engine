"""
SlowMate Chess Engine - Enhanced Search Module
Version: 1.0.0-BETA
Based on stable v0.2.01 architecture
"""

import chess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    """Search node types for transposition table."""
    EXACT = 0    # Exact score
    UPPER = 1    # Upper bound (beta cutoff)
    LOWER = 2    # Lower bound (failed low)

@dataclass
class TTEntry:
    """Transposition table entry."""
    key: int         # Zobrist hash key
    depth: int       # Search depth
    score: int       # Position score
    node_type: NodeType  # Type of score
    move: Optional[chess.Move]  # Best move found
    age: int        # Search iteration when entry was stored

class TranspositionTable:
    """Enhanced transposition table with aging and replacement scheme."""
    
    def __init__(self, size_mb: int = 64):
        """Initialize transposition table.
        
        Args:
            size_mb: Size in megabytes (default: 64)
        """
        self.size = (size_mb * 1024 * 1024) // 32  # Entries per MB
        self.table: Dict[int, TTEntry] = {}
        self.age = 0
        
    def store(self, key: int, depth: int, score: int, node_type: NodeType,
              move: Optional[chess.Move] = None) -> None:
        """Store a position in the table."""
        if len(self.table) >= self.size:
            # Simple cleanup - remove 10% oldest entries
            sorted_entries = sorted(self.table.items(), 
                                 key=lambda x: x[1].age)
            for k, _ in sorted_entries[:self.size // 10]:
                del self.table[k]
                
        self.table[key] = TTEntry(
            key=key,
            depth=depth,
            score=score,
            node_type=node_type,
            move=move,
            age=self.age
        )
        
    def lookup(self, key: int, depth: int, alpha: int, beta: int) -> Optional[Tuple[int, Optional[chess.Move]]]:
        """Lookup a position in the table."""
        entry = self.table.get(key)
        if not entry:
            return None
            
        if entry.depth >= depth:
            if entry.node_type == NodeType.EXACT:
                return entry.score, entry.move
            elif entry.node_type == NodeType.UPPER and entry.score <= alpha:
                return alpha, entry.move
            elif entry.node_type == NodeType.LOWER and entry.score >= beta:
                return beta, entry.move
                
        return None

class MoveOrderer:
    """Advanced move ordering system."""
    
    def __init__(self):
        """Initialize move ordering system."""
        self.killer_moves: Dict[int, List[chess.Move]] = {}  # depth -> moves
        self.history_table: Dict[Tuple[int, int], int] = {}  # (from, to) -> score
        self.counter_moves: Dict[chess.Move, chess.Move] = {}  # move -> counter
        
    def order_moves(self, board: chess.Board, moves: List[chess.Move], depth: int,
                   tt_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """Order moves for optimal search efficiency."""
        scored_moves = []
        
        for move in moves:
            score = self._score_move(board, move, depth, tt_move)
            scored_moves.append((move, score))
            
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]
        
    def _score_move(self, board: chess.Board, move: chess.Move, depth: int,
                    tt_move: Optional[chess.Move]) -> int:
        """Score a move for ordering."""
        if tt_move and move == tt_move:
            return 20000  # Hash move
            
        score = 0
        
        # Captures
        if board.is_capture(move):
            victim_piece = board.piece_at(move.to_square)
            attacker_piece = board.piece_at(move.from_square)
            if victim_piece and attacker_piece:
                score = 10000 + self._mvv_lva(victim_piece.piece_type,
                                            attacker_piece.piece_type)
                                            
        # Promotions
        if move.promotion:
            score += 9000 + self._get_piece_value(move.promotion)
            
        # Killer moves
        if depth in self.killer_moves and move in self.killer_moves[depth]:
            score += 8000 + (1000 if move == self.killer_moves[depth][0] else 0)
            
        # Counter moves
        last_move = board.peek() if board.move_stack else None
        if last_move and last_move in self.counter_moves and \
           move == self.counter_moves[last_move]:
            score += 7000
            
        # History heuristic
        history_key = (move.from_square, move.to_square)
        score += self.history_table.get(history_key, 0)
        
        return score
        
    def update_killer_move(self, move: chess.Move, depth: int) -> None:
        """Update killer moves at given depth."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
            
        if move not in self.killer_moves[depth]:
            self.killer_moves[depth].insert(0, move)
            if len(self.killer_moves[depth]) > 2:
                self.killer_moves[depth].pop()
                
    def update_history(self, move: chess.Move, depth: int) -> None:
        """Update history table."""
        key = (move.from_square, move.to_square)
        self.history_table[key] = self.history_table.get(key, 0) + depth * depth
        
    def update_counter_move(self, opponent_move: chess.Move, 
                          counter_move: chess.Move) -> None:
        """Update counter move table."""
        self.counter_moves[opponent_move] = counter_move
        
    @staticmethod
    def _mvv_lva(victim: chess.PieceType, attacker: chess.PieceType) -> int:
        """Calculate MVV-LVA (Most Valuable Victim - Least Valuable Attacker) score."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 2,
            chess.BISHOP: 2,
            chess.ROOK: 3,
            chess.QUEEN: 4,
            chess.KING: 5
        }
        return piece_values[victim] * 10 - piece_values[attacker]
        
    @staticmethod
    def _get_piece_value(piece_type: chess.PieceType) -> int:
        """Get the value of a piece type."""
        values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        return values[piece_type]
