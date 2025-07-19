#!/usr/bin/env python3
"""
SlowMate Chess Engine - Basic Demo

This script demonstrates the basic functionality of the SlowMate engine.
It plays a complete game using random moves and shows the thought process.
"""

from slowmate.engine import SlowMateEngine


def main():
    """Run a demonstration game with the SlowMate engine."""
    print("SlowMate Chess Engine - Basic Demo")
    print("=" * 50)
    print("Playing a game with random move selection...\n")
    
    engine = SlowMateEngine()
    
    # Show initial board
    print("Initial Position:")
    print(engine.get_board_state())
    print(f"Status: {engine.get_game_status()}\n")
    
    move_number = 1
    max_moves = 200  # Prevent infinite games
    
    # Play the game
    while not engine.is_game_over() and move_number <= max_moves:
        # Show whose turn it is
        current_player = "White" if engine.board.turn else "Black"
        
        # Get legal moves count for transparency
        legal_moves = engine.get_legal_moves()
        
        print(f"Move {move_number} - {current_player}'s turn")
        print(f"Legal moves available: {len(legal_moves)}")
        
        # Engine selects and plays a move
        move_played = engine.play_random_move()
        
        if move_played is None:
            print("No legal moves available!")
            break
            
        print(f"Engine selected: {move_played}")
        print(f"Status: {engine.get_game_status()}")
        print()
        
        # Show board every 5 moves or if game is over
        if move_number % 5 == 0 or engine.is_game_over():
            print("Current Position:")
            print(engine.get_board_state())
            print()
        
        move_number += 1
    
    # Game conclusion
    print("=" * 50)
    print("GAME OVER")
    print(f"Final Status: {engine.get_game_status()}")
    print(f"Result: {engine.get_game_result()}")
    print(f"Total moves played: {engine.move_count}")
    print()
    print("Final Position:")
    print(engine.get_board_state())


if __name__ == "__main__":
    main()
