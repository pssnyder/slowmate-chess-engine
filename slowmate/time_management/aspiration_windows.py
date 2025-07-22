"""
Aspiration Windows for SlowMate v0.2.02 Phase 2
Narrow window search optimization for improved search efficiency.
"""

from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import math

from .iterative_deepening import SearchResult


class AspirationResult(Enum):
    """Results from aspiration window search."""
    SUCCESS = "success"        # Search completed within window
    FAIL_LOW = "fail_low"     # Search failed low (alpha cutoff)  
    FAIL_HIGH = "fail_high"   # Search failed high (beta cutoff)
    TIMEOUT = "timeout"       # Search timed out
    ERROR = "error"          # Search error


@dataclass 
class AspirationWindow:
    """Represents an aspiration window for search."""
    alpha: int
    beta: int
    center: int
    delta: int
    
    @property
    def width(self) -> int:
        """Width of the aspiration window."""
        return self.beta - self.alpha
    
    def contains(self, value: int) -> bool:
        """Check if a value is within this window."""
        return self.alpha < value < self.beta
    
    def widen(self, factor: float = 2.0) -> 'AspirationWindow':
        """Create a wider version of this window."""
        new_delta = int(self.delta * factor)
        return AspirationWindow(
            alpha=self.center - new_delta,
            beta=self.center + new_delta, 
            center=self.center,
            delta=new_delta
        )
    
    def widen_low(self, factor: float = 2.0) -> 'AspirationWindow':
        """Widen only the lower bound (alpha)."""
        new_delta_low = int(self.delta * factor)
        return AspirationWindow(
            alpha=self.center - new_delta_low,
            beta=self.beta,
            center=self.center,
            delta=max(new_delta_low, self.delta)
        )
    
    def widen_high(self, factor: float = 2.0) -> 'AspirationWindow':
        """Widen only the upper bound (beta).""" 
        new_delta_high = int(self.delta * factor)
        return AspirationWindow(
            alpha=self.alpha,
            beta=self.center + new_delta_high,
            center=self.center,
            delta=max(new_delta_high, self.delta)
        )


@dataclass
class AspirationConfig:
    """Configuration for aspiration windows."""
    initial_delta: int = 50           # Initial window size
    growth_factor: float = 2.0        # How much to widen on failure
    max_delta: int = 1000            # Maximum window size
    max_attempts: int = 4            # Maximum re-search attempts
    min_depth_for_aspiration: int = 3 # Minimum depth to use aspiration
    
    # Special handling for different evaluation ranges
    large_eval_threshold: int = 500   # Threshold for "large" evaluations
    large_eval_factor: float = 1.5    # Extra widening for large evals
    
    # Mate score handling
    mate_threshold: int = 29000       # Threshold for mate scores
    mate_window_size: int = 200       # Special window size for mate scores


class AspirationWindowManager:
    """Manages aspiration windows for iterative deepening search."""
    
    def __init__(self, config: Optional[AspirationConfig] = None):
        self.config = config or AspirationConfig()
        self.search_history: Dict[int, SearchResult] = {}  # depth -> result
        self.window_history: Dict[int, AspirationWindow] = {}  # depth -> window used
        
        # Statistics
        self.total_searches = 0
        self.successful_searches = 0
        self.fail_high_count = 0
        self.fail_low_count = 0
        self.total_attempts = 0
    
    def should_use_aspiration(self, depth: int, prev_evaluation: Optional[int]) -> bool:
        """
        Determine if aspiration windows should be used for this depth.
        
        Args:
            depth: Current search depth
            prev_evaluation: Previous evaluation (None if no previous result)
        
        Returns:
            True if aspiration windows should be used
        """
        # Don't use aspiration for shallow depths
        if depth < self.config.min_depth_for_aspiration:
            return False
        
        # Don't use aspiration if no previous evaluation
        if prev_evaluation is None:
            return False
        
        # Don't use aspiration for mate scores (too risky)
        if abs(prev_evaluation) >= self.config.mate_threshold:
            return False
        
        return True
    
    def create_window(
        self, 
        depth: int, 
        prev_evaluation: int,
        position_complexity: float = 0.5
    ) -> AspirationWindow:
        """
        Create an appropriate aspiration window.
        
        Args:
            depth: Current search depth
            prev_evaluation: Previous search evaluation
            position_complexity: Position complexity factor (0-1)
        
        Returns:
            AspirationWindow for this search
        """
        # Base delta
        delta = self.config.initial_delta
        
        # Adjust delta based on evaluation magnitude
        if abs(prev_evaluation) >= self.config.large_eval_threshold:
            delta = int(delta * self.config.large_eval_factor)
        
        # Adjust delta based on position complexity
        complexity_factor = 0.8 + (position_complexity * 0.4)  # 0.8 to 1.2
        delta = int(delta * complexity_factor)
        
        # Adjust delta based on search history
        if depth > 3 and (depth - 1) in self.search_history:
            prev_result = self.search_history[depth - 1]
            prev_prev_result = self.search_history.get(depth - 2)
            
            if prev_prev_result:
                # If evaluation changed significantly, use wider window
                eval_change = abs(prev_result.evaluation - prev_prev_result.evaluation)
                if eval_change > delta:
                    delta = int(eval_change * 1.2)
        
        # Special handling for mate scores
        if abs(prev_evaluation) >= self.config.mate_threshold:
            delta = self.config.mate_window_size
        
        # Clamp delta
        delta = min(delta, self.config.max_delta)
        
        window = AspirationWindow(
            alpha=prev_evaluation - delta,
            beta=prev_evaluation + delta,
            center=prev_evaluation,
            delta=delta
        )
        
        self.window_history[depth] = window
        return window
    
    def handle_search_result(
        self, 
        result: SearchResult, 
        window: AspirationWindow
    ) -> AspirationResult:
        """
        Analyze search result and determine if re-search is needed.
        
        Args:
            result: Search result
            window: Aspiration window used
        
        Returns:
            AspirationResult indicating what happened
        """
        if not result or not result.best_move:
            return AspirationResult.ERROR
        
        evaluation = result.evaluation
        
        # Check if result is within window
        if window.contains(evaluation):
            self.successful_searches += 1
            return AspirationResult.SUCCESS
        
        # Failed low (alpha cutoff)
        if evaluation <= window.alpha:
            self.fail_low_count += 1
            return AspirationResult.FAIL_LOW
        
        # Failed high (beta cutoff)  
        if evaluation >= window.beta:
            self.fail_high_count += 1
            return AspirationResult.FAIL_HIGH
        
        # Should not reach here
        return AspirationResult.ERROR
    
    def get_next_window(
        self, 
        current_window: AspirationWindow, 
        result: AspirationResult,
        search_result: Optional[SearchResult] = None
    ) -> AspirationWindow:
        """
        Get the next window to try after a failed search.
        
        Args:
            current_window: Current aspiration window
            result: Result of the search (FAIL_LOW or FAIL_HIGH)
            search_result: Actual search result (for bound adjustment)
        
        Returns:
            New aspiration window for re-search
        """
        growth_factor = self.config.growth_factor
        
        if result == AspirationResult.FAIL_LOW:
            # Search failed low, widen alpha (lower bound)
            new_window = current_window.widen_low(growth_factor)
            
            # If we have the actual evaluation, set alpha just below it
            if search_result and search_result.evaluation is not None:
                eval_buffer = max(10, current_window.delta // 4)
                new_window.alpha = min(new_window.alpha, search_result.evaluation - eval_buffer)
            
        elif result == AspirationResult.FAIL_HIGH:
            # Search failed high, widen beta (upper bound)
            new_window = current_window.widen_high(growth_factor)
            
            # If we have the actual evaluation, set beta just above it
            if search_result and search_result.evaluation is not None:
                eval_buffer = max(10, current_window.delta // 4)
                new_window.beta = max(new_window.beta, search_result.evaluation + eval_buffer)
        
        else:
            # Fallback: widen entire window
            new_window = current_window.widen(growth_factor)
        
        # Ensure delta doesn't exceed maximum
        if new_window.delta > self.config.max_delta:
            # Fall back to full window
            return AspirationWindow(
                alpha=-30000,
                beta=30000,
                center=current_window.center,
                delta=30000
            )
        
        return new_window
    
    def record_search_result(self, depth: int, result: SearchResult):
        """Record a successful search result."""
        self.search_history[depth] = result
        self.total_searches += 1
        self.total_attempts += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aspiration window statistics."""
        success_rate = self.successful_searches / max(1, self.total_searches)
        avg_attempts = self.total_attempts / max(1, self.total_searches)
        
        return {
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'success_rate': success_rate,
            'fail_high_count': self.fail_high_count,
            'fail_low_count': self.fail_low_count,
            'average_attempts': avg_attempts,
            'fail_high_rate': self.fail_high_count / max(1, self.total_searches),
            'fail_low_rate': self.fail_low_count / max(1, self.total_searches)
        }
    
    def optimize_config(self):
        """
        Optimize configuration based on search history.
        Called periodically to improve aspiration window performance.
        """
        if self.total_searches < 10:
            return  # Not enough data
        
        stats = self.get_statistics()
        
        # If success rate is too low, increase initial delta
        if stats['success_rate'] < 0.6:
            self.config.initial_delta = min(
                int(self.config.initial_delta * 1.2),
                self.config.max_delta // 2
            )
        
        # If too many fail-highs, consider starting with wider windows
        elif stats['fail_high_rate'] > 0.3:
            self.config.initial_delta = min(
                int(self.config.initial_delta * 1.1),
                self.config.max_delta // 2
            )
        
        # If too many fail-lows, might be evaluations are unstable
        elif stats['fail_low_rate'] > 0.3:
            self.config.growth_factor = min(self.config.growth_factor * 1.1, 3.0)
    
    def reset_statistics(self):
        """Reset statistics for new game or testing."""
        self.total_searches = 0
        self.successful_searches = 0
        self.fail_high_count = 0
        self.fail_low_count = 0
        self.total_attempts = 0
        self.search_history.clear()
        self.window_history.clear()


# Helper functions for integration with iterative deepening

def create_aspiration_search_function(base_search_func, window_manager: AspirationWindowManager):
    """
    Create an aspiration-enabled search function wrapper.
    
    Args:
        base_search_func: Original search function
        window_manager: Aspiration window manager
    
    Returns:
        Wrapped search function that uses aspiration windows
    """
    
    def aspiration_search(position, depth, alpha, beta, timeout_manager):
        # Check if we should use aspiration
        prev_result = None
        if depth > 1:
            prev_result = window_manager.search_history.get(depth - 1)
        
        prev_eval = prev_result.evaluation if prev_result else None
        
        if not window_manager.should_use_aspiration(depth, prev_eval):
            # Use full window
            result = base_search_func(position, depth, alpha, beta, timeout_manager)
            if result:
                window_manager.record_search_result(depth, result)
            return result
        
        # Use aspiration windows (prev_eval is guaranteed not None here)
        if prev_eval is None:
            # Fallback to full window if somehow prev_eval is None
            result = base_search_func(position, depth, alpha, beta, timeout_manager)
            if result:
                window_manager.record_search_result(depth, result)
            return result
        
        window = window_manager.create_window(depth, prev_eval)
        
        for attempt in range(window_manager.config.max_attempts):
            window_manager.total_attempts += 1
            
            # Check timeout
            status = timeout_manager.check_all_limits(depth, 0)
            if status.should_stop:
                break
            
            # Perform search with current window
            result = base_search_func(
                position, 
                depth, 
                window.alpha, 
                window.beta, 
                timeout_manager
            )
            
            if not result:
                break
            
            # Analyze result
            aspiration_result = window_manager.handle_search_result(result, window)
            
            if aspiration_result == AspirationResult.SUCCESS:
                # Success! Record result and return
                window_manager.record_search_result(depth, result)
                return result
            elif aspiration_result in [AspirationResult.FAIL_LOW, AspirationResult.FAIL_HIGH]:
                # Need to re-search with wider window
                window = window_manager.get_next_window(window, aspiration_result, result)
                continue
            else:
                # Error or timeout
                break
        
        # If we get here, aspiration failed - fall back to full window
        result = base_search_func(position, depth, alpha, beta, timeout_manager)
        if result:
            window_manager.record_search_result(depth, result)
        return result
    
    return aspiration_search


# Export main classes
__all__ = [
    'AspirationResult',
    'AspirationWindow', 
    'AspirationConfig',
    'AspirationWindowManager',
    'create_aspiration_search_function'
]


def main():
    """Test aspiration windows."""
    from .iterative_deepening import SearchResult
    
    # Create window manager
    config = AspirationConfig(initial_delta=30, max_attempts=3)
    manager = AspirationWindowManager(config)
    
    print("Aspiration Windows Test:")
    print("=" * 40)
    
    # Simulate search progression
    evaluations = [100, 120, 110, 140, 135, 200]  # Simulated evaluations
    
    for depth, evaluation in enumerate(evaluations, 1):
        print(f"\nDepth {depth}:")
        
        # Create mock previous result
        if depth > 1:
            prev_result = SearchResult(evaluation=evaluations[depth-2], depth=depth-1)
            manager.record_search_result(depth-1, prev_result)
        
        # Check if should use aspiration
        prev_eval = evaluations[depth-2] if depth > 1 else None
        should_use = manager.should_use_aspiration(depth, prev_eval)
        print(f"  Should use aspiration: {should_use}")
        
        if should_use and prev_eval is not None:
            # Create window
            window = manager.create_window(depth, prev_eval)
            print(f"  Window: [{window.alpha}, {window.beta}] (delta={window.delta})")
            
            # Simulate search result
            mock_result = SearchResult(
                best_move=None,  # We'll set this to a dummy move
                evaluation=evaluation, 
                depth=depth
            )
            # Add a dummy move to make it valid
            import chess
            mock_result.best_move = chess.Move.from_uci("e2e4")
            
            aspiration_result = manager.handle_search_result(mock_result, window)
            print(f"  Result: {aspiration_result.value}")
            
            if aspiration_result != AspirationResult.SUCCESS:
                # Show what next window would be
                next_window = manager.get_next_window(window, aspiration_result, mock_result)
                print(f"  Next window: [{next_window.alpha}, {next_window.beta}]")
        
        print(f"  Final evaluation: {evaluation}")
    
    # Print statistics
    print(f"\nFinal Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
