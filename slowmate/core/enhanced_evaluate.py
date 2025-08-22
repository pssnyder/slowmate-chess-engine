"""
SlowMate Chess Engine v2.2 - Enhanced Evaluation Function
Advanced positional evaluation to compete at 650-750 ELO level
"""

import chess
from typing import Dict, List, Tuple, Optional
import math


class EnhancedEvaluator:
    """Enhanced evaluation function for SlowMate v2.2."""
    
    def __init__(self):
        """Initialize the enhanced evaluator."""
        # Piece values (centipawns)
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # v2.2 ENHANCEMENT: Piece-square tables (from white's perspective)
        self.pawn_table = [
             0,  0,  0,  0,  0,  0,  0,  0,
            78, 83, 86, 73, 102, 82, 85, 90,
             7, 29, 21, 44, 40, 31, 44, 7,
           -17,  16, -2, 15, 14, 0, 15, -13,
           -26, 3, 10, 9, 6, 1, 0, -23,
           -22, 9, 5, -11, -10, -2, 3, -19,
           -31, 8, -7, -37, -36, -14, 3, -31,
             0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        self.knight_table = [
            -66, -53, -75, -75, -10, -55, -58, -70,
            -3, -6, 100, -36, 4, 62, -4, -14,
            10, 67, 1, 74, 73, 27, 62, -2,
            24, 24, 45, 37, 33, 41, 25, 17,
            -1, 5, 31, 21, 22, 35, 2, 0,
            -18, 10, 13, 22, 18, 15, 11, -14,
            -23, -15, 2, 0, 2, 0, -23, -20,
            -74, -23, -26, -24, -19, -35, -22, -69
        ]
        
        self.bishop_table = [
            -59, -78, -82, -76, -23,-107, -37, -50,
            -11, 20, 35, -42, -39, 31, 2, -22,
            -9, 39, -32, 41, 52, -10, 28, -14,
            25, 17, 20, 34, 26, 25, 15, 10,
            13, 10, 17, 23, 17, 16, 0, 7,
            14, 25, 24, 15, 8, 25, 20, 15,
            19, 20, 11, 6, 7, 6, 20, 16,
            -7, 2, -15, -12, -14, -15, -10, -10
        ]
        
        self.rook_table = [
            35, 29, 33, 4, 37, 33, 56, 50,
            55, 29, 56, 67, 55, 62, 34, 60,
            19, 35, 28, 33, 45, 27, 25, 15,
             0, 5, 16, 13, 18, -4, -9, -6,
           -28, -35, -16, -21, -13, -29, -46, -30,
           -42, -28, -42, -25, -25, -35, -26, -46,
           -53, -38, -31, -26, -29, -43, -44, -53,
           -30, -24, -18, 5, -2, -18, -31, -32
        ]
        
        self.queen_table = [
            6, 1, -8,-104, 69, 24, 88, 26,
            14, 32, 60, -10, 20, 76, 57, 24,
            -2, 43, 32, 60, 72, 63, 43, 2,
            1, -16, 22, 17, 25, 20, -13, -6,
            -14, -15, -2, -5, -1, -10, -20, -22,
            -30, -6, -13, -11, -16, -11, -16, -27,
            -36, -18, 0, -19, -15, -15, -21, -38,
            -39, -30, -31, -13, -31, -36, -34, -42
        ]
        
        self.king_middle_table = [
            4, 54, 47, -99, -99, 60, 83, -62,
           -32, 10, 55, 56, 56, 55, 10, 3,
           -62, 12, -57, 44, -67, 28, 37, -31,
           -55, 50, 11, -4, -19, 13, 0, -49,
           -55, -43, -52, -28, -51, -47, -8, -50,
           -47, -42, -43, -79, -64, -32, -29, -32,
            -4, 3, -14, -50, -57, -18, 13, 4,
            17, 30, -3, -14, 6, -1, 40, 18
        ]
        
        self.king_end_table = [
           -74, -35, -18, -18, -11, 15, 4, -17,
           -12, 17, 14, 17, 17, 38, 23, 11,
            10, 17, 23, 15, 20, 45, 44, 13,
            -8, 22, 24, 27, 26, 33, 26, 3,
           -18, -4, 21, 24, 27, 23, 9, -11,
           -19, -3, 11, 21, 23, 16, 7, -9,
           -27, -11, 4, 13, 14, 4, -5, -17,
           -53, -34, -21, -11, -28, -14, -24, -43
        ]
        
        # v2.2 ENHANCEMENT: Evaluation weights
        self.weights = {
            'material': 1.0,
            'piece_square': 0.8,
            'pawn_structure': 0.6,
            'king_safety': 0.7,
            'piece_activity': 0.5,
            'endgame_factor': 0.4
        }
        
        # v2.2 ENHANCEMENT: Game phase detection
        self.phase_material = {
            chess.PAWN: 0,
            chess.KNIGHT: 1,
            chess.BISHOP: 1,
            chess.ROOK: 2,
            chess.QUEEN: 4
        }
        self.total_phase = 24  # 4*Q + 4*R + 4*B + 4*N = 24
        
    def evaluate(self, board) -> float:
        """Enhanced evaluation function for v2.2."""
        try:
            if board.board.is_checkmate():
                return -20000 if board.board.turn else 20000
            
            if board.board.is_stalemate() or board.board.is_insufficient_material():
                return 0
            
            # Calculate game phase
            phase = self._calculate_game_phase(board.board)
            mg_score = 0  # Middle game score
            eg_score = 0  # Endgame score
            
            # Material and piece-square evaluation
            for square in chess.SQUARES:
                piece = board.board.piece_at(square)
                if piece:
                    color_factor = 1 if piece.color == chess.WHITE else -1
                    
                    # Material
                    material_value = self.piece_values[piece.piece_type]
                    mg_score += material_value * color_factor
                    eg_score += material_value * color_factor
                    
                    # Piece-square tables
                    pst_value = self._get_piece_square_value(piece, square, phase < 8)
                    mg_score += pst_value * color_factor * self.weights['piece_square']
                    eg_score += pst_value * color_factor * self.weights['piece_square']
            
            # v2.2 ENHANCEMENT: Positional factors
            positional_mg = self._evaluate_positional_factors(board.board, True)
            positional_eg = self._evaluate_positional_factors(board.board, False)
            
            mg_score += positional_mg
            eg_score += positional_eg
            
            # Interpolate between middle game and endgame
            if phase >= 24:
                final_score = mg_score
            elif phase <= 0:
                final_score = eg_score
            else:
                final_score = (mg_score * phase + eg_score * (24 - phase)) / 24
            
            # CRITICAL FIX: Return evaluation from perspective of side to move
            # final_score is calculated from White's perspective
            # If it's White's turn: return as-is (positive = good for White)
            # If it's Black's turn: negate (positive = good for Black)
            return final_score if board.board.turn == chess.WHITE else -final_score
            
        except Exception as e:
            # Fallback to basic material evaluation
            try:
                return self._basic_material_evaluation(board.board)
            except:
                return 0
    
    def _calculate_game_phase(self, board: chess.Board) -> int:
        """Calculate the current game phase (0 = endgame, 24 = opening)."""
        phase = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                phase += self.phase_material.get(piece.piece_type, 0)
        return min(phase, 24)
    
    def _get_piece_square_value(self, piece: chess.Piece, square: int, is_middlegame: bool) -> int:
        """Get piece-square table value."""
        # Flip square for black pieces
        sq = square if piece.color == chess.WHITE else square ^ 56
        
        if piece.piece_type == chess.PAWN:
            return self.pawn_table[sq]
        elif piece.piece_type == chess.KNIGHT:
            return self.knight_table[sq]
        elif piece.piece_type == chess.BISHOP:
            return self.bishop_table[sq]
        elif piece.piece_type == chess.ROOK:
            return self.rook_table[sq]
        elif piece.piece_type == chess.QUEEN:
            return self.queen_table[sq]
        elif piece.piece_type == chess.KING:
            if is_middlegame:
                return self.king_middle_table[sq]
            else:
                return self.king_end_table[sq]
        
        return 0
    
    def _evaluate_positional_factors(self, board: chess.Board, is_middlegame: bool) -> float:
        """v2.2 ENHANCEMENT: Evaluate positional factors."""
        score = 0
        
        # Pawn structure evaluation
        score += self._evaluate_pawn_structure(board) * self.weights['pawn_structure']
        
        # King safety (more important in middlegame)
        if is_middlegame:
            score += self._evaluate_king_safety(board) * self.weights['king_safety']
        
        # Piece activity
        score += self._evaluate_piece_activity(board) * self.weights['piece_activity']
        
        # Center control
        score += self._evaluate_center_control(board) * 0.3
        
        # Mobility
        score += self._evaluate_mobility(board) * 0.2
        
        return score
    
    def _evaluate_pawn_structure(self, board: chess.Board) -> float:
        """Evaluate pawn structure (doubled, isolated, passed pawns)."""
        score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            color_factor = 1 if color == chess.WHITE else -1
            pawns = board.pieces(chess.PAWN, color)
            
            # Count pawns per file
            files = [0] * 8
            for pawn in pawns:
                files[chess.square_file(pawn)] += 1
            
            for file_idx, pawn_count in enumerate(files):
                if pawn_count == 0:
                    continue
                
                # Doubled pawns penalty
                if pawn_count > 1:
                    score += (pawn_count - 1) * -20 * color_factor
                
                # Isolated pawns penalty
                if (file_idx == 0 or files[file_idx - 1] == 0) and \
                   (file_idx == 7 or files[file_idx + 1] == 0):
                    score += -15 * color_factor
            
            # Passed pawns bonus
            for pawn in pawns:
                if self._is_passed_pawn(board, pawn, color):
                    rank = chess.square_rank(pawn)
                    if color == chess.WHITE:
                        bonus = (rank - 1) * 10
                    else:
                        bonus = (6 - rank) * 10
                    score += bonus * color_factor
        
        return score
    
    def _is_passed_pawn(self, board: chess.Board, pawn_square: int, color: chess.Color) -> bool:
        """Check if a pawn is passed."""
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        # Check files (current and adjacent)
        files_to_check = [file]
        if file > 0:
            files_to_check.append(file - 1)
        if file < 7:
            files_to_check.append(file + 1)
        
        opponent_color = not color
        
        for check_file in files_to_check:
            if color == chess.WHITE:
                # Check ranks ahead for white
                for check_rank in range(rank + 1, 8):
                    square = chess.square(check_file, check_rank)
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == opponent_color:
                        return False
            else:
                # Check ranks ahead for black
                for check_rank in range(rank):
                    square = chess.square(check_file, check_rank)
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == opponent_color:
                        return False
        
        return True
    
    def _evaluate_king_safety(self, board: chess.Board) -> float:
        """Evaluate king safety."""
        score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            color_factor = 1 if color == chess.WHITE else -1
            king_square = board.king(color)
            
            if king_square is None:
                continue
            
            # Pawn shield
            shield_score = self._evaluate_pawn_shield(board, king_square, color)
            score += shield_score * color_factor
            
            # King exposure (number of attacking pieces)
            attackers = 0
            for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                attackers += len(board.attackers(not color, king_square) & board.pieces(piece_type, not color))
            
            score += -attackers * 10 * color_factor
        
        return score
    
    def _evaluate_pawn_shield(self, board: chess.Board, king_square: int, color: chess.Color) -> float:
        """Evaluate pawn shield around the king."""
        score = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check pawn shield (3 files around king, 2 ranks ahead)
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if 0 <= file <= 7:
                for rank_offset in [1, 2]:
                    if color == chess.WHITE:
                        rank = king_rank + rank_offset
                    else:
                        rank = king_rank - rank_offset
                    
                    if 0 <= rank <= 7:
                        square = chess.square(file, rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            score += 10 if rank_offset == 1 else 5
        
        return score
    
    def _evaluate_piece_activity(self, board: chess.Board) -> float:
        """Evaluate piece activity and development."""
        score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            color_factor = 1 if color == chess.WHITE else -1
            
            # Knight development
            knights = board.pieces(chess.KNIGHT, color)
            for knight in knights:
                rank = chess.square_rank(knight)
                # Prefer knights on 3rd rank or higher
                if (color == chess.WHITE and rank >= 2) or (color == chess.BLACK and rank <= 5):
                    score += 15 * color_factor
            
            # Bishop development
            bishops = board.pieces(chess.BISHOP, color)
            for bishop in bishops:
                # Prefer bishops not on back rank
                rank = chess.square_rank(bishop)
                if (color == chess.WHITE and rank > 0) or (color == chess.BLACK and rank < 7):
                    score += 10 * color_factor
            
            # Rook activity (on open/semi-open files)
            rooks = board.pieces(chess.ROOK, color)
            for rook in rooks:
                file = chess.square_file(rook)
                file_score = self._evaluate_file_for_rook(board, file, color)
                score += file_score * color_factor
        
        return score
    
    def _evaluate_file_for_rook(self, board: chess.Board, file: int, color: chess.Color) -> float:
        """Evaluate how good a file is for a rook."""
        own_pawns = 0
        opponent_pawns = 0
        
        for rank in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                if piece.color == color:
                    own_pawns += 1
                else:
                    opponent_pawns += 1
        
        if own_pawns == 0 and opponent_pawns == 0:
            return 20  # Open file
        elif own_pawns == 0:
            return 10  # Semi-open file
        else:
            return 0   # Closed file
    
    def _evaluate_center_control(self, board: chess.Board) -> float:
        """Evaluate control of central squares."""
        score = 0
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                          chess.D3, chess.D6, chess.E3, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6]
        
        for square in center_squares:
            white_attackers = len(board.attackers(chess.WHITE, square))
            black_attackers = len(board.attackers(chess.BLACK, square))
            score += (white_attackers - black_attackers) * 5
            
            # Bonus for pieces actually on central squares
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                score += 10 if piece.color == chess.WHITE else -10
        
        for square in extended_center:
            white_attackers = len(board.attackers(chess.WHITE, square))
            black_attackers = len(board.attackers(chess.BLACK, square))
            score += (white_attackers - black_attackers) * 2
        
        return score
    
    def _evaluate_mobility(self, board: chess.Board) -> float:
        """Evaluate piece mobility."""
        score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            color_factor = 1 if color == chess.WHITE else -1
            mobility = 0
            
            # Count legal moves (excluding king moves for speed)
            for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                pieces = board.pieces(piece_type, color)
                for piece_square in pieces:
                    attacks = board.attacks(piece_square)
                    mobility += len(attacks)
            
            score += mobility * 0.5 * color_factor
        
        return score
    
    def _basic_material_evaluation(self, board: chess.Board) -> float:
        """Basic material evaluation as fallback."""
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        
        return score if board.turn == chess.WHITE else -score
