"""
Iterative Deepening Framework for SlowMate v0.2.02 Phase 2
Progressive depth increase with time awareness for optimal search control.
"""

import time
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import chess

from .time_allocation import TimeAllocation
from .search_timeout import SearchTimeoutManager, TimeoutStatus, TimeoutReason


class SearchResult:
    """Result from a search iteration."""
    
    def __init__(
        self,
        best_move: Optional[chess.Move] = None,
        evaluation: int = 0,
        depth: int = 0,
        nodes: int = 0,
        time_ms: int = 0,
        pv_line: Optional[List[chess.Move]] = None,
        is_complete: bool = False,
        mate_in: Optional[int] = None
    ):
        self.best_move = best_move
        self.evaluation = evaluation
        self.depth = depth
        self.nodes = nodes
        self.time_ms = time_ms
        self.pv_line = pv_line or []
        self.is_complete = is_complete
        self.mate_in = mate_in
    
    @property
    def nps(self) -> int:
        """Nodes per second."""
        if self.time_ms == 0:
            return 0
        return int(self.nodes / (self.time_ms / 1000))
    
    def __str__(self) -> str:
        mate_str = f" mate {self.mate_in}" if self.mate_in is not None else ""
        pv_str = " ".join([move.uci() for move in self.pv_line[:5]])
        return (f"depth {self.depth} score cp {self.evaluation}{mate_str} "
                f"nodes {self.nodes} time {self.time_ms} pv {pv_str}")


@dataclass
class IterativeConfig:
    """Configuration for iterative deepening search."""
    min_depth: int = 1
    max_depth: int = 50
    use_aspiration_windows: bool = True
    aspiration_delta: int = 50
    aspiration_growth_factor: float = 2.0
    emergency_min_depth: int = 3
    time_allocation_buffer: float = 0.9  # Use 90% of allocated time for safety


class IterativeDeepeningSearch:
    """
    Iterative deepening search engine with time awareness.
    
    This class manages progressive depth searches, maintaining the best move
    at each depth and providing early termination when time runs out.
    """
    
    def __init__(self, config: Optional[IterativeConfig] = None):
        self.config = config or IterativeConfig()
        self.timeout_manager = SearchTimeoutManager()
        
        # Search state
        self.current_best_move: Optional[chess.Move] = None
        self.current_evaluation = 0
        self.depth_results: Dict[int, SearchResult] = {}
        self.search_cancelled = False
        
        # Search function - to be provided by engine
        self.search_function: Optional[Callable] = None
        
        # Statistics
        self.total_nodes = 0
        self.iterations_completed = 0
        self.last_complete_depth = 0
    
    def set_search_function(self, search_func: Callable):
        """
        Set the actual search function to use for each depth.
        
        The function should have signature:
        search_func(position: chess.Board, depth: int, alpha: int, beta: int, 
                   timeout_manager: SearchTimeoutManager) -> SearchResult
        """
        self.search_function = search_func
    
    def search(
        self, 
        position: chess.Board, 
        allocation: TimeAllocation,
        depth_limit: Optional[int] = None,
        nodes_limit: Optional[int] = None
    ) -> SearchResult:
        """
        Perform iterative deepening search.
        
        Args:
            position: Chess position to search
            allocation: Time allocation for this search
            depth_limit: Optional depth limit override
            nodes_limit: Optional nodes limit override
        
        Returns:
            SearchResult with best move and evaluation
        """
        if not self.search_function:
            raise ValueError("Search function not set. Call set_search_function() first.")
        
        # Reset search state
        self._reset_search_state()
        
        # Start timeout management
        timer = self.timeout_manager.start_search(
            allocation, 
            depth_limit, 
            nodes_limit,
            self._on_timeout
        )
        
        start_time = time.perf_counter()
        best_result = SearchResult()
        
        # Determine depth range
        min_depth = max(self.config.min_depth, 1)
        max_depth = min(depth_limit or self.config.max_depth, self.config.max_depth)
        
        # Emergency situation handling
        is_emergency = allocation.has_emergency_time
        if is_emergency:
            min_depth = min(min_depth, self.config.emergency_min_depth)
            max_depth = min(max_depth, self.config.emergency_min_depth + 2)
        
        try:
            # Iterative deepening loop
            for depth in range(min_depth, max_depth + 1):
                # Check if we should start this depth
                if not self.timeout_manager.should_start_new_depth(depth):
                    break
                
                # Check time before starting iteration
                status = self.timeout_manager.check_all_limits(depth - 1, self.total_nodes)
                if status.should_stop:
                    break
                
                # Perform search at this depth
                depth_result = self._search_at_depth(position, depth, timer)
                
                if depth_result and depth_result.best_move:
                    # Update best result
                    best_result = depth_result
                    self.depth_results[depth] = depth_result
                    self.last_complete_depth = depth
                    self.iterations_completed += 1
                    
                    # Update current best move
                    self.current_best_move = depth_result.best_move
                    self.current_evaluation = depth_result.evaluation
                    
                    # Check for mate
                    if depth_result.mate_in is not None:
                        # Found mate, no need to search deeper
                        break
                else:
                    # Search was interrupted or failed
                    break
                
                # Emergency exit for very low time
                if is_emergency and depth >= self.config.emergency_min_depth:
                    remaining = timer.get_remaining_ms()
                    if remaining < allocation.target_time_ms * 0.1:  # Less than 10% remaining
                        break
        
        except Exception as e:
            print(f"Search error at depth {depth}: {e}")
            # Return best result found so far
        
        finally:
            self.timeout_manager.stop_search()
        
        # Ensure we have a valid result
        if not best_result.best_move and self.current_best_move:
            best_result.best_move = self.current_best_move
            best_result.evaluation = self.current_evaluation
        
        # Update final statistics
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        best_result.time_ms = elapsed_ms
        best_result.nodes = self.total_nodes
        
        return best_result
    
    def _search_at_depth(
        self, 
        position: chess.Board, 
        depth: int, 
        timer
    ) -> Optional[SearchResult]:
        """Search at a specific depth with aspiration windows."""
        
        if self.config.use_aspiration_windows and depth > 2 and self.current_evaluation != 0:
            # Use aspiration windows for depths > 2
            return self._aspiration_search(position, depth, timer)
        else:
            # Full window search
            return self._full_window_search(position, depth, timer)
    
    def _full_window_search(
        self, 
        position: chess.Board, 
        depth: int, 
        timer
    ) -> Optional[SearchResult]:
        """Perform full window search."""
        if not self.search_function:
            return None
            
        alpha = -30000  # Large negative value
        beta = 30000    # Large positive value
        
        try:
            result = self.search_function(
                position, 
                depth, 
                alpha, 
                beta, 
                self.timeout_manager
            )
            
            if result:
                self.total_nodes += result.nodes
                result.depth = depth
            
            return result
            
        except Exception as e:
            print(f"Full window search error at depth {depth}: {e}")
            return None
    
    def _aspiration_search(
        self, 
        position: chess.Board, 
        depth: int, 
        timer
    ) -> Optional[SearchResult]:
        """Perform aspiration window search."""
        
        # Start with narrow window around previous evaluation
        delta = self.config.aspiration_delta
        alpha = self.current_evaluation - delta
        beta = self.current_evaluation + delta
        
        max_attempts = 4
        
        for attempt in range(max_attempts):
            try:
                # Check timeout before each attempt
                status = self.timeout_manager.check_all_limits(depth, self.total_nodes)
                if status.should_stop:
                    return None
                
                if not self.search_function:
                    return None
                
                result = self.search_function(
                    position, 
                    depth, 
                    alpha, 
                    beta, 
                    self.timeout_manager
                )
                
                if not result:
                    return None
                
                self.total_nodes += result.nodes
                result.depth = depth
                
                # Check if search failed high or low
                if result.evaluation <= alpha:
                    # Failed low, widen alpha
                    alpha = result.evaluation - int(delta * self.config.aspiration_growth_factor)
                    delta = int(delta * self.config.aspiration_growth_factor)
                    continue
                elif result.evaluation >= beta:
                    # Failed high, widen beta
                    beta = result.evaluation + int(delta * self.config.aspiration_growth_factor)
                    delta = int(delta * self.config.aspiration_growth_factor)
                    continue
                else:
                    # Success within window
                    return result
                    
            except Exception as e:
                print(f"Aspiration search error at depth {depth}, attempt {attempt + 1}: {e}")
                # Fall back to full window on error
                break
        
        # If aspiration windows failed, fall back to full window
        print(f"Aspiration window failed at depth {depth}, falling back to full window")
        return self._full_window_search(position, depth, timer)
    
    def _on_timeout(self, status: TimeoutStatus):
        """Handle timeout callback."""
        self.search_cancelled = True
        print(f"Search timeout: {status.reason.value if status.reason else 'unknown'} "
              f"after {status.elapsed_ms}ms")
    
    def _reset_search_state(self):
        """Reset search state for new search."""
        self.current_best_move = None
        self.current_evaluation = 0
        self.depth_results.clear()
        self.search_cancelled = False
        self.total_nodes = 0
        self.iterations_completed = 0
        self.last_complete_depth = 0
    
    def get_search_info(self) -> Dict[str, Any]:
        """Get current search information for UCI output."""
        stats = self.timeout_manager.get_search_stats()
        
        return {
            'depth': self.last_complete_depth,
            'seldepth': self.last_complete_depth,  # TODO: Implement selective depth
            'nodes': stats['nodes'],
            'nps': stats['nps'],
            'time': stats['elapsed_ms'],
            'score': self.current_evaluation,
            'pv': [move.uci() for move in self._get_principal_variation()],
            'multipv': 1,
            'currmove': self.current_best_move.uci() if self.current_best_move else None,
            'currmovenumber': 1
        }
    
    def _get_principal_variation(self) -> List[chess.Move]:
        """Get principal variation from the deepest complete search."""
        if self.last_complete_depth in self.depth_results:
            return self.depth_results[self.last_complete_depth].pv_line
        return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'iterations_completed': self.iterations_completed,
            'last_complete_depth': self.last_complete_depth,
            'total_nodes': self.total_nodes,
            'depth_results': len(self.depth_results),
            'search_cancelled': self.search_cancelled,
            'average_nodes_per_depth': self.total_nodes / max(1, self.iterations_completed)
        }


# Export main classes
__all__ = [
    'SearchResult',
    'IterativeConfig',
    'IterativeDeepeningSearch'
]


def main():
    """Test the iterative deepening framework."""
    import chess
    
    # Mock search function for testing
    def mock_search(position, depth, alpha, beta, timeout_manager):
        # Simulate search time
        import time
        time.sleep(0.1 * depth)  # Deeper searches take longer
        
        # Check timeout
        status = timeout_manager.check_all_limits(depth, depth * 1000)
        if status.should_stop:
            return None
        
        # Return mock result
        moves = list(position.legal_moves)
        if not moves:
            return None
        
        return SearchResult(
            best_move=moves[0],
            evaluation=depth * 10,  # Mock evaluation
            depth=depth,
            nodes=depth * 1000,
            pv_line=[moves[0]] if moves else []
        )
    
    # Create iterative deepening search
    config = IterativeConfig(min_depth=1, max_depth=6)
    search = IterativeDeepeningSearch(config)
    search.set_search_function(mock_search)
    
    # Create test position
    position = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    # Create time allocation
    from .time_allocation import TimeAllocation, AllocationStrategy
    allocation = TimeAllocation(
        target_time_ms=2000,
        maximum_time_ms=3000,
        minimum_time_ms=500,
        soft_limit_ms=2200,
        hard_limit_ms=2800,
        strategy=AllocationStrategy.ADAPTIVE
    )
    
    print("Iterative Deepening Test:")
    print("=" * 40)
    
    # Perform search
    result = search.search(position, allocation)
    
    print(f"Search completed!")
    print(f"Best move: {result.best_move}")
    print(f"Evaluation: {result.evaluation}")
    print(f"Depth: {result.depth}")
    print(f"Nodes: {result.nodes:,}")
    print(f"Time: {result.time_ms}ms")
    print(f"NPS: {result.nps:,}")
    
    # Print performance stats
    stats = search.get_performance_stats()
    print("\nPerformance Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
