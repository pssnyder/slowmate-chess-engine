"""
SlowMate Chess Engine v2.2 - Enhanced UCI Protocol
Advanced time management and robust communication
"""

import chess
import threading
import time
import sys
from typing import Optional, Dict, Any

# Import TranspositionTable for hash option
try:
    from slowmate.search.enhanced import TranspositionTable
except ImportError:
    # Fallback if import fails
    class TranspositionTable:
        def __init__(self, size_mb=64):
            self.size_mb = size_mb


class UCIProtocol:
    """Enhanced UCI Protocol implementation for v2.2."""
    
    def __init__(self, engine):
        """Initialize UCI protocol handler."""
        self.engine = engine
        self.stop_requested = False
        self.debug_mode = False
        self.position_set = False
        self.search_thread = None
        
        # v2.2 ENHANCEMENT: UCI options
        self.options = {
            'Hash': {
                'type': 'spin',
                'default': 64,
                'min': 1,
                'max': 1024,
                'value': 64
            },
            'MultiPV': {
                'type': 'spin', 
                'default': 1,
                'min': 1,
                'max': 5,
                'value': 1
            },
            'Ponder': {
                'type': 'check',
                'default': False,
                'value': False
            },
            'OwnBook': {
                'type': 'check',
                'default': False,
                'value': False
            }
        }
        
        # v2.2 ENHANCEMENT: Performance tracking
        self.search_stats = {
            'positions_analyzed': 0,
            'total_search_time': 0.0,
            'average_depth': 0.0,
            'nodes_per_second': 0
        }
    
    def _out(self, message: str):
        """Send message to UCI interface."""
        try:
            print(message, flush=True)
            if self.debug_mode:
                with open('slowmate_uci_debug.log', 'a') as f:
                    f.write(f"OUT: {message}\n")
        except Exception:
            pass  # Fail silently to avoid UCI protocol disruption
    
    def _debug(self, message: str):
        """Send debug message if debug mode is enabled."""
        if self.debug_mode:
            try:
                self._out(f"info string DEBUG: {message}")
                with open('slowmate_uci_debug.log', 'a') as f:
                    f.write(f"DEBUG: {message}\n")
            except Exception:
                pass
    
    def handle_command(self, command: str):
        """Handle incoming UCI command."""
        try:
            if self.debug_mode:
                with open('slowmate_uci_debug.log', 'a') as f:
                    f.write(f"IN: {command}\n")
            
            parts = command.strip().split()
            if not parts:
                return
            
            cmd = parts[0].lower()
            
            if cmd == "uci":
                self._handle_uci()
            elif cmd == "debug":
                self._handle_debug(parts)
            elif cmd == "isready":
                self._handle_isready()
            elif cmd == "setoption":
                self._handle_setoption(parts)
            elif cmd == "register":
                self._handle_register()
            elif cmd == "ucinewgame":
                self._handle_ucinewgame()
            elif cmd == "position":
                self._handle_position(parts)
            elif cmd == "go":
                self._handle_go(parts)
            elif cmd == "stop":
                self._handle_stop()
            elif cmd == "ponderhit":
                self._handle_ponderhit()
            elif cmd == "quit":
                self._handle_quit()
            else:
                self._debug(f"Unknown command: {command}")
                
        except Exception as e:
            self._debug(f"Command handling error: {e}")
            self._out(f"info string COMMAND_ERROR: {e}")
    
    def _handle_uci(self):
        """Handle UCI initialization."""
        self._out("id name SlowMate v3.1")
        self._out("id author SlowMate Team")
        
        # Send options
        for option_name, option_data in self.options.items():
            if option_data['type'] == 'spin':
                self._out(f"option name {option_name} type spin default {option_data['default']} min {option_data['min']} max {option_data['max']}")
            elif option_data['type'] == 'check':
                self._out(f"option name {option_name} type check default {option_data['default']}")
        
        self._out("uciok")
    
    def _handle_debug(self, parts):
        """Handle debug command."""
        if len(parts) > 1:
            self.debug_mode = parts[1].lower() == "on"
            self._debug(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
    
    def _handle_isready(self):
        """Handle isready command."""
        # v2.2 ENHANCEMENT: Verify engine readiness
        try:
            if hasattr(self.engine, 'board') and self.engine.board:
                self._out("readyok")
            else:
                # Initialize if needed
                self.engine.new_game()
                self._out("readyok")
        except Exception as e:
            self._debug(f"Engine readiness check failed: {e}")
            self._out("readyok")  # Still respond to maintain UCI compliance
    
    def _handle_setoption(self, parts):
        """Handle setoption command."""
        try:
            if len(parts) >= 4 and parts[1].lower() == "name":
                option_name = parts[2]
                if len(parts) >= 5 and parts[3].lower() == "value":
                    option_value = " ".join(parts[4:])
                    
                    if option_name in self.options:
                        # v2.2 ENHANCEMENT: Process option changes
                        if option_name == "Hash":
                            hash_size = int(option_value)
                            self.options[option_name]['value'] = hash_size
                            if hasattr(self.engine, 'tt'):
                                self.engine.tt = TranspositionTable(size_mb=hash_size)
                            self._debug(f"Hash size set to {hash_size} MB")
                        
                        elif option_name == "MultiPV":
                            self.options[option_name]['value'] = int(option_value)
                            self._debug(f"MultiPV set to {option_value}")
                        
                        elif option_name in ["Ponder", "OwnBook"]:
                            self.options[option_name]['value'] = option_value.lower() == "true"
                            self._debug(f"{option_name} set to {option_value}")
                        
                        else:
                            self._debug(f"Option {option_name} not implemented")
                    else:
                        self._debug(f"Unknown option: {option_name}")
        except Exception as e:
            self._debug(f"Set option error: {e}")
    
    def _handle_register(self):
        """Handle register command (not needed for free engine)."""
        pass
    
    def _handle_ucinewgame(self):
        """Handle new game command."""
        try:
            self.engine.new_game()
            self.position_set = False
            self.search_stats = {
                'positions_analyzed': 0,
                'total_search_time': 0.0,
                'average_depth': 0.0,
                'nodes_per_second': 0
            }
            self._debug("New game initialized")
        except Exception as e:
            self._debug(f"New game error: {e}")
    
    def _handle_position(self, parts):
        """Handle position command."""
        try:
            if len(parts) < 2:
                return
            
            if parts[1] == "startpos":
                self.engine.set_position("startpos")
                moves_start = 2
            elif parts[1] == "fen":
                # Find where FEN ends and moves begin
                fen_parts = []
                moves_start = 2
                for i in range(2, len(parts)):
                    if parts[i] == "moves":
                        moves_start = i
                        break
                    fen_parts.append(parts[i])
                
                if fen_parts:
                    fen = " ".join(fen_parts)
                    self.engine.set_position(fen)
                else:
                    self._debug("Invalid FEN in position command")
                    return
            else:
                self._debug(f"Invalid position command: {' '.join(parts)}")
                return
            
            # Apply moves if present
            if moves_start < len(parts) and parts[moves_start] == "moves":
                for move_str in parts[moves_start + 1:]:
                    try:
                        move = chess.Move.from_uci(move_str)
                        if move in self.engine.board.board.legal_moves:
                            self.engine.make_move(move)
                        else:
                            self._debug(f"Illegal move: {move_str}")
                            break
                    except Exception as e:
                        self._debug(f"Move parsing error: {move_str} - {e}")
                        break
            
            self.position_set = True
            self._debug(f"Position set: {self.engine.board.get_fen()}")
            
        except Exception as e:
            self._debug(f"Position command error: {e}")
    
    def _handle_go(self, parts):
        """Handle go command with enhanced time management."""
        if not self.position_set:
            self._debug("No position set, cannot search")
            return
        
        # Stop any ongoing search
        self._handle_stop()
        
        try:
            # Parse search parameters
            search_params = self._parse_go_command(parts)
            self._debug(f"Search parameters: {search_params}")
            
            # Start search in separate thread
            self.stop_requested = False
            self.search_thread = threading.Thread(
                target=self._search_thread,
                args=(search_params,),
                daemon=True
            )
            self.search_thread.start()
            
        except Exception as e:
            self._debug(f"Go command error: {e}")
            self._out("bestmove 0000")  # Emergency fallback
    
    def _parse_go_command(self, parts) -> Dict[str, Any]:
        """v2.2 ENHANCEMENT: Parse go command parameters."""
        params = {}
        i = 1
        
        while i < len(parts):
            param = parts[i].lower()
            
            if param in ["wtime", "btime", "winc", "binc", "movestogo"]:
                if i + 1 < len(parts):
                    try:
                        params[param] = int(parts[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif param == "movetime":
                if i + 1 < len(parts):
                    try:
                        params["movetime"] = int(parts[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif param == "depth":
                if i + 1 < len(parts):
                    try:
                        params["depth"] = int(parts[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif param == "nodes":
                if i + 1 < len(parts):
                    try:
                        params["nodes"] = int(parts[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif param == "infinite":
                params["infinite"] = True
                i += 1
            elif param == "ponder":
                params["ponder"] = True
                i += 1
            else:
                i += 1
        
        return params
    
    def _search_thread(self, search_params: Dict[str, Any]):
        """Enhanced search thread with better error handling."""
        try:
            start_time = time.time()
            
            # Calculate time allocation
            time_limit = None
            depth_limit = None
            
            if "movetime" in search_params:
                time_limit = search_params["movetime"]
            elif "depth" in search_params:
                depth_limit = search_params["depth"]
            elif not search_params.get("infinite", False):
                # Calculate time from time control
                time_limit = self._calculate_time_limit(search_params)
            
            # Perform search
            best_move = self.engine.search(
                time_limit_ms=time_limit,
                depth_override=depth_limit,
                **search_params
            )
            
            # Calculate search statistics
            elapsed_time = time.time() - start_time
            self.search_stats['positions_analyzed'] += 1
            self.search_stats['total_search_time'] += elapsed_time
            
            if hasattr(self.engine, 'nodes'):
                self.search_stats['nodes_per_second'] = int(self.engine.nodes / max(elapsed_time, 0.001))
            
            # Send best move
            if best_move and not self.stop_requested:
                self._out(f"bestmove {best_move.uci()}")
                self._debug(f"Search completed: {best_move.uci()} in {elapsed_time:.3f}s, {self.engine.nodes} nodes")
            else:
                # Emergency fallback
                legal_moves = list(self.engine.board.board.legal_moves)
                if legal_moves:
                    fallback_move = legal_moves[0]
                    self._out(f"bestmove {fallback_move.uci()}")
                    self._debug(f"Emergency fallback move: {fallback_move.uci()}")
                else:
                    self._out("bestmove 0000")
                    self._debug("No legal moves available")
            
        except Exception as e:
            self._debug(f"Search thread error: {e}")
            try:
                # Ultimate fallback
                legal_moves = list(self.engine.board.board.legal_moves)
                if legal_moves:
                    self._out(f"bestmove {legal_moves[0].uci()}")
                else:
                    self._out("bestmove 0000")
            except:
                self._out("bestmove 0000")
    
    def _calculate_time_limit(self, search_params: Dict[str, Any]) -> Optional[int]:
        """v2.2 ENHANCEMENT: Advanced time limit calculation."""
        is_white = self.engine.board.board.turn == chess.WHITE
        
        our_time = search_params.get('wtime' if is_white else 'btime', 0)
        our_increment = search_params.get('winc' if is_white else 'binc', 0)
        moves_to_go = search_params.get('movestogo', 40)
        
        if our_time <= 0:
            return None
        
        # Basic time allocation: divide remaining time by expected moves
        base_allocation = our_time / (moves_to_go + 5)  # Conservative
        
        # Add most of the increment
        base_allocation += our_increment * 0.8
        
        # Position complexity adjustment (if available)
        if hasattr(self.engine, 'position_complexity'):
            complexity_factor = 1.0
            if self.engine.critical_position:
                complexity_factor = 1.5
            elif self.engine.position_complexity > 40:
                complexity_factor = 1.2
            elif self.engine.position_complexity < 20:
                complexity_factor = 0.8
            
            base_allocation *= complexity_factor
        
        # Safety limits
        max_time = our_time * 0.1  # Never use more than 10%
        min_time = max(100, our_time * 0.01)  # At least 100ms or 1%
        
        allocated_time = max(min_time, min(base_allocation, max_time))
        
        return int(allocated_time)
    
    def _handle_stop(self):
        """Handle stop command."""
        self.stop_requested = True
        
        # Wait for search thread to finish
        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.join(timeout=1.0)
        
        self._debug("Search stopped")
    
    def _handle_ponderhit(self):
        """Handle ponderhit command."""
        # Convert ponder search to normal search
        # For now, just continue the current search
        self._debug("Ponder hit - converting to normal search")
    
    def _handle_quit(self):
        """Handle quit command."""
        self._handle_stop()
        self._debug("Engine shutting down")
        try:
            sys.exit(0)
        except:
            pass
    
    def run(self):
        """Main UCI loop."""
        self._debug("SlowMate v2.2 UCI interface started")
        
        try:
            while True:
                try:
                    line = input().strip()
                    if line:
                        self.handle_command(line)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._debug(f"Input error: {e}")
        except Exception as e:
            self._debug(f"UCI loop error: {e}")
        finally:
            self._debug("UCI interface shutting down")
