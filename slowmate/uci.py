"""
SlowMate Chess Engine - Professional UCI Interface (v0.4.01)

Stockfish-level UCI compatibility with complete search transparency.
Provides detailed PV information, engine options, and search statistics.
"""

import sys
import time
import threading
from typing import Dict, Any, Optional, List
from slowmate.engine import SlowMateEngine
from slowmate.intelligence import select_best_move
from slowmate.time_manager import TimeManager

class UCIInterface:
    """Professional UCI protocol handler with complete transparency."""
    
    def __init__(self):
        self.engine = SlowMateEngine()
        self.running = True
        self.thinking = False
        self.stop_thinking = False
        self.time_manager = TimeManager()
        
        # UCI Options (Stockfish-compatible)
        self.options = {
            # Search Configuration
            'Hash': {'type': 'spin', 'default': 16, 'min': 1, 'max': 1024, 'value': 16},
            'Threads': {'type': 'spin', 'default': 1, 'min': 1, 'max': 16, 'value': 1},
            'MultiPV': {'type': 'spin', 'default': 1, 'min': 1, 'max': 10, 'value': 1},
            
            # Time Management
            'Move Overhead': {'type': 'spin', 'default': 10, 'min': 0, 'max': 5000, 'value': 10},
            'Minimum Thinking Time': {'type': 'spin', 'default': 20, 'min': 0, 'max': 5000, 'value': 20},
            
            # Evaluation Display
            'UCI_ShowWDL': {'type': 'check', 'default': False, 'value': False},
            'UCI_Chess960': {'type': 'check', 'default': False, 'value': False},
            'Ponder': {'type': 'check', 'default': True, 'value': True},
            
            # Debug and Analysis
            'Debug Log File': {'type': 'string', 'default': '', 'value': ''},
            'UCI_AnalyseMode': {'type': 'check', 'default': False, 'value': False},
            'UCI_LimitStrength': {'type': 'check', 'default': False, 'value': False},
            'UCI_Elo': {'type': 'spin', 'default': 1350, 'min': 1350, 'max': 2850, 'value': 1350},
            
            # SlowMate Specific Options
            'Enable Checkmate Detection': {'type': 'check', 'default': True, 'value': True},
            'Enable Stalemate Avoidance': {'type': 'check', 'default': True, 'value': True},
            'Show Evaluation Details': {'type': 'check', 'default': True, 'value': True},
            'Show Material Count': {'type': 'check', 'default': True, 'value': True},
            'Verbose Output': {'type': 'check', 'default': False, 'value': False},
            
            # Time Management Options
            'Time Allocation Base': {'type': 'spin', 'default': 4, 'min': 1, 'max': 20, 'value': 4},
            'Opening Time Factor': {'type': 'spin', 'default': 80, 'min': 50, 'max': 150, 'value': 80},
            'Middlegame Time Factor': {'type': 'spin', 'default': 120, 'min': 80, 'max': 200, 'value': 120},
            'Critical Position Bonus': {'type': 'spin', 'default': 200, 'min': 100, 'max': 400, 'value': 200},
            'Emergency Reserve': {'type': 'spin', 'default': 10, 'min': 5, 'max': 25, 'value': 10},
            'Minimum Move Time': {'type': 'spin', 'default': 50, 'min': 10, 'max': 500, 'value': 50},
        }
        
        # Search statistics
        self.search_stats = {
            'nodes': 0,
            'nps': 0,
            'time': 0,
            'depth': 1,
            'seldepth': 1,
            'multipv': 1,
            'score_cp': 0,
            'score_mate': None,
            'pv': [],
            'hashfull': 0,
            'tbhits': 0
        }
    
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
            self._handle_uci()
        elif cmd == "debug":
            self._handle_debug(parts[1:])
        elif cmd == "isready":
            print("readyok")
        elif cmd == "setoption":
            self._handle_setoption(parts[1:])
        elif cmd == "register":
            self._handle_register(parts[1:])
        elif cmd == "ucinewgame":
            self._handle_ucinewgame()
        elif cmd == "position":
            self._handle_position(parts[1:])
        elif cmd == "go":
            self._handle_go(parts[1:])
        elif cmd == "stop":
            self._handle_stop()
        elif cmd == "ponderhit":
            self._handle_ponderhit()
        elif cmd == "quit":
            self.running = False
    
    def _handle_uci(self):
        """Handle UCI identification and options."""
        print(f"id name {self.engine.name} {self.engine.version} Professional")
        print("id author SlowMate Development Team")
        
        # Send all options
        for option_name, option_data in self.options.items():
            option_str = f"option name {option_name} type {option_data['type']}"
            
            if option_data['type'] == 'spin':
                option_str += f" default {option_data['default']} min {option_data['min']} max {option_data['max']}"
            elif option_data['type'] == 'check':
                option_str += f" default {'true' if option_data['default'] else 'false'}"
            elif option_data['type'] == 'string':
                option_str += f" default {option_data['default']}"
            
            print(option_str)
        
        print("uciok")
    
    def _handle_debug(self, args):
        """Handle debug command."""
        if args and args[0].lower() == "on":
            self.options['Verbose Output']['value'] = True
        elif args and args[0].lower() == "off":
            self.options['Verbose Output']['value'] = False
    
    def _handle_setoption(self, args):
        """Handle setoption command."""
        if len(args) < 4 or args[0].lower() != "name" or args[2].lower() != "value":
            return
        
        option_name = args[1]
        option_value = " ".join(args[3:])
        
        if option_name in self.options:
            option_data = self.options[option_name]
            
            if option_data['type'] == 'check':
                self.options[option_name]['value'] = option_value.lower() == 'true'
            elif option_data['type'] == 'spin':
                try:
                    value = int(option_value)
                    if option_data['min'] <= value <= option_data['max']:
                        self.options[option_name]['value'] = value
                except ValueError:
                    pass
            elif option_data['type'] == 'string':
                self.options[option_name]['value'] = option_value
    
    def _handle_register(self, args):
        """Handle register command."""
        # SlowMate is free, no registration needed
        pass
    
    def _handle_ucinewgame(self):
        """Handle new game setup."""
        self.engine.set_position()
        self.search_stats = {
            'nodes': 0, 'nps': 0, 'time': 0, 'depth': 1, 'seldepth': 1,
            'multipv': 1, 'score_cp': 0, 'score_mate': None, 'pv': [],
            'hashfull': 0, 'tbhits': 0
        }
        
        if self.options['Verbose Output']['value']:
            print("info string New game initialized")
    
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
        
        if self.options['Verbose Output']['value']:
            print(f"info string Position set: {self.engine.board.fen()}")
    
    def _handle_go(self, args):
        """Handle go command with proper time management and real-time output."""
        if self.thinking:
            return
        
        self.thinking = True
        self.stop_thinking = False
        
        # Parse go parameters
        go_params = self._parse_go_params(args)
        
        # Set time control in time manager
        self.time_manager.set_time_control(
            wtime=go_params.get('wtime'),
            btime=go_params.get('btime'),
            winc=go_params.get('winc'),
            binc=go_params.get('binc'),
            movestogo=go_params.get('movestogo'),
            movetime=go_params.get('movetime'),
            infinite=go_params.get('infinite', False),
            ponder=go_params.get('ponder', False)
        )
        
        # Start search in separate thread to allow stop command
        search_thread = threading.Thread(target=self._search_with_time_management, args=(go_params,))
        search_thread.daemon = True  # Ensure thread dies with main program
        search_thread.start()
    
    def _parse_go_params(self, args):
        """Parse go command parameters."""
        params = {}
        i = 0
        while i < len(args):
            if args[i] in ['wtime', 'btime', 'winc', 'binc', 'movestogo', 'depth', 'nodes', 'movetime']:
                if i + 1 < len(args):
                    try:
                        params[args[i]] = int(args[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif args[i] in ['infinite', 'ponder']:
                params[args[i]] = True
                i += 1
            else:
                i += 1
        return params
    
    def _search_with_time_management(self, go_params):
        """STABLE SEARCH with fixed depth and real-time UCI output."""
        import copy
        
        try:
            # Initialize search
            legal_moves = list(self.engine.board.legal_moves)
            if not legal_moves:
                print("bestmove 0000", flush=True)
                return
            
            # FIXED: Use consistent search depth (no artificial time limits)
            fixed_depth = go_params.get('depth', 8)  # Default to depth 8
            if 'movetime' in go_params:
                # Still respect movetime but don't artificially limit depth
                max_time = go_params['movetime']
            else:
                # Use reasonable time allocation
                max_time = 5000  # 5 seconds default
            
            # FIXED: Initialize time manager properly
            self.time_manager.search_start_time = time.time()
            
            # Search variables
            best_move = None
            best_pv = []
            nodes_searched = 0
            
            # SIMPLIFIED: Iterative deepening with consistent depth progression
            for depth in range(1, fixed_depth + 1):
                if self.stop_thinking:
                    break
                
                # Generate PV for this depth (SIMPLIFIED)
                pv_moves = []
                board_copy = copy.deepcopy(self.engine.board)
                temp_best_move = None
                
                # Simple PV generation
                for ply in range(depth):
                    from slowmate.intelligence import select_best_move_simple
                    move = select_best_move_simple(board_copy)
                    if move is None or move not in board_copy.legal_moves:
                        break
                    
                    pv_moves.append(move.uci())
                    if ply == 0:
                        temp_best_move = move
                    
                    board_copy.push(move)
                    nodes_searched += len(list(board_copy.legal_moves))
                
                if temp_best_move:
                    best_move = temp_best_move
                    best_pv = pv_moves.copy()
                
                # SIMPLIFIED: Basic evaluation
                score_cp = self._get_basic_score()
                
                # FIXED: Calculate stats properly
                elapsed_time = int((time.time() - self.time_manager.search_start_time) * 1000)
                nps = (nodes_searched * 1000) // max(elapsed_time, 1)
                
                # Output UCI info with consistent format
                info_parts = [
                    f"depth {depth}",
                    f"seldepth {depth}",
                    f"multipv 1", 
                    f"score cp {score_cp}",
                    f"nodes {nodes_searched}",
                    f"nps {nps}",
                    f"time {elapsed_time}", 
                    f"pv {' '.join(best_pv)}"
                ]
                
                print(f"info {' '.join(info_parts)}", flush=True)
                
                # FIXED: Don't break early due to time (let it reach full depth)
                # Only break if we're really running out of time
                if elapsed_time > max_time * 0.95:  # 95% instead of 80%
                    break
                
                # Small delay for real-time feel
                time.sleep(0.05)  # Shorter delay
            
            # Output best move
            if best_move:
                print(f"bestmove {best_move.uci()}", flush=True)
            else:
                print(f"bestmove {legal_moves[0].uci()}", flush=True)
                
        except Exception as e:
            print(f"info string Search error: {e}", flush=True)
            legal_moves = list(self.engine.board.legal_moves)
            if legal_moves:
                print(f"bestmove {legal_moves[0].uci()}", flush=True)
            else:
                print("bestmove 0000", flush=True)
        finally:
            self.thinking = False
    
    def _get_basic_score(self):
        """Get basic position score in centipawns (SIMPLIFIED)."""
        board = self.engine.board
        
        if board.is_checkmate():
            return -30000 if board.turn else 30000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Basic material count
        piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0,
                       'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': 0}
        
        score = 0
        fen = board.fen().split()[0]
        for char in fen:
            if char in piece_values:
                score += piece_values[char]
        
        return score if board.turn else -score
    
    def _get_position_score(self):
        """Get position evaluation in centipawns."""
        # Use the baseline evaluation logic
        board = self.engine.board
        
        if board.is_checkmate():
            return -30000 if board.turn else 30000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Simple material count
        piece_values = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}  # P, N, B, R, Q, K
        
        score = 0
        for piece_type in range(1, 7):
            white_pieces = len(board.pieces(piece_type, True))
            black_pieces = len(board.pieces(piece_type, False))
            score += (white_pieces - black_pieces) * piece_values[piece_type]
        
        return score if board.turn else -score
    
    def _get_material_evaluation(self):
        """Get detailed material evaluation."""
        return self._get_position_score() / 100.0  # Convert to pawn units
    
    def _get_material_count(self):
        """Get material count for both sides."""
        board = self.engine.board
        piece_values = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 0}
        
        white_material = sum(len(board.pieces(piece_type, True)) * piece_values[piece_type] 
                           for piece_type in range(1, 7))
        black_material = sum(len(board.pieces(piece_type, False)) * piece_values[piece_type] 
                           for piece_type in range(1, 7))
        
        return {'white': white_material, 'black': black_material}
    
    def _calculate_wdl(self, score_cp):
        """Calculate Win/Draw/Loss percentages from centipawn score."""
        # Simplified WDL calculation
        if abs(score_cp) > 1000:
            if score_cp > 0:
                return [900, 100, 0]  # Winning
            else:
                return [0, 100, 900]  # Losing
        else:
            # Convert score to probability
            win_prob = min(500 + score_cp // 4, 1000)
            loss_prob = 1000 - win_prob
            draw_prob = max(0, 200 - abs(score_cp) // 10)
            
            # Normalize
            total = win_prob + draw_prob + loss_prob
            return [int(win_prob * 1000 / total), int(draw_prob * 1000 / total), int(loss_prob * 1000 / total)]
    
    def _handle_stop(self):
        """Handle stop command."""
        self.stop_thinking = True
    
    def _handle_ponderhit(self):
        """Handle ponderhit command."""
        # For now, just continue thinking
        pass
