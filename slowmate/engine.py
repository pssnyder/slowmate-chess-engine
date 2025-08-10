"""
SlowMate Chess Engine        self.move_orderer = MoveOrderer()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 4  # Configurable via UCI option MaxDepth
        self.search_deadline = None
        self.last_score = None
        
    def new_game(self):Engine Interface
Version: 1.0.0-BETA
Based on stable v0.2.01 architecture
"""

import chess
import time
from typing import Optional, List, Tuple

from .core.board import Board
from .core.moves import MoveGenerator
from .core.evaluate import Evaluator
from .search.enhanced import TranspositionTable, MoveOrderer, NodeType
from .uci.protocol import UCIProtocol


class SlowMateEngine:
    """Main chess engine interface with enhanced search capabilities."""
    
    def __init__(self):
        """Initialize the chess engine."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.evaluator = Evaluator()
        self.tt = TranspositionTable()
        self.move_orderer = MoveOrderer()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 4  # Configurable via UCI option MaxDepth
        self.search_deadline = None
        self.last_score = None
        
    def new_game(self):
        """Reset the engine for a new game."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.tt = TranspositionTable()  # Clear transposition table
        self.move_orderer = MoveOrderer()  # Reset move ordering
        
    def set_position(self, position):
        """Set the board position."""
        if position == "startpos":
            self.board = Board()
        else:
            self.board.set_fen(position)
        self.move_generator = MoveGenerator(self.board)
        
    def make_move(self, move):
        """Make a move on the board."""
        self.board.make_move(move)
        
    def search(self, time_limit_ms: Optional[int] = None, depth_override: Optional[int] = None, *, time_limit: Optional[int] = None) -> Optional[chess.Move]:
        """Search for the best move using a fixed-depth alpha-beta (negamax) search.

        Parameters
        ----------
        time_limit : float | int
            Requested time budget in milliseconds (or seconds if > 1000). Currently
            this implementation uses a fixed depth (max_depth) and does not yet
            implement dynamic time allocation; the parameter is accepted for API
            compatibility and future iterative deepening/time management integration.

        Returns
        -------
        Optional[chess.Move]
            The selected best move, or None if no legal moves are available.

        Notes
        -----
        Future enhancement: Replace fixed-depth search with iterative deepening
        loop honoring time_limit and integrating aspiration windows plus time
        management heuristics. This docstring is added now to clarify the
        contract while that system is under development.
        """
        # Backward compatibility: some callers use time_limit (ms)
        if time_limit_ms is None and time_limit is not None:
            time_limit_ms = time_limit

        self.nodes = 0
        self.last_score = None
        alpha = -30000
        beta = 30000
        alpha_orig = alpha
        max_depth = depth_override if depth_override is not None else self.max_depth
        self.search_deadline = (time.time() + (time_limit_ms / 1000.0)) if time_limit_ms else None

        # Transposition table probe
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, max_depth, alpha, beta)
        tt_move = tt_entry[1] if tt_entry else None

        # Move ordering
        moves = self.move_generator.get_legal_moves()
        ordered_moves = self.move_orderer.order_moves(self.board.board, moves, max_depth, tt_move)

        best_move: Optional[chess.Move] = None
        best_score = -30000

        for move in ordered_moves:
            if self.uci.stop_requested:
                break
            self.board.make_move(move)
            score = -self._negamax(max_depth - 1, -beta, -alpha)
            self.board.unmake_move()

            if score > best_score:
                best_score = score
                best_move = move
                self.last_score = best_score
                alpha = max(alpha, score)

            if alpha >= beta:
                if not self.board.board.is_capture(move):
                    self.move_orderer.update_killer_move(move, max_depth)
                break

        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha_orig:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
            self.tt.store(pos_key, max_depth, int(best_score), node_type, best_move)

        return best_move
        
    def _negamax(self, depth: int, alpha: int, beta: int) -> int:
        """Enhanced negamax search with move ordering and transposition table."""
        self.nodes += 1
        alpha_orig = alpha
        
        # Check transposition table
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        if tt_entry:
            return tt_entry[0]
            
        # Time / stop check
        if self.uci.stop_requested:
            return 0
        if self.search_deadline and time.time() > self.search_deadline:
            self.uci.stop_requested = True
            return 0
        if depth == 0:
            return int(self.evaluator.evaluate(self.board))
            
        # Get ordered moves
        moves = self.move_generator.get_legal_moves()
        tt_move = tt_entry[1] if tt_entry else None
        ordered_moves = self.move_orderer.order_moves(
            self.board.board, moves, depth, tt_move)
            
        if not ordered_moves:
            if self.board.is_check():
                return -20000  # Checkmate
            return 0  # Stalemate
            
        best_score = -30000  # Instead of float('-inf')
        best_move = None
        
        # Search moves
        for move in ordered_moves:
            self.board.make_move(move)
            score = -self._negamax(depth - 1, -beta, -alpha)
            self.board.unmake_move()
            
            if score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, score)
                
            if alpha >= beta:
                # Store killer move and update history
                if not self.board.board.is_capture(move):
                    self.move_orderer.update_killer_move(move, depth)
                    self.move_orderer.update_history(move, depth)
                    
                # Store counter move
                if self.board.board.move_stack:
                    last_move = self.board.board.peek()
                    self.move_orderer.update_counter_move(last_move, move)
                break
                
        # Store position in transposition table
        if best_move:
            node_type = NodeType.EXACT
            if best_score <= alpha_orig:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
                
            self.tt.store(pos_key, depth, int(best_score), node_type, best_move)
            
        return best_score
