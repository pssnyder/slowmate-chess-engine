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
            'Hash': {'type': 'spin', 'default': 64, 'min': 1, 'max': 1024, 'value': 64},
            'Threads': {'type': 'spin', 'default': 1, 'min': 1, 'max': 16, 'value': 1},
            'MultiPV': {'type': 'spin', 'default': 1, 'min': 1, 'max': 10, 'value': 1},
            'Clear Hash': {'type': 'button', 'value': False},
            
            # Advanced Search Options  
            'Contempt': {'type': 'spin', 'default': 0, 'min': -100, 'max': 100, 'value': 0},
            'NullMove': {'type': 'check', 'default': True, 'value': True},
            'QuiescenceSearch': {'type': 'check', 'default': True, 'value': True},
            'QuiescenceDepth': {'type': 'spin', 'default': 6, 'min': 0, 'max': 16, 'value': 6},
            'NullMoveReduction': {'type': 'spin', 'default': 2, 'min': 1, 'max': 4, 'value': 2},
            
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
        elif cmd == "eval":
            self._handle_eval()
        elif cmd == "d":
            self._handle_display()
        elif cmd == "flip":
            self._handle_flip()
        elif cmd == "perft":
            self._handle_perft(parts)
        elif cmd == "clearhash":
            self._handle_clearhash()
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
                
                # Handle check options
                if option_name == "NullMove":
                    self.engine.search_engine.null_move_enabled = option_value.lower() == 'true'
                elif option_name == "QuiescenceSearch":
                    self.engine.search_engine.quiescence_enabled = option_value.lower() == 'true'
                    
            elif option_data['type'] == 'button':
                # Handle button options
                if option_name == "Clear Hash":
                    self.engine.clear_hash()
            elif option_data['type'] == 'spin':
                try:
                    value = int(option_value)
                    if option_data['min'] <= value <= option_data['max']:
                        self.options[option_name]['value'] = value
                        
                        # Handle special options
                        if option_name == "Hash":
                            self.engine.set_hash_size(value)
                        elif option_name == "Contempt":
                            self.engine.set_contempt(value)
                        elif option_name == "QuiescenceDepth":
                            self.engine.search_engine.max_quiescence_depth = value
                        elif option_name == "NullMoveReduction":
                            self.engine.search_engine.null_move_reduction = value
                        
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
            wtime=go_params.get('wtime', 0),
            btime=go_params.get('btime', 0),
            winc=go_params.get('winc', 0),
            binc=go_params.get('binc', 0),
            movestogo=go_params.get('movestogo', 0),
            movetime=go_params.get('movetime', 0),
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
        """ENHANCED SEARCH with NegaScout and real-time UCI output."""
        import copy
        
        try:
            # Initialize search
            legal_moves = list(self.engine.board.legal_moves)
            if not legal_moves:
                print("bestmove 0000", flush=True)
                return
            
            # Search parameters
            fixed_depth = go_params.get('depth', 8)  # Default to depth 8
            if 'movetime' in go_params:
                max_time = go_params['movetime']
            else:
                max_time = 5000  # 5 seconds default
            
            # Initialize search engine
            self.time_manager.search_start_time = time.time()
            self.engine.search_engine.reset_stats()
            self.engine.search_engine.max_search_time = int(max_time)
            
            # Search variables
            best_move = None
            best_pv = []
            nodes_searched = 0
            
            # Iterative deepening with NegaScout search
            for depth in range(1, fixed_depth + 1):
                if self.stop_thinking:
                    break
                
                # NegaScout search at current depth
                score_cp, temp_best_move = self.engine.search_engine.negascout_search(
                    self.engine.board, depth, -3000, 3000
                )
                
                if temp_best_move:
                    best_move = temp_best_move
                    best_pv = self.engine.search_engine.get_pv()
                else:
                    # Fallback: Use first legal move and get a basic evaluation
                    legal_moves = list(self.engine.board.legal_moves)
                    if legal_moves:
                        best_move = legal_moves[0]
                        best_pv = [best_move.uci()]
                        # Get basic position evaluation
                        score_cp = self.engine.search_engine.evaluate_position(self.engine.board)
                    else:
                        # No legal moves (shouldn't happen in normal play)
                        score_cp = 0
                
                # Get search statistics
                search_stats = self.engine.get_search_stats()
                nodes_searched = search_stats.get('nodes_searched', 0)
                
                # Calculate stats
                elapsed_time = int((time.time() - self.time_manager.search_start_time) * 1000)
                nps = (nodes_searched * 1000) // max(elapsed_time, 1)
                
                # Format score
                if score_cp > 29000:
                    mate_in = (30000 - score_cp + 1) // 2
                    score_str = f"score mate {mate_in}"
                elif score_cp < -29000:
                    mate_in = -(score_cp + 30000 - 1) // 2
                    score_str = f"score mate {mate_in}"
                else:
                    score_str = f"score cp {score_cp}"
                
                # Output UCI info
                info_parts = [
                    f"depth {depth}",
                    f"seldepth {depth}",
                    f"multipv 1", 
                    score_str,
                    f"nodes {nodes_searched}",
                    f"nps {nps}",
                    f"hashfull {search_stats.get('hash_full', 0)}",
                    f"time {elapsed_time}", 
                    f"pv {' '.join(best_pv[:8])}"
                ]
                
                print(f"info {' '.join(info_parts)}", flush=True)
                
                # Check time limit
                if elapsed_time > max_time * 0.95:
                    break
                
                time.sleep(0.01)
            
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
            # Return mate score based on whose turn it is
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
    
    def _handle_eval(self):
        """Handle eval command - display position evaluation."""
        try:
            import chess
            score = self._get_basic_score()
            print(f"Total evaluation: {score / 100:.2f}")
            
            # Show detailed breakdown
            material = self._get_material_evaluation()
            print(f"Material: {material:.2f}")
            
            # Position info
            print(f"FEN: {self.engine.board.fen()}")
            print(f"Key: {hash(self.engine.board.fen()) & 0xFFFFFFFF:08x}")
            print(f"Legal moves: {len(list(self.engine.board.legal_moves))}")
            
            # Game state
            if self.engine.board.is_checkmate():
                print("Position: Checkmate")
            elif self.engine.board.is_stalemate():
                print("Position: Stalemate")
            elif self.engine.board.is_check():
                print("Position: Check")
            else:
                print("Position: Normal")
            
            # Game rules status
            game_status = self.engine.game_rules.get_game_status(self.engine.board)
            if game_status['can_claim_draw']:
                print("\nDRAW INFORMATION:")
                rep_info = game_status['repetition_info']
                fifty_info = game_status['fifty_move_info']
                
                if rep_info['can_claim_threefold']:
                    print(f"  Threefold repetition: YES (count: {rep_info['current_repetitions']})")
                elif rep_info['approaching_threefold']:
                    print(f"  Approaching threefold: count {rep_info['current_repetitions']}")
                
                if fifty_info['can_claim_fifty']:
                    print(f"  50-move rule: YES (halfmoves: {fifty_info['halfmove_clock']})")
                elif fifty_info['approaching_fifty']:
                    print(f"  Approaching 50-move: {fifty_info['moves_to_fifty']} moves left")
                    
        except Exception as e:
            print(f"Error in eval: {e}")
    
    def _handle_display(self):
        """Handle d command - display current board position."""
        try:
            import chess
            print(self.engine.board)
            print(f"FEN: {self.engine.board.fen()}")
            print(f"Turn: {'White' if self.engine.board.turn else 'Black'}")
            print(f"Legal moves: {len(list(self.engine.board.legal_moves))}")
            
            # Show castling rights
            castling = []
            if self.engine.board.has_kingside_castling_rights(True):
                castling.append("K")
            if self.engine.board.has_queenside_castling_rights(True):
                castling.append("Q") 
            if self.engine.board.has_kingside_castling_rights(False):
                castling.append("k")
            if self.engine.board.has_queenside_castling_rights(False):
                castling.append("q")
            
            print(f"Castling: {''.join(castling) if castling else '-'}")
            
            # Show en passant
            if self.engine.board.ep_square:
                print(f"En passant: {chess.square_name(self.engine.board.ep_square)}")
            
            # Show draw-related counters
            print(f"Halfmove clock: {self.engine.board.halfmove_clock}")
            print(f"Fullmove number: {self.engine.board.fullmove_number}")
            
        except Exception as e:
            print(f"Error in display: {e}")
    
    def _handle_flip(self):
        """Handle flip command - flip board display."""
        # For console display, we can't really flip the board
        # But we can acknowledge the command
        print("Board flipped (console mode)")
    
    def _handle_ponderhit(self):
        """Handle ponderhit command."""
        # TODO: Implement pondering
        pass
    
    def _handle_perft(self, parts):
        """Handle perft command - performance test."""
        try:
            depth = int(parts[1]) if len(parts) > 1 else 5
            if depth > 7:
                print(f"Depth {depth} too large, limiting to 7")
                depth = 7
            
            nodes = self._perft(self.engine.board, depth)
            print(f"Nodes searched: {nodes}")
        except (ValueError, IndexError):
            print("Usage: perft <depth>")
        except Exception as e:
            print(f"Error in perft: {e}")
    
    def _perft(self, board, depth):
        """Recursive perft calculation."""
        if depth == 0:
            return 1
        
        nodes = 0
        for move in board.legal_moves:
            board.push(move)
            nodes += self._perft(board, depth - 1)
            board.pop()
        return nodes
    
    def _handle_clearhash(self):
        """Handle clearhash command - clear the hash table."""
        try:
            self.engine.clear_hash()
            if self.options.get('Verbose Output', {}).get('value', False):
                print("info string Hash table cleared")
        except Exception as e:
            print(f"Error clearing hash: {e}")
