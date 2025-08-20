"""
Advanced Time Management System for SlowMate Chess Engine
Version: 1.1.0
"""

from typing import Optional, Dict, Tuple
import time
import chess

class TimeManager:
    """Advanced time management system with dynamic allocation and phase awareness."""
    
    def __init__(self):
        self.remaining_time: float = 0
        self.increment: float = 0
        self.moves_to_go: Optional[int] = None
        self.nodes_searched: int = 0
        self.start_time: float = 0
        self.allocated_time: float = 0
        self.emergency_move_time: float = 0.1  # 100ms minimum
        
        # Phase-based time allocation weights
        self.phase_weights = {
            'opening': 0.8,
            'middlegame': 1.25,  # Slightly increased for deeper tactical play
            'endgame': 1.0
        }
        # Complexity factors (slightly reduced for speed)
        self.complexity_weights = {
            'material_balance': 0.22,
            'piece_mobility': 0.25,
            'king_safety': 0.18,
            'pawn_structure': 0.15,
            'tactical_opportunities': 1.25,  # Slightly increased for deeper tactical play
        }
        
    def start_new_game(self):
        """Reset time manager for a new game."""
        self.remaining_time = 0
        self.increment = 0
        self.moves_to_go = None
        self.nodes_searched = 0
        
    def set_time_controls(self, wtime: Optional[int], btime: Optional[int], 
                         winc: Optional[int], binc: Optional[int], 
                         moves_to_go: Optional[int], is_white: bool):
        """Set time controls for the current position.
        
        Parameters
        ----------
        wtime : Optional[int]
            White's remaining time in milliseconds
        btime : Optional[int]
            Black's remaining time in milliseconds
        winc : Optional[int]
            White's increment in milliseconds
        binc : Optional[int]
            Black's increment in milliseconds
        moves_to_go : Optional[int]
            Number of moves to next time control
        is_white : bool
            Whether engine is playing as white
        """
        # Always set a reasonable minimum remaining time if missing
        # Defensive: always set a reasonable minimum remaining time if missing
        rt = wtime if is_white else btime
        if rt is None or rt == 0:
            self.remaining_time = 2.0
        else:
            self.remaining_time = float(rt) / 1000
        inc = winc if is_white else binc
        if inc is None or inc == 0:
            self.increment = 0.0
        else:
            self.increment = float(inc) / 1000
        self.moves_to_go = moves_to_go
        if self.remaining_time <= 0:
            self.remaining_time = 2.0
        
    def _calculate_phase_factor(self, board: chess.Board) -> float:
        """Calculate time allocation factor based on game phase.
        
        Parameters
        ----------
        board : chess.Board
            Current position
            
        Returns
        -------
        float
            Time allocation factor (0.0 to 1.0)
        """
        # Count material to determine game phase
        material = sum(len(board.pieces(piece_type, color)) 
                      for color in chess.COLORS 
                      for piece_type in chess.PIECE_TYPES)
        
        if material >= 28:  # Opening (full material is 32)
            return self.phase_weights['opening']
        elif material >= 14:  # Middlegame
            return self.phase_weights['middlegame']
        else:  # Endgame
            return self.phase_weights['endgame']
            
    def _calculate_complexity(self, board: chess.Board) -> float:
        """Calculate position complexity factor.
        
        Parameters
        ----------
        board : chess.Board
            Current position
            
        Returns
        -------
        float
            Complexity factor (0.0 to 1.0)
        """
        complexity = 0.0
        
        # Material tension
        material_diff = abs(self._calculate_material_balance(board))
        complexity += (1.0 - min(1.0, material_diff / 10.0)) * self.complexity_weights['material_balance']
        
        # Piece mobility (approximation)
        mobility = len(list(board.legal_moves))
        complexity += min(1.0, mobility / 40.0) * self.complexity_weights['piece_mobility']
        
        # King safety (basic metric)
        king_safety = self._evaluate_king_safety(board)
        complexity += king_safety * self.complexity_weights['king_safety']
        
        # Pawn structure
        pawn_complexity = self._evaluate_pawn_structure(board)
        complexity += pawn_complexity * self.complexity_weights['pawn_structure']
        
        # Tactical opportunities (basic check)
        tactics = self._evaluate_tactical_potential(board)
        complexity += tactics * self.complexity_weights['tactical_opportunities']
        
        return min(1.0, complexity)
        
    def _calculate_material_balance(self, board: chess.Board) -> float:
        """Calculate material balance in the position."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        balance = 0.0
        for piece_type in piece_values:
            balance += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            balance -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
        return balance
        
    def _evaluate_king_safety(self, board: chess.Board) -> float:
        """Evaluate king safety for both sides."""
        def king_zone_attacks(color: chess.Color) -> int:
            king_square = board.king(color)
            if king_square is None:
                return 0
            attacks = 0
            king_zone = chess.BB_KING_ATTACKS[king_square]
            for move in board.legal_moves:
                if king_zone & chess.BB_SQUARES[move.to_square]:
                    attacks += 1
            return attacks
            
        white_attacks = king_zone_attacks(chess.WHITE)
        black_attacks = king_zone_attacks(chess.BLACK)
        
        # Normalize to 0-1 range
        return min(1.0, (white_attacks + black_attacks) / 10.0)
        
    def _evaluate_pawn_structure(self, board: chess.Board) -> float:
        """Evaluate pawn structure complexity."""
        doubled_pawns = 0
        isolated_pawns = 0
        
        for file_idx in range(8):
            file_mask = chess.BB_FILES[file_idx]
            adjacent_files_mask = (
                (chess.BB_FILES[file_idx - 1] if file_idx > 0 else 0) |
                (chess.BB_FILES[file_idx + 1] if file_idx < 7 else 0)
            )
            
            # Count doubled pawns
            white_pawns_in_file = bin(board.pieces(chess.PAWN, chess.WHITE) & file_mask).count('1')
            black_pawns_in_file = bin(board.pieces(chess.PAWN, chess.BLACK) & file_mask).count('1')
            if white_pawns_in_file > 1:
                doubled_pawns += white_pawns_in_file - 1
            if black_pawns_in_file > 1:
                doubled_pawns += black_pawns_in_file - 1
                
            # Count isolated pawns
            if (board.pieces(chess.PAWN, chess.WHITE) & file_mask) and not (board.pieces(chess.PAWN, chess.WHITE) & adjacent_files_mask):
                isolated_pawns += 1
            if (board.pieces(chess.PAWN, chess.BLACK) & file_mask) and not (board.pieces(chess.PAWN, chess.BLACK) & adjacent_files_mask):
                isolated_pawns += 1
                
        return min(1.0, (doubled_pawns + isolated_pawns) / 8.0)
        
    def _evaluate_tactical_potential(self, board: chess.Board) -> float:
        """Evaluate tactical potential in the position."""
        tactical_potential = 0.0
        
        # Check for pieces under attack
        for move in board.legal_moves:
            if board.is_capture(move):
                tactical_potential += 0.1
            if board.gives_check(move):
                tactical_potential += 0.2
                
        return min(1.0, tactical_potential)
        
    def calculate_move_time(self, board: chess.Board, ply: int) -> float:
        """Calculate how much time to spend on the current move.
        
        Parameters
        ----------
        board : chess.Board
            Current position
        ply : int
            Current ply number
            
        Returns
        -------
        float
            Allocated time in seconds
        """
        if self.remaining_time <= 0:
            self.remaining_time = 2.0
        # Always allocate at least 1 second for any move
        min_alloc = 1.0
            
        # Base time calculation
        if self.moves_to_go:
            # Reserve some time for remaining moves
            base_time = (self.remaining_time * 0.8) / (self.moves_to_go + 1)
        else:
            # Estimate remaining moves based on game phase
            moves_played = ply // 2
            if moves_played < 10:  # Opening
                estimated_moves = 40
            elif moves_played < 30:  # Middlegame
                estimated_moves = 30
            else:  # Endgame
                estimated_moves = 20
            
            # Use smaller divisor for critical phases
            divisor = max(10, estimated_moves - moves_played)
            base_time = (self.remaining_time * 0.8) / divisor
            
        # Apply factors
        phase_factor = self._calculate_phase_factor(board)
        complexity_factor = self._calculate_complexity(board)
        
        # Calculate final time with stronger weight for complexity
        allocated_time = base_time * phase_factor * (1.0 + complexity_factor)
        
        # Add increment more aggressively when needed
        if self.increment > 0:
            if self.remaining_time < self.increment * 10:
                # Use most of increment when low on time
                allocated_time += self.increment * 0.9
            else:
                # Use increment based on position complexity
                allocated_time += self.increment * (0.5 + complexity_factor * 0.4)
            
        # Safety checks
        min_time = max(self.emergency_move_time, 
                      min(1.0, self.remaining_time * 0.05))  # At least 5% of remaining time
        max_time = min(
            self.remaining_time * 0.4,  # Never use more than 40% of remaining time
            30.0  # Hard cap at 30 seconds
        )
        
        self.allocated_time = max(min_time, min(allocated_time, max_time))
        return self.allocated_time
        
    def should_stop(self, nodes: int, elapsed: float) -> bool:
        """Determine if search should stop based on time usage.
        
        Parameters
        ----------
        nodes : int
            Number of nodes searched
        elapsed : float
            Time elapsed in seconds
            
        Returns
        -------
        bool
            True if search should stop
        """
        self.nodes_searched = nodes
        
        # Emergency stop if we've used 120% of allocated time
        if elapsed >= self.allocated_time * 1.2:
            return True
            
        # Allow more time in critical positions
        if nodes > 500000 and elapsed < self.allocated_time * 0.9:
            return False
            
        # Continue if making good progress and have time
        nodes_per_second = nodes / max(0.001, elapsed)
        if nodes_per_second > 50000 and elapsed < self.allocated_time * 0.95:
            return False
            
        # Ensure minimum thinking time in complex positions
        if elapsed < max(1.0, self.allocated_time * 0.25):
            return False
            
        # Standard time management
        return elapsed >= self.allocated_time
