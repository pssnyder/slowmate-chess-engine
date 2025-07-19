"""
SlowMate Chess Engine - Move Selection Intelligence

This module contains intelligent move selection logic that goes beyond random selection.
Current implementation includes critical game state handling for checkmate, stalemate, and draws,
plus position evaluation based on material count and piece values.

Architecture: Modular move filters that can be easily extended with additional intelligence.
"""

import random
from typing import Optional, List, Tuple, Dict
import chess
from slowmate.engine import SlowMateEngine


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
        good_moves = []
        
        for move in legal_moves:
            # Make the move temporarily
            self.engine.board.push(move)
            
            # Check if this move creates a bad position
            is_bad_move = (
                self.engine.board.is_stalemate() or
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
        
        # Combine material and positional scores
        if current_player == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
        
        total_score = material_score + positional_score
        
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
        
        # Combine scores from current player's perspective
        if self.engine.board.turn == chess.WHITE:
            material_score = white_material - black_material
            positional_score = white_pst - black_pst
        else:
            material_score = black_material - white_material
            positional_score = black_pst - white_pst
        
        return material_score + positional_score
    
    def _calculate_material(self, color: chess.Color) -> int:
        """
        Calculate total material value for a given color.
        
        Args:
            color: The color to calculate material for
            
        Returns:
            Total material value in centipawns
        """
        total = 0
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, 
                          chess.ROOK, chess.QUEEN]:
            piece_count = len(self.engine.board.pieces(piece_type, color))
            total += piece_count * self.PIECE_VALUES[piece_type]
        
        return total
    
    def _calculate_pst_score(self, color: chess.Color) -> int:
        """
        Calculate piece-square table score for a given color.
        
        Args:
            color: The color to calculate PST score for
            
        Returns:
            Total PST score in centipawns
        """
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
        
        return {
            'white_material': white_material,
            'black_material': black_material,
            'material_difference': white_material - black_material,
            'white_pst': white_pst,
            'black_pst': black_pst,
            'pst_difference': white_pst - black_pst,
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
