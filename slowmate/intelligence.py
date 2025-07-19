"""
SlowMate Chess Engine - Move Selection Intelligence

This module contains intelligent move selection logic that goes beyond random selection.
Current implementation includes critical game state handling for checkmate, stalemate, and draws.

Architecture: Modular move filters that can be easily extended with additional intelligence.
"""

import random
from typing import Optional, List, Tuple
import chess
from slowmate.engine import SlowMateEngine


class MoveIntelligence:
    """
    Intelligent move selection for SlowMate Chess Engine
    
    Provides layered move filtering and selection logic:
    1. Critical game state handling (checkmate, stalemate, draws)
    2. Future: Opening book, tactical patterns, positional evaluation
    3. Fallback: Random selection from remaining legal moves
    """
    
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
        
        # Phase 3: Select from remaining moves
        if filtered_moves:
            # We have good moves available
            return random.choice(filtered_moves)
        else:
            # All moves lead to stalemate/draw - we're forced to play one
            # This is a critical edge case handling
            return random.choice(legal_moves)
    
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
        
        # Check what type of move this was
        checkmate_moves = self._find_checkmate_moves(legal_moves)
        filtered_moves = self._filter_bad_moves(legal_moves)
        
        if selected_move in checkmate_moves:
            return f"CHECKMATE MOVE: Selected {move_analysis['san']} to deliver checkmate!"
        
        elif len(filtered_moves) == 0:
            return f"FORCED MOVE: Selected {move_analysis['san']} - all moves lead to stalemate/draw"
        
        elif selected_move in filtered_moves:
            bad_moves_count = len(legal_moves) - len(filtered_moves)
            if bad_moves_count > 0:
                return f"SAFE MOVE: Selected {move_analysis['san']} (avoided {bad_moves_count} stalemate/draw moves)"
            else:
                return f"RANDOM SELECTION: Selected {move_analysis['san']} from {len(legal_moves)} good moves"
        
        else:
            return f"FALLBACK MOVE: Selected {move_analysis['san']} (unexpected selection path)"


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
            'random_moves': 0
        }
    
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
        
        # Convert to algebraic notation before making the move
        move_notation = self.board.san(move)
        
        # Make the move
        self.make_move(move)
        
        # Update statistics (simplified for now)
        if "CHECKMATE" in reasoning:
            self.move_stats['checkmate_moves'] += 1
        elif "FORCED" in reasoning:
            self.move_stats['forced_moves'] += 1
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
                f"{self.move_stats['random_moves']} random moves")
    
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
