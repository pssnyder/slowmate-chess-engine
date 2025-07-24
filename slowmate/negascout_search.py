#!/usr/bin/env python3
"""
SlowMate v0.5.0 - Advanced Search Engine
Modern NegaScout implementation with comprehensive move ordering and search enhancements.

Features:
- NegaScout (Principal Variation Search)
- Advanced Move Ordering (TT, PV, SEE, Killers, History)
- Null Move Pruning
- Quiescence Search  
- Static Exchange Evaluation
- Contempt Factor
- Modular evaluation for neural network integration
"""

import chess
import time
import random
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    """Transposition table node types."""
    EXACT = "exact"
    LOWER_BOUND = "lower"
    UPPER_BOUND = "upper"

@dataclass
class SearchStats:
    """Search statistics for analysis and debugging."""
    nodes_searched: int = 0
    qnodes_searched: int = 0
    tt_hits: int = 0
    tt_lookups: int = 0
    cutoffs: int = 0
    null_cutoffs: int = 0
    killer_cutoffs: int = 0
    history_cutoffs: int = 0
    see_evaluations: int = 0
    extensions: int = 0
    reductions: int = 0
    
    def reset(self):
        """Reset all statistics."""
        for field in self.__dataclass_fields__:
            setattr(self, field, 0)

class TranspositionTableEntry:
    """Enhanced transposition table entry."""
    
    def __init__(self, depth: int, score: int, node_type: NodeType, 
                 best_move: Optional[str] = None, age: int = 0):
        self.depth = depth
        self.score = score
        self.node_type = node_type
        self.best_move = best_move
        self.age = age
        self.access_count = 1

class AdvancedTranspositionTable:
    """Advanced transposition table with replacement scheme."""
    
    def __init__(self, size_mb: int = 64):
        """Initialize advanced transposition table."""
        self.max_entries = (size_mb * 1024 * 1024) // 64  # ~64 bytes per entry
        self.table: Dict[int, TranspositionTableEntry] = {}
        self.current_age = 0
        
    def store(self, position_hash: int, depth: int, score: int, node_type: NodeType, 
              best_move: Optional[str] = None):
        """Store position with advanced replacement scheme."""
        if len(self.table) >= self.max_entries:
            self._replace_entry()
        
        if position_hash in self.table:
            existing = self.table[position_hash]
            # Replace if new entry is deeper or more recent
            if depth >= existing.depth or self.current_age - existing.age > 4:
                self.table[position_hash] = TranspositionTableEntry(
                    depth, score, node_type, best_move, self.current_age
                )
        else:
            self.table[position_hash] = TranspositionTableEntry(
                depth, score, node_type, best_move, self.current_age
            )
    
    def lookup(self, position_hash: int) -> Optional[TranspositionTableEntry]:
        """Lookup position in transposition table."""
        if position_hash in self.table:
            entry = self.table[position_hash]
            entry.access_count += 1
            return entry
        return None
    
    def _replace_entry(self):
        """Replace least valuable entry."""
        if not self.table:
            return
        
        # Replace 10% of entries to make room for new ones
        entries_to_remove = max(1, len(self.table) // 10)
        
        # Find entries with lowest value (old + shallow + low access)
        sorted_keys = sorted(self.table.keys(), 
                           key=lambda k: (self.table[k].depth * 2 + 
                                        self.table[k].access_count - 
                                        (self.current_age - self.table[k].age)))
        
        for i in range(min(entries_to_remove, len(sorted_keys))):
            del self.table[sorted_keys[i]]
    
    def clear(self):
        """Clear transposition table."""
        self.table.clear()
        self.current_age += 1
    
    def get_hashfull(self) -> int:
        """Get hash table usage in permille (0-1000)."""
        return min(1000, (len(self.table) * 1000) // self.max_entries)

class MoveOrderer:
    """Advanced move ordering with multiple heuristics."""
    
    def __init__(self):
        # Killer moves: [depth][slot] = move
        self.killer_moves: Dict[int, List[Optional[chess.Move]]] = {}
        
        # History heuristic: [from_square][to_square] = score
        self.history_scores: Dict[Tuple[int, int], int] = {}
        
        # Counter moves: last_move -> best_response
        self.counter_moves: Dict[str, chess.Move] = {}
        
        # Piece-Square tables for move ordering
        self.piece_square_bonus = self._init_piece_square_tables()
    
    def _init_piece_square_tables(self) -> Dict[int, List[int]]:
        """Initialize piece-square tables for move ordering."""
        # Simplified piece-square bonuses (will be enhanced later)
        pst = {}
        
        # Pawn advancement bonus
        pst[chess.PAWN] = [0] * 64
        for sq in range(64):
            rank = chess.square_rank(sq)
            pst[chess.PAWN][sq] = rank * 10  # Encourage pawn advancement
        
        # Knight centralization bonus  
        pst[chess.KNIGHT] = [0] * 64
        for sq in range(64):
            file, rank = chess.square_file(sq), chess.square_rank(sq)
            center_distance = abs(3.5 - file) + abs(3.5 - rank)
            pst[chess.KNIGHT][sq] = int((7 - center_distance) * 5)
        
        # Default for other pieces
        for piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
            pst[piece_type] = [0] * 64
        
        return pst
    
    def order_moves(self, board: chess.Board, moves: List[chess.Move], 
                   depth: int, tt_move: Optional[chess.Move] = None,
                   pv_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """Order moves using multiple heuristics."""
        move_scores = []
        
        for move in moves:
            score = self._score_move(board, move, depth, tt_move, pv_move)
            move_scores.append((score, move))
        
        # Sort by score (highest first)
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in move_scores]
    
    def _score_move(self, board: chess.Board, move: chess.Move, depth: int,
                   tt_move: Optional[chess.Move], pv_move: Optional[chess.Move]) -> int:
        """Score individual move for ordering."""
        score = 0
        
        # 1. Transposition table move (highest priority)
        if tt_move and move == tt_move:
            return 1000000
        
        # 2. Principal variation move
        if pv_move and move == pv_move:
            return 900000
        
        # 3. Captures with SEE evaluation
        if board.is_capture(move):
            see_score = self._static_exchange_evaluation(board, move)
            if see_score >= 0:
                score += 800000 + see_score
            else:
                score += 100000 + see_score  # Bad captures, but still try
        
        # 4. Killer moves
        if depth in self.killer_moves:
            for killer in self.killer_moves[depth]:
                if killer and move == killer:
                    score += 700000
                    break
        
        # 5. Counter moves
        if len(board.move_stack) > 0:
            last_move = board.move_stack[-1].uci()
            if last_move in self.counter_moves and move == self.counter_moves[last_move]:
                score += 600000
        
        # 6. History heuristic
        move_key = (move.from_square, move.to_square)
        if move_key in self.history_scores:
            score += self.history_scores[move_key]
        
        # 7. Piece-square table bonus
        piece = board.piece_at(move.from_square)
        if piece:
            to_bonus = self.piece_square_bonus.get(piece.piece_type, [0] * 64)[move.to_square]
            from_bonus = self.piece_square_bonus.get(piece.piece_type, [0] * 64)[move.from_square]
            score += (to_bonus - from_bonus) * 10
        
        # 8. Promotion bonus
        if move.promotion:
            promotion_value = {chess.QUEEN: 9000, chess.ROOK: 5000, 
                             chess.BISHOP: 3000, chess.KNIGHT: 3000}.get(move.promotion, 0)
            score += promotion_value
        
        # 9. Check bonus
        board.push(move)
        if board.is_check():
            score += 50000
        board.pop()
        
        return score
    
    def _static_exchange_evaluation(self, board: chess.Board, move: chess.Move) -> int:
        """Static Exchange Evaluation for captures."""
        if not board.is_capture(move):
            return 0
        
        # Piece values for SEE
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10000
        }
        
        # Get captured piece value
        captured_piece = board.piece_at(move.to_square)
        if not captured_piece:
            return 0
        
        captured_value = piece_values.get(captured_piece.piece_type, 0)
        
        # Get attacking piece value
        attacking_piece = board.piece_at(move.from_square)
        if not attacking_piece:
            return captured_value
        
        attacking_value = piece_values.get(attacking_piece.piece_type, 0)
        
        # Simple SEE: if we're trading equally or better, it's good
        material_balance = captured_value - attacking_value
        
        # TODO: Implement full SEE calculation with X-ray attacks
        # For now, return simplified evaluation
        return material_balance
    
    def update_killers(self, depth: int, move: chess.Move):
        """Update killer moves."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = [None, None]
        
        # Shift killers
        if self.killer_moves[depth][0] != move:
            self.killer_moves[depth][1] = self.killer_moves[depth][0]
            self.killer_moves[depth][0] = move
    
    def update_history(self, move: chess.Move, depth: int, cutoff: bool):
        """Update history heuristic."""
        move_key = (move.from_square, move.to_square)
        bonus = depth * depth if cutoff else -depth
        
        if move_key not in self.history_scores:
            self.history_scores[move_key] = 0
        
        self.history_scores[move_key] += bonus
        
        # Prevent overflow
        if abs(self.history_scores[move_key]) > 1000000:
            self.history_scores[move_key] //= 2
    
    def update_counter_move(self, last_move: chess.Move, response: chess.Move):
        """Update counter moves."""
        self.counter_moves[last_move.uci()] = response

class AdvancedSearchEngine:
    """Advanced chess search engine with NegaScout and modern techniques."""
    
    def __init__(self, hash_size_mb: int = 64):
        """Initialize advanced search engine."""
        self.tt = AdvancedTranspositionTable(hash_size_mb)
        self.move_orderer = MoveOrderer()
        self.stats = SearchStats()
        
        # Search parameters
        self.contempt = 0  # Contempt factor in centipawns
        self.null_move_enabled = True
        self.null_move_reduction = 2
        self.quiescence_enabled = True
        self.max_quiescence_depth = 6
        
        # Principal variation
        self.pv_line: List[chess.Move] = []
        self.pv_table: Dict[int, List[chess.Move]] = {}
        
        # Time management
        self.search_start_time = 0
        self.max_search_time = 0
        self.time_up = False
        
    def negascout_search(self, board: chess.Board, depth: int, alpha: int, beta: int,
                        ply: int = 0, do_null: bool = True) -> Tuple[int, Optional[chess.Move]]:
        """
        NegaScout (Principal Variation Search) implementation.
        
        This is the modern standard for chess engines, providing optimal search
        with proper move ordering. It's a refinement of alpha-beta that searches
        the first (best) move with a full window and subsequent moves with null windows.
        """
        self.stats.nodes_searched += 1
        
        # Check for time limit
        if self.time_up or (self.max_search_time > 0 and 
                           time.time() - self.search_start_time > self.max_search_time):
            self.time_up = True
            return alpha, None
        
        # Initialize PV for this ply
        self.pv_table[ply] = []
        
        # Check for terminal positions
        if board.is_checkmate():
            return -30000 + ply, None  # Prefer shorter mates
        
        if board.is_stalemate() or board.is_insufficient_material():
            return self._contempt_score(), None
        
        # Check for threefold repetition
        if board.is_repetition():
            return self._contempt_score(), None
        
        # Quiescence search at leaf nodes
        if depth <= 0:
            if self.quiescence_enabled:
                return self.quiescence_search(board, alpha, beta, ply), None
            else:
                return self.evaluate_position(board), None
        
        # Transposition table lookup
        position_hash = self._position_hash(board)
        tt_entry = self.tt.lookup(position_hash)
        tt_move = None
        
        if tt_entry:
            self.stats.tt_hits += 1
            if tt_entry.depth >= depth:
                score = self._adjust_mate_score(tt_entry.score, ply)
                
                if tt_entry.node_type == NodeType.EXACT:
                    return score, chess.Move.from_uci(tt_entry.best_move) if tt_entry.best_move else None
                elif tt_entry.node_type == NodeType.LOWER_BOUND and score >= beta:
                    return score, chess.Move.from_uci(tt_entry.best_move) if tt_entry.best_move else None
                elif tt_entry.node_type == NodeType.UPPER_BOUND and score <= alpha:
                    return score, chess.Move.from_uci(tt_entry.best_move) if tt_entry.best_move else None
            
            if tt_entry.best_move:
                tt_move = chess.Move.from_uci(tt_entry.best_move)
        
        self.stats.tt_lookups += 1
        
        # Null move pruning
        if (do_null and self.null_move_enabled and depth >= 3 and 
            not board.is_check() and self._has_non_pawn_material(board) and
            not self._is_endgame(board)):
            
            # Make null move
            board.push(chess.Move.null())
            null_score, _ = self.negascout_search(board, depth - 1 - self.null_move_reduction, 
                                                 -beta, -beta + 1, ply + 1, False)
            board.pop()
            
            if -null_score >= beta:
                self.stats.null_cutoffs += 1
                return -null_score, None
        
        # Generate and order moves
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return -30000 + ply, None  # Checkmate
        
        ordered_moves = self.move_orderer.order_moves(
            board, legal_moves, depth, tt_move, 
            self.pv_line[ply] if ply < len(self.pv_line) else None
        )
        
        best_move = None
        best_score = -50000
        move_count = 0
        original_alpha = alpha
        node_type = NodeType.UPPER_BOUND
        
        for move in ordered_moves:
            board.push(move)
            move_count += 1
            
            if move_count == 1:
                # Full window search for first (best) move
                score, _ = self.negascout_search(board, depth - 1, -beta, -alpha, ply + 1)
                score = -score
            else:
                # Null window search for remaining moves
                score, _ = self.negascout_search(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                score = -score
                
                # Re-search with full window if null window failed high
                if alpha < score < beta:
                    score, _ = self.negascout_search(board, depth - 1, -beta, -score, ply + 1)
                    score = -score
            
            board.pop()
            
            if self.time_up:
                return best_score, best_move
            
            if score > best_score:
                best_score = score
                best_move = move
                
                # Update principal variation
                self.pv_table[ply] = [move] + self.pv_table.get(ply + 1, [])
                
                if score > alpha:
                    alpha = score
                    node_type = NodeType.EXACT
                    
                    if alpha >= beta:
                        # Beta cutoff
                        self.stats.cutoffs += 1
                        node_type = NodeType.LOWER_BOUND
                        
                        # Update move ordering heuristics
                        if not board.is_capture(move):
                            self.move_orderer.update_killers(depth, move)
                            if len(board.move_stack) > 0:
                                self.move_orderer.update_counter_move(board.move_stack[-1], move)
                        
                        self.move_orderer.update_history(move, depth, True)
                        break
            
            # Update history for non-cutoff moves
            if not board.is_capture(move):
                self.move_orderer.update_history(move, depth, False)
        
        # Store in transposition table
        if best_move:
            mate_adjusted_score = self._adjust_mate_score_for_storage(best_score, ply)
            self.tt.store(position_hash, depth, mate_adjusted_score, node_type, best_move.uci())
        
        return best_score, best_move
    
    def quiescence_search(self, board: chess.Board, alpha: int, beta: int, 
                         ply: int, qply: int = 0) -> int:
        """
        Quiescence search to avoid horizon effect.
        
        Searches all captures and checks until a quiet position is reached,
        ensuring tactical accuracy at the search boundary.
        """
        self.stats.qnodes_searched += 1
        
        # Check time limit
        if self.time_up or qply >= self.max_quiescence_depth:
            return self.evaluate_position(board)
        
        # Stand pat (current position evaluation)
        stand_pat = self.evaluate_position(board)
        
        if stand_pat >= beta:
            return beta
        
        if stand_pat > alpha:
            alpha = stand_pat
        
        # Generate tactical moves (captures, checks, promotions)
        tactical_moves = []
        for move in board.legal_moves:
            if (board.is_capture(move) or 
                move.promotion or
                (qply < 2 and self._gives_check(board, move))):
                tactical_moves.append(move)
        
        # Order tactical moves
        if tactical_moves:
            ordered_moves = self.move_orderer.order_moves(board, tactical_moves, 0)
            
            for move in ordered_moves:
                # Delta pruning for captures
                if board.is_capture(move) and qply > 0:
                    captured_piece = board.piece_at(move.to_square)
                    if captured_piece:
                        piece_value = self._piece_value(captured_piece.piece_type)
                        if stand_pat + piece_value + 200 < alpha:  # 200cp margin
                            continue
                
                board.push(move)
                score = -self.quiescence_search(board, -beta, -alpha, ply + 1, qply + 1)
                board.pop()
                
                if score >= beta:
                    return beta
                
                if score > alpha:
                    alpha = score
        
        return alpha
    
    def evaluate_position(self, board: chess.Board) -> int:
        """
        Evaluate position (placeholder for comprehensive evaluation).
        This will be enhanced with the modular evaluation system.
        """
        if board.is_checkmate():
            return -30000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return self._contempt_score()
        
        # Basic material evaluation
        material_score = self._evaluate_material(board)
        
        # Apply contempt factor
        score = material_score + self.contempt
        
        return score if board.turn else -score
    
    def _contempt_score(self) -> int:
        """Return contempt-adjusted draw score."""
        return self.contempt
    
    def _evaluate_material(self, board: chess.Board) -> int:
        """Basic material evaluation."""
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
        }
        
        score = 0
        for piece_type in piece_values:
            white_pieces = len(board.pieces(piece_type, chess.WHITE))
            black_pieces = len(board.pieces(piece_type, chess.BLACK))
            score += (white_pieces - black_pieces) * piece_values[piece_type]
        
        return score
    
    def _piece_value(self, piece_type: int) -> int:
        """Get piece value for calculations."""
        values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                 chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10000}
        return values.get(piece_type, 0)
    
    def _has_non_pawn_material(self, board: chess.Board) -> bool:
        """Check if side to move has non-pawn material."""
        color = board.turn
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if board.pieces(piece_type, color):
                return True
        return False
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Check if position is in endgame (limited material)."""
        # Simple endgame detection: few pieces remaining
        total_pieces = len(board.piece_map())
        return total_pieces <= 8  # Kings + 6 other pieces or fewer
    
    def _gives_check(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move gives check."""
        board.push(move)
        is_check = board.is_check()
        board.pop()
        return is_check
    
    def _position_hash(self, board: chess.Board) -> int:
        """Get position hash for transposition table."""
        return hash(board.fen().split()[0])  # Position only, not move counters
    
    def _adjust_mate_score(self, score: int, ply: int) -> int:
        """Adjust mate score from transposition table."""
        if score > 29000:
            return score - ply
        elif score < -29000:
            return score + ply
        return score
    
    def _adjust_mate_score_for_storage(self, score: int, ply: int) -> int:
        """Adjust mate score for transposition table storage."""
        if score > 29000:
            return score + ply
        elif score < -29000:
            return score - ply
        return score
    
    def set_contempt(self, contempt: int):
        """Set contempt factor in centipawns."""
        self.contempt = contempt
    
    def set_hash_size(self, size_mb: int):
        """Set transposition table size."""
        self.tt = AdvancedTranspositionTable(size_mb)
    
    def clear_hash(self):
        """Clear transposition table."""
        self.tt.clear()
    
    def get_pv(self) -> List[str]:
        """Get principal variation as UCI strings."""
        return [move.uci() for move in self.pv_table.get(0, [])]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            'nodes_searched': self.stats.nodes_searched,
            'qnodes_searched': self.stats.qnodes_searched,
            'tt_hits': self.stats.tt_hits,
            'tt_lookups': self.stats.tt_lookups,
            'cutoffs': self.stats.cutoffs,
            'null_cutoffs': self.stats.null_cutoffs,
            'hash_full': self.tt.get_hashfull()
        }
    
    def reset_stats(self):
        """Reset search statistics."""
        self.stats.reset()
        self.pv_table.clear()
        self.pv_line.clear()
