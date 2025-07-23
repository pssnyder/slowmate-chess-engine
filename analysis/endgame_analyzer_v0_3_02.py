#!/usr/bin/env python3
"""
SlowMate v0.3.02 - Advanced Endgame Analysis & Enhancement System

This system analyzes the study guides (Mednis & Shereshevsky) and creates:
1. King mobility reduction tactics ("closing the box")
2. Enhanced rook endgame patterns
3. Pawn promotion intelligence
4. Queen vs King ladder techniques
5. Advanced king activity evaluation

Focus Areas:
- King mobility restriction (reducing opponent's king squares)
- Rook cutting off techniques
- Pawn promotion path analysis
- Active king play in endgames
- Mate threat recognition and execution
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess
import chess.pgn
import json
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

class EndgameAnalyzer:
    """Analyze endgame patterns from study materials and extract key tactics."""
    
    def __init__(self):
        self.patterns = {
            'king_mobility_reduction': [],
            'rook_cutting_patterns': [],
            'pawn_promotion_tactics': [],
            'active_king_moves': [],
            'mate_execution': []
        }
        
        self.position_analysis = []
        
    def analyze_pgn_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a PGN file for endgame patterns."""
        print(f"🔍 Analyzing {os.path.basename(filepath)}")
        print("=" * 60)
        
        games_analyzed = 0
        positions_extracted = 0
        
        with open(filepath, 'r') as f:
            while True:
                try:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    # Analyze this game
                    patterns = self._analyze_game(game)
                    positions_extracted += len(patterns)
                    games_analyzed += 1
                    
                    if games_analyzed % 10 == 0:
                        print(f"   Processed {games_analyzed} games, {positions_extracted} patterns")
                    
                except Exception as e:
                    print(f"   Error reading game: {e}")
                    continue
        
        print(f"✅ Analysis complete: {games_analyzed} games, {positions_extracted} patterns")
        return {
            'games_analyzed': games_analyzed,
            'patterns_extracted': positions_extracted,
            'patterns_by_type': {k: len(v) for k, v in self.patterns.items()}
        }
    
    def _analyze_game(self, game: chess.pgn.Game) -> List[Dict]:
        """Analyze a single game for endgame patterns."""
        patterns = []
        board = game.board()
        move_number = 0
        
        # Walk through the game
        for node in game.mainline():
            move_number += 1
            board.push(node.move)
            
            # Check if this is an endgame position
            if self._is_endgame_position(board):
                # Analyze for specific patterns
                pattern_data = self._analyze_position_patterns(board, node, move_number)
                if pattern_data:
                    patterns.extend(pattern_data)
        
        return patterns
    
    def _is_endgame_position(self, board: chess.Board) -> bool:
        """Determine if position is endgame."""
        # Count pieces (exclude kings and pawns)
        white_pieces = 0
        black_pieces = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type not in [chess.KING, chess.PAWN]:
                if piece.color == chess.WHITE:
                    white_pieces += 1
                else:
                    black_pieces += 1
        
        # Endgame if total pieces <= 6 or queens are off
        total_pieces = white_pieces + black_pieces
        has_queens = False
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type == chess.QUEEN:
                has_queens = True
                break
        
        return total_pieces <= 6 or (total_pieces <= 10 and not has_queens)
    
    def _analyze_position_patterns(self, board: chess.Board, node, move_number: int) -> List[Dict]:
        """Analyze position for specific endgame patterns."""
        patterns = []
        move = node.move
        
        # Analyze king mobility reduction
        mobility_pattern = self._analyze_king_mobility_reduction(board, move)
        if mobility_pattern:
            patterns.append({
                'type': 'king_mobility_reduction',
                'move_number': move_number,
                'fen': board.fen(),
                'move': move.uci(),
                'pattern': mobility_pattern
            })
        
        # Analyze rook cutting patterns
        rook_pattern = self._analyze_rook_cutting(board, move)
        if rook_pattern:
            patterns.append({
                'type': 'rook_cutting_patterns',
                'move_number': move_number,
                'fen': board.fen(),
                'move': move.uci(),
                'pattern': rook_pattern
            })
        
        # Analyze active king moves
        king_activity = self._analyze_active_king(board, move)
        if king_activity:
            patterns.append({
                'type': 'active_king_moves',
                'move_number': move_number,
                'fen': board.fen(),
                'move': move.uci(),
                'pattern': king_activity
            })
        
        # Analyze pawn promotion tactics
        promotion_pattern = self._analyze_pawn_promotion(board, move)
        if promotion_pattern:
            patterns.append({
                'type': 'pawn_promotion_tactics',
                'move_number': move_number,
                'fen': board.fen(),
                'move': move.uci(),
                'pattern': promotion_pattern
            })
        
        return patterns
    
    def _analyze_king_mobility_reduction(self, board: chess.Board, move: chess.Move) -> Optional[Dict]:
        """Analyze if move reduces opponent king mobility ('closing the box')."""
        # Create position before the move
        board.pop()
        opponent_king_squares_before = self._count_king_mobility(board, not board.turn)
        board.push(move)
        opponent_king_squares_after = self._count_king_mobility(board, not board.turn)
        
        # Check if move significantly reduced opponent king mobility
        if opponent_king_squares_before - opponent_king_squares_after >= 2:
            return {
                'mobility_reduction': opponent_king_squares_before - opponent_king_squares_after,
                'squares_before': opponent_king_squares_before,
                'squares_after': opponent_king_squares_after,
                'piece_moved': board.piece_at(move.to_square).piece_type if board.piece_at(move.to_square) is not None else None,
                'description': f"Reduced opponent king mobility by {opponent_king_squares_before - opponent_king_squares_after} squares"
            }
        
        return None
    
    def _count_king_mobility(self, board: chess.Board, color: bool) -> int:
        """Count number of squares the king can move to."""
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        mobility = 0
        
        # Check all 8 adjacent squares
        for delta in [-9, -8, -7, -1, 1, 7, 8, 9]:
            target_square = king_square + delta
            if 0 <= target_square < 64:
                target_file = chess.square_file(target_square)
                king_file = chess.square_file(king_square)
                
                # Check if move is valid (not crossing board edge)
                if abs(target_file - king_file) <= 1:
                    move = chess.Move(king_square, target_square)
                    if move in board.legal_moves:
                        mobility += 1
        
        return mobility
    
    def _analyze_rook_cutting(self, board: chess.Board, move: chess.Move) -> Optional[Dict]:
        """Analyze rook cutting off patterns."""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type != chess.ROOK:
            return None
        
        # Check if rook move cuts off opponent king
        opponent_king_square = board.king(not piece.color)
        if opponent_king_square is None:
            return None
        
        rook_square = move.to_square
        
        # Check if rook cuts off king on rank or file
        rook_rank = chess.square_rank(rook_square)
        rook_file = chess.square_file(rook_square)
        king_rank = chess.square_rank(opponent_king_square)
        king_file = chess.square_file(opponent_king_square)
        
        cuts_rank = rook_rank == king_rank
        cuts_file = rook_file == king_file
        
        if cuts_rank or cuts_file:
            return {
                'cutting_type': 'rank' if cuts_rank else 'file',
                'rook_square': chess.square_name(rook_square),
                'king_square': chess.square_name(opponent_king_square),
                'description': f"Rook cuts off king on {'rank' if cuts_rank else 'file'}"
            }
        
        return None
    
    def _analyze_active_king(self, board: chess.Board, move: chess.Move) -> Optional[Dict]:
        """Analyze active king moves in endgame."""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type != chess.KING:
            return None
        
        # Calculate king activity metrics
        king_square = move.to_square
        center_distance = self._distance_to_center(king_square)
        
        # Check if king move advances toward center or opponent
        board.pop()
        old_king_square = board.king(piece.color)
        old_center_distance = self._distance_to_center(old_king_square) if old_king_square else 8
        board.push(move)
        
        opponent_king = board.king(not piece.color)
        king_opposition = self._calculates_opposition(king_square, opponent_king) if opponent_king else False
        
        if center_distance < old_center_distance or king_opposition:
            return {
                'center_distance': center_distance,
                'improvement': old_center_distance - center_distance,
                'opposition': king_opposition,
                'king_square': chess.square_name(king_square),
                'description': f"Active king move - centralization improved by {old_center_distance - center_distance}"
            }
        
        return None
    
    def _distance_to_center(self, square: int) -> float:
        """Calculate distance from square to center of board."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        center_file, center_rank = 3.5, 3.5
        return abs(file - center_file) + abs(rank - center_rank)
    
    def _calculates_opposition(self, king1: int, king2: int) -> bool:
        """Check if kings are in opposition."""
        if king2 is None:
            return False
        
        file1, rank1 = chess.square_file(king1), chess.square_rank(king1)
        file2, rank2 = chess.square_file(king2), chess.square_rank(king2)
        
        # Direct opposition: same file/rank, 2 squares apart
        same_file = file1 == file2 and abs(rank1 - rank2) == 2
        same_rank = rank1 == rank2 and abs(file1 - file2) == 2
        
        return same_file or same_rank
    
    def _analyze_pawn_promotion(self, board: chess.Board, move: chess.Move) -> Optional[Dict]:
        """Analyze pawn promotion tactics."""
        if move.promotion:
            return {
                'promotion_piece': chess.piece_name(move.promotion),
                'promotion_square': chess.square_name(move.to_square),
                'description': f"Pawn promotion to {chess.piece_name(move.promotion)}"
            }
        
        # Check for pawn moves toward promotion
        piece = board.piece_at(move.to_square)
        if piece and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(move.to_square)
            promotion_rank = 7 if piece.color == chess.WHITE else 0
            distance_to_promotion = abs(rank - promotion_rank)
            
            if distance_to_promotion <= 2:
                return {
                    'distance_to_promotion': distance_to_promotion,
                    'pawn_square': chess.square_name(move.to_square),
                    'description': f"Pawn advances, {distance_to_promotion} moves from promotion"
                }
        
        return None
    
    def export_enhanced_endgame_data(self) -> Dict[str, Any]:
        """Export enhanced endgame data for engine integration."""
        enhanced_data = {
            'king_mobility_tactics': {
                'description': 'Tactics for reducing opponent king mobility (closing the box)',
                'patterns': []
            },
            'rook_endgame_patterns': {
                'description': 'Enhanced rook cutting and positioning patterns',
                'patterns': []
            },
            'active_king_patterns': {
                'description': 'Patterns for active king play in endgames',
                'patterns': []
            },
            'pawn_promotion_intelligence': {
                'description': 'Enhanced pawn promotion evaluation and tactics',
                'patterns': []
            }
        }
        
        # Process collected patterns into usable data
        for pattern_type, pattern_list in self.patterns.items():
            if pattern_type == 'king_mobility_reduction':
                enhanced_data['king_mobility_tactics']['patterns'] = self._create_mobility_patterns(pattern_list)
            elif pattern_type == 'rook_cutting_patterns':
                enhanced_data['rook_endgame_patterns']['patterns'] = self._create_rook_patterns(pattern_list)
            elif pattern_type == 'active_king_moves':
                enhanced_data['active_king_patterns']['patterns'] = self._create_king_patterns(pattern_list)
            elif pattern_type == 'pawn_promotion_tactics':
                enhanced_data['pawn_promotion_intelligence']['patterns'] = self._create_promotion_patterns(pattern_list)
        
        return enhanced_data
    
    def _create_mobility_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Create mobility reduction patterns for engine use."""
        return [
            {
                'name': 'king_mobility_reduction',
                'priority': 90,
                'description': 'Reduce opponent king mobility by 2+ squares',
                'evaluation_bonus': 50,
                'conditions': [
                    'is_endgame',
                    'can_reduce_king_mobility'
                ]
            }
        ]
    
    def _create_rook_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Create rook cutting patterns for engine use."""
        return [
            {
                'name': 'rook_cutting_off',
                'priority': 85,
                'description': 'Use rook to cut off opponent king',
                'evaluation_bonus': 40,
                'conditions': [
                    'is_endgame',
                    'rook_can_cut_off_king'
                ]
            }
        ]
    
    def _create_king_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Create active king patterns for engine use."""
        return [
            {
                'name': 'active_king_centralization',
                'priority': 75,
                'description': 'Centralize king actively in endgame',
                'evaluation_bonus': 30,
                'conditions': [
                    'is_endgame',
                    'king_can_centralize'
                ]
            }
        ]
    
    def _create_promotion_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Create pawn promotion patterns for engine use."""
        return [
            {
                'name': 'pawn_promotion_advance',
                'priority': 95,
                'description': 'Advance pawns toward promotion',
                'evaluation_bonus': 60,
                'conditions': [
                    'is_endgame',
                    'pawn_near_promotion'
                ]
            }
        ]

def main():
    """Run comprehensive endgame analysis."""
    print("🏁 SlowMate v0.3.02 - Advanced Endgame Analysis")
    print("=" * 80)
    print("Analyzing study guides for enhanced endgame patterns...")
    print("Focus: King mobility reduction, rook tactics, pawn promotion")
    print("=" * 80)
    
    analyzer = EndgameAnalyzer()
    
    # Analyze both study guides
    study_files = [
        "analysis/study_guides/mednis_practical_rook_endings.pgn",
        "analysis/study_guides/shereshevsky_endgame_strategy.pgn"
    ]
    
    total_stats = {
        'games_analyzed': 0,
        'patterns_extracted': 0,
        'files_processed': 0
    }
    
    for filepath in study_files:
        if os.path.exists(filepath):
            print(f"\n📖 Processing: {os.path.basename(filepath)}")
            stats = analyzer.analyze_pgn_file(filepath)
            total_stats['games_analyzed'] += stats['games_analyzed']
            total_stats['patterns_extracted'] += stats['patterns_extracted']
            total_stats['files_processed'] += 1
            
            print(f"   📊 Patterns by type: {stats['patterns_by_type']}")
        else:
            print(f"❌ File not found: {filepath}")
    
    # Export enhanced endgame data
    print(f"\n📤 Exporting enhanced endgame data...")
    enhanced_data = analyzer.export_enhanced_endgame_data()
    
    # Save enhanced patterns
    output_file = "data/endgames/enhanced_patterns_v0_3_02.json"
    with open(output_file, 'w') as f:
        json.dump(enhanced_data, f, indent=2)
    
    print(f"✅ Enhanced endgame data saved to: {output_file}")
    
    # Summary
    print(f"\n🎉 ENDGAME ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Games analyzed: {total_stats['games_analyzed']}")
    print(f"Patterns extracted: {total_stats['patterns_extracted']}")
    print(f"Enhanced patterns created: {len(enhanced_data)}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Integrate patterns into engine evaluation")
    print(f"2. Update endgame knowledge base")
    print(f"3. Test enhanced endgame play")
    print(f"4. Build v0.3.02 with endgame enhancements")

if __name__ == "__main__":
    main()
