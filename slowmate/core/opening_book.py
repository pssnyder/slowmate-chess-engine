"""
OpeningBook module for SlowMate Chess Engine
Manages opening moves and book logic for enhanced opening play.
"""
import os
import json
import random
from typing import Optional, List

class OpeningBook:
    def __init__(self, book_path: Optional[str] = None):
        self.book_path = book_path or os.path.join(os.path.dirname(__file__), '../../data/openings/opening_book.json')
        self.book = self._load_book()

    def _load_book(self) -> dict:
        if os.path.exists(self.book_path):
            with open(self.book_path, 'r') as f:
                return json.load(f)
        return {}

    def get_book_moves(self, fen: str) -> List[str]:
        """
        Returns a list of book moves for the given FEN position.
        """
        return self.book.get(fen, [])

    def select_book_move(self, fen: str) -> Optional[str]:
        """
        Selects a random book move for the given FEN position, if available.
        """
        moves = self.get_book_moves(fen)
        if moves:
            return random.choice(moves)
        return None

    def in_book(self, fen: str) -> bool:
        """
        Returns True if the position is in the opening book.
        """
        return fen in self.book
