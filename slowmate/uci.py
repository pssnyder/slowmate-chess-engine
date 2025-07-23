"""
SlowMate Chess Engine - UCI Interface (v0.1.0 Baseline)

Basic UCI protocol implementation for tournament play.
"""

import sys
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import select_best_move

class UCIInterface:
    """UCI protocol handler."""
    
    def __init__(self):
        self.engine = SlowMateEngine()
        self.running = True
    
    def run(self):
        """Main UCI loop."""
        while self.running:
            try:
                line = input().strip()
                if line:
                    self.handle_command(line)
            except EOFError:
                break
    
    def handle_command(self, command: str):
        """Handle UCI command."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == "uci":
            print(f"id name {self.engine.name} {self.engine.version}")
            print("id author SlowMate Development Team")
            print("uciok")
        
        elif cmd == "isready":
            print("readyok")
        
        elif cmd == "ucinewgame":
            self.engine.set_position()
        
        elif cmd == "position":
            self._handle_position(parts[1:])
        
        elif cmd == "go":
            self._handle_go(parts[1:])
        
        elif cmd == "quit":
            self.running = False
    
    def _handle_position(self, args):
        """Handle position command."""
        if not args:
            return
        
        if args[0] == "startpos":
            self.engine.set_position()
            if len(args) > 1 and args[1] == "moves":
                for move_uci in args[2:]:
                    self.engine.make_move(move_uci)
        
        elif args[0] == "fen":
            # Find where moves start
            moves_idx = None
            try:
                moves_idx = args.index("moves")
                fen = " ".join(args[1:moves_idx])
            except ValueError:
                fen = " ".join(args[1:])
                moves_idx = len(args)
            
            self.engine.set_position(fen)
            
            # Apply moves if any
            if moves_idx < len(args) - 1:
                for move_uci in args[moves_idx + 1:]:
                    self.engine.make_move(move_uci)
    
    def _handle_go(self, args):
        """Handle go command."""
        # Simple go - just find best move
        best_move = select_best_move(self.engine.board)
        if best_move:
            print(f"bestmove {best_move.uci()}")
        else:
            print("bestmove 0000")
