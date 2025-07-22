"""
Time Control Parser for SlowMate v0.2.02 Phase 1
Handles parsing and understanding of various time control formats.
"""

import re
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class TimeControlType(Enum):
    """Types of time controls supported."""
    CLASSICAL = "classical"
    RAPID = "rapid"
    BLITZ = "blitz"
    BULLET = "bullet"
    FIXED_DEPTH = "fixed_depth"
    FIXED_NODES = "fixed_nodes"
    INFINITE = "infinite"


@dataclass
class TimeControl:
    """Represents a parsed time control configuration."""
    control_type: TimeControlType
    base_time_ms: int = 0          # Base time in milliseconds
    increment_ms: int = 0          # Increment per move in milliseconds
    moves_to_go: Optional[int] = None  # Moves until time control repeats (e.g., 40/90)
    depth_limit: Optional[int] = None  # Fixed depth limit
    nodes_limit: Optional[int] = None  # Fixed nodes limit
    
    # Additional parameters
    movestogo: Optional[int] = None    # Moves to reach next time control
    wtime: Optional[int] = None        # White time remaining (ms)
    btime: Optional[int] = None        # Black time remaining (ms)
    winc: Optional[int] = None         # White increment (ms)
    binc: Optional[int] = None         # Black increment (ms)
    
    def __post_init__(self):
        """Validate and normalize time control parameters."""
        if self.base_time_ms < 0:
            self.base_time_ms = 0
        if self.increment_ms < 0:
            self.increment_ms = 0
    
    @property
    def is_time_limited(self) -> bool:
        """Check if this time control has time limits."""
        return self.control_type not in [TimeControlType.INFINITE, TimeControlType.FIXED_DEPTH, TimeControlType.FIXED_NODES]
    
    @property
    def is_increment_game(self) -> bool:
        """Check if this time control has increments."""
        return self.increment_ms > 0
    
    @property
    def total_estimated_time_ms(self) -> Union[int, float]:
        """Estimate total game time in milliseconds."""
        if not self.is_time_limited:
            return float('inf')
        
        # Base time + estimated increments for ~40 moves
        estimated_moves = 40
        return self.base_time_ms + (self.increment_ms * estimated_moves)


class TimeControlParser:
    """Parser for various time control formats."""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for different time control formats."""
        return {
            # Classical: 40/90+30, 40/5400+30
            'classical': re.compile(r'^(\d+)/(\d+)(?:\+(\d+))?$'),
            
            # Rapid/Blitz: 15+10, 180+2, 3+2, 1+0
            'increment': re.compile(r'^(\d+)(?:\.(\d+))?\+(\d+)$'),
            
            # Fixed time: 15, 180, 300 (seconds)
            'fixed_time': re.compile(r'^(\d+)(?:\.(\d+))?$'),
            
            # Fixed depth: depth 6, d6
            'depth': re.compile(r'^(?:depth\s+|d)(\d+)$', re.IGNORECASE),
            
            # Fixed nodes: nodes 1000000, n1000000
            'nodes': re.compile(r'^(?:nodes\s+|n)(\d+)$', re.IGNORECASE),
            
            # Infinite: infinite, inf
            'infinite': re.compile(r'^(?:infinite|inf)$', re.IGNORECASE)
        }
    
    def parse(self, time_control_str: str) -> Optional[TimeControl]:
        """
        Parse a time control string into a TimeControl object.
        
        Args:
            time_control_str: Time control string (e.g., "15+10", "40/90+30", "depth 6")
        
        Returns:
            TimeControl object or None if parsing fails
        """
        if not time_control_str:
            return None
        
        time_control_str = time_control_str.strip()
        
        # Try classical format (40/90+30)
        match = self.patterns['classical'].match(time_control_str)
        if match:
            moves = int(match.group(1))
            base_time_seconds = int(match.group(2))
            increment_seconds = int(match.group(3)) if match.group(3) else 0
            
            return TimeControl(
                control_type=TimeControlType.CLASSICAL,
                base_time_ms=base_time_seconds * 1000,
                increment_ms=increment_seconds * 1000,
                moves_to_go=moves
            )
        
        # Try increment format (15+10, 3+2)
        match = self.patterns['increment'].match(time_control_str)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            increment_seconds = int(match.group(3))
            
            base_time_ms = (minutes * 60 + seconds) * 1000
            increment_ms = increment_seconds * 1000
            
            # Classify based on time
            if base_time_ms >= 15 * 60 * 1000:  # 15+ minutes
                control_type = TimeControlType.RAPID
            elif base_time_ms >= 3 * 60 * 1000:  # 3+ minutes
                control_type = TimeControlType.BLITZ
            else:  # < 3 minutes
                control_type = TimeControlType.BULLET
            
            return TimeControl(
                control_type=control_type,
                base_time_ms=base_time_ms,
                increment_ms=increment_ms
            )
        
        # Try fixed time format (15, 180)
        match = self.patterns['fixed_time'].match(time_control_str)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            
            base_time_ms = (minutes * 60 + seconds) * 1000
            
            # Classify based on time
            if base_time_ms >= 15 * 60 * 1000:  # 15+ minutes
                control_type = TimeControlType.RAPID
            elif base_time_ms >= 3 * 60 * 1000:  # 3+ minutes
                control_type = TimeControlType.BLITZ
            else:  # < 3 minutes
                control_type = TimeControlType.BULLET
            
            return TimeControl(
                control_type=control_type,
                base_time_ms=base_time_ms,
                increment_ms=0
            )
        
        # Try fixed depth (depth 6)
        match = self.patterns['depth'].match(time_control_str)
        if match:
            depth = int(match.group(1))
            return TimeControl(
                control_type=TimeControlType.FIXED_DEPTH,
                depth_limit=depth
            )
        
        # Try fixed nodes (nodes 1000000)
        match = self.patterns['nodes'].match(time_control_str)
        if match:
            nodes = int(match.group(1))
            return TimeControl(
                control_type=TimeControlType.FIXED_NODES,
                nodes_limit=nodes
            )
        
        # Try infinite
        match = self.patterns['infinite'].match(time_control_str)
        if match:
            return TimeControl(
                control_type=TimeControlType.INFINITE
            )
        
        return None
    
    def parse_uci_go_command(self, params: Dict[str, Any]) -> TimeControl:
        """
        Parse UCI 'go' command parameters into a TimeControl object.
        
        Args:
            params: Dictionary of UCI go command parameters
        
        Returns:
            TimeControl object representing the search constraints
        """
        # Fixed depth
        if 'depth' in params:
            return TimeControl(
                control_type=TimeControlType.FIXED_DEPTH,
                depth_limit=int(params['depth'])
            )
        
        # Fixed nodes
        if 'nodes' in params:
            return TimeControl(
                control_type=TimeControlType.FIXED_NODES,
                nodes_limit=int(params['nodes'])
            )
        
        # Infinite search
        if 'infinite' in params:
            return TimeControl(
                control_type=TimeControlType.INFINITE
            )
        
        # Time-based search
        wtime = params.get('wtime', 0)
        btime = params.get('btime', 0)
        winc = params.get('winc', 0)
        binc = params.get('binc', 0)
        movestogo = params.get('movestogo')
        
        # Determine control type based on available time
        total_time = max(wtime, btime)
        if total_time >= 15 * 60 * 1000:  # 15+ minutes
            control_type = TimeControlType.RAPID
        elif total_time >= 3 * 60 * 1000:  # 3+ minutes
            control_type = TimeControlType.BLITZ
        elif total_time >= 1 * 60 * 1000:  # 1+ minute
            control_type = TimeControlType.BULLET
        else:
            control_type = TimeControlType.BULLET  # Ultra-bullet/emergency
        
        return TimeControl(
            control_type=control_type,
            wtime=wtime,
            btime=btime,
            winc=winc,
            binc=binc,
            movestogo=movestogo
        )
    
    def get_time_classification(self, time_control: TimeControl) -> str:
        """Get a human-readable classification of the time control."""
        if time_control.control_type == TimeControlType.CLASSICAL:
            base_minutes = time_control.base_time_ms//1000//60
            return f"Classical ({time_control.moves_to_go}/{base_minutes}+{time_control.increment_ms//1000})"
        elif time_control.control_type == TimeControlType.RAPID:
            return f"Rapid ({time_control.base_time_ms//1000//60}+{time_control.increment_ms//1000})"
        elif time_control.control_type == TimeControlType.BLITZ:
            return f"Blitz ({time_control.base_time_ms//1000//60}+{time_control.increment_ms//1000})"
        elif time_control.control_type == TimeControlType.BULLET:
            return f"Bullet ({time_control.base_time_ms//1000//60}+{time_control.increment_ms//1000})"
        elif time_control.control_type == TimeControlType.FIXED_DEPTH:
            return f"Fixed Depth ({time_control.depth_limit})"
        elif time_control.control_type == TimeControlType.FIXED_NODES:
            return f"Fixed Nodes ({time_control.nodes_limit:,})"
        elif time_control.control_type == TimeControlType.INFINITE:
            return "Infinite Analysis"
        else:
            return "Unknown"


# Export main classes
__all__ = [
    'TimeControlType',
    'TimeControl',
    'TimeControlParser'
]


def main():
    """Test the time control parser with various formats."""
    parser = TimeControlParser()
    
    test_cases = [
        "40/90+30",    # Classical
        "15+10",       # Rapid
        "3+2",         # Blitz
        "1+0",         # Bullet
        "180",         # Fixed 3 minutes
        "depth 6",     # Fixed depth
        "nodes 1000000",  # Fixed nodes
        "infinite",    # Infinite
        "invalid"      # Should fail
    ]
    
    print("Time Control Parser Test Results:")
    print("=" * 50)
    
    for test_case in test_cases:
        result = parser.parse(test_case)
        if result:
            classification = parser.get_time_classification(result)
            print(f"'{test_case}' -> {classification}")
            print(f"  Type: {result.control_type.value}")
            if result.is_time_limited:
                print(f"  Base: {result.base_time_ms//1000//60}m {(result.base_time_ms//1000)%60}s")
                print(f"  Increment: {result.increment_ms//1000}s")
            print()
        else:
            print(f"'{test_case}' -> FAILED TO PARSE")
            print()


if __name__ == "__main__":
    main()
