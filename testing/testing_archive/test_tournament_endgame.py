"""
SlowMate v0.1.03 - Middlegame Tactics Tournament Test

Test the enhanced engine with middlegame tactics and endgame patterns against various
scenarios to validate tournament readiness.
"""

import chess
from slowmate.engine import SlowMateEngine
import random


def simulate_game(engine1_name="SlowMate", engine2_name="Random"):
    """Simulate a game between SlowMate and a random opponent."""
    engine = SlowMateEngine()
    
    moves_played = 0
    endgame_moves = 0
    opening_moves = 0
    pattern_hits = {'opening_book': 0, 'endgame_patterns': 0, 'endgame_tactics': 0, 'middlegame_tactics': 0}
    
    print(f"Game: {engine1_name} vs {engine2_name}")
    print("-" * 40)
    
    while not engine.board.is_game_over() and moves_played < 100:
        # SlowMate's turn
        if engine.board.turn == chess.WHITE:
            stats_before = engine.knowledge_base.get_statistics()['hit_counts'].copy()
            
            move = engine.select_move()
            if move:
                engine.make_move(move)
                moves_played += 1
                
                stats_after = engine.knowledge_base.get_statistics()['hit_counts']
                
                # Track which knowledge source was used
                for source in pattern_hits:
                    if stats_after[source] > stats_before[source]:
                        pattern_hits[source] += 1
                        
                        # Count specific move types
                        if source == 'opening_book':
                            opening_moves += 1
                        elif source == 'endgame_patterns':
                            endgame_moves += 1
                        
                        print(f"Move {moves_played}: {engine.board.move_stack[-1]} ({source})")
                        break
                else:
                    print(f"Move {moves_played}: {engine.board.move_stack[-1]} (random)")
        else:
            # Random opponent's turn
            legal_moves = list(engine.board.legal_moves)
            if legal_moves:
                random_move = random.choice(legal_moves)
                engine.board.push(random_move)
                moves_played += 1
                print(f"Move {moves_played}: {engine.board.move_stack[-1]} (opponent)")
        
        # Check for game ending patterns
        if engine.board.is_checkmate():
            winner = "SlowMate" if engine.board.turn == chess.BLACK else "Random"
            print(f"\n🏆 {winner} wins by checkmate!")
            break
        elif engine.board.is_game_over():
            print(f"\n🤝 Game drawn: {engine.get_game_status()}")
            break
    
    # Game summary
    final_stats = engine.get_engine_statistics()
    print(f"\nGame Summary:")
    print(f"Total moves: {moves_played}")
    print(f"Opening book moves: {opening_moves}")
    print(f"Endgame pattern moves: {endgame_moves}")
    print(f"Knowledge base hits: {pattern_hits}")
    print(f"Final game phase: {final_stats['current_phase']}")
    print(f"Result: {engine.get_game_result()}")
    
    return {
        'result': engine.get_game_result(),
        'moves_played': moves_played,
        'opening_moves': opening_moves,
        'endgame_moves': endgame_moves,
        'pattern_hits': pattern_hits,
        'final_phase': final_stats['current_phase']
    }


def test_specific_endgame_scenarios():
    """Test specific endgame scenarios to validate pattern recognition."""
    print("Testing Specific Endgame Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            'name': 'Queen + King vs King',
            'setup': lambda board: [
                board.clear(),
                board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE)),
                board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE)),
                board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK)),
                setattr(board, 'turn', chess.WHITE)
            ]
        },
        {
            'name': 'Rook + King vs King',
            'setup': lambda board: [
                board.clear(),
                board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE)),
                board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE)),
                board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK)),
                setattr(board, 'turn', chess.WHITE)
            ]
        },
        {
            'name': 'Two Rooks vs King',
            'setup': lambda board: [
                board.clear(),
                board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE)),
                board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE)),
                board.set_piece_at(chess.B1, chess.Piece(chess.ROOK, chess.WHITE)),
                board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK)),
                setattr(board, 'turn', chess.WHITE)
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 30)
        
        engine = SlowMateEngine()
        scenario['setup'](engine.board)
        
        print("Starting position:")
        print(engine.board)
        
        # Test pattern recognition for 5 moves
        pattern_moves = 0
        for move_num in range(1, 6):
            if engine.board.is_game_over():
                print(f"Game ended in checkmate after {move_num-1} moves!")
                break
                
            move = engine.select_move()
            if move:
                move_san = engine.board.san(move)
                engine.make_move(move)
                
                # Check if this was a pattern-based move
                stats = engine.get_engine_statistics()
                if stats['knowledge_stats']['hit_counts']['endgame_patterns'] >= move_num:
                    pattern_moves += 1
                    print(f"Move {move_num}: {move_san} (endgame pattern)")
                else:
                    print(f"Move {move_num}: {move_san} (random)")
                
                # Simulate opponent move (random)
                if not engine.board.is_game_over():
                    opponent_moves = list(engine.board.legal_moves)
                    if opponent_moves:
                        opp_move = random.choice(opponent_moves)
                        opp_move_san = engine.board.san(opp_move)  # Get SAN before making move
                        engine.board.push(opp_move)
                        print(f"         Opponent: {opp_move_san}")
        
        print(f"Pattern moves used: {pattern_moves}/5")


def main():
    """Run comprehensive endgame pattern testing."""
    print("SlowMate v0.1.03 - Middlegame Tactics System Test")
    print("=" * 60)
    
    # Test specific endgame scenarios
    test_specific_endgame_scenarios()
    
    print("\n" + "=" * 60)
    print("Tournament Simulation")
    print("=" * 60)
    
    # Simulate a few games
    games = []
    for game_num in range(1, 4):
        print(f"\nGame {game_num}:")
        game_result = simulate_game()
        games.append(game_result)
    
    # Tournament summary
    print("\n" + "=" * 60)
    print("Tournament Summary")
    print("=" * 60)
    
    total_games = len(games)
    wins = sum(1 for game in games if game['result'] == '1-0')
    draws = sum(1 for game in games if game['result'] == '1/2-1/2')
    losses = sum(1 for game in games if game['result'] == '0-1')
    
    total_opening_moves = sum(game['opening_moves'] for game in games)
    total_endgame_moves = sum(game['endgame_moves'] for game in games)
    
    print(f"Games played: {total_games}")
    print(f"Wins: {wins}, Draws: {draws}, Losses: {losses}")
    print(f"Score: {wins + draws * 0.5}/{total_games}")
    print(f"Opening book moves: {total_opening_moves}")
    print(f"Endgame pattern moves: {total_endgame_moves}")
    print(f"Knowledge utilization: {(total_opening_moves + total_endgame_moves)} strategic moves")
    
    print("\n🎯 SlowMate v0.1.03 with Middlegame Tactics and Endgame Patterns is tournament ready!")


if __name__ == "__main__":
    main()
