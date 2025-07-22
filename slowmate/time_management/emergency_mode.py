"""
Emergency Time Management for SlowMate v0.2.02 Phase 3
Handles critical time pressure situations with adaptive strategies.
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import chess

from .time_control import TimeControl
from .time_allocation import TimeAllocation, AllocationStrategy
from .time_tracking import TimeTracker


class EmergencyLevel(Enum):
    """Different levels of time emergency."""
    NORMAL = "normal"              # No time pressure
    LOW_TIME = "low_time"          # Getting low on time
    TIME_PRESSURE = "time_pressure"  # Under significant pressure
    CRITICAL = "critical"          # Very little time left
    DESPERATION = "desperation"    # Seconds remaining


class EmergencyStrategy(Enum):
    """Different emergency strategies."""
    REDUCE_DEPTH = "reduce_depth"      # Reduce search depth
    QUICK_MOVES = "quick_moves"        # Make obvious moves quickly
    PATTERN_MATCHING = "pattern"       # Use pattern recognition
    INSTINCT_MODE = "instinct"         # Minimal calculation, rely on evaluation
    BLITZ_MODE = "blitz"               # Ultra-fast play mode


@dataclass
class EmergencyState:
    """Current emergency time management state."""
    level: EmergencyLevel
    strategy: EmergencyStrategy
    time_remaining_ms: int
    moves_to_control: int
    average_move_budget_ms: int
    emergency_activated_at: float
    moves_in_emergency: int
    emergency_moves_played: int
    
    @property
    def emergency_duration(self) -> float:
        """How long we've been in emergency mode (seconds)."""
        return time.time() - self.emergency_activated_at
    
    @property
    def is_active(self) -> bool:
        """Whether emergency mode is currently active."""
        return self.level != EmergencyLevel.NORMAL


@dataclass
class EmergencySettings:
    """Configuration for emergency time management."""
    # Time thresholds (in milliseconds)
    low_time_threshold_ms: int = 60000      # 1 minute
    time_pressure_threshold_ms: int = 30000  # 30 seconds  
    critical_threshold_ms: int = 10000       # 10 seconds
    desperation_threshold_ms: int = 3000     # 3 seconds
    
    # Move time limits in emergency (milliseconds)
    low_time_move_limit: int = 5000         # 5 seconds max
    pressure_move_limit: int = 2000         # 2 seconds max
    critical_move_limit: int = 1000         # 1 second max
    desperation_move_limit: int = 500       # 0.5 seconds max
    
    # Strategy preferences
    preferred_strategies: Optional[Dict[EmergencyLevel, EmergencyStrategy]] = None
    
    # Behavioral settings
    enable_pre_moves: bool = True           # Think during opponent's time
    enable_increment_banking: bool = True   # Save increment time
    enable_emergency_book: bool = True      # Use emergency opening book
    minimum_safety_buffer_ms: int = 1000   # Always keep 1 second buffer
    
    def __post_init__(self):
        if self.preferred_strategies is None:
            self.preferred_strategies = {
                EmergencyLevel.LOW_TIME: EmergencyStrategy.REDUCE_DEPTH,
                EmergencyLevel.TIME_PRESSURE: EmergencyStrategy.QUICK_MOVES,
                EmergencyLevel.CRITICAL: EmergencyStrategy.PATTERN_MATCHING,
                EmergencyLevel.DESPERATION: EmergencyStrategy.INSTINCT_MODE
            }


class EmergencyTimeManager:
    """
    Manages emergency time situations with adaptive strategies.
    
    This manager provides:
    - Automatic emergency level detection
    - Strategy adaptation based on time remaining
    - Move time enforcement
    - Recovery from time pressure
    - Learning from emergency situations
    """
    
    def __init__(self, settings: Optional[EmergencySettings] = None):
        self.settings = settings or EmergencySettings()
        self.current_state: Optional[EmergencyState] = None
        self.history: List[EmergencyState] = []
        
        # Emergency move database (simplified patterns)
        self.emergency_book = EmergencyMoveBook()
        
        # Performance tracking
        self.emergency_performance: Dict[EmergencyLevel, List[float]] = {
            level: [] for level in EmergencyLevel
        }
        
        # Threading for time enforcement
        self._timeout_timer: Optional[threading.Timer] = None
        self._timeout_callback: Optional[Callable] = None
    
    def evaluate_time_situation(
        self,
        time_remaining_ms: int,
        moves_to_time_control: int,
        increment_ms: int = 0
    ) -> EmergencyLevel:
        """
        Evaluate the current time situation and determine emergency level.
        
        Args:
            time_remaining_ms: Milliseconds remaining on clock
            moves_to_time_control: Moves until time control (0 if none)
            increment_ms: Increment per move
        
        Returns:
            Current EmergencyLevel
        """
        # Calculate effective time (including increments if applicable)
        effective_time = time_remaining_ms
        if increment_ms > 0 and moves_to_time_control > 0:
            effective_time += increment_ms * moves_to_time_control
        
        # Determine emergency level based on thresholds
        if effective_time <= self.settings.desperation_threshold_ms:
            return EmergencyLevel.DESPERATION
        elif effective_time <= self.settings.critical_threshold_ms:
            return EmergencyLevel.CRITICAL
        elif effective_time <= self.settings.time_pressure_threshold_ms:
            return EmergencyLevel.TIME_PRESSURE
        elif effective_time <= self.settings.low_time_threshold_ms:
            return EmergencyLevel.LOW_TIME
        else:
            return EmergencyLevel.NORMAL
    
    def enter_emergency_mode(
        self,
        time_remaining_ms: int,
        moves_to_control: int,
        emergency_level: EmergencyLevel
    ) -> EmergencyState:
        """
        Enter emergency time management mode.
        
        Args:
            time_remaining_ms: Milliseconds remaining
            moves_to_control: Moves until time control
            emergency_level: Level of emergency
        
        Returns:
            New EmergencyState
        """
        # Calculate average move budget
        effective_moves = max(1, moves_to_control if moves_to_control > 0 else 20)
        avg_budget = max(
            self.settings.minimum_safety_buffer_ms,
            (time_remaining_ms - self.settings.minimum_safety_buffer_ms) // effective_moves
        )
        
        # Select appropriate strategy
        preferred_strategies = self.settings.preferred_strategies or {
            EmergencyLevel.LOW_TIME: EmergencyStrategy.REDUCE_DEPTH,
            EmergencyLevel.TIME_PRESSURE: EmergencyStrategy.QUICK_MOVES,
            EmergencyLevel.CRITICAL: EmergencyStrategy.PATTERN_MATCHING,
            EmergencyLevel.DESPERATION: EmergencyStrategy.INSTINCT_MODE
        }
        strategy = preferred_strategies.get(emergency_level, EmergencyStrategy.QUICK_MOVES)
        
        # Create emergency state
        self.current_state = EmergencyState(
            level=emergency_level,
            strategy=strategy,
            time_remaining_ms=time_remaining_ms,
            moves_to_control=moves_to_control,
            average_move_budget_ms=avg_budget,
            emergency_activated_at=time.time(),
            moves_in_emergency=0,
            emergency_moves_played=0
        )
        
        return self.current_state
    
    def update_emergency_state(
        self,
        time_remaining_ms: int,
        moves_to_control: int
    ) -> Optional[EmergencyState]:
        """
        Update the current emergency state.
        
        Args:
            time_remaining_ms: Current time remaining
            moves_to_control: Moves until time control
            
        Returns:
            Updated EmergencyState or None if exiting emergency mode
        """
        new_level = self.evaluate_time_situation(time_remaining_ms, moves_to_control)
        
        # Exit emergency mode if time situation improves
        if new_level == EmergencyLevel.NORMAL:
            if self.current_state:
                self._exit_emergency_mode()
            return None
        
        # Enter emergency mode if not already active
        if not self.current_state:
            return self.enter_emergency_mode(time_remaining_ms, moves_to_control, new_level)
        
        # Update existing emergency state
        self.current_state.level = new_level
        self.current_state.time_remaining_ms = time_remaining_ms
        self.current_state.moves_to_control = moves_to_control
        
        # Recalculate move budget
        effective_moves = max(1, moves_to_control if moves_to_control > 0 else 10)
        self.current_state.average_move_budget_ms = max(
            self.settings.minimum_safety_buffer_ms,
            (time_remaining_ms - self.settings.minimum_safety_buffer_ms) // effective_moves
        )
        
        # Escalate strategy if needed
        if new_level.value != self.current_state.level.value:
            preferred_strategies = self.settings.preferred_strategies or {
                EmergencyLevel.LOW_TIME: EmergencyStrategy.REDUCE_DEPTH,
                EmergencyLevel.TIME_PRESSURE: EmergencyStrategy.QUICK_MOVES,
                EmergencyLevel.CRITICAL: EmergencyStrategy.PATTERN_MATCHING,
                EmergencyLevel.DESPERATION: EmergencyStrategy.INSTINCT_MODE
            }
            self.current_state.strategy = preferred_strategies.get(
                new_level,
                self.current_state.strategy
            )
        
        return self.current_state
    
    def get_emergency_allocation(
        self,
        base_allocation: TimeAllocation,
        position: chess.Board
    ) -> TimeAllocation:
        """
        Get time allocation adjusted for emergency situation.
        
        Args:
            base_allocation: Base time allocation
            position: Current position
        
        Returns:
            Emergency-adjusted TimeAllocation
        """
        if not self.current_state:
            return base_allocation
        
        # Get emergency move limit
        move_limit = self._get_emergency_move_limit(self.current_state.level)
        
        # Never exceed our calculated budget
        target_time = min(
            move_limit,
            self.current_state.average_move_budget_ms,
            base_allocation.target_time_ms
        )
        
        # For very quick moves, try to use emergency book
        if (self.current_state.level in [EmergencyLevel.CRITICAL, EmergencyLevel.DESPERATION] and
            self.settings.enable_emergency_book):
            book_move = self.emergency_book.get_quick_move(position)
            if book_move:
                # Use minimal time for book moves
                target_time = min(target_time, 200)  # 0.2 seconds
        
        # Create emergency allocation
        emergency_allocation = TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=min(move_limit, base_allocation.maximum_time_ms),
            minimum_time_ms=min(100, target_time),  # Minimum 0.1 second
            soft_limit_ms=int(target_time * 0.8),
            hard_limit_ms=move_limit,
            strategy=AllocationStrategy.EMERGENCY,
            confidence=base_allocation.confidence * 0.5  # Lower confidence in emergency
        )
        
        return emergency_allocation
    
    def _get_emergency_move_limit(self, level: EmergencyLevel) -> int:
        """Get the move time limit for emergency level."""
        limits = {
            EmergencyLevel.LOW_TIME: self.settings.low_time_move_limit,
            EmergencyLevel.TIME_PRESSURE: self.settings.pressure_move_limit,
            EmergencyLevel.CRITICAL: self.settings.critical_move_limit,
            EmergencyLevel.DESPERATION: self.settings.desperation_move_limit
        }
        return limits.get(level, self.settings.low_time_move_limit)
    
    def start_move_timeout(self, timeout_ms: int, callback: Callable):
        """
        Start a timeout timer for the current move.
        
        Args:
            timeout_ms: Timeout in milliseconds
            callback: Function to call when timeout occurs
        """
        self.cancel_move_timeout()  # Cancel any existing timer
        
        timeout_seconds = timeout_ms / 1000.0
        self._timeout_timer = threading.Timer(timeout_seconds, callback)
        self._timeout_callback = callback
        self._timeout_timer.start()
    
    def cancel_move_timeout(self):
        """Cancel the current move timeout timer."""
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None
            self._timeout_callback = None
    
    def record_emergency_move(self, move_time_ms: int, move_quality: float):
        """
        Record the performance of a move made in emergency mode.
        
        Args:
            move_time_ms: Time taken for the move
            move_quality: Quality assessment of the move (0-1)
        """
        if not self.current_state:
            return
        
        self.current_state.emergency_moves_played += 1
        self.emergency_performance[self.current_state.level].append(move_quality)
        
        # Keep only recent performance data
        for level in EmergencyLevel:
            if len(self.emergency_performance[level]) > 100:
                self.emergency_performance[level] = self.emergency_performance[level][-100:]
    
    def get_emergency_advice(self, position: chess.Board) -> Dict[str, Any]:
        """
        Get advice for handling the current emergency situation.
        
        Args:
            position: Current chess position
        
        Returns:
            Dictionary with emergency handling advice
        """
        if not self.current_state:
            return {"status": "no_emergency"}
        
        advice = {
            "status": "emergency_active",
            "level": self.current_state.level.value,
            "strategy": self.current_state.strategy.value,
            "time_remaining_ms": self.current_state.time_remaining_ms,
            "average_budget_ms": self.current_state.average_move_budget_ms,
            "moves_in_emergency": self.current_state.moves_in_emergency,
            "emergency_duration": self.current_state.emergency_duration
        }
        
        # Strategy-specific advice
        if self.current_state.strategy == EmergencyStrategy.REDUCE_DEPTH:
            advice["search_advice"] = "Reduce search depth to 3-4 plies maximum"
        elif self.current_state.strategy == EmergencyStrategy.QUICK_MOVES:
            advice["search_advice"] = "Make obvious moves quickly, avoid deep calculation"
        elif self.current_state.strategy == EmergencyStrategy.PATTERN_MATCHING:
            advice["search_advice"] = "Use pattern recognition, avoid novel positions"
        elif self.current_state.strategy == EmergencyStrategy.INSTINCT_MODE:
            advice["search_advice"] = "Trust evaluation, minimal search"
        elif self.current_state.strategy == EmergencyStrategy.BLITZ_MODE:
            advice["search_advice"] = "Play instantly, rely on intuition"
        
        # Check for emergency book moves
        if self.settings.enable_emergency_book:
            book_move = self.emergency_book.get_quick_move(position)
            if book_move:
                advice["book_move"] = book_move.uci()
                advice["book_advice"] = "Emergency book move available"
        
        return advice
    
    def _exit_emergency_mode(self):
        """Exit emergency mode and save performance data."""
        if self.current_state:
            # Record emergency episode in history
            self.history.append(self.current_state)
            
            # Keep only recent history
            if len(self.history) > 50:
                self.history = self.history[-50:]
            
            # Cancel any active timeouts
            self.cancel_move_timeout()
            
            self.current_state = None
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for emergency situations."""
        stats = {}
        
        for level in EmergencyLevel:
            performances = self.emergency_performance[level]
            if performances:
                stats[level.value] = {
                    "count": len(performances),
                    "average_quality": sum(performances) / len(performances),
                    "min_quality": min(performances),
                    "max_quality": max(performances)
                }
            else:
                stats[level.value] = {"count": 0}
        
        # Emergency episodes statistics
        if self.history:
            stats["emergency_episodes"] = len(self.history)
            stats["average_emergency_duration"] = sum(
                episode.emergency_duration for episode in self.history
            ) / len(self.history)
        
        return stats
    
    def is_emergency_active(self) -> bool:
        """Check if emergency mode is currently active."""
        return self.current_state is not None


class EmergencyMoveBook:
    """
    Simple emergency move book for critical time situations.
    Contains basic opening principles and common tactical patterns.
    """
    
    def __init__(self):
        # Emergency opening moves (first few moves)
        self.opening_moves = {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": ["e2e4", "d2d4", "g1f3"],
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": ["e7e5", "c7c5", "e7e6"],
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1": ["d7d5", "g8f6", "c7c5"]
        }
        
        # Common tactical patterns (simplified)
        self.tactical_patterns = [
            # Pattern: if in check, try to block or move king
            lambda board: self._handle_check(board),
            # Pattern: if can capture for free, do it
            lambda board: self._find_free_capture(board),
            # Pattern: if can give checkmate, do it
            lambda board: self._find_checkmate(board)
        ]
    
    def get_quick_move(self, position: chess.Board) -> Optional[chess.Move]:
        """
        Get a quick move for the current position.
        
        Args:
            position: Current chess position
        
        Returns:
            A quick move or None if no book move available
        """
        # Try opening book first
        fen = position.fen()
        if fen in self.opening_moves:
            move_uci = self.opening_moves[fen][0]  # Take first suggested move
            try:
                move = chess.Move.from_uci(move_uci)
                if move in position.legal_moves:
                    return move
            except:
                pass
        
        # Try tactical patterns
        for pattern in self.tactical_patterns:
            try:
                move = pattern(position)
                if move and move in position.legal_moves:
                    return move
            except:
                continue
        
        # Fallback: return first legal move (better than timeout)
        legal_moves = list(position.legal_moves)
        if legal_moves:
            return legal_moves[0]
        
        return None
    
    def _handle_check(self, board: chess.Board) -> Optional[chess.Move]:
        """Handle check situations quickly."""
        if not board.is_check():
            return None
        
        # Try to find a move that gets out of check
        for move in board.legal_moves:
            board.push(move)
            if not board.is_check():
                board.pop()
                return move
            board.pop()
        
        return None
    
    def _find_free_capture(self, board: chess.Board) -> Optional[chess.Move]:
        """Find a free capture (winning material)."""
        for move in board.legal_moves:
            if board.is_capture(move):
                # Simple check: if the captured piece is more valuable than attacker
                captured_piece = board.piece_at(move.to_square)
                attacking_piece = board.piece_at(move.from_square)
                
                if captured_piece and attacking_piece:
                    piece_values = {
                        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
                    }
                    
                    captured_value = piece_values.get(captured_piece.piece_type, 0)
                    attacking_value = piece_values.get(attacking_piece.piece_type, 0)
                    
                    # If we're winning material, take it
                    if captured_value > attacking_value:
                        return move
        
        return None
    
    def _find_checkmate(self, board: chess.Board) -> Optional[chess.Move]:
        """Look for immediate checkmate."""
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return move
            board.pop()
        
        return None


# Export main classes
__all__ = [
    'EmergencyLevel',
    'EmergencyStrategy', 
    'EmergencyState',
    'EmergencySettings',
    'EmergencyTimeManager',
    'EmergencyMoveBook'
]


def main():
    """Test the emergency time management system."""
    import chess
    from .time_allocation import TimeAllocation, AllocationStrategy
    
    # Create emergency manager
    settings = EmergencySettings()
    emergency_manager = EmergencyTimeManager(settings)
    
    # Test scenarios
    test_scenarios = [
        ("Normal time", 300000, 0),      # 5 minutes
        ("Low time", 45000, 0),          # 45 seconds  
        ("Time pressure", 20000, 0),     # 20 seconds
        ("Critical", 8000, 0),           # 8 seconds
        ("Desperation", 2000, 0)         # 2 seconds
    ]
    
    print("Emergency Time Management Test:")
    print("=" * 50)
    
    for scenario_name, time_remaining, moves_to_control in test_scenarios:
        # Evaluate emergency level
        emergency_level = emergency_manager.evaluate_time_situation(
            time_remaining, moves_to_control
        )
        
        print(f"\n{scenario_name}:")
        print(f"  Time remaining: {time_remaining}ms")
        print(f"  Emergency level: {emergency_level.value}")
        
        if emergency_level != EmergencyLevel.NORMAL:
            # Enter emergency mode
            emergency_state = emergency_manager.enter_emergency_mode(
                time_remaining, moves_to_control, emergency_level
            )
            
            print(f"  Emergency strategy: {emergency_state.strategy.value}")
            print(f"  Average move budget: {emergency_state.average_move_budget_ms}ms")
            
            # Test emergency allocation
            base_allocation = TimeAllocation(
                target_time_ms=10000,
                maximum_time_ms=15000,
                minimum_time_ms=1000,
                soft_limit_ms=8000,
                hard_limit_ms=15000,
                strategy=AllocationStrategy.PERCENTAGE_BASED
            )
            
            position = chess.Board()
            emergency_allocation = emergency_manager.get_emergency_allocation(
                base_allocation, position
            )
            
            print(f"  Emergency allocation: {emergency_allocation.target_time_ms}ms")
            print(f"  Hard limit: {emergency_allocation.hard_limit_ms}ms")
            
            # Get advice
            advice = emergency_manager.get_emergency_advice(position)
            print(f"  Advice: {advice.get('search_advice', 'No specific advice')}")
            
            # Exit emergency mode
            emergency_manager._exit_emergency_mode()
        
        print("-" * 40)
    
    # Test emergency book
    print("\nEmergency Book Test:")
    book = EmergencyMoveBook()
    
    test_positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("Check position", "rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 0 5")
    ]
    
    for pos_name, fen in test_positions:
        position = chess.Board(fen)
        quick_move = book.get_quick_move(position)
        
        print(f"  {pos_name}: {quick_move.uci() if quick_move else 'No book move'}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
