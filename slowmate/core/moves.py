"""
SlowMate Chess Engine - Move Generation Module
Handles move generation and move ordering
Version: 1.0.0-BETA
"""

import chess


class MoveGenerator:
    """Handles move generation and basic move ordering."""
    
    def __init__(self, board):
        """Initialize move generator with a board instance."""
        self.board = board
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
    def get_legal_moves(self):
        """Get list of legal moves in current position."""
        return self.board.get_legal_moves()
        
    def get_ordered_moves(self):
        """Get legal moves with basic ordering for better search efficiency."""
        moves = self.get_legal_moves()
        scored_moves = []
        
        for move in moves:
            # Special case: pawn captures queen gets highest priority
            if self.board.board.is_capture(move):
                victim = self.board.board.piece_at(move.to_square)
                attacker = self.board.board.piece_at(move.from_square)
                if (victim and attacker and 
                    victim.piece_type == chess.QUEEN and 
                    attacker.piece_type == chess.PAWN):
                    scored_moves.append((move, 1000000))  # Highest possible score
                    continue
                    
            # Normal move scoring
            score = self._score_move(move)
            scored_moves.append((move, score))
            
        # Sort moves by score, highest first
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]
        
    def _score_move(self, move):
        """Score moves for ordering based on likely quality."""
        # Move scoring constants
        QUEEN_PROMOTION = 100000    # Highest regular priority
        CAPTURE_QUEEN = 90000      # Capturing queen (regular captures)
        CAPTURE_ROOK = 80000       # Capturing rook
        CAPTURE_MINOR = 70000      # Capturing bishop/knight
        CAPTURE_PAWN = 60000       # Capturing pawn
        CHECK_BONUS = 50000        # Giving check
        DEVELOP_BONUS = 40000      # Development in opening
        CENTER_BONUS = 30000       # Center control
        
        score = 0
        board = self.board.board
        
        # Queen promotions always highest
        if move.promotion == chess.QUEEN:
            score += QUEEN_PROMOTION
            
        # Special case: Pawn captures queen
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and victim.piece_type == chess.QUEEN and attacker.piece_type == chess.PAWN:
                return 1000000  # Immediate highest priority for pawn takes queen
                
        # Other captures
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                victim_value = self._get_piece_value(victim.piece_type)
                attacker_value = self._get_piece_value(attacker.piece_type)
                capture_score = victim_value * 100 - attacker_value
                score = CAPTURE_QUEEN + capture_score
                
        # Check bonus
        if board.gives_check(move):
            score += CHECK_BONUS
            
        # Development and center control in opening
        if self.board.get_phase() == 'opening':
            piece = board.piece_at(move.from_square)
            if piece:
                # Development bonus for moving pieces out
                from_back_rank = (piece.color == chess.WHITE and 
                                chess.square_rank(move.from_square) == 0) or \
                               (piece.color == chess.BLACK and 
                                chess.square_rank(move.from_square) == 7)
                if from_back_rank and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                    score += DEVELOP_BONUS
                    
                # Center control bonus
                to_rank = chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                if 2 <= to_rank <= 5 and 2 <= to_file <= 5:
                    score += CENTER_BONUS
            
        # Check moves - using native python-chess gives_check
        if board.gives_check(move):
            score += 1000  # Higher priority for check moves
        
        # Central squares control and development in early game
        if self.board.get_phase() == 'opening':
            to_rank, to_file = chess.square_rank(move.to_square), chess.square_file(move.to_square)
            from_rank, from_file = chess.square_rank(move.from_square), chess.square_file(move.from_square)
            
            # Bonus for controlling center
            if 2 <= to_rank <= 5 and 2 <= to_file <= 5:
                score += 100  # Increased priority for central control
                
            # Development bonus for knights and bishops
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                if from_rank in [0, 7] and 2 <= to_rank <= 5:
                    score += 80  # Development bonus
                
        return score
        
    @staticmethod
    def _get_piece_value(piece_type):
        """Get the basic value of a piece in centipawns."""
        values = {
            chess.PAWN: 1000,
            chess.KNIGHT: 3200,
            chess.BISHOP: 3300,
            chess.ROOK: 5000,
            chess.QUEEN: 9000,
            chess.KING: 20000
        }
        return values.get(piece_type, 0)
