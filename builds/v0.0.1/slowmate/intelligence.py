"""
SlowMate Chess Engine - Move Selection Intelligence

This module contains intelligent move selection logic that goes beyond random selection.
Current implementation includes critical game state handling for checkmate, stalemate, and draws,
plus position evaluation based on material count and piece values.

Architecture: Modular move filters that can be easily extended with additional intelligence.
"""

import random
from typing import Optional, List, Tuple, Dict, Any
import chess
from slowmate.engine import SlowMateEngine


# =============================================================================
# DEBUGGING CONFIGURATION - FEATURE TOGGLES
# =============================================================================
# Toggle individual features on/off for isolation testing and debugging.
# When a feature is disabled, it returns a minimal/zero value instead of running
# its full evaluation, allowing you to test feature interactions and identify
# which components might be interfering with each other.

DEBUG_CONFIG = {
    # Core game state detection
    'checkmate_detection': True,        # Find and prioritize checkmate moves
    'stalemate_detection': True,        # Avoid moves that cause stalemate
    'draw_prevention': True,            # Avoid moves that cause draws
    
    # Material and position evaluation
    'material_calculation': True,       # Basic piece value calculation
    'positional_evaluation': True,     # Piece-square table (PST) evaluation
    'game_phase_detection': True,      # Opening/middlegame/endgame phase detection
    
    # Safety and tactical features
    'king_safety': True,               # King safety evaluation (castling, pawn shield)
    'threat_awareness': True,          # ENABLED: Piece threat detection and penalty system
    'capture_calculation': True,       # Capture opportunity evaluation
    'tactical_combinations': True,     # ENABLED: Unified tactical bonus (threats + captures)
    
    # Advanced tactical patterns
    'attack_patterns': True,           # ENABLED: Pin, fork, discovered attack recognition
    'piece_coordination': True,        # ENABLED: Rook stacking, batteries, piece pairing
    
    # Specific attack pattern recognition
    'pin_detection': True,             # Detect and exploit pins
    'fork_detection': True,            # Detect and create forks  
    'discovered_attacks': True,        # Discovered attacks and checks
    'skewer_detection': True,          # Detect and create skewers
    'double_attack_patterns': True,    # Multiple simultaneous threats
    
    # Specific coordination patterns
    'rook_coordination': True,         # Rook stacking and file control
    'battery_attacks': True,           # Queen-rook and queen-bishop batteries
    'knight_coordination': True,       # Knight pairing and outpost control
    'bishop_coordination': True,       # Bishop pairing and color coordination
    
    # Future features (placeholders for when implemented)
    'pawn_structure': False,          # Future: Advanced pawn structure analysis
    'opening_book': False,            # Future: Opening book integration
}

# Debug values to return when features are disabled
DEBUG_DISABLED_VALUES = {
    'material_calculation': 0.0,       # No material advantage
    'positional_evaluation': 0.0,     # No positional advantage  
    'king_safety': 0.0,              # Neutral king safety
    'threat_awareness': 0.0,          # No threat penalties
    'capture_calculation': 0.0,       # No capture bonuses
    'tactical_combinations': 0.001,   # Tiny value to identify in debug output
    'attack_patterns': 0.0,           # No attack pattern bonuses
    'piece_coordination': 0.0,        # No coordination bonuses
    'pin_detection': 0.0,
    'fork_detection': 0.0,
    'discovered_attacks': 0.0,
    'skewer_detection': 0.0,
    'double_attack_patterns': 0.0,
    'rook_coordination': 0.0,
    'battery_attacks': 0.0,
    'knight_coordination': 0.0,
    'bishop_coordination': 0.0,
    'pawn_structure': 0.0,
}

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a debugging feature is enabled."""
    return DEBUG_CONFIG.get(feature_name, False)

def get_disabled_value(feature_name: str) -> float:
    """Get the return value for a disabled feature."""
    return DEBUG_DISABLED_VALUES.get(feature_name, 0.0)

# =============================================================================


class MoveIntelligence:
    """
    Intelligent move selection for SlowMate Chess Engine
    
    Provides layered move filtering and selection logic:
    1. Critical game state handling (checkmate, stalemate, draws)
    2. Position evaluation (material count and piece values)
    3. Future: Opening book, tactical patterns, positional evaluation
    4. Fallback: Random selection from remaining legal moves
    """
    
    # Standard piece values in centipawns (UCI standard)
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,    # Slightly higher than knight as requested
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0         # King safety handled separately
    }
    
    # Piece-Square Tables (PST) for positional evaluation
    # Phase 1: Base PST - Universal positioning preferences (fallback)
    # Board representation: a1=0, b1=1, ..., h8=63 (chess.SQUARE_NAMES order)
    # Values in centipawns (positive = good position)
    BASE_PST = [
        # Rank 1 (a1-h1): Own piece starting positions
        -1, -1,  0,  0,  1,  0, -1, -1,  # a1-h1: R N B Q K B N R
        # Rank 2 (a2-h2): Own pawn starting positions = 0
         0,  0,  0,  0,  0,  0,  0,  0,  # a2-h2: Own pawns
        # Rank 3 (a3-h3): Internal squares, avoid edges
        -1,  1,  1,  1,  1,  1,  1, -1,  # a3-h3
        # Rank 4 (a4-h4): Internal squares, center preference  
        -1,  1,  2,  2,  2,  2,  1, -1,  # a4-h4: center +2
        # Rank 5 (a5-h5): Internal squares, center preference
        -1,  1,  2,  2,  2,  2,  1, -1,  # a5-h5: center +2
        # Rank 6 (a6-h6): Internal squares, avoid edges
        -1,  1,  1,  1,  1,  1,  1, -1,  # a6-h6
        # Rank 7 (a7-h7): Black pawn starting positions = 0  
         0,  0,  0,  0,  0,  0,  0,  0,  # a7-h7: Black pawns
        # Rank 8 (a8-h8): Black piece starting positions = 0
         0,  0,  0,  0,  0,  0,  0,  0   # a8-h8: Black pieces
    ]
    
    # Phase 2: Piece-Specific PST Tables
    # Each piece gets tailored positional preferences
    
    # Pawn PST - Encourage advancement and center control
    PAWN_PST = [
        # Rank 1: Pawns can't be here (promotion squares)
         0,   0,   0,   0,   0,   0,   0,   0,
        # Rank 2: Starting position, neutral
         0,   0,   0,   0,   0,   0,   0,   0,
        # Rank 3: Modest advance bonus
         5,  10,  10, -20, -20,  10,  10,   5,
        # Rank 4: Good central advance, strong center bonus
         5,  -5, -10,  20,  20, -10,  -5,   5,
        # Rank 5: Strong central control
         0,   0,   0,  25,  25,   0,   0,   0,
        # Rank 6: Advanced pawns, very good
        10,  10,  20,  30,  30,  20,  10,  10,
        # Rank 7: About to promote, excellent
        50,  50,  50,  50,  50,  50,  50,  50,
        # Rank 8: Promotion squares (shouldn't stay as pawn)
         0,   0,   0,   0,   0,   0,   0,   0
    ]
    
    # Knight PST - Prefer center, avoid edges
    KNIGHT_PST = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]
    
    # Bishop PST - Prefer long diagonals and development
    BISHOP_PST = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]
    
    # Rook PST - Prefer open files and 7th rank
    ROOK_PST = [
        # Rank 1: Starting rank, neutral
         0,   0,   0,   0,   0,   0,   0,   0,
        # Rank 2: Second rank, good for activity
         5,  10,  10,  10,  10,  10,  10,   5,
        # Rank 3-6: Middle ranks, avoid files a/h
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        # Rank 7: Excellent for attacks on opponent
         5,  10,  10,  15,  15,  10,  10,   5,
        # Rank 8: Opponent back rank, very good
         0,   0,   0,   5,   5,   0,   0,   0
    ]
    
    # Queen PST - Flexible positioning, slight center preference
    QUEEN_PST = [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
         -5,   0,   5,   5,   5,   5,   0,  -5,
          0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20
    ]
    
    # King PST - Safety first, prefer back rank in middlegame
    KING_PST = [
        # Rank 1: Back rank safety (where king starts)
         20,  30,  10,   5,   5,  10,  30,  20,
        # Rank 2: Second rank, still relatively safe
         20,  20,   0,   0,   0,   0,  20,  20,
        # Rank 3: Getting more exposed
        -10, -20, -20, -20, -20, -20, -20, -10,
        # Rank 4: Very exposed
        -20, -30, -30, -40, -40, -30, -30, -20,
        # Rank 5: Very exposed
        -30, -40, -40, -50, -50, -40, -40, -30,
        # Rank 6: Very exposed
        -30, -40, -40, -50, -50, -40, -40, -30,
        # Rank 7: Very exposed
        -30, -40, -40, -50, -50, -40, -40, -30,
        # Rank 8: Opponent's back rank (usually empty)
        -30, -40, -40, -50, -50, -40, -40, -30
    ]
    
    # Phase 3: Endgame-Specific PST Tables
    # These tables activate when game phase is detected as endgame
    
    # Pawn Endgame PST - Promote at all costs!
    PAWN_ENDGAME_PST = [
        # Rank 1: Pawns can't be here
         0,   0,   0,   0,   0,   0,   0,   0,
        # Rank 2: Starting position (endgame shouldn't have pawns here)
         0,   0,   0,   0,   0,   0,   0,   0,
        # Rank 3: Push forward aggressively
        20,  25,  30,  35,  35,  30,  25,  20,
        # Rank 4: Even more aggressive
        30,  35,  40,  50,  50,  40,  35,  30,
        # Rank 5: Very advanced
        50,  60,  70,  80,  80,  70,  60,  50,
        # Rank 6: Almost there!
        80,  90, 100, 120, 120, 100,  90,  80,
        # Rank 7: About to promote - maximum value!
       200, 200, 200, 200, 200, 200, 200, 200,
        # Rank 8: Promotion
         0,   0,   0,   0,   0,   0,   0,   0
    ]
    
    # King Endgame PST - Activate and centralize!
    KING_ENDGAME_PST = [
        # Rank 1: Get out of back rank in endgame
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        # Rank 2: Start moving forward
        -10,  -5,   0,   5,   5,   0,  -5, -10,
        # Rank 3: Good activity
         -5,   0,  10,  15,  15,  10,   0,  -5,
        # Rank 4: Very active
          0,   5,  15,  25,  25,  15,   5,   0,
        # Rank 5: Excellent central activity
          5,  10,  20,  30,  30,  20,  10,   5,
        # Rank 6: Perfect centralization
         10,  15,  25,  35,  35,  25,  15,  10,
        # Rank 7: Supporting pawn advancement
         15,  20,  30,  35,  35,  30,  20,  15,
        # Rank 8: Following pawns to promotion
         10,  15,  20,  25,  25,  20,  15,  10
    ]
    
    # Rook Endgame PST - Control ranks and files, limit opponent king
    ROOK_ENDGAME_PST = [
        # Rank 1: Back rank control
         5,  10,  10,  15,  15,  10,  10,   5,
        # Rank 2: Good second rank control
        10,  15,  15,  20,  20,  15,  15,  10,
        # Rank 3-6: Central files preferred, avoid edges
         0,  10,  15,  15,  15,  15,  10,   0,
         0,  10,  15,  15,  15,  15,  10,   0,
         0,  10,  15,  15,  15,  15,  10,   0,
         0,  10,  15,  15,  15,  15,  10,   0,
        # Rank 7: Excellent attacking rank against opponent
        15,  20,  25,  30,  30,  25,  20,  15,
        # Rank 8: Opponent back rank domination
        10,  15,  20,  25,  25,  20,  15,  10
    ]
    
    def __init__(self, engine: SlowMateEngine):
        """
        Initialize move intelligence with reference to engine.
        
        Args:
            engine: The SlowMateEngine instance to analyze
        """
        self.engine = engine
    
    def detect_game_phase(self) -> str:
        """
        Detect the current game phase for PST selection.
        
        Returns:
            'opening' | 'middlegame' | 'endgame'
        """
        if not is_feature_enabled('game_phase_detection'):
            return 'middlegame'  # Default to middlegame when disabled
            
        board = self.engine.board
        
        # Count total material (excluding kings)
        material_count = 0
        piece_count = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                piece_count += 1
                material_count += self.PIECE_VALUES[piece.piece_type]
        
        # Divide by 2 since we counted both sides
        total_material = material_count // 2
        total_pieces = piece_count // 2
        
        # Endgame criteria (per side):
        # - Less than 13 points of material (roughly R+B+N = 1150 points)
        # - Or less than 6 pieces total per side
        if total_material < 1300 or total_pieces < 6:
            return 'endgame'
        
        # Opening criteria:
        # - More than 20 points of material (most pieces still on board)
        # - Or more than 12 pieces per side  
        elif total_material > 2000 or total_pieces > 12:
            return 'opening'
        
        # Everything else is middlegame
        else:
            return 'middlegame'
    
    def _get_pst_value(self, square: chess.Square, piece_type: int, color: chess.Color) -> int:
        """
        Get piece-square table value for a piece on a square.
        Now includes game phase awareness for enhanced endgame play.
        
        Args:
            square: The square the piece is on
            piece_type: The type of piece (PAWN, KNIGHT, etc.)
            color: The color of the piece
        
        Returns:
            PST value in centipawns
        """
        game_phase = self.detect_game_phase()
        
        # For black pieces, flip the square to get white's perspective
        if color == chess.BLACK:
            # Flip rank: rank 0 becomes 7, rank 1 becomes 6, etc.
            flipped_square = chess.square(chess.square_file(square), 7 - chess.square_rank(square))
        else:
            flipped_square = square
        
        # Select appropriate PST based on piece type and game phase
        if piece_type == chess.PAWN:
            if game_phase == 'endgame':
                pst_value = self.PAWN_ENDGAME_PST[flipped_square]
            else:
                pst_value = self.PAWN_PST[flipped_square]
                
        elif piece_type == chess.KING:
            if game_phase == 'endgame':
                pst_value = self.KING_ENDGAME_PST[flipped_square]
            else:
                pst_value = self.KING_PST[flipped_square]
                
        elif piece_type == chess.ROOK:
            if game_phase == 'endgame':
                pst_value = self.ROOK_ENDGAME_PST[flipped_square]
            else:
                pst_value = self.ROOK_PST[flipped_square]
                
        elif piece_type == chess.KNIGHT:
            pst_value = self.KNIGHT_PST[flipped_square]
        elif piece_type == chess.BISHOP:
            pst_value = self.BISHOP_PST[flipped_square]
        elif piece_type == chess.QUEEN:
            pst_value = self.QUEEN_PST[flipped_square]
        else:
            pst_value = 0
        
        # Return positive for white, negative for black
        return pst_value if color == chess.WHITE else -pst_value
    
    def select_best_move(self) -> Optional[chess.Move]:
        """
        Select the best move using intelligent analysis.
        
        Returns:
            chess.Move: The selected move, or None if no legal moves
        """
        legal_moves = list(self.engine.board.legal_moves)
        
        if not legal_moves:
            return None
        
        # Phase 1: Look for winning moves (checkmate)
        checkmate_moves = self._find_checkmate_moves(legal_moves)
        if checkmate_moves:
            # If we can checkmate, always do it
            return random.choice(checkmate_moves)
        
        # Phase 2: Filter out losing/drawing moves
        filtered_moves = self._filter_bad_moves(legal_moves)
        
        # Phase 3: If we have good moves, evaluate them for best material gain
        if filtered_moves:
            return self._select_best_evaluated_move(filtered_moves)
        else:
            # All moves lead to stalemate/draw - we're forced to play one
            # Even in this case, try to pick the least bad one
            return self._select_best_evaluated_move(legal_moves)
    
    def _find_checkmate_moves(self, legal_moves: List[chess.Move]) -> List[chess.Move]:
        """
        Find all moves that result in checkmate.
        
        Args:
            legal_moves: List of legal moves to analyze
            
        Returns:
            List of moves that deliver checkmate
        """
        if not is_feature_enabled('checkmate_detection'):
            return []  # Return empty list when disabled
            
        checkmate_moves = []
        
        for move in legal_moves:
            # Make the move temporarily
            self.engine.board.push(move)
            
            # Check if this results in checkmate
            if self.engine.board.is_checkmate():
                checkmate_moves.append(move)
            
            # Undo the move
            self.engine.board.pop()
        
        return checkmate_moves
    
    def _filter_bad_moves(self, legal_moves: List[chess.Move]) -> List[chess.Move]:
        """
        Filter out moves that lead to stalemate or draws.
        
        Args:
            legal_moves: List of legal moves to analyze
            
        Returns:
            List of moves that don't lead to immediate stalemate/draw
        """
        if not is_feature_enabled('stalemate_detection') and not is_feature_enabled('draw_prevention'):
            return legal_moves  # Return all moves when both features disabled
            
        good_moves = []
        
        for move in legal_moves:
            # Make the move temporarily
            self.engine.board.push(move)
            
            # Check if this move creates a bad position
            is_bad_move = False
            
            if is_feature_enabled('stalemate_detection'):
                is_bad_move = is_bad_move or self.engine.board.is_stalemate()
            
            if is_feature_enabled('draw_prevention'):
                is_bad_move = is_bad_move or (
                    self.engine.board.is_insufficient_material() or
                    self.engine.board.is_seventyfive_moves() or
                    self.engine.board.is_fivefold_repetition() or
                    self.engine.board.can_claim_draw()
                )
            
            if not is_bad_move:
                good_moves.append(move)
            
            # Undo the move
            self.engine.board.pop()
        
        return good_moves
    
    def _select_best_evaluated_move(self, moves: List[chess.Move]) -> Optional[chess.Move]:
        """
        Select the best move from candidates based on position evaluation.
        
        Args:
            moves: List of candidate moves to evaluate
            
        Returns:
            The move with the best evaluation score, or None if no moves available
        """
        if not moves:
            # This should never happen, but return None as fallback
            return None
        
        best_moves = []
        best_score = float('-inf')
        
        for move in moves:
            # Evaluate the position after this move
            score = self._evaluate_move(move)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        # If multiple moves have the same best score, pick randomly
        return random.choice(best_moves)
    
    def _evaluate_move(self, move: chess.Move) -> int:
        """
        Evaluate a move and return its score in centipawns.
        
        Args:
            move: The move to evaluate
            
        Returns:
            Evaluation score in centipawns (positive = good for current player)
        """
        # Store whose turn it is before making the move
        current_player = self.engine.board.turn
        
        # TACTICAL COMBINATION BONUS: Reward moves that solve multiple tactical problems
        # This must be calculated BEFORE making the move to check original threat status
        combination_bonus = self._calculate_tactical_combination_bonus(move, current_player)
        
        # Make the move temporarily
        self.engine.board.push(move)
        
        # Calculate position evaluation from the original player's perspective
        # Material evaluation
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        # PST evaluation
        white_pst = self._calculate_pst_score(chess.WHITE)
        black_pst = self._calculate_pst_score(chess.BLACK)
        
        # King safety evaluation
        white_king_safety = self._calculate_king_safety(chess.WHITE)
        black_king_safety = self._calculate_king_safety(chess.BLACK)
        
        # Captures evaluation
        white_captures = self._calculate_captures_score(chess.WHITE)
        black_captures = self._calculate_captures_score(chess.BLACK)
        
        # Attack patterns evaluation
        white_attacks = self._calculate_attack_patterns_score(chess.WHITE)
        black_attacks = self._calculate_attack_patterns_score(chess.BLACK)
        
        # Piece coordination evaluation
        white_coordination = self._calculate_piece_coordination_score(chess.WHITE)
        black_coordination = self._calculate_piece_coordination_score(chess.BLACK)
        
        # Combine all scores from current player's perspective
        if current_player == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
            king_safety_score = white_king_safety - black_king_safety
            captures_score = white_captures - black_captures
            attacks_score = white_attacks - black_attacks
            coordination_score = white_coordination - black_coordination
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
            king_safety_score = black_king_safety - white_king_safety
            captures_score = black_captures - white_captures
            attacks_score = black_attacks - white_attacks
            coordination_score = black_coordination - white_coordination
        
        total_score = material_score + positional_score + king_safety_score + captures_score + attacks_score + coordination_score
        
        # Add the pre-calculated tactical combination bonus
        total_score += combination_bonus
        
        # Debug output for key moves
        if str(move) in ['g2a8', 'g2b7']:
            print(f"DEBUG: Move {move} combination bonus: {combination_bonus}, total: {total_score}")
        
        # Undo the move
        self.engine.board.pop()
        
        return total_score
    
    def _evaluate_position(self) -> int:
        """
        Evaluate the current position and return score in centipawns.
        
        Returns:
            Evaluation score from current player's perspective
        """
        # Material evaluation
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        # PST evaluation
        white_pst = self._calculate_pst_score(chess.WHITE)
        black_pst = self._calculate_pst_score(chess.BLACK)
        
        # King safety evaluation
        white_king_safety = self._calculate_king_safety(chess.WHITE)
        black_king_safety = self._calculate_king_safety(chess.BLACK)
        
        # Captures evaluation (tactical opportunities)
        white_captures = self._calculate_captures_score(chess.WHITE)
        black_captures = self._calculate_captures_score(chess.BLACK)
        
        # Attack patterns evaluation
        white_attacks = self._calculate_attack_patterns_score(chess.WHITE)
        black_attacks = self._calculate_attack_patterns_score(chess.BLACK)
        
        # Piece coordination evaluation  
        white_coordination = self._calculate_piece_coordination_score(chess.WHITE)
        black_coordination = self._calculate_piece_coordination_score(chess.BLACK)
        
        # Combine scores from current player's perspective
        if self.engine.board.turn == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
            king_safety_score = white_king_safety - black_king_safety
            captures_score = white_captures - black_captures
            attacks_score = white_attacks - black_attacks
            coordination_score = white_coordination - black_coordination
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
            king_safety_score = black_king_safety - white_king_safety
            captures_score = black_captures - white_captures
            attacks_score = black_attacks - white_attacks
            coordination_score = black_coordination - white_coordination
        
        return material_score + positional_score + king_safety_score + captures_score + attacks_score + coordination_score
    
    def _calculate_material(self, color: chess.Color) -> int:
        """
        Calculate total material value for a given color with threat awareness.
        
        Args:
            color: The color to calculate material for
            
        Returns:
            Total material value in centipawns (threat-adjusted)
        """
        return self._calculate_material_with_threats(color)
    
    def _calculate_material_with_threats(self, color: chess.Color) -> int:
        """
        Calculate material value with threat modifiers applied.
        Threatened pieces are valued at 50% to reflect risk.
        
        Args:
            color: The color to calculate material for
            
        Returns:
            Threat-adjusted material value in centipawns
        """
        if not is_feature_enabled('material_calculation'):
            return int(get_disabled_value('material_calculation'))
            
        total = 0
        
        # Iterate through all squares to get specific piece positions
        for square in chess.SQUARES:
            piece = self.engine.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type != chess.KING:
                base_value = self.PIECE_VALUES[piece.piece_type]
                
                # Apply threat modifier if threat awareness is enabled
                if is_feature_enabled('threat_awareness') and self._is_piece_under_threat(square, color):
                    # Threatened piece worth 50% of base value
                    threat_modifier = 0.5
                else:
                    # Safe piece worth full value (or threat awareness disabled)
                    threat_modifier = 1.0
                
                total += int(base_value * threat_modifier)
        
        return total
    
    def _is_piece_under_threat(self, square: chess.Square, piece_color: chess.Color) -> bool:
        """
        Determine if a piece on a given square is under threat by the opponent.
        Only considers actual attacks, not potential future attacks.
        
        Args:
            square: The square to check
            piece_color: The color of the piece on the square
            
        Returns:
            True if the piece is under threat, False otherwise
        """
        opponent_color = not piece_color
        board = self.engine.board
        
        # Use python-chess built-in attack detection for accuracy
        return board.is_attacked_by(opponent_color, square)
    
    def _piece_attacks_square(self, attacker_square: chess.Square, target_square: chess.Square, 
                             attacker_piece: chess.Piece) -> bool:
        """
        Check if a piece on attacker_square can attack target_square.
        This is a backup method - we now use python-chess built-in attack detection.
        
        Args:
            attacker_square: Square of the attacking piece
            target_square: Square being attacked
            attacker_piece: The attacking piece
            
        Returns:
            True if the piece can attack the target square
        """
        # This method is kept for potential future enhancements
        # Currently we use board.is_attacked_by() for accuracy
        return self.engine.board.is_attacked_by(attacker_piece.color, target_square)
    
    def _calculate_pst_score(self, color: chess.Color) -> int:
        """
        Calculate piece-square table score for a given color.
        
        Args:
            color: The color to calculate PST score for
            
        Returns:
            Total PST score in centipawns
        """
        if not is_feature_enabled('positional_evaluation'):
            return int(get_disabled_value('positional_evaluation'))
            
        total_pst_score = 0
        
        # Iterate through all piece types
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, 
                          chess.ROOK, chess.QUEEN, chess.KING]:
            pieces = self.engine.board.pieces(piece_type, color)
            
            for square in pieces:
                # Get PST value for this square and piece
                pst_value = self._get_pst_value(square, piece_type, color)
                total_pst_score += pst_value
        
        return total_pst_score
    
    def _calculate_king_safety(self, color: chess.Color) -> int:
        """
        Calculate king safety evaluation for the given color.
        
        Args:
            color: The color to evaluate king safety for
            
        Returns:
            King safety score in centipawns (positive = safer)
        """
        if not is_feature_enabled('king_safety'):
            return int(get_disabled_value('king_safety'))
            
        king_safety_score = 0
        
        # 1. Castling Rights Evaluation (small bonus for maintaining rights)
        castling_rights_bonus = self._evaluate_castling_rights(color)
        king_safety_score += castling_rights_bonus
        
        # 2. Castling Status Evaluation (larger bonus for having castled)
        castling_status_bonus = self._evaluate_castling_status(color)
        king_safety_score += castling_status_bonus
        
        # 3. King Pawn Shield Evaluation (bonus for pawns protecting king)
        pawn_shield_bonus = self._evaluate_king_pawn_shield(color)
        king_safety_score += pawn_shield_bonus
        
        return king_safety_score
    
    def _evaluate_castling_rights(self, color: chess.Color) -> int:
        """
        Evaluate castling rights (small bonus for maintaining ability to castle).
        
        Args:
            color: The color to evaluate
            
        Returns:
            Castling rights bonus in centipawns
        """
        bonus = 0
        board = self.engine.board
        
        if color == chess.WHITE:
            # Small bonus for maintaining castling rights
            if board.has_kingside_castling_rights(chess.WHITE):
                bonus += 10  # Small bonus for kingside castling rights
            if board.has_queenside_castling_rights(chess.WHITE):
                bonus += 8   # Slightly smaller bonus for queenside (often less safe)
        else:
            if board.has_kingside_castling_rights(chess.BLACK):
                bonus += 10
            if board.has_queenside_castling_rights(chess.BLACK):
                bonus += 8
        
        return bonus
    
    def _evaluate_castling_status(self, color: chess.Color) -> int:
        """
        Evaluate whether the king has castled (larger bonus for having castled).
        This bonus is larger than castling rights to ensure action > preparation.
        
        Args:
            color: The color to evaluate
            
        Returns:
            Castling status bonus in centipawns
        """
        board = self.engine.board
        
        # Determine if king has castled by checking king position and move history
        king_square = board.king(color)
        
        if color == chess.WHITE:
            # White king starts on e1
            if king_square == chess.G1:  # Kingside castling
                return 25  # Larger bonus than castling rights (10)
            elif king_square == chess.C1:  # Queenside castling
                return 20  # Still good, but kingside often safer
        else:
            # Black king starts on e8
            if king_square == chess.G8:  # Kingside castling
                return 25
            elif king_square == chess.C8:  # Queenside castling
                return 20
        
        return 0  # King hasn't castled
    
    def _evaluate_king_pawn_shield(self, color: chess.Color) -> int:
        """
        Evaluate the pawn shield in front of the king.
        Bonus for having pawns in the three squares directly in front of the king.
        
        Args:
            color: The color to evaluate
            
        Returns:
            Pawn shield bonus in centipawns
        """
        board = self.engine.board
        king_square = board.king(color)
        
        if king_square is None:
            return 0  # No king found (shouldn't happen in valid positions)
        
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        shield_bonus = 0
        
        # Determine the rank in front of the king
        if color == chess.WHITE:
            # White king looks "up" the board (increasing rank)
            shield_rank = king_rank + 1
            if shield_rank > 7:  # Can't have pawns beyond rank 8
                return 0
        else:
            # Black king looks "down" the board (decreasing rank)
            shield_rank = king_rank - 1
            if shield_rank < 0:  # Can't have pawns below rank 1
                return 0
        
        # Check the three files: left, center, right of king
        for file_offset in [-1, 0, 1]:
            check_file = king_file + file_offset
            
            # Skip if file is off the board
            if check_file < 0 or check_file > 7:
                continue
                
            check_square = chess.square(check_file, shield_rank)
            piece = board.piece_at(check_square)
            
            # Bonus for having our own pawn in front of king
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                shield_bonus += 8  # Moderate bonus per protecting pawn
        
        return shield_bonus
    
    def _calculate_captures_score(self, color: chess.Color) -> int:
        """
        Calculate captures score using square-centric evaluation.
        
        For each square on the board, we calculate:
        1. Total value of our pieces that can attack it
        2. Total value of opponent pieces that can attack it  
        3. The difference gives us the "capture weight" for that square
        
        This immediately shows tactical advantages/disadvantages and focuses on
        immediate material exchanges rather than abstract opportunities.
        
        Args:
            color: The color to calculate captures score for
            
        Returns:
            Captures score in centipawns
        """
        if not is_feature_enabled('capture_calculation'):
            return int(get_disabled_value('capture_calculation'))
            
        total_capture_score = 0
        
        # Evaluate each square on the board
        for square in chess.SQUARES:
            square_score = self._evaluate_square_capture_weight(square, color)
            total_capture_score += square_score
        
        return total_capture_score
    
    def _evaluate_square_capture_weight(self, square: chess.Square, color: chess.Color) -> int:
        """
        Evaluate the capture weight for a specific square from our perspective.
        
        Calculate the net tactical value if all eligible pieces attack this square:
        - Our attacking pieces value (positive)
        - Opponent attacking pieces value (negative) 
        - If there's a piece on the square, factor in its value
        
        Args:
            square: The square to evaluate
            color: Our color (perspective for evaluation)
            
        Returns:
            Net capture weight in centipawns (positive = good for us)
        """
        # Get the piece currently on this square (if any)
        target_piece = self.engine.board.piece_at(square)
        
        # Calculate attacking piece values
        our_attackers_value = self._get_square_attackers_value(square, color)
        opponent_attackers_value = self._get_square_attackers_value(square, not color)
        
        # Base tactical weight: our attacking power minus opponent's
        tactical_weight = our_attackers_value - opponent_attackers_value
        
        # If there's a piece on this square, factor it into the evaluation
        if target_piece:
            piece_value = self.PIECE_VALUES[target_piece.piece_type]
            
            if target_piece.color != color:
                # Enemy piece: if we have tactical advantage, reward capturing it
                if tactical_weight > 0:
                    # Scale the piece value by our tactical advantage
                    capture_bonus = int(piece_value * min(tactical_weight / 1000.0, 1.0))
                    return capture_bonus
                else:
                    # We can't safely capture this piece
                    return 0
            else:
                # Our own piece: if opponent has tactical advantage, penalize exposure
                if opponent_attackers_value > our_attackers_value:
                    # Our piece is under threat
                    threat_penalty = int(piece_value * 0.3)  # 30% penalty for threatened piece
                    return -threat_penalty
                else:
                    # Our piece is safe or defended
                    return 0
        else:
            # Empty square: tactical control has some value for future moves
            if tactical_weight > 0:
                # We control this square better than opponent
                control_bonus = min(tactical_weight // 10, 10)  # Small bonus, capped at 10cp
                return control_bonus
            else:
                # No significant tactical advantage on empty square
                return 0
    
    def _get_square_attackers_value(self, square: chess.Square, color: chess.Color) -> int:
        """
        Calculate total value of pieces that can attack a given square.
        
        Args:
            square: The square to analyze
            color: The color of attacking pieces to count
            
        Returns:
            Total value of attacking pieces in centipawns
        """
        total_value = 0
        
        # Find all pieces of the given color that can attack this square
        for piece_square in chess.SQUARES:
            piece = self.engine.board.piece_at(piece_square)
            if piece and piece.color == color:
                # Check if this piece can attack the target square
                if self.engine.board.attacks(piece_square) & chess.BB_SQUARES[square]:
                    piece_value = self.PIECE_VALUES[piece.piece_type]
                    total_value += piece_value
        
        return total_value
    
        return total_value
    
    def _get_captures_analysis(self, color: chess.Color) -> Dict[str, Any]:
        """
        Get detailed captures analysis for debugging and evaluation details.
        Now uses square-centric evaluation approach.
        
        Args:
            color: The color to analyze captures for
            
        Returns:
            Dictionary with captures analysis details
        """
        significant_squares = []
        total_captures_score = 0
        controlled_squares = 0
        threatened_pieces = 0
        
        # Analyze each square for tactical significance
        for square in chess.SQUARES:
            square_weight = self._evaluate_square_capture_weight(square, color)
            
            if abs(square_weight) >= 10:  # Only report significant squares
                square_name = chess.square_name(square)
                target_piece = self.engine.board.piece_at(square)
                our_attackers = self._get_square_attackers_value(square, color)
                opponent_attackers = self._get_square_attackers_value(square, not color)
                
                analysis = {
                    'square': square_name,
                    'weight': square_weight,
                    'our_attackers_value': our_attackers,
                    'opponent_attackers_value': opponent_attackers,
                    'target_piece': target_piece.symbol() if target_piece else None,
                    'target_value': self.PIECE_VALUES[target_piece.piece_type] if target_piece else 0
                }
                significant_squares.append(analysis)
                
                if square_weight > 0:
                    controlled_squares += 1
                elif target_piece and target_piece.color == color:
                    threatened_pieces += 1
            
            total_captures_score += square_weight
        
        # Sort by absolute weight for better readability
        significant_squares.sort(key=lambda x: abs(x['weight']), reverse=True)
        
        return {
            'significant_squares': significant_squares,
            'total_score': total_captures_score,
            'controlled_squares': controlled_squares,
            'threatened_pieces': threatened_pieces,
            'analysis_type': 'square_centric'
        }

    def _get_threat_analysis(self, color: chess.Color) -> Dict[str, Any]:
        """
        Get detailed threat analysis for debugging and evaluation details.
        
        Args:
            color: The color to analyze threats for
            
        Returns:
            Dictionary with threat analysis details
        """
        threatened_pieces = []
        safe_pieces = []
        total_threat_penalty = 0
        
        for square in chess.SQUARES:
            piece = self.engine.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type != chess.KING:
                base_value = self.PIECE_VALUES[piece.piece_type]
                
                if self._is_piece_under_threat(square, color):
                    threat_penalty = base_value // 2  # 50% penalty
                    threatened_pieces.append({
                        'square': chess.square_name(square),
                        'piece': piece.symbol(),
                        'base_value': base_value,
                        'threat_penalty': threat_penalty,
                        'effective_value': base_value - threat_penalty
                    })
                    total_threat_penalty += threat_penalty
                else:
                    safe_pieces.append({
                        'square': chess.square_name(square),
                        'piece': piece.symbol(),
                        'value': base_value
                    })
        
        return {
            'threatened_pieces': threatened_pieces,
            'safe_pieces': safe_pieces,
            'total_threat_penalty': total_threat_penalty,
            'pieces_under_threat': len(threatened_pieces),
            'safe_pieces_count': len(safe_pieces)
        }
    
    def _calculate_tactical_combination_bonus(self, move: chess.Move, color: chess.Color) -> int:
        """
        Calculate bonus for moves that solve multiple tactical problems.
        This unifies threats and captures evaluation to prioritize moves that:
        1. Escape threats while capturing valuable pieces
        2. Remove attacking pieces while gaining material
        3. Create forcing sequences that improve position
        
        Args:
            move: The move to evaluate
            color: The color making the move
            
        Returns:
            Bonus score in centipawns
        """
        if not is_feature_enabled('tactical_combinations'):
            return int(get_disabled_value('tactical_combinations'))
            
        bonus = 0
        from_square = move.from_square
        to_square = move.to_square
        
        # Get the piece being moved
        piece = self.engine.board.piece_at(from_square)
        if not piece:
            return 0
            
        # Check if this move solves a threat (piece was under attack)
        escapes_threat = is_feature_enabled('threat_awareness') and self._is_piece_under_threat(from_square, color)
        
        # Check if this is a capture
        captured_piece = self.engine.board.piece_at(to_square)
        is_capture = captured_piece is not None
        
        # Debug output
        if str(move) in ['g2a8', 'g2b7']:
            print(f"DEBUG TACTICAL: Move {move}")
            print(f"  - escapes_threat: {escapes_threat}")
            print(f"  - is_capture: {is_capture}")
            print(f"  - piece: {piece.symbol() if piece else None}")
            print(f"  - captured_piece: {captured_piece.symbol() if captured_piece else None}")
            print(f"  - threat_awareness enabled: {is_feature_enabled('threat_awareness')}")
            print(f"  - tactical_combinations enabled: {is_feature_enabled('tactical_combinations')}")
        
        # Combination bonus: Escape threat + capture valuable piece
        if escapes_threat and is_capture:
            # Base bonus for solving both problems at once
            bonus += 200  # 2.0 pawn bonus for tactical combination
            
            # Additional bonus based on value difference
            piece_value = self.PIECE_VALUES[piece.piece_type]
            captured_value = self.PIECE_VALUES[captured_piece.piece_type]
            
            # Extra bonus if we're capturing a more valuable piece while escaping
            if captured_value > piece_value:
                bonus += min(captured_value - piece_value, 400)  # Cap at 4 pawns
            
            # Extra bonus if we're removing the piece that was threatening us
            if self.engine.board.is_attacked_by(not color, from_square):
                # Check if the captured piece was one of the attackers
                if captured_piece and self.engine.board.attacks(to_square):
                    if from_square in self.engine.board.attacks(to_square):
                        bonus += 100  # 1.0 pawn bonus for removing attacker
                        
            # Special bonus for escaping threat by capturing high-value pieces
            if captured_value >= 500:  # Rook or Queen
                bonus += 300  # Extra 3.0 pawn bonus for capturing rook/queen while escaping
        
        # Bonus for capturing while creating new threats
        elif is_capture:
            # Make the move temporarily to see if it creates new tactical opportunities
            self.engine.board.push(move)
            
            try:
                # Check if this capture creates new threats against enemy pieces
                new_threats = 0
                if is_feature_enabled('threat_awareness'):
                    for square in chess.SQUARES:
                        enemy_piece = self.engine.board.piece_at(square)
                        if enemy_piece and enemy_piece.color != color:
                            if self._is_piece_under_threat(square, not color):
                                new_threats += 1
                
                # Small bonus for captures that create additional threats
                if new_threats > 0:
                    bonus += min(new_threats * 10, 30)  # Max 0.3 pawn bonus
                    
            finally:
                self.engine.board.pop()
        
        # Bonus for moves that escape threats to central squares
        elif escapes_threat:
            # Small bonus for escaping to better squares
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            # Bonus for escaping to central squares (d4, d5, e4, e5)
            if to_file in [3, 4] and to_rank in [3, 4]:
                bonus += 15  # 0.15 pawn bonus for centralizing while escaping
        
        return bonus
    
    def _calculate_attack_patterns_score(self, color: chess.Color) -> int:
        """
        Calculate attack patterns score for pins, forks, discovered attacks, etc.
        
        Args:
            color: The color to evaluate attack patterns for
            
        Returns:
            Attack patterns score in centipawns
        """
        if not is_feature_enabled('attack_patterns'):
            return int(get_disabled_value('attack_patterns'))
            
        total_attack_score = 0
        
        # Pin detection and exploitation
        if is_feature_enabled('pin_detection'):
            total_attack_score += self._detect_pins(color)
        
        # Fork detection and creation
        if is_feature_enabled('fork_detection'):
            total_attack_score += self._detect_forks(color)
            
        # Discovered attacks and checks
        if is_feature_enabled('discovered_attacks'):
            total_attack_score += self._detect_discovered_attacks(color)
            
        # Skewer detection and creation  
        if is_feature_enabled('skewer_detection'):
            total_attack_score += self._detect_skewers(color)
            
        # Double attack patterns
        if is_feature_enabled('double_attack_patterns'):
            total_attack_score += self._detect_double_attacks(color)
        
        return total_attack_score
    
    def _calculate_piece_coordination_score(self, color: chess.Color) -> int:
        """
        Calculate piece coordination score for batteries, stacking, pairing, etc.
        
        Args:
            color: The color to evaluate coordination for
            
        Returns:
            Coordination score in centipawns
        """
        if not is_feature_enabled('piece_coordination'):
            return int(get_disabled_value('piece_coordination'))
            
        total_coordination_score = 0
        
        # Rook coordination (stacking and file control)
        if is_feature_enabled('rook_coordination'):
            total_coordination_score += self._evaluate_rook_coordination(color)
            
        # Battery attacks (queen-rook, queen-bishop)
        if is_feature_enabled('battery_attacks'):
            total_coordination_score += self._evaluate_battery_attacks(color)
            
        # Knight coordination (pairing and outpost control)
        if is_feature_enabled('knight_coordination'):
            total_coordination_score += self._evaluate_knight_coordination(color)
            
        # Bishop coordination (pairing and color coordination)
        if is_feature_enabled('bishop_coordination'):
            total_coordination_score += self._evaluate_bishop_coordination(color)
        
        return total_coordination_score
    
    # =============================================================================
    # ATTACK PATTERNS IMPLEMENTATION
    # =============================================================================
    
    def _detect_pins(self, color: chess.Color) -> int:
        """
        Detect and evaluate pins that we can exploit or are exploiting.
        
        A pin occurs when an enemy piece cannot move without exposing 
        a more valuable piece behind it to attack.
        
        Args:
            color: Our color (we're looking for pins we can exploit)
            
        Returns:
            Pin exploitation bonus in centipawns
        """
        pin_score = 0
        board = self.engine.board
        
        # Look for pins created by our sliding pieces (bishops, rooks, queens)
        sliding_pieces = []
        
        # Get our sliding pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                sliding_pieces.append((square, piece))
        
        # Check each sliding piece for pins it might be creating
        for piece_square, piece in sliding_pieces:
            pin_bonus = self._evaluate_pin_from_piece(piece_square, piece, color)
            pin_score += pin_bonus
        
        return pin_score
    
    def _evaluate_pin_from_piece(self, piece_square: chess.Square, piece: chess.Piece, color: chess.Color) -> int:
        """
        Evaluate pins created by a specific sliding piece.
        
        Args:
            piece_square: Square of our sliding piece
            piece: The sliding piece
            color: Our color
            
        Returns:
            Pin bonus for this piece in centipawns
        """
        pin_bonus = 0
        board = self.engine.board
        
        # Get attack rays from this piece
        attacks = board.attacks(piece_square)
        
        for target_square in attacks:
            target_piece = board.piece_at(target_square)
            
            # Skip if no piece or it's our piece
            if not target_piece or target_piece.color == color:
                continue
                
            # Check if this piece is pinned by looking beyond it
            pin_value = self._check_pin_beyond_piece(piece_square, target_square, piece, color)
            pin_bonus += pin_value
        
        return pin_bonus
    
    def _check_pin_beyond_piece(self, attacker_square: chess.Square, pinned_square: chess.Square, 
                               attacker_piece: chess.Piece, color: chess.Color) -> int:
        """
        Check if there's a more valuable piece behind the pinned piece.
        
        Args:
            attacker_square: Square of our attacking piece  
            pinned_square: Square of potentially pinned piece
            attacker_piece: Our attacking piece
            color: Our color
            
        Returns:
            Pin value bonus in centipawns
        """
        board = self.engine.board
        
        # Calculate direction vector from attacker to pinned piece
        attacker_file, attacker_rank = chess.square_file(attacker_square), chess.square_rank(attacker_square)
        pinned_file, pinned_rank = chess.square_file(pinned_square), chess.square_rank(pinned_square)
        
        file_diff = pinned_file - attacker_file
        rank_diff = pinned_rank - attacker_rank
        
        # Normalize direction (for sliding piece movement)
        if file_diff != 0:
            file_dir = 1 if file_diff > 0 else -1
        else:
            file_dir = 0
            
        if rank_diff != 0:
            rank_dir = 1 if rank_diff > 0 else -1
        else:
            rank_dir = 0
        
        # Look beyond the pinned piece in the same direction
        current_file = pinned_file + file_dir
        current_rank = pinned_rank + rank_dir
        
        while 0 <= current_file <= 7 and 0 <= current_rank <= 7:
            behind_square = chess.square(current_file, current_rank)
            behind_piece = board.piece_at(behind_square)
            
            if behind_piece:
                # Found a piece behind the pinned piece
                if behind_piece.color != color:
                    # Enemy piece behind - this could be a valuable pin target
                    pinned_piece = board.piece_at(pinned_square)
                    if pinned_piece:  # Safety check
                        pinned_value = self.PIECE_VALUES[pinned_piece.piece_type]
                        behind_value = self.PIECE_VALUES[behind_piece.piece_type]
                        
                        # Pin is valuable if the piece behind is more valuable than the pinned piece
                        if behind_value > pinned_value:
                            # Pin bonus based on value difference
                            pin_bonus = min(behind_value - pinned_value, 300)  # Cap at 3 pawns
                            return pin_bonus
                break  # Stop looking after first piece found
                
            # Move to next square in direction
            current_file += file_dir
            current_rank += rank_dir
        
        return 0  # No valuable pin found
    
    def _detect_forks(self, color: chess.Color) -> int:
        """
        Detect fork opportunities (one piece attacking multiple enemy pieces).
        
        Args:
            color: Our color
            
        Returns:
            Fork opportunity bonus in centipawns
        """
        fork_score = 0
        board = self.engine.board
        
        # Check each of our pieces for fork opportunities
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color:
                fork_bonus = self._evaluate_fork_from_piece(square, piece, color)
                fork_score += fork_bonus
        
        return fork_score
    
    def _evaluate_fork_from_piece(self, piece_square: chess.Square, piece: chess.Piece, color: chess.Color) -> int:
        """
        Evaluate fork opportunities from a specific piece.
        
        Args:
            piece_square: Square of our piece
            piece: Our piece
            color: Our color
            
        Returns:
            Fork bonus for this piece in centipawns
        """
        board = self.engine.board
        attacks = board.attacks(piece_square)
        
        # Count enemy pieces this piece attacks
        attacked_enemies = []
        total_attacked_value = 0
        
        for target_square in attacks:
            target_piece = board.piece_at(target_square)
            if target_piece and target_piece.color != color:
                attacked_enemies.append(target_piece)
                total_attacked_value += self.PIECE_VALUES[target_piece.piece_type]
        
        # Fork bonus if attacking multiple pieces
        if len(attacked_enemies) >= 2:
            our_piece_value = self.PIECE_VALUES[piece.piece_type]
            
            # Sort attacked pieces by value (highest first)
            attacked_enemies.sort(key=lambda p: self.PIECE_VALUES[p.piece_type], reverse=True)
            
            # Fork is valuable if we can capture the highest value piece
            # (opponent can only save one piece from the fork)
            highest_value = self.PIECE_VALUES[attacked_enemies[0].piece_type]
            second_value = self.PIECE_VALUES[attacked_enemies[1].piece_type] if len(attacked_enemies) > 1 else 0
            
            # Conservative bonus: assume we capture the second-highest value piece
            # (opponent will save the most valuable one)
            if second_value > our_piece_value:
                fork_bonus = min(second_value - our_piece_value, 400)  # Cap at 4 pawns
                return fork_bonus
            elif second_value > 0:
                # Even if we don't gain material, forks create tactical pressure
                fork_bonus = 50  # Small bonus for tactical pressure
                return fork_bonus
        
        return 0
    
    def _detect_discovered_attacks(self, color: chess.Color) -> int:
        """
        Detect discovered attack opportunities.
        
        Args:
            color: Our color
            
        Returns:
            Discovered attack bonus in centipawns
        """
        # For now, return a placeholder value
        # Full discovered attack detection requires move simulation
        discovered_score = 0
        
        # TODO: Implement full discovered attack detection
        # This requires checking if moving one piece reveals an attack from another
        
        return discovered_score
    
    def _detect_skewers(self, color: chess.Color) -> int:
        """
        Detect skewer opportunities (valuable piece forced to move, exposing less valuable piece).
        
        Args:
            color: Our color
            
        Returns:
            Skewer bonus in centipawns
        """
        skewer_score = 0
        board = self.engine.board
        
        # Look for skewers created by our sliding pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                skewer_bonus = self._evaluate_skewer_from_piece(square, piece, color)
                skewer_score += skewer_bonus
        
        return skewer_score
    
    def _evaluate_skewer_from_piece(self, piece_square: chess.Square, piece: chess.Piece, color: chess.Color) -> int:
        """
        Evaluate skewer opportunities from a sliding piece.
        Similar to pins, but the front piece is more valuable than the back piece.
        
        Args:
            piece_square: Square of our sliding piece
            piece: Our sliding piece
            color: Our color
            
        Returns:
            Skewer bonus in centipawns
        """
        # Skewer logic is similar to pins, but reversed value comparison
        # For now, use simplified implementation
        return 0  # TODO: Implement full skewer detection
    
    def _detect_double_attacks(self, color: chess.Color) -> int:
        """
        Detect multiple simultaneous threats.
        
        Args:
            color: Our color
            
        Returns:
            Double attack bonus in centipawns
        """
        double_attack_score = 0
        
        # Look for positions where we're creating multiple threats simultaneously
        # This could include combinations of the above patterns
        
        return double_attack_score
    
    # =============================================================================
    # PIECE COORDINATION IMPLEMENTATION  
    # =============================================================================
    
    def _evaluate_rook_coordination(self, color: chess.Color) -> int:
        """
        Evaluate rook stacking and file coordination.
        
        Args:
            color: Our color
            
        Returns:
            Rook coordination bonus in centipawns
        """
        coord_score = 0
        board = self.engine.board
        
        # Get all our rooks
        rooks = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.ROOK:
                rooks.append(square)
        
        # Check for rook stacking (same file or rank)
        for i, rook1 in enumerate(rooks):
            for rook2 in rooks[i+1:]:
                file1, rank1 = chess.square_file(rook1), chess.square_rank(rook1)
                file2, rank2 = chess.square_file(rook2), chess.square_rank(rook2)
                
                # Same file (doubled rooks)
                if file1 == file2:
                    coord_score += 80  # Strong bonus for doubled rooks
                    
                    # Extra bonus if file is open or semi-open
                    if self._is_file_open_or_semi_open(file1, color):
                        coord_score += 40
                
                # Same rank (rooks on same rank for back-rank attacks)
                elif rank1 == rank2:
                    # Especially valuable on 7th rank (attacking opponent's pawns)
                    if (color == chess.WHITE and rank1 == 6) or (color == chess.BLACK and rank1 == 1):
                        coord_score += 60  # Very strong for 7th rank
                    else:
                        coord_score += 30  # Good for other ranks
        
        return coord_score
    
    def _evaluate_battery_attacks(self, color: chess.Color) -> int:
        """
        Evaluate queen-rook and queen-bishop battery attacks.
        
        Args:
            color: Our color
            
        Returns:
            Battery attack bonus in centipawns
        """
        battery_score = 0
        board = self.engine.board
        
        # Find our queen
        queen_square = None
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.QUEEN:
                queen_square = square
                break
        
        if not queen_square:
            return 0  # No queen, no batteries
        
        queen_file, queen_rank = chess.square_file(queen_square), chess.square_rank(queen_square)
        
        # Check for queen-rook batteries
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.ROOK:
                rook_file, rook_rank = chess.square_file(square), chess.square_rank(square)
                
                # Same file or rank as queen
                if rook_file == queen_file or rook_rank == queen_rank:
                    battery_score += 50  # Bonus for queen-rook battery
        
        # Check for queen-bishop batteries  
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.BISHOP:
                bishop_file, bishop_rank = chess.square_file(square), chess.square_rank(square)
                
                # Same diagonal as queen
                if abs(bishop_file - queen_file) == abs(bishop_rank - queen_rank):
                    battery_score += 45  # Bonus for queen-bishop battery
        
        return battery_score
    
    def _evaluate_knight_coordination(self, color: chess.Color) -> int:
        """
        Evaluate knight pairing and outpost coordination.
        
        Args:
            color: Our color
            
        Returns:
            Knight coordination bonus in centipawns
        """
        knight_score = 0
        board = self.engine.board
        
        # Get all our knights
        knights = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.KNIGHT:
                knights.append(square)
        
        # Knight pairing bonus
        if len(knights) >= 2:
            # Check if knights are supporting each other or controlling key squares
            for knight1 in knights:
                for knight2 in knights:
                    if knight1 != knight2:
                        # Check if knights are mutually supporting
                        if self._knights_mutually_supporting(knight1, knight2):
                            knight_score += 40  # Bonus for mutual support
        
        # Outpost evaluation for each knight
        for knight_square in knights:
            outpost_bonus = self._evaluate_knight_outpost(knight_square, color)
            knight_score += outpost_bonus
        
        return knight_score
    
    def _evaluate_bishop_coordination(self, color: chess.Color) -> int:
        """
        Evaluate bishop pairing and color coordination.
        
        Args:
            color: Our color
            
        Returns:
            Bishop coordination bonus in centipawns
        """
        bishop_score = 0
        board = self.engine.board
        
        # Get all our bishops
        bishops = []
        light_square_bishops = 0
        dark_square_bishops = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.BISHOP:
                bishops.append(square)
                
                # Count light/dark square bishops
                if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0:
                    dark_square_bishops += 1
                else:
                    light_square_bishops += 1
        
        # Bishop pair bonus (two bishops > two knights)
        if len(bishops) >= 2:
            # Strong bonus for having both light and dark square bishops
            if light_square_bishops >= 1 and dark_square_bishops >= 1:
                bishop_score += 120  # Significant bonus for bishop pair
            else:
                # Multiple bishops on same color (less valuable)
                bishop_score += 40
        
        # Penalty for single bishop vs knights (single bishop < knight)  
        elif len(bishops) == 1:
            # Count opponent knights
            opponent_knights = 0
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color != color and piece.piece_type == chess.KNIGHT:
                    opponent_knights += 1
            
            # Small penalty if we have single bishop vs multiple knights
            if opponent_knights >= 2:
                bishop_score -= 20
        
        # Bishop-pawn color coordination
        for bishop_square in bishops:
            pawn_coord_bonus = self._evaluate_bishop_pawn_coordination(bishop_square, color)
            bishop_score += pawn_coord_bonus
        
        return bishop_score
    
    # =============================================================================
    # HELPER METHODS FOR COORDINATION
    # =============================================================================
    
    def _is_file_open_or_semi_open(self, file: int, color: chess.Color) -> bool:
        """
        Check if a file is open (no pawns) or semi-open (no our pawns).
        
        Args:
            file: The file to check (0-7)
            color: Our color
            
        Returns:
            True if file is open or semi-open for us
        """
        board = self.engine.board
        our_pawns_on_file = 0
        enemy_pawns_on_file = 0
        
        for rank in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                if piece.color == color:
                    our_pawns_on_file += 1
                else:
                    enemy_pawns_on_file += 1
        
        # Open file: no pawns at all
        if our_pawns_on_file == 0 and enemy_pawns_on_file == 0:
            return True
            
        # Semi-open file: no our pawns (but enemy may have pawns)
        if our_pawns_on_file == 0:
            return True
            
        return False
    
    def _knights_mutually_supporting(self, knight1: chess.Square, knight2: chess.Square) -> bool:
        """
        Check if two knights are mutually supporting each other.
        
        Args:
            knight1: First knight square
            knight2: Second knight square
            
        Returns:
            True if knights support each other
        """
        board = self.engine.board
        
        # Check if knight1 attacks squares around knight2 and vice versa
        knight1_attacks = board.attacks(knight1)
        knight2_attacks = board.attacks(knight2)
        
        # Knights are mutually supporting if they control complementary squares
        # This is a simplified check - could be enhanced
        return len(knight1_attacks & knight2_attacks) > 0
    
    def _evaluate_knight_outpost(self, knight_square: chess.Square, color: chess.Color) -> int:
        """
        Evaluate how good a knight's outpost position is.
        
        Args:
            knight_square: The knight's square
            color: Our color
            
        Returns:
            Outpost bonus in centipawns
        """
        # Knights on advanced, central squares that can't be attacked by pawns
        # are very valuable outposts
        
        file, rank = chess.square_file(knight_square), chess.square_rank(knight_square)
        
        # Advanced squares are more valuable  
        if color == chess.WHITE:
            advancement_bonus = max(0, (rank - 3) * 10)  # Bonus for ranks 4+ 
        else:
            advancement_bonus = max(0, (4 - rank) * 10)  # Bonus for ranks 4-
        
        # Central files are more valuable
        central_bonus = 0
        if file in [3, 4]:  # d and e files
            central_bonus = 15
        elif file in [2, 5]:  # c and f files  
            central_bonus = 10
        
        return advancement_bonus + central_bonus
    
    def _evaluate_bishop_pawn_coordination(self, bishop_square: chess.Square, color: chess.Color) -> int:
        """
        Evaluate bishop-pawn color coordination.
        
        Bishops work best when pawns are on opposite colored squares,
        allowing the bishop to control the squares the pawns can't.
        
        Args:
            bishop_square: The bishop's square
            color: Our color
            
        Returns:
            Coordination bonus in centipawns
        """
        board = self.engine.board
        
        # Determine bishop's square color
        bishop_on_light = (chess.square_file(bishop_square) + chess.square_rank(bishop_square)) % 2 == 1
        
        coord_bonus = 0
        our_pawns_good = 0
        our_pawns_bad = 0
        
        # Check our pawns
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                pawn_on_light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
                
                # Good coordination: pawn on opposite color from bishop
                if bishop_on_light != pawn_on_light:
                    our_pawns_good += 1
                else:
                    our_pawns_bad += 1
        
        # Bonus for good coordination, penalty for bad
        coord_bonus = our_pawns_good * 5 - our_pawns_bad * 3
        
        return coord_bonus
    
    def get_position_evaluation(self) -> Dict[str, int]:
        """
        Get detailed evaluation of the current position.
        
        Returns:
            Dictionary with evaluation details
        """
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        white_pst = self._calculate_pst_score(chess.WHITE)
        black_pst = self._calculate_pst_score(chess.BLACK)
        
        white_king_safety = self._calculate_king_safety(chess.WHITE)
        black_king_safety = self._calculate_king_safety(chess.BLACK)
        
        white_captures = self._calculate_captures_score(chess.WHITE)
        black_captures = self._calculate_captures_score(chess.BLACK)
        
        # Get threat analysis for detailed breakdown
        white_threats = self._get_threat_analysis(chess.WHITE)
        black_threats = self._get_threat_analysis(chess.BLACK)
        
        # Get captures analysis for detailed breakdown
        white_captures_analysis = self._get_captures_analysis(chess.WHITE)
        black_captures_analysis = self._get_captures_analysis(chess.BLACK)
        
        return {
            'white_material': white_material,
            'black_material': black_material,
            'material_difference': white_material - black_material,
            'white_pst': white_pst,
            'black_pst': black_pst,
            'pst_difference': white_pst - black_pst,
            'white_king_safety': white_king_safety,
            'black_king_safety': black_king_safety,
            'king_safety_difference': white_king_safety - black_king_safety,
            'white_captures': white_captures,
            'black_captures': black_captures,
            'captures_difference': white_captures - black_captures,
            'white_threat_penalty': white_threats['total_threat_penalty'],
            'black_threat_penalty': black_threats['total_threat_penalty'],
            'white_pieces_under_threat': white_threats['pieces_under_threat'],
            'black_pieces_under_threat': black_threats['pieces_under_threat'],
            'threat_difference': black_threats['total_threat_penalty'] - white_threats['total_threat_penalty'],
            'white_significant_squares': len(white_captures_analysis['significant_squares']),
            'white_controlled_squares': white_captures_analysis['controlled_squares'],
            'white_threatened_pieces': white_captures_analysis['threatened_pieces'],
            'black_significant_squares': len(black_captures_analysis['significant_squares']),
            'black_controlled_squares': black_captures_analysis['controlled_squares'],
            'black_threatened_pieces': black_captures_analysis['threatened_pieces'],
            'total_evaluation': self._evaluate_position(),
            'current_player_advantage': self._evaluate_position()
        }
    
    def get_move_analysis(self, move: chess.Move) -> dict:
        """
        Analyze a specific move and return detailed information.
        
        Args:
            move: The move to analyze
            
        Returns:
            Dictionary with move analysis details
        """
        # Get SAN notation before making the move
        move_san = self.engine.board.san(move)
        
        # Make the move temporarily
        self.engine.board.push(move)
        
        analysis = {
            'move': move.uci(),
            'san': move_san,
            'is_checkmate': self.engine.board.is_checkmate(),
            'is_stalemate': self.engine.board.is_stalemate(),
            'is_check': self.engine.board.is_check(),
            'is_draw': (
                self.engine.board.is_insufficient_material() or
                self.engine.board.is_seventyfive_moves() or
                self.engine.board.is_fivefold_repetition() or
                self.engine.board.can_claim_draw()
            ),
            'legal_moves_after': len(list(self.engine.board.legal_moves))
        }
        
        # Undo the move
        self.engine.board.pop()
        
        return analysis
    
    def get_selection_reasoning(self, legal_moves: List[chess.Move], selected_move: chess.Move) -> str:
        """
        Provide human-readable explanation of move selection reasoning.
        
        Args:
            legal_moves: All legal moves that were considered
            selected_move: The move that was selected
            
        Returns:
            String explanation of the selection logic
        """
        # Analyze the selected move
        move_analysis = self.get_move_analysis(selected_move)
        move_score = self._evaluate_move(selected_move)
        
        # Check what type of move this was
        checkmate_moves = self._find_checkmate_moves(legal_moves)
        filtered_moves = self._filter_bad_moves(legal_moves)
        
        if selected_move in checkmate_moves:
            return f"CHECKMATE MOVE: Selected {move_analysis['san']} to deliver checkmate!"
        
        elif len(filtered_moves) == 0:
            return f"FORCED MOVE: Selected {move_analysis['san']} (score: {move_score:+d}) - all moves lead to stalemate/draw"
        
        elif selected_move in filtered_moves:
            bad_moves_count = len(legal_moves) - len(filtered_moves)
            if bad_moves_count > 0:
                return f"EVALUATED MOVE: Selected {move_analysis['san']} (score: {move_score:+d}) - avoided {bad_moves_count} stalemate/draw moves"
            else:
                return f"BEST EVALUATION: Selected {move_analysis['san']} (score: {move_score:+d}) from {len(legal_moves)} moves"
        
        else:
            return f"FALLBACK MOVE: Selected {move_analysis['san']} (score: {move_score:+d}) - unexpected selection path"


class IntelligentSlowMateEngine(SlowMateEngine):
    """
    Enhanced SlowMate Engine with intelligent move selection.
    
    Extends the base SlowMateEngine with strategic move selection while
    maintaining full UCI compatibility and the existing API.
    """
    
    def __init__(self):
        """Initialize the intelligent engine."""
        super().__init__()
        self.intelligence = MoveIntelligence(self)
        self.enable_intelligence = True
        
        # Statistics tracking
        self.move_stats = {
            'checkmate_moves': 0,
            'avoided_stalemates': 0,
            'avoided_draws': 0,
            'forced_moves': 0,
            'evaluated_moves': 0,
            'random_moves': 0
        }
        
        # Evaluation tracking
        self.evaluation_history = []
    
    def select_move(self) -> Optional[chess.Move]:
        """
        Select a move using intelligent analysis or fallback to random.
        
        Returns:
            chess.Move: Selected move, or None if no legal moves available
        """
        if self.enable_intelligence:
            return self.intelligence.select_best_move()
        else:
            # Fallback to original random selection
            return super().select_move()
    
    def play_intelligent_move(self) -> Optional[str]:
        """
        Select and play an intelligent move with detailed reasoning.
        
        Returns:
            str: Algebraic notation of the move played, or None if game over
        """
        legal_moves = self.get_legal_moves()
        
        if not legal_moves:
            return None
        
        # Select move using intelligence
        move = self.select_move()
        if move is None:
            return None
        
        # Get reasoning before making the move
        reasoning = self.intelligence.get_selection_reasoning(legal_moves, move)
        
        # Get evaluation score
        move_score = self.intelligence._evaluate_move(move)
        
        # Convert to algebraic notation before making the move
        move_notation = self.board.san(move)
        
        # Make the move
        self.make_move(move)
        
        # Store evaluation history
        self.evaluation_history.append({
            'move': move_notation,
            'score': move_score,
            'reasoning': reasoning
        })
        
        # Update statistics
        if "CHECKMATE" in reasoning:
            self.move_stats['checkmate_moves'] += 1
        elif "FORCED" in reasoning:
            self.move_stats['forced_moves'] += 1
        elif "EVALUATED" in reasoning or "BEST EVALUATION" in reasoning:
            self.move_stats['evaluated_moves'] += 1
        elif "SAFE" in reasoning and "avoided" in reasoning:
            if "stalemate" in reasoning:
                self.move_stats['avoided_stalemates'] += 1
            else:
                self.move_stats['avoided_draws'] += 1
        else:
            self.move_stats['random_moves'] += 1
        
        return move_notation
    
    def get_move_reasoning(self) -> str:
        """
        Get the reasoning for the last move selection.
        
        Returns:
            String explanation of the last move's selection logic
        """
        # This would be enhanced to store and return the last reasoning
        # For now, return basic statistics
        total_moves = sum(self.move_stats.values())
        if total_moves == 0:
            return "No moves played yet"
        
        return (f"Move statistics: {self.move_stats['checkmate_moves']} checkmates, "
                f"{self.move_stats['avoided_stalemates']} stalemates avoided, "
                f"{self.move_stats['avoided_draws']} draws avoided, "
                f"{self.move_stats['forced_moves']} forced moves, "
                f"{self.move_stats['evaluated_moves']} evaluated moves, "
                f"{self.move_stats['random_moves']} random moves")
    
    def get_current_evaluation(self) -> int:
        """
        Get the evaluation of the current position in centipawns.
        
        Returns:
            Current position evaluation from current player's perspective
        """
        return self.intelligence._evaluate_position()
    
    def get_evaluation_details(self) -> Dict[str, int]:
        """
        Get detailed evaluation information for the current position.
        
        Returns:
            Dictionary with detailed evaluation breakdown
        """
        return self.intelligence.get_position_evaluation()
    
    def toggle_intelligence(self, enabled: Optional[bool] = None) -> bool:
        """
        Enable or disable intelligent move selection.
        
        Args:
            enabled: True to enable intelligence, False for random, None to toggle
            
        Returns:
            Current intelligence state
        """
        if enabled is None:
            self.enable_intelligence = not self.enable_intelligence
        else:
            self.enable_intelligence = enabled
        
        return self.enable_intelligence
