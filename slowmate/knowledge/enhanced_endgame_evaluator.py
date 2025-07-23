"""
SlowMate v0.3.02 - Enhanced Endgame Intelligence System

This system implements advanced endgame evaluation focusing on:
1. King mobility reduction ("closing the box")
2. Rook cutting techniques 
3. Active king play
4. Pawn promotion priorities
5. Mate threat recognition

Key improvements:
- King activity bonus in endgames
- Opposition recognition
- Passed pawn advancement
- King safety vs activity trade-offs
- Advanced mate pattern recognition
"""

import chess
from chess import Board, Move, Color
from typing import Optional, Dict, List, Tuple, Any
import json
import os


class EnhancedEndgameEvaluator:
    """Enhanced endgame evaluation with advanced tactical awareness."""
    
    def __init__(self, data_dir: str = "data/endgames"):
        """
        Initialize enhanced endgame evaluator.
        
        Args:
            data_dir: Directory containing endgame pattern files
        """
        self.data_dir = data_dir
        self.enhanced_patterns = {}
        self.mate_patterns = {}
        self.is_loaded = False
        
        self._load_enhanced_patterns()
    
    def _load_enhanced_patterns(self):
        """Load enhanced endgame patterns."""
        try:
            # Load v0.3.02 enhanced patterns
            enhanced_file = os.path.join(self.data_dir, "enhanced_patterns_v0_3_02.json")
            if os.path.exists(enhanced_file):
                with open(enhanced_file, 'r') as f:
                    self.enhanced_patterns = json.load(f)
            
            # Load existing mate patterns
            mate_file = os.path.join(self.data_dir, "mate_patterns.json")
            if os.path.exists(mate_file):
                with open(mate_file, 'r') as f:
                    self.mate_patterns = json.load(f)
            
            self.is_loaded = True
            
        except Exception as e:
            print(f"Warning: Could not load enhanced endgame patterns: {e}")
            self.is_loaded = False
    
    def evaluate_endgame_position(self, board: Board) -> float:
        """
        Comprehensive endgame position evaluation.
        
        Args:
            board: Current chess position
            
        Returns:
            Endgame evaluation score (positive favors white)
        """
        if not self._is_endgame_position(board):
            return 0.0
        
        total_eval = 0.0
        
        # 1. King activity and centralization
        total_eval += self._evaluate_king_activity(board)
        
        # 2. King mobility and "closing the box" 
        total_eval += self._evaluate_king_mobility_control(board)
        
        # 3. Rook endgame patterns
        total_eval += self._evaluate_rook_endgame_patterns(board)
        
        # 4. Pawn promotion evaluation
        total_eval += self._evaluate_pawn_promotion_potential(board)
        
        # 5. Opposition and king positioning
        total_eval += self._evaluate_king_opposition(board)
        
        # 6. Mate threat recognition
        total_eval += self._evaluate_mate_threats(board)
        
        return total_eval
    
    def _is_endgame_position(self, board: Board) -> bool:
        """Determine if position qualifies as endgame."""
        # Count non-pawn, non-king pieces
        piece_count = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type not in [chess.KING, chess.PAWN]:
                piece_count += 1
        
        return piece_count <= 6
    
    def _evaluate_king_activity(self, board: Board) -> float:
        """Evaluate king activity and centralization in endgame."""
        score = 0.0
        
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is not None:
            # King centralization bonus
            white_centralization = self._calculate_king_centralization(white_king)
            score += white_centralization * 15  # Increased emphasis on active king
            
            # King advancement bonus (moving up the board)
            white_advancement = chess.square_rank(white_king)
            score += white_advancement * 5
        
        if black_king is not None:
            # King centralization bonus (negative for black)
            black_centralization = self._calculate_king_centralization(black_king)
            score -= black_centralization * 15
            
            # King advancement bonus (moving down the board for black)
            black_advancement = 7 - chess.square_rank(black_king)
            score -= black_advancement * 5
        
        return score
    
    def _calculate_king_centralization(self, king_square: int) -> float:
        """Calculate how centralized the king is."""
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        
        # Distance from center (3.5, 3.5)
        center_distance = abs(file - 3.5) + abs(rank - 3.5)
        
        # Convert to centralization score (higher is better)
        return max(0, 7 - center_distance)
    
    def _evaluate_king_mobility_control(self, board: Board) -> float:
        """Evaluate 'closing the box' - restricting opponent king mobility."""
        score = 0.0
        
        white_king_mobility = self._count_king_mobility(board, chess.WHITE)
        black_king_mobility = self._count_king_mobility(board, chess.BLACK)
        
        # Bonus for restricting opponent king mobility
        if black_king_mobility <= 3:  # Severely restricted
            score += 40
        elif black_king_mobility <= 5:  # Moderately restricted
            score += 20
        
        if white_king_mobility <= 3:  # Severely restricted
            score -= 40
        elif white_king_mobility <= 5:  # Moderately restricted
            score -= 20
        
        return score
    
    def _count_king_mobility(self, board: Board, color: Color) -> int:
        """Count legal king moves."""
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        mobility = 0
        for delta in [-9, -8, -7, -1, 1, 7, 8, 9]:
            target_square = king_square + delta
            if 0 <= target_square < 64:
                # Check board edge crossing
                king_file = chess.square_file(king_square)
                target_file = chess.square_file(target_square)
                if abs(target_file - king_file) <= 1:
                    move = chess.Move(king_square, target_square)
                    if move in board.legal_moves:
                        mobility += 1
        
        return mobility
    
    def _evaluate_rook_endgame_patterns(self, board: Board) -> float:
        """Evaluate rook endgame specific patterns."""
        score = 0.0
        
        # Check for rook cutting off patterns
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.ROOK:
                cutting_bonus = self._evaluate_rook_cutting_off(board, square, piece.color)
                if piece.color == chess.WHITE:
                    score += cutting_bonus
                else:
                    score -= cutting_bonus
        
        return score
    
    def _evaluate_rook_cutting_off(self, board: Board, rook_square: int, rook_color: Color) -> float:
        """Evaluate if rook is cutting off the opponent king."""
        opponent_king = board.king(not rook_color)
        if opponent_king is None:
            return 0.0
        
        rook_rank = chess.square_rank(rook_square)
        rook_file = chess.square_file(rook_square)
        king_rank = chess.square_rank(opponent_king)
        king_file = chess.square_file(opponent_king)
        
        # Check if rook cuts off king on rank or file
        if rook_rank == king_rank or rook_file == king_file:
            # Additional bonus if king is near edge
            edge_distance = min(king_rank, 7 - king_rank, king_file, 7 - king_file)
            return 30 + (3 - edge_distance) * 10
        
        return 0.0
    
    def _evaluate_pawn_promotion_potential(self, board: Board) -> float:
        """Enhanced pawn promotion evaluation."""
        score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                promotion_score = self._calculate_pawn_promotion_value(board, square, piece.color)
                if piece.color == chess.WHITE:
                    score += promotion_score
                else:
                    score -= promotion_score
        
        return score
    
    def _calculate_pawn_promotion_value(self, board: Board, pawn_square: int, pawn_color: Color) -> float:
        """Calculate promotion potential for a specific pawn."""
        rank = chess.square_rank(pawn_square)
        file = chess.square_file(pawn_square)
        
        if pawn_color == chess.WHITE:
            distance_to_promotion = 7 - rank
            advancement = rank
        else:
            distance_to_promotion = rank
            advancement = 7 - rank
        
        # Base score based on advancement
        base_score = advancement * 10
        
        # Huge bonus for pawns close to promotion
        if distance_to_promotion == 1:
            base_score += 200  # About to promote!
        elif distance_to_promotion == 2:
            base_score += 100  # Two moves to promotion
        elif distance_to_promotion == 3:
            base_score += 50   # Three moves to promotion
        
        # Check if pawn is passed
        if self._is_passed_pawn(board, pawn_square, pawn_color):
            base_score += 30
        
        # Check if pawn is protected
        if self._is_pawn_protected(board, pawn_square, pawn_color):
            base_score += 15
        
        return base_score
    
    def _is_passed_pawn(self, board: Board, pawn_square: int, pawn_color: Color) -> bool:
        """Check if pawn is passed (no opposing pawns blocking)."""
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        # Check files (own file and adjacent files)
        for check_file in [file - 1, file, file + 1]:
            if 0 <= check_file < 8:
                # Check ranks ahead of the pawn
                if pawn_color == chess.WHITE:
                    check_ranks = range(rank + 1, 8)
                else:
                    check_ranks = range(0, rank)
                
                for check_rank in check_ranks:
                    check_square = chess.square(check_file, check_rank)
                    piece = board.piece_at(check_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color != pawn_color:
                        return False
        
        return True
    
    def _is_pawn_protected(self, board: Board, pawn_square: int, pawn_color: Color) -> bool:
        """Check if pawn is protected by another pawn."""
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        # Check diagonal protection
        for delta_file in [-1, 1]:
            protect_file = file + delta_file
            if 0 <= protect_file < 8:
                if pawn_color == chess.WHITE:
                    protect_rank = rank - 1
                else:
                    protect_rank = rank + 1
                
                if 0 <= protect_rank < 8:
                    protect_square = chess.square(protect_file, protect_rank)
                    piece = board.piece_at(protect_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == pawn_color:
                        return True
        
        return False
    
    def _evaluate_king_opposition(self, board: Board) -> float:
        """Evaluate king opposition in endgames."""
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is None or black_king is None:
            return 0.0
        
        # Check for direct opposition
        opposition_score = self._calculate_opposition(white_king, black_king)
        
        # Bonus for having the opposition in the endgame
        if board.turn == chess.WHITE and opposition_score > 0:
            return 25  # White has opposition and it's white to move
        elif board.turn == chess.BLACK and opposition_score < 0:
            return -25  # Black has opposition and it's black to move
        
        return opposition_score * 10
    
    def _calculate_opposition(self, white_king: int, black_king: int) -> float:
        """Calculate opposition between kings."""
        w_file, w_rank = chess.square_file(white_king), chess.square_rank(white_king)
        b_file, b_rank = chess.square_file(black_king), chess.square_rank(black_king)
        
        file_diff = abs(w_file - b_file)
        rank_diff = abs(w_rank - b_rank)
        
        # Direct opposition: 2 squares apart on same rank/file
        if (file_diff == 0 and rank_diff == 2) or (rank_diff == 0 and file_diff == 2):
            return 1.0  # White has opposition
        
        # Distant opposition: even number of squares apart
        if (file_diff == 0 and rank_diff > 2 and rank_diff % 2 == 0) or \
           (rank_diff == 0 and file_diff > 2 and file_diff % 2 == 0):
            return 0.5  # Weaker opposition
        
        return 0.0
    
    def _evaluate_mate_threats(self, board: Board) -> float:
        """Evaluate immediate and near-term mate threats."""
        score = 0.0
        
        # Check for mate in 1
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                score += 1000 if board.turn == chess.BLACK else -1000  # Huge bonus for mate
            board.pop()
        
        # Check for back-rank weakness
        score += self._evaluate_back_rank_weakness(board)
        
        return score
    
    def _evaluate_back_rank_weakness(self, board: Board) -> float:
        """Evaluate back-rank mate potential."""
        score = 0.0
        
        # Check white's back rank (rank 0)
        white_king = board.king(chess.WHITE)
        if white_king is not None and chess.square_rank(white_king) == 0:
            # Check if king is trapped by its own pawns
            back_rank_escape = self._count_back_rank_escapes(board, white_king, chess.WHITE)
            if back_rank_escape <= 1:
                score -= 30  # Vulnerable to back-rank mate
        
        # Check black's back rank (rank 7)
        black_king = board.king(chess.BLACK)
        if black_king is not None and chess.square_rank(black_king) == 7:
            back_rank_escape = self._count_back_rank_escapes(board, black_king, chess.BLACK)
            if back_rank_escape <= 1:
                score += 30  # Black vulnerable to back-rank mate
        
        return score
    
    def _count_back_rank_escapes(self, board: Board, king_square: int, king_color: Color) -> int:
        """Count escape squares for king on back rank."""
        escapes = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check squares in front of the king
        if king_color == chess.WHITE:
            escape_rank = king_rank + 1
        else:
            escape_rank = king_rank - 1
        
        if 0 <= escape_rank < 8:
            for delta_file in [-1, 0, 1]:
                escape_file = king_file + delta_file
                if 0 <= escape_file < 8:
                    escape_square = chess.square(escape_file, escape_rank)
                    move = chess.Move(king_square, escape_square)
                    if move in board.legal_moves:
                        escapes += 1
        
        return escapes
    
    def get_endgame_move_suggestion(self, board: Board) -> Optional[Move]:
        """Get move suggestion based on endgame patterns."""
        if not self._is_endgame_position(board):
            return None
        
        best_move = None
        best_score = float('-inf')
        
        for move in board.legal_moves:
            # Evaluate move based on endgame criteria
            move_score = self._evaluate_endgame_move(board, move)
            
            if move_score > best_score:
                best_score = move_score
                best_move = move
        
        return best_move if best_score > 10 else None  # Only return if significantly good
    
    def _evaluate_endgame_move(self, board: Board, move: Move) -> float:
        """Evaluate a specific move in endgame context."""
        board.push(move)
        
        # Get position evaluation after move
        position_score = self.evaluate_endgame_position(board)
        
        move_score = 0.0
        
        # Bonus for moves that improve endgame factors
        piece = board.piece_at(move.to_square)
        
        if piece and piece.piece_type == chess.KING:
            # King activity bonus
            move_score += 10
            
        elif piece and piece.piece_type == chess.PAWN:
            # Pawn advancement bonus
            if piece.color == chess.WHITE:
                advance_bonus = chess.square_rank(move.to_square) * 5
            else:
                advance_bonus = (7 - chess.square_rank(move.to_square)) * 5
            move_score += advance_bonus
            
        elif piece and piece.piece_type == chess.ROOK:
            # Rook activity bonus
            move_score += 5
        
        board.pop()
        
        return position_score + move_score
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get endgame evaluator statistics."""
        return {
            'enhanced_patterns_loaded': len(self.enhanced_patterns),
            'mate_patterns_loaded': len(self.mate_patterns),
            'is_loaded': self.is_loaded,
            'features': [
                'king_mobility_control',
                'rook_cutting_patterns', 
                'pawn_promotion_intelligence',
                'king_opposition_evaluation',
                'mate_threat_recognition'
            ]
        }
