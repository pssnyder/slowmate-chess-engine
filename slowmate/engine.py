"""
SlowMate Chess Engine        self.move_orderer = MoveOrderer()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 4  # Config            # Time management checks
        if self.uci.stop_requested:
            return 0
        
        if self.search_deadline:
            elapsed = time.time() - self.start_time
            if self.time_manager.should_stop(self.nodes, elapsed):
                self.uci.stop_requested = True
                return 0 via UCI option MaxDepth
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
from .core.time_manager import TimeManager
from .core.opening_book import OpeningBook
from .core.tablebase import Tablebase
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
        self.time_manager = TimeManager()
        self.opening_book = OpeningBook()
        self.tablebase = Tablebase()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 4  # Configurable via UCI option MaxDepth
        self.search_deadline = None
        self.last_score = None
        self.start_time = None  # Track search start time
        
    def new_game(self):
        """Reset the engine for a new game."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.tt = TranspositionTable()  # Clear transposition table
        self.move_orderer = MoveOrderer()  # Reset move ordering
        self.time_manager.start_new_game()  # Reset time management
        
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
        
    def search(self, time_limit_ms: Optional[int] = None, depth_override: Optional[int] = None, *,
             wtime: Optional[int] = None, btime: Optional[int] = None,
             winc: Optional[int] = None, binc: Optional[int] = None,
             moves_to_go: Optional[int] = None) -> Optional[chess.Move]:
        # Endgame tablebase integration
        fen = self.board.board.fen()
        tablebase_move = self.tablebase.select_tablebase_move(fen)
        if tablebase_move:
            return chess.Move.from_uci(tablebase_move)
        # Opening book integration
        book_move = self.opening_book.select_book_move(fen)
        if book_move:
            return chess.Move.from_uci(book_move)
        # Restore dynamic time management
        is_white = self.board.board.turn
        self.start_time = time.time()
        self.time_manager.set_time_controls(wtime, btime, winc, binc, moves_to_go, is_white)
        allocated_time = self.time_manager.calculate_move_time(
            self.board.board,
            len(self.board.board.move_stack)
        )
        self.search_deadline = self.start_time + allocated_time
        try:
            self.uci._out(f"info string ALLOCATED_TIME {allocated_time:.3f}")
            self.uci._out("info string START_SEARCH")
        except Exception:
            pass
        """Search for the best move using iterative deepening with time management.

        Parameters
        ----------
        time_limit_ms : Optional[int]
            Optional fixed time limit in milliseconds (deprecated)
        depth_override : Optional[int]
            Optional fixed depth limit
        wtime : Optional[int]
            White's remaining time in milliseconds
        btime : Optional[int]
            Black's remaining time in milliseconds
        winc : Optional[int]
            White's increment in milliseconds
        binc : Optional[int]
            Black's increment in milliseconds
        moves_to_go : Optional[int]
            Number of moves until next time control

        Returns
        -------
        Optional[chess.Move]
            The selected best move, or None if no legal moves are available
        """
        self.nodes = 0
        self.last_score = None
        self.start_time = time.time()

        # Set up time management and initial depth
        # Ignore all time controls and force a fixed minimum search time for every move (2 seconds)
        allocated_time = 2.0
        self.search_deadline = self.start_time + allocated_time
        try:
            self.uci._out(f"info string ALLOCATED_TIME {allocated_time:.3f}")
            self.uci._out("info string START_SEARCH")
        except Exception:
            pass

        # Start timing from here
        self.start_time = time.time()

        # Initialize search parameters
        alpha = -30000
        beta = 30000
        alpha_orig = alpha

        # Set up iterative deepening
        if depth_override is not None:
            max_depth = depth_override
        else:
            max_depth = self.max_depth
            if wtime is not None or btime is not None:
                # Scale depth with time
                allocated_time = self.time_manager.allocated_time
                if allocated_time >= 10:
                    max_depth = max(max_depth, 6)
                elif allocated_time >= 5:
                    max_depth = max(max_depth, 5)
                else:
                    max_depth = 4
        
        best_move: Optional[chess.Move] = None
        best_score = -30000
        
        # Get legal moves
        moves = self.move_generator.get_legal_moves()
        if not moves:
            return None
            
        # Set initial best move in case we need to stop early
        best_move = moves[0]
        
        # Iterative deepening loop
        for current_depth in range(2, max_depth + 1):
            self.uci._out("info string ===START ITERATION===")
            alpha = -30000
            beta = 30000
            iteration_start = time.time()
            pos_key = hash(self.board.get_fen())
            tt_entry = self.tt.lookup(pos_key, current_depth, alpha, beta)
            tt_move = tt_entry[1] if tt_entry else None
            # Improved move ordering
            ordered_moves = self.move_orderer.order_moves(
                self.board.board,
                moves,
                current_depth,
                tt_move,
                use_killer=True,
                prioritize_captures=True
            )
            stable_iteration = True
            iteration_best_move = None
            iteration_best_score = -30000
            for move in ordered_moves:
                if self.uci.stop_requested:
                    break
                # Null move pruning: skip obviously bad moves if current_depth > 2
                if current_depth > 2 and not self.board.board.is_capture(move):
                    self.board.make_move(move)
                    null_score = -self._negamax(current_depth - 2, -beta, -alpha)
                    self.board.unmake_move()
                    if null_score >= beta:
                        continue
                # Validate move before making
                if move not in self.move_generator.get_legal_moves():
                    self.uci._out(f"info string ILLEGAL MOVE DETECTED: {move.uci()}")
                    continue
                self.board.make_move(move)
                score = -self._negamax(current_depth - 1, -beta, -alpha)
                self.board.unmake_move()
                
                elapsed = time.time() - self.start_time
                if elapsed >= self.time_manager.allocated_time * 1.2:
                    self.uci.stop_requested = True
                    break
                
                if score > iteration_best_score:
                    iteration_best_score = score
                    iteration_best_move = move
                    stable_iteration = (move == best_move)
                    alpha = max(alpha, score)
                
                if alpha >= beta:
                    if not self.board.board.is_capture(move):
                        self.move_orderer.update_killer_move(move, current_depth)
                    break
                
            # Update best move if this iteration completed
            if not self.uci.stop_requested and iteration_best_move:
                best_move = iteration_best_move
                best_score = iteration_best_score
                self.last_score = best_score
                
                # Store in transposition table and log progress
                node_type = NodeType.EXACT
                if best_score <= alpha_orig:
                    node_type = NodeType.UPPER
                elif best_score >= beta:
                    node_type = NodeType.LOWER
                self.tt.store(pos_key, current_depth, int(best_score), node_type, best_move)
                
                    # Log detailed iteration stats
                total_time = time.time() - self.start_time
                self.uci._out(
                    f"info string >>>STATS<<<\n"
                    f"info string Depth: {current_depth}\n"
                    f"info string Score: {best_score}\n"
                    f"info string Total time: {total_time:.3f}s\n"
                    f"info string Allocated time: {self.time_manager.allocated_time:.3f}s\n"
                    f"info string Move: {best_move.uci()}\n"
                    f"info string <<<STATS>>>"
                )
            
            # Check time management
            elapsed = time.time() - self.start_time
            if self.uci.stop_requested:
                break
                
            # Minimum search time based on allocated time
            if self.time_manager.allocated_time > 0:
                min_time = min(1.0, self.time_manager.allocated_time * 0.2)
                if elapsed < min_time:
                    continue  # Force minimum search time
                    
            # Check if we should continue or stop
            allocated = self.time_manager.allocated_time
            if allocated > 0 and elapsed >= allocated:
                if stable_iteration or current_depth >= 5:
                    self.uci._out(f"info string Stopping search: stable={stable_iteration}, depth={current_depth}")
                    break
        
        # Wait until allocated search time has elapsed
        while time.time() - self.start_time < allocated_time:
            time.sleep(0.01)
        # Final timing report
        total_time = time.time() - self.start_time
        self.uci._out(
            f"info string >>>FINAL STATS<<<\n"
            f"info string Total time: {total_time:.3f}s\n"
            f"info string Allocated time: {allocated_time:.3f}s\n"
            f"info string Last depth: {current_depth}\n"
            f"info string Nodes: {self.nodes}\n"
            f"info string <<<FINAL STATS>>>"
        )
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
