#!/usr/bin/env python3
"""
SlowMate v0.0.2 - Enhanced Intelligence Engine
Tactical Improvements with Move Intelligence

Features in this version:
- Enhanced move selection with tactical awareness
- Basic position evaluation improvements
- Move intelligence system integration
- Still depth-1 but with smarter move choices
- Significant improvement over pure random

Usage: python slowmate_engine.py
"""

import sys
import os

# Add the engine directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.uci import main

if __name__ == "__main__":
    print("SlowMate v0.0.2 - Enhanced Intelligence Engine")
    print("Features: Tactical awareness + Move intelligence")
    print("Notable improvement over pure random baseline")
    print("-" * 50)
    main()
