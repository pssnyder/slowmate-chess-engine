"""
Time Allocation System for SlowMate v0.2.02 Phase 1
Implements fundamental time budgeting algorithms for optimal time usage.
"""

import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from .time_control import TimeControl, TimeControlType


class AllocationStrategy(Enum):
    """Different time allocation strategies."""
    FIXED_PER_MOVE = "fixed_per_move"         # Fixed time per move
    PERCENTAGE_BASED = "percentage_based"      # Percentage of remaining time
    ADAPTIVE = "adaptive"                      # Adaptive based on position/phase
    EMERGENCY = "emergency"                    # Emergency time management
    CONSERVATIVE = "conservative"              # Conservative allocation


@dataclass
class TimeAllocation:
    """Represents time allocation for a single move."""
    target_time_ms: int          # Target time for this move
    maximum_time_ms: int         # Absolute maximum time allowed
    minimum_time_ms: int         # Minimum time for decent move
    soft_limit_ms: int          # Soft limit for iterative deepening
    hard_limit_ms: int          # Hard limit (must stop here)
    strategy: AllocationStrategy # Strategy used for allocation
    confidence: float = 1.0      # Confidence in this allocation (0-1)
    
    @property
    def has_emergency_time(self) -> bool:
        """Check if we're in emergency time situation."""
        return self.strategy == AllocationStrategy.EMERGENCY
    
    @property
    def time_buffer_ms(self) -> int:
        """Get time buffer between soft and hard limits."""
        return self.hard_limit_ms - self.soft_limit_ms


class TimeAllocator:
    """Core time allocation system."""
    
    def __init__(self):
        self.move_overhead_ms = 50   # Communication overhead per move
        self.emergency_threshold = 0.1  # 10% of time = emergency
        self.conservative_factor = 0.8  # Use 80% of allocated time
        
        # Allocation percentages for different strategies
        self.allocation_percentages = {
            AllocationStrategy.FIXED_PER_MOVE: 0.025,      # 2.5% per move
            AllocationStrategy.PERCENTAGE_BASED: 0.04,      # 4% per move
            AllocationStrategy.ADAPTIVE: 0.035,             # 3.5% base per move
            AllocationStrategy.CONSERVATIVE: 0.02,          # 2% per move
            AllocationStrategy.EMERGENCY: 0.01              # 1% per move
        }
    
    def allocate_time(
        self, 
        time_control: TimeControl, 
        remaining_time_ms: int,
        is_white_to_move: bool,
        move_number: int = 1,
        position_complexity: float = 0.5
    ) -> TimeAllocation:
        """
        Allocate time for the current move.
        
        Args:
            time_control: Time control configuration
            remaining_time_ms: Time remaining for this side
            is_white_to_move: Whether it's white's turn
            move_number: Current move number
            position_complexity: Complexity factor (0-1, 0.5 = average)
        
        Returns:
            TimeAllocation object with time budgets
        """
        # Handle non-time-limited searches
        if not time_control.is_time_limited:
            return self._allocate_unlimited_time(time_control)
        
        # Get increment for this side
        increment_ms = self._get_increment(time_control, is_white_to_move)
        
        # Calculate effective remaining time (including increment)
        effective_time_ms = remaining_time_ms + increment_ms - self.move_overhead_ms
        effective_time_ms = max(0, effective_time_ms)
        
        # Determine allocation strategy
        strategy = self._determine_strategy(
            effective_time_ms, 
            time_control, 
            move_number,
            position_complexity
        )
        
        # Calculate base allocation
        if strategy == AllocationStrategy.EMERGENCY:
            allocation = self._allocate_emergency_time(effective_time_ms, increment_ms)
        elif strategy == AllocationStrategy.FIXED_PER_MOVE:
            allocation = self._allocate_fixed_per_move(effective_time_ms, time_control, move_number)
        elif strategy == AllocationStrategy.PERCENTAGE_BASED:
            allocation = self._allocate_percentage_based(effective_time_ms, move_number)
        elif strategy == AllocationStrategy.ADAPTIVE:
            allocation = self._allocate_adaptive(
                effective_time_ms, 
                time_control, 
                move_number, 
                position_complexity
            )
        else:  # CONSERVATIVE
            allocation = self._allocate_conservative(effective_time_ms, move_number)
        
        # Apply safety constraints
        allocation = self._apply_safety_constraints(allocation, effective_time_ms)
        
        return allocation
    
    def _allocate_unlimited_time(self, time_control: TimeControl) -> TimeAllocation:
        """Allocate time for unlimited search modes."""
        if time_control.control_type == TimeControlType.FIXED_DEPTH:
            # For fixed depth, allocate reasonable time but no hard limits
            return TimeAllocation(
                target_time_ms=30000,    # 30 seconds target
                maximum_time_ms=300000,  # 5 minutes max
                minimum_time_ms=1000,    # 1 second min
                soft_limit_ms=60000,     # 1 minute soft
                hard_limit_ms=300000,    # 5 minutes hard
                strategy=AllocationStrategy.FIXED_PER_MOVE
            )
        elif time_control.control_type == TimeControlType.FIXED_NODES:
            # For fixed nodes, minimal time limits
            return TimeAllocation(
                target_time_ms=10000,    # 10 seconds target
                maximum_time_ms=120000,  # 2 minutes max
                minimum_time_ms=500,     # 0.5 seconds min
                soft_limit_ms=30000,     # 30 seconds soft
                hard_limit_ms=120000,    # 2 minutes hard
                strategy=AllocationStrategy.FIXED_PER_MOVE
            )
        else:  # INFINITE
            # For infinite analysis, very high limits
            return TimeAllocation(
                target_time_ms=60000,     # 1 minute target
                maximum_time_ms=3600000,  # 1 hour max
                minimum_time_ms=1000,     # 1 second min
                soft_limit_ms=300000,     # 5 minutes soft
                hard_limit_ms=3600000,    # 1 hour hard
                strategy=AllocationStrategy.PERCENTAGE_BASED
            )
    
    def _determine_strategy(
        self, 
        effective_time_ms: int, 
        time_control: TimeControl, 
        move_number: int,
        position_complexity: float
    ) -> AllocationStrategy:
        """Determine the best allocation strategy for current situation."""
        
        # Emergency time (less than 10% of estimated game time)
        estimated_total = time_control.total_estimated_time_ms
        if isinstance(estimated_total, (int, float)) and effective_time_ms < estimated_total * self.emergency_threshold:
            return AllocationStrategy.EMERGENCY
        
        # Very low time (less than 30 seconds)
        if effective_time_ms < 30000:
            return AllocationStrategy.EMERGENCY
        
        # Opening phase (first 15 moves) - conservative
        if move_number <= 15:
            return AllocationStrategy.CONSERVATIVE
        
        # Complex positions need more time
        if position_complexity > 0.7:
            return AllocationStrategy.ADAPTIVE
        
        # Classical games - more strategic allocation
        if time_control.control_type == TimeControlType.CLASSICAL:
            if move_number <= 40:  # Before time control
                return AllocationStrategy.PERCENTAGE_BASED
            else:  # After time control
                return AllocationStrategy.ADAPTIVE
        
        # Rapid games - balanced approach
        if time_control.control_type == TimeControlType.RAPID:
            return AllocationStrategy.ADAPTIVE
        
        # Blitz games - quick decisions
        if time_control.control_type == TimeControlType.BLITZ:
            return AllocationStrategy.PERCENTAGE_BASED
        
        # Bullet games - very fast
        if time_control.control_type == TimeControlType.BULLET:
            return AllocationStrategy.FIXED_PER_MOVE
        
        # Default
        return AllocationStrategy.PERCENTAGE_BASED
    
    def _allocate_emergency_time(self, effective_time_ms: int, increment_ms: int) -> TimeAllocation:
        """Allocate time in emergency situations."""
        # In emergency, use minimal time with increment safety
        base_time = min(effective_time_ms * 0.1, 1000)  # 10% or 1 second max
        
        # If we have increment, we can be slightly more generous
        if increment_ms > 0:
            base_time = min(base_time + increment_ms * 0.5, effective_time_ms * 0.2)
        
        target_time = int(base_time)
        soft_limit = int(target_time * 1.2)
        hard_limit = int(min(target_time * 1.5, effective_time_ms * 0.3))
        
        return TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=hard_limit,
            minimum_time_ms=max(100, target_time // 2),
            soft_limit_ms=soft_limit,
            hard_limit_ms=hard_limit,
            strategy=AllocationStrategy.EMERGENCY
        )
    
    def _allocate_fixed_per_move(
        self, 
        effective_time_ms: int, 
        time_control: TimeControl, 
        move_number: int
    ) -> TimeAllocation:
        """Allocate fixed time per move."""
        percentage = self.allocation_percentages[AllocationStrategy.FIXED_PER_MOVE]
        
        # Estimate remaining moves
        if time_control.control_type == TimeControlType.BULLET:
            estimated_moves = max(20, 40 - move_number)  # Shorter games
        else:
            estimated_moves = max(30, 60 - move_number)  # Normal games
        
        base_allocation = effective_time_ms / estimated_moves
        target_time = int(base_allocation * percentage / (percentage * 0.5))  # Normalize
        
        soft_limit = int(target_time * 1.2)
        hard_limit = int(target_time * 1.8)
        
        return TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=hard_limit,
            minimum_time_ms=max(100, target_time // 3),
            soft_limit_ms=soft_limit,
            hard_limit_ms=hard_limit,
            strategy=AllocationStrategy.FIXED_PER_MOVE
        )
    
    def _allocate_percentage_based(self, effective_time_ms: int, move_number: int) -> TimeAllocation:
        """Allocate based on percentage of remaining time."""
        percentage = self.allocation_percentages[AllocationStrategy.PERCENTAGE_BASED]
        
        # Adjust percentage based on game phase
        if move_number <= 15:  # Opening
            percentage *= 0.7  # Use less time
        elif move_number >= 30:  # Endgame approach
            percentage *= 1.3  # Use more time
        
        target_time = int(effective_time_ms * percentage)
        soft_limit = int(target_time * 1.3)
        hard_limit = int(target_time * 2.0)
        
        return TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=hard_limit,
            minimum_time_ms=max(200, target_time // 4),
            soft_limit_ms=soft_limit,
            hard_limit_ms=hard_limit,
            strategy=AllocationStrategy.PERCENTAGE_BASED
        )
    
    def _allocate_adaptive(
        self, 
        effective_time_ms: int, 
        time_control: TimeControl, 
        move_number: int,
        position_complexity: float
    ) -> TimeAllocation:
        """Adaptive allocation based on position complexity."""
        base_percentage = self.allocation_percentages[AllocationStrategy.ADAPTIVE]
        
        # Adjust for position complexity
        complexity_multiplier = 0.5 + position_complexity  # 0.5 to 1.5
        adjusted_percentage = base_percentage * complexity_multiplier
        
        # Adjust for game phase
        if move_number <= 15:  # Opening
            phase_multiplier = 0.8
        elif move_number <= 30:  # Middlegame
            phase_multiplier = 1.2
        else:  # Endgame
            phase_multiplier = 1.4
        
        final_percentage = adjusted_percentage * phase_multiplier
        final_percentage = min(final_percentage, 0.15)  # Cap at 15%
        
        target_time = int(effective_time_ms * final_percentage)
        soft_limit = int(target_time * 1.25)
        hard_limit = int(target_time * 2.5)
        
        return TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=hard_limit,
            minimum_time_ms=max(300, target_time // 4),
            soft_limit_ms=soft_limit,
            hard_limit_ms=hard_limit,
            strategy=AllocationStrategy.ADAPTIVE,
            confidence=position_complexity
        )
    
    def _allocate_conservative(self, effective_time_ms: int, move_number: int) -> TimeAllocation:
        """Conservative allocation for opening and safe play."""
        percentage = self.allocation_percentages[AllocationStrategy.CONSERVATIVE]
        
        target_time = int(effective_time_ms * percentage * self.conservative_factor)
        soft_limit = int(target_time * 1.1)
        hard_limit = int(target_time * 1.4)
        
        return TimeAllocation(
            target_time_ms=target_time,
            maximum_time_ms=hard_limit,
            minimum_time_ms=max(150, target_time // 2),
            soft_limit_ms=soft_limit,
            hard_limit_ms=hard_limit,
            strategy=AllocationStrategy.CONSERVATIVE
        )
    
    def _apply_safety_constraints(self, allocation: TimeAllocation, effective_time_ms: int) -> TimeAllocation:
        """Apply safety constraints to prevent time forfeit."""
        # Ensure we don't use more than 90% of available time
        max_safe_time = int(effective_time_ms * 0.9)
        
        # Clamp all time limits
        allocation.target_time_ms = min(allocation.target_time_ms, max_safe_time)
        allocation.maximum_time_ms = min(allocation.maximum_time_ms, max_safe_time)
        allocation.soft_limit_ms = min(allocation.soft_limit_ms, max_safe_time)
        allocation.hard_limit_ms = min(allocation.hard_limit_ms, max_safe_time)
        
        # Ensure minimum constraints
        allocation.minimum_time_ms = max(50, allocation.minimum_time_ms)  # At least 50ms
        
        # Ensure logical ordering
        allocation.target_time_ms = max(allocation.minimum_time_ms, allocation.target_time_ms)
        allocation.soft_limit_ms = max(allocation.target_time_ms, allocation.soft_limit_ms)
        allocation.hard_limit_ms = max(allocation.soft_limit_ms, allocation.hard_limit_ms)
        allocation.maximum_time_ms = max(allocation.hard_limit_ms, allocation.maximum_time_ms)
        
        return allocation
    
    def _get_increment(self, time_control: TimeControl, is_white_to_move: bool) -> int:
        """Get increment for the current side."""
        if time_control.winc is not None and time_control.binc is not None:
            return time_control.winc if is_white_to_move else time_control.binc
        return time_control.increment_ms
    
    def calculate_time_pressure(self, remaining_time_ms: int, time_control: TimeControl) -> float:
        """
        Calculate time pressure factor (0-1, where 1 is maximum pressure).
        
        Args:
            remaining_time_ms: Time remaining
            time_control: Time control configuration
        
        Returns:
            Time pressure factor (0-1)
        """
        if not time_control.is_time_limited:
            return 0.0
        
        total_time = time_control.total_estimated_time_ms
        if isinstance(total_time, float):  # Infinite
            return 0.0
        
        time_ratio = remaining_time_ms / total_time
        
        # Convert to pressure (inverse of ratio)
        if time_ratio >= 0.5:
            return 0.0  # No pressure
        elif time_ratio >= 0.2:
            return (0.5 - time_ratio) / 0.3  # Gradual pressure
        elif time_ratio >= 0.1:
            return 0.5 + (0.2 - time_ratio) / 0.1 * 0.3  # High pressure
        else:
            return 0.8 + (0.1 - time_ratio) / 0.1 * 0.2  # Maximum pressure


# Export main classes
__all__ = [
    'AllocationStrategy',
    'TimeAllocation',
    'TimeAllocator'
]


def main():
    """Test the time allocation system."""
    from .time_control import TimeControlParser
    
    allocator = TimeAllocator()
    parser = TimeControlParser()
    
    # Test different time controls
    test_cases = [
        ("3+2", 180000, True, 1),     # 3+2 blitz, white to move, move 1
        ("15+10", 900000, False, 15), # 15+10 rapid, black to move, move 15
        ("40/90+30", 5400000, True, 20), # Classical, white to move, move 20
        ("1+0", 60000, True, 25),     # Bullet, white to move, move 25
    ]
    
    print("Time Allocation Test Results:")
    print("=" * 60)
    
    for tc_str, remaining_ms, is_white, move_num in test_cases:
        time_control = parser.parse(tc_str)
        if time_control:
            allocation = allocator.allocate_time(
                time_control, 
                remaining_ms, 
                is_white, 
                move_num
            )
            
            pressure = allocator.calculate_time_pressure(remaining_ms, time_control)
            
            print(f"Time Control: {tc_str}")
            print(f"Remaining: {remaining_ms//1000}s, Move: {move_num}")
            print(f"Strategy: {allocation.strategy.value}")
            print(f"Target: {allocation.target_time_ms//1000}s")
            print(f"Soft/Hard: {allocation.soft_limit_ms//1000}s / {allocation.hard_limit_ms//1000}s")
            print(f"Time Pressure: {pressure:.2f}")
            print("-" * 40)


if __name__ == "__main__":
    main()
