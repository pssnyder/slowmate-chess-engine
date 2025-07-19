#!/usr/bin/env python3
"""
SlowMate Chess Engine - UCI Executable

This is the main executable for the SlowMate chess engine.
It implements the UCI (Universal Chess Interface) protocol for
compatibility with chess GUIs like Nibbler, Arena, and others.

Usage:
    python slowmate_uci.py

The engine will run in UCI mode, listening for commands on stdin
and responding on stdout according to UCI protocol specifications.
"""

import sys
import os

# Add the slowmate package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.uci import main

if __name__ == "__main__":
    main()
