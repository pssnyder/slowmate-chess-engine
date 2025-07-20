#!/usr/bin/env python3
"""
SlowMate v0.1.03 Beta - Chess Engine Executable
Enhanced with Endgame Pattern Recognition System

Features in this version:
- Knowledge-based move selection (Opening Book + Endgame Patterns)
- Comprehensive endgame pattern recognition for KQ vs K, KR vs K, KRR vs K
- Strategic endgame conversion (material advantage → checkmate)
- Tournament-tested performance with Arena compatibility
- JSON-based pattern libraries for mates, pawn endings, tactical setups

Usage: python slowmate_engine.py
"""

import sys
import os

# Add the engine directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.uci import main

if __name__ == "__main__":
    print("SlowMate v0.1.03 Beta - Endgame Pattern Enhanced")
    print("Features: Opening Book + Endgame Patterns + Strategic Conversion")
    print("Compatible with Arena and UCI protocol")
    print("-" * 60)
    main()
