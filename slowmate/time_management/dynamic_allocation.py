"""
Dynamic Time Allocation for SlowMate v0.2.02 Phase 3
Adaptive time budgeting based on position complexity and game context.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import chess
import statistics

from .time_control import TimeControl
from .time_allocation import TimeAllocation, TimeAllocator, AllocationStrategy
from .time_tracking import TimeTracker, MoveTimeRecord


class PositionType(Enum):
    """Different types of chess positions requiring different time allocation."""
    TACTICAL = "tactical"          # Positions with tactical opportunities
    STRATEGIC = "strategic"        # Quiet positional play
    CRITICAL = "critical"          # Critical decisions (piece sacrifices, king safety)
    FORCING = "forcing"            # Forcing sequences (checks, captures, threats)
    ENDGAME = "endgame"           # Endgame positions
    OPENING = "opening"            # Opening phase
    TRANSITION = "transition"      # Game phase transitions


class GameContext(Enum):
    """Game context that affects time allocation."""
    NORMAL = "normal"              # Normal game flow
    TIME_PRESSURE = "time_pressure"  # Under time pressure
    WINNING = "winning"            # Ahead in material/position
    LOSING = "losing"              # Behind in material/position
    EQUAL = "equal"                # Roughly equal position
    MUST_WIN = "must_win"          # Must win situation
    DEFENDING = "defending"        # Under attack/defending


@dataclass
class PositionAnalysis:
    """Analysis of current position for time allocation decisions."""
    complexity_score: float        # Overall complexity (0-1)
    position_type: PositionType   # Type of position
    game_context: GameContext     # Current game context
    tactical_density: float       # Density of tactical opportunities (0-1)
    strategic_importance: float   # Strategic importance of decision (0-1)
    forcing_factor: float         # How forcing the position is (0-1)
    time_sensitivity: float       # How time-sensitive the decision is (0-1)
    
    # Specific factors
    material_balance: float       # Material advantage (-1 to 1)
    king_safety_white: float      # White king safety (0-1)
    king_safety_black: float      # Black king safety (0-1)
    piece_activity: float         # Overall piece activity (0-1)
    pawn_structure_quality: float # Pawn structure health (0-1)


class DynamicTimeAllocator:
    """
    Advanced time allocator that adapts allocation based on position analysis.
    
    This allocator considers multiple factors:
    - Position complexity and type
    - Current game context (winning/losing/equal)
    - Historical performance patterns
    - Time pressure situation
    - Critical decision points
    """
    
    def __init__(self, base_allocator: Optional[TimeAllocator] = None):
        self.base_allocator = base_allocator or TimeAllocator()
        self.position_analyzer = PositionAnalyzer()
        
        # Dynamic allocation factors
        self.complexity_multipliers = {
            PositionType.TACTICAL: 1.5,      # Tactical positions need more time
            PositionType.CRITICAL: 2.0,      # Critical decisions need much more time
            PositionType.FORCING: 1.2,       # Forcing positions need some extra time
            PositionType.STRATEGIC: 0.9,     # Strategic positions can be quicker
            PositionType.ENDGAME: 1.3,       # Endgames need precision
            PositionType.OPENING: 0.7,       # Openings should be fast
            PositionType.TRANSITION: 1.1     # Transitions need slight extra time
        }
        
        self.context_multipliers = {
            GameContext.NORMAL: 1.0,
            GameContext.TIME_PRESSURE: 0.6,  # Forced to move faster
            GameContext.WINNING: 0.8,        # Can play more quickly when winning
            GameContext.LOSING: 1.4,         # Need more time when behind
            GameContext.EQUAL: 1.0,          # Normal time usage
            GameContext.MUST_WIN: 1.8,       # Critical situations need more time
            GameContext.DEFENDING: 1.3       # Defense requires careful calculation
        }
        
        # Adaptive learning from historical performance
        self.performance_history: List[Tuple[PositionAnalysis, MoveTimeRecord]] = []
        self.learned_adjustments: Dict[str, float] = {}
        
    def allocate_time_dynamic(
        self,
        position: chess.Board,
        base_allocation: TimeAllocation,
        time_control: TimeControl,
        move_number: int,
        time_tracker: Optional[TimeTracker] = None
    ) -> TimeAllocation:
        """
        Perform dynamic time allocation based on position analysis.
        
        Args:
            position: Current chess position
            base_allocation: Base time allocation from standard allocator
            time_control: Time control being used
            move_number: Current move number
            time_tracker: Time tracker for historical data
        
        Returns:
            Dynamically adjusted TimeAllocation
        """
        # Analyze current position
        analysis = self.position_analyzer.analyze_position(position, move_number)
        
        # Calculate dynamic multiplier
        base_multiplier = self._calculate_base_multiplier(analysis)
        
        # Apply historical learning adjustments
        learned_multiplier = self._apply_learned_adjustments(analysis, time_tracker)
        
        # Combine multipliers
        final_multiplier = base_multiplier * learned_multiplier
        
        # Apply safety constraints
        final_multiplier = self._apply_safety_constraints(
            final_multiplier, 
            base_allocation, 
            time_control,
            analysis
        )
        
        # Create adjusted allocation
        adjusted_allocation = self._create_adjusted_allocation(
            base_allocation, 
            final_multiplier, 
            analysis
        )
        
        return adjusted_allocation
    
    def _calculate_base_multiplier(self, analysis: PositionAnalysis) -> float:
        """Calculate base multiplier from position analysis."""
        # Start with position type multiplier
        type_multiplier = self.complexity_multipliers.get(analysis.position_type, 1.0)
        
        # Apply context multiplier
        context_multiplier = self.context_multipliers.get(analysis.game_context, 1.0)
        
        # Apply complexity score (0-1 becomes 0.7-1.3 multiplier)
        complexity_multiplier = 0.7 + (analysis.complexity_score * 0.6)
        
        # Apply tactical density factor
        tactical_multiplier = 1.0 + (analysis.tactical_density * 0.4)
        
        # Apply time sensitivity
        sensitivity_multiplier = 1.0 + (analysis.time_sensitivity * 0.3)
        
        # Combine all factors
        base_multiplier = (
            type_multiplier * 
            context_multiplier * 
            complexity_multiplier * 
            tactical_multiplier * 
            sensitivity_multiplier
        )
        
        return base_multiplier
    
    def _apply_learned_adjustments(
        self, 
        analysis: PositionAnalysis, 
        time_tracker: Optional[TimeTracker]
    ) -> float:
        """Apply learned adjustments based on historical performance."""
        if not time_tracker or len(self.performance_history) < 10:
            return 1.0  # Not enough data for learning
        
        # Find similar positions in history
        similar_positions = self._find_similar_positions(analysis)
        
        if not similar_positions:
            return 1.0  # No similar positions found
        
        # Calculate average efficiency for similar positions
        efficiencies = [record.efficiency for _, record in similar_positions]
        avg_efficiency = statistics.mean(efficiencies)
        
        # If efficiency is too low, suggest using more time
        if avg_efficiency < 0.6:
            return 1.3  # Use 30% more time
        elif avg_efficiency > 0.9:
            return 0.9  # Use 10% less time (we're being too conservative)
        else:
            return 1.0  # Good balance
    
    def _find_similar_positions(
        self, 
        current_analysis: PositionAnalysis
    ) -> List[Tuple[PositionAnalysis, MoveTimeRecord]]:
        """Find historically similar positions."""
        similar = []
        
        for analysis, record in self.performance_history:
            similarity = self._calculate_position_similarity(current_analysis, analysis)
            if similarity > 0.7:  # 70% similarity threshold
                similar.append((analysis, record))
        
        return similar[-20:]  # Return most recent 20 similar positions
    
    def _calculate_position_similarity(
        self, 
        pos1: PositionAnalysis, 
        pos2: PositionAnalysis
    ) -> float:
        """Calculate similarity between two position analyses."""
        similarity = 0.0
        
        # Position type similarity
        if pos1.position_type == pos2.position_type:
            similarity += 0.3
        
        # Game context similarity  
        if pos1.game_context == pos2.game_context:
            similarity += 0.2
        
        # Numerical factor similarities
        factors = [
            ('complexity_score', 0.2),
            ('tactical_density', 0.15),
            ('strategic_importance', 0.1),
            ('time_sensitivity', 0.05)
        ]
        
        for factor, weight in factors:
            val1 = getattr(pos1, factor)
            val2 = getattr(pos2, factor)
            factor_similarity = 1.0 - abs(val1 - val2)
            similarity += factor_similarity * weight
        
        return min(1.0, similarity)
    
    def _apply_safety_constraints(
        self,
        multiplier: float,
        base_allocation: TimeAllocation,
        time_control: TimeControl,
        analysis: PositionAnalysis
    ) -> float:
        """Apply safety constraints to prevent time forfeit."""
        # Never use more than 3x base allocation
        multiplier = min(multiplier, 3.0)
        
        # In time pressure, cap the multiplier more strictly
        if analysis.game_context == GameContext.TIME_PRESSURE:
            multiplier = min(multiplier, 1.2)
        
        # Emergency situations - strict limits
        if base_allocation.has_emergency_time:
            multiplier = min(multiplier, 0.8)
        
        # Never go below 0.3x base allocation (need minimum thinking time)
        multiplier = max(multiplier, 0.3)
        
        return multiplier
    
    def _create_adjusted_allocation(
        self,
        base_allocation: TimeAllocation,
        multiplier: float,
        analysis: PositionAnalysis
    ) -> TimeAllocation:
        """Create new allocation with dynamic adjustments."""
        # Apply multiplier to target time
        new_target = int(base_allocation.target_time_ms * multiplier)
        
        # Adjust soft and hard limits proportionally, but with safety margins
        new_soft = int(base_allocation.soft_limit_ms * min(multiplier, 2.0))
        new_hard = int(base_allocation.hard_limit_ms * min(multiplier, 1.5))
        
        # Ensure logical ordering
        new_target = max(base_allocation.minimum_time_ms, new_target)
        new_soft = max(new_target, new_soft)
        new_hard = max(new_soft, new_hard)
        
        # Create adjusted allocation
        adjusted_allocation = TimeAllocation(
            target_time_ms=new_target,
            maximum_time_ms=new_hard,
            minimum_time_ms=base_allocation.minimum_time_ms,
            soft_limit_ms=new_soft,
            hard_limit_ms=new_hard,
            strategy=base_allocation.strategy,
            confidence=base_allocation.confidence * min(1.0, multiplier)
        )
        
        return adjusted_allocation
    
    def record_performance(
        self, 
        analysis: PositionAnalysis, 
        move_record: MoveTimeRecord
    ):
        """Record performance data for future learning."""
        self.performance_history.append((analysis, move_record))
        
        # Keep only recent history (last 1000 positions)
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def get_allocation_explanation(
        self, 
        analysis: PositionAnalysis, 
        base_allocation: TimeAllocation,
        final_allocation: TimeAllocation
    ) -> str:
        """Get human-readable explanation of allocation decision."""
        multiplier = final_allocation.target_time_ms / max(1, base_allocation.target_time_ms)
        
        explanation = f"Dynamic time allocation (multiplier: {multiplier:.2f})\n"
        explanation += f"  Position type: {analysis.position_type.value}\n"
        explanation += f"  Game context: {analysis.game_context.value}\n"
        explanation += f"  Complexity: {analysis.complexity_score:.2f}\n"
        explanation += f"  Tactical density: {analysis.tactical_density:.2f}\n"
        explanation += f"  Time sensitivity: {analysis.time_sensitivity:.2f}\n"
        explanation += f"  Base allocation: {base_allocation.target_time_ms}ms\n"
        explanation += f"  Final allocation: {final_allocation.target_time_ms}ms"
        
        return explanation


class PositionAnalyzer:
    """Analyzes chess positions for dynamic time allocation decisions."""
    
    def analyze_position(
        self, 
        position: chess.Board, 
        move_number: int
    ) -> PositionAnalysis:
        """
        Analyze a chess position for time allocation purposes.
        
        Args:
            position: Chess position to analyze
            move_number: Current move number
        
        Returns:
            PositionAnalysis with all relevant factors
        """
        # Basic position metrics
        material_balance = self._calculate_material_balance(position)
        king_safety_white, king_safety_black = self._analyze_king_safety(position)
        piece_activity = self._calculate_piece_activity(position)
        pawn_structure = self._analyze_pawn_structure(position)
        
        # Tactical analysis
        tactical_density = self._calculate_tactical_density(position)
        forcing_factor = self._calculate_forcing_factor(position)
        
        # Position classification
        position_type = self._classify_position_type(
            position, move_number, tactical_density, material_balance
        )
        
        # Game context
        game_context = self._determine_game_context(
            position, material_balance, king_safety_white, king_safety_black
        )
        
        # Strategic importance
        strategic_importance = self._calculate_strategic_importance(position, move_number)
        
        # Time sensitivity
        time_sensitivity = self._calculate_time_sensitivity(
            position, position_type, game_context
        )
        
        # Overall complexity
        complexity_score = self._calculate_overall_complexity(
            tactical_density, strategic_importance, forcing_factor, position_type
        )
        
        return PositionAnalysis(
            complexity_score=complexity_score,
            position_type=position_type,
            game_context=game_context,
            tactical_density=tactical_density,
            strategic_importance=strategic_importance,
            forcing_factor=forcing_factor,
            time_sensitivity=time_sensitivity,
            material_balance=material_balance,
            king_safety_white=king_safety_white,
            king_safety_black=king_safety_black,
            piece_activity=piece_activity,
            pawn_structure_quality=pawn_structure
        )
    
    def _calculate_material_balance(self, position: chess.Board) -> float:
        """Calculate material balance (-1 to 1, positive = white advantage)."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = position.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        total_material = white_material + black_material
        if total_material == 0:
            return 0.0
        
        balance = (white_material - black_material) / total_material
        return max(-1.0, min(1.0, balance))
    
    def _analyze_king_safety(self, position: chess.Board) -> Tuple[float, float]:
        """Analyze king safety for both sides (0-1, higher = safer)."""
        white_king_square = position.king(chess.WHITE)
        black_king_square = position.king(chess.BLACK)
        
        if white_king_square is None or black_king_square is None:
            return 0.5, 0.5
        
        white_safety = self._calculate_king_safety(position, white_king_square, chess.WHITE)
        black_safety = self._calculate_king_safety(position, black_king_square, chess.BLACK)
        
        return white_safety, black_safety
    
    def _calculate_king_safety(
        self, 
        position: chess.Board, 
        king_square: chess.Square,
        king_color: chess.Color
    ) -> float:
        """Calculate king safety for one side."""
        safety_score = 0.5  # Base safety
        
        # Check if king is under attack
        if position.is_attacked_by(not king_color, king_square):
            safety_score -= 0.3
        
        # Check for checks
        if position.is_check():
            safety_score -= 0.2
        
        # Pawn shield analysis (simplified)
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check for pawn shield in front of king
        shield_squares = []
        if king_color == chess.WHITE:
            if king_rank < 7:
                shield_squares = [
                    chess.square(f, king_rank + 1) 
                    for f in [king_file - 1, king_file, king_file + 1]
                    if 0 <= f <= 7
                ]
        else:
            if king_rank > 0:
                shield_squares = [
                    chess.square(f, king_rank - 1)
                    for f in [king_file - 1, king_file, king_file + 1] 
                    if 0 <= f <= 7
                ]
        
        # Count pawns in shield
        shield_pawns = 0
        for square in shield_squares:
            piece = position.piece_at(square)
            if piece and piece.piece_type == chess.PAWN and piece.color == king_color:
                shield_pawns += 1
        
        safety_score += shield_pawns * 0.1
        
        return max(0.0, min(1.0, safety_score))
    
    def _calculate_piece_activity(self, position: chess.Board) -> float:
        """Calculate overall piece activity (0-1)."""
        total_mobility = 0
        piece_count = 0
        
        for square in chess.SQUARES:
            piece = position.piece_at(square)
            if piece and piece.piece_type != chess.PAWN:
                # Count legal moves for this piece
                piece_moves = 0
                for move in position.legal_moves:
                    if move.from_square == square:
                        piece_moves += 1
                
                total_mobility += piece_moves
                piece_count += 1
        
        if piece_count == 0:
            return 0.5
        
        avg_mobility = total_mobility / piece_count
        return min(1.0, avg_mobility / 10.0)  # Normalize to 0-1
    
    def _analyze_pawn_structure(self, position: chess.Board) -> float:
        """Analyze pawn structure quality (0-1)."""
        # Simplified pawn structure analysis
        white_pawns = position.pieces(chess.PAWN, chess.WHITE)
        black_pawns = position.pieces(chess.PAWN, chess.BLACK)
        
        structure_score = 0.5  # Base score
        
        # Count doubled pawns (penalty)
        for color, pawns in [(chess.WHITE, white_pawns), (chess.BLACK, black_pawns)]:
            files_with_pawns = defaultdict(int)
            for pawn_square in pawns:
                files_with_pawns[chess.square_file(pawn_square)] += 1
            
            doubled_pawns = sum(max(0, count - 1) for count in files_with_pawns.values())
            structure_score -= doubled_pawns * 0.05
        
        # Count isolated pawns (penalty) - simplified
        # This is a basic implementation
        
        return max(0.0, min(1.0, structure_score))
    
    def _calculate_tactical_density(self, position: chess.Board) -> float:
        """Calculate density of tactical opportunities (0-1)."""
        tactical_score = 0.0
        
        # Count captures
        captures = [move for move in position.legal_moves if position.is_capture(move)]
        tactical_score += len(captures) * 0.1
        
        # Count checks
        checks = [move for move in position.legal_moves if position.gives_check(move)]
        tactical_score += len(checks) * 0.15
        
        # Check if in check
        if position.is_check():
            tactical_score += 0.3
        
        # Count attacks on pieces
        attacked_squares = 0
        for square in chess.SQUARES:
            if position.is_attacked_by(chess.WHITE, square) or position.is_attacked_by(chess.BLACK, square):
                attacked_squares += 1
        
        tactical_score += (attacked_squares / 64) * 0.2
        
        return min(1.0, tactical_score)
    
    def _calculate_forcing_factor(self, position: chess.Board) -> float:
        """Calculate how forcing the current position is (0-1)."""
        forcing_score = 0.0
        
        # Checks are forcing
        if position.is_check():
            forcing_score += 0.4
        
        # Limited legal moves = more forcing
        legal_moves_count = len(list(position.legal_moves))
        if legal_moves_count < 10:
            forcing_score += (10 - legal_moves_count) * 0.05
        
        # Captures are somewhat forcing
        captures = [move for move in position.legal_moves if position.is_capture(move)]
        forcing_score += len(captures) * 0.02
        
        return min(1.0, forcing_score)
    
    def _classify_position_type(
        self, 
        position: chess.Board, 
        move_number: int,
        tactical_density: float,
        material_balance: float
    ) -> PositionType:
        """Classify the type of position."""
        # Opening phase
        if move_number <= 15:
            return PositionType.OPENING
        
        # Endgame phase (simplified check)
        total_pieces = len(position.piece_map())
        if total_pieces <= 12:
            return PositionType.ENDGAME
        
        # High tactical density = tactical position
        if tactical_density > 0.6:
            return PositionType.TACTICAL
        
        # In check or critical material imbalance = critical
        if position.is_check() or abs(material_balance) > 0.3:
            return PositionType.CRITICAL
        
        # Check for forcing moves
        legal_moves = list(position.legal_moves)
        checks = [move for move in legal_moves if position.gives_check(move)]
        if len(checks) > len(legal_moves) * 0.3:
            return PositionType.FORCING
        
        # Transition between phases
        if 15 < move_number <= 25 or 25 <= total_pieces <= 20:
            return PositionType.TRANSITION
        
        # Default to strategic
        return PositionType.STRATEGIC
    
    def _determine_game_context(
        self,
        position: chess.Board,
        material_balance: float,
        king_safety_white: float,
        king_safety_black: float
    ) -> GameContext:
        """Determine current game context."""
        # Determine which side we're analyzing for
        to_move = position.turn
        
        if to_move == chess.WHITE:
            our_material = material_balance
            our_king_safety = king_safety_white
            opponent_king_safety = king_safety_black
        else:
            our_material = -material_balance
            our_king_safety = king_safety_black  
            opponent_king_safety = king_safety_white
        
        # Winning/losing based on material
        if our_material > 0.15:
            return GameContext.WINNING
        elif our_material < -0.15:
            return GameContext.LOSING
        
        # Under attack = defending
        if our_king_safety < 0.3:
            return GameContext.DEFENDING
        
        # Opponent under attack = attacking advantage
        if opponent_king_safety < 0.3:
            return GameContext.MUST_WIN
        
        # Default to equal/normal
        return GameContext.EQUAL if abs(our_material) < 0.05 else GameContext.NORMAL
    
    def _calculate_strategic_importance(
        self, 
        position: chess.Board, 
        move_number: int
    ) -> float:
        """Calculate strategic importance of current decision (0-1)."""
        importance = 0.5  # Base importance
        
        # Opening moves are less strategically important individually
        if move_number <= 10:
            importance -= 0.2
        
        # Middlegame moves are more important
        elif 20 <= move_number <= 40:
            importance += 0.2
        
        # Endgame moves are very important
        elif len(position.piece_map()) <= 12:
            importance += 0.3
        
        # Positions with few legal moves = higher importance
        legal_moves_count = len(list(position.legal_moves))
        if legal_moves_count < 5:
            importance += 0.2
        
        return max(0.0, min(1.0, importance))
    
    def _calculate_time_sensitivity(
        self,
        position: chess.Board,
        position_type: PositionType,
        game_context: GameContext
    ) -> float:
        """Calculate how time-sensitive the current decision is (0-1)."""
        sensitivity = 0.5  # Base sensitivity
        
        # Position type adjustments
        type_sensitivity = {
            PositionType.TACTICAL: 0.8,
            PositionType.CRITICAL: 0.9,
            PositionType.FORCING: 0.6,
            PositionType.STRATEGIC: 0.3,
            PositionType.ENDGAME: 0.7,
            PositionType.OPENING: 0.2,
            PositionType.TRANSITION: 0.5
        }
        
        sensitivity = type_sensitivity.get(position_type, 0.5)
        
        # Context adjustments
        if game_context in [GameContext.MUST_WIN, GameContext.DEFENDING]:
            sensitivity += 0.2
        elif game_context == GameContext.TIME_PRESSURE:
            sensitivity -= 0.3  # Ironically, less time to be sensitive about time
        
        return max(0.0, min(1.0, sensitivity))
    
    def _calculate_overall_complexity(
        self,
        tactical_density: float,
        strategic_importance: float,
        forcing_factor: float,
        position_type: PositionType
    ) -> float:
        """Calculate overall position complexity (0-1)."""
        # Weight different factors
        complexity = (
            tactical_density * 0.4 +
            strategic_importance * 0.3 +
            forcing_factor * 0.2 +
            (0.1 if position_type == PositionType.CRITICAL else 0.0)
        )
        
        return max(0.0, min(1.0, complexity))


# Import defaultdict for pawn structure analysis
from collections import defaultdict

# Export main classes
__all__ = [
    'PositionType',
    'GameContext',
    'PositionAnalysis',
    'DynamicTimeAllocator',
    'PositionAnalyzer'
]


def main():
    """Test the dynamic time allocation system."""
    import chess
    from .time_control import TimeControlParser
    from .time_allocation import TimeAllocator
    
    # Create components
    parser = TimeControlParser()
    base_allocator = TimeAllocator()
    dynamic_allocator = DynamicTimeAllocator(base_allocator)
    
    # Test positions
    test_positions = [
        ("Opening", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
        ("Tactical", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"),
        ("Endgame", "8/8/8/8/8/3K4/8/3k4 w - - 0 1"),
        ("Check", "rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")
    ]
    
    time_control = parser.parse("3+2")
    if not time_control:
        print("Failed to parse time control")
        return
    
    print("Dynamic Time Allocation Test:")
    print("=" * 50)
    
    for pos_name, fen in test_positions:
        position = chess.Board(fen)
        move_number = 1 if pos_name == "Opening" else 20
        
        # Get base allocation
        base_allocation = base_allocator.allocate_time(
            time_control, 180000, True, move_number
        )
        
        # Get dynamic allocation
        dynamic_allocation = dynamic_allocator.allocate_time_dynamic(
            position, base_allocation, time_control, move_number
        )
        
        # Analyze position
        analysis = dynamic_allocator.position_analyzer.analyze_position(position, move_number)
        
        print(f"\n{pos_name} Position:")
        print(f"  FEN: {fen}")
        print(f"  Position Type: {analysis.position_type.value}")
        print(f"  Game Context: {analysis.game_context.value}")
        print(f"  Complexity: {analysis.complexity_score:.3f}")
        print(f"  Tactical Density: {analysis.tactical_density:.3f}")
        print(f"  Time Sensitivity: {analysis.time_sensitivity:.3f}")
        print(f"  Base Allocation: {base_allocation.target_time_ms}ms")
        print(f"  Dynamic Allocation: {dynamic_allocation.target_time_ms}ms")
        
        multiplier = dynamic_allocation.target_time_ms / max(1, base_allocation.target_time_ms)
        print(f"  Multiplier: {multiplier:.2f}x")
        print("-" * 40)


if __name__ == "__main__":
    main()
