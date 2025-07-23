"""
Enhanced Search Controller for SlowMate v0.2.02 Phase 2
Unified search control with time awareness, iterative deepening, and aspiration windows.
"""

import time
import threading
from typing import Optional, Dict, Any, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import chess

from .time_control import TimeControl, TimeControlParser
from .time_allocation import TimeAllocation, TimeAllocator
from .search_timeout import SearchTimeoutManager
from .time_tracking import TimeTracker, MoveTimeRecord
from .iterative_deepening import IterativeDeepeningSearch, IterativeConfig, SearchResult
from .aspiration_windows import AspirationWindowManager, AspirationConfig, create_aspiration_search_function


class SearchMode(Enum):
    """Different search modes available."""
    TOURNAMENT = "tournament"      # Full tournament search with time management
    ANALYSIS = "analysis"          # Deep analysis mode
    FIXED_DEPTH = "fixed_depth"    # Search to fixed depth
    FIXED_NODES = "fixed_nodes"    # Search fixed number of nodes
    FIXED_TIME = "fixed_time"      # Search for fixed time
    INFINITE = "infinite"          # Infinite analysis


@dataclass
class SearchConfig:
    """Complete search configuration."""
    # Time management
    time_control: Optional[TimeControl] = None
    move_overhead_ms: int = 50
    
    # Search limits
    max_depth: int = 50
    max_nodes: Optional[int] = None
    max_time_ms: Optional[int] = None
    
    # Iterative deepening
    use_iterative_deepening: bool = True
    iterative_config: Optional[IterativeConfig] = None
    
    # Aspiration windows
    use_aspiration_windows: bool = True
    aspiration_config: Optional[AspirationConfig] = None
    
    # Search behavior
    contempt: int = 0              # Contempt factor for draws
    multi_pv: int = 1              # Number of principal variations
    
    # Emergency settings
    emergency_time_threshold: float = 0.1  # Emergency when < 10% time remaining
    minimum_search_depth: int = 1          # Minimum depth even in emergency


class SearchController:
    """
    Master search controller that coordinates all search components.
    
    This class provides a unified interface for tournament play, combining:
    - Time management and allocation
    - Iterative deepening search
    - Aspiration windows optimization
    - Comprehensive performance tracking
    """
    
    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        
        # Initialize components
        self.time_parser = TimeControlParser()
        self.time_allocator = TimeAllocator()
        self.time_tracker = TimeTracker()
        
        # Search components
        iterative_config = self.config.iterative_config or IterativeConfig()
        self.iterative_search = IterativeDeepeningSearch(iterative_config)
        
        aspiration_config = self.config.aspiration_config or AspirationConfig()
        self.aspiration_manager = AspirationWindowManager(aspiration_config)
        
        # Game state
        self.current_position: Optional[chess.Board] = None
        self.move_number = 1
        self.remaining_time_ms = 0
        self.is_white_to_move = True
        
        # Search state
        self.search_in_progress = False
        self.search_cancelled = False
        self.search_thread: Optional[threading.Thread] = None
        self.current_search_result: Optional[SearchResult] = None
        
        # Callbacks for real-time updates
        self.info_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Base search function (to be set by engine)
        self.base_search_function: Optional[Callable] = None
    
    def set_base_search_function(self, search_func: Callable):
        """
        Set the base search function used by the engine.
        
        Function signature should be:
        search_func(position: chess.Board, depth: int, alpha: int, beta: int, 
                   timeout_manager: SearchTimeoutManager) -> SearchResult
        """
        self.base_search_function = search_func
        
        # Create aspiration-enhanced search function if enabled
        if self.config.use_aspiration_windows:
            enhanced_search = create_aspiration_search_function(
                search_func, 
                self.aspiration_manager
            )
            self.iterative_search.set_search_function(enhanced_search)
        else:
            self.iterative_search.set_search_function(search_func)
    
    def set_position(self, position: chess.Board, move_number: int = 1):
        """Set the current position to search."""
        self.current_position = position.copy()
        self.move_number = move_number
        self.is_white_to_move = position.turn
    
    def set_time_control(self, time_control_str: str):
        """Set time control from string (e.g., "15+10", "40/90+30")."""
        self.config.time_control = self.time_parser.parse(time_control_str)
    
    def set_remaining_time(self, time_ms: int):
        """Set remaining time for current side."""
        self.remaining_time_ms = time_ms
    
    def add_info_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for real-time search information."""
        self.info_callbacks.append(callback)
    
    def search_position(
        self,
        position: Optional[chess.Board] = None,
        time_allocation: Optional[TimeAllocation] = None,
        depth_limit: Optional[int] = None,
        nodes_limit: Optional[int] = None,
        time_limit_ms: Optional[int] = None,
        search_mode: SearchMode = SearchMode.TOURNAMENT
    ) -> SearchResult:
        """
        Search the current position with full time management.
        
        Args:
            position: Position to search (uses current if None)
            time_allocation: Override time allocation
            depth_limit: Override depth limit
            nodes_limit: Override nodes limit
            time_limit_ms: Override time limit
            search_mode: Search mode to use
        
        Returns:
            SearchResult with best move and analysis
        """
        if self.search_in_progress:
            raise RuntimeError("Search already in progress")
        
        if not self.base_search_function:
            raise RuntimeError("Base search function not set")
        
        # Use provided position or current position
        search_position = position or self.current_position
        if not search_position:
            raise ValueError("No position to search")
        
        # Determine search parameters
        allocation = time_allocation or self._calculate_time_allocation(search_mode)
        
        # Apply overrides
        if depth_limit is not None:
            self.config.max_depth = depth_limit
        if nodes_limit is not None:
            self.config.max_nodes = nodes_limit
        if time_limit_ms is not None:
            allocation.hard_limit_ms = time_limit_ms
            allocation.soft_limit_ms = min(allocation.soft_limit_ms, time_limit_ms)
        
        # Start time tracking
        self.time_tracker.start_move_timing(allocation)
        
        # Perform search
        try:
            self.search_in_progress = True
            self.search_cancelled = False
            
            if search_mode == SearchMode.FIXED_DEPTH and depth_limit:
                result = self._search_fixed_depth(search_position, depth_limit)
            elif search_mode == SearchMode.FIXED_NODES and nodes_limit:
                result = self._search_fixed_nodes(search_position, nodes_limit)
            elif search_mode == SearchMode.FIXED_TIME and time_limit_ms:
                result = self._search_fixed_time(search_position, time_limit_ms)
            elif search_mode == SearchMode.INFINITE:
                result = self._search_infinite(search_position)
            else:
                # Tournament or analysis mode
                result = self._search_tournament(search_position, allocation)
            
            # Record timing
            timing_record = self.time_tracker.end_move_timing(
                move_number=self.move_number,
                depth_reached=result.depth,
                nodes_searched=result.nodes,
                position_complexity=self._estimate_position_complexity(search_position)
            )
            
            # Update remaining time
            if self.config.time_control and self.config.time_control.is_time_limited:
                self.remaining_time_ms -= timing_record.used_time_ms
                if self.config.time_control.increment_ms:
                    self.remaining_time_ms += self.config.time_control.increment_ms
            
            return result
            
        finally:
            self.search_in_progress = False
    
    def _calculate_time_allocation(self, search_mode: SearchMode) -> TimeAllocation:
        """Calculate time allocation for the current position."""
        if not self.config.time_control:
            # Default allocation for analysis
            from .time_allocation import TimeAllocation, AllocationStrategy
            return TimeAllocation(
                target_time_ms=5000,
                maximum_time_ms=30000,
                minimum_time_ms=500,
                soft_limit_ms=8000,
                hard_limit_ms=25000,
                strategy=AllocationStrategy.ADAPTIVE
            )
        
        # Calculate position complexity for adaptive allocation
        complexity = self._estimate_position_complexity(self.current_position)
        
        return self.time_allocator.allocate_time(
            time_control=self.config.time_control,
            remaining_time_ms=self.remaining_time_ms,
            is_white_to_move=self.is_white_to_move,
            move_number=self.move_number,
            position_complexity=complexity
        )
    
    def _estimate_position_complexity(self, position: Optional[chess.Board]) -> float:
        """Estimate position complexity (0-1 scale)."""
        if not position:
            return 0.5
        
        complexity = 0.5  # Base complexity
        
        # More pieces = higher complexity (up to middlegame)
        piece_count = len(position.piece_map())
        if piece_count > 20:
            complexity += 0.2  # Opening/early middlegame
        elif piece_count < 10:
            complexity -= 0.1  # Endgame is often simpler
        
        # More legal moves = higher complexity
        legal_moves = len(list(position.legal_moves))
        if legal_moves > 35:
            complexity += 0.1
        elif legal_moves < 20:
            complexity -= 0.1
        
        # Check and threats increase complexity
        if position.is_check():
            complexity += 0.2
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, complexity))
    
    def _search_tournament(self, position: chess.Board, allocation: TimeAllocation) -> SearchResult:
        """Perform tournament search with iterative deepening."""
        if self.config.use_iterative_deepening:
            return self.iterative_search.search(
                position=position,
                allocation=allocation,
                depth_limit=self.config.max_depth,
                nodes_limit=self.config.max_nodes
            )
        else:
            # Single depth search (fallback)
            return self._single_depth_search(position, self.config.max_depth, allocation)
    
    def _search_fixed_depth(self, position: chess.Board, depth: int) -> SearchResult:
        """Search to fixed depth."""
        from .time_allocation import TimeAllocation, AllocationStrategy
        
        # Create generous time allocation for fixed depth
        allocation = TimeAllocation(
            target_time_ms=30000,
            maximum_time_ms=300000,
            minimum_time_ms=1000,
            soft_limit_ms=60000,
            hard_limit_ms=300000,
            strategy=AllocationStrategy.FIXED_PER_MOVE
        )
        
        return self._single_depth_search(position, depth, allocation)
    
    def _search_fixed_nodes(self, position: chess.Board, nodes: int) -> SearchResult:
        """Search fixed number of nodes."""
        # This would need integration with the base search function
        # For now, convert to approximate depth
        estimated_depth = max(1, min(20, nodes // 10000))
        return self._search_fixed_depth(position, estimated_depth)
    
    def _search_fixed_time(self, position: chess.Board, time_ms: int) -> SearchResult:
        """Search for fixed time."""
        from .time_allocation import TimeAllocation, AllocationStrategy
        
        allocation = TimeAllocation(
            target_time_ms=int(time_ms * 0.9),
            maximum_time_ms=time_ms,
            minimum_time_ms=min(100, time_ms // 10),
            soft_limit_ms=int(time_ms * 0.8),
            hard_limit_ms=time_ms,
            strategy=AllocationStrategy.FIXED_PER_MOVE
        )
        
        return self.iterative_search.search(
            position=position,
            allocation=allocation,
            depth_limit=self.config.max_depth
        )
    
    def _search_infinite(self, position: chess.Board) -> SearchResult:
        """Infinite search mode."""
        from .time_allocation import TimeAllocation, AllocationStrategy
        
        # Very large time allocation
        allocation = TimeAllocation(
            target_time_ms=3600000,  # 1 hour
            maximum_time_ms=3600000,
            minimum_time_ms=1000,
            soft_limit_ms=3600000,
            hard_limit_ms=3600000,
            strategy=AllocationStrategy.ADAPTIVE
        )
        
        return self.iterative_search.search(
            position=position,
            allocation=allocation,
            depth_limit=self.config.max_depth
        )
    
    def _single_depth_search(self, position: chess.Board, depth: int, allocation: TimeAllocation) -> SearchResult:
        """Perform single depth search (fallback)."""
        if not self.base_search_function:
            raise RuntimeError("Base search function not set")
        
        timeout_manager = SearchTimeoutManager()
        timeout_manager.start_search(allocation)
        
        try:
            result = self.base_search_function(
                position, depth, -30000, 30000, timeout_manager
            )
            return result or SearchResult()
        finally:
            timeout_manager.stop_search()
    
    def stop_search(self):
        """Stop current search."""
        self.search_cancelled = True
        if self.iterative_search:
            self.iterative_search.search_cancelled = True
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics."""
        stats = {
            'time_tracking': self.time_tracker.get_performance_metrics(),
            'move_number': self.move_number,
            'remaining_time_ms': self.remaining_time_ms,
            'search_in_progress': self.search_in_progress
        }
        
        if self.iterative_search:
            stats['iterative_search'] = self.iterative_search.get_performance_stats()
        
        if self.aspiration_manager:
            stats['aspiration_windows'] = self.aspiration_manager.get_statistics()
        
        return stats
    
    def reset_for_new_game(self):
        """Reset controller for new game."""
        self.time_tracker.reset_game_tracking()
        self.aspiration_manager.reset_statistics()
        self.move_number = 1
        self.remaining_time_ms = 0
        self.search_in_progress = False
        self.search_cancelled = False


# Export main class
__all__ = [
    'SearchMode',
    'SearchConfig', 
    'SearchController'
]


def main():
    """Test the search controller."""
    import chess
    
    # Mock base search function
    def mock_search(position, depth, alpha, beta, timeout_manager):
        import time
        time.sleep(0.1)  # Simulate search time
        
        # Check timeout
        status = timeout_manager.check_all_limits(depth, 1000)
        if status.should_stop:
            return None
        
        moves = list(position.legal_moves)
        if not moves:
            return None
        
        return SearchResult(
            best_move=moves[0],
            evaluation=depth * 5,
            depth=depth,
            nodes=depth * 500,
            pv_line=[moves[0]]
        )
    
    # Create search controller
    config = SearchConfig(
        max_depth=6,
        use_iterative_deepening=True,
        use_aspiration_windows=True
    )
    controller = SearchController(config)
    controller.set_base_search_function(mock_search)
    
    # Set up position and time control
    position = chess.Board()
    controller.set_position(position)
    controller.set_time_control("3+2")
    controller.set_remaining_time(180000)  # 3 minutes
    
    print("Search Controller Test:")
    print("=" * 40)
    
    # Perform tournament search
    result = controller.search_position(search_mode=SearchMode.TOURNAMENT)
    
    print(f"Search Result:")
    print(f"  Best move: {result.best_move}")
    print(f"  Evaluation: {result.evaluation}")
    print(f"  Depth: {result.depth}")
    print(f"  Nodes: {result.nodes:,}")
    print(f"  Time: {result.time_ms}ms")
    print(f"  NPS: {result.nps:,}")
    
    # Print statistics
    print(f"\nSearch Statistics:")
    stats = controller.get_search_stats()
    print(f"  Remaining time: {stats['remaining_time_ms']}ms")
    if 'iterative_search' in stats:
        it_stats = stats['iterative_search']
        print(f"  Iterations completed: {it_stats['iterations_completed']}")
        print(f"  Last complete depth: {it_stats['last_complete_depth']}")


if __name__ == "__main__":
    main()
