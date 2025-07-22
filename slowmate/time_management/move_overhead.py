"""
Move Overhead Compensation for SlowMate v0.2.02 Phase 3
Compensates for network latency, UCI communication delays, and other timing overhead.
"""

import time
from typing import Dict, List, Optional, Tuple, Deque, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading

from .time_allocation import TimeAllocation
from .time_control import TimeControl


class OverheadType(Enum):
    """Different types of timing overhead."""
    NETWORK = "network"              # Network/internet lag
    UCI_COMMUNICATION = "uci"        # UCI protocol communication  
    ENGINE_STARTUP = "startup"       # Engine initialization
    POSITION_SETUP = "position"      # Position setup/parsing
    MOVE_GENERATION = "movegen"      # Move generation overhead
    EVALUATION = "evaluation"        # Evaluation overhead
    GUI_PROCESSING = "gui"           # GUI processing delays
    SYSTEM_SCHEDULING = "system"     # OS scheduling delays


@dataclass
class OverheadMeasurement:
    """Single overhead measurement."""
    overhead_type: OverheadType
    measured_overhead_ms: int
    timestamp: float
    position_complexity: float = 0.5  # 0-1 scale
    
    @property
    def age_seconds(self) -> float:
        """Age of this measurement in seconds."""
        return time.time() - self.timestamp


@dataclass
class OverheadSettings:
    """Settings for overhead compensation."""
    # Base overhead estimates (milliseconds)
    base_overheads: Dict[OverheadType, int] = field(default_factory=lambda: {
        OverheadType.NETWORK: 50,           # 50ms network lag
        OverheadType.UCI_COMMUNICATION: 10, # 10ms UCI overhead
        OverheadType.ENGINE_STARTUP: 5,     # 5ms startup overhead
        OverheadType.POSITION_SETUP: 5,     # 5ms position setup
        OverheadType.MOVE_GENERATION: 2,    # 2ms move generation
        OverheadType.EVALUATION: 3,         # 3ms evaluation overhead
        OverheadType.GUI_PROCESSING: 20,    # 20ms GUI delays
        OverheadType.SYSTEM_SCHEDULING: 10  # 10ms system delays
    })
    
    # Measurement settings
    max_measurements_per_type: int = 100    # Keep last 100 measurements
    measurement_weight_decay: float = 0.95  # Decay factor for old measurements
    min_measurements_for_learning: int = 5  # Minimum before learning adjustments
    
    # Adaptation settings
    adaptation_rate: float = 0.1            # How quickly to adapt (0-1)
    max_overhead_adjustment: float = 2.0    # Maximum adjustment factor
    confidence_threshold: float = 0.7       # Confidence threshold for adjustments
    
    # Safety settings
    minimum_safety_buffer_ms: int = 50      # Always keep this buffer
    maximum_total_overhead_ms: int = 500    # Cap total overhead at this
    enable_dynamic_adjustment: bool = True   # Enable dynamic learning
    
    # Online/offline settings
    online_multiplier: float = 1.5          # Extra overhead for online play
    bullet_multiplier: float = 1.2          # Extra for very fast time controls
    tournament_multiplier: float = 1.3      # Extra for tournament conditions


class MoveOverheadManager:
    """
    Manages and compensates for various sources of timing overhead.
    
    This manager:
    - Tracks different types of overhead
    - Learns from actual timing measurements
    - Adjusts time allocation to compensate
    - Provides recommendations for time management
    """
    
    def __init__(self, settings: Optional[OverheadSettings] = None):
        self.settings = settings or OverheadSettings()
        
        # Measurement history for each overhead type
        self.measurements: Dict[OverheadType, Deque[OverheadMeasurement]] = {
            overhead_type: deque(maxlen=self.settings.max_measurements_per_type)
            for overhead_type in OverheadType
        }
        
        # Current overhead estimates
        self.current_estimates: Dict[OverheadType, int] = self.settings.base_overheads.copy()
        
        # Performance tracking
        self.total_moves_tracked = 0
        self.total_overhead_compensation = 0
        self.accuracy_history: List[Tuple[int, int]] = []  # (predicted, actual)
        
        # Threading for measurements
        self.measurement_lock = threading.Lock()
        
        # Calibration state
        self.calibration_mode = False
        self.calibration_measurements: List[Tuple[float, float]] = []  # (start_time, end_time)
    
    def compensate_allocation(
        self,
        base_allocation: TimeAllocation,
        time_control: TimeControl,
        position_complexity: float = 0.5,
        is_online: bool = False,
        is_tournament: bool = False
    ) -> TimeAllocation:
        """
        Adjust time allocation to compensate for overhead.
        
        Args:
            base_allocation: Base time allocation
            time_control: Current time control
            position_complexity: Position complexity (0-1)
            is_online: Whether playing online
            is_tournament: Whether in tournament conditions
            
        Returns:
            Overhead-compensated TimeAllocation
        """
        # Calculate total overhead
        total_overhead = self.calculate_total_overhead(
            position_complexity, is_online, is_tournament, time_control
        )
        
        # Apply safety buffer
        safe_overhead = min(
            total_overhead + self.settings.minimum_safety_buffer_ms,
            self.settings.maximum_total_overhead_ms
        )
        
        # Adjust allocation times
        adjusted_target = max(
            base_allocation.minimum_time_ms,
            base_allocation.target_time_ms - safe_overhead
        )
        
        adjusted_soft = max(
            adjusted_target,
            base_allocation.soft_limit_ms - safe_overhead
        )
        
        adjusted_hard = max(
            adjusted_soft + 100,  # Minimum 100ms buffer
            base_allocation.hard_limit_ms - safe_overhead
        )
        
        # Ensure we don't go below minimum thresholds
        minimum_think_time = 100  # Always think for at least 100ms
        adjusted_target = max(adjusted_target, minimum_think_time)
        adjusted_soft = max(adjusted_soft, adjusted_target)
        adjusted_hard = max(adjusted_hard, adjusted_soft)
        
        # Create compensated allocation
        compensated_allocation = TimeAllocation(
            target_time_ms=adjusted_target,
            maximum_time_ms=adjusted_hard,
            minimum_time_ms=max(base_allocation.minimum_time_ms, minimum_think_time),
            soft_limit_ms=adjusted_soft,
            hard_limit_ms=adjusted_hard,
            strategy=base_allocation.strategy,
            confidence=base_allocation.confidence * 0.9  # Slightly lower confidence
        )
        
        return compensated_allocation
    
    def calculate_total_overhead(
        self,
        position_complexity: float = 0.5,
        is_online: bool = False,
        is_tournament: bool = False,
        time_control: Optional[TimeControl] = None
    ) -> int:
        """Calculate total expected overhead for current conditions."""
        base_overhead = sum(self.current_estimates.values())
        
        # Apply multipliers based on conditions
        multiplier = 1.0
        
        if is_online:
            multiplier *= self.settings.online_multiplier
        
        if is_tournament:
            multiplier *= self.settings.tournament_multiplier
        
        # Extra overhead for very fast time controls
        if time_control and time_control.base_time_ms < 60000:  # Less than 1 minute
            multiplier *= self.settings.bullet_multiplier
        
        # Position complexity factor (complex positions may have more overhead)
        complexity_factor = 0.8 + (position_complexity * 0.4)  # 0.8 to 1.2
        multiplier *= complexity_factor
        
        total_overhead = int(base_overhead * multiplier)
        return min(total_overhead, self.settings.maximum_total_overhead_ms)
    
    def record_overhead_measurement(
        self,
        overhead_type: OverheadType,
        measured_overhead_ms: int,
        position_complexity: float = 0.5
    ):
        """Record an actual overhead measurement for learning."""
        with self.measurement_lock:
            measurement = OverheadMeasurement(
                overhead_type=overhead_type,
                measured_overhead_ms=measured_overhead_ms,
                timestamp=time.time(),
                position_complexity=position_complexity
            )
            
            self.measurements[overhead_type].append(measurement)
            
            # Update estimates if we have enough data
            if (self.settings.enable_dynamic_adjustment and
                len(self.measurements[overhead_type]) >= self.settings.min_measurements_for_learning):
                self._update_overhead_estimate(overhead_type)
    
    def _update_overhead_estimate(self, overhead_type: OverheadType):
        """Update overhead estimate based on recent measurements."""
        measurements = list(self.measurements[overhead_type])
        if not measurements:
            return
        
        # Calculate weighted average (more recent measurements have higher weight)
        total_weight = 0.0
        weighted_sum = 0.0
        
        current_time = time.time()
        for measurement in measurements:
            age = current_time - measurement.timestamp
            weight = (self.settings.measurement_weight_decay ** age)
            total_weight += weight
            weighted_sum += measurement.measured_overhead_ms * weight
        
        if total_weight > 0:
            new_estimate = int(weighted_sum / total_weight)
            
            # Adaptive update (don't change too quickly)
            current_estimate = self.current_estimates[overhead_type]
            adjusted_estimate = (
                current_estimate * (1 - self.settings.adaptation_rate) +
                new_estimate * self.settings.adaptation_rate
            )
            
            # Apply safety bounds
            base_estimate = self.settings.base_overheads[overhead_type]
            min_estimate = int(base_estimate * 0.5)  # Don't go below 50% of base
            max_estimate = int(base_estimate * self.settings.max_overhead_adjustment)
            
            adjusted_estimate = max(min_estimate, min(max_estimate, adjusted_estimate))
            
            self.current_estimates[overhead_type] = int(adjusted_estimate)
    
    def start_move_timing(self) -> str:
        """Start timing a move for overhead measurement. Returns timing ID."""
        timing_id = f"move_{time.time()}_{id(self)}"
        setattr(self, f"_timing_{timing_id}", time.time())
        return timing_id
    
    def end_move_timing(
        self,
        timing_id: str,
        planned_time_ms: int,
        position_complexity: float = 0.5
    ):
        """End timing and record overhead measurement."""
        start_time = getattr(self, f"_timing_{timing_id}", None)
        if start_time is None:
            return
        
        end_time = time.time()
        actual_time_ms = int((end_time - start_time) * 1000)
        
        # Calculate overhead (difference between actual and planned time)
        overhead_ms = max(0, actual_time_ms - planned_time_ms)
        
        # Record as UCI communication overhead (simplified)
        self.record_overhead_measurement(
            OverheadType.UCI_COMMUNICATION,
            overhead_ms,
            position_complexity
        )
        
        # Track accuracy
        self.accuracy_history.append((planned_time_ms, actual_time_ms))
        if len(self.accuracy_history) > 100:
            self.accuracy_history = self.accuracy_history[-100:]
        
        # Cleanup
        delattr(self, f"_timing_{timing_id}")
        
        self.total_moves_tracked += 1
        self.total_overhead_compensation += overhead_ms
    
    def calibrate_overhead(
        self,
        overhead_type: OverheadType,
        test_function: Callable[[], None],
        num_tests: int = 10
    ) -> int:
        """
        Calibrate overhead for a specific type by running test function.
        
        Args:
            overhead_type: Type of overhead to calibrate
            test_function: Function to run for measurement
            num_tests: Number of test runs
            
        Returns:
            Average measured overhead in milliseconds
        """
        measurements = []
        
        for _ in range(num_tests):
            start_time = time.perf_counter()
            test_function()
            end_time = time.perf_counter()
            
            overhead_ms = int((end_time - start_time) * 1000)
            measurements.append(overhead_ms)
        
        # Calculate average and record
        if measurements:
            avg_overhead = sum(measurements) // len(measurements)
            self.current_estimates[overhead_type] = avg_overhead
            
            # Record individual measurements
            for measurement in measurements:
                self.record_overhead_measurement(overhead_type, measurement)
            
            return avg_overhead
        
        return 0
    
    def get_overhead_analysis(self) -> Dict[str, Any]:
        """Get detailed analysis of current overhead situation."""
        analysis = {
            "current_estimates": self.current_estimates.copy(),
            "base_estimates": self.settings.base_overheads.copy(),
            "total_overhead": sum(self.current_estimates.values()),
            "moves_tracked": self.total_moves_tracked,
            "total_compensation": self.total_overhead_compensation
        }
        
        # Calculate measurement statistics
        measurement_stats = {}
        for overhead_type, measurements in self.measurements.items():
            if measurements:
                recent_measurements = [m.measured_overhead_ms for m in measurements]
                measurement_stats[overhead_type.value] = {
                    "count": len(recent_measurements),
                    "average": sum(recent_measurements) // len(recent_measurements),
                    "min": min(recent_measurements),
                    "max": max(recent_measurements),
                    "most_recent": recent_measurements[-1] if recent_measurements else 0
                }
            else:
                measurement_stats[overhead_type.value] = {"count": 0}
        
        analysis["measurement_stats"] = measurement_stats
        
        # Calculate accuracy statistics
        if self.accuracy_history:
            errors = [abs(actual - planned) for planned, actual in self.accuracy_history]
            analysis["accuracy"] = {
                "average_error_ms": sum(errors) // len(errors),
                "max_error_ms": max(errors),
                "predictions": len(self.accuracy_history)
            }
        
        # Provide recommendations
        recommendations = []
        total_overhead = sum(self.current_estimates.values())
        
        if total_overhead > 200:
            recommendations.append("High overhead detected - consider optimizing setup")
        
        if analysis.get("accuracy", {}).get("average_error_ms", 0) > 100:
            recommendations.append("Large timing errors - may need recalibration")
        
        for overhead_type, estimate in self.current_estimates.items():
            base = self.settings.base_overheads[overhead_type]
            if estimate > base * 2:
                recommendations.append(f"High {overhead_type.value} overhead - investigate")
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    def reset_measurements(self):
        """Reset all overhead measurements and return to base estimates."""
        with self.measurement_lock:
            for measurements in self.measurements.values():
                measurements.clear()
            
            self.current_estimates = self.settings.base_overheads.copy()
            self.accuracy_history.clear()
            self.total_moves_tracked = 0
            self.total_overhead_compensation = 0
    
    def export_measurements(self) -> Dict[str, List[Dict]]:
        """Export measurements for external analysis."""
        exported = {}
        
        with self.measurement_lock:
            for overhead_type, measurements in self.measurements.items():
                exported[overhead_type.value] = [
                    {
                        "overhead_ms": m.measured_overhead_ms,
                        "timestamp": m.timestamp,
                        "position_complexity": m.position_complexity,
                        "age_seconds": m.age_seconds
                    }
                    for m in measurements
                ]
        
        return exported
    
    def import_measurements(self, measurement_data: Dict[str, List[Dict]]):
        """Import measurements from external source."""
        with self.measurement_lock:
            for overhead_type_name, measurement_list in measurement_data.items():
                try:
                    overhead_type = OverheadType(overhead_type_name)
                    measurements_deque = self.measurements[overhead_type]
                    
                    for data in measurement_list:
                        measurement = OverheadMeasurement(
                            overhead_type=overhead_type,
                            measured_overhead_ms=data["overhead_ms"],
                            timestamp=data["timestamp"],
                            position_complexity=data.get("position_complexity", 0.5)
                        )
                        measurements_deque.append(measurement)
                    
                    # Update estimates
                    if len(measurements_deque) >= self.settings.min_measurements_for_learning:
                        self._update_overhead_estimate(overhead_type)
                
                except (ValueError, KeyError) as e:
                    print(f"Error importing measurements for {overhead_type_name}: {e}")


# Export main classes
__all__ = [
    'OverheadType',
    'OverheadMeasurement',
    'OverheadSettings',
    'MoveOverheadManager'
]


def main():
    """Test the move overhead compensation system."""
    import chess
    from .time_allocation import TimeAllocation, AllocationStrategy
    from .time_control import TimeControlParser
    
    # Create overhead manager
    overhead_manager = MoveOverheadManager()
    
    # Create test time control and allocation
    parser = TimeControlParser()
    time_control = parser.parse("5+3")  # 5 minutes + 3 second increment
    
    base_allocation = TimeAllocation(
        target_time_ms=10000,  # 10 seconds
        maximum_time_ms=15000,
        minimum_time_ms=1000,
        soft_limit_ms=8000,
        hard_limit_ms=12000,
        strategy=AllocationStrategy.ADAPTIVE
    )
    
    print("Move Overhead Compensation Test:")
    print("=" * 50)
    
    # Test different scenarios
    scenarios = [
        ("Normal conditions", False, False, 0.5),
        ("Online play", True, False, 0.5),
        ("Tournament", False, True, 0.6),
        ("Complex position", False, False, 0.9),
        ("Online tournament", True, True, 0.7)
    ]
    
    for scenario_name, is_online, is_tournament, complexity in scenarios:
        if time_control:
            compensated = overhead_manager.compensate_allocation(
                base_allocation, time_control, complexity, is_online, is_tournament
            )
            
            total_overhead = overhead_manager.calculate_total_overhead(
                complexity, is_online, is_tournament, time_control
            )
        else:
            print(f"  {scenario_name}: Failed to parse time control")
            continue
        
        print(f"\n{scenario_name}:")
        print(f"  Base target time: {base_allocation.target_time_ms}ms")
        print(f"  Calculated overhead: {total_overhead}ms")
        print(f"  Compensated target: {compensated.target_time_ms}ms")
        print(f"  Compensation: {base_allocation.target_time_ms - compensated.target_time_ms}ms")
        print(f"  Soft limit: {compensated.soft_limit_ms}ms")
        print(f"  Hard limit: {compensated.hard_limit_ms}ms")
    
    print("\n" + "-" * 50)
    
    # Test overhead measurement and learning
    print("\nTesting overhead measurement:")
    
    # Simulate some overhead measurements
    test_overheads = [
        (OverheadType.NETWORK, 75),
        (OverheadType.UCI_COMMUNICATION, 15),
        (OverheadType.GUI_PROCESSING, 30),
        (OverheadType.NETWORK, 80),
        (OverheadType.UCI_COMMUNICATION, 12)
    ]
    
    for overhead_type, measurement in test_overheads:
        overhead_manager.record_overhead_measurement(overhead_type, measurement)
        print(f"  Recorded {overhead_type.value}: {measurement}ms")
    
    # Show analysis
    analysis = overhead_manager.get_overhead_analysis()
    
    print(f"\nOverhead Analysis:")
    print(f"  Total moves tracked: {analysis['moves_tracked']}")
    print(f"  Total estimated overhead: {analysis['total_overhead']}ms")
    
    print(f"\nCurrent estimates vs base:")
    for overhead_type in OverheadType:
        current = analysis['current_estimates'][overhead_type]
        base = analysis['base_estimates'][overhead_type] 
        change = current - base
        print(f"  {overhead_type.value}: {current}ms (base: {base}ms, change: {change:+d}ms)")
    
    # Test timing functionality
    print(f"\nTesting move timing:")
    timing_id = overhead_manager.start_move_timing()
    
    # Simulate some work
    time.sleep(0.05)  # 50ms
    
    planned_time = 1000  # We planned 1000ms
    overhead_manager.end_move_timing(timing_id, planned_time)
    
    final_analysis = overhead_manager.get_overhead_analysis()
    if "accuracy" in final_analysis:
        accuracy = final_analysis["accuracy"]
        print(f"  Average timing error: {accuracy['average_error_ms']}ms")
        print(f"  Timing predictions made: {accuracy['predictions']}")
    
    # Show recommendations
    if final_analysis["recommendations"]:
        print(f"\nRecommendations:")
        for rec in final_analysis["recommendations"]:
            print(f"  - {rec}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
