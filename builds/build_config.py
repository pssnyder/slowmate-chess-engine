#!/usr/bin/env python3
"""
Build Configuration for SlowMate Chess Engine

Centralized configuration for build process to avoid manual edits.
"""

# =============================================================================
# BUILD CONFIGURATION
# =============================================================================

BUILD_CONFIG = {
    # Version Information
    'version': '0.4.03',
    'variant': 'STABLE_BASELINE',  # BETA, ALPHA, NAGASAKI, etc.
    'engine_name': 'SlowMate Chess Engine - Stable UCI Baseline',
    
    # Build Settings
    'executable_name': 'slowmate_v0.4.03_STABLE_BASELINE',
    'tournament_folder': 'SlowMate_v0.4.03_STABLE_BASELINE_Tournament',
    
    # Features Description
    'features': [
        'Professional UCI Interface',
        'Fixed Depth Search (No Artificial Limits)',
        'Real-Time Info Output',
        'Simplified Intelligence (Bug-Free)',
        'Stable Time Management',
        'Consistent Depth Progression'
    ]
}

def get_build_info():
    """Get formatted build information."""
    config = BUILD_CONFIG
    return {
        'version_string': f"v{config['version']}",
        'full_name': f"SlowMate {config['version']} {config['variant']}",
        'executable_name': f"{config['executable_name']}.exe",
        'tournament_name': config['tournament_folder'],
        'description': config['engine_name'],
        'features': ', '.join(config['features'])
    }

def update_version(version, variant='BETA'):
    """Update build version dynamically."""
    BUILD_CONFIG['version'] = version
    BUILD_CONFIG['variant'] = variant
    BUILD_CONFIG['executable_name'] = f"slowmate_v{version}_{variant}"
    BUILD_CONFIG['tournament_folder'] = f"SlowMate_v{version}_{variant}_Tournament"
