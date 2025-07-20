"""
SlowMate Middlegame Tactics Library

A self-learning tactical database built from historical game analysis.
Stores discovered moves, patterns, and evaluations with confidence weighting.

Compatible with transposition tables, killer moves, and other chess data structures.
"""

import json
import os
import hashlib
import chess
from typing import Dict, List, Optional, Tuple, Union
import statistics


class MiddlegameTactics:
    """
    Middlegame tactical library for storing and retrieving discovered moves.
    
    Features:
    - Confidence-weighted move selection
    - Statistical evaluation tracking
    - Checkmate pattern recognition
    - Transposition table compatibility
    """
    
    def __init__(self, data_file: Optional[str] = None):
        """Initialize middlegame tactics library."""
        self.data_file = data_file or "data/middlegame/tactics.json"
        self.tactics_db = {}
        self.checkmate_patterns = {}
        self.session_stats = {
            'moves_added': 0,
            'patterns_discovered': 0,
            'confidence_updates': 0,
            'checkmates_stored': 0
        }
        
        # Load existing tactics
        self.load_tactics()
    
    def position_hash(self, board: chess.Board) -> str:
        """
        Generate position hash compatible with transposition tables.
        Uses FEN without move counters for position-only identification.
        """
        # Use only position, turn, castling, and en passant for hash
        fen_parts = board.fen().split()
        position_fen = ' '.join(fen_parts[:4])  # Position + turn + castling + ep
        return hashlib.md5(position_fen.encode()).hexdigest()
    
    def calculate_confidence_weight(self, eval_improvement: float, deviation_factor: float, 
                                  game_impact: str, pattern_type: str) -> float:
        """
        Calculate confidence weight using mathematical evaluation criteria.
        
        Args:
            eval_improvement: Centipawn improvement from move
            deviation_factor: Standard deviations from game average
            game_impact: 'low', 'medium', 'high' based on positional change
            pattern_type: 'tactical', 'positional', 'checkmate'
        """
        base_confidence = 0.5
        
        # Evaluation improvement factor (0.0 - 0.3)
        eval_factor = min(abs(eval_improvement) / 500.0, 0.3)
        
        # Statistical deviation factor (0.0 - 0.4)  
        deviation_factor = min(abs(deviation_factor) / 3.0, 0.4)
        
        # Game impact factor (0.0 - 0.2)
        impact_weights = {'low': 0.05, 'medium': 0.1, 'high': 0.2}
        impact_factor = impact_weights.get(game_impact, 0.1)
        
        # Pattern type factor (0.0 - 0.1)
        pattern_weights = {'positional': 0.05, 'tactical': 0.08, 'checkmate': 0.1}
        pattern_factor = pattern_weights.get(pattern_type, 0.05)
        
        confidence = base_confidence + eval_factor + deviation_factor + impact_factor + pattern_factor
        
        # Checkmate patterns get maximum confidence
        if pattern_type == 'checkmate':
            confidence = 1.0
            
        return min(confidence, 1.0)
    
    def store_tactic(self, board: chess.Board, move: chess.Move, pv: List[str],
                    eval_improvement: float, confidence: float, pattern_type: str,
                    game_id: str, mate_in: Optional[int] = None) -> bool:
        """
        Store a discovered tactical move in the library.
        
        Args:
            board: Current position
            move: The tactical move
            pv: Principal variation sequence
            eval_improvement: Centipawn improvement
            confidence: Calculated confidence weight
            pattern_type: Type of tactical pattern
            game_id: Source game identifier
            mate_in: Moves to mate (if applicable)
        """
        pos_hash = self.position_hash(board)
        move_uci = move.uci()
        
        # Create tactic entry
        tactic_entry = {
            'move': move_uci,
            'move_san': board.san(move),
            'pv': pv,
            'pv_san': [board.san(chess.Move.from_uci(m)) for m in pv[:5]],  # Convert first 5 moves to SAN
            'confidence_weight': confidence,
            'eval_improvement': eval_improvement,
            'pattern_type': pattern_type,
            'discovered_in_game': game_id,
            'usage_count': 0,
            'success_rate': 0.0,
            'last_updated': game_id,
            'mate_in': mate_in
        }
        
        # Store in appropriate database
        if pattern_type == 'checkmate' and mate_in:
            self.checkmate_patterns[pos_hash] = tactic_entry
            self.session_stats['checkmates_stored'] += 1
        else:
            # Handle multiple tactics for same position
            if pos_hash not in self.tactics_db:
                self.tactics_db[pos_hash] = []
            
            # Check for existing move
            existing_move = None
            for i, existing in enumerate(self.tactics_db[pos_hash]):
                if existing['move'] == move_uci:
                    existing_move = i
                    break
            
            if existing_move is not None:
                # Update existing move with higher confidence
                old_entry = self.tactics_db[pos_hash][existing_move]
                if confidence > old_entry['confidence_weight']:
                    old_entry.update({
                        'confidence_weight': confidence,
                        'eval_improvement': eval_improvement,
                        'last_updated': game_id,
                        'pv': pv,
                        'pv_san': tactic_entry['pv_san']
                    })
                    self.session_stats['confidence_updates'] += 1
            else:
                # Add new tactic
                self.tactics_db[pos_hash].append(tactic_entry)
                self.session_stats['moves_added'] += 1
        
        return True
    
    def get_tactical_move(self, board: chess.Board, min_confidence: float = 0.7) -> Optional[Dict]:
        """
        Retrieve best tactical move for position.
        
        Args:
            board: Current position
            min_confidence: Minimum confidence threshold
            
        Returns:
            Best tactical move data or None
        """
        pos_hash = self.position_hash(board)
        
        # Check for forced mate patterns first
        if pos_hash in self.checkmate_patterns:
            checkmate = self.checkmate_patterns[pos_hash]
            if checkmate['confidence_weight'] >= min_confidence:
                return checkmate
        
        # Check tactical database
        if pos_hash in self.tactics_db:
            tactics = self.tactics_db[pos_hash]
            
            # Sort by confidence, then by evaluation improvement
            valid_tactics = [t for t in tactics if t['confidence_weight'] >= min_confidence]
            if valid_tactics:
                best_tactic = max(valid_tactics, 
                                key=lambda x: (x['confidence_weight'], x['eval_improvement']))
                return best_tactic
        
        return None
    
    def get_all_moves(self, board: chess.Board) -> List[Dict]:
        """Get all tactical moves for position, sorted by confidence."""
        pos_hash = self.position_hash(board)
        all_moves = []
        
        # Add checkmate patterns
        if pos_hash in self.checkmate_patterns:
            all_moves.append(self.checkmate_patterns[pos_hash])
        
        # Add regular tactics
        if pos_hash in self.tactics_db:
            all_moves.extend(self.tactics_db[pos_hash])
        
        # Sort by confidence descending
        all_moves.sort(key=lambda x: x['confidence_weight'], reverse=True)
        return all_moves
    
    def update_success_rate(self, board: chess.Board, move: chess.Move, success: bool):
        """Update success rate for a used tactical move."""
        pos_hash = self.position_hash(board)
        move_uci = move.uci()
        
        # Update in checkmate patterns
        if pos_hash in self.checkmate_patterns:
            if self.checkmate_patterns[pos_hash]['move'] == move_uci:
                pattern = self.checkmate_patterns[pos_hash]
                pattern['usage_count'] += 1
                current_successes = pattern['success_rate'] * (pattern['usage_count'] - 1)
                new_successes = current_successes + (1 if success else 0)
                pattern['success_rate'] = new_successes / pattern['usage_count']
                return
        
        # Update in tactics database
        if pos_hash in self.tactics_db:
            for tactic in self.tactics_db[pos_hash]:
                if tactic['move'] == move_uci:
                    tactic['usage_count'] += 1
                    current_successes = tactic['success_rate'] * (tactic['usage_count'] - 1)
                    new_successes = current_successes + (1 if success else 0)
                    tactic['success_rate'] = new_successes / tactic['usage_count']
                    break
    
    def load_tactics(self):
        """Load tactics from disk."""
        if not os.path.exists(self.data_file):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            return
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.tactics_db = data.get('tactics', {})
                self.checkmate_patterns = data.get('checkmates', {})
        except (FileNotFoundError, json.JSONDecodeError):
            # Start with empty databases
            self.tactics_db = {}
            self.checkmate_patterns = {}
    
    def save_tactics(self):
        """Save tactics to disk."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        data = {
            'tactics': self.tactics_db,
            'checkmates': self.checkmate_patterns,
            'metadata': {
                'version': '0.1.03',
                'total_positions': len(self.tactics_db) + len(self.checkmate_patterns),
                'session_stats': self.session_stats
            }
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_statistics(self) -> Dict:
        """Get library statistics."""
        total_tactics = sum(len(moves) for moves in self.tactics_db.values())
        total_checkmates = len(self.checkmate_patterns)
        
        # Calculate average confidence
        all_confidences = []
        for moves in self.tactics_db.values():
            all_confidences.extend([m['confidence_weight'] for m in moves])
        for checkmate in self.checkmate_patterns.values():
            all_confidences.append(checkmate['confidence_weight'])
        
        avg_confidence = statistics.mean(all_confidences) if all_confidences else 0.0
        
        return {
            'total_positions': len(self.tactics_db) + len(self.checkmate_patterns),
            'total_tactics': total_tactics,
            'total_checkmates': total_checkmates,
            'average_confidence': avg_confidence,
            'session_stats': self.session_stats.copy()
        }
    
    def clear_session_stats(self):
        """Reset session statistics."""
        self.session_stats = {
            'moves_added': 0,
            'patterns_discovered': 0,
            'confidence_updates': 0,
            'checkmates_stored': 0
        }
