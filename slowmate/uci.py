"""
SlowMate Chess Engine - UCI Interface

This module implements the Universal Chess Interface (UCI) protocol
for compatibility with chess GUIs like Nibbler, Arena, and others.

UCI Protocol Documentation: http://wbec-ridderkerk.nl/html/UCIProtocol.html
"""

import sys
import threading
from typing import Optional, List
import chess
from slowmate.intelligence import IntelligentSlowMateEngine


class UCIInterface:
    """
    UCI Protocol Interface for SlowMate Chess Engine
    
    Handles communication between chess GUIs and the SlowMate engine
    using the standard UCI (Universal Chess Interface) protocol.
    """
    
    def __init__(self):
        """Initialize UCI interface with SlowMate engine."""
        self.engine = IntelligentSlowMateEngine()
        self.debug = False
        self.is_thinking = False
        self.search_thread = None
        
        # Engine identification
        self.engine_name = "SlowMate"
        self.engine_version = "0.0.2-dev"
        self.author = "SlowMate Project"
    
    def run(self):
        """
        Main UCI command loop.
        Reads commands from stdin and processes them according to UCI protocol.
        """
        try:
            while True:
                try:
                    # Read command from GUI
                    line = input().strip()
                    if not line:
                        continue
                        
                    if self.debug:
                        print(f"info string Debug: Received command '{line}'", flush=True)
                    
                    # Parse and handle command
                    self.handle_command(line)
                    
                except EOFError:
                    # GUI closed connection
                    break
                except KeyboardInterrupt:
                    # Ctrl+C pressed
                    break
                except Exception as e:
                    if self.debug:
                        print(f"info string Error: {str(e)}", flush=True)
                    
        except Exception as e:
            if self.debug:
                print(f"info string Fatal error: {str(e)}", flush=True)
    
    def handle_command(self, command: str):
        """
        Parse and handle a UCI command.
        
        Args:
            command: The UCI command string to process
        """
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle UCI commands
        if cmd == "uci":
            self.handle_uci()
        elif cmd == "debug":
            self.handle_debug(args)
        elif cmd == "isready":
            self.handle_isready()
        elif cmd == "setoption":
            self.handle_setoption(args)
        elif cmd == "ucinewgame":
            self.handle_ucinewgame()
        elif cmd == "position":
            self.handle_position(args)
        elif cmd == "go":
            self.handle_go(args)
        elif cmd == "stop":
            self.handle_stop()
        elif cmd == "ponderhit":
            self.handle_ponderhit()
        elif cmd == "quit":
            self.handle_quit()
        else:
            if self.debug:
                print(f"info string Unknown command: {command}", flush=True)
    
    def handle_uci(self):
        """
        Handle 'uci' command - initialize UCI mode.
        Sends engine identification and options.
        """
        print(f"id name {self.engine_name} {self.engine_version}", flush=True)
        print(f"id author {self.author}", flush=True)
        
        # Engine options
        print("option name Intelligence type check default true", flush=True)
        
        print("uciok", flush=True)
    
    def handle_debug(self, args: List[str]):
        """
        Handle 'debug' command - toggle debug mode.
        
        Args:
            args: Command arguments ("on" or "off")
        """
        if args and len(args) > 0:
            if args[0].lower() == "on":
                self.debug = True
                print("info string Debug mode enabled", flush=True)
            elif args[0].lower() == "off":
                self.debug = False
    
    def handle_isready(self):
        """Handle 'isready' command - confirm engine readiness."""
        print("readyok", flush=True)
    
    def handle_setoption(self, args: List[str]):
        """
        Handle 'setoption' command - configure engine options.
        
        Args:
            args: Option setting arguments
        """
        if len(args) >= 4 and args[0] == "name" and args[2] == "value":
            option_name = args[1].lower()
            option_value = args[3].lower()
            
            if option_name == "intelligence":
                if option_value in ["true", "1", "on"]:
                    self.engine.toggle_intelligence(True)
                    if self.debug:
                        print("info string Intelligence enabled", flush=True)
                elif option_value in ["false", "0", "off"]:
                    self.engine.toggle_intelligence(False)
                    if self.debug:
                        print("info string Intelligence disabled (random moves)", flush=True)
            else:
                if self.debug:
                    print(f"info string Unknown option: {option_name}", flush=True)
        else:
            if self.debug:
                print(f"info string Invalid setoption format: {' '.join(args)}", flush=True)
    
    def handle_ucinewgame(self):
        """Handle 'ucinewgame' command - prepare for new game."""
        self.engine.reset_game()
        if self.debug:
            print("info string New game initialized", flush=True)
    
    def handle_position(self, args: List[str]):
        """
        Handle 'position' command - set up board position.
        
        Args:
            args: Position arguments (startpos/fen + moves)
        """
        if not args:
            return
            
        try:
            if args[0] == "startpos":
                # Set to starting position
                self.engine.board = chess.Board()
                move_index = 1
                
                # Check for moves after startpos
                if len(args) > 1 and args[1] == "moves":
                    move_index = 2
                    
            elif args[0] == "fen":
                # Set position from FEN string
                # Find where FEN ends and moves begin
                fen_parts = []
                move_index = 1
                
                # FEN has 6 parts, find them
                for i in range(1, min(7, len(args))):
                    if args[i] == "moves":
                        move_index = i + 1
                        break
                    fen_parts.append(args[i])
                    move_index = i + 1
                
                if fen_parts:
                    fen_string = " ".join(fen_parts)
                    self.engine.board = chess.Board(fen_string)
                else:
                    return
            else:
                return
            
            # Apply moves if present
            if move_index < len(args) and args[move_index - 1] == "moves":
                for move_str in args[move_index:]:
                    try:
                        move = chess.Move.from_uci(move_str)
                        if move in self.engine.board.legal_moves:
                            self.engine.board.push(move)
                        else:
                            if self.debug:
                                print(f"info string Illegal move: {move_str}", flush=True)
                            break
                    except ValueError:
                        if self.debug:
                            print(f"info string Invalid move format: {move_str}", flush=True)
                        break
            
            if self.debug:
                print(f"info string Position set: {self.engine.board.fen()}", flush=True)
                
        except Exception as e:
            if self.debug:
                print(f"info string Position error: {str(e)}", flush=True)
    
    def handle_go(self, args: List[str]):
        """
        Handle 'go' command - start searching for best move.
        
        Args:
            args: Search parameters (time controls, depth, etc.)
        """
        if self.is_thinking:
            return
            
        # TODO: Parse search parameters (wtime, btime, depth, etc.)
        # For now, we'll ignore parameters and just select a random move
        
        self.is_thinking = True
        
        # Start search in separate thread to avoid blocking UCI communication
        self.search_thread = threading.Thread(target=self._search_and_respond)
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def _search_and_respond(self):
        """
        Internal method to search for best move and send response.
        Runs in separate thread to avoid blocking UCI communication.
        """
        try:
            if self.debug:
                print("info string Starting intelligent move search", flush=True)
            
            # Get current legal moves
            legal_moves = list(self.engine.board.legal_moves)
            
            if not legal_moves:
                print("bestmove (none)", flush=True)
                self.is_thinking = False
                return
            
            if self.debug:
                print(f"info string Found {len(legal_moves)} legal moves", flush=True)
            
            # Use intelligent engine to select move
            selected_move = self.engine.select_move()
            
            if selected_move is None:
                print("bestmove (none)", flush=True)
            else:
                # Get evaluation score for UCI
                move_score = self.engine.intelligence._evaluate_move(selected_move)
                
                # Send evaluation information (UCI standard)
                print(f"info depth 1 score cp {move_score}", flush=True)
                
                # Get move analysis for UCI info
                if self.debug:
                    reasoning = self.engine.intelligence.get_selection_reasoning(legal_moves, selected_move)
                    print(f"info string {reasoning}", flush=True)
                
                # Convert to UCI format and send
                move_uci = selected_move.uci()
                print(f"bestmove {move_uci}", flush=True)
                
                if self.debug:
                    # Show detailed analysis
                    move_san = self.engine.board.san(selected_move)
                    analysis = self.engine.intelligence.get_move_analysis(selected_move)
                    
                    print(f"info string Selected move: {move_san} ({move_uci})", flush=True)
                    
                    if analysis['is_checkmate']:
                        print("info string This move delivers CHECKMATE!", flush=True)
                    elif analysis['is_check']:
                        print("info string This move gives CHECK", flush=True)
                    
                    if analysis['is_stalemate']:
                        print("info string Warning: This move causes stalemate", flush=True)
                    elif analysis['is_draw']:
                        print("info string Warning: This move leads to a draw", flush=True)
        
        except Exception as e:
            if self.debug:
                print(f"info string Search error: {str(e)}", flush=True)
            print("bestmove (none)", flush=True)
        finally:
            self.is_thinking = False
    
    def handle_stop(self):
        """Handle 'stop' command - stop current search."""
        if self.is_thinking:
            self.is_thinking = False
            # Wait for search thread to finish
            if self.search_thread and self.search_thread.is_alive():
                self.search_thread.join(timeout=1.0)
            if self.debug:
                print("info string Search stopped", flush=True)
    
    def handle_ponderhit(self):
        """Handle 'ponderhit' command - ponder move was played."""
        # TODO: Implement pondering in future phases
        if self.debug:
            print("info string Ponderhit not yet implemented", flush=True)
    
    def handle_quit(self):
        """Handle 'quit' command - terminate engine."""
        if self.debug:
            print("info string Engine shutting down", flush=True)
        sys.exit(0)


def main():
    """
    Main entry point for UCI interface.
    Creates and runs the UCI interface.
    """
    uci = UCIInterface()
    uci.run()


if __name__ == "__main__":
    main()
