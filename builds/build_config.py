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
    'version': '0.4.0',
    'variant': 'RESTORATION_BASE',  # BETA, ALPHA, NAGASAKI, etc.
    'engine_name': 'SlowMate Chess Engine - Baseline Restoration',
    
    # Build Settings
    'executable_name': 'slowmate_v0.4.0_RESTORATION_BASE',
    'tournament_folder': 'SlowMate_v0.4.0_RESTORATION_BASE_Tournament',
    
    # Features Description
    'features': [
        'v0.1.0 Baseline Restored',
        'Tournament-Winning Configuration', 
        'Systematic Restoration Process',
        'Verified Stable Foundation',
        'Ready for Incremental Enhancement'
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
