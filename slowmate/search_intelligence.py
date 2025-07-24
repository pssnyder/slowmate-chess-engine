#!/usr/bin/env python3
"""
SlowMate v0.4.06 - Search Intelligence & Hash Tables Implementation
Phase 2 of v0.5.0 development: Advanced search algorithms and performance.
"""

import chess
import time
from typing import Dict, List, Optional, Tuple, Any

class TranspositionTable:
    """Simple transposition table for position caching."""
    
    def __init__(self, size_mb: int = 16):
        """Initialize transposition table."""
        # Estimate entries based on size (rough calculation)
        self.max_entries = (size_mb * 1024 * 1024) // 32  # ~32 bytes per entry
        self.table: Dict[int, Dict[str, Any]] = {}
        self.hits = 0
        self.lookups = 0
        
    def store(self, position_hash: int, depth: int, score: int, node_type: str, best_move: Optional[str] = None):
        """Store position evaluation in hash table."""
        if len(self.table) >= self.max_entries:
            # Simple replacement: remove oldest entries (could be improved)
            oldest_key = next(iter(self.table))
            del self.table[oldest_key]
        
        self.table[position_hash] = {
            'depth': depth,
            'score': score, 
            'node_type': node_type,  # 'exact', 'lower', 'upper'
            'best_move': best_move,
            'time': time.time()
        }
    
    def lookup(self, position_hash: int, depth: int, alpha: int, beta: int) -> Optional[Tuple[int, Optional[str]]]:
        """Lookup position in hash table."""
        self.lookups += 1
        
        if position_hash not in self.table:
            return None
        
        entry = self.table[position_hash]
        
        # Check if stored depth is sufficient
        if entry['depth'] < depth:
            return None
        
        self.hits += 1
        score = entry['score']
        node_type = entry['node_type']
        
        # Check if we can use this score
        if node_type == 'exact':
            return score, entry['best_move']
        elif node_type == 'lower' and score >= beta:
            return score, entry['best_move']
        elif node_type == 'upper' and score <= alpha:
            return score, entry['best_move']
        
        # Can't use score, but return best move if available
        return None
    
    def get_hash_full(self) -> int:
        """Get hash table fullness in permille (0-1000)."""
        if self.max_entries == 0:
            return 0
        return min(1000, (len(self.table) * 1000) // self.max_entries)
    
    def clear(self):
        """Clear the hash table."""
        self.table.clear()
        self.hits = 0
        self.lookups = 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get hash table statistics."""
        hit_rate = (self.hits * 100) // max(self.lookups, 1)
        return {
            'entries': len(self.table),
            'max_entries': self.max_entries,
            'hits': self.hits,
            'lookups': self.lookups,
            'hit_rate': hit_rate,
            'hash_full': self.get_hash_full()
        }

class SearchIntelligence:
    """Advanced search algorithms with alpha-beta pruning."""
    
    def __init__(self, transposition_table: TranspositionTable):
        """Initialize search intelligence."""
        self.tt = transposition_table
        self.nodes_searched = 0
        self.current_move = None
        self.current_move_number = 0
        
        # Search statistics
        self.cutoffs = 0
        self.search_start_time = 0
        
    def search_with_alpha_beta(self, board: chess.Board, depth: int, alpha: int = -50000, beta: int = 50000, 
                              maximize: bool = True, info_callback=None) -> Tuple[int, Optional[chess.Move]]:
        """Alpha-beta search with transposition table."""
        self.nodes_searched += 1
        
        # Check for terminal positions
        if board.is_checkmate():
            return (-30000 + (self.nodes_searched % 100)) if maximize else (30000 - (self.nodes_searched % 100)), None
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0, None
        
        # Base case
        if depth <= 0:
            return self._evaluate_position(board), None
        
        # Transposition table lookup
        position_hash = hash(board.fen())
        tt_result = self.tt.lookup(position_hash, depth, alpha, beta)
        if tt_result and tt_result[0] is not None:
            return tt_result[0], chess.Move.from_uci(tt_result[1]) if tt_result[1] else None
        
        best_move = None
        best_score = -50000 if maximize else 50000
        original_alpha = alpha
        
        # Get ordered moves
        moves = self._order_moves(board, list(board.legal_moves))
        
        for i, move in enumerate(moves):
            # Update current move info for UCI
            if info_callback and depth > 1:
                self.current_move = move.uci()
                self.current_move_number = i + 1
                info_callback(self.current_move, self.current_move_number)
            
            board.push(move)
            
            if maximize:
                score, _ = self.search_with_alpha_beta(board, depth - 1, alpha, beta, False, info_callback)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                score, _ = self.search_with_alpha_beta(board, depth - 1, alpha, beta, True, info_callback)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)
            
            board.pop()
            
            # Alpha-beta cutoff
            if beta <= alpha:
                self.cutoffs += 1
                break
        
        # Store in transposition table
        if best_move:
            node_type = 'exact'
            if best_score <= original_alpha:
                node_type = 'upper'
            elif best_score >= beta:
                node_type = 'lower'
            
            self.tt.store(position_hash, depth, best_score, node_type, best_move.uci())
        
        return best_score, best_move
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Order moves for better alpha-beta performance."""
        # Simple move ordering: captures first, then quiet moves
        captures = []
        quiet_moves = []
        
        for move in moves:
            if board.is_capture(move):
                captures.append(move)
            else:
                quiet_moves.append(move)
        
        # Sort captures by victim value (simple MVV)
        captures.sort(key=lambda m: self._get_capture_value(board, m), reverse=True)
        
        return captures + quiet_moves
    
    def _get_capture_value(self, board: chess.Board, move: chess.Move) -> int:
        """Get capture value for move ordering."""
        piece_values = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}  # P, N, B, R, Q, K
        
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            return piece_values.get(captured_piece.piece_type, 0)
        return 0
    
    def _evaluate_position(self, board: chess.Board) -> int:
        """Simple position evaluation."""
        if board.is_checkmate():
            return -30000 if board.turn else 30000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Material evaluation
        piece_values = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}
        score = 0
        
        for piece_type in range(1, 7):
            white_pieces = len(board.pieces(piece_type, True))
            black_pieces = len(board.pieces(piece_type, False))
            score += (white_pieces - black_pieces) * piece_values[piece_type]
        
        return score if board.turn else -score
    
    def get_search_stats(self) -> Dict[str, int]:
        """Get search statistics."""
        return {
            'nodes_searched': self.nodes_searched,
            'cutoffs': self.cutoffs,
            'current_move': self.current_move or "",
            'current_move_number': self.current_move_number
        }
    
    def reset_stats(self):
        """Reset search statistics."""
        self.nodes_searched = 0
        self.cutoffs = 0
        self.current_move = None
        self.current_move_number = 0

# Test the new search implementation
def test_search_intelligence():
    """Test the new search algorithms."""
    print("🧪 Testing Search Intelligence & Hash Tables")
    print("=" * 50)
    
    # Test 1: Basic alpha-beta vs minimax comparison
    print("\n1. Testing Alpha-Beta Performance...")
    
    board = chess.Board()
    tt = TranspositionTable(16)  # 16MB hash table
    search = SearchIntelligence(tt)
    
    # Test search
    start_time = time.time()
    score, best_move = search.search_with_alpha_beta(board, 4)
    search_time = time.time() - start_time
    
    stats = search.get_search_stats()
    tt_stats = tt.get_stats()
    
    print(f"   Best move: {best_move}")
    print(f"   Score: {score}")
    print(f"   Nodes: {stats['nodes_searched']}")
    print(f"   Cutoffs: {stats['cutoffs']}")
    print(f"   Time: {search_time:.3f}s")
    print(f"   Hash entries: {tt_stats['entries']}")
    print(f"   Hash hit rate: {tt_stats['hit_rate']}%")
    
    # Test 2: Hash table functionality
    print("\n2. Testing Hash Table...")
    
    # Store and retrieve
    test_hash = 12345
    tt.store(test_hash, 3, 150, 'exact', 'e2e4')
    result = tt.lookup(test_hash, 2, -100, 100)
    
    if result:
        print(f"   ✅ Hash lookup successful: score={result[0]}, move={result[1]}")
    else:
        print("   ❌ Hash lookup failed")
    
    print(f"   Hash fullness: {tt.get_hash_full()}/1000")
    
    print("\n✅ Search Intelligence tests completed!")

if __name__ == "__main__":
    test_search_intelligence()
