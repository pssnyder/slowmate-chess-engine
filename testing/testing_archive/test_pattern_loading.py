"""Test endgame patterns loading directly."""

from slowmate.knowledge.endgame_patterns import EndgamePatterns
import os

def test_direct_loading():
    """Test loading endgame patterns directly."""
    print("Testing direct endgame patterns loading")
    print("=" * 40)
    
    # Test with different data directories
    test_dirs = [
        "data/endgames",
        "../data/endgames",
        "./data/endgames",
        "s:/Maker Stuff/Programming/SlowMate Chess Engine/slowmate_chess_engine/data/endgames"
    ]
    
    for data_dir in test_dirs:
        print(f"\nTrying data directory: {data_dir}")
        print(f"Directory exists: {os.path.exists(data_dir)}")
        
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            print(f"Files in directory: {files}")
            
        patterns = EndgamePatterns(data_dir)
        success = patterns.load_patterns()
        
        print(f"Load successful: {success}")
        if success:
            stats = patterns.get_statistics()
            print(f"Loaded patterns: {stats}")
            break
        
    # Test with manual pattern creation (fallback)
    print("\nTesting with manual pattern creation...")
    patterns = EndgamePatterns()
    
    # Manually populate patterns
    patterns.mate_patterns = {
        "basic_mates": {
            "KQ_vs_K": {"name": "Queen and King vs King", "difficulty": "basic"},
            "KR_vs_K": {"name": "Rook and King vs King", "difficulty": "basic"}
        }
    }
    patterns.is_loaded = True
    
    stats = patterns.get_statistics()
    print(f"Manual patterns: {stats}")
    
    # Test actual move generation
    import chess
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    
    move = patterns.get_strategic_move(board)
    if move:
        print(f"Strategic move found: {board.san(move)}")
    else:
        print("No strategic move found")

if __name__ == "__main__":
    test_direct_loading()
