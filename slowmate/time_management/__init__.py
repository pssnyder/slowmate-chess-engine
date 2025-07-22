"""
SlowMate Time Management System
Complete time control and search optimization for chess engine v0.2.02
"""

# Phase 1: Core Time Management
from .time_control import (
    TimeControl,
    TimeControlType,
    TimeControlParser
)

from .time_allocation import (
    TimeAllocation,
    AllocationStrategy,
    TimeAllocator
)

from .search_timeout import (
    SearchTimeoutManager,
    TimeoutReason,
    TimeoutStatus,
    SearchTimer,
    TimeoutDecorator
)

from .time_tracking import (
    TimeTracker,
    MoveTimeRecord,
    GameTimeStats,
    RealTimeMonitor
)

# Phase 2: Iterative Deepening and Search Control
from .iterative_deepening import (
    IterativeDeepeningSearch,
    SearchResult,
    IterativeConfig
)

from .aspiration_windows import (
    AspirationWindowManager,
    AspirationResult,
    AspirationWindow,
    AspirationConfig
)

from .search_controller import (
    SearchController,
    SearchMode,
    SearchConfig
)

# Phase 3: Advanced Time Features
from .dynamic_allocation import (
    DynamicTimeAllocator,
    PositionAnalyzer,
    PositionAnalysis,
    PositionType,
    GameContext
)

from .emergency_mode import (
    EmergencyTimeManager,
    EmergencyLevel,
    EmergencyStrategy,
    EmergencyState,
    EmergencySettings,
    EmergencyMoveBook
)

from .search_extensions import (
    SearchExtensionManager,
    ExtensionType,
    ExtensionConfig,
    ExtensionAnalysis
)

from .move_overhead import (
    MoveOverheadManager,
    OverheadType,
    OverheadMeasurement,
    OverheadSettings
)

# Version information
__version__ = "0.2.02"
__phase__ = "Phase 3 - Advanced Time Features Complete"

# All available exports
__all__ = [
    # Phase 1: Core Time Management
    'TimeControl',
    'TimeControlType', 
    'TimeControlParser',
    'TimeAllocation',
    'AllocationStrategy',
    'TimeAllocator',
    'SearchTimeoutManager',
    'TimeoutReason',
    'TimeoutStatus',
    'SearchTimer',
    'TimeoutDecorator',
    'TimeTracker',
    'MoveTimeRecord', 
    'GameTimeStats',
    'RealTimeMonitor',
    
    # Phase 2: Iterative Deepening and Search Control
    'IterativeDeepeningSearch',
    'SearchResult',
    'IterativeConfig',
    'AspirationWindowManager',
    'AspirationResult',
    'AspirationWindow',
    'AspirationConfig',
    'SearchController',
    'SearchMode',
    'SearchConfig',
    
    # Phase 3: Advanced Time Features  
    'DynamicTimeAllocator',
    'PositionAnalyzer',
    'PositionAnalysis',
    'PositionType',
    'GameContext',
    'EmergencyTimeManager', 
    'EmergencyLevel',
    'EmergencyStrategy',
    'EmergencyState',
    'EmergencySettings',
    'EmergencyMoveBook',
    'SearchExtensionManager',
    'ExtensionType',
    'ExtensionConfig', 
    'ExtensionAnalysis',
    'MoveOverheadManager',
    'OverheadType',
    'OverheadMeasurement',
    'OverheadSettings',
    
    # Module metadata
    '__version__',
    '__phase__'
]


def get_time_management_info() -> dict:
    """Get information about the time management system."""
    return {
        "version": __version__,
        "phase": __phase__,
        "components": {
            "phase_1": [
                "Time Control Parsing",
                "Basic Time Allocation", 
                "Search Timeout Management",
                "Time Usage Tracking"
            ],
            "phase_2": [
                "Iterative Deepening",
                "Aspiration Windows",
                "Unified Search Controller"
            ],
            "phase_3": [
                "Dynamic Time Allocation",
                "Emergency Time Management",
                "Search Extensions",
                "Move Overhead Compensation"
            ]
        },
        "features": [
            "Complete UCI time control support",
            "Adaptive time allocation strategies", 
            "Real-time timeout enforcement",
            "Performance analytics and learning",
            "Position-aware time budgeting",
            "Emergency time handling",
            "Selective search extensions",
            "Network/system overhead compensation"
        ]
    }


# Create convenience function for basic setup
def create_time_manager():
    """Create a basic time management setup with sensible defaults."""
    from .time_control import TimeControlParser
    from .time_allocation import TimeAllocator
    from .time_tracking import TimeTracker
    from .search_controller import SearchController
    
    parser = TimeControlParser()
    allocator = TimeAllocator()
    tracker = TimeTracker()
    controller = SearchController()
    
    return {
        "parser": parser,
        "allocator": allocator, 
        "tracker": tracker,
        "controller": controller
    }


# Create advanced time management setup
def create_advanced_time_manager():
    """Create an advanced time management setup with all Phase 3 features."""
    basic_manager = create_time_manager()
    
    # Add Phase 3 components
    dynamic_allocator = DynamicTimeAllocator(basic_manager["allocator"])
    emergency_manager = EmergencyTimeManager()
    extension_manager = SearchExtensionManager()
    overhead_manager = MoveOverheadManager()
    
    return {
        **basic_manager,
        "dynamic_allocator": dynamic_allocator,
        "emergency_manager": emergency_manager,
        "extension_manager": extension_manager,
        "overhead_manager": overhead_manager
    }


if __name__ == "__main__":
    # Display time management system information only in interactive mode
    import sys
    
    if hasattr(sys, 'ps1') or '--info' in sys.argv:
        info = get_time_management_info()
        print("SlowMate Time Management System")
        print("=" * 40)
        print(f"Version: {info['version']}")
        print(f"Current Phase: {info['phase']}")
        print()
        
        print("Components by Phase:")
        for phase, components in info['components'].items():
            print(f"  {phase.replace('_', ' ').title()}:")
            for component in components:
                print(f"    - {component}")
            print()
        
        print("Key Features:")
        for feature in info['features']:
            print(f"  - {feature}")
        
        print(f"\nTotal exported symbols: {len(__all__)}")
        print("Time Management System ready for integration!")
