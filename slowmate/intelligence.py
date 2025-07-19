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
    'threat_awareness': True,          # Piece threat detection and penalty system
    'capture_calculation': True,       # Capture opportunity evaluation
    'tactical_combinations': True,     # Unified tactical bonus (threats + captures)
    
    # Future features (placeholders for when implemented)
    'attack_patterns': False,          # Planned: Attack pattern recognition
    'piece_coordination': False,      # Planned: Piece coordination evaluation
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
    'attack_patterns': 0.0,
    'piece_coordination': 0.0,
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
        
        # Combine all scores from current player's perspective
        if current_player == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
            king_safety_score = white_king_safety - black_king_safety
            captures_score = white_captures - black_captures
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
            king_safety_score = black_king_safety - white_king_safety
            captures_score = black_captures - white_captures
        
        total_score = material_score + positional_score + king_safety_score + captures_score
        
        # TACTICAL COMBINATION BONUS: Reward moves that solve multiple tactical problems
        combination_bonus = self._calculate_tactical_combination_bonus(move, current_player)
        print(f"EVAL_DEBUG: Move {move} - player {current_player} - bonus {combination_bonus}")
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
        
        # Combine scores from current player's perspective
        if self.engine.board.turn == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
            king_safety_score = white_king_safety - black_king_safety
            captures_score = white_captures - black_captures
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
            king_safety_score = black_king_safety - white_king_safety
            captures_score = black_captures - white_captures
        
        return material_score + positional_score + king_safety_score + captures_score
    
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
        Calculate captures score - bonus/penalty for offensive capture opportunities.
        
        This evaluates all possible captures by pieces of the given color and assigns:
        - High positive bonus for winning captures (victim > attacker)
        - Small positive bonus for equal captures (victim = attacker)  
        - Heavy penalty for losing captures (victim < attacker)
        
        Args:
            color: The color to calculate captures score for
            
        Returns:
            Captures score in centipawns
        """
        if not is_feature_enabled('capture_calculation'):
            return int(get_disabled_value('capture_calculation'))
            
        capture_score = 0
        
        # Get all legal moves for this color
        if self.engine.board.turn != color:
            # If it's not this color's turn, we can't evaluate their captures directly
            # Instead, we need to analyze what captures would be available
            return self._calculate_potential_captures_score(color)
        
        legal_moves = list(self.engine.board.legal_moves)
        
        for move in legal_moves:
            if self.engine.board.is_capture(move):
                capture_evaluation = self._evaluate_capture_move(move)
                capture_score += capture_evaluation['net_score']
        
        return capture_score
    
    def _calculate_potential_captures_score(self, color: chess.Color) -> int:
        """
        Calculate potential captures score when it's not the given color's turn.
        
        This analyzes what captures would be available if it were this color's turn.
        Used for position evaluation when we need to consider both sides' opportunities.
        
        Args:
            color: The color to analyze potential captures for
            
        Returns:
            Potential captures score in centipawns
        """
        capture_score = 0
        
        # Look at each piece of the given color and see what it can capture
        for square in chess.SQUARES:
            piece = self.engine.board.piece_at(square)
            if piece and piece.color == color:
                # Get all squares this piece attacks
                attacks = self.engine.board.attacks(square)
                
                for target_square in attacks:
                    target_piece = self.engine.board.piece_at(target_square)
                    if target_piece and target_piece.color != color:
                        # This is a potential capture
                        capture_evaluation = self._evaluate_potential_capture(
                            piece, target_piece, square, target_square
                        )
                        capture_score += capture_evaluation['net_score']
        
        return capture_score
    
    def _evaluate_capture_move(self, move: chess.Move) -> Dict[str, Any]:
        """
        Evaluate a capture move and return detailed analysis.
        
        Args:
            move: The capture move to evaluate
            
        Returns:
            Dictionary with capture evaluation details
        """
        attacker_piece = self.engine.board.piece_at(move.from_square)
        victim_piece = self.engine.board.piece_at(move.to_square)
        
        if not attacker_piece or not victim_piece:
            return {'net_score': 0, 'type': 'not_capture'}
        
        return self._evaluate_potential_capture(
            attacker_piece, victim_piece, move.from_square, move.to_square
        )
    
    def _evaluate_potential_capture(self, attacker_piece, victim_piece, 
                                   attacker_square: chess.Square, victim_square: chess.Square) -> Dict[str, Any]:
        """
        Evaluate a potential capture between two pieces.
        
        Args:
            attacker_piece: The piece making the capture
            victim_piece: The piece being captured
            attacker_square: Square of the attacking piece
            victim_square: Square of the victim piece
            
        Returns:
            Dictionary with detailed capture evaluation
        """
        attacker_value = self.PIECE_VALUES[attacker_piece.piece_type]
        victim_value = self.PIECE_VALUES[victim_piece.piece_type]
        
        material_gain = victim_value - attacker_value
        
        if material_gain > 0:
            # Winning capture - victim worth more than attacker
            capture_type = 'winning'
            # High bonus for winning captures (75% of material gain)
            net_score = int(material_gain * 0.75)
            
        elif material_gain == 0:
            # Equal capture - same value pieces
            capture_type = 'equal'
            # Small bonus for equal captures (encourage activity)
            net_score = 25  # Small bonus, can be overridden by other factors
            
        else:
            # Losing capture - victim worth less than attacker
            capture_type = 'losing'
            # Heavy penalty - assume we'll lose our piece
            # Penalty is 90% of our piece value (we lose almost everything)
            net_score = int(material_gain * 0.9)  # This will be negative
        
        return {
            'type': capture_type,
            'attacker_value': attacker_value,
            'victim_value': victim_value,
            'material_gain': material_gain,
            'net_score': net_score,
            'attacker_square': chess.square_name(attacker_square),
            'victim_square': chess.square_name(victim_square),
            'attacker_piece': attacker_piece.symbol(),
            'victim_piece': victim_piece.symbol()
        }
    
    def _get_captures_analysis(self, color: chess.Color) -> Dict[str, Any]:
        """
        Get detailed captures analysis for debugging and evaluation details.
        
        Args:
            color: The color to analyze captures for
            
        Returns:
            Dictionary with captures analysis details
        """
        winning_captures = []
        equal_captures = []
        losing_captures = []
        total_captures_score = 0
        
        # Analyze potential captures for this color
        for square in chess.SQUARES:
            piece = self.engine.board.piece_at(square)
            if piece and piece.color == color:
                attacks = self.engine.board.attacks(square)
                
                for target_square in attacks:
                    target_piece = self.engine.board.piece_at(target_square)
                    if target_piece and target_piece.color != color:
                        capture_eval = self._evaluate_potential_capture(
                            piece, target_piece, square, target_square
                        )
                        
                        total_captures_score += capture_eval['net_score']
                        
                        if capture_eval['type'] == 'winning':
                            winning_captures.append(capture_eval)
                        elif capture_eval['type'] == 'equal':
                            equal_captures.append(capture_eval)
                        elif capture_eval['type'] == 'losing':
                            losing_captures.append(capture_eval)
        
        return {
            'winning_captures': winning_captures,
            'equal_captures': equal_captures,
            'losing_captures': losing_captures,
            'total_score': total_captures_score,
            'capture_count': len(winning_captures) + len(equal_captures) + len(losing_captures)
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
            print(f"DEBUG: Move {move} - escapes_threat: {escapes_threat}, is_capture: {is_capture}")
        
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
            'white_winning_captures': len(white_captures_analysis['winning_captures']),
            'white_equal_captures': len(white_captures_analysis['equal_captures']),
            'white_losing_captures': len(white_captures_analysis['losing_captures']),
            'black_winning_captures': len(black_captures_analysis['winning_captures']),
            'black_equal_captures': len(black_captures_analysis['equal_captures']),
            'black_losing_captures': len(black_captures_analysis['losing_captures']),
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
