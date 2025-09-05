"""SlowMate Chess Engine - Enhanced UCI Protocol Module."""

import chess
import time
import threading
import sys
from typing import Optional, Dict, Any, List, Callable


class UCIProtocol:
    """Enhanced UCI protocol implementation with comprehensive search output and testing support."""

    def __init__(self, engine):
        self.engine = engine
        self.debug = False
        self.name = "SlowMate Chess Engine"
        self.author = "Github Copilot"
        self.version = "1.0.0"
        self.searching = False
        self.stop_requested = False
        
        # Enhanced search tracking
        self.nodes_searched = 0
        self.current_depth = 0
        self.current_score = 0
        self.search_start_time = 0
        self.current_pv = []
        self.search_thread = None
        
        # Testing and callback support
        self.search_info_callback: Optional[Callable] = None
        self.move_callback: Optional[Callable] = None
        self.silent_mode = False  # For testing without output
        
        # Options
        self.options = {
            "Hash": {"type": "spin", "default": 64, "min": 1, "max": 1024, "value": 64},
            "Debug": {"type": "check", "default": False, "value": False},
            "Threads": {"type": "spin", "default": 1, "min": 1, "max": 16, "value": 1},
            "MultiPV": {"type": "spin", "default": 1, "min": 1, "max": 10, "value": 1}
        }
        
        if not self.silent_mode:
            self._out("info string SlowMate UCI initialized")

    def _out(self, text: str) -> None:
        """Output text with proper flushing, respecting silent mode."""
        if not self.silent_mode:
            print(text, flush=True)
            
    def set_silent_mode(self, silent: bool = True) -> None:
        """Enable/disable silent mode for testing."""
        self.silent_mode = silent
        
    def set_search_info_callback(self, callback: Optional[Callable] = None) -> None:
        """Set callback for search information (useful for testing)."""
        self.search_info_callback = callback
        
    def set_move_callback(self, callback: Optional[Callable] = None) -> None:
        """Set callback for best move (useful for testing)."""
        self.move_callback = callback

    def _format_score(self, score: int) -> tuple[str, str]:
        """Format evaluation score according to UCI protocol."""
        if abs(score) >= 29000:  # Mate score threshold
            # Calculate mate score:
            # - A mate in N should return "score mate N"
            # - Being mated in N should return "score mate -N"
            mate_in = -((30000 - abs(score) + 1) // 2)
            if score > 0:
                mate_in = -mate_in
            score_type = "mate"
            score_value = str(mate_in)
        else:
            score_type = "cp"
            score_value = str(score)
        return score_type, score_value
        
    def _send_search_info(self, info: Dict[str, Any]) -> None:
        """Send search information in UCI format."""
        info_parts = ["info"]
        
        if "depth" in info:
            info_parts.extend(["depth", str(info["depth"])])
            self.current_depth = info["depth"]
        
        if "score" in info:
            score = info["score"]
            score_type, score_value = self._format_score(score)
            info_parts.extend(["score", score_type, score_value])
            self.current_score = score
        
        if "time" in info:
            info_parts.extend(["time", str(info["time"])])
            
        if "nodes" in info:
            info_parts.extend(["nodes", str(info["nodes"])])
            self.nodes_searched = info["nodes"]
            
            # Calculate nodes per second
            if self.search_start_time > 0:
                elapsed = max(1, (time.time() - self.search_start_time) * 1000)
                nps = int(self.nodes_searched * 1000 / elapsed)
                info_parts.extend(["nps", str(nps)])
        
        if "pv" in info and info["pv"]:
            pv_moves = [move.uci() if hasattr(move, 'uci') else str(move) for move in info["pv"]]
            info_parts.extend(["pv"] + pv_moves)
            self.current_pv = pv_moves
            
        if self.debug and "string" in info:
            info_parts.extend(["string", str(info["string"])])
            
        output = " ".join(info_parts)
        self._out(output)
        
        # Call callback if set (for testing)
        if self.search_info_callback:
            self.search_info_callback(info)
            
    def send_search_info(self, depth: int, score: int, pv: List[chess.Move],
                        nodes: int = 0, time_ms: float = 0, debug_info: Optional[str] = None) -> None:
        """Public method to send search information."""
        info = {
            "depth": depth,
            "score": score,
            "pv": pv,
            "nodes": nodes,
            "time": int(time_ms)
        }
        if debug_info and self.debug:
            info["string"] = debug_info
            
        self._send_search_info(info)
        
    def send_bestmove(self, move: Optional[chess.Move], ponder: Optional[chess.Move] = None) -> None:
        """Send best move in UCI format."""
        if move:
            output = f"bestmove {move.uci()}"
            if ponder:
                output += f" ponder {ponder.uci()}"
        else:
            output = "bestmove (none)"
            
        self._out(output)
        
        # Call callback if set (for testing)
        if self.move_callback:
            self.move_callback(move, ponder)

    def process_command(self, command: str) -> None:
        tokens = command.split()
        if not tokens:
            return
        handlers = {
            "uci": self._handle_uci,
            "debug": self._handle_debug,
            "isready": self._handle_isready,
            "setoption": self._handle_setoption,
            "ucinewgame": self._handle_ucinewgame,
            "position": self._handle_position,
            "go": self._handle_go,
            "stop": self._handle_stop,
            "quit": self._handle_quit,
        }
        h = handlers.get(tokens[0])
        if h:
            h(tokens[1:])

    def _handle_uci(self, args):
        """Handle UCI identification command."""
        self._out(f"id name {self.name} v{self.version}")
        self._out(f"id author {self.author}")
        
        # Send all available options
        for option_name, option_data in self.options.items():
            option_str = f"option name {option_name} type {option_data['type']}"
            if option_data['type'] == 'spin':
                option_str += f" default {option_data['default']} min {option_data['min']} max {option_data['max']}"
            elif option_data['type'] == 'check':
                option_str += f" default {str(option_data['default']).lower()}"
            self._out(option_str)
            
        self._out("uciok")

    def _handle_debug(self, args):
        self.debug = bool(args and args[0] == "on")

    def _handle_isready(self, args):
        self._out("readyok")

    def _handle_setoption(self, args):
        """Handle setoption command with comprehensive option support."""
        if len(args) >= 4 and args[0] == "name" and args[2] == "value":
            option_name = args[1]
            option_value = args[3]
            
            if option_name in self.options:
                option_data = self.options[option_name]
                
                if option_data['type'] == 'check':
                    self.options[option_name]['value'] = (option_value.lower() == "true")
                    if option_name == "Debug":
                        self.debug = self.options[option_name]['value']
                elif option_data['type'] == 'spin':
                    try:
                        value = int(option_value)
                        if option_data['min'] <= value <= option_data['max']:
                            self.options[option_name]['value'] = value
                            # Apply specific option changes
                            if option_name == "Hash":
                                # Could adjust engine hash table size here
                                if self.debug:
                                    self._out(f"info string Hash size set to {value} MB")
                    except ValueError:
                        if self.debug:
                            self._out(f"info string Invalid value for {option_name}: {option_value}")
                            
                if self.debug:
                    self._out(f"info string Set {option_name} = {self.options[option_name]['value']}")

    def _handle_ucinewgame(self, args):
        self.engine.new_game()

    def _handle_position(self, args):
        if not args:
            return
        if args[0] == "startpos":
            self.engine.set_position("startpos")
            move_index = 1
        elif args[0] == "fen" and len(args) >= 7:
            fen = " ".join(args[1:7])
            self.engine.set_position(fen)
            move_index = 7
        else:
            return
        if len(args) > move_index and args[move_index] == "moves":
            for mv in args[move_index + 1:]:
                self.engine.make_move(chess.Move.from_uci(mv))

    def _handle_go(self, args):
        """Handle the 'go' command with enhanced time management and search info."""
        params = {}
        i = 0
        while i < len(args):
            if args[i] in ["wtime", "btime", "winc", "binc", "movestogo", "movetime", "depth", "nodes", "infinite"]:
                if args[i] == "infinite":
                    params[args[i]] = True
                    i += 1
                elif i + 1 < len(args):
                    try:
                        params[args[i]] = int(args[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
            
        self.searching = True
        self.stop_requested = False
        self.search_start_time = time.time()
        self.nodes_searched = 0
        self.current_depth = 0
        
        # Start search in a separate thread
        self.search_thread = threading.Thread(
            target=self._search_and_respond,
            args=(params,),
            daemon=False  # Non-daemon thread for proper cleanup
        )
        self.search_thread.start()

    def _handle_stop(self, args):
        if self.searching:
            self.stop_requested = True

    def _handle_quit(self, args):
        self.stop_requested = True

    def _search_and_respond(self, params: dict) -> None:
        """Execute search with enhanced information output and respond with best move."""
        try:
            best_move = None
            search_info = {}
            
            try:
                # Send initial search info
                if self.debug:
                    self._send_search_info({"string": f"Starting search with params: {params}"})
                
                # Handle different types of time controls
                if "movetime" in params:
                    # Fixed time per move
                    best_move = self.engine.search(time_limit_ms=params["movetime"])
                elif "infinite" in params:
                    # Infinite search until stopped
                    best_move = self.engine.search(time_limit_ms=None)
                else:
                    # Tournament time controls
                    best_move = self.engine.search(
                        wtime=params.get("wtime"),
                        btime=params.get("btime"),
                        winc=params.get("winc"),
                        binc=params.get("binc"),
                        moves_to_go=params.get("movestogo"),
                        depth_override=params.get("depth")
                    )
                    
            except Exception as e:
                if self.debug:
                    self._send_search_info({"string": f"Search error: {e}"})
                
            # Send best move
            if best_move and not self.stop_requested:
                self.send_bestmove(best_move)
            else:
                # Emergency move - get any legal move
                try:
                    # Try to get legal moves from the engine's move generator
                    legal_moves = self.engine.move_generator.get_legal_moves()
                    
                    if legal_moves:
                        emergency_move = legal_moves[0]
                        self.send_bestmove(emergency_move)
                        if self.debug:
                            self._send_search_info({"string": "Used emergency move"})
                    else:
                        self._out("bestmove 0000")
                        if self.debug:
                            self._send_search_info({"string": "No legal moves available"})
                except Exception as emergency_error:
                    if self.debug:
                        self._send_search_info({"string": f"Emergency move error: {emergency_error}"})
                    self._out("bestmove 0000")
                    
        except Exception as e:
            if self.debug:
                self._send_search_info({"string": f"Thread error: {e}"})
            self._out("bestmove 0000")
            
        finally:
            self.searching = False
            self.stop_requested = False
            
    def _search_info_handler(self, info: Dict[str, Any]) -> None:
        """Handle search information from the engine during search."""
        if not self.stop_requested:
            self._send_search_info(info)
            
    # Testing and utility methods
    def run_command(self, command: str) -> Optional[str]:
        """Run a single UCI command and return response (useful for testing)."""
        original_silent = self.silent_mode
        responses = []
        
        def capture_output(text):
            responses.append(text)
            
        # Temporarily capture output
        old_out = self._out
        self._out = capture_output
        
        try:
            self.process_command(command)
            # Wait a bit for threaded commands
            if command.startswith("go"):
                time.sleep(0.1)
                while self.searching:
                    time.sleep(0.01)
        finally:
            self._out = old_out
            self.silent_mode = original_silent
            
        return "\n".join(responses) if responses else None
        
    def run_uci_session(self, commands: List[str]) -> List[str]:
        """Run a series of UCI commands and return all responses (useful for testing)."""
        responses = []
        for command in commands:
            response = self.run_command(command)
            if response:
                responses.append(response)
        return responses
