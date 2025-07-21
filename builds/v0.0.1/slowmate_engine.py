#!/usr/bin/env python3
"""
SlowMate v0.0.1 - Pure Random Chess Engine
The Earliest Stage - Educational Baseline

Features in this version:
- Pure random move selection from legal moves
- Basic UCI protocol implementation
- No search depth, no evaluation, no knowledge
- Perfect baseline for measuring incremental improvements

Usage: python slowmate_engine.py
"""

import sys
import os

# Add the engine directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.uci import main

if __name__ == "__main__":
    print("SlowMate v0.0.1 - Pure Random Engine")
    print("Educational baseline with no strategic knowledge")
    print("Perfect for measuring incremental improvements")
    print("-" * 50)
    main()
