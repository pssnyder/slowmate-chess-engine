"""
Tablebase module for SlowMate Chess Engine
Provides perfect endgame move selection for supported positions.
"""
import os
import json
from typing import Optional, List

class Tablebase:
    def __init__(self, tablebase_path: Optional[str] = None):
        self.tablebase_path = tablebase_path or os.path.join(os.path.dirname(__file__), '../../data/endgames/tablebase.json')
        self.tablebase = self._load_tablebase()

    def _load_tablebase(self) -> dict:
        if os.path.exists(self.tablebase_path):
            with open(self.tablebase_path, 'r') as f:
                return json.load(f)
        return {}

    def get_tablebase_moves(self, fen: str) -> List[str]:
        """
        Returns a list of perfect moves for the given FEN position if available.
        """
        return self.tablebase.get(fen, [])

    def select_tablebase_move(self, fen: str) -> Optional[str]:
        """
        Selects the best tablebase move for the given FEN position, if available.
        """
        moves = self.get_tablebase_moves(fen)
        if moves:
            # For simplicity, pick the first move (could be extended for WDL/DTZ)
            return moves[0]
        return None

    def in_tablebase(self, fen: str) -> bool:
        """
        Returns True if the position is in the tablebase.
        """
        return fen in self.tablebase
