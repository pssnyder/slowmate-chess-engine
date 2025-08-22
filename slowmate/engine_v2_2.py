"""
SlowMate Chess Engine v2.2 - Competitive Restoration
Enhanced search algorithms and evaluation to beat V7P3R v4.1 (711 ELO)
Target: 650-750 ELO range with systematic improvements
"""

import chess
import time
import math
from typing import Optional, List, Tuple, Dict

from .core.board import Board
from .core.moves import MoveGenerator
from .core.enhanced_evaluate import EnhancedEvaluator
from .search.enhanced import TranspositionTable, MoveOrderer, NodeType
from .uci.protocol_v2_2 import UCIProtocol


class SlowMateEngine:
    """SlowMate v2.2 - Competitive Restoration with Enhanced Search & Evaluation."""
    
    def __init__(self):
        """Initialize the enhanced chess engine."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.evaluator = EnhancedEvaluator()
        self.tt = TranspositionTable(size_mb=64)  # Larger hash table
        self.move_orderer = MoveOrderer()
        self.uci = UCIProtocol(self)
        self.nodes = 0
        self.max_depth = 6  # Increased from v2.1's 4
        self.search_deadline = None
        self.last_score = None
        self.start_time = None
        
        # v2.2 ENHANCEMENTS: Advanced search parameters
        self.aspiration_window = 50  # Centipawns
        self.null_move_reduction = 2  # Depth reduction for null move
        self.late_move_reduction_threshold = 4  # When to start LMR
        self.quiescence_max_depth = 4  # Maximum quiescence search depth
        
        # v2.2 ENHANCEMENTS: History and killer move tables
        self.history_table = {}  # [from_square][to_square] -> score
        self.killer_moves = [[] for _ in range(20)]  # Killer moves by depth
        self.counter_moves = {}  # last_move -> counter_move
        
        # v2.2 ENHANCEMENTS: Position complexity tracking
        self.position_complexity = 0
        self.critical_position = False
        
        # v2.2 ENHANCEMENTS: Performance tracking
        self.search_info = {
            'nodes_searched': 0,
            'tt_hits': 0,
            'null_move_cutoffs': 0,
            'late_move_reductions': 0
        }
        
    def new_game(self):
        """Reset the engine for a new game."""
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.tt = TranspositionTable(size_mb=64)  # Fresh hash table
        self.move_orderer = MoveOrderer()
        
        # Reset v2.2 enhancement tables
        self.history_table = {}
        self.killer_moves = [[] for _ in range(20)]
        self.counter_moves = {}
        self.search_info = {
            'nodes_searched': 0,
            'tt_hits': 0,
            'null_move_cutoffs': 0,
            'late_move_reductions': 0
        }
        
    def set_position(self, position):
        """Set the board position."""
        if position == "startpos":
            self.board = Board()
        else:
            self.board.set_fen(position)
        self.move_generator = MoveGenerator(self.board)
        self._analyze_position_complexity()
        
    def make_move(self, move):
        """Make a move on the board."""
        self.board.make_move(move)
        self._analyze_position_complexity()
    
    def _analyze_position_complexity(self):
        """v2.2 ENHANCEMENT: Analyze position complexity for time management."""
        try:
            legal_moves = list(self.board.board.legal_moves)
            num_legal_moves = len(legal_moves)
            
            # Count tactical elements
            captures = sum(1 for move in legal_moves if self.board.board.is_capture(move))
            checks = sum(1 for move in legal_moves if self.board.board.gives_check(move))
            
            # Piece activity (simplified)
            piece_count = len(self.board.board.piece_map())
            
            # Calculate complexity score
            self.position_complexity = (
                num_legal_moves * 2 +
                captures * 5 +
                checks * 3 +
                max(0, piece_count - 10) * 2
            )
            
            # Mark as critical if high complexity
            self.critical_position = (
                self.position_complexity > 60 or
                captures > 3 or
                checks > 2 or
                self.board.is_check()
            )
            
        except Exception:
            self.position_complexity = 30  # Default complexity
            self.critical_position = False
    
    def _validate_move_legal(self, move) -> bool:
        """Strict move validation to prevent illegal moves."""
        try:
            legal_moves = list(self.board.board.legal_moves)
            if move not in legal_moves:
                try:
                    self.uci._out(f"info string ILLEGAL MOVE BLOCKED: {move.uci()}")
                except:
                    pass
                return False
            return True
        except Exception as e:
            try:
                self.uci._out(f"info string MOVE_VALIDATION_ERROR: {e}")
            except:
                pass
            return False
    
    def _calculate_time_allocation(self, time_limit_ms: Optional[int], **kwargs) -> float:
        """v2.2 ENHANCEMENT: Advanced time management with position complexity."""
        base_time = time_limit_ms / 1000.0 if time_limit_ms else 3.0
        
        # Extract time control parameters
        wtime = kwargs.get('wtime', 0)
        btime = kwargs.get('btime', 0)
        winc = kwargs.get('winc', 0)
        binc = kwargs.get('binc', 0)
        moves_to_go = kwargs.get('moves_to_go', 40)
        
        is_white = self.board.board.turn
        our_time = wtime if is_white else btime
        our_increment = winc if is_white else binc
        
        if our_time > 0:
            # Dynamic time allocation based on position complexity
            base_allocation = our_time / (moves_to_go + 10)  # Conservative base
            
            # Complexity multiplier
            complexity_multiplier = 1.0
            if self.critical_position:
                complexity_multiplier = 1.5
            elif self.position_complexity > 40:
                complexity_multiplier = 1.2
            elif self.position_complexity < 20:
                complexity_multiplier = 0.8
                
            # Game phase consideration
            piece_count = len(self.board.board.piece_map())
            if piece_count <= 10:  # Endgame
                complexity_multiplier *= 1.3
            elif piece_count >= 28:  # Opening
                complexity_multiplier *= 0.9
                
            allocated_time = base_allocation * complexity_multiplier
            
            # Add increment
            allocated_time += our_increment * 0.8
            
            # Safety limits
            max_time = min(our_time * 0.1, 10000)  # Never use more than 10% of remaining time (in ms)
            min_time = min(500, our_time * 0.01)  # Always use at least 1% of remaining time (in ms)
            
            allocated_time = max(min_time, min(allocated_time, max_time))
            
            return allocated_time / 1000.0  # Convert to seconds
        
        return base_time
        
    def search(self, time_limit_ms: Optional[int] = None, depth_override: Optional[int] = None, **kwargs) -> Optional[chess.Move]:
        """v2.2 ENHANCEMENT: Advanced iterative deepening search with aspiration windows."""
        try:
            # Enhanced time management
            allocated_time = self._calculate_time_allocation(time_limit_ms, **kwargs)
            
            self.nodes = 0
            self.last_score = None
            self.start_time = time.time()
            self.search_deadline = self.start_time + allocated_time
            
            # Reset search statistics
            self.search_info = {
                'nodes_searched': 0,
                'tt_hits': 0,
                'null_move_cutoffs': 0,
                'late_move_reductions': 0
            }
            
            # Get legal moves with emergency fallback
            moves = self.move_generator.get_legal_moves()
            if not moves:
                return None
                
            emergency_fallback = moves[0]
            best_move = emergency_fallback
            best_score = -30000
            
            # Set up iterative deepening
            max_depth = depth_override if depth_override is not None else self.max_depth
            
            # v2.2 ENHANCEMENT: Aspiration window search
            aspiration_score = 0  # Start with no aspiration window
            
            # Iterative deepening loop
            for current_depth in range(1, max_depth + 1):
                if self.uci.stop_requested or time.time() > self.search_deadline:
                    break
                    
                try:
                    iteration_start = time.time()
                    
                    # Set up aspiration windows for depth > 2
                    if current_depth > 2 and best_score != -30000:
                        alpha = best_score - self.aspiration_window
                        beta = best_score + self.aspiration_window
                    else:
                        alpha = -30000
                        beta = 30000
                        
                    # Search with current depth
                    score = self._aspiration_search(current_depth, alpha, beta, best_move)
                    
                    # Handle aspiration window failure
                    if score <= alpha or score >= beta:
                        # Re-search with full window
                        score = self._negamax(current_depth, -30000, 30000, best_move)
                    
                    # Update best move if search completed
                    if not self.uci.stop_requested:
                        iteration_move = self._get_best_move_from_root(current_depth)
                        if iteration_move and self._validate_move_legal(iteration_move):
                            best_move = iteration_move
                            best_score = score
                            self.last_score = best_score
                            
                        # Output search info
                        elapsed = time.time() - iteration_start
                        nodes_per_second = int(self.nodes / max(elapsed, 0.001))
                        try:
                            self.uci._out(f"info depth {current_depth} score cp {score} nodes {self.nodes} nps {nodes_per_second} time {int(elapsed*1000)} pv {best_move.uci()}")
                        except:
                            pass
                            
                    # Check if we should continue
                    elapsed_total = time.time() - self.start_time
                    remaining_time = allocated_time - elapsed_total
                    
                    # If we're running low on time and have a decent depth, stop
                    if remaining_time < elapsed * 2 and current_depth >= 4:
                        break
                        
                except Exception as e:
                    try:
                        self.uci._out(f"info string ITERATION_ERROR depth {current_depth}: {e}")
                    except:
                        pass
                    break
            
            # Final validation
            if best_move and not self._validate_move_legal(best_move):
                legal_moves = list(self.board.board.legal_moves)
                best_move = legal_moves[0] if legal_moves else None
                
            return best_move
            
        except Exception as e:
            try:
                self.uci._out(f"info string CRITICAL_SEARCH_ERROR: {e}")
                legal_moves = list(self.board.board.legal_moves)
                return legal_moves[0] if legal_moves else None
            except:
                return None
    
    def _aspiration_search(self, depth: int, alpha: int, beta: int, best_move: Optional[chess.Move]) -> int:
        """v2.2 ENHANCEMENT: Aspiration window search."""
        return self._negamax(depth, alpha, beta, best_move)
    
    def _get_best_move_from_root(self, depth: int) -> Optional[chess.Move]:
        """v2.2 ENHANCEMENT: Extract best move from root position."""
        try:
            moves = self.move_generator.get_legal_moves()
            if not moves:
                return None
                
            best_move = None
            best_score = -30000
            alpha = -30000
            beta = 30000
            
            # Order moves for root search
            ordered_moves = self._order_moves(moves, depth, None)
            
            for move in ordered_moves[:5]:  # Only check top 5 moves for speed
                if not self._validate_move_legal(move):
                    continue
                    
                try:
                    self.board.make_move(move)
                    score = -self._negamax(depth - 1, -beta, -alpha, None)
                    self.board.unmake_move()
                    
                    if score > best_score:
                        best_score = score
                        best_move = move
                        alpha = max(alpha, score)
                        
                    if alpha >= beta:
                        break
                        
                except Exception:
                    try:
                        self.board.unmake_move()
                    except:
                        pass
                    continue
                    
            return best_move
            
        except Exception:
            moves = self.move_generator.get_legal_moves()
            return moves[0] if moves else None
    
    def _negamax(self, depth: int, alpha: int, beta: int, best_move: Optional[chess.Move]) -> int:
        """v2.2 ENHANCEMENT: Advanced negamax with null move pruning and LMR."""
        self.nodes += 1
        self.search_info['nodes_searched'] += 1
        alpha_orig = alpha
        
        # Time and stop checks
        if self.uci.stop_requested:
            return 0
        if self.search_deadline and time.time() > self.search_deadline:
            self.uci.stop_requested = True
            return 0
            
        # Check transposition table
        pos_key = hash(self.board.get_fen())
        tt_entry = self.tt.lookup(pos_key, depth, alpha, beta)
        if tt_entry:
            self.search_info['tt_hits'] += 1
            return tt_entry[0]
        
        # Quiescence search at leaf nodes
        if depth <= 0:
            return self._quiescence_search(alpha, beta, 0)
            
        # Get ordered moves
        moves = self.move_generator.get_legal_moves()
        if not moves:
            if self.board.is_check():
                return -20000 + (self.max_depth - depth)  # Checkmate with depth bonus
            return 0  # Stalemate
        
        # v2.2 ENHANCEMENT: Null move pruning
        if (depth >= 3 and not self.board.is_check() and 
            self._has_non_pawn_material() and beta > -19000):
            try:
                # Make null move (pass the turn)
                self.board.board.push(chess.Move.null())
                null_score = -self._negamax(depth - 1 - self.null_move_reduction, -beta, -beta + 1, None)
                self.board.board.pop()
                
                if null_score >= beta:
                    self.search_info['null_move_cutoffs'] += 1
                    return beta  # Null move cutoff
            except Exception:
                try:
                    self.board.board.pop()
                except:
                    pass
        
        # Order moves
        tt_move = tt_entry[1] if tt_entry else best_move
        ordered_moves = self._order_moves(moves, depth, tt_move)
        
        best_score = -30000
        best_move_found = None
        moves_searched = 0
        
        # Search moves
        for i, move in enumerate(ordered_moves):
            if not self._validate_move_legal(move):
                continue
                
            try:
                self.board.make_move(move)
                moves_searched += 1
                
                # v2.2 ENHANCEMENT: Late Move Reductions (LMR)
                reduction = 0
                if (i >= self.late_move_reduction_threshold and 
                    depth >= 3 and 
                    not self.board.board.is_capture(move) and
                    not self.board.board.gives_check(move) and
                    not self.board.is_check()):
                    
                    reduction = 1
                    if i >= 8:
                        reduction = 2
                    self.search_info['late_move_reductions'] += 1
                
                # Search with possible reduction
                if moves_searched == 1:
                    # First move: full search
                    score = -self._negamax(depth - 1, -beta, -alpha, None)
                else:
                    # Other moves: try reduced search first
                    if reduction > 0:
                        score = -self._negamax(depth - 1 - reduction, -alpha - 1, -alpha, None)
                        if score > alpha:
                            # Re-search with full depth
                            score = -self._negamax(depth - 1, -alpha - 1, -alpha, None)
                    else:
                        score = -self._negamax(depth - 1, -alpha - 1, -alpha, None)
                    
                    # If score raised alpha, do full re-search
                    if score > alpha and score < beta:
                        score = -self._negamax(depth - 1, -beta, -alpha, None)
                
                self.board.unmake_move()
                
                if score > best_score:
                    best_score = score
                    best_move_found = move
                    alpha = max(alpha, score)
                    
                if alpha >= beta:
                    # Beta cutoff - update history and killer moves
                    self._update_history(move, depth)
                    self._update_killer_moves(move, depth)
                    break
                    
            except Exception:
                try:
                    self.board.unmake_move()
                except:
                    pass
                continue
        
        # Store in transposition table
        if best_move_found:
            node_type = NodeType.EXACT
            if best_score <= alpha_orig:
                node_type = NodeType.UPPER
            elif best_score >= beta:
                node_type = NodeType.LOWER
                
            try:
                self.tt.store(pos_key, depth, int(best_score), node_type, best_move_found)
            except:
                pass
        
        return best_score
    
    def _quiescence_search(self, alpha: int, beta: int, qs_depth: int) -> int:
        """v2.2 ENHANCEMENT: Quiescence search for tactical stability."""
        self.nodes += 1
        
        if qs_depth >= self.quiescence_max_depth:
            return int(self.evaluator.evaluate(self.board))
        
        # Stand pat evaluation
        stand_pat = int(self.evaluator.evaluate(self.board))
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        
        # Generate only captures and checks
        moves = []
        for move in self.board.board.legal_moves:
            if self.board.board.is_capture(move) or self.board.board.gives_check(move):
                moves.append(move)
        
        if not moves:
            return stand_pat
        
        # Order captures by MVV-LVA
        moves.sort(key=lambda m: self._mvv_lva_score(m), reverse=True)
        
        for move in moves[:8]:  # Limit quiescence width
            try:
                self.board.make_move(move)
                score = -self._quiescence_search(-beta, -alpha, qs_depth + 1)
                self.board.unmake_move()
                
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
                
            except Exception:
                try:
                    self.board.unmake_move()
                except:
                    pass
                continue
        
        return alpha
    
    def _has_non_pawn_material(self) -> bool:
        """Check if side to move has non-pawn material (for null move pruning)."""
        try:
            color = self.board.board.turn
            pieces = self.board.board.pieces(chess.KNIGHT, color) | \
                    self.board.board.pieces(chess.BISHOP, color) | \
                    self.board.board.pieces(chess.ROOK, color) | \
                    self.board.board.pieces(chess.QUEEN, color)
            return len(pieces) > 0
        except:
            return True  # Conservative assumption
    
    def _order_moves(self, moves: List[chess.Move], depth: int, tt_move: Optional[chess.Move]) -> List[chess.Move]:
        """v2.2 ENHANCEMENT: Advanced move ordering."""
        move_scores = []
        
        for move in moves:
            score = 0
            
            # Transposition table move gets highest priority
            if tt_move and move == tt_move:
                score += 10000
            
            # Captures sorted by MVV-LVA
            if self.board.board.is_capture(move):
                score += self._mvv_lva_score(move)
            
            # Promotions
            if move.promotion:
                score += 8000 + (move.promotion - 1) * 100
            
            # Checks
            if self.board.board.gives_check(move):
                score += 500
            
            # Killer moves
            if depth < len(self.killer_moves):
                if move in self.killer_moves[depth]:
                    score += 300 - self.killer_moves[depth].index(move) * 50
            
            # History heuristic
            history_key = (move.from_square, move.to_square)
            if history_key in self.history_table:
                score += min(self.history_table[history_key], 200)
            
            # Counter moves
            if self.board.board.move_stack:
                last_move = self.board.board.peek()
                if last_move in self.counter_moves and self.counter_moves[last_move] == move:
                    score += 250
            
            move_scores.append((move, score))
        
        # Sort by score (highest first)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, score in move_scores]
    
    def _mvv_lva_score(self, move: chess.Move) -> int:
        """Most Valuable Victim - Least Valuable Attacker scoring."""
        if not self.board.board.is_capture(move):
            return 0
        
        # Piece values (centipawns)
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 10000
        }
        
        # Get victim piece type
        victim_square = move.to_square
        victim_piece = self.board.board.piece_at(victim_square)
        victim_value = piece_values.get(victim_piece.piece_type, 0) if victim_piece else 0
        
        # Get attacker piece type
        attacker_piece = self.board.board.piece_at(move.from_square)
        attacker_value = piece_values.get(attacker_piece.piece_type, 100) if attacker_piece else 100
        
        # MVV-LVA: (victim_value * 10) - attacker_value
        return (victim_value * 10) - attacker_value
    
    def _update_history(self, move: chess.Move, depth: int):
        """Update history heuristic."""
        history_key = (move.from_square, move.to_square)
        if history_key not in self.history_table:
            self.history_table[history_key] = 0
        self.history_table[history_key] += depth * depth
        
        # Prevent overflow
        if self.history_table[history_key] > 10000:
            # Age all history scores
            for key in self.history_table:
                self.history_table[key] //= 2
    
    def _update_killer_moves(self, move: chess.Move, depth: int):
        """Update killer move table."""
        if depth < len(self.killer_moves):
            killers = self.killer_moves[depth]
            if move not in killers:
                killers.insert(0, move)
                if len(killers) > 2:  # Keep only top 2 killers per depth
                    killers.pop()
    
    def _update_counter_moves(self, last_move: chess.Move, counter_move: chess.Move):
        """Update counter move table."""
        self.counter_moves[last_move] = counter_move
