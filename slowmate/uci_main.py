#!/usr/bin/env python3
"""
SlowMate Chess Engine - UCI Main Entry Point
This module provides the main entry point for UCI communication.
Can be used as a standalone script or imported for testing.
"""

import sys
import os
import signal
from typing import Optional

# Add the parent directory to the path to import slowmate modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.engine import SlowMateEngine
from slowmate.uci.protocol import UCIProtocol


class UCIMain:
    """Main UCI interface for SlowMate Chess Engine."""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the UCI main interface."""
        self.debug_mode = debug_mode
        self.engine = None
        self.uci = None
        self.running = True
        
    def initialize_engine(self) -> bool:
        """Initialize the chess engine and UCI protocol."""
        try:
            self.engine = SlowMateEngine()
            self.uci = UCIProtocol(self.engine)
            self.uci.debug = self.debug_mode
            return True
        except Exception as e:
            print(f"info string Engine initialization failed: {e}", flush=True)
            return False
            
    def run_uci_loop(self) -> None:
        """Run the main UCI command loop."""
        if not self.initialize_engine():
            return
            
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                try:
                    command = input().strip()
                    if not command:
                        continue
                        
                    if command == "quit":
                        self.running = False
                        break
                        
                    if self.uci:
                        self.uci.process_command(command)
                    
                except EOFError:
                    # End of input stream
                    break
                except KeyboardInterrupt:
                    # Ctrl+C pressed
                    break
                except Exception as e:
                    if self.debug_mode:
                        print(f"info string Command error: {e}", flush=True)
                        
        except Exception as e:
            if self.debug_mode:
                print(f"info string UCI loop error: {e}", flush=True)
        finally:
            self._cleanup()
            
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.running = False
        if self.uci and self.uci.searching:
            self.uci.stop_requested = True
            
    def _cleanup(self):
        """Clean up resources before exit."""
        if self.uci and self.uci.searching:
            self.uci.stop_requested = True
            # Wait for search thread to finish
            if hasattr(self.uci, 'search_thread') and self.uci.search_thread:
                self.uci.search_thread.join(timeout=1.0)
            
    def test_uci_command(self, command: str) -> Optional[str]:
        """Test a single UCI command (useful for testing)."""
        if not self.uci:
            if not self.initialize_engine():
                return None
        if self.uci:
            return self.uci.run_command(command)
        return None
        
    def test_uci_session(self, commands: list) -> list:
        """Test a series of UCI commands (useful for testing)."""
        if not self.uci:
            if not self.initialize_engine():
                return []
        if self.uci:
            return self.uci.run_uci_session(commands)
        return []


def main():
    """Main entry point for the UCI interface."""
    debug_mode = False
    
    # Check for debug flag
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        debug_mode = True
        
    uci_main = UCIMain(debug_mode=debug_mode)
    uci_main.run_uci_loop()


if __name__ == "__main__":
    main()
