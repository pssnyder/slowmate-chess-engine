"""
SlowMate Chess Engine v2.1 - Emergency Stabilization
Critical bug fixes to restore competitive functionality
Rollback to proven v1.0 architecture with essential fixes
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
    """Main chess engine interface - v2.1 Emergency Stabilization."""
    
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
    
    def _validate_move_legal(self, move) -> bool:
        """CRITICAL FIX: Strict move validation to prevent illegal moves."""
        try:
            legal_moves = list(self.board.board.legal_moves)
            if move not in legal_moves:
                try:
                    self.uci._out(f"info string ILLEGAL MOVE BLOCKED: {move.uci()}")
                except:
                    pass  # Fail silently if UCI unavailable
                return False
            return True
        except Exception as e:
            try:
                self.uci._out(f"info string MOVE_VALIDATION_ERROR: {e}")
            except:
                pass
            return False
        
    def search(self, time_limit_ms: Optional[int] = None, depth_override: Optional[int] = None, **kwargs) -> Optional[chess.Move]:
        """EMERGENCY FIX: Rollback to v1.0 stable search architecture.
        
        This is a simplified, stable search that prioritizes reliability over features.
        Complex v2.0 features (time management, iterative deepening) removed to restore functionality.
        
        Parameters
        ----------
        time_limit_ms : Optional[int]
            Time limit in milliseconds (simplified from v2.0 complex time management)
        depth_override : Optional[int]
            Optional fixed depth limit
            
        Returns
        -------
        Optional[chess.Move]
            The selected best move, or None if no legal moves are available
        """
        try:
            # CRITICAL FIX: Simplified time management (rollback from v2.0 complexity)
            if time_limit_ms is None:
                time_limit_ms = 5000  # Default 5 seconds - stable fallback
            
            self.nodes = 0
            self.last_score = None
            alpha = -30000
            beta = 30000
            alpha_orig = alpha
            max_depth = depth_override if depth_override is not None else self.max_depth
            self.search_deadline = time.time() + (time_limit_ms / 1000.0)

            # Get legal moves with validation
            moves = self.move_generator.get_legal_moves()
            if not moves:
                return None
                
            # CRITICAL FIX: Emergency fallback move (prevent returning None)
            emergency_fallback = moves[0] if moves else None
            
            # Transposition table probe (keep this - it's stable)
            pos_key = hash(self.board.get_fen())
            tt_entry = self.tt.lookup(pos_key, max_depth, alpha, beta)
            tt_move = tt_entry[1] if tt_entry else None

            # Move ordering (keep this - it's beneficial and stable)
            ordered_moves = self.move_orderer.order_moves(self.board.board, moves, max_depth, tt_move)

            best_move: Optional[chess.Move] = emergency_fallback  # Always have a fallback
            best_score = -30000

            # SIMPLIFIED SEARCH: Return to v1.0 architecture (no complex iterative deepening)
            for move in ordered_moves:
                # CRITICAL FIX: Strict move validation before making
                if not self._validate_move_legal(move):
                    continue  # Skip any illegal moves
                    
                if self.uci.stop_requested:
                    break
                    
                # Time check (simplified)
                if self.search_deadline and time.time() > self.search_deadline:
                    self.uci.stop_requested = True
                    break
                
                try:
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
                        
                except Exception as e:
                    # CRITICAL FIX: Handle any search errors gracefully
                    try:
                        self.uci._out(f"info string SEARCH_ERROR: {e}")
                        # Try to unmake move if it was made
                        self.board.unmake_move()
                    except:
                        pass  # Fail silently
                    continue

            # Store in transposition table (keep this - it's stable)
            if best_move:
                try:
                    node_type = NodeType.EXACT
                    if best_score <= alpha_orig:
                        node_type = NodeType.UPPER
                    elif best_score >= beta:
                        node_type = NodeType.LOWER
                    self.tt.store(pos_key, max_depth, int(best_score), node_type, best_move)
                except:
                    pass  # Fail silently if TT storage fails

            # CRITICAL FIX: Always return a legal move
            if best_move is None:
                best_move = emergency_fallback
                
            # Final validation of returned move
            if best_move and not self._validate_move_legal(best_move):
                # Last resort: return first legal move
                legal_moves = list(self.board.board.legal_moves)
                best_move = legal_moves[0] if legal_moves else None

            return best_move
            
        except Exception as e:
            # CRITICAL FIX: Emergency exception handling
            try:
                self.uci._out(f"info string CRITICAL_SEARCH_ERROR: {e}")
                # Return emergency fallback
                legal_moves = list(self.board.board.legal_moves)
                return legal_moves[0] if legal_moves else None
            except:
                return None
        
    def _negamax(self, depth: int, alpha: int, beta: int) -> int:
        """STABLE: v1.0 negamax implementation (proven to work)."""
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
            # CRITICAL FIX: Add move validation in negamax too
            if not self._validate_move_legal(move):
                continue
                
            try:
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
                    
            except Exception as e:
                # CRITICAL FIX: Handle move/unmake errors gracefully
                try:
                    self.board.unmake_move()
                except:
                    pass
                continue
                
        # Store position in transposition table
        if best_move:
            try:
                node_type = NodeType.EXACT
                if best_score <= alpha_orig:
                    node_type = NodeType.UPPER
                elif best_score >= beta:
                    node_type = NodeType.LOWER
                    
                self.tt.store(pos_key, depth, int(best_score), node_type, best_move)
            except:
                pass  # Fail silently if TT storage fails
                
        return best_score
