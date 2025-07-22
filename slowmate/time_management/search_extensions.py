"""
Search Extensions for SlowMate v0.2.02 Phase 3
Selective search depth extensions based on position characteristics.
"""

from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import chess

from .time_allocation import TimeAllocation


class ExtensionType(Enum):
    """Different types of search extensions."""
    CHECK = "check"                    # Extend when in check
    CAPTURE = "capture"                # Extend on captures
    PROMOTION = "promotion"            # Extend on pawn promotions
    THREAT = "threat"                  # Extend when under threat
    SINGULAR = "singular"              # Extend singular moves
    RECAPTURE = "recapture"           # Extend recaptures
    PASSED_PAWN = "passed_pawn"       # Extend passed pawn advances
    MATE_THREAT = "mate_threat"       # Extend mate threats
    ENDGAME = "endgame"               # Extend in endgames
    PV_NODE = "pv_node"               # Extend PV nodes


@dataclass
class ExtensionConfig:
    """Configuration for search extensions."""
    enabled_extensions: Set[ExtensionType]
    max_extensions_per_path: int = 6     # Maximum extensions in one line
    reduction_threshold: int = 3         # Depth where reductions start
    
    # Extension amounts (in plies)
    extension_amounts: Optional[Dict[ExtensionType, int]] = None
    
    # Conditions for extensions
    min_depth_for_extensions: int = 3    # Minimum depth to allow extensions
    time_factor_threshold: float = 2.0   # Don't extend if time is too tight
    
    def __post_init__(self):
        if self.extension_amounts is None:
            self.extension_amounts = {
                ExtensionType.CHECK: 1,            # Full ply for checks
                ExtensionType.CAPTURE: 1,          # Full ply for good captures
                ExtensionType.PROMOTION: 1,        # Full ply for promotions
                ExtensionType.THREAT: 1,           # Full ply for threats
                ExtensionType.SINGULAR: 2,         # Two plies for singular moves
                ExtensionType.RECAPTURE: 1,        # Full ply for recaptures
                ExtensionType.PASSED_PAWN: 1,      # Full ply for passed pawns
                ExtensionType.MATE_THREAT: 2,      # Two plies for mate threats
                ExtensionType.ENDGAME: 1,          # Full ply in endgames
                ExtensionType.PV_NODE: 1           # Full ply on PV
            }


@dataclass
class ExtensionAnalysis:
    """Analysis result for search extension decisions."""
    extensions_to_apply: List[Tuple[ExtensionType, int]]  # (type, amount)
    total_extension: int                                   # Total extension amount
    extension_reasons: List[str]                          # Human-readable reasons
    position_characteristics: Dict[str, bool]             # Position features
    
    @property
    def should_extend(self) -> bool:
        """Whether any extensions should be applied."""
        return self.total_extension > 0


class SearchExtensionManager:
    """
    Manages selective search extensions to improve tactical strength.
    
    Extensions allow the engine to search deeper in tactically critical
    positions while maintaining reasonable time usage.
    """
    
    def __init__(self, config: Optional[ExtensionConfig] = None):
        self.config = config or ExtensionConfig(
            enabled_extensions={
                ExtensionType.CHECK,
                ExtensionType.CAPTURE, 
                ExtensionType.PROMOTION,
                ExtensionType.RECAPTURE,
                ExtensionType.MATE_THREAT
            }
        )
        
        # Extension tracking
        self.extension_history: Dict[str, int] = {}
        self.extensions_used: Dict[ExtensionType, int] = {
            ext_type: 0 for ext_type in ExtensionType
        }
        
        # Performance tracking
        self.extension_performance: Dict[ExtensionType, List[float]] = {
            ext_type: [] for ext_type in ExtensionType
        }
    
    def analyze_extensions(
        self,
        position: chess.Board,
        move: chess.Move,
        depth: int,
        alpha: float,
        beta: float,
        extensions_in_path: int,
        time_allocation: TimeAllocation,
        is_pv_node: bool = False,
        previous_move: Optional[chess.Move] = None
    ) -> ExtensionAnalysis:
        """
        Analyze whether extensions should be applied to this position.
        
        Args:
            position: Current chess position
            move: Move being analyzed
            depth: Current search depth
            alpha: Alpha value
            beta: Beta value  
            extensions_in_path: Extensions already applied in this line
            time_allocation: Current time allocation
            is_pv_node: Whether this is a PV node
            previous_move: Previous move played
            
        Returns:
            ExtensionAnalysis with extension decisions
        """
        extensions_to_apply = []
        reasons = []
        characteristics = {}
        
        # Check basic conditions for extensions
        if not self._should_allow_extensions(
            depth, extensions_in_path, time_allocation
        ):
            return ExtensionAnalysis(
                extensions_to_apply=[],
                total_extension=0,
                extension_reasons=["Extensions disabled by conditions"],
                position_characteristics=characteristics
            )
        
        # Make the move to analyze resulting position
        position.push(move)
        
        try:
            # Analyze position characteristics
            characteristics = self._analyze_position_characteristics(
                position, move, previous_move
            )
            
            # Check each enabled extension type
            for ext_type in self.config.enabled_extensions:
                extension_amount = self._evaluate_extension(
                    ext_type, position, move, characteristics, 
                    is_pv_node, alpha, beta
                )
                
                if extension_amount > 0:
                    extensions_to_apply.append((ext_type, extension_amount))
                    reasons.append(self._get_extension_reason(ext_type, characteristics))
        
        finally:
            position.pop()
        
        # Calculate total extension (with limits)
        total_extension = min(
            sum(amount for _, amount in extensions_to_apply),
            2  # Maximum 2 plies extension per node
        )
        
        return ExtensionAnalysis(
            extensions_to_apply=extensions_to_apply,
            total_extension=total_extension,
            extension_reasons=reasons,
            position_characteristics=characteristics
        )
    
    def _should_allow_extensions(
        self,
        depth: int,
        extensions_in_path: int,
        time_allocation: TimeAllocation
    ) -> bool:
        """Check if extensions should be allowed in current situation."""
        # Don't extend if depth is too shallow
        if depth < self.config.min_depth_for_extensions:
            return False
        
        # Don't extend if too many extensions already in this path
        if extensions_in_path >= self.config.max_extensions_per_path:
            return False
        
        # Don't extend if time is very tight
        if (time_allocation.has_emergency_time and 
            extensions_in_path >= 2):
            return False
        
        return True
    
    def _analyze_position_characteristics(
        self,
        position: chess.Board,
        move: chess.Move,
        previous_move: Optional[chess.Move]
    ) -> Dict[str, bool]:
        """Analyze characteristics relevant for extensions."""
        characteristics = {}
        
        # Basic position features
        characteristics['in_check'] = position.is_check()
        characteristics['is_capture'] = position.piece_at(move.to_square) is not None
        characteristics['is_promotion'] = move.promotion is not None
        characteristics['is_checkmate'] = position.is_checkmate()
        characteristics['is_stalemate'] = position.is_stalemate()
        
        # Tactical features
        characteristics['gives_check'] = self._move_gives_check(position, move)
        characteristics['is_recapture'] = self._is_recapture(move, previous_move)
        characteristics['threatens_mate'] = self._threatens_mate(position)
        characteristics['under_threat'] = self._is_under_threat(position)
        
        # Strategic features
        characteristics['is_endgame'] = self._is_endgame(position)
        characteristics['advances_passed_pawn'] = self._advances_passed_pawn(position, move)
        characteristics['is_singular'] = self._is_singular_move(position, move)
        
        # Positional features  
        characteristics['reduces_mobility'] = self._reduces_opponent_mobility(position)
        characteristics['improves_king_safety'] = self._improves_king_safety(position, move)
        
        return characteristics
    
    def _evaluate_extension(
        self,
        ext_type: ExtensionType,
        position: chess.Board,
        move: chess.Move,
        characteristics: Dict[str, bool],
        is_pv_node: bool,
        alpha: float,
        beta: float
    ) -> int:
        """Evaluate whether a specific extension type should be applied."""
        extension_amounts = self.config.extension_amounts or {
            ExtensionType.CHECK: 1,
            ExtensionType.CAPTURE: 1,
            ExtensionType.PROMOTION: 1,
            ExtensionType.THREAT: 1,
            ExtensionType.SINGULAR: 2,
            ExtensionType.RECAPTURE: 1,
            ExtensionType.PASSED_PAWN: 1,
            ExtensionType.MATE_THREAT: 2,
            ExtensionType.ENDGAME: 1,
            ExtensionType.PV_NODE: 1
        }
        base_amount = extension_amounts.get(ext_type, 0)
        
        if ext_type == ExtensionType.CHECK:
            return base_amount if characteristics['in_check'] else 0
            
        elif ext_type == ExtensionType.CAPTURE:
            if characteristics['is_capture']:
                # Only extend good captures (simplified)
                return base_amount if self._is_good_capture(position, move) else 0
            return 0
            
        elif ext_type == ExtensionType.PROMOTION:
            return base_amount if characteristics['is_promotion'] else 0
            
        elif ext_type == ExtensionType.THREAT:
            return base_amount if characteristics['under_threat'] else 0
            
        elif ext_type == ExtensionType.SINGULAR:
            return base_amount if characteristics['is_singular'] else 0
            
        elif ext_type == ExtensionType.RECAPTURE:
            return base_amount if characteristics['is_recapture'] else 0
            
        elif ext_type == ExtensionType.PASSED_PAWN:
            return base_amount if characteristics['advances_passed_pawn'] else 0
            
        elif ext_type == ExtensionType.MATE_THREAT:
            return base_amount if characteristics['threatens_mate'] else 0
            
        elif ext_type == ExtensionType.ENDGAME:
            return base_amount if characteristics['is_endgame'] else 0
            
        elif ext_type == ExtensionType.PV_NODE:
            return base_amount if is_pv_node else 0
        
        return 0
    
    def _move_gives_check(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move gives check (position is after move)."""
        # We're analyzing the position after the move, so we need to check
        # if the opponent king is in check
        return position.is_check()
    
    def _is_recapture(self, move: chess.Move, previous_move: Optional[chess.Move]) -> bool:
        """Check if move is a recapture."""
        if not previous_move:
            return False
        
        # Recapture if we're capturing on the square the opponent just moved to
        return move.to_square == previous_move.to_square
    
    def _threatens_mate(self, position: chess.Board) -> bool:
        """Check if position threatens mate in 1."""
        # Simple check: do any of our moves result in checkmate?
        for move in position.legal_moves:
            position.push(move)
            is_mate = position.is_checkmate()
            position.pop()
            if is_mate:
                return True
        return False
    
    def _is_under_threat(self, position: chess.Board) -> bool:
        """Check if our pieces are under significant threat."""
        # Simplified: check if opponent has many attacking moves
        attacking_moves = 0
        for move in position.legal_moves:
            if position.piece_at(move.to_square):  # Capture
                attacking_moves += 1
        
        return attacking_moves >= 3
    
    def _is_endgame(self, position: chess.Board) -> bool:
        """Check if position is in endgame phase."""
        # Simple endgame detection: few pieces remaining
        piece_count = len(position.piece_map())
        return piece_count <= 12
    
    def _advances_passed_pawn(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move advances a passed pawn."""
        piece = position.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False
        
        # Simplified passed pawn detection
        # This would need more sophisticated logic for a real implementation
        return self._is_passed_pawn(position, move.from_square, piece.color)
    
    def _is_passed_pawn(self, position: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if pawn is passed (simplified)."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        # Check if there are opponent pawns blocking this pawn's path
        if color == chess.WHITE:
            # Check ranks ahead of this pawn
            for check_rank in range(rank + 1, 8):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        piece = position.piece_at(check_square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == chess.BLACK:
                            return False
        else:
            # Check ranks ahead of this pawn (for black)
            for check_rank in range(rank - 1, -1, -1):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        piece = position.piece_at(check_square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == chess.WHITE:
                            return False
        
        return True
    
    def _is_singular_move(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move is singular (only good move)."""
        # This is a simplified check - in practice, this would require 
        # a reduced-depth search to verify other moves are worse
        legal_moves = list(position.legal_moves)
        
        # If very few legal moves, the move might be singular
        if len(legal_moves) <= 2:
            return True
        
        # Check if move is only legal move that doesn't lose material
        # (This is a very simplified implementation)
        return False
    
    def _reduces_opponent_mobility(self, position: chess.Board) -> bool:
        """Check if position significantly reduces opponent mobility."""
        legal_moves_count = len(list(position.legal_moves))
        return legal_moves_count < 5  # Arbitrary threshold
    
    def _improves_king_safety(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move improves our king safety."""
        # Simplified king safety check
        our_king = position.king(not position.turn)  # Our king (before move)
        if our_king is None:
            return False
        
        # Check if king is less attacked after our move
        attacks_before = len([
            m for m in position.legal_moves 
            if m.to_square == our_king
        ])
        
        return attacks_before > 0  # Any reduction in attacks is good
    
    def _is_good_capture(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if capture is tactically sound."""
        # Simplified good capture check
        captured_piece = position.piece_at(move.to_square)
        capturing_piece = position.piece_at(move.from_square)
        
        if not captured_piece or not capturing_piece:
            return False
        
        # Basic material value comparison
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        captured_value = piece_values.get(captured_piece.piece_type, 0)
        capturing_value = piece_values.get(capturing_piece.piece_type, 0)
        
        # Good capture if we gain material or equal exchange
        return captured_value >= capturing_value
    
    def _get_extension_reason(self, ext_type: ExtensionType, characteristics: Dict[str, bool]) -> str:
        """Get human-readable reason for extension."""
        reasons = {
            ExtensionType.CHECK: "Position is in check",
            ExtensionType.CAPTURE: "Good capture opportunity",
            ExtensionType.PROMOTION: "Pawn promotion",
            ExtensionType.THREAT: "Under significant threat",
            ExtensionType.SINGULAR: "Only good move available",
            ExtensionType.RECAPTURE: "Recapture sequence",
            ExtensionType.PASSED_PAWN: "Passed pawn advance",
            ExtensionType.MATE_THREAT: "Threatening checkmate",
            ExtensionType.ENDGAME: "Critical endgame position",
            ExtensionType.PV_NODE: "Principal variation node"
        }
        return reasons.get(ext_type, f"Extension type {ext_type.value}")
    
    def record_extension_performance(
        self, 
        ext_type: ExtensionType, 
        performance_score: float
    ):
        """Record performance data for extension type."""
        self.extension_performance[ext_type].append(performance_score)
        self.extensions_used[ext_type] += 1
        
        # Keep only recent performance data
        if len(self.extension_performance[ext_type]) > 100:
            self.extension_performance[ext_type] = self.extension_performance[ext_type][-100:]
    
    def get_extension_statistics(self) -> Dict[str, Any]:
        """Get statistics on extension usage and performance."""
        stats = {}
        
        for ext_type in ExtensionType:
            usage_count = self.extensions_used[ext_type]
            performances = self.extension_performance[ext_type]
            
            if usage_count > 0 and performances:
                avg_performance = sum(performances) / len(performances)
                stats[ext_type.value] = {
                    "usage_count": usage_count,
                    "average_performance": avg_performance,
                    "total_evaluations": len(performances)
                }
            else:
                stats[ext_type.value] = {"usage_count": 0}
        
        return stats
    
    def update_config(self, new_config: ExtensionConfig):
        """Update extension configuration."""
        self.config = new_config
        
    def reset_statistics(self):
        """Reset performance tracking statistics."""
        self.extensions_used = {ext_type: 0 for ext_type in ExtensionType}
        self.extension_performance = {ext_type: [] for ext_type in ExtensionType}


# Export main classes
__all__ = [
    'ExtensionType',
    'ExtensionConfig',
    'ExtensionAnalysis', 
    'SearchExtensionManager'
]


def main():
    """Test the search extension system."""
    import chess
    from .time_allocation import TimeAllocation, AllocationStrategy
    
    # Create extension manager with default config
    extension_manager = SearchExtensionManager()
    
    # Test time allocation
    time_allocation = TimeAllocation(
        target_time_ms=5000,
        maximum_time_ms=10000,
        minimum_time_ms=1000,
        soft_limit_ms=4000,
        hard_limit_ms=8000,
        strategy=AllocationStrategy.ADAPTIVE
    )
    
    # Test positions and moves
    test_cases = [
        ("Check extension", "rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 0 5", "c4f7"),
        ("Capture extension", "rnbqkb1r/ppp2ppp/5n2/3Pp3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w kq e6 0 6", "d5e6"),
        ("Promotion", "8/P7/8/8/8/8/8/k6K w - - 0 1", "a7a8q"),
        ("Normal move", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "e7e5")
    ]
    
    print("Search Extension Analysis Test:")
    print("=" * 50)
    
    for test_name, fen, move_uci in test_cases:
        position = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        
        if move not in position.legal_moves:
            print(f"\n{test_name}: INVALID MOVE")
            continue
        
        # Analyze extensions
        analysis = extension_manager.analyze_extensions(
            position=position,
            move=move,
            depth=4,
            alpha=-1.0,
            beta=1.0,
            extensions_in_path=0,
            time_allocation=time_allocation,
            is_pv_node=True
        )
        
        print(f"\n{test_name}:")
        print(f"  Move: {move_uci}")
        print(f"  Should extend: {analysis.should_extend}")
        print(f"  Total extension: {analysis.total_extension} plies")
        
        if analysis.extensions_to_apply:
            print("  Extensions to apply:")
            for ext_type, amount in analysis.extensions_to_apply:
                print(f"    - {ext_type.value}: +{amount} plies")
        
        if analysis.extension_reasons:
            print("  Reasons:")
            for reason in analysis.extension_reasons:
                print(f"    - {reason}")
        
        print("  Position characteristics:")
        for char, value in analysis.position_characteristics.items():
            if value:
                print(f"    - {char}: {value}")
        
        print("-" * 40)
    
    # Test configuration
    print("\nExtension Configuration:")
    print(f"Enabled extensions: {[ext.value for ext in extension_manager.config.enabled_extensions]}")
    print(f"Max extensions per path: {extension_manager.config.max_extensions_per_path}")
    print(f"Minimum depth for extensions: {extension_manager.config.min_depth_for_extensions}")
    
    # Test statistics
    stats = extension_manager.get_extension_statistics()
    print("\nExtension Statistics:")
    for ext_type, data in stats.items():
        print(f"  {ext_type}: {data['usage_count']} uses")


if __name__ == "__main__":
    main()
