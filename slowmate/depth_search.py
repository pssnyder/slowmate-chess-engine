"""
SlowMate Chess Engine - Depth Search Module

This module implements multi-ply minimax search with alpha-beta pruning, 
move ordering, and quiescence search for deep tactical analysis.

Architecture: Modular search system that integrates with existing tactical intelligence
while providing configurable depth and performance controls.
"""

import time
from typing import Optional, List, Tuple, Dict, Any, Union
import chess
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence


# =============================================================================
# SEARCH CONFIGURATION - PERFORMANCE AND DEPTH CONTROLS
# =============================================================================
# Separate configuration for search performance vs core intelligence quality.
# These settings primarily affect speed/efficiency with minimal quality impact
# when properly tuned, allowing clear distinction between intelligence and performance.

SEARCH_CONFIG = {
    # Core search algorithm controls
    'enable_minimax': True,            # Enable multi-ply minimax search
    'enable_alpha_beta': True,         # Enable alpha-beta pruning optimization
    'enable_iterative_deepening': True, # Start shallow, increase depth progressively
    
    # Move evaluation and ordering
    'enable_move_ordering': True,      # Priority-based move evaluation for efficiency
    'enable_quiescence': True,         # Terminal position stability analysis
    'enable_mate_override': True,      # Always extend search for mate detection
    
    # Depth configuration
    'base_depth': 2,                   # Uniform base depth applied to all positions
    'max_depth': 6,                    # Maximum depth for forcing variations
    'mate_search_depth': 5,            # Minimum depth for mate detection (engine's next 3 turns)
    
    # UCI and reporting
    'enable_uci_updates': True,        # Real-time search updates during thinking
    'enable_multi_pv': True,           # Track and report multiple best variations
    'enable_debug_info': True,         # Send additional debug information to UCI
    'update_frequency_ms': 100         # Minimum milliseconds between UCI updates
}


# =============================================================================
# MOVE ORDERING PRIORITY SYSTEM
# =============================================================================
# Priority hierarchy for move ordering to improve alpha-beta pruning efficiency.
# Higher values = higher priority = evaluated first.

MOVE_ORDER_PRIORITY = {
    # Considerable moves (based on Turing's theory)
    'mate': 10000,                     # Give mate (highest priority)
    'capture_undefended': 5000,        # Capture undefended pieces
    'recapture': 4000,                 # Recapture a square
    'capture_defended_lower': 3000,    # Capture defended piece with lower-value piece
    
    # Additional tactical priorities
    'check': 2000,                     # Give check
    'create_attack': 1000,             # Create attack based on existing attack criteria
    
    # Base move value
    'default': 0                       # All other moves
}


# =============================================================================
# SEARCH STATISTICS AND NODE TRACKING
# =============================================================================

class SearchStats:
    """Track search performance and debugging information."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all statistics for new search."""
        self.nodes_evaluated = 0
        self.max_depth_reached = 0
        self.alpha_beta_cutoffs = 0
        self.quiescence_nodes = 0
        self.mate_nodes = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Move ordering statistics
        self.moves_ordered = 0
        self.ordering_time_ms = 0
        
        # Best line tracking
        self.best_move: Optional[chess.Move] = None
        self.best_score: Optional[int] = None
        self.principal_variation: List[chess.Move] = []
    
    @property
    def nodes_per_second(self) -> int:
        """Calculate nodes per second."""
        if not self.start_time or not self.end_time:
            return 0
        elapsed = self.end_time - self.start_time
        if elapsed <= 0:
            return 0
        return int(self.nodes_evaluated / elapsed)
    
    @property
    def search_time_ms(self) -> int:
        """Calculate total search time in milliseconds."""
        if not self.start_time or not self.end_time:
            return 0
        return int((self.end_time - self.start_time) * 1000)


# =============================================================================
# DEPTH SEARCH ENGINE
# =============================================================================

class DepthSearchEngine(SlowMateEngine):
    """
    Advanced SlowMate Engine with multi-ply depth search capability.
    
    Implements minimax algorithm with alpha-beta pruning, move ordering,
    and quiescence search while maintaining UCI compatibility and 
    integration with existing tactical intelligence.
    """
    
    def __init__(self):
        """Initialize the depth search engine."""
        super().__init__()
        
        # Initialize tactical intelligence (reuse existing system)
        self.intelligence = MoveIntelligence(self)
        
        # Search configuration and statistics
        self.search_config = SEARCH_CONFIG.copy()
        self.stats = SearchStats()
        
        # Search control
        self.search_cancelled = False
        self.search_start_time = None
        
        # UCI communication
        self.uci_info_callback = None  # Function to call with UCI info updates
    
    def configure_search(self, **kwargs):
        """Update search configuration parameters."""
        for key, value in kwargs.items():
            if key in self.search_config:
                self.search_config[key] = value
            else:
                raise ValueError(f"Unknown search configuration: {key}")
    
    def set_uci_callback(self, callback):
        """Set callback function for UCI info updates."""
        self.uci_info_callback = callback
    
    def cancel_search(self):
        """Cancel current search operation."""
        self.search_cancelled = True
    
    def search_best_move(self, time_limit: Optional[float] = None) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """
        Search for the best move using depth analysis.
        
        Args:
            time_limit: Optional time limit in seconds (NOT USED - engine does not manage time)
            
        Returns:
            Tuple of (best_move, evaluation_score, principal_variation)
        """
        # Reset search state
        self.stats.reset()
        self.search_cancelled = False
        self.search_start_time = time.time()
        self.stats.start_time = self.search_start_time
        
        try:
            if self.search_config['enable_iterative_deepening']:
                result = self._iterative_deepening_search()
            else:
                result = self._fixed_depth_search()
            
            return result
                
        except Exception as e:
            # Fallback to tactical intelligence on search failure
            print(f"Search failed, falling back to tactical intelligence: {e}")
            return self._fallback_to_tactical()
        
        finally:
            self.stats.end_time = time.time()
    
    def _iterative_deepening_search(self) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """
        Iterative deepening search without timeout management.
        
        Starts at depth 1 and progressively increases until max depth.
        Engine will search to max configured depth.
        """
        best_move = None
        best_score = None
        best_pv = []
        
        # Start with minimum depth
        for depth in range(1, self.search_config['max_depth'] + 1):
            try:
                # Search at current depth
                move, score, pv = self._search_at_depth(depth)
                
                if move is not None:
                    best_move = move
                    best_score = score
                    best_pv = pv
                    
                    # Update statistics
                    self.stats.max_depth_reached = depth
                    self.stats.best_move = best_move
                    self.stats.best_score = best_score
                    self.stats.principal_variation = best_pv
                    
                    # Send UCI update
                    self._send_uci_info(depth, score, pv, self.stats.nodes_evaluated)
                    
                    # Check for forced mate (can stop search early)
                    if self._is_mate_score(score) and self.search_config['enable_mate_override']:
                        break
                
            except Exception as e:
                # Continue with previous best if this depth fails
                print(f"Depth {depth} failed: {e}")
                break
        
        # Return best result found
        if best_move is None:
            return self._fallback_to_tactical()
        
        return best_move, best_score or 0, best_pv
    
    def _search_at_depth(self, depth: int) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """
        Search at a specific depth using minimax with alpha-beta pruning.
        
        Args:
            depth: Search depth
            
        Returns:
            Tuple of (best_move, score, principal_variation)
        """
        # Get legal moves
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None, 0, []
        
        # Order moves for better alpha-beta pruning
        if self.search_config['enable_move_ordering']:
            legal_moves = self._order_moves(legal_moves)
        
        # Initialize alpha-beta values
        alpha = float('-inf')
        beta = float('inf')
        best_move = legal_moves[0]
        best_score = float('-inf')
        best_pv = []
        
        # Evaluate each move
        for move in legal_moves:
            # Make move
            self.board.push(move)
            
            try:
                # Search this branch
                score, pv = self._minimax(depth - 1, alpha, beta, False)
                
                # Update best move if this is better
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_pv = [move] + pv
                    
                # Update alpha for alpha-beta pruning
                if self.search_config['enable_alpha_beta']:
                    alpha = max(alpha, score)
                
            finally:
                # Always unmake move
                self.board.pop()
            
            # Alpha-beta cutoff
            if self.search_config['enable_alpha_beta'] and alpha >= beta:
                self.stats.alpha_beta_cutoffs += 1
                break
        
        return best_move, int(best_score), best_pv
    
    def _minimax(self, depth: int, alpha: float, beta: float, 
                 maximizing_player: bool) -> Tuple[int, List[chess.Move]]:
        """
        Unified minimax algorithm with optional alpha-beta pruning.
        
        Args:
            depth: Remaining search depth
            alpha: Alpha value for pruning (ignored if alpha-beta disabled)
            beta: Beta value for pruning (ignored if alpha-beta disabled)
            maximizing_player: True if maximizing, False if minimizing
            
        Returns:
            Tuple of (evaluation_score, principal_variation)
        """
        # Update node count
        self.stats.nodes_evaluated += 1
        
        # Check for cancellation
        if self.search_cancelled:
            return 0, []
        
        # Terminal node conditions
        if depth <= 0 or self.board.is_game_over():
            return self._evaluate_position(depth, maximizing_player)
        
        # Get legal moves
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return self._evaluate_position(depth, maximizing_player)
        
        # Order moves for better pruning (if enabled)
        if self.search_config['enable_move_ordering']:
            legal_moves = self._order_moves(legal_moves)
        
        best_pv = []
        use_alpha_beta = self.search_config['enable_alpha_beta']
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                if self.search_cancelled:
                    break
                    
                self.board.push(move)
                eval_score, pv = self._minimax(depth - 1, alpha, beta, False)
                self.board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_pv = [move] + pv
                
                # Alpha-beta pruning (only if enabled)
                if use_alpha_beta:
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        self.stats.alpha_beta_cutoffs += 1
                        break
                        
            return int(max_eval), best_pv
        else:
            min_eval = float('inf')
            for move in legal_moves:
                if self.search_cancelled:
                    break
                    
                self.board.push(move)
                eval_score, pv = self._minimax(depth - 1, alpha, beta, True)
                self.board.pop()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_pv = [move] + pv
                
                # Alpha-beta pruning (only if enabled)
                if use_alpha_beta:
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        self.stats.alpha_beta_cutoffs += 1
                        break
                        
            return int(min_eval), best_pv
    
    def _evaluate_position(self, depth: int, maximizing_player: bool) -> Tuple[int, List[chess.Move]]:
        """
        Evaluate terminal position using existing tactical intelligence.
        
        Applies quiescence search if enabled to ensure position stability.
        """
        # Handle game over positions
        if self.board.is_game_over():
            if self.board.is_checkmate():
                # Fixed: Correct mate score calculation with reasonable values
                # Mate score should reflect actual plies to mate
                plies_to_mate = self.search_config['max_depth'] - depth + 1
                mate_score = 1000 + plies_to_mate  # Use 1000 as base (10 pawns) + distance
                return (-mate_score if maximizing_player else mate_score), []
            else:
                # Stalemate or draw
                return 0, []
        
        # Apply quiescence search if enabled (but only with alpha-beta for performance)
        if (self.search_config['enable_quiescence'] and 
            self.search_config['enable_alpha_beta'] and 
            depth <= 0):
            return self._quiescence_search(maximizing_player, depth=4)
        
        # Use intelligence evaluation system (with all the emergency caps)
        try:
            score = self.intelligence._evaluate_position()
            # Adjust score based on maximizing player (intelligence returns from white's perspective)
            if not maximizing_player:
                score = -score
            return score, []
        except Exception as e:
            # Fallback to simple evaluation only if intelligence fails
            print(f"Intelligence evaluation failed: {e}, using fallback")
            score = 0
            piece_values = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300, 
                            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
            for square in chess.SQUARES:
                piece = self.board.piece_at(square)
                if piece:
                    value = piece_values.get(piece.piece_type, 0)
                    score += value if piece.color == chess.WHITE else -value
            
            # Apply emergency cap to fallback too
            if abs(score) > 200:
                score = 200 if score > 0 else -200
            
            # Adjust score based on maximizing player
            if not maximizing_player:
                score = -score
            
            return score, []
    
    def _quiescence_search(self, maximizing_player: bool, depth: int = 4) -> Tuple[int, List[chess.Move]]:
        """
        Quiescence search to ensure terminal positions are tactically stable.
        
        Based on Turing's theory: continue searching until no "considerable moves" remain.
        """
        self.stats.quiescence_nodes += 1
        
        # Depth limit to prevent infinite recursion
        if depth <= 0:
            stand_pat = self.intelligence._evaluate_position()
            return -stand_pat if not maximizing_player else stand_pat, []
        
        # Get stand-pat score (static evaluation)
        stand_pat = self.intelligence._evaluate_position()
        if not maximizing_player:
            stand_pat = -stand_pat
        
        # Get considerable moves (captures, checks, threats)
        considerable_moves = self._get_considerable_moves()
        
        # If no considerable moves, position is quiet
        if not considerable_moves:
            return stand_pat, []
        
        # Search considerable moves
        best_score = stand_pat
        best_pv = []
        
        for move in considerable_moves:
            self.board.push(move)
            score, pv = self._quiescence_search(not maximizing_player, depth - 1)
            self.board.pop()
            
            if maximizing_player and score > best_score:
                best_score = score
                best_pv = [move] + pv
            elif not maximizing_player and score < best_score:
                best_score = score
                best_pv = [move] + pv
        
        return best_score, best_pv
    
    def _get_considerable_moves(self) -> List[chess.Move]:
        """
        Get "considerable moves" based on Turing's theory.
        
        Considerable moves are:
        1. Captures of undefended pieces
        2. Recapturing a square
        3. Capture defended piece with lower-value piece
        4. Give mate
        5. Give check
        6. Create attack
        """
        considerable = []
        legal_moves = list(self.board.legal_moves)
        
        for move in legal_moves:
            # Check if move is considerable
            if self._is_considerable_move(move):
                considerable.append(move)
        
        return considerable
    
    def _is_considerable_move(self, move: chess.Move) -> bool:
        """
        Determine if a move is "considerable" based on Turing's criteria.
        """
        # Make the move to test its effects
        self.board.push(move)
        try:
            # 1. Give mate
            if self.board.is_checkmate():
                return True
            
            # 2. Give check
            if self.board.is_check():
                return True
            
        finally:
            self.board.pop()
        
        # 3. Captures (undefended, recapture, or favorable exchange)
        if self.board.is_capture(move):
            return True
        
        # 4. Create attack (based on existing attack patterns)
        # This could be expensive, so make it optional
        if self.search_config.get('enable_attack_detection_in_considerable', False):
            # Use existing attack pattern detection
            # Implementation would use self.intelligence attack pattern methods
            pass
        
        return False
    
    def _order_moves(self, moves: List[chess.Move]) -> List[chess.Move]:
        """
        Order moves by priority for better alpha-beta pruning efficiency.
        
        Higher priority moves are evaluated first to improve cutoff chances.
        """
        start_time = time.time()
        
        # Calculate priority for each move
        move_priorities = []
        for move in moves:
            priority = self._calculate_move_priority(move)
            move_priorities.append((move, priority))
        
        # Sort by priority (highest first)
        move_priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Update statistics
        self.stats.moves_ordered += len(moves)
        self.stats.ordering_time_ms += int((time.time() - start_time) * 1000)
        
        return [move for move, _ in move_priorities]
    
    def _calculate_move_priority(self, move: chess.Move) -> int:
        """Calculate priority score for move ordering."""
        priority = MOVE_ORDER_PRIORITY['default']
        
        # Test move effects
        self.board.push(move)
        try:
            # Mate (highest priority)
            if self.board.is_checkmate():
                priority += MOVE_ORDER_PRIORITY['mate']
            
            # Check
            elif self.board.is_check():
                priority += MOVE_ORDER_PRIORITY['check']
        
        finally:
            self.board.pop()
        
        # Captures
        if self.board.is_capture(move):
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                # Basic capture priority (could be enhanced with MVV-LVA)
                if self._is_piece_defended(move.to_square):
                    priority += MOVE_ORDER_PRIORITY['capture_defended_lower']
                else:
                    priority += MOVE_ORDER_PRIORITY['capture_undefended']
        
        return priority
    
    def _is_piece_defended(self, square: chess.Square) -> bool:
        """Check if a piece on the given square is defended."""
        # Simple implementation - could be enhanced
        attackers = self.board.attackers(not self.board.turn, square)
        return len(attackers) > 0
    
    def _fixed_depth_search(self) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """Fixed depth search (when iterative deepening is disabled)."""
        return self._search_at_depth(self.search_config['max_depth'])
    
    def _fallback_to_tactical(self) -> Tuple[Optional[chess.Move], int, List[chess.Move]]:
        """Fallback to existing tactical intelligence if search fails."""
        try:
            move = self.intelligence.select_best_move()
            score = self.intelligence._evaluate_position()
            return move, score, [move] if move else []
        except Exception as e:
            # Final fallback to random legal move
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                import random
                move = random.choice(legal_moves)
                return move, 0, [move]
            return None, 0, []
    
    def _is_mate_score(self, score: int) -> bool:
        """Check if score indicates a forced mate."""
        return abs(score) > 900  # Mate scores are 1000+ (anything above 9 pawns)
    
    def _send_uci_info(self, depth: int, score: int, pv: List[chess.Move], nodes: int):
        """
        Send comprehensive UCI info update for debugging and analysis.
        
        Enhanced output includes:
        - Real-time search progress
        - Performance metrics (nodes/sec, time)
        - Search statistics (cutoffs, move ordering)
        - Principal variation analysis
        - Score interpretation (mate vs evaluation)
        """
        if not self.uci_info_callback or not self.search_config['enable_uci_updates']:
            return
        
        # Calculate comprehensive timing information
        current_time = time.time()
        elapsed_ms = int((current_time - self.stats.start_time) * 1000) if self.stats.start_time else 100
        elapsed_sec = elapsed_ms / 1000.0
        
        # Calculate nodes per second (more accurate real-time calculation)
        nps = int(nodes / max(elapsed_sec, 0.001))  # Avoid division by zero
        
        # Format principal variation with move numbers for clarity
        pv_moves = []
        move_number = 1
        for i, move in enumerate(pv[:8]):  # Show first 8 moves of PV
            if i % 2 == 0:  # White moves
                pv_moves.append(f"{move_number}.{str(move)}")
                if i + 1 < len(pv) and i + 1 < 8:  # Add black move if available
                    pv_moves.append(str(pv[i + 1]))
                    move_number += 1
        pv_str = " ".join(pv_moves)
        
        # Enhanced score interpretation
        if self._is_mate_score(score):
            # Fixed: Calculate mate distance correctly with new scoring
            mate_distance = abs(score) - 1000  # Remove the 1000 base
            mate_moves = max(1, (mate_distance + 1) // 2)  # Convert plies to moves
            if score < 0:
                mate_moves = -mate_moves
            score_str = f"mate {mate_moves}"
        else:
            # Convert to centipawns for standard UCI format
            score_str = f"cp {score}"
        
        # Build comprehensive UCI info string
        info_parts = [
            f"info depth {depth}",
            f"nodes {nodes}",
            f"nps {nps}",
            f"time {elapsed_ms}",
            f"score {score_str}"
        ]
        
        # Add search efficiency metrics
        if self.stats.alpha_beta_cutoffs > 0:
            cutoff_rate = (self.stats.alpha_beta_cutoffs / max(nodes, 1)) * 100
            info_parts.append(f"string Alpha-beta cutoffs: {self.stats.alpha_beta_cutoffs} ({cutoff_rate:.1f}%)")
        
        # Add move ordering efficiency (if available)
        if self.stats.moves_ordered > 0:
            avg_ordering_time = self.stats.ordering_time_ms / max(self.stats.moves_ordered, 1)
            info_parts.append(f"string Move ordering: {avg_ordering_time:.1f}ms/batch")
        
        # Add quiescence search info
        if self.stats.quiescence_nodes > 0:
            q_percentage = (self.stats.quiescence_nodes / max(nodes, 1)) * 100
            info_parts.append(f"string Quiescence nodes: {self.stats.quiescence_nodes} ({q_percentage:.1f}%)")
        
        # Add principal variation
        if pv_str:
            info_parts.append(f"pv {pv_str}")
        
        # Send the main info line
        main_info = " ".join(info_parts[:5])  # Core UCI info
        if pv_str:
            main_info += f" pv {' '.join(str(move) for move in pv)}"  # Full PV for UCI compliance
        
        self.uci_info_callback(main_info)
        
        # Send additional debug information as separate string commands
        if self.search_config.get('enable_debug_info', True):
            # Search tree statistics
            if nodes > 100:  # Only for substantial searches
                self.uci_info_callback(f"info string Search tree: {nodes} nodes, {depth} depth, {nps} nps")
            
            # Performance breakdown
            if self.stats.alpha_beta_cutoffs > 0:
                efficiency = ((nodes - self.stats.alpha_beta_cutoffs) / max(nodes, 1)) * 100
                self.uci_info_callback(f"info string Pruning efficiency: {self.stats.alpha_beta_cutoffs} cutoffs saved {100-efficiency:.1f}% work")
            
            # Move selection insight
            if len(pv) > 0:
                move_insight = self._get_move_insight(pv[0])
                if move_insight:
                    self.uci_info_callback(f"info string Best move analysis: {move_insight}")
    
    def _get_move_insight(self, move: chess.Move) -> str:
        """Generate human-readable insight about the chosen move."""
        insights = []
        
        # Analyze move characteristics
        if self.board.is_capture(move):
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                piece_names = {
                    chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
                    chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"
                }
                insights.append(f"captures {piece_names.get(captured_piece.piece_type, 'piece')}")
        
        # Check if move gives check
        self.board.push(move)
        try:
            if self.board.is_check():
                insights.append("gives check")
            if self.board.is_checkmate():
                insights.append("delivers mate")
        finally:
            self.board.pop()
        
        # Analyze piece movement patterns
        moving_piece = self.board.piece_at(move.from_square)
        if moving_piece:
            piece_names = {
                chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
                chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"
            }
            piece_name = piece_names.get(moving_piece.piece_type, "piece")
            
            # Special move types
            if move.promotion:
                promotion_names = {
                    chess.QUEEN: "queen", chess.ROOK: "rook",
                    chess.BISHOP: "bishop", chess.KNIGHT: "knight"
                }
                promo_piece = promotion_names.get(move.promotion, "piece")
                insights.append(f"{piece_name} promotes to {promo_piece}")
            
            # Castling
            if moving_piece.piece_type == chess.KING and abs(move.from_square - move.to_square) == 2:
                if move.to_square > move.from_square:
                    insights.append("castles kingside")
                else:
                    insights.append("castles queenside")
        
        return ", ".join(insights) if insights else "positional move"
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics for debugging and analysis."""
        # Calculate advanced metrics
        total_time = self.stats.search_time_ms / 1000.0 if self.stats.search_time_ms > 0 else 0.001
        
        return {
            # Core search metrics
            'nodes_evaluated': self.stats.nodes_evaluated,
            'max_depth_reached': self.stats.max_depth_reached,
            'alpha_beta_cutoffs': self.stats.alpha_beta_cutoffs,
            'quiescence_nodes': self.stats.quiescence_nodes,
            
            # Performance metrics
            'nodes_per_second': self.stats.nodes_per_second,
            'search_time_ms': self.stats.search_time_ms,
            'search_time_seconds': total_time,
            
            # Move ordering efficiency
            'moves_ordered': self.stats.moves_ordered,
            'ordering_time_ms': self.stats.ordering_time_ms,
            'avg_ordering_time_ms': (self.stats.ordering_time_ms / max(self.stats.moves_ordered, 1)) if self.stats.moves_ordered > 0 else 0,
            
            # Search tree efficiency
            'pruning_efficiency_percent': (self.stats.alpha_beta_cutoffs / max(self.stats.nodes_evaluated, 1)) * 100,
            'quiescence_ratio_percent': (self.stats.quiescence_nodes / max(self.stats.nodes_evaluated, 1)) * 100,
            
            # Best move information
            'best_move': str(self.stats.best_move) if self.stats.best_move else None,
            'best_score': self.stats.best_score,
            'is_mate_score': self._is_mate_score(self.stats.best_score or 0),
            
            # Principal variation
            'principal_variation': [str(move) for move in self.stats.principal_variation],
            'pv_length': len(self.stats.principal_variation),
            
            # Search configuration snapshot
            'search_config': self.search_config.copy(),
            
            # Advanced analytics
            'nodes_per_depth': self.stats.nodes_evaluated / max(self.stats.max_depth_reached, 1),
            'effective_branching_factor': self._calculate_branching_factor(),
        }
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine identification information for UCI."""
        return {
            'name': 'SlowMate Depth Engine',
            'version': '0.1.01',
            'author': 'SlowMate Development Team',
            'description': 'Educational chess engine with depth search and tactical intelligence',
            'features': [
                'Minimax with Alpha-Beta Pruning',
                'Iterative Deepening',
                'Move Ordering',
                'Quiescence Search',
                'Tactical Intelligence Integration',
                'Real-time UCI Analysis'
            ],
            'algorithms': 'Turing-based considerable moves, Material+Positional evaluation',
            'max_depth': str(self.search_config['max_depth']),
            'alpha_beta_enabled': str(self.search_config['enable_alpha_beta']),
            'move_ordering_enabled': str(self.search_config['enable_move_ordering'])
        }
    
    def print_search_summary(self):
        """Print a comprehensive search summary for debugging."""
        stats = self.get_search_stats()
        
        print("\n" + "="*60)
        print("SlowMate Depth Search Engine - Search Summary")
        print("="*60)
        
        # Core metrics
        print(f"Depth Reached:      {stats['max_depth_reached']}")
        print(f"Nodes Evaluated:    {stats['nodes_evaluated']:,}")
        print(f"Search Time:        {stats['search_time_seconds']:.3f}s")
        print(f"Nodes/Second:       {stats['nodes_per_second']:,}")
        
        # Efficiency metrics
        print(f"\nSearch Efficiency:")
        print(f"  Alpha-Beta Cutoffs: {stats['alpha_beta_cutoffs']} ({stats['pruning_efficiency_percent']:.1f}%)")
        print(f"  Quiescence Nodes:   {stats['quiescence_nodes']} ({stats['quiescence_ratio_percent']:.1f}%)")
        print(f"  Branching Factor:   {stats['effective_branching_factor']:.2f}")
        
        # Move analysis
        print(f"\nBest Move Analysis:")
        print(f"  Move:               {stats['best_move']}")
        print(f"  Score:              {stats['best_score']} {'(Mate!)' if stats['is_mate_score'] else '(Eval)'}")
        print(f"  Principal Variation: {' '.join(stats['principal_variation'][:5])}{'...' if len(stats['principal_variation']) > 5 else ''}")
        
        # Configuration
        print(f"\nEngine Configuration:")
        config = stats['search_config']
        print(f"  Max Depth:          {config['max_depth']}")
        print(f"  Alpha-Beta:         {config['enable_alpha_beta']}")
        print(f"  Move Ordering:      {config['enable_move_ordering']}")
        print(f"  Quiescence:         {config['enable_quiescence']}")
        print(f"  Iterative Deepen:   {config['enable_iterative_deepening']}")
        
        print("="*60)
    
    def _calculate_branching_factor(self) -> float:
        """Calculate effective branching factor for search analysis."""
        if self.stats.max_depth_reached <= 1 or self.stats.nodes_evaluated <= 1:
            return 1.0
        
        # Approximate branching factor: nodes^(1/depth)
        try:
            return self.stats.nodes_evaluated ** (1.0 / self.stats.max_depth_reached)
        except:
            return 1.0


# =============================================================================
# INTEGRATION WITH EXISTING SYSTEMS
# =============================================================================

class DepthIntelligentSlowMateEngine(DepthSearchEngine):
    """
    Full integration of depth search with existing intelligent move selection.
    
    Provides seamless fallback and configuration options for debugging and comparison.
    """
    
    def __init__(self):
        """Initialize integrated depth + intelligence engine."""
        super().__init__()
        
        # Additional integration settings
        self.enable_depth_search = True
        self.fallback_to_intelligence = True
    
    def play_move(self) -> Optional[chess.Move]:
        """
        Play the best move using depth search or tactical intelligence.
        
        This is the main interface method that integrates with existing UCI system.
        """
        if self.enable_depth_search:
            try:
                best_move, score, pv = self.search_best_move()
                if best_move is not None:
                    self.board.push(best_move)
                    return best_move
            except Exception as e:
                print(f"Depth search failed: {e}")
        
        # Fallback to existing tactical intelligence
        if self.fallback_to_intelligence:
            move = self.intelligence.select_best_move()
            if move is not None:
                self.board.push(move)
                return move
        
        # Final fallback to random move
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            import random
            move = random.choice(legal_moves)
            self.board.push(move)
            return move
        
        return None
    
    def configure_depth(self, enable_depth: bool = True, **search_kwargs):
        """Configure depth search settings."""
        self.enable_depth_search = enable_depth
        if search_kwargs:
            self.configure_search(**search_kwargs)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics for debugging and analysis."""
        # Calculate advanced metrics
        total_time = self.stats.search_time_ms / 1000.0 if self.stats.search_time_ms > 0 else 0.001
        
        return {
            # Core search metrics
            'nodes_evaluated': self.stats.nodes_evaluated,
            'max_depth_reached': self.stats.max_depth_reached,
            'alpha_beta_cutoffs': self.stats.alpha_beta_cutoffs,
            'quiescence_nodes': self.stats.quiescence_nodes,
            
            # Performance metrics
            'nodes_per_second': self.stats.nodes_per_second,
            'search_time_ms': self.stats.search_time_ms,
            'search_time_seconds': total_time,
            
            # Move ordering efficiency
            'moves_ordered': self.stats.moves_ordered,
            'ordering_time_ms': self.stats.ordering_time_ms,
            'avg_ordering_time_ms': (self.stats.ordering_time_ms / max(self.stats.moves_ordered, 1)) if self.stats.moves_ordered > 0 else 0,
            
            # Search tree efficiency
            'pruning_efficiency_percent': (self.stats.alpha_beta_cutoffs / max(self.stats.nodes_evaluated, 1)) * 100,
            'quiescence_ratio_percent': (self.stats.quiescence_nodes / max(self.stats.nodes_evaluated, 1)) * 100,
            
            # Best move information
            'best_move': str(self.stats.best_move) if self.stats.best_move else None,
            'best_score': self.stats.best_score,
            'is_mate_score': self._is_mate_score(self.stats.best_score or 0),
            
            # Principal variation
            'principal_variation': [str(move) for move in self.stats.principal_variation],
            'pv_length': len(self.stats.principal_variation),
            
            # Search configuration snapshot
            'search_config': self.search_config.copy(),
            
            # Advanced analytics
            'nodes_per_depth': self.stats.nodes_evaluated / max(self.stats.max_depth_reached, 1),
            'effective_branching_factor': self._calculate_branching_factor(),
        }
