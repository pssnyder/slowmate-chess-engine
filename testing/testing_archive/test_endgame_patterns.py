"""Test endgame pattern recognition functionality."""

import chess
from slowmate.knowledge.endgame_patterns import EndgamePatterns


def test_basic_endgame_patterns():
    """Test basic endgame pattern recognition."""
    endgame = EndgamePatterns()
    
    # Try to load patterns
    if not endgame.load_patterns():
        print("Pattern files not found, creating mock patterns for testing...")
        # Create basic test patterns
        endgame.mate_patterns = {"basic": {"KQ_vs_K": "Queen + King mate"}}
        endgame.is_loaded = True
    
    print(f"Endgame patterns loaded: {endgame.is_loaded}")
    print(f"Statistics: {endgame.get_statistics()}")
    
    # Test Queen + King vs King position
    board = chess.Board()
    board.clear()
    
    # Set up KQ vs K position
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    
    print(f"\nTest position (KQ vs K):")
    print(board)
    
    # Get strategic move
    strategic_move = endgame.get_strategic_move(board)
    
    if strategic_move:
        print(f"Strategic endgame move suggested: {strategic_move}")
        print(f"From {chess.square_name(strategic_move.from_square)} to {chess.square_name(strategic_move.to_square)}")
    else:
        print("No strategic endgame move found")
    
    # Test material signature
    material_sig = endgame._get_material_signature(board)
    print(f"Material signature: {material_sig}")
    
    # Test if position is considered endgame
    is_endgame = endgame._is_endgame_position(board)
    print(f"Position is endgame: {is_endgame}")


if __name__ == "__main__":
    test_basic_endgame_patterns()
