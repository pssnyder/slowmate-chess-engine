"""
Time Tracking System for SlowMate v0.2.02 Phase 1
Real-time monitoring of search time usage with comprehensive analytics.
"""

import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
import threading

from .time_control import TimeControl, TimeControlType
from .time_allocation import TimeAllocation, AllocationStrategy
from .search_timeout import TimeoutStatus, TimeoutReason


@dataclass
class MoveTimeRecord:
    """Record of time usage for a single move."""
    move_number: int
    allocated_time_ms: int
    used_time_ms: int
    strategy: AllocationStrategy
    depth_reached: int
    nodes_searched: int
    timeout_reason: Optional[TimeoutReason] = None
    position_complexity: float = 0.5
    timestamp: float = field(default_factory=time.time)
    
    @property
    def efficiency(self) -> float:
        """Time usage efficiency (used/allocated)."""
        if self.allocated_time_ms == 0:
            return 0.0
        return min(1.0, self.used_time_ms / self.allocated_time_ms)
    
    @property
    def nps(self) -> int:
        """Nodes per second."""
        if self.used_time_ms == 0:
            return 0
        return int(self.nodes_searched / (self.used_time_ms / 1000))


@dataclass
class GameTimeStats:
    """Statistics for time usage throughout a game."""
    total_time_used_ms: int = 0
    total_time_allocated_ms: int = 0
    moves_played: int = 0
    average_time_per_move_ms: float = 0.0
    time_efficiency: float = 0.0
    emergency_moves: int = 0
    timeout_count: int = 0
    
    def update(self, record: MoveTimeRecord):
        """Update stats with a new move record."""
        self.total_time_used_ms += record.used_time_ms
        self.total_time_allocated_ms += record.allocated_time_ms
        self.moves_played += 1
        self.average_time_per_move_ms = self.total_time_used_ms / self.moves_played
        
        if self.total_time_allocated_ms > 0:
            self.time_efficiency = self.total_time_used_ms / self.total_time_allocated_ms
        
        if record.strategy == AllocationStrategy.EMERGENCY:
            self.emergency_moves += 1
        
        if record.timeout_reason in [TimeoutReason.HARD_LIMIT, TimeoutReason.SOFT_LIMIT]:
            self.timeout_count += 1


class TimeTracker:
    """Tracks and analyzes time usage patterns."""
    
    def __init__(self):
        self.move_records: List[MoveTimeRecord] = []
        self.game_stats = GameTimeStats()
        self.session_stats: Dict[str, Any] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Performance tracking
        self.start_time: Optional[float] = None
        self.current_move_start: Optional[float] = None
        self.current_allocation: Optional[TimeAllocation] = None
        
    def start_move_timing(self, allocation: TimeAllocation) -> None:
        """Start timing a new move."""
        with self._lock:
            self.current_move_start = time.perf_counter()
            self.current_allocation = allocation
    
    def end_move_timing(
        self, 
        move_number: int,
        depth_reached: int,
        nodes_searched: int,
        timeout_status: Optional[TimeoutStatus] = None,
        position_complexity: float = 0.5
    ) -> MoveTimeRecord:
        """
        End move timing and record the results.
        
        Args:
            move_number: Move number in the game
            depth_reached: Maximum depth reached
            nodes_searched: Total nodes searched
            timeout_status: Final timeout status
            position_complexity: Complexity of the position (0-1)
        
        Returns:
            MoveTimeRecord with timing information
        """
        with self._lock:
            if self.current_move_start is None or self.current_allocation is None:
                raise ValueError("Move timing not started")
            
            used_time_ms = int((time.perf_counter() - self.current_move_start) * 1000)
            
            record = MoveTimeRecord(
                move_number=move_number,
                allocated_time_ms=self.current_allocation.target_time_ms,
                used_time_ms=used_time_ms,
                strategy=self.current_allocation.strategy,
                depth_reached=depth_reached,
                nodes_searched=nodes_searched,
                timeout_reason=timeout_status.reason if timeout_status else None,
                position_complexity=position_complexity
            )
            
            self.move_records.append(record)
            self.game_stats.update(record)
            self._update_session_stats(record)
            
            # Reset current tracking
            self.current_move_start = None
            self.current_allocation = None
            
            return record
    
    def _update_session_stats(self, record: MoveTimeRecord):
        """Update session-wide statistics."""
        self.session_stats['time_usage'].append(record.efficiency)
        self.session_stats['nps'].append(record.nps)
        self.session_stats['depth'].append(record.depth_reached)
        self.session_stats['complexity'].append(record.position_complexity)
        
        # Track by strategy
        strategy_key = f"strategy_{record.strategy.value}"
        self.session_stats[strategy_key].append(record.used_time_ms)
    
    def get_current_efficiency(self) -> float:
        """Get current time usage efficiency."""
        if not self.move_records:
            return 0.0
        
        recent_moves = self.move_records[-10:]  # Last 10 moves
        efficiencies = [r.efficiency for r in recent_moves]
        return statistics.mean(efficiencies) if efficiencies else 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        if not self.move_records:
            return {}
        
        metrics = {
            'game_stats': self.game_stats,
            'total_moves': len(self.move_records),
            'recent_efficiency': self.get_current_efficiency(),
        }
        
        # Time allocation analysis
        if len(self.move_records) >= 5:
            recent_records = self.move_records[-5:]
            
            metrics.update({
                'avg_time_usage_ms': statistics.mean([r.used_time_ms for r in recent_records]),
                'avg_depth': statistics.mean([r.depth_reached for r in recent_records]),
                'avg_nps': statistics.mean([r.nps for r in recent_records if r.nps > 0]),
                'time_variance': statistics.stdev([r.used_time_ms for r in recent_records]) if len(recent_records) > 1 else 0
            })
        
        # Strategy analysis
        strategy_stats = defaultdict(list)
        for record in self.move_records:
            strategy_stats[record.strategy].append(record.efficiency)
        
        metrics['strategy_efficiency'] = {
            strategy.value: statistics.mean(efficiencies) if efficiencies else 0.0
            for strategy, efficiencies in strategy_stats.items()
        }
        
        return metrics
    
    def get_time_pressure_analysis(self, time_control: TimeControl, remaining_time_ms: int) -> Dict[str, Any]:
        """Analyze current time pressure situation."""
        if not time_control.is_time_limited:
            return {'pressure_level': 'none', 'recommendations': []}
        
        total_estimated = time_control.total_estimated_time_ms
        if isinstance(total_estimated, float):  # Infinite
            return {'pressure_level': 'none', 'recommendations': []}
        
        time_ratio = remaining_time_ms / total_estimated
        moves_played = len(self.move_records)
        estimated_moves_remaining = max(10, 60 - moves_played)
        
        analysis = {
            'time_ratio': time_ratio,
            'moves_played': moves_played,
            'estimated_moves_remaining': estimated_moves_remaining,
            'time_per_remaining_move_ms': remaining_time_ms // estimated_moves_remaining,
            'recent_efficiency': self.get_current_efficiency(),
        }
        
        # Determine pressure level
        if time_ratio >= 0.5:
            analysis['pressure_level'] = 'low'
            analysis['recommendations'] = ['maintain_current_strategy']
        elif time_ratio >= 0.3:
            analysis['pressure_level'] = 'moderate'
            analysis['recommendations'] = ['consider_faster_moves', 'reduce_complexity_threshold']
        elif time_ratio >= 0.15:
            analysis['pressure_level'] = 'high'
            analysis['recommendations'] = ['switch_to_conservative', 'reduce_depth_limit', 'faster_decisions']
        else:
            analysis['pressure_level'] = 'critical'
            analysis['recommendations'] = ['emergency_mode', 'minimal_time_per_move', 'accept_reasonable_moves']
        
        return analysis
    
    def suggest_time_allocation_adjustments(self, base_allocation: TimeAllocation) -> TimeAllocation:
        """
        Suggest adjustments to time allocation based on historical performance.
        
        Args:
            base_allocation: Base time allocation to adjust
        
        Returns:
            Adjusted TimeAllocation
        """
        if len(self.move_records) < 3:
            return base_allocation  # Not enough data
        
        recent_efficiency = self.get_current_efficiency()
        
        # If we're consistently using less time, we can be more aggressive
        if recent_efficiency < 0.7:
            # We're under-utilizing time, can be more generous
            adjustment_factor = 1.2
        elif recent_efficiency > 0.95:
            # We're cutting it close, be more conservative
            adjustment_factor = 0.85
        else:
            # Good balance
            adjustment_factor = 1.0
        
        # Apply adjustment
        adjusted = TimeAllocation(
            target_time_ms=int(base_allocation.target_time_ms * adjustment_factor),
            maximum_time_ms=base_allocation.maximum_time_ms,
            minimum_time_ms=base_allocation.minimum_time_ms,
            soft_limit_ms=int(base_allocation.soft_limit_ms * adjustment_factor),
            hard_limit_ms=base_allocation.hard_limit_ms,
            strategy=base_allocation.strategy,
            confidence=base_allocation.confidence * (1.0 if 0.8 <= recent_efficiency <= 0.95 else 0.8)
        )
        
        return adjusted
    
    def export_timing_report(self) -> Dict[str, Any]:
        """Export comprehensive timing report for analysis."""
        return {
            'game_summary': {
                'moves_played': len(self.move_records),
                'total_time_used_ms': self.game_stats.total_time_used_ms,
                'average_time_per_move_ms': self.game_stats.average_time_per_move_ms,
                'time_efficiency': self.game_stats.time_efficiency,
                'emergency_moves': self.game_stats.emergency_moves,
                'timeout_count': self.game_stats.timeout_count
            },
            'move_by_move': [
                {
                    'move': record.move_number,
                    'allocated_ms': record.allocated_time_ms,
                    'used_ms': record.used_time_ms,
                    'efficiency': record.efficiency,
                    'strategy': record.strategy.value,
                    'depth': record.depth_reached,
                    'nodes': record.nodes_searched,
                    'nps': record.nps,
                    'complexity': record.position_complexity,
                    'timeout': record.timeout_reason.value if record.timeout_reason else None
                }
                for record in self.move_records
            ],
            'performance_metrics': self.get_performance_metrics(),
            'session_stats': dict(self.session_stats)
        }
    
    def reset_game_tracking(self):
        """Reset tracking for a new game."""
        with self._lock:
            self.move_records.clear()
            self.game_stats = GameTimeStats()
            self.start_time = time.time()
            self.current_move_start = None
            self.current_allocation = None


class RealTimeMonitor:
    """Real-time monitoring of search progress."""
    
    def __init__(self, update_interval_ms: int = 100):
        self.update_interval_ms = update_interval_ms
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
        # Current search state
        self.search_start_time: Optional[float] = None
        self.current_depth = 0
        self.current_nodes = 0
        self.allocation: Optional[TimeAllocation] = None
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for real-time updates."""
        with self._lock:
            self.callbacks.append(callback)
    
    def start_monitoring(self, allocation: TimeAllocation):
        """Start real-time monitoring."""
        with self._lock:
            self.allocation = allocation
            self.search_start_time = time.perf_counter()
            self.monitoring = True
            
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        with self._lock:
            self.monitoring = False
    
    def update_search_progress(self, depth: int, nodes: int):
        """Update current search progress."""
        with self._lock:
            self.current_depth = depth
            self.current_nodes = nodes
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._send_update()
                time.sleep(self.update_interval_ms / 1000.0)
            except Exception as e:
                print(f"Monitor error: {e}")
                break
    
    def _send_update(self):
        """Send update to all callbacks."""
        if not self.search_start_time or not self.allocation:
            return
        
        elapsed_ms = int((time.perf_counter() - self.search_start_time) * 1000)
        remaining_ms = max(0, self.allocation.hard_limit_ms - elapsed_ms)
        
        progress = {
            'elapsed_ms': elapsed_ms,
            'remaining_ms': remaining_ms,
            'target_ms': self.allocation.target_time_ms,
            'depth': self.current_depth,
            'nodes': self.current_nodes,
            'nps': int(self.current_nodes / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0,
            'progress_ratio': min(1.0, elapsed_ms / self.allocation.target_time_ms) if self.allocation.target_time_ms > 0 else 0
        }
        
        for callback in self.callbacks:
            try:
                callback(progress)
            except Exception as e:
                print(f"Callback error: {e}")


# Export main classes
__all__ = [
    'MoveTimeRecord',
    'GameTimeStats', 
    'TimeTracker',
    'RealTimeMonitor'
]


def main():
    """Test the time tracking system."""
    from .time_control import TimeControlParser
    from .time_allocation import TimeAllocator
    
    # Setup
    parser = TimeControlParser()
    allocator = TimeAllocator()
    tracker = TimeTracker()
    
    # Simulate a short game
    time_control = parser.parse("3+2")
    if not time_control:
        print("Failed to parse time control")
        return
        
    remaining_time = 180000  # 3 minutes
    
    print("Time Tracking System Test:")
    print("=" * 50)
    
    for move in range(1, 6):
        # Allocate time
        allocation = allocator.allocate_time(
            time_control, remaining_time, move % 2 == 1, move
        )
        
        # Start timing
        tracker.start_move_timing(allocation)
        
        # Simulate search
        import time as time_module
        search_time = allocation.target_time_ms / 1000 * (0.8 + 0.4 * move / 10)  # Variable usage
        time_module.sleep(min(search_time, 0.5))  # Cap for testing
        
        # End timing
        record = tracker.end_move_timing(
            move_number=move,
            depth_reached=4 + move // 2,
            nodes_searched=1000 * move * move,
            position_complexity=0.5 + 0.1 * move
        )
        
        remaining_time -= record.used_time_ms
        remaining_time += time_control.increment_ms  # Add increment
        
        print(f"Move {move}: Used {record.used_time_ms}ms/{record.allocated_time_ms}ms "
              f"(efficiency: {record.efficiency:.2f}), Depth: {record.depth_reached}, "
              f"NPS: {record.nps:,}")
    
    # Print final stats
    print("\nGame Summary:")
    metrics = tracker.get_performance_metrics()
    print(f"Average efficiency: {tracker.get_current_efficiency():.2f}")
    print(f"Total moves: {metrics['total_moves']}")
    print(f"Total time used: {tracker.game_stats.total_time_used_ms}ms")


if __name__ == "__main__":
    main()
