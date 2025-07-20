"""
SlowMate Chess Engine - Opening Book System

Fast-access opening move reference library with comprehensive coverage:
- Mainlines: 10+ moves until position stability/advantage
- Sidelines: 8+ moves for major variations  
- Edge cases: 3-5 moves for challenging positions
- Universal base: 1-2 moves from all major starting positions

Features:
- Position-based lookup (not rigid opening adherence)
- Transposition handling
- Weighted preference system integration
- Performance optimized with hash-based lookups
"""

import json
import os
from typing import Optional, List, Dict, Tuple, Any
import chess
from chess import Board, Move


class OpeningBook:
    """
    Fast-access opening book with comprehensive coverage and intelligent selection.
    
    Provides move recommendations based on position analysis rather than
    memorized sequences, with support for weighted preferences and anti-repetition.
    """
    
    def __init__(self, data_dir: str = "data/openings"):
        """
        Initialize opening book with position database.
        
        Args:
            data_dir: Directory containing opening book data files
        """
        self.data_dir = data_dir
        self.mainlines = {}      # 10+ move coverage
        self.sidelines = {}      # 8+ move variations
        self.edge_cases = {}     # 3-5 move challenging positions
        self.preferences = {}    # Opening weights and preferences
        
        self.position_cache = {}  # Performance optimization
        self.is_loaded = False
        
        # Load opening data if available
        self._load_opening_data()
    
    def _load_opening_data(self):
        """Load opening book data from JSON files."""
        try:
            # Load mainlines (comprehensive coverage)
            mainlines_file = os.path.join(self.data_dir, "mainlines.json")
            if os.path.exists(mainlines_file):
                with open(mainlines_file, 'r') as f:
                    self.mainlines = json.load(f)
            
            # Load sidelines (variation support)
            sidelines_file = os.path.join(self.data_dir, "sidelines.json")
            if os.path.exists(sidelines_file):
                with open(sidelines_file, 'r') as f:
                    self.sidelines = json.load(f)
                    
            # Load edge cases (fast bypass positions)
            edge_cases_file = os.path.join(self.data_dir, "edge_cases.json")
            if os.path.exists(edge_cases_file):
                with open(edge_cases_file, 'r') as f:
                    self.edge_cases = json.load(f)
                    
            # Load preferences (opening weights)
            preferences_file = os.path.join(self.data_dir, "preferences.json")
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r') as f:
                    self.preferences = json.load(f)
                    
            self.is_loaded = True
            
        except Exception as e:
            print(f"Warning: Could not load opening book data: {e}")
            self.is_loaded = False
    
    def get_book_move(self, board: Board) -> Optional[Move]:
        """
        Get the best opening book move for the current position.
        
        Priority order:
        1. Mainline moves (highest priority - comprehensive coverage)
        2. Sideline moves (variation support)
        3. Edge case moves (fast bypass for challenging evaluations)
        
        Args:
            board: Current chess position
            
        Returns:
            Best book move if available, None if position not in book
        """
        if not self.is_loaded:
            return None
            
        position_key = self._get_position_key(board)
        
        # Check cache first for performance
        if position_key in self.position_cache:
            return self.position_cache[position_key]
        
        # Priority 1: Check mainlines (10+ move coverage)
        move = self._get_move_from_book(position_key, self.mainlines)
        if move:
            self.position_cache[position_key] = move
            return move
            
        # Priority 2: Check sidelines (8+ move variations)
        move = self._get_move_from_book(position_key, self.sidelines)
        if move:
            self.position_cache[position_key] = move
            return move
            
        # Priority 3: Check edge cases (3-5 move challenging positions)
        move = self._get_move_from_book(position_key, self.edge_cases)
        if move:
            self.position_cache[position_key] = move
            return move
            
        # No book move found
        self.position_cache[position_key] = None
        return None
    
    def _get_position_key(self, board: Board) -> str:
        """
        Generate a unique key for the current position.
        
        Uses FEN without move counters for transposition handling.
        """
        # Use FEN but ignore move counters for transposition independence
        fen_parts = board.fen().split()
        position_fen = " ".join(fen_parts[:4])  # Position, color, castling, en passant
        return position_fen
    
    def _get_move_from_book(self, position_key: str, book_data: Dict) -> Optional[Move]:
        """
        Look up move from specific book section with weighted selection.
        
        Args:
            position_key: Position identifier
            book_data: Book section to search (mainlines/sidelines/edge_cases)
            
        Returns:
            Selected move or None if not found
        """
        if position_key not in book_data:
            return None
            
        position_data = book_data[position_key]
        
        # If single move, return it
        if isinstance(position_data, str):
            try:
                return Move.from_uci(position_data)
            except:
                return None
        
        # If multiple moves with weights, select intelligently
        if isinstance(position_data, dict):
            return self._select_weighted_move(position_data)
        
        # If list of moves, select with preference system
        if isinstance(position_data, list):
            return self._select_from_list(position_data)
            
        return None
    
    def _select_weighted_move(self, move_data: Dict) -> Optional[Move]:
        """
        Select move from weighted options with preference consideration.
        
        Format: {"e4": 50, "d4": 30, "Nf3": 20}
        """
        import random
        
        # Create weighted list for random selection
        moves = []
        weights = []
        
        for move_uci, weight in move_data.items():
            try:
                move = Move.from_uci(move_uci)
                moves.append(move)
                weights.append(weight)
            except:
                continue
        
        if not moves:
            return None
            
        # Weighted random selection for variety
        selected_move = random.choices(moves, weights=weights)[0]
        return selected_move
    
    def _select_from_list(self, move_list: List[str]) -> Optional[Move]:
        """
        Select move from list with anti-repetition variety.
        """
        import random
        
        valid_moves = []
        for move_uci in move_list:
            try:
                move = Move.from_uci(move_uci)
                valid_moves.append(move)
            except:
                continue
                
        if valid_moves:
            # Random selection for variety in tournament play
            return random.choice(valid_moves)
            
        return None
    
    def is_in_opening_book(self, board: Board) -> bool:
        """
        Check if current position has opening book coverage.
        
        Args:
            board: Current chess position
            
        Returns:
            True if position is covered by opening book
        """
        position_key = self._get_position_key(board)
        return (position_key in self.mainlines or 
                position_key in self.sidelines or 
                position_key in self.edge_cases)
    
    def get_book_info(self, board: Board) -> Dict[str, Any]:
        """
        Get detailed information about opening book coverage for position.
        
        Args:
            board: Current chess position
            
        Returns:
            Dictionary with book coverage details for debugging
        """
        position_key = self._get_position_key(board)
        
        info = {
            'position_key': position_key,
            'in_mainlines': position_key in self.mainlines,
            'in_sidelines': position_key in self.sidelines,
            'in_edge_cases': position_key in self.edge_cases,
            'book_loaded': self.is_loaded,
            'cache_size': len(self.position_cache)
        }
        
        # Add available moves if in book
        if info['in_mainlines']:
            info['mainline_moves'] = self.mainlines[position_key]
        if info['in_sidelines']:
            info['sideline_moves'] = self.sidelines[position_key]  
        if info['in_edge_cases']:
            info['edge_case_moves'] = self.edge_cases[position_key]
            
        return info
    
    def clear_cache(self):
        """Clear position cache to free memory."""
        self.position_cache.clear()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get opening book statistics for monitoring.
        
        Returns:
            Dictionary with coverage statistics
        """
        return {
            'mainline_positions': len(self.mainlines),
            'sideline_positions': len(self.sidelines),
            'edge_case_positions': len(self.edge_cases),
            'total_positions': len(self.mainlines) + len(self.sidelines) + len(self.edge_cases),
            'cached_lookups': len(self.position_cache),
            'is_loaded': self.is_loaded
        }
