"""
SlowMate Chess Engine - Opening Weights System

Manages opening preferences and intelligent move weighting:
- White preferences: London System, Queen's Gambit, Vienna Game
- Black preferences: Caro-Kann, French Defense, Dutch Defense, King's Indian Defense
- Dynamic cross-color adaptation
- Anti-repetition variety for tournament play

Features:
- Position-based preference evaluation
- Cross-color opening knowledge (can defend against preferred openings)
- Weighted randomness for variety
- Tournament-ready anti-repetition
"""

import json
import random
from typing import Dict, List, Optional, Tuple, Any
import chess
from chess import Board, Move


class OpeningWeights:
    """
    Opening preference and weighting system for intelligent move selection.
    
    Provides preference-guided opening selection while maintaining positional
    flexibility and tournament variety through weighted randomness.
    """
    
    # Preferred opening systems with weights
    WHITE_PREFERENCES = {
        'london_system': {
            'weight': 100,
            'key_moves': ['d4', 'Bf4', 'e3', 'Nf3', 'Bd3'],
            'positions': []  # Will be populated from data
        },
        'queens_gambit': {
            'weight': 90,
            'key_moves': ['d4', 'c4', 'Nc3', 'e3', 'Nf3'],
            'positions': []
        },
        'vienna_game': {
            'weight': 80,
            'key_moves': ['e4', 'Nc3', 'd3', 'f4', 'Nf3'],
            'positions': []
        }
    }
    
    BLACK_PREFERENCES = {
        'caro_kann': {
            'weight': 100,
            'key_moves': ['c6', 'd5', 'Bf5', 'e6', 'Nd7'],
            'positions': []
        },
        'french_defense': {
            'weight': 90,
            'key_moves': ['e6', 'd5', 'c5', 'Nc6', 'Bd7'],
            'positions': []
        },
        'dutch_defense': {
            'weight': 85,
            'key_moves': ['f5', 'd6', 'e6', 'Nf6', 'Be7'],
            'positions': []
        },
        'kings_indian': {
            'weight': 80,
            'key_moves': ['Nf6', 'g6', 'Bg7', 'd6', 'O-O'],
            'positions': []
        }
    }
    
    def __init__(self, data_dir: str = "data/openings"):
        """
        Initialize opening weights system.
        
        Args:
            data_dir: Directory containing preference data
        """
        self.data_dir = data_dir
        self.white_prefs = self.WHITE_PREFERENCES.copy()
        self.black_prefs = self.BLACK_PREFERENCES.copy()
        self.game_history = []  # Track recent games for variety
        self.max_history = 10   # Remember last 10 games
        
        self._load_preference_data()
    
    def _load_preference_data(self):
        """Load opening preference data from file."""
        try:
            preferences_file = f"{self.data_dir}/preferences.json"
            with open(preferences_file, 'r') as f:
                data = json.load(f)
                
                # Update white preferences if available
                if 'white_preferences' in data:
                    for opening, pref_data in data['white_preferences'].items():
                        if opening in self.white_prefs:
                            self.white_prefs[opening].update(pref_data)
                
                # Update black preferences if available
                if 'black_preferences' in data:
                    for opening, pref_data in data['black_preferences'].items():
                        if opening in self.black_prefs:
                            self.black_prefs[opening].update(pref_data)
                            
        except FileNotFoundError:
            # Use default preferences if file doesn't exist
            pass
        except Exception as e:
            print(f"Warning: Could not load preference data: {e}")
    
    def get_move_weight(self, board: Board, move: Move, available_moves: List[Move]) -> float:
        """
        Calculate preference weight for a given move.
        
        Args:
            board: Current position
            move: Move to evaluate
            available_moves: All available moves for context
            
        Returns:
            Weight multiplier (1.0 = neutral, >1.0 = preferred, <1.0 = discouraged)
        """
        base_weight = 1.0
        color = board.turn
        
        # Get opening system identification
        opening_info = self._identify_opening_system(board)
        
        # Apply preference weights based on color and opening
        if color == chess.WHITE:
            preference_weight = self._calculate_white_preference(board, move, opening_info)
        else:
            preference_weight = self._calculate_black_preference(board, move, opening_info)
        
        # Apply anti-repetition adjustment
        repetition_weight = self._calculate_repetition_adjustment(board, move)
        
        # Combine weights
        final_weight = base_weight * preference_weight * repetition_weight
        
        return max(0.1, min(10.0, final_weight))  # Clamp to reasonable range
    
    def _identify_opening_system(self, board: Board) -> Dict[str, float]:
        """
        Identify which opening system(s) the current position belongs to.
        
        Returns:
            Dictionary mapping opening names to confidence scores
        """
        move_history = []
        temp_board = Board()
        
        # Reconstruct move sequence
        for move in board.move_stack:
            move_history.append(temp_board.san(move))
            temp_board.push(move)
        
        opening_scores = {}
        
        # Check white openings
        for opening_name, opening_data in self.white_prefs.items():
            score = self._calculate_opening_match_score(move_history, opening_data['key_moves'])
            if score > 0:
                opening_scores[opening_name] = score
        
        # Check black openings
        for opening_name, opening_data in self.black_prefs.items():
            score = self._calculate_opening_match_score(move_history, opening_data['key_moves'])
            if score > 0:
                opening_scores[opening_name] = score
        
        return opening_scores
    
    def _calculate_opening_match_score(self, move_history: List[str], key_moves: List[str]) -> float:
        """
        Calculate how well move history matches an opening system.
        
        Args:
            move_history: Moves played in the game
            key_moves: Key moves that define the opening
            
        Returns:
            Match score (0.0 = no match, 1.0 = perfect match)
        """
        if not key_moves:
            return 0.0
            
        matches = 0
        for key_move in key_moves:
            if key_move in move_history:
                matches += 1
            elif len(move_history) > 6:  # Only penalize after reasonable development
                break
        
        return matches / len(key_moves)
    
    def _calculate_white_preference(self, board: Board, move: Move, opening_info: Dict) -> float:
        """Calculate preference weight for White moves."""
        weight = 1.0
        move_san = board.san(move)
        
        # London System preference
        if self._is_london_move(board, move_san):
            weight *= 1.3
        
        # Queen's Gambit preference
        elif self._is_queens_gambit_move(board, move_san):
            weight *= 1.2
            
        # Vienna Game preference
        elif self._is_vienna_move(board, move_san):
            weight *= 1.1
        
        # Boost if continuing established opening
        for opening_name, score in opening_info.items():
            if opening_name in self.white_prefs and score > 0.5:
                weight *= (1.0 + score * 0.2)
        
        return weight
    
    def _calculate_black_preference(self, board: Board, move: Move, opening_info: Dict) -> float:
        """Calculate preference weight for Black moves."""
        weight = 1.0
        move_san = board.san(move)
        
        # Caro-Kann preference
        if self._is_caro_kann_move(board, move_san):
            weight *= 1.3
            
        # French Defense preference  
        elif self._is_french_move(board, move_san):
            weight *= 1.2
            
        # Dutch Defense preference
        elif self._is_dutch_move(board, move_san):
            weight *= 1.15
            
        # King's Indian preference
        elif self._is_kings_indian_move(board, move_san):
            weight *= 1.1
        
        # Boost if continuing established opening
        for opening_name, score in opening_info.items():
            if opening_name in self.black_prefs and score > 0.5:
                weight *= (1.0 + score * 0.2)
        
        return weight
    
    def _calculate_repetition_adjustment(self, board: Board, move: Move) -> float:
        """
        Adjust weight to encourage variety in tournament play.
        
        Reduces weight of moves that lead to recently played openings.
        """
        if len(self.game_history) < 2:
            return 1.0  # No adjustment for first few games
            
        move_san = board.san(move)
        
        # Count how often this type of move was used recently
        recent_count = 0
        for game_moves in self.game_history[-5:]:  # Last 5 games
            if len(game_moves) > len(board.move_stack) and game_moves[len(board.move_stack)] == move_san:
                recent_count += 1
        
        # Reduce weight if move was used recently (anti-repetition)
        if recent_count > 0:
            adjustment = 1.0 - (recent_count * 0.15)  # Up to 45% reduction
            return max(0.3, adjustment)
            
        return 1.0
    
    def _is_london_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits London System pattern."""
        move_num = len(board.move_stack) // 2 + 1
        
        if move_num == 1 and move_san == 'd4':
            return True
        elif move_num == 2 and move_san == 'Bf4':
            return True  
        elif move_san in ['e3', 'Nf3', 'Bd3', 'Nbd2']:
            return True
            
        return False
    
    def _is_queens_gambit_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits Queen's Gambit pattern."""
        move_num = len(board.move_stack) // 2 + 1
        
        if move_num == 1 and move_san == 'd4':
            return True
        elif move_num == 2 and move_san == 'c4':
            return True
        elif move_san in ['Nc3', 'e3', 'Nf3', 'Bg5', 'cxd5']:
            return True
            
        return False
    
    def _is_vienna_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits Vienna Game pattern."""
        move_num = len(board.move_stack) // 2 + 1
        
        if move_num == 1 and move_san == 'e4':
            return True
        elif move_num == 2 and move_san == 'Nc3':
            return True
        elif move_san in ['f4', 'd3', 'Nf3', 'Bb5']:
            return True
            
        return False
    
    def _is_caro_kann_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits Caro-Kann pattern."""
        if move_san in ['c6', 'd5', 'Bf5', 'e6', 'Nd7', 'Ngf6']:
            return True
        return False
    
    def _is_french_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits French Defense pattern."""
        if move_san in ['e6', 'd5', 'c5', 'Nc6', 'Bd7', 'Be7']:
            return True
        return False
    
    def _is_dutch_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits Dutch Defense pattern."""
        if move_san in ['f5', 'd6', 'e6', 'Nf6', 'Be7', 'O-O']:
            return True
        return False
    
    def _is_kings_indian_move(self, board: Board, move_san: str) -> bool:
        """Check if move fits King's Indian pattern."""
        if move_san in ['Nf6', 'g6', 'Bg7', 'd6', 'O-O', 'e5']:
            return True
        return False
    
    def record_game(self, moves: List[str]):
        """
        Record a completed game for anti-repetition analysis.
        
        Args:
            moves: List of moves in SAN notation
        """
        self.game_history.append(moves[:15])  # Store first 15 moves
        
        # Maintain history limit
        if len(self.game_history) > self.max_history:
            self.game_history.pop(0)
    
    def get_preference_info(self, board: Board) -> Dict:
        """
        Get detailed preference information for debugging.
        
        Returns:
            Dictionary with preference analysis
        """
        opening_info = self._identify_opening_system(board)
        
        return {
            'current_color': 'white' if board.turn == chess.WHITE else 'black',
            'identified_openings': opening_info,
            'game_history_size': len(self.game_history),
            'move_number': len(board.move_stack) // 2 + 1,
            'white_preferences': list(self.white_prefs.keys()),
            'black_preferences': list(self.black_prefs.keys())
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get opening weights system statistics."""
        return {
            'white_preferences': len(self.white_prefs),
            'black_preferences': len(self.black_prefs),
            'game_history_size': len(self.game_history),
            'max_history': self.max_history,
            'data_loaded': bool(self.white_prefs or self.black_prefs)
        }
