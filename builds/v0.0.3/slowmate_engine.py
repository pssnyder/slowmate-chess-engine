#!/usr/bin/env python3
"""
SlowMate v0.0.3 - Opening Book System Engine
Knowledge Base Integration with Opening Library

Features in this version:
- Complete knowledge base system implementation
- Opening book with mainlines, sidelines, preferences  
- Enhanced move selection with opening knowledge
- Strategic opening play with weighted preferences
- Major leap in opening game performance

Usage: python slowmate_engine.py
"""

import sys
import os

# Add the engine directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.uci import main

if __name__ == "__main__":
    print("SlowMate v0.0.3 - Opening Book System Engine")
    print("Features: Knowledge base + Opening library")
    print("Strategic opening play with weighted preferences")
    print("-" * 50)
    main()
