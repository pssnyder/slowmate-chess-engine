"""
Transposition Table for SlowMate Chess Engine

This module implements a high-performance transposition table using Zobrist
hashing for position identification. Includes replacement strategies and
efficient memory management.

The transposition table stores previously searched positions to avoid
redundant search work and provides hash moves for move ordering.
"""

import time
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import chess

from slowmate.search.zobrist import ZobristHasher


class BoundType(Enum):
    """Types of bounds stored in transposition table entries."""
    EXACT = 0       # Exact score (PV node)
    LOWER_BOUND = 1 # Beta cutoff (score >= beta)
    UPPER_BOUND = 2 # Alpha cutoff (score <= alpha)


@dataclass
class TranspositionEntry:
    """Entry in the transposition table."""
    
    position_hash: int              # Full 64-bit Zobrist hash
    depth: int                      # Search depth when entry was stored
    score: int                      # Position evaluation
    bound_type: BoundType          # Type of bound (exact, lower, upper)
    best_move: Optional[chess.Move] # Best move found in this position
    age: int                       # Search age for replacement strategy
    
    def is_valid_for_depth(self, required_depth: int) -> bool:
        """Check if entry is valid for required search depth."""
        return self.depth >= required_depth
    
    def is_cutoff_score(self, alpha: int, beta: int) -> Optional[int]:
        """
        Check if stored score causes a cutoff.
        
        Args:
            alpha: Current alpha value
            beta: Current beta value
            
        Returns:
            Score if cutoff occurs, None otherwise
        """
        if self.bound_type == BoundType.EXACT:
            return self.score
        elif self.bound_type == BoundType.LOWER_BOUND and self.score >= beta:
            return self.score
        elif self.bound_type == BoundType.UPPER_BOUND and self.score <= alpha:
            return self.score
        return None


class TranspositionTable:
    """High-performance transposition table with replacement strategy."""
    
    def __init__(self, size_mb: int = 64):
        """
        Initialize transposition table.
        
        Args:
            size_mb: Size of table in megabytes
        """
        # Calculate table size (each entry is roughly 32 bytes)
        bytes_per_entry = 32
        self.table_size = (size_mb * 1024 * 1024) // bytes_per_entry
        
        # Ensure table size is power of 2 for efficient modulo
        self.table_size = 2 ** (self.table_size.bit_length() - 1)
        
        # Initialize hash table
        self.table: Dict[int, TranspositionEntry] = {}
        
        # Initialize Zobrist hasher
        self.zobrist = ZobristHasher()
        
        # Statistics
        self.stats = {
            'stores': 0,
            'lookups': 0,
            'hits': 0,
            'exact_hits': 0,
            'hash_moves_found': 0,
            'cutoffs': 0,
            'replacements': 0,
            'collisions': 0
        }
        
        # Current search age for replacement strategy
        self.current_age = 0
    
    def clear(self):
        """Clear the transposition table."""
        self.table.clear()
        for key in self.stats:
            self.stats[key] = 0
        self.current_age = 0
    
    def new_search(self):
        """Increment age for new search."""
        self.current_age += 1
    
    def store(self, board: chess.Board, depth: int, score: int, 
             bound_type: BoundType, best_move: Optional[chess.Move] = None):
        """
        Store position in transposition table.
        
        Args:
            board: Current board position
            depth: Search depth
            score: Position evaluation
            bound_type: Type of bound
            best_move: Best move found (if any)
        """
        position_hash = self.zobrist.hash_position(board)
        table_index = position_hash % self.table_size
        
        self.stats['stores'] += 1
        
        # Check if we should replace existing entry
        existing_entry = self.table.get(table_index)
        
        if existing_entry is None:
            # Empty slot - store entry
            self._store_entry(table_index, position_hash, depth, score, 
                            bound_type, best_move)
        elif existing_entry.position_hash == position_hash:
            # Same position - update if better
            if self._should_replace_same_position(existing_entry, depth, bound_type):
                self._store_entry(table_index, position_hash, depth, score, 
                                bound_type, best_move)
            else:
                # Keep existing entry but update best move if we don't have one
                if existing_entry.best_move is None and best_move is not None:
                    existing_entry.best_move = best_move
        else:
            # Hash collision - use replacement strategy
            self.stats['collisions'] += 1
            if self._should_replace_different_position(existing_entry, depth):
                self.stats['replacements'] += 1
                self._store_entry(table_index, position_hash, depth, score, 
                                bound_type, best_move)
    
    def _store_entry(self, table_index: int, position_hash: int, depth: int, 
                    score: int, bound_type: BoundType, best_move: Optional[chess.Move]):
        """Store entry at table index."""
        self.table[table_index] = TranspositionEntry(
            position_hash=position_hash,
            depth=depth,
            score=score,
            bound_type=bound_type,
            best_move=best_move,
            age=self.current_age
        )
    
    def _should_replace_same_position(self, existing: TranspositionEntry, 
                                    new_depth: int, new_bound_type: BoundType) -> bool:
        """
        Decide if we should replace entry for same position.
        
        Args:
            existing: Existing entry
            new_depth: New search depth
            new_bound_type: New bound type
            
        Returns:
            True if we should replace
        """
        # Always replace if new search is deeper
        if new_depth > existing.depth:
            return True
            
        # Replace if same depth but new bound is exact and old is not
        if (new_depth == existing.depth and 
            new_bound_type == BoundType.EXACT and 
            existing.bound_type != BoundType.EXACT):
            return True
            
        # Replace if entry is from much older search
        if self.current_age - existing.age > 10:
            return True
            
        return False
    
    def _should_replace_different_position(self, existing: TranspositionEntry, 
                                         new_depth: int) -> bool:
        """
        Decide if we should replace entry for different position.
        
        Args:
            existing: Existing entry
            new_depth: New search depth
            
        Returns:
            True if we should replace
        """
        # Prefer newer entries
        age_factor = self.current_age - existing.age
        
        # Prefer deeper searches
        depth_factor = new_depth - existing.depth
        
        # Simple replacement strategy: replace if significantly newer or deeper
        return age_factor >= 2 or depth_factor >= 2
    
    def lookup(self, board: chess.Board, depth: int, alpha: int, beta: int) -> tuple:
        """
        Look up position in transposition table.
        
        Args:
            board: Current board position
            depth: Required search depth
            alpha: Current alpha value
            beta: Current beta value
            
        Returns:
            Tuple of (score, best_move, hit_type)
            score: Position score if cutoff, None otherwise
            best_move: Best move if found, None otherwise
            hit_type: 'exact', 'cutoff', 'hash_move', or 'miss'
        """
        position_hash = self.zobrist.hash_position(board)
        table_index = position_hash % self.table_size
        
        self.stats['lookups'] += 1
        
        entry = self.table.get(table_index)
        if entry is None:
            return None, None, 'miss'
        
        # Verify this is the same position (avoid hash collisions)
        if entry.position_hash != position_hash:
            return None, None, 'miss'
        
        self.stats['hits'] += 1
        
        # Check if we can use the score (sufficient depth)
        if entry.is_valid_for_depth(depth):
            cutoff_score = entry.is_cutoff_score(alpha, beta)
            if cutoff_score is not None:
                self.stats['cutoffs'] += 1
                if entry.bound_type == BoundType.EXACT:
                    self.stats['exact_hits'] += 1
                    return cutoff_score, entry.best_move, 'exact'
                else:
                    return cutoff_score, entry.best_move, 'cutoff'
        
        # Can't use score, but return hash move if available
        if entry.best_move is not None:
            self.stats['hash_moves_found'] += 1
            return None, entry.best_move, 'hash_move'
        
        return None, None, 'miss'
    
    def get_hash_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get hash move for position (for move ordering).
        
        Args:
            board: Current board position
            
        Returns:
            Best move if found, None otherwise
        """
        position_hash = self.zobrist.hash_position(board)
        table_index = position_hash % self.table_size
        
        entry = self.table.get(table_index)
        if entry and entry.position_hash == position_hash:
            return entry.best_move
        return None
    
    def get_principal_variation(self, board: chess.Board, max_depth: int = 10) -> list:
        """
        Extract principal variation from transposition table.
        
        Args:
            board: Starting board position
            max_depth: Maximum PV depth to extract
            
        Returns:
            List of moves in principal variation
        """
        pv = []
        temp_board = board.copy()
        
        for _ in range(max_depth):
            hash_move = self.get_hash_move(temp_board)
            if hash_move is None or hash_move in pv:  # Avoid cycles
                break
                
            # Verify move is legal
            if hash_move not in temp_board.legal_moves:
                break
                
            pv.append(hash_move)
            temp_board.push(hash_move)
            
            # Stop if game ends
            if temp_board.is_game_over():
                break
        
        return pv
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get transposition table statistics."""
        stats: Dict[str, Any] = self.stats.copy()
        
        # Calculate percentages
        if stats['lookups'] > 0:
            stats['hit_rate'] = (stats['hits'] / stats['lookups']) * 100
            stats['cutoff_rate'] = (stats['cutoffs'] / stats['lookups']) * 100
            stats['hash_move_rate'] = (stats['hash_moves_found'] / stats['lookups']) * 100
        else:
            stats['hit_rate'] = 0.0
            stats['cutoff_rate'] = 0.0
            stats['hash_move_rate'] = 0.0
        
        # Table utilization
        stats['table_size'] = self.table_size
        stats['entries_used'] = len(self.table)
        stats['utilization'] = (len(self.table) / max(self.table_size, 1)) * 100
        stats['current_age'] = self.current_age
        
        return stats
    
    def resize(self, size_mb: int):
        """
        Resize transposition table.
        
        Args:
            size_mb: New size in megabytes
        """
        # Store current entries
        old_entries = list(self.table.values())
        
        # Clear and resize
        self.clear()
        bytes_per_entry = 32
        self.table_size = (size_mb * 1024 * 1024) // bytes_per_entry
        self.table_size = 2 ** (self.table_size.bit_length() - 1)
        
        # Re-insert valid entries
        for entry in old_entries:
            table_index = entry.position_hash % self.table_size
            if table_index not in self.table:
                self.table[table_index] = entry
