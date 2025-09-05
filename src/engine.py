"""
SlowMate Chess Engine v3.0 - Production Release
Comprehensive fix for evaluation perspective bug and competitive restoration
Target: Stable 650+ ELO with robust UCI compliance and reliable move generation
"""

import chess
import time
import math
from typing import Optional, List, Tuple, Dict, Any

from .core.board import Board
from .core.moves import MoveGenerator
from .core.enhanced_evaluate import EnhancedEvaluator
from .search.enhanced import TranspositionTable, MoveOrderer, NodeType
from .uci.protocol_v2_2 import UCIProtocol


class SlowMateEngine:
    """SlowMate v3.0 - Production Release with Critical Bug Fixes."""
    
    def __init__(self):
        """Initialize the production chess engine."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.evaluator = EnhancedEvaluator()
        self.tt = TranspositionTable(size_mb=64)
        self.move_orderer = MoveOrderer()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 6
        self.search_deadline = None
        self.last_score = None
        self.start_time = None
        self.current_pv = []  # Principal variation line
        
        # v3.0: Advanced search parameters
        self.aspiration_window = 50
        self.null_move_reduction = 2
        self.late_move_reduction_threshold = 4
        self.quiescence_max_depth = 4
        
        # v3.0: History and killer move management
        self.history_table = {}
        self.killer_moves = [[] for _ in range(20)]
        self.counter_moves = {}
        
        # v3.0: Time management improvements
        self.time_scaling_factor = 1.0
        self.complexity_bonus = 0.0
        
    def get_version(self) -> str:
        """Return engine version."""
        return "3.0"
        
    def new_game(self):
        """Reset the engine for a new game."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.tt = TranspositionTable(size_mb=64)
        self.move_orderer = MoveOrderer()
        self.nodes = 0
        self.last_score = None
        
        # Clear history tables
        self.history_table.clear()
        self.killer_moves = [[] for _ in range(20)]
        self.counter_moves.clear()
        
    def set_position(self, position: str):
        """Set the board position."""
        if position == "startpos":
            self.board = Board()
        else:
            self.board.set_fen(position)
        self.move_generator = MoveGenerator(self.board)
        
    def make_move(self, move: chess.Move):
        """Make a move on the board."""
        if move not in self.move_generator.get_legal_moves():
            raise ValueError(f"Illegal move: {move.uci()}")
        self.board.make_move(move)
        
    def search(self, time_limit_ms: Optional[int] = None, depth_override: Optional[int] = None, *,
             wtime: Optional[int] = None, btime: Optional[int] = None,
             winc: Optional[int] = None, binc: Optional[int] = None,
             moves_to_go: Optional[int] = None) -> Optional[chess.Move]:
        """
        Search for the best move using iterative deepening with enhanced time management.
        
        Returns:
            The best move found, or None if no legal moves available
        """
        self.nodes = 0
        self.last_score = None
        self.start_time = time.time()
        self.uci.stop_requested = False
        
        # Calculate time allocation
        allocated_time = self._calculate_time_allocation(
            wtime, btime, winc, binc, moves_to_go, time_limit_ms
        )
        self.search_deadline = self.start_time + allocated_time
        
        try:
            self.uci._out(f"info string SlowMate v3.0 - Allocated time: {allocated_time:.3f}s")
        except Exception:
            pass
        
        # Get legal moves
        moves = self.move_generator.get_legal_moves()
        if not moves:
            return None
            
        best_move = moves[0]  # Fallback move
        best_score = -30000
        
        # Determine search depth
        max_depth = depth_override if depth_override else self.max_depth
        if allocated_time >= 10:
            max_depth = max(max_depth, 8)
        elif allocated_time >= 5:
            max_depth = max(max_depth, 7)
        
        # Iterative deepening search
        for current_depth in range(1, max_depth + 1):
            if self.uci.stop_requested:
                break
                
            alpha = -30000
            beta = 30000
            
            # Aspiration windows for deeper searches
            if current_depth >= 4 and self.last_score is not None:
                alpha = self.last_score - self.aspiration_window
                beta = self.last_score + self.aspiration_window
            
            iteration_best_move, iteration_best_score, iteration_pv = self._search_depth_with_pv(
                current_depth, alpha, beta, moves
            )
            
            # Handle aspiration window failures
            if (iteration_best_score <= alpha or iteration_best_score >= beta) and current_depth >= 4:
                # Widen window and re-search
                alpha = -30000
                beta = 30000
                iteration_best_move, iteration_best_score, iteration_pv = self._search_depth_with_pv(
                    current_depth, alpha, beta, moves
                )
            
            # Update best move if iteration completed
            if not self.uci.stop_requested and iteration_best_move:
                best_move = iteration_best_move
                best_score = iteration_best_score
                self.current_pv = iteration_pv
                self.last_score = best_score
                
                try:
                    elapsed = time.time() - self.start_time
                    nps = int(self.nodes / max(elapsed, 0.001))
                    pv_string = " ".join([move.uci() for move in self.current_pv])
                    self.uci._out(
                        f"info depth {current_depth} score cp {best_score} "
                        f"nodes {self.nodes} nps {nps} time {int(elapsed * 1000)} "
                        f"pv {pv_string}"
                    )
                except Exception:
                    pass
            
            # Time management: check if we should continue
            elapsed = time.time() - self.start_time
            if elapsed >= allocated_time * 0.8:  # Use 80% of allocated time
                break
                
        return best_move
    
    def _calculate_time_allocation(self, wtime: Optional[int], btime: Optional[int],
                                 winc: Optional[int], binc: Optional[int],
                                 moves_to_go: Optional[int], 
                                 time_limit_ms: Optional[int]) -> float:
        """Calculate optimal time allocation for the current move."""
        if time_limit_ms:
            return time_limit_ms / 1000.0
            
        # Default allocation if no time controls provided
        if not wtime and not btime:
            return 2.0
            
        # Get our remaining time and increment
        our_time = wtime if self.board.board.turn == chess.WHITE else btime
        our_inc = winc if self.board.board.turn == chess.WHITE else binc
        
        if not our_time:
            return 2.0
            
        our_time /= 1000.0  # Convert to seconds
        our_inc = (our_inc or 0) / 1000.0
        
        # Estimate moves remaining
        game_length = len(self.board.board.move_stack)
        estimated_moves_remaining = max(40 - game_length // 2, 15)
        
        if moves_to_go:
            estimated_moves_remaining = min(estimated_moves_remaining, moves_to_go)
        
        # Basic time allocation: divide remaining time by estimated moves
        base_time = our_time / estimated_moves_remaining + our_inc * 0.8
        
        # Complexity adjustments
        position_complexity = self._evaluate_position_complexity()
        if position_complexity > 0.7:
            base_time *= 1.5  # Spend more time on complex positions
        elif position_complexity < 0.3:
            base_time *= 0.8  # Spend less time on simple positions
            
        # Ensure minimum and maximum bounds
        base_time = max(0.1, min(base_time, our_time * 0.1))
        
        return base_time
    
    def _evaluate_position_complexity(self) -> float:
        """Evaluate the complexity of the current position (0.0 to 1.0)."""
        board = self.board.board
        complexity = 0.0
        
        # Material on board
        total_material = sum(len(board.pieces(piece_type, color)) 
                           for piece_type in chess.PIECE_TYPES 
                           for color in chess.COLORS)
        complexity += min(total_material / 32.0, 1.0) * 0.3
        
        # Number of legal moves
        legal_moves = len(list(board.legal_moves))
        complexity += min(legal_moves / 40.0, 1.0) * 0.4
        
        # Checks and tactics
        if board.is_check():
            complexity += 0.2
        if any(board.is_capture(move) for move in board.legal_moves):
            complexity += 0.1
            
        return min(complexity, 1.0)
    
    def _search_depth_with_pv(self, depth: int, alpha: int, beta: int, 
                             moves: List[chess.Move]) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """Search all moves at a given depth and collect principal variation."""
        best_move = None
        best_score = -30000
        best_pv = []
        
        # Order moves for better alpha-beta pruning
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        tt_move = tt_entry[1] if tt_entry else None
        
        ordered_moves = self.move_orderer.order_moves(
            self.board.board, moves, depth, tt_move,
            use_killer=True, prioritize_captures=True
        )
        
        for i, move in enumerate(ordered_moves):
            if self.uci.stop_requested:
                break
                
            # Validate move legality
            if move not in moves:
                continue
                
            self.board.make_move(move)
            
            # Late move reduction for non-critical moves
            reduction = 0
            if (depth >= 3 and i >= self.late_move_reduction_threshold 
                and not self.board.board.is_check() 
                and not self.board.board.is_capture(move)):
                reduction = 1
            
            score, child_pv = self._negamax_with_pv(depth - 1 - reduction, -beta, -alpha)
            score = -score
            
            # Re-search if reduction failed high
            if reduction > 0 and score > alpha:
                score, child_pv = self._negamax_with_pv(depth - 1, -beta, -alpha)
                score = -score
            
            self.board.unmake_move()
            
            if score > best_score:
                best_score = score
                best_move = move
                best_pv = [move] + child_pv
                alpha = max(alpha, score)
                
            if alpha >= beta:
                # Update killer moves and history
                if not self.board.board.is_capture(move):
                    self._update_killer_move(move, depth)
                    self._update_history(move, depth)
                break
                
        # Store in transposition table
        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
            self.tt.store(pos_key, depth, best_score, node_type, best_move)
            
        return best_move, best_score, best_pv

    def _search_depth(self, depth: int, alpha: int, beta: int, 
                     moves: List[chess.Move]) -> Tuple[Optional[chess.Move], int]:
        """Search all moves at a given depth."""
        best_move = None
        best_score = -30000
        
        # Order moves for better alpha-beta pruning
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        tt_move = tt_entry[1] if tt_entry else None
        
        ordered_moves = self.move_orderer.order_moves(
            self.board.board, moves, depth, tt_move,
            use_killer=True, prioritize_captures=True
        )
        
        for i, move in enumerate(ordered_moves):
            if self.uci.stop_requested:
                break
                
            # Validate move legality
            if move not in moves:
                continue
                
            self.board.make_move(move)
            
            # Late move reduction for non-critical moves
            reduction = 0
            if (depth >= 3 and i >= self.late_move_reduction_threshold 
                and not self.board.board.is_check() 
                and not self.board.board.is_capture(move)):
                reduction = 1
            
            score = -self._negamax(depth - 1 - reduction, -beta, -alpha)
            
            # Re-search if reduction failed high
            if reduction > 0 and score > alpha:
                score = -self._negamax(depth - 1, -beta, -alpha)
            
            self.board.unmake_move()
            
            if score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, score)
                
            if alpha >= beta:
                # Update killer moves and history
                if not self.board.board.is_capture(move):
                    self._update_killer_move(move, depth)
                    self._update_history(move, depth)
                break
                
        # Store in transposition table
        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
            self.tt.store(pos_key, depth, best_score, node_type, best_move)
            
        return best_move, best_score
    
    def _negamax_with_pv(self, depth: int, alpha: int, beta: int) -> Tuple[int, List[chess.Move]]:
        """Enhanced negamax search with principal variation collection."""
        self.nodes += 1
        
        # Time management check
        if self.uci.stop_requested:
            return 0, []
        if self.search_deadline and time.time() > self.search_deadline:
            self.uci.stop_requested = True
            return 0, []
            
        # Transposition table lookup
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        if tt_entry:
            return tt_entry[0], []
            
        # Quiescence search at leaf nodes
        if depth <= 0:
            return self._quiescence_search(alpha, beta, self.quiescence_max_depth), []
            
        # Null move pruning
        if (depth >= 3 and not self.board.board.is_check() 
            and self._has_non_pawn_material()):
            self.board.board.push(chess.Move.null())
            null_score, _ = self._negamax_with_pv(depth - 1 - self.null_move_reduction, -beta, -alpha)
            null_score = -null_score
            self.board.board.pop()
            
            if null_score >= beta:
                return beta, []
        
        # Get and order moves
        moves = self.move_generator.get_legal_moves()
        if not moves:
            if self.board.board.is_check():
                return -20000 + self.nodes, []  # Checkmate (prefer shorter mates)
            return 0, []  # Stalemate
            
        tt_move = tt_entry[1] if tt_entry else None
        ordered_moves = self.move_orderer.order_moves(
            self.board.board, moves, depth, tt_move
        )
        
        best_score = -30000
        best_move = None
        best_pv = []
        
        for i, move in enumerate(ordered_moves):
            if self.uci.stop_requested:
                break
                
            # Check extension
            extension = 0
            if self.board.board.is_check():
                extension = 1
                
            self.board.make_move(move)
            score, child_pv = self._negamax_with_pv(depth - 1 + extension, -beta, -alpha)
            score = -score
            self.board.unmake_move()
            
            if score > best_score:
                best_score = score
                best_move = move
                best_pv = [move] + child_pv
                alpha = max(alpha, score)
                
            if alpha >= beta:
                # Update move ordering data
                if not self.board.board.is_capture(move):
                    self._update_killer_move(move, depth)
                    self._update_history(move, depth)
                break
                
        # Store in transposition table
        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
            self.tt.store(pos_key, depth, best_score, node_type, best_move)
            
        return best_score, best_pv

    def _negamax(self, depth: int, alpha: int, beta: int) -> int:
        """Enhanced negamax search with pruning and extensions."""
        self.nodes += 1
        
        # Time management check
        if self.uci.stop_requested:
            return 0
        if self.search_deadline and time.time() > self.search_deadline:
            self.uci.stop_requested = True
            return 0
            
        # Transposition table lookup
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        if tt_entry:
            return tt_entry[0]
            
        # Quiescence search at leaf nodes
        if depth <= 0:
            return self._quiescence_search(alpha, beta, self.quiescence_max_depth)
            
        # Null move pruning
        if (depth >= 3 and not self.board.board.is_check() 
            and self._has_non_pawn_material()):
            self.board.board.push(chess.Move.null())
            null_score = -self._negamax(depth - 1 - self.null_move_reduction, -beta, -alpha)
            self.board.board.pop()
            
            if null_score >= beta:
                return beta
        
        # Get and order moves
        moves = self.move_generator.get_legal_moves()
        if not moves:
            if self.board.board.is_check():
                return -20000 + self.nodes  # Checkmate (prefer shorter mates)
            return 0  # Stalemate
            
        tt_move = tt_entry[1] if tt_entry else None
        ordered_moves = self.move_orderer.order_moves(
            self.board.board, moves, depth, tt_move
        )
        
        best_score = -30000
        best_move = None
        
        for i, move in enumerate(ordered_moves):
            if self.uci.stop_requested:
                break
                
            # Check extension
            extension = 0
            if self.board.board.is_check():
                extension = 1
                
            self.board.make_move(move)
            score = -self._negamax(depth - 1 + extension, -beta, -alpha)
            self.board.unmake_move()
            
            if score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, score)
                
            if alpha >= beta:
                # Update move ordering data
                if not self.board.board.is_capture(move):
                    self._update_killer_move(move, depth)
                    self._update_history(move, depth)
                break
                
        # Store in transposition table
        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
            self.tt.store(pos_key, depth, best_score, node_type, best_move)
            
        return best_score
    
    def _quiescence_search(self, alpha: int, beta: int, depth: int) -> int:
        """Quiescence search to avoid horizon effect."""
        self.nodes += 1
        
        # Evaluate current position
        stand_pat = int(self.evaluator.evaluate(self.board))
        
        if depth <= 0 or stand_pat >= beta:
            return stand_pat
            
        alpha = max(alpha, stand_pat)
        
        # Only consider captures in quiescence
        moves = [move for move in self.move_generator.get_legal_moves() 
                if self.board.board.is_capture(move)]
        
        if not moves:
            return stand_pat
            
        # Order captures by SEE (Static Exchange Evaluation)
        moves.sort(key=lambda m: self._see_capture_value(m), reverse=True)
        
        for move in moves:
            if self.uci.stop_requested:
                break
                
            # Delta pruning: skip captures that can't improve alpha
            capture_value = self._see_capture_value(move)
            if stand_pat + capture_value + 200 < alpha:  # 200cp margin
                continue
                
            self.board.make_move(move)
            score = -self._quiescence_search(-beta, -alpha, depth - 1)
            self.board.unmake_move()
            
            if score >= beta:
                return beta
            alpha = max(alpha, score)
            
        return alpha
    
    def _see_capture_value(self, move: chess.Move) -> int:
        """Static Exchange Evaluation for captures."""
        board = self.board.board
        if not board.is_capture(move):
            return 0
            
        captured_piece = board.piece_at(move.to_square)
        if not captured_piece:
            return 0
            
        return self.evaluator.piece_values.get(captured_piece.piece_type, 0)
    
    def _has_non_pawn_material(self) -> bool:
        """Check if current side has non-pawn material."""
        board = self.board.board
        our_color = board.turn
        
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if board.pieces(piece_type, our_color):
                return True
        return False
    
    def _update_killer_move(self, move: chess.Move, depth: int):
        """Update killer move table."""
        if depth < len(self.killer_moves):
            killers = self.killer_moves[depth]
            if move not in killers:
                killers.insert(0, move)
                if len(killers) > 2:  # Keep only 2 killer moves per depth
                    killers.pop()
    
    def _update_history(self, move: chess.Move, depth: int):
        """Update history heuristic."""
        key = (move.from_square, move.to_square)
        if key not in self.history_table:
            self.history_table[key] = 0
        self.history_table[key] += depth * depth  # Depth squared bonus
    
    def get_best_move(self) -> Optional[chess.Move]:
        """Get the best move from the last search."""
        return self.search()
    
    def get_evaluation(self) -> Optional[int]:
        """Get the evaluation from the last search."""
        return self.last_score
    
    def get_info(self) -> Dict[str, Any]:
        """Get engine information."""
        return {
            'name': 'SlowMate',
            'version': '3.0',
            'author': 'SlowMate Team',
            'nodes': self.nodes,
            'evaluation': self.last_score,
            'tt_size': self.tt.size,
            'tt_entries': len(self.tt.table)
        }
