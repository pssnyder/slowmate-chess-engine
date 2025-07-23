#!/usr/bin/env python3
"""
SlowMate Chess Engine - UCI Entry Point (v0.1.0 Baseline)

Tournament-winning baseline version.
"""

from slowmate.uci import UCIInterface

def main():
    """Run the UCI interface."""
    uci = UCIInterface()
    uci.run()

if __name__ == "__main__":
    main()
