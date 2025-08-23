"""
SlowMate Chess Engine - Evaluation Module
Handles position evaluation
Version: 1.0.0-BETA
"""

import chess

class Evaluator:
    """Position evaluation with basic material and piece-square tables."""
    
    def __init__(self):
        """Initialize evaluator with piece values and piece-square tables."""
        # Material values in centipawns (standard scale)
        self.piece_values = {
            chess.PAWN: 100,     # Base unit of material
            chess.KNIGHT: 325,   # Slightly better than bishop in closed positions
            chess.BISHOP: 325,   # Equal to knight but different strengths
            chess.ROOK: 500,     # Worth roughly 5 pawns
            chess.QUEEN: 975,    # Worth slightly less than 2 rooks
            chess.KING: 20000    # Effectively infinite value
        }
        
        # Initialize piece-square tables
        self.pst = self._init_piece_square_tables()
        
        # Evaluation constants and weights
        self.CHECKMATE_SCORE = 30000      # Higher than any possible material score
        self.STALEMATE_SCORE = 0          # Draw score
        self.MOBILITY_WEIGHT = 5          # Lower weight for mobility (was too high)
        self.CENTER_CONTROL_WEIGHT = 15   # Reduced from 30 to balance with material
        
        # Evaluation hierarchy weights (higher = more important)
        self.MATERIAL_WEIGHT = 1.0        # Base material value
        self.PIECE_POSITION_WEIGHT = 0.5  # Position value from PST
        self.MOBILITY_FACTOR = 0.3        # Overall mobility importance
        self.KING_SAFETY_WEIGHT = 0.8     # High priority for king safety
        
        # No need to scale values up - using standard centipawn scale
        
    def evaluate(self, board, material_only: bool = False) -> int:
        """Evaluate position, returning centipawn score from side-to-move perspective.

        Args:
            board: Either a python-chess Board or our wrapper Board
            material_only: If True, skip all non-material terms and terminal checks
        """
        # Normalize to python-chess board
        board_obj = board.board if hasattr(board, 'board') else board

        # Pure material fast path (used by tests); always White perspective
        if material_only:
            white_material = sum(len(board_obj.pieces(pt, chess.WHITE)) * self.piece_values[pt]
                                 for pt in self.piece_values)
            black_material = sum(len(board_obj.pieces(pt, chess.BLACK)) * self.piece_values[pt]
                                 for pt in self.piece_values)
            return white_material - black_material

        # Terminal detection
        if board_obj.is_checkmate():
            ply_to_mate = len(board_obj.move_stack) + 1
            mate_score = self.CHECKMATE_SCORE - ply_to_mate
            return -mate_score
        if board_obj.is_stalemate() or board_obj.is_insufficient_material():
            return self.STALEMATE_SCORE

        # Material
        if hasattr(board, 'get_material_count') and not isinstance(board, chess.Board):
            white_material, black_material = board.get_material_count()
        else:
            white_material = sum(len(board_obj.pieces(pt, chess.WHITE)) * self.piece_values[pt]
                                 for pt in self.piece_values)
            black_material = sum(len(board_obj.pieces(pt, chess.BLACK)) * self.piece_values[pt]
                                 for pt in self.piece_values)
        material_score = (white_material - black_material) * self.MATERIAL_WEIGHT

        # Positional terms
        position_score = self._evaluate_piece_squares(board_obj) * self.PIECE_POSITION_WEIGHT
        mobility_score = self._evaluate_mobility(board_obj) * self.MOBILITY_FACTOR
        king_safety_score = self._evaluate_king_safety(board_obj) * self.KING_SAFETY_WEIGHT

        total = material_score + position_score + mobility_score + king_safety_score
        final_score = int(round(total))
        return final_score if board_obj.turn else -final_score
        
    def _evaluate_piece_squares(self, board_obj):
        """Evaluate piece positioning using piece-square tables."""
        score = 0
        
        for square in chess.SQUARES:
            piece = board_obj.piece_at(square)
            if piece is None:
                continue
                
            if piece.color == chess.WHITE:
                score += self.pst[piece.piece_type][square]
            else:
                score -= self.pst[piece.piece_type][chess.square_mirror(square)]
                
        return score
        
    def _evaluate_mobility(self, board_obj):
        """Evaluate piece mobility and control of key squares."""
        original_turn = board_obj.turn
        score = 0
        
        try:
            # Count white moves and central control
            board_obj.turn = chess.WHITE
            white_moves = list(board_obj.legal_moves)
            white_mobility = len(white_moves)
            white_central = sum(1 for m in white_moves if 2 <= chess.square_rank(m.to_square) <= 5 
                              and 2 <= chess.square_file(m.to_square) <= 5)
            
            # Count black moves and central control
            board_obj.turn = chess.BLACK
            black_moves = list(board_obj.legal_moves)
            black_mobility = len(black_moves)
            black_central = sum(1 for m in black_moves if 2 <= chess.square_rank(m.to_square) <= 5 
                              and 2 <= chess.square_file(m.to_square) <= 5)
            
            # Combine mobility and central control with proper weights
            score = (white_mobility - black_mobility) * self.MOBILITY_WEIGHT
            score += (white_central - black_central) * self.CENTER_CONTROL_WEIGHT
            
        finally:
            # Always restore the original turn
            board_obj.turn = original_turn
            
        return score
        
    def _evaluate_king_safety(self, board_obj):
        """Evaluate king safety and attack potential."""
        def analyze_king_safety(color):
            """Analyze safety of king of given color."""
            king_square = board_obj.king(color)
            if king_square is None:
                return 0
                
            safety = 0
            
            # Define king zone squares
            rank, file = chess.square_rank(king_square), chess.square_file(king_square)
            zone_squares = []
            
            # Add squares around king to zone
            for r in range(max(0, rank - 1), min(8, rank + 2)):
                for f in range(max(0, file - 1), min(8, file + 2)):
                    zone_squares.append(chess.square(f, r))
                    
            # Count defenders and attackers
            defenders = 0
            attackers = 0
            
            for square in zone_squares:
                piece = board_obj.piece_at(square)
                if piece is not None:
                    if piece.color == color:
                        # Value defenders based on piece type
                        if piece.piece_type == chess.PAWN:
                            defenders += 1
                        elif piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                            defenders += 2
                        elif piece.piece_type == chess.ROOK:
                            defenders += 3
                        elif piece.piece_type == chess.QUEEN:
                            defenders += 4
                    else:
                        # Value attackers based on piece type
                        if piece.piece_type == chess.PAWN:
                            attackers += 1
                        elif piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                            attackers += 3
                        elif piece.piece_type == chess.ROOK:
                            attackers += 4
                        elif piece.piece_type == chess.QUEEN:
                            attackers += 6
                            
            # Calculate safety score
            safety = defenders * 10 - attackers * 15
            
            # Penalize exposed king
            if len(zone_squares) < 9:  # King near edge
                safety -= 15
                
            return safety
            
        # Evaluate both kings
        white_safety = analyze_king_safety(chess.WHITE)
        black_safety = analyze_king_safety(chess.BLACK)
        
        # Return safety differential
        return white_safety - black_safety
        
    def _init_piece_square_tables(self):
        """Initialize piece-square tables."""
        # Values in centipawns
        pawn_table = [
             0,   0,   0,   0,   0,   0,   0,   0,
           500, 500, 500, 500, 500, 500, 500, 500,
           100, 100, 200, 300, 300, 200, 100, 100,
            50,  50, 100, 250, 250, 100,  50,  50,
             0,   0,   0, 200, 200,   0,   0,   0,
            50, -50,-100,   0,   0,-100, -50,  50,
            50, 100, 100,-200,-200, 100, 100,  50,
             0,   0,   0,   0,   0,   0,   0,   0
        ]
        
        knight_table = [
            -500,-400,-300,-300,-300,-300,-400,-500,
            -400,-200,   0,   0,   0,   0,-200,-400,
            -300,   0, 100, 150, 150, 100,   0,-300,
            -300,  50, 150, 200, 200, 150,  50,-300,
            -300,   0, 150, 200, 200, 150,   0,-300,
            -300,  50, 100, 150, 150, 100,  50,-300,
            -400,-200,   0,  50,  50,   0,-200,-400,
            -500,-400,-300,-300,-300,-300,-400,-500
        ]
        
        bishop_table = [
            -200,-100,-100,-100,-100,-100,-100,-200,
            -100,   0,   0,   0,   0,   0,   0,-100,
            -100,   0,  50, 100, 100,  50,   0,-100,
            -100,  50,  50, 100, 100,  50,  50,-100,
            -100,   0, 100, 100, 100, 100,   0,-100,
            -100, 100, 100, 100, 100, 100, 100,-100,
            -100,  50,   0,   0,   0,   0,  50,-100,
            -200,-100,-100,-100,-100,-100,-100,-200
        ]
        
        rook_table = [
             0,   0,   0,   0,   0,   0,   0,   0,
            50, 100, 100, 100, 100, 100, 100,  50,
           -50,   0,   0,   0,   0,   0,   0, -50,
           -50,   0,   0,   0,   0,   0,   0, -50,
           -50,   0,   0,   0,   0,   0,   0, -50,
           -50,   0,   0,   0,   0,   0,   0, -50,
           -50,   0,   0,   0,   0,   0,   0, -50,
             0,   0,   0,  50,  50,   0,   0,   0
        ]
        
        queen_table = [
            -200,-100,-100, -50, -50,-100,-100,-200,
            -100,   0,   0,   0,   0,   0,   0,-100,
            -100,   0,  50,  50,  50,  50,   0,-100,
             -50,   0,  50,  50,  50,  50,   0, -50,
               0,   0,  50,  50,  50,  50,   0, -50,
            -100,  50,  50,  50,  50,  50,   0,-100,
            -100,   0,  50,   0,   0,   0,   0,-100,
            -200,-100,-100, -50, -50,-100,-100,-200
        ]
        
        king_table = [
            -300,-400,-400,-500,-500,-400,-400,-300,
            -300,-400,-400,-500,-500,-400,-400,-300,
            -300,-400,-400,-500,-500,-400,-400,-300,
            -300,-400,-400,-500,-500,-400,-400,-300,
            -200,-300,-300,-400,-400,-300,-300,-200,
            -100,-200,-200,-200,-200,-200,-200,-100,
             200, 200,   0,   0,   0,   0, 200, 200,
             200, 300, 100,   0,   0, 100, 300, 200
        ]
        
        return {
            chess.PAWN: pawn_table,
            chess.KNIGHT: knight_table,
            chess.BISHOP: bishop_table,
            chess.ROOK: rook_table,
            chess.QUEEN: queen_table,
            chess.KING: king_table
        }
