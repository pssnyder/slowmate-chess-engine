#!/usr/bin/env python3
"""
SlowMate v0.4.07 - Advanced Search Framework
Modern chess engine search with NegaScout, comprehensive move ordering, and modular evaluation.

Key Features:
- NegaScout (Principal Variation Search) with null window search
- Advanced move ordering with SEE (Static Exchange Evaluation)
- Null move pruning with verification
- Quiescence search for tactical positions
- Modular evaluation framework for future neural network integration
- Contempt factor to avoid draws and seek initiative
- Genetic algorithm hooks for self-tuning parameters
"""

import chess
import time
import random
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    """Search node types for transposition table."""
    EXACT = "exact"      # Exact score
    LOWER_BOUND = "lower"  # Beta cutoff (score >= beta)
    UPPER_BOUND = "upper"  # Alpha cutoff (score <= alpha)

@dataclass
class SearchParameters:
    """Tunable search parameters for genetic algorithm optimization."""
    # NegaScout parameters
    null_move_reduction: int = 2
    null_move_verification_depth: int = 6
    null_move_min_depth: int = 3
    
    # Late Move Reduction parameters
    lmr_min_depth: int = 3
    lmr_min_moves: int = 4
    lmr_reduction_factor: float = 0.75
    
    # Quiescence parameters
    quiescence_max_depth: int = 10
    delta_pruning_margin: int = 200
    
    # Evaluation parameters
    contempt_factor: int = 25  # Centipawns to avoid draws
    initiative_bonus: int = 15  # Bonus for aggressive moves
    tempo_bonus: int = 10      # Bonus for gaining tempo
    
    # SEE parameters
    see_prune_threshold: int = -100  # Prune bad captures
    see_quiet_threshold: int = 0     # Threshold for quiet moves

class StaticExchangeEvaluator:
    """Static Exchange Evaluation for move ordering and pruning."""
    
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    @classmethod
    def evaluate(cls, board: chess.Board, move: chess.Move) -> int:
        """
        Calculate Static Exchange Evaluation for a move.
        Returns the material gain/loss from the exchange.
        """
        if not board.is_capture(move):
            return 0
        
        # Get attacking and defending pieces
        to_square = move.to_square
        from_square = move.from_square
        
        # Value of captured piece
        captured_piece = board.piece_at(to_square)
        if not captured_piece:
            return 0
        
        gain = cls.PIECE_VALUES[captured_piece.piece_type]
        
        # Value of attacking piece
        attacking_piece = board.piece_at(from_square)
        if not attacking_piece:
            return gain
        
        # Simple SEE: assume we lose the attacking piece
        attacking_value = cls.PIECE_VALUES[attacking_piece.piece_type]
        
        # Get all attackers to this square
        board.push(move)
        attackers = board.attackers(not board.turn, to_square)
        board.pop()
        
        if not attackers:
            return gain  # No recapture possible
        
        # Find least valuable attacker for recapture
        least_valuable = None
        min_value = float('inf')
        
        for attacker_square in attackers:
            piece = board.piece_at(attacker_square)
            if piece and cls.PIECE_VALUES[piece.piece_type] < min_value:
                min_value = cls.PIECE_VALUES[piece.piece_type]
                least_valuable = piece
        
        if least_valuable:
            # Simplified SEE: gain - attacking_piece_value + defending_piece_value
            return gain - attacking_value + min_value
        
        return gain - attacking_value

class MoveOrderer:
    """Advanced move ordering for optimal alpha-beta performance."""
    
    def __init__(self, parameters: SearchParameters):
        self.params = parameters
        self.killer_moves: Dict[int, List[chess.Move]] = {}  # Killer moves by depth
        self.history_scores: Dict[str, int] = {}  # History heuristic
        self.see = StaticExchangeEvaluator()
    
    def order_moves(self, board: chess.Board, moves: List[chess.Move], 
                   depth: int, pv_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """Order moves for optimal search performance."""
        move_scores = []
        
        for move in moves:
            score = self._score_move(board, move, depth, pv_move)
            move_scores.append((score, move))
        
        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in move_scores]
    
    def _score_move(self, board: chess.Board, move: chess.Move, 
                   depth: int, pv_move: Optional[chess.Move]) -> int:
        """Score a move for ordering purposes."""
        score = 0
        
        # 1. PV move gets highest priority
        if pv_move and move == pv_move:
            return 10000
        
        # 2. Captures with SEE evaluation
        if board.is_capture(move):
            see_score = self.see.evaluate(board, move)
            if see_score >= 0:
                score += 8000 + see_score  # Good captures
            else:
                score += 2000 + see_score  # Bad captures (but still try them)
        
        # 3. Promotions
        if move.promotion:
            promotion_value = self.see.PIECE_VALUES.get(move.promotion, 0)
            score += 7000 + promotion_value
        
        # 4. Killer moves
        killers = self.killer_moves.get(depth, [])
        if move in killers:
            score += 6000 - killers.index(move) * 100
        
        # 5. Checks
        board.push(move)
        if board.is_check():
            score += 5000
            # Bonus for checks that ask questions
            if len(list(board.legal_moves)) < 10:  # Forcing check
                score += self.params.initiative_bonus
        board.pop()
        
        # 6. Castling (development and safety)
        if board.is_castling(move):
            score += 4000
        
        # 7. History heuristic
        move_key = move.uci()
        history_score = self.history_scores.get(move_key, 0)
        score += min(history_score // 10, 1000)  # Cap history bonus
        
        # 8. Initiative and tempo bonuses
        if self._move_gains_tempo(board, move):
            score += self.params.tempo_bonus
        
        if self._move_takes_initiative(board, move):
            score += self.params.initiative_bonus
        
        # 9. Central piece development
        if move.from_square in [chess.B1, chess.G1, chess.B8, chess.G8]:  # Knights
            if move.to_square in [chess.C3, chess.D4, chess.E4, chess.F3, 
                                chess.C6, chess.D5, chess.E5, chess.F6]:  # Central squares
                score += 200
        
        # 10. Penalty for moving pieces multiple times in opening
        piece = board.piece_at(move.from_square)
        if piece and board.fullmove_number <= 10:
            # Check if piece has moved before (simplified)
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP] and move.from_square not in [
                chess.B1, chess.G1, chess.C1, chess.F1, chess.B8, chess.G8, chess.C8, chess.F8
            ]:
                score -= 100  # Penalty for moving developed pieces again
        
        return score
    
    def _move_gains_tempo(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move gains tempo (attacks opponent pieces)."""
        board.push(move)
        gains_tempo = bool(board.attackers(board.turn, move.to_square))
        board.pop()
        return gains_tempo
    
    def _move_takes_initiative(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move takes initiative (creates threats)."""
        board.push(move)
        
        # Count attacking moves available
        attacking_moves = 0
        for legal_move in board.legal_moves:
            if board.is_capture(legal_move) or board.gives_check(legal_move):
                attacking_moves += 1
        
        board.pop()
        return attacking_moves >= 3  # Has multiple tactical options
    
    def update_killers(self, depth: int, move: chess.Move):
        """Update killer moves for this depth."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        killers = self.killer_moves[depth]
        if move not in killers:
            killers.insert(0, move)
            if len(killers) > 2:  # Keep only 2 killers per depth
                killers.pop()
    
    def update_history(self, move: chess.Move, depth: int, node_type: NodeType):
        """Update history heuristic scores."""
        move_key = move.uci()
        bonus = depth * depth  # Deeper moves get higher scores
        
        if node_type == NodeType.LOWER_BOUND:  # Beta cutoff
            bonus *= 2
        
        self.history_scores[move_key] = self.history_scores.get(move_key, 0) + bonus
        
        # Decay old entries to prevent overflow
        if len(self.history_scores) > 10000:
            for key in list(self.history_scores.keys()):
                self.history_scores[key] //= 2
                if self.history_scores[key] == 0:
                    del self.history_scores[key]

class AdvancedTranspositionTable:
    """Enhanced transposition table with aging and better replacement scheme."""
    
    def __init__(self, size_mb: int = 64):
        self.max_entries = (size_mb * 1024 * 1024) // 48  # ~48 bytes per entry
        self.table: Dict[int, Dict[str, Any]] = {}
        self.hits = 0
        self.lookups = 0
        self.generation = 0  # For aging entries
    
    def store(self, position_hash: int, depth: int, score: int, 
              node_type: NodeType, best_move: Optional[str] = None, 
              search_depth: int = 0):
        """Store position with enhanced replacement scheme."""
        
        # Replace if: 1) New entry, 2) Deeper search, 3) Same depth but newer generation
        should_replace = True
        
        if position_hash in self.table:
            existing = self.table[position_hash]
            if (existing['depth'] > depth and 
                existing['generation'] == self.generation):
                should_replace = False
        
        if should_replace:
            # Implement aging - remove old entries if table is full
            if len(self.table) >= self.max_entries:
                self._age_table()
            
            self.table[position_hash] = {
                'depth': depth,
                'score': score,
                'node_type': node_type.value,
                'best_move': best_move,
                'search_depth': search_depth,
                'generation': self.generation,
                'access_count': 1
            }
    
    def lookup(self, position_hash: int, depth: int, alpha: int, beta: int) -> Optional[Tuple[int, Optional[str]]]:
        """Enhanced lookup with statistics tracking."""
        self.lookups += 1
        
        if position_hash not in self.table:
            return None
        
        entry = self.table[position_hash]
        entry['access_count'] += 1
        
        # Check depth sufficiency
        if entry['depth'] < depth:
            return None
        
        self.hits += 1
        score = entry['score']
        node_type = NodeType(entry['node_type'])
        
        # Check if we can use this score
        if node_type == NodeType.EXACT:
            return score, entry['best_move']
        elif node_type == NodeType.LOWER_BOUND and score >= beta:
            return score, entry['best_move']
        elif node_type == NodeType.UPPER_BOUND and score <= alpha:
            return score, entry['best_move']
        
        return None
    
    def _age_table(self):
        """Age table entries and remove old/unused ones."""
        self.generation += 1
        
        # Remove entries from old generations or with low access counts
        to_remove = []
        for key, entry in self.table.items():
            if (entry['generation'] < self.generation - 2 or 
                entry['access_count'] < 2):
                to_remove.append(key)
        
        for key in to_remove[:len(to_remove)//2]:  # Remove half of old entries
            del self.table[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive table statistics."""
        hit_rate = (self.hits * 100) // max(self.lookups, 1)
        hash_full = min(1000, (len(self.table) * 1000) // self.max_entries)
        
        return {
            'entries': len(self.table),
            'max_entries': self.max_entries,
            'hits': self.hits,
            'lookups': self.lookups,
            'hit_rate': hit_rate,
            'hash_full': hash_full,
            'generation': self.generation
        }

class QuiescenceSearch:
    """Quiescence search for tactical evaluation at leaf nodes."""
    
    def __init__(self, parameters: SearchParameters, move_orderer: MoveOrderer, 
                 evaluator: Callable):
        self.params = parameters
        self.move_orderer = move_orderer
        self.evaluator = evaluator
        self.nodes_searched = 0
    
    def search(self, board: chess.Board, alpha: int, beta: int, depth: int = 0) -> int:
        """Quiescence search to resolve tactical sequences."""
        self.nodes_searched += 1
        
        # Terminal position checks
        if board.is_checkmate():
            return -30000 + depth
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Max depth reached
        if depth >= self.params.quiescence_max_depth:
            return self.evaluator(board)
        
        # Stand pat evaluation
        stand_pat = self.evaluator(board)
        
        # Beta cutoff
        if stand_pat >= beta:
            return beta
        
        # Delta pruning - if we're way behind, don't search further
        if stand_pat < alpha - self.params.delta_pruning_margin:
            return alpha
        
        # Update alpha
        alpha = max(alpha, stand_pat)
        
        # Generate and order captures only
        captures = [move for move in board.legal_moves if board.is_capture(move)]
        if not captures:
            return stand_pat
        
        # Order captures by SEE
        captures = self.move_orderer.order_moves(board, captures, depth)
        
        for move in captures:
            # SEE pruning - skip obviously bad captures
            see_score = StaticExchangeEvaluator.evaluate(board, move)
            if see_score < self.params.see_prune_threshold:
                continue
            
            board.push(move)
            score = -self.search(board, -beta, -alpha, depth + 1)
            board.pop()
            
            if score >= beta:
                return beta
            
            alpha = max(alpha, score)
        
        return alpha

# Test the advanced search framework
def test_advanced_search():
    """Test the new advanced search components."""
    print("🧪 Testing Advanced Search Framework")
    print("=" * 50)
    
    # Test 1: Static Exchange Evaluation
    print("\n1. Testing Static Exchange Evaluation...")
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 4")
    
    # Test a simple capture
    move = chess.Move.from_uci("f3e5")  # Knight takes pawn
    see_score = StaticExchangeEvaluator.evaluate(board, move)
    print(f"   Knight takes pawn SEE: {see_score}")
    
    # Test 2: Move Ordering
    print("\n2. Testing Move Ordering...")
    params = SearchParameters()
    orderer = MoveOrderer(params)
    
    moves = list(board.legal_moves)
    ordered_moves = orderer.order_moves(board, moves, 4)
    
    print(f"   Original moves: {len(moves)}")
    print(f"   Top 3 ordered moves: {[move.uci() for move in ordered_moves[:3]]}")
    
    # Test 3: Transposition Table
    print("\n3. Testing Advanced Transposition Table...")
    tt = AdvancedTranspositionTable(16)
    
    test_hash = hash(board.fen())
    tt.store(test_hash, 5, 150, NodeType.EXACT, "e2e4")
    
    result = tt.lookup(test_hash, 4, -100, 200)
    if result:
        print(f"   TT lookup successful: score={result[0]}, move={result[1]}")
    
    stats = tt.get_stats()
    print(f"   TT hit rate: {stats['hit_rate']}%")
    
    print("\n✅ Advanced Search Framework tests completed!")

if __name__ == "__main__":
    test_advanced_search()
