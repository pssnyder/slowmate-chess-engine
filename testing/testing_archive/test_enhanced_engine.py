"""Test the enhanced SlowMate engine with endgame pattern integration."""

import chess
from slowmate.engine import SlowMateEngine


def test_enhanced_engine():
    """Test the enhanced engine with knowledge base integration."""
    print("Testing SlowMate Engine with Endgame Patterns")
    print("=" * 50)
    
    engine = SlowMateEngine()
    
    # Test 1: Basic initialization
    print("Test 1: Engine Initialization")
    stats = engine.get_engine_statistics()
    print(f"Current game phase: {stats['current_phase']}")
    print(f"Knowledge base loaded: {stats['knowledge_stats']['components']['endgame_patterns']['is_loaded']}")
    print()
    
    # Test 2: Regular opening position (should use opening book or random)
    print("Test 2: Opening Position")
    print(engine.get_board_state())
    move = engine.select_move()
    if move:
        move_san = engine.board.san(move)
        engine.make_move(move)
        print(f"Selected move: {move_san}")
    print()
    
    # Test 3: Setup a Queen + King vs King endgame position
    print("Test 3: KQ vs K Endgame Pattern Test")
    engine.reset_game()
    engine.board.clear()
    
    # Set up endgame position: White has King + Queen, Black has King
    engine.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    engine.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    engine.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    engine.board.turn = chess.WHITE
    
    print("Endgame position (KQ vs K):")
    print(engine.board)
    
    # Test multiple moves to see endgame pattern behavior
    for i in range(3):
        if not engine.board.is_game_over():
            move = engine.select_move()
            if move:
                move_san = engine.board.san(move)
                engine.make_move(move)
                print(f"Move {i+1}: {move_san}")
                print(f"Game phase: {engine._get_game_phase()}")
                
                # Check if checkmate was achieved
                if engine.is_game_over():
                    print(f"Game Over! {engine.get_game_status()}")
                    break
            else:
                print("No legal moves available!")
                break
        else:
            print("Game is over!")
            break
    print()
    
    # Test 4: Engine statistics
    print("Test 4: Engine Statistics")
    final_stats = engine.get_engine_statistics()
    print(f"Total moves played: {final_stats['move_count']}")
    print(f"Final game phase: {final_stats['current_phase']}")
    
    knowledge_stats = final_stats['knowledge_stats']
    print(f"Total knowledge queries: {knowledge_stats['performance']['total_queries']}")
    print(f"Hit counts: {knowledge_stats['hit_counts']}")
    
    # Component statistics
    endgame_stats = knowledge_stats['components']['endgame_patterns']
    print(f"Endgame patterns loaded: {endgame_stats['mate_patterns']} mate patterns")
    print(f"Pawn endings: {endgame_stats['pawn_endings']} patterns")
    print(f"Tactical setups: {endgame_stats['tactical_setups']} patterns")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_enhanced_engine()
