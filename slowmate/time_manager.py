"""
SlowMate Chess Engine - Time Management System

Professional time management with UCI integration and dynamic allocation.
"""

import time
from typing import Dict, Any, Optional
from enum import Enum

class TimeControlType(Enum):
    """Types of time controls."""
    SUDDEN_DEATH = "sudden_death"        # Fixed time per game
    INCREMENT = "increment"              # Time + increment per move  
    MOVES_TO_GO = "moves_to_go"         # X moves in Y time
    MOVE_TIME = "move_time"             # Fixed time per move
    INFINITE = "infinite"               # No time limit
    PONDER = "ponder"                   # Pondering mode

class GamePhase(Enum):
    """Game phases for time allocation."""
    OPENING = "opening"
    MIDDLEGAME = "middlegame" 
    ENDGAME = "endgame"

class TimeManager:
    """Professional time management system."""
    
    def __init__(self):
        """Initialize time manager."""
        
        # Time control state
        self.white_time = 0      # milliseconds remaining
        self.black_time = 0      # milliseconds remaining
        self.white_increment = 0 # increment per move
        self.black_increment = 0 # increment per move
        self.moves_to_go = None  # moves until time control
        self.move_time = None    # fixed time per move
        self.is_white = True     # are we playing white?
        
        # Search timing
        self.search_start_time = 0
        self.allocated_time = 0
        self.emergency_time = 0
        self.maximum_time = 0
        
        # Time allocation settings (UCI configurable)
        self.time_allocation = {
            'base_allocation': 0.04,     # 4% of remaining time in normal positions
            'opening_factor': 0.8,       # Use less time in opening
            'middlegame_factor': 1.2,    # Use more time in middlegame
            'endgame_factor': 1.0,       # Normal time in endgame
            'critical_factor': 2.0,      # Extra time for critical positions
            'emergency_reserve': 0.1,    # Keep 10% as emergency reserve
            'increment_usage': 0.9,      # Use 90% of increment
            'minimum_time': 50,          # Minimum 50ms per move
            'maximum_time_factor': 0.25, # Never use more than 25% of remaining
        }
        
        # Position criticality factors
        self.criticality_factors = {
            'material_imbalance': False,
            'king_safety_concern': False,
            'tactical_opportunity': False,
            'endgame_precision': False,
            'time_pressure': False
        }
    
    def set_time_control(self, wtime: int = None, btime: int = None, 
                        winc: int = None, binc: int = None,
                        movestogo: int = None, movetime: int = None,
                        infinite: bool = False, ponder: bool = False):
        """Set time control from UCI go command."""
        
        if wtime is not None:
            self.white_time = wtime
        if btime is not None:
            self.black_time = btime
        if winc is not None:
            self.white_increment = winc
        if binc is not None:
            self.black_increment = binc
        if movestogo is not None:
            self.moves_to_go = movestogo
        if movetime is not None:
            self.move_time = movetime
    
    def get_time_control_type(self) -> TimeControlType:
        """Determine the type of time control in use."""
        
        if self.move_time is not None:
            return TimeControlType.MOVE_TIME
        elif self.moves_to_go is not None:
            return TimeControlType.MOVES_TO_GO
        elif self.white_increment > 0 or self.black_increment > 0:
            return TimeControlType.INCREMENT
        elif self.white_time > 0 or self.black_time > 0:
            return TimeControlType.SUDDEN_DEATH
        else:
            return TimeControlType.INFINITE
    
    def determine_game_phase(self, piece_count: int, move_number: int) -> GamePhase:
        """Determine current game phase for time allocation."""
        
        if move_number <= 15 or piece_count >= 28:
            return GamePhase.OPENING
        elif piece_count <= 12:
            return GamePhase.ENDGAME
        else:
            return GamePhase.MIDDLEGAME
    
    def calculate_time_allocation(self, board, move_number: int) -> Dict[str, int]:
        """Calculate time allocation for this move."""
        
        our_time = self.white_time if self.is_white else self.black_time
        our_increment = self.white_increment if self.is_white else self.black_increment
        
        time_control_type = self.get_time_control_type()
        
        # Handle different time control types
        if time_control_type == TimeControlType.MOVE_TIME:
            allocated = self.move_time
            emergency = allocated // 2
            maximum = allocated
            
        elif time_control_type == TimeControlType.INFINITE:
            allocated = 5000  # 5 seconds for infinite analysis
            emergency = 2000
            maximum = 10000
            
        else:
            # Calculate base allocation
            if time_control_type == TimeControlType.MOVES_TO_GO and self.moves_to_go:
                # Allocate time over remaining moves
                base_time = our_time / max(self.moves_to_go, 1)
            else:
                # Use percentage of remaining time
                base_time = our_time * self.time_allocation['base_allocation']
            
            # Adjust for game phase
            piece_count = len(board.piece_map())
            game_phase = self.determine_game_phase(piece_count, move_number)
            
            if game_phase == GamePhase.OPENING:
                phase_factor = self.time_allocation['opening_factor']
            elif game_phase == GamePhase.MIDDLEGAME:
                phase_factor = self.time_allocation['middlegame_factor']
            else:
                phase_factor = self.time_allocation['endgame_factor']
            
            allocated = int(base_time * phase_factor)
            
            # Add increment usage
            if our_increment > 0:
                allocated += int(our_increment * self.time_allocation['increment_usage'])
            
            # Adjust for position criticality
            criticality_bonus = 1.0
            if any(self.criticality_factors.values()):
                criticality_bonus = self.time_allocation['critical_factor']
            
            allocated = int(allocated * criticality_bonus)
            
            # Apply limits
            minimum = self.time_allocation['minimum_time']
            maximum_allowed = int(our_time * self.time_allocation['maximum_time_factor'])
            
            allocated = max(minimum, min(allocated, maximum_allowed))
            emergency = allocated // 3
            maximum = min(allocated * 2, maximum_allowed)
        
        return {
            'allocated': allocated,
            'emergency': emergency, 
            'maximum': maximum,
            'our_time': our_time,
            'our_increment': our_increment,
            'time_control': time_control_type.value
        }
    
    def start_search(self, board, move_number: int, is_white: bool = True):
        """Start search timing."""
        
        self.is_white = is_white
        self.search_start_time = time.time()
        
        # Calculate time allocation
        allocation = self.calculate_time_allocation(board, move_number)
        
        self.allocated_time = allocation['allocated']
        self.emergency_time = allocation['emergency']
        self.maximum_time = allocation['maximum']
        
        return allocation
    
    def get_elapsed_time(self) -> int:
        """Get elapsed search time in milliseconds."""
        if self.search_start_time == 0:
            return 0
        return int((time.time() - self.search_start_time) * 1000)
    
    def should_stop_search(self, depth_completed: int) -> bool:
        """Check if search should stop based on time."""
        
        elapsed = self.get_elapsed_time()
        
        # Always allow at least depth 1
        if depth_completed < 1:
            return False
            
        # Stop if we've used allocated time
        if elapsed >= self.allocated_time:
            return True
            
        # Stop if we're approaching maximum time
        if elapsed >= self.maximum_time * 0.9:
            return True
            
        return False
    
    def get_max_depth_for_time(self, remaining_time: int) -> int:
        """FIXED: Don't artificially limit search depth based on time."""
        
        # TODO: Implement proper time-based depth estimation
        # For now, allow reasonable depth regardless of time
        
        if remaining_time < 50:
            return 3   # Emergency minimum
        elif remaining_time < 200:
            return 6   # Quick move
        elif remaining_time < 1000:
            return 8   # Normal move  
        else:
            return 10  # Deep search allowed
    
    def update_criticality(self, board, **factors):
        """Update position criticality factors."""
        
        self.criticality_factors.update(factors)
    
    def get_time_info(self) -> Dict[str, Any]:
        """Get current time management information."""
        
        elapsed = self.get_elapsed_time()
        
        return {
            'elapsed_time': elapsed,
            'allocated_time': self.allocated_time,
            'emergency_time': self.emergency_time,
            'maximum_time': self.maximum_time,
            'our_time': self.white_time if self.is_white else self.black_time,
            'our_increment': self.white_increment if self.is_white else self.black_increment,
            'time_control_type': self.get_time_control_type().value,
            'time_usage_percent': (elapsed / max(self.allocated_time, 1)) * 100
        }
