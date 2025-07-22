"""
Search Timeout System for SlowMate v0.2.02 Phase 1
Adds hard and soft time limits to search functions with clean termination.
"""

import time
import threading
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum

from .time_allocation import TimeAllocation


class TimeoutReason(Enum):
    """Reasons for search timeout."""
    SOFT_LIMIT = "soft_limit"        # Soft time limit reached
    HARD_LIMIT = "hard_limit"        # Hard time limit reached
    EMERGENCY_STOP = "emergency_stop"  # Emergency termination
    USER_STOP = "user_stop"          # User-requested stop
    DEPTH_REACHED = "depth_reached"   # Target depth reached
    NODES_REACHED = "nodes_reached"   # Node limit reached


@dataclass
class TimeoutStatus:
    """Status information for search timeout."""
    is_timeout: bool = False
    reason: Optional[TimeoutReason] = None
    elapsed_ms: int = 0
    remaining_ms: int = 0
    should_stop: bool = False


class SearchTimer:
    """High-precision timer for search operations."""
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._timeout_allocation: Optional[TimeAllocation] = None
        self._stop_requested = False
        self._timeout_callback: Optional[Callable] = None
        self._timer_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start_timer(self, allocation: TimeAllocation, timeout_callback: Optional[Callable] = None):
        """
        Start the search timer with the given time allocation.
        
        Args:
            allocation: Time allocation for this search
            timeout_callback: Optional callback when timeout occurs
        """
        with self._lock:
            self._start_time = time.perf_counter()
            self._timeout_allocation = allocation
            self._stop_requested = False
            self._timeout_callback = timeout_callback
            
            # Start monitoring thread for hard timeout
            if self._timer_thread is None or not self._timer_thread.is_alive():
                self._timer_thread = threading.Thread(target=self._monitor_timeout, daemon=True)
                self._timer_thread.start()
    
    def stop_timer(self):
        """Stop the search timer."""
        with self._lock:
            self._stop_requested = True
    
    def get_status(self) -> TimeoutStatus:
        """Get current timeout status."""
        if self._start_time is None or self._timeout_allocation is None:
            return TimeoutStatus()
        
        elapsed_ms = int((time.perf_counter() - self._start_time) * 1000)
        remaining_soft_ms = max(0, self._timeout_allocation.soft_limit_ms - elapsed_ms)
        remaining_hard_ms = max(0, self._timeout_allocation.hard_limit_ms - elapsed_ms)
        
        # Determine timeout status
        is_timeout = False
        reason = None
        should_stop = False
        
        if self._stop_requested:
            is_timeout = True
            reason = TimeoutReason.USER_STOP
            should_stop = True
        elif elapsed_ms >= self._timeout_allocation.hard_limit_ms:
            is_timeout = True
            reason = TimeoutReason.HARD_LIMIT
            should_stop = True
        elif elapsed_ms >= self._timeout_allocation.soft_limit_ms:
            is_timeout = True
            reason = TimeoutReason.SOFT_LIMIT
            should_stop = False  # Soft timeout - can continue briefly
        
        return TimeoutStatus(
            is_timeout=is_timeout,
            reason=reason,
            elapsed_ms=elapsed_ms,
            remaining_ms=remaining_hard_ms,
            should_stop=should_stop
        )
    
    def check_timeout(self) -> TimeoutStatus:
        """Quick timeout check for use in search loops."""
        return self.get_status()
    
    def should_continue(self) -> bool:
        """Check if search should continue (quick check)."""
        if self._start_time is None or self._timeout_allocation is None:
            return True
        
        if self._stop_requested:
            return False
        
        elapsed_ms = int((time.perf_counter() - self._start_time) * 1000)
        return elapsed_ms < self._timeout_allocation.hard_limit_ms
    
    def time_for_next_depth(self) -> bool:
        """Check if there's time to start another depth iteration."""
        if self._start_time is None or self._timeout_allocation is None:
            return True
        
        status = self.get_status()
        
        # If we've exceeded soft limit, probably not worth starting new depth
        if status.reason == TimeoutReason.SOFT_LIMIT:
            # Only continue if we have substantial time remaining
            return status.remaining_ms > self._timeout_allocation.target_time_ms * 0.3
        
        return not status.should_stop
    
    def get_elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        if self._start_time is None:
            return 0
        return int((time.perf_counter() - self._start_time) * 1000)
    
    def get_remaining_ms(self) -> int:
        """Get remaining time in milliseconds."""
        if self._start_time is None or self._timeout_allocation is None:
            return 0
        
        elapsed = self.get_elapsed_ms()
        return max(0, self._timeout_allocation.hard_limit_ms - elapsed)
    
    def _monitor_timeout(self):
        """Monitor for hard timeout in background thread."""
        while not self._stop_requested and self._timeout_allocation is not None:
            status = self.get_status()
            
            if status.reason == TimeoutReason.HARD_LIMIT:
                if self._timeout_callback:
                    self._timeout_callback(status)
                break
            
            # Check every 10ms for responsiveness
            time.sleep(0.01)


class SearchTimeoutManager:
    """Manages search timeouts with multiple timeout strategies."""
    
    def __init__(self):
        self.active_timer: Optional[SearchTimer] = None
        self._depth_reached = False
        self._nodes_count = 0
        self._nodes_limit: Optional[int] = None
        self._depth_limit: Optional[int] = None
        self._current_depth = 0
    
    def start_search(
        self, 
        allocation: TimeAllocation, 
        depth_limit: Optional[int] = None,
        nodes_limit: Optional[int] = None,
        timeout_callback: Optional[Callable] = None
    ) -> SearchTimer:
        """
        Start a new search with timeout management.
        
        Args:
            allocation: Time allocation for this search
            depth_limit: Optional depth limit
            nodes_limit: Optional nodes limit
            timeout_callback: Callback when timeout occurs
        
        Returns:
            SearchTimer instance for this search
        """
        self.stop_search()  # Stop any existing search
        
        self.active_timer = SearchTimer()
        self.active_timer.start_timer(allocation, timeout_callback)
        
        # Set limits
        self._depth_limit = depth_limit
        self._nodes_limit = nodes_limit
        self._nodes_count = 0
        self._current_depth = 0
        self._depth_reached = False
        
        return self.active_timer
    
    def stop_search(self):
        """Stop the current search."""
        if self.active_timer:
            self.active_timer.stop_timer()
            self.active_timer = None
    
    def check_all_limits(self, depth: int, nodes: int) -> TimeoutStatus:
        """
        Check all limits (time, depth, nodes) and return comprehensive status.
        
        Args:
            depth: Current search depth
            nodes: Current nodes count
        
        Returns:
            TimeoutStatus with reason for termination
        """
        self._current_depth = depth
        self._nodes_count = nodes
        
        # Check depth limit
        if self._depth_limit is not None and depth >= self._depth_limit:
            self._depth_reached = True
            return TimeoutStatus(
                is_timeout=True,
                reason=TimeoutReason.DEPTH_REACHED,
                elapsed_ms=self.active_timer.get_elapsed_ms() if self.active_timer else 0,
                should_stop=True
            )
        
        # Check nodes limit
        if self._nodes_limit is not None and nodes >= self._nodes_limit:
            return TimeoutStatus(
                is_timeout=True,
                reason=TimeoutReason.NODES_REACHED,
                elapsed_ms=self.active_timer.get_elapsed_ms() if self.active_timer else 0,
                should_stop=True
            )
        
        # Check time limits
        if self.active_timer:
            return self.active_timer.check_timeout()
        
        return TimeoutStatus()
    
    def should_start_new_depth(self, next_depth: int) -> bool:
        """
        Check if we should start searching at the next depth level.
        
        Args:
            next_depth: The next depth we want to search
        
        Returns:
            True if we should start the new depth
        """
        # Check depth limit
        if self._depth_limit is not None and next_depth > self._depth_limit:
            return False
        
        # Check time availability
        if self.active_timer:
            return self.active_timer.time_for_next_depth()
        
        return True
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get current search statistics."""
        stats = {
            'depth': self._current_depth,
            'nodes': self._nodes_count,
            'elapsed_ms': 0,
            'remaining_ms': 0,
            'nps': 0  # Nodes per second
        }
        
        if self.active_timer:
            elapsed = self.active_timer.get_elapsed_ms()
            stats['elapsed_ms'] = elapsed
            stats['remaining_ms'] = self.active_timer.get_remaining_ms()
            
            if elapsed > 0:
                stats['nps'] = int(self._nodes_count / (elapsed / 1000))
        
        return stats
    
    def is_emergency_situation(self) -> bool:
        """Check if we're in an emergency time situation."""
        if not self.active_timer or not self.active_timer._timeout_allocation:
            return False
        
        return self.active_timer._timeout_allocation.has_emergency_time


class TimeoutDecorator:
    """Decorator to add timeout functionality to search functions."""
    
    def __init__(self, timeout_manager: SearchTimeoutManager):
        self.timeout_manager = timeout_manager
    
    def timeout_check(self, func: Callable) -> Callable:
        """
        Decorator that adds timeout checking to a function.
        
        Args:
            func: Function to wrap with timeout checking
        
        Returns:
            Wrapped function with timeout checking
        """
        def wrapper(*args, **kwargs):
            # Check timeout before function execution
            if self.timeout_manager.active_timer:
                status = self.timeout_manager.active_timer.check_timeout()
                if status.should_stop:
                    return None  # or appropriate timeout return value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Check timeout after function execution
            if self.timeout_manager.active_timer:
                status = self.timeout_manager.active_timer.check_timeout()
                if status.should_stop:
                    return result  # Return partial result
            
            return result
        
        return wrapper


# Export main classes
__all__ = [
    'TimeoutReason',
    'TimeoutStatus',
    'SearchTimer',
    'SearchTimeoutManager',
    'TimeoutDecorator'
]


def main():
    """Test the search timeout system."""
    import time as time_module
    
    from .time_allocation import TimeAllocation, AllocationStrategy
    
    # Create test allocation
    allocation = TimeAllocation(
        target_time_ms=1000,
        maximum_time_ms=2000,
        minimum_time_ms=200,
        soft_limit_ms=1200,
        hard_limit_ms=1800,
        strategy=AllocationStrategy.PERCENTAGE_BASED
    )
    
    # Test timeout manager
    timeout_manager = SearchTimeoutManager()
    
    def timeout_callback(status: TimeoutStatus):
        if status.reason:
            print(f"Timeout callback: {status.reason.value} after {status.elapsed_ms}ms")
        else:
            print(f"Timeout callback after {status.elapsed_ms}ms")
    
    print("Search Timeout System Test:")
    print("=" * 40)
    
    # Start search
    timer = timeout_manager.start_search(allocation, timeout_callback=timeout_callback)
    
    print(f"Started search with {allocation.target_time_ms}ms target")
    
    # Simulate search progress
    for i in range(20):
        time_module.sleep(0.1)  # 100ms intervals
        
        status = timeout_manager.check_all_limits(depth=i//5 + 1, nodes=i * 1000)
        stats = timeout_manager.get_search_stats()
        
        print(f"Depth {stats['depth']}, Nodes {stats['nodes']:,}, "
              f"Elapsed {stats['elapsed_ms']}ms, Remaining {stats['remaining_ms']}ms")
        
        if status.should_stop:
            reason_str = status.reason.value if status.reason else "unknown"
            print(f"Search stopped: {reason_str}")
            break
        elif status.is_timeout and status.reason == TimeoutReason.SOFT_LIMIT:
            print("Soft timeout reached - should consider stopping")
    
    timeout_manager.stop_search()
    print("Search completed")


if __name__ == "__main__":
    main()
