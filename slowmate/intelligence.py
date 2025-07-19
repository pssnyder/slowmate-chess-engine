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
    
    def __init__(self, engine: SlowMateEngine):
        """
        Initialize move intelligence with reference to engine.
        
        Args:
            engine: The SlowMateEngine instance to analyze
        """
        self.engine = engine
    
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
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        if current_player == chess.WHITE:
            score = white_material - black_material
        else:
            score = black_material - white_material
        
        # Undo the move
        self.engine.board.pop()
        
        return score
    
    def _evaluate_position(self) -> int:
        """
        Evaluate the current position and return score in centipawns.
        
        Returns:
            Evaluation score from current player's perspective
        """
        # Simple material evaluation
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        # Return score from current player's perspective
        if self.engine.board.turn == chess.WHITE:
            return white_material - black_material
        else:
            return black_material - white_material
    
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
    
    def get_position_evaluation(self) -> Dict[str, int]:
        """
        Get detailed evaluation of the current position.
        
        Returns:
            Dictionary with evaluation details
        """
        white_material = self._calculate_material(chess.WHITE)
        black_material = self._calculate_material(chess.BLACK)
        
        return {
            'white_material': white_material,
            'black_material': black_material,
            'material_difference': white_material - black_material,
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
