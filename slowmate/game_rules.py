#!/usr/bin/env python3
"""
SlowMate v0.4.05 - Game Rules & Draw Detection Implementation
Phase 1 of v0.5.0 development: Critical game rule compliance features.
"""

import chess
from typing import List, Dict, Set, Optional, Any

class GameRulesManager:
    """Manages chess game rules including draw detection and position tracking."""
    
    def __init__(self):
        """Initialize game rules manager."""
        self.position_history: List[str] = []  # FEN positions for repetition
        self.move_history: List[str] = []      # Move history for analysis
        self.halfmove_counts: List[int] = []   # Halfmove clock history
        
        # Draw tracking
        self.repetition_count: Dict[str, int] = {}
        self.current_repetitions = 0
        
        # Game state
        self.game_result = None  # None, "1-0", "0-1", "1/2-1/2"
        self.game_termination = None  # "checkmate", "stalemate", "threefold", "50move", etc.
        
    def add_position(self, board: chess.Board, move: Optional[chess.Move] = None):
        """Add a position to the game history and check for draws."""
        fen = board.fen()
        
        # Store position and move
        self.position_history.append(fen)
        self.halfmove_counts.append(board.halfmove_clock)
        
        if move:
            self.move_history.append(move.uci())
        
        # Update repetition tracking
        position_key = self._get_position_key(board)
        self.repetition_count[position_key] = self.repetition_count.get(position_key, 0) + 1
        self.current_repetitions = self.repetition_count[position_key]
        
        # Check for game termination
        self._check_game_termination(board)
    
    def _get_position_key(self, board: chess.Board) -> str:
        """Get position key for repetition detection (FEN without move counters)."""
        fen_parts = board.fen().split(' ')
        # Use position, turn, castling, en passant (not halfmove/fullmove counters)
        return ' '.join(fen_parts[:4])
    
    def _check_game_termination(self, board: chess.Board):
        """Check if the game has terminated and set result."""
        # Checkmate
        if board.is_checkmate():
            self.game_termination = "checkmate"
            self.game_result = "0-1" if board.turn else "1-0"
            return
        
        # Stalemate
        if board.is_stalemate():
            self.game_termination = "stalemate"
            self.game_result = "1/2-1/2"
            return
        
        # Insufficient material
        if board.is_insufficient_material():
            self.game_termination = "insufficient_material"
            self.game_result = "1/2-1/2"
            return
        
        # Threefold repetition
        if self.current_repetitions >= 3:
            self.game_termination = "threefold_repetition"
            self.game_result = "1/2-1/2"
            return
        
        # 50-move rule
        if board.halfmove_clock >= 100:  # 50 moves by each side = 100 halfmoves
            self.game_termination = "fifty_moves"
            self.game_result = "1/2-1/2"
            return
        
        # Game continues
        self.game_termination = None
        self.game_result = None
    
    def is_threefold_repetition(self) -> bool:
        """Check if current position is a threefold repetition."""
        return self.current_repetitions >= 3
    
    def is_fifty_move_rule(self, board: chess.Board) -> bool:
        """Check if 50-move rule applies."""
        return board.halfmove_clock >= 100
    
    def can_claim_draw(self, board: chess.Board) -> bool:
        """Check if a draw can be claimed."""
        return (self.is_threefold_repetition() or 
                self.is_fifty_move_rule(board) or
                board.is_stalemate() or
                board.is_insufficient_material())
    
    def get_repetition_info(self) -> Dict[str, int]:
        """Get current repetition information."""
        return {
            "current_repetitions": self.current_repetitions,
            "can_claim_threefold": self.current_repetitions >= 3,
            "approaching_threefold": self.current_repetitions == 2
        }
    
    def get_fifty_move_info(self, board: chess.Board) -> Dict[str, int]:
        """Get 50-move rule information."""
        halfmoves = board.halfmove_clock
        return {
            "halfmove_clock": halfmoves,
            "moves_to_fifty": max(0, 100 - halfmoves),
            "can_claim_fifty": halfmoves >= 100,
            "approaching_fifty": halfmoves >= 90
        }
    
    def get_game_status(self, board: chess.Board) -> Dict[str, Any]:
        """Get comprehensive game status."""
        return {
            "result": self.game_result,
            "termination": self.game_termination,
            "is_game_over": self.game_result is not None,
            "repetition_info": self.get_repetition_info(),
            "fifty_move_info": self.get_fifty_move_info(board),
            "can_claim_draw": self.can_claim_draw(board),
            "total_positions": len(self.position_history),
            "total_moves": len(self.move_history)
        }
    
    def reset_game(self):
        """Reset all game tracking for new game."""
        self.position_history.clear()
        self.move_history.clear()
        self.halfmove_counts.clear()
        self.repetition_count.clear()
        self.current_repetitions = 0
        self.game_result = None
        self.game_termination = None

# Test the game rules manager
def test_game_rules():
    """Test game rules implementation."""
    print("🧪 Testing Game Rules Manager")
    print("=" * 40)
    
    # Test 1: Basic position tracking
    print("\n1. Testing position tracking...")
    manager = GameRulesManager()
    board = chess.Board()
    
    manager.add_position(board)
    print(f"   Positions tracked: {len(manager.position_history)}")
    print(f"   Current repetitions: {manager.current_repetitions}")
    
    # Test 2: Threefold repetition
    print("\n2. Testing threefold repetition...")
    board = chess.Board()
    manager = GameRulesManager()
    
    # Create repetition: Nf3-Ng1-Nf3-Ng1-Nf3
    moves = ["g1f3", "b8c6", "f3g1", "c6b8", "g1f3", "b8c6", "f3g1", "c6b8", "g1f3"]
    
    for move_uci in moves:
        move = chess.Move.from_uci(move_uci)
        board.push(move)
        manager.add_position(board, move)
        
        status = manager.get_game_status(board)
        if status["repetition_info"]["approaching_threefold"]:
            print(f"   Approaching threefold after {move_uci}")
        if status["repetition_info"]["can_claim_threefold"]:
            print(f"   ✅ Threefold repetition detected after {move_uci}")
            break
    
    # Test 3: 50-move rule simulation
    print("\n3. Testing 50-move rule...")
    board = chess.Board()
    manager = GameRulesManager()
    
    # Simulate position close to 50-move rule
    board.halfmove_clock = 95  # 47.5 moves
    manager.add_position(board)
    
    fifty_info = manager.get_fifty_move_info(board)
    print(f"   Halfmove clock: {fifty_info['halfmove_clock']}")
    print(f"   Moves to fifty: {fifty_info['moves_to_fifty']}")
    print(f"   Approaching fifty: {fifty_info['approaching_fifty']}")
    
    # Test 4: Game termination detection
    print("\n4. Testing checkmate detection...")
    # Fool's mate position
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    manager = GameRulesManager()
    manager.add_position(board)
    
    status = manager.get_game_status(board)
    print(f"   Game over: {status['is_game_over']}")
    print(f"   Result: {status['result']}")
    print(f"   Termination: {status['termination']}")
    
    print("\n✅ Game Rules Manager tests completed!")

if __name__ == "__main__":
    test_game_rules()
