"""SlowMate UCI Entry Point

This script provides the executable entry point for the SlowMate chess engine
implementing the UCI (Universal Chess Interface) protocol. It wires together
engine initialization and a simple stdin/stdout command loop suitable for
PyInstaller packaging.
"""

import sys
from slowmate.engine import SlowMateEngine


def main() -> int:
    engine = SlowMateEngine()
    uci = engine.uci
    print("SlowMate UCI ready. Type 'uci' to begin.")
    try:
        for line in sys.stdin:
            cmd = line.strip()
            if not cmd:
                continue
            uci.process_command(cmd)
            if cmd == 'quit':
                break
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
