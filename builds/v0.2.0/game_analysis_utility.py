"""
SlowMate Historical Game Analysis Utility

Standalone tool for analyzing historical PGN games and building the middlegame tactics library.
This utility extracts significant moves from SlowMate's winning games and builds a 
confidence-weighted tactical database for future games.

Usage:
    python game_analysis_utility.py [--games-dir games/] [--strictness high]

Features:
- Mathematical evaluation comparison using standard deviation analysis
- Confidence weighting based on multiple statistical factors
- Detection of considerable moves and checkmate patterns
- Batch processing of PGN files with duplicate detection
- Compatible data structures for transposition table integration
"""

import os
import sys
import json
import argparse
import chess
import chess.pgn
import chess.engine
from typing import Dict, List, Optional, Tuple, Set
import statistics
import hashlib
from pathlib import Path

# Add slowmate to path for importing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.engine import SlowMateEngine
from slowmate.intelligence import MoveIntelligence
from slowmate.knowledge.middlegame_tactics import MiddlegameTactics


class EvaluationHelper:
    """Helper class for position evaluation during game analysis."""
    
    def __init__(self):
        """Initialize evaluation helper with intelligence module."""
        self.temp_engine = SlowMateEngine()
        self.intelligence = MoveIntelligence(self.temp_engine)
    
    def evaluate_position(self, board: chess.Board) -> float:
        """
        Evaluate a chess position and return centipawn score.
        Positive values favor white, negative favor black.
        """
        # Set the temporary engine's board to the position we want to evaluate
        original_board = self.temp_engine.board.fen()
        
        try:
            # Set position
            self.temp_engine.board.set_fen(board.fen())
            
            # Use the intelligence module's position evaluation
            evaluation = self.intelligence._evaluate_position()
            return float(evaluation)
        finally:
            # Restore original board
            self.temp_engine.board.set_fen(original_board)


class GameAnalysisUtility:
    """
    Utility for analyzing historical games and extracting tactical knowledge.
    """
    
    def __init__(self, games_directory: str = "games/", strictness: str = "high"):
        """
        Initialize the game analysis utility.
        
        Args:
            games_directory: Directory containing PGN files
            strictness: Analysis strictness ('high', 'medium', 'low')
        """
        self.games_dir = Path(games_directory)
        self.strictness = strictness
        self.middlegame_tactics = MiddlegameTactics()
        self.evaluator = EvaluationHelper()  # Add evaluation helper
        
        # Session tracking
        self.processed_games = set()  # Track duplicates in current session
        self.session_stats = {
            'games_analyzed': 0,
            'slowmate_wins': 0,
            'significant_moves': 0,
            'checkmate_patterns': 0,
            'eval_comparisons': 0,
            'tactics_added': 0
        }
        
        # Analysis parameters by strictness
        self.strictness_config = {
            'high': {
                'min_eval_improvement': 50,  # centipawns
                'min_deviation_factor': 1.5,  # standard deviations
                'require_all_criteria': True
            },
            'medium': {
                'min_eval_improvement': 30,
                'min_deviation_factor': 1.0,
                'require_all_criteria': True
            },
            'low': {
                'min_eval_improvement': 20,
                'min_deviation_factor': 0.8,
                'require_all_criteria': False
            }
        }
        
        print(f"🔍 SlowMate Game Analysis Utility v0.1.03")
        print(f"📁 Games directory: {self.games_dir}")
        print(f"🎯 Analysis strictness: {strictness}")
        print(f"⚙️  Config: {self.strictness_config[strictness]}")
        print("-" * 60)
    
    def get_pgn_files(self) -> List[Path]:
        """Get all PGN files in the games directory."""
        if not self.games_dir.exists():
            print(f"❌ Games directory not found: {self.games_dir}")
            return []
        
        pgn_files = list(self.games_dir.glob("*.pgn"))
        print(f"📋 Found {len(pgn_files)} PGN files")
        return pgn_files
    
    def generate_game_id(self, game_headers: Dict[str, str], moves: List[str]) -> str:
        """Generate unique ID for game to detect duplicates."""
        # Combine key headers and first few moves for unique identification
        id_string = f"{game_headers.get('Date', '')}-{game_headers.get('White', '')}-{game_headers.get('Black', '')}"
        id_string += f"-{'-'.join(moves[:10])}"  # First 10 moves
        return hashlib.md5(id_string.encode()).hexdigest()[:16]
    
    def parse_pgn_game(self, pgn_file: Path) -> List[Dict]:
        """Parse all games from a PGN file."""
        games = []
        
        try:
            with open(pgn_file, 'r', encoding='utf-8') as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    # Extract game information
                    headers = dict(game.headers)
                    moves = []
                    board = game.board()
                    
                    # Extract moves and positions
                    for move in game.mainline_moves():
                        moves.append(move.uci())
                        board.push(move)
                    
                    game_id = self.generate_game_id(headers, moves)
                    
                    games.append({
                        'id': game_id,
                        'file': pgn_file.name,
                        'headers': headers,
                        'moves': moves,
                        'result': headers.get('Result', '*')
                    })
                    
        except Exception as e:
            print(f"❌ Error parsing {pgn_file}: {e}")
        
        return games
    
    def is_slowmate_game(self, game: Dict) -> Optional[bool]:
        """
        Determine if SlowMate played in this game and return if it won.
        
        Returns:
            True if SlowMate won
            False if SlowMate lost  
            None if SlowMate didn't play
        """
        white = game['headers'].get('White', '').lower()
        black = game['headers'].get('Black', '').lower()
        result = game['result']
        
        slowmate_as_white = 'slowmate' in white
        slowmate_as_black = 'slowmate' in black
        
        if not (slowmate_as_white or slowmate_as_black):
            return None  # SlowMate not in this game
        
        # Check if SlowMate won
        if slowmate_as_white and result == '1-0':
            return True
        elif slowmate_as_black and result == '0-1':
            return True
        else:
            return False
    
    def calculate_game_evaluation_stats(self, game: Dict) -> Dict:
        """
        Calculate evaluation statistics for the entire game.
        Used to determine significant move thresholds.
        """
        evaluations = []
        eval_changes = []
        
        board = chess.Board()
        previous_eval = 0
        
        # Analyze each position in the game
        for i, move_uci in enumerate(game['moves']):
            try:
                move = chess.Move.from_uci(move_uci)
                
                # Evaluate position before move
                current_eval = self.evaluator.evaluate_position(board)
                evaluations.append(current_eval)
                
                # Calculate evaluation change
                if i > 0:
                    eval_change = abs(current_eval - previous_eval)
                    eval_changes.append(eval_change)
                
                board.push(move)
                previous_eval = current_eval
                
                self.session_stats['eval_comparisons'] += 1
                
            except Exception as e:
                print(f"⚠️  Evaluation error at move {i+1}: {e}")
                continue
        
        # Calculate statistical measures
        if not eval_changes:
            return {'mean_change': 0, 'std_dev': 0, 'total_moves': len(game['moves'])}
        
        mean_change = statistics.mean(eval_changes)
        std_dev = statistics.stdev(eval_changes) if len(eval_changes) > 1 else 0
        
        return {
            'mean_change': mean_change,
            'std_dev': std_dev,
            'total_moves': len(game['moves']),
            'max_change': max(eval_changes) if eval_changes else 0,
            'evaluations': evaluations[:50],  # Store first 50 for analysis
            'eval_changes': eval_changes[:50]
        }
    
    def analyze_move_significance(self, board: chess.Board, move: chess.Move, 
                                prev_eval: float, new_eval: float, game_stats: Dict) -> Dict:
        """
        Analyze if a move meets 'considerable move' criteria.
        
        Returns analysis with significance scoring.
        """
        eval_improvement = new_eval - prev_eval
        
        # Handle perspective (negative is good for black)
        if not board.turn:  # Black to move (after white played)
            eval_improvement = -eval_improvement
        
        # Calculate deviation factor
        if game_stats['std_dev'] > 0:
            deviation_factor = abs(eval_improvement) / game_stats['std_dev']
        else:
            deviation_factor = 0
        
        # Determine game impact level
        impact_level = 'low'
        if abs(eval_improvement) > game_stats['mean_change'] * 2:
            impact_level = 'high'
        elif abs(eval_improvement) > game_stats['mean_change'] * 1.5:
            impact_level = 'medium'
        
        # Check for checkmate patterns
        board.push(move)
        is_checkmate = board.is_checkmate()
        mate_in = None
        
        if is_checkmate:
            mate_in = 1
        # Could add deeper mate detection here
        
        board.pop()  # Restore position
        
        # Determine pattern type
        if is_checkmate or mate_in:
            pattern_type = 'checkmate'
        elif abs(eval_improvement) > 100:
            pattern_type = 'tactical'
        else:
            pattern_type = 'positional'
        
        config = self.strictness_config[self.strictness]
        
        # Check criteria
        criteria_met = {
            'eval_improvement': abs(eval_improvement) >= config['min_eval_improvement'],
            'deviation_significant': deviation_factor >= config['min_deviation_factor'],
            'positive_improvement': eval_improvement > 0,  # Must improve position
            'checkmate_pattern': pattern_type == 'checkmate'
        }
        
        # Special case: checkmate always passes
        if criteria_met['checkmate_pattern']:
            is_considerable = True
        elif config['require_all_criteria']:
            is_considerable = all([
                criteria_met['eval_improvement'],
                criteria_met['deviation_significant'], 
                criteria_met['positive_improvement']
            ])
        else:
            # For low strictness, require at least 2 of 3 criteria
            core_criteria = [
                criteria_met['eval_improvement'],
                criteria_met['deviation_significant'],
                criteria_met['positive_improvement']
            ]
            is_considerable = sum(core_criteria) >= 2
        
        return {
            'is_considerable': is_considerable,
            'eval_improvement': eval_improvement,
            'deviation_factor': deviation_factor,
            'impact_level': impact_level,
            'pattern_type': pattern_type,
            'mate_in': mate_in,
            'criteria_met': criteria_met
        }
    
    def extract_principal_variation(self, board: chess.Board, move: chess.Move, depth: int = 5) -> List[str]:
        """Extract principal variation starting from the given move."""
        # For now, just return the single move - could be enhanced with deeper analysis
        return [move.uci()]
    
    def analyze_game(self, game: Dict) -> bool:
        """
        Analyze a single game for tactical patterns.
        
        Returns True if any tactics were discovered.
        """
        # Skip if already processed this session
        if game['id'] in self.processed_games:
            return False
        
        self.processed_games.add(game['id'])
        
        # Check if this is a SlowMate winning game
        slowmate_result = self.is_slowmate_game(game)
        if slowmate_result is not True:  # Must be a SlowMate win
            return False
        
        print(f"🎯 Analyzing SlowMate win: {game['file']} ({game['id'][:8]})")
        
        # Calculate game evaluation statistics
        game_stats = self.calculate_game_evaluation_stats(game)
        
        tactics_found = 0
        engine = SlowMateEngine()
        board = chess.Board()
        
        # Determine which color SlowMate played
        slowmate_as_white = 'slowmate' in game['headers'].get('White', '').lower()
        
        # Analyze each SlowMate move
        for i, move_uci in enumerate(game['moves']):
            try:
                move = chess.Move.from_uci(move_uci)
                
                # Check if this is SlowMate's move
                is_slowmate_move = (slowmate_as_white and board.turn == chess.WHITE) or \
                                 (not slowmate_as_white and board.turn == chess.BLACK)
                
                if is_slowmate_move and i < len(game_stats['evaluations']) - 1:
                    # Get evaluations before and after move
                    prev_eval = game_stats['evaluations'][i]
                    
                    # Evaluate position after move
                    board.push(move)
                    new_eval = self.evaluator.evaluate_position(board)
                    board.pop()
                    
                    # Analyze move significance
                    analysis = self.analyze_move_significance(board, move, prev_eval, new_eval, game_stats)
                    
                    if analysis['is_considerable']:
                        # Calculate confidence weight
                        confidence = self.middlegame_tactics.calculate_confidence_weight(
                            analysis['eval_improvement'],
                            analysis['deviation_factor'],
                            analysis['impact_level'],
                            analysis['pattern_type']
                        )
                        
                        # Extract principal variation
                        pv = self.extract_principal_variation(board, move)
                        
                        # Store in middlegame tactics
                        success = self.middlegame_tactics.store_tactic(
                            board, move, pv,
                            analysis['eval_improvement'],
                            confidence,
                            analysis['pattern_type'],
                            game['id'],
                            analysis['mate_in']
                        )
                        
                        if success:
                            tactics_found += 1
                            self.session_stats['significant_moves'] += 1
                            if analysis['pattern_type'] == 'checkmate':
                                self.session_stats['checkmate_patterns'] += 1
                            
                            print(f"  ✅ Move {i+1}: {board.san(move)} ({analysis['pattern_type']}, conf={confidence:.3f})")
                
                board.push(move)
                
            except Exception as e:
                print(f"  ⚠️  Error analyzing move {i+1}: {e}")
                continue
        
        self.session_stats['tactics_added'] += tactics_found
        if tactics_found > 0:
            print(f"  📈 Found {tactics_found} tactical moves")
        
        return tactics_found > 0
    
    def analyze_all_games(self) -> Dict:
        """Analyze all PGN files in the games directory."""
        pgn_files = self.get_pgn_files()
        
        if not pgn_files:
            print("❌ No PGN files found")
            return self.session_stats
        
        total_games_processed = 0
        
        for pgn_file in pgn_files:
            print(f"\n📄 Processing: {pgn_file.name}")
            
            games = self.parse_pgn_game(pgn_file)
            
            for game in games:
                slowmate_result = self.is_slowmate_game(game)
                
                if slowmate_result is True:
                    self.session_stats['slowmate_wins'] += 1
                    self.analyze_game(game)
                
                total_games_processed += 1
                self.session_stats['games_analyzed'] += 1
        
        print(f"\n" + "=" * 60)
        print("📊 Analysis Complete!")
        print("=" * 60)
        
        return self.session_stats
    
    def save_results(self):
        """Save middlegame tactics and generate report."""
        # Save tactics library
        self.middlegame_tactics.save_tactics()
        
        # Generate analysis report
        library_stats = self.middlegame_tactics.get_statistics()
        
        report = {
            'analysis_session': self.session_stats,
            'library_stats': library_stats,
            'configuration': {
                'strictness': self.strictness,
                'games_directory': str(self.games_dir),
                'strictness_config': self.strictness_config[self.strictness]
            }
        }
        
        report_file = f"analysis_report_{self.session_stats['games_analyzed']}_games.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"💾 Results saved:")
        print(f"  📚 Tactics library: {self.middlegame_tactics.data_file}")
        print(f"  📋 Analysis report: {report_file}")
        
        # Print summary
        print(f"\n🎯 Session Summary:")
        print(f"  Games analyzed: {self.session_stats['games_analyzed']}")
        print(f"  SlowMate wins: {self.session_stats['slowmate_wins']}")  
        print(f"  Significant moves: {self.session_stats['significant_moves']}")
        print(f"  Checkmate patterns: {self.session_stats['checkmate_patterns']}")
        print(f"  Tactics added: {self.session_stats['tactics_added']}")
        
        print(f"\n📚 Library Statistics:")
        print(f"  Total positions: {library_stats['total_positions']}")
        print(f"  Total tactics: {library_stats['total_tactics']}")
        print(f"  Checkmate patterns: {library_stats['total_checkmates']}")
        print(f"  Average confidence: {library_stats['average_confidence']:.3f}")


def main():
    """Main entry point for the game analysis utility."""
    parser = argparse.ArgumentParser(
        description="SlowMate Historical Game Analysis Utility",
        epilog="Analyzes PGN games to build middlegame tactics library"
    )
    
    parser.add_argument(
        '--games-dir', 
        default='games/',
        help='Directory containing PGN files (default: games/)'
    )
    
    parser.add_argument(
        '--strictness',
        choices=['high', 'medium', 'low'],
        default='high',
        help='Analysis strictness level (default: high)'
    )
    
    args = parser.parse_args()
    
    # Create and run analysis utility
    analyzer = GameAnalysisUtility(args.games_dir, args.strictness)
    
    # Analyze all games
    stats = analyzer.analyze_all_games()
    
    # Save results
    analyzer.save_results()
    
    print(f"\n🏁 Analysis complete! Check the tactics library for new discoveries.")


if __name__ == "__main__":
    main()
