"""
SlowMate Chess Engine v2.1 - Emergency UCI Protocol Fix
Critical fixes to restore tournament stability and UCI compliance
"""

import chess
import time
import threading
import sys
from typing import Optional, Dict, Any, List, Callable


class UCIProtocol:
    """EMERGENCY FIX: Stabilized UCI protocol implementation for v2.1."""

    def __init__(self, engine):
        self.engine = engine
        self.debug = False
        self.name = "SlowMate Chess Engine v2.1-CRITICAL-FIX"
        self.author = "Pat Snyder"
        self.version = "2.1.0"
        self.searching = False
        self.stop_requested = False
        
        # Simplified tracking (remove complex features that caused issues)
        self.nodes_searched = 0
        self.search_start_time = 0
        self.search_thread = None
        
        # Testing support (keep this - it's stable)
        self.search_info_callback: Optional[Callable] = None
        self.move_callback: Optional[Callable] = None
        self.silent_mode = False
        
        # Simplified options (remove complex options that may cause issues)
        self.options = {
            "Hash": {"type": "spin", "default": 64, "min": 1, "max": 512, "value": 64},
            "Debug": {"type": "check", "default": False, "value": False}
        }
        
        if not self.silent_mode:
            self._out("info string SlowMate v2.1 Emergency Stabilization - UCI initialized")

    def _out(self, text: str) -> None:
        """CRITICAL FIX: Robust output with error handling."""
        if not self.silent_mode:
            try:
                print(text, flush=True)
            except Exception:
                # Fail silently if output fails
                pass
            
    def set_silent_mode(self, silent: bool = True) -> None:
        """Set silent mode for testing."""
        self.silent_mode = silent

    def process_command(self, command: str) -> None:
        """CRITICAL FIX: Enhanced command processing with error handling."""
        try:
            command = command.strip()
            if not command:
                return
                
            parts = command.split()
            cmd = parts[0].lower()
            
            # CRITICAL FIX: Handle each command with error recovery
            if cmd == "uci":
                self._handle_uci()
            elif cmd == "isready":
                self._handle_isready()
            elif cmd == "ucinewgame":
                self._handle_ucinewgame()
            elif cmd == "position":
                self._handle_position(parts[1:])
            elif cmd == "go":
                self._handle_go(parts[1:])
            elif cmd == "stop":
                self._handle_stop()
            elif cmd == "quit":
                self._handle_quit()
            elif cmd == "setoption":
                self._handle_setoption(parts[1:])
            else:
                self._out(f"info string Unknown command: {command}")
                
        except Exception as e:
            # CRITICAL FIX: Never crash on command errors
            self._out(f"info string COMMAND_ERROR: {e}")
            
    def _handle_uci(self):
        """CRITICAL FIX: Robust UCI identification."""
        try:
            self._out(f"id name {self.name}")
            self._out(f"id author {self.author}")
            
            # Output options
            for name, option in self.options.items():
                option_str = f"option name {name} type {option['type']}"
                if "default" in option:
                    option_str += f" default {option['default']}"
                if "min" in option:
                    option_str += f" min {option['min']}"
                if "max" in option:
                    option_str += f" max {option['max']}"
                self._out(option_str)
                
            self._out("uciok")
        except Exception as e:
            self._out(f"info string UCI_ERROR: {e}")
            self._out("uciok")  # Always respond to prevent timeout
            
    def _handle_isready(self):
        """CRITICAL FIX: Always respond ready."""
        try:
            # Simple ready check
            self._out("readyok")
        except Exception:
            self._out("readyok")  # Always respond to prevent timeout
            
    def _handle_ucinewgame(self):
        """CRITICAL FIX: Robust new game handling."""
        try:
            self.stop_requested = True  # Stop any ongoing search
            if self.search_thread and self.search_thread.is_alive():
                self.search_thread.join(timeout=1.0)
            
            self.engine.new_game()
            self.searching = False
            self.stop_requested = False
            self._out("info string New game started")
        except Exception as e:
            self._out(f"info string NEWGAME_ERROR: {e}")
            
    def _handle_position(self, args):
        """CRITICAL FIX: Robust position handling."""
        try:
            if not args:
                return
                
            if args[0] == "startpos":
                self.engine.set_position("startpos")
                move_index = 1
            elif args[0] == "fen":
                # Extract FEN (may be multiple parts)
                fen_parts = []
                move_index = 1
                while move_index < len(args) and args[move_index] != "moves":
                    fen_parts.append(args[move_index])
                    move_index += 1
                fen = " ".join(fen_parts)
                self.engine.set_position(fen)
            else:
                self._out("info string Invalid position command")
                return
                
            # Handle moves
            if move_index < len(args) and args[move_index] == "moves":
                for move_str in args[move_index + 1:]:
                    try:
                        move = chess.Move.from_uci(move_str)
                        # CRITICAL FIX: Validate move before making
                        if move in self.engine.board.board.legal_moves:
                            self.engine.make_move(move)
                        else:
                            self._out(f"info string ILLEGAL_MOVE_IN_POSITION: {move_str}")
                    except Exception as e:
                        self._out(f"info string INVALID_MOVE_IN_POSITION: {move_str} - {e}")
                        
        except Exception as e:
            self._out(f"info string POSITION_ERROR: {e}")
            
    def _handle_go(self, args):
        """CRITICAL FIX: Robust search handling with emergency fallbacks."""
        try:
            if self.searching:
                self._out("info string Already searching")
                return
                
            # Parse go command arguments
            params = {}
            i = 0
            while i < len(args):
                if args[i] == "movetime" and i + 1 < len(args):
                    params["time_limit_ms"] = int(args[i + 1])
                    i += 2
                elif args[i] == "wtime" and i + 1 < len(args):
                    params["wtime"] = int(args[i + 1])
                    i += 2
                elif args[i] == "btime" and i + 1 < len(args):
                    params["btime"] = int(args[i + 1])
                    i += 2
                elif args[i] == "depth" and i + 1 < len(args):
                    params["depth_override"] = int(args[i + 1])
                    i += 2
                else:
                    i += 1
                    
            # CRITICAL FIX: Always ensure we have a time limit
            if "time_limit_ms" not in params:
                # Emergency fallback time
                is_white = self.engine.board.board.turn
                if "wtime" in params and is_white:
                    # Use a fraction of remaining time
                    remaining_time = params["wtime"]
                    params["time_limit_ms"] = min(remaining_time // 20, 5000)  # Max 5 seconds
                elif "btime" in params and not is_white:
                    remaining_time = params["btime"]
                    params["time_limit_ms"] = min(remaining_time // 20, 5000)  # Max 5 seconds
                else:
                    params["time_limit_ms"] = 3000  # Default 3 seconds
                    
            # CRITICAL FIX: Start search in thread with timeout protection
            self.searching = True
            self.stop_requested = False
            self.search_start_time = time.time()
            
            def search_wrapper():
                try:
                    # CRITICAL FIX: Always get a move with timeout
                    start_time = time.time()
                    timeout = (params.get("time_limit_ms", 3000) / 1000.0) + 2.0  # Add 2s buffer
                    
                    result = self.engine.search(**params)
                    
                    # EMERGENCY FALLBACK: If no move returned, get any legal move
                    if result is None:
                        legal_moves = list(self.engine.board.board.legal_moves)
                        result = legal_moves[0] if legal_moves else None
                        self._out("info string EMERGENCY_FALLBACK_MOVE")
                        
                    # Check if we took too long
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        self._out(f"info string SEARCH_TIMEOUT: {elapsed:.2f}s > {timeout:.2f}s")
                        
                    if result:
                        self._out(f"bestmove {result.uci()}")
                    else:
                        self._out("bestmove 0000")  # No legal moves (shouldn't happen)
                        
                except Exception as e:
                    self._out(f"info string SEARCH_THREAD_ERROR: {e}")
                    # FINAL EMERGENCY FALLBACK
                    try:
                        legal_moves = list(self.engine.board.board.legal_moves)
                        if legal_moves:
                            self._out(f"bestmove {legal_moves[0].uci()}")
                        else:
                            self._out("bestmove 0000")
                    except:
                        self._out("bestmove 0000")
                finally:
                    self.searching = False
                    
            self.search_thread = threading.Thread(target=search_wrapper, daemon=False)
            self.search_thread.start()
            
        except Exception as e:
            self._out(f"info string GO_ERROR: {e}")
            self.searching = False
            # FINAL EMERGENCY FALLBACK
            try:
                legal_moves = list(self.engine.board.board.legal_moves)
                if legal_moves:
                    self._out(f"bestmove {legal_moves[0].uci()}")
                else:
                    self._out("bestmove 0000")
            except:
                self._out("bestmove 0000")
                
    def _handle_stop(self):
        """CRITICAL FIX: Robust search stopping."""
        try:
            self.stop_requested = True
            if self.search_thread and self.search_thread.is_alive():
                # Wait for search to stop (with timeout)
                self.search_thread.join(timeout=2.0)
                if self.search_thread.is_alive():
                    self._out("info string FORCE_STOP_TIMEOUT")
        except Exception as e:
            self._out(f"info string STOP_ERROR: {e}")
            
    def _handle_quit(self):
        """CRITICAL FIX: Clean shutdown."""
        try:
            self.stop_requested = True
            if self.search_thread and self.search_thread.is_alive():
                self.search_thread.join(timeout=1.0)
        except:
            pass  # Exit gracefully regardless
            
    def _handle_setoption(self, args):
        """CRITICAL FIX: Robust option handling."""
        try:
            if len(args) >= 4 and args[0] == "name" and args[2] == "value":
                option_name = args[1]
                option_value = args[3]
                
                if option_name in self.options:
                    if self.options[option_name]["type"] == "check":
                        self.options[option_name]["value"] = option_value.lower() == "true"
                    elif self.options[option_name]["type"] == "spin":
                        self.options[option_name]["value"] = int(option_value)
                    self._out(f"info string Option {option_name} set to {option_value}")
                else:
                    self._out(f"info string Unknown option: {option_name}")
        except Exception as e:
            self._out(f"info string SETOPTION_ERROR: {e}")
            
    # Testing support methods (keep these - they're stable and useful)
    def run_command(self, command: str) -> Optional[str]:
        """Run a single command for testing."""
        self.process_command(command)
        return None
        
    def run_uci_session(self, commands: list) -> list:
        """Run a series of commands for testing."""
        results = []
        for command in commands:
            self.run_command(command)
            results.append(f"Executed: {command}")
        return results
