# SlowMate Chess Engine

A learning-focused, incremental chess engine built in Python with emphasis on clarity, simplicity, and UCI compatibility.

## Project Philosophy

SlowMate is designed as a step-by-step learning project where each feature is implemented incrementally with clear documentation of the development process. This approach allows for:

- **Transparency**: Every decision and implementation step is documented
- **Maintainability**: Simple, readable code over complex optimizations
- **Modularity**: Features can be easily added, modified, or rolled back
- **Compatibility**: Built to UCI (Universal Chess Interface) standards for integration with chess software

## Current Status

🏆 **KING SAFETY ENGINE - Comprehensive Strategic Intelligence!** 🏆

The engine now features sophisticated king safety evaluation alongside advanced positional understanding!

### Current Version: 0.0.08 (King Safety)
- **Engine ID**: slowmate_0.0.08_king_safety
- **Latest Feature**: King safety evaluation system
- **Previous Version**: 0.0.07 (Game Phase Awareness)

### Completed Features
- ✅ **🆕 King Safety Evaluation (Document 09 - Version 0.0.08)**: Castling rights, castling status, and pawn shield analysis!
- ✅ **Complete PST system (Document 08 - Version 0.0.07)**: Universal → Piece-specific → Game phase aware!
- ✅ **Material evaluation system (Document 07 - Version 0.0.06)**: Strategic piece value assessment!
- ✅ **Intelligent move selection (Document 06 - Version 0.0.05)**: Checkmate detection, stalemate avoidance!
- ✅ **Nibbler.exe integration (Document 05 - Version 0.0.04)**: Production validated!
- ✅ **UCI protocol implementation (Document 04 - Version 0.0.03)**: Full compatibility!
- ✅ **Basic engine implementation (Document 03 - Version 0.0.02)**: Legal move generation and game completion
- ✅ **Project setup (Document 01 - Version 0.0.01)**: Foundation and architecture
- ✅ Basic chess board representation (via python-chess)
- ✅ Move generation (20 legal moves from starting position)
- ✅ Legal move validation (automatic via python-chess)
- ✅ Game state management (checkmate, stalemate, draw detection)
- ⏳ Advanced search algorithms (Phase 4 - minimax/alpha-beta)
- ⏳ Opening book integration (Phase 5 - theoretical knowledge)

### Latest Milestone: King Safety Implementation (Document 09 - Version 0.0.08)
- **Castling Rights Evaluation**: Small bonus for maintaining castling ability (+10/+8)
- **Castling Status Evaluation**: Larger bonus for having castled (+25/+20) - Action > Preparation
- **Pawn Shield Evaluation**: Bonus for pawns protecting king (+8 per pawn, up to 3)
- **Strategic Integration**: King safety influences move selection without overriding tactics
- **Balanced Design**: Enhances strategic sophistication while maintaining tactical sharpness

### Previous Milestone: Complete PST Implementation (Document 08 - Version 0.0.07)
- **Three-Phase Evolution**: Universal PST → Piece-specific PST → Game phase awareness
- **Adaptive Strategy**: Engine changes behavior based on Opening/Middlegame/Endgame detection
- **Endgame Excellence**: Pawn advancement (+200 near promotion), King centralization (+65 swing), Rook activity
- **Phase Detection**: Material and piece-count based algorithm automatically detects game phase
- **Strategic Depth**: Engine now shows understanding of when to activate pieces vs maintain safety
- **Real-world Validation**: Excellent strategic play demonstrated in tournament games

## Core Goals

### Primary Goal (Phase 1)
**Legal Move Generation and Game Completion**: The engine must be able to play any legal chess move and see a complete game through to its conclusion (checkmate, stalemate, or draw).

### Secondary Goals (Future Phases)
- **Real-time Transparency**: Provide clear, real-time insights into the engine's decision-making process
- **UCI Compliance**: Full compatibility with Universal Chess Interface for integration with:
  - Arena Chess GUI
  - Nibbler.exe
  - Other UCI-compatible chess software
- **Competitive Integration**: Structured for potential deployment on chess platforms (pending platform policies)

## Architecture Overview

*To be filled as implementation progresses*

## Installation

1. Clone the repository:
```bash
git clone https://github.com/pssnyder/slowmate_chess_engine.git
cd slowmate_chess_engine
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Connect to Nibbler.exe
1. Open Nibbler.exe
2. Add engine: Browse to `slowmate.bat` in the project folder
3. Engine will appear as "SlowMate 0.0.1-dev"
4. Start analyzing positions or play games!

### Manual UCI Testing
```bash
# Test UCI protocol
echo "uci" | slowmate.bat

# Run comprehensive test
python test_uci.py
```

### Basic Demo
Run a complete random game:
```bash
python demo.py
```

### Engine API
```python
from slowmate.intelligence import IntelligentSlowMateEngine

# Create intelligent engine
engine = IntelligentSlowMateEngine()

# Play intelligent moves with reasoning
while not engine.is_game_over():
    move = engine.play_intelligent_move()
    reasoning = engine.get_move_reasoning()
    print(f"Engine played: {move}")
    print(f"Strategy: {reasoning}")

print(f"Game over: {engine.get_game_result()}")
```

### Intelligence Testing
```bash
# Test intelligent move selection
python test_intelligence.py

# Toggle intelligence on/off via UCI
echo "setoption name Intelligence value false" | slowmate.bat
```

### Current Features
- **Intelligent Move Selection**: Checkmate detection, stalemate/draw avoidance
- **UCI Protocol**: Full compatibility with chess GUIs (Nibbler, Arena, etc.)
- **Nibbler.exe Integration**: Production-validated, runs complete games
- **Strategic Decision Making**: Prioritizes winning moves, avoids losing positions  
- **Complete Game Support**: Plays from start to checkmate/stalemate/draw
- **Real-time Analysis**: Detailed reasoning for every move selection
- **Robust Game Logic**: Handles all chess rules via python-chess library
- **Engine Testing Ready**: Can compete intelligently against other engines
- **Professional Standards**: Industry-grade UCI compliance with analysis output

## Development Roadmap

See `/docs/` folder for detailed development timeline and decision history.

## Testing

✅ **Production Validated**:
- **Nibbler.exe**: Full integration tested with complete games
- **UCI Compliance**: All protocol commands validated
- **Self-Play Testing**: Multiple game variations completed successfully
- **Real-World Performance**: Stable operation in professional chess software

**Additional Testing Capabilities**:
- Unit tests for core functionality
- Integration with Arena Chess GUI  
- Engine vs engine competition testing
- Tournament-style automated play

## Future Enhancement Parking Lot

### En Passant Refinements (Later Development)
- **Current Status**: Working excellently, demonstrated in game analysis
- **Future Enhancements**: 
  - Add checks to only take en passant if it's a "free piece"  
  - Exception handling for structure-improving en passant (removes doubled pawns, trades isolated pawns)
  - Monitor for any detrimental en passant moves in future games

### Advanced Castling Logic (Later Development)
- **Kingside vs Queenside**: Weight preferences based on position evaluation
- **King Safety Integration**: Coordinate with upcoming king safety features
- **Timing Optimization**: Further refine when castling is most beneficial

### Piece Coordination Features (Advanced Development)
- **Piece Pairing**: Bonuses for coordinated pieces working together
- **Piece Proximity**: Distance-based cooperation bonuses between pieces
- **Rank/File Alignment**: Rook and Queen coordination patterns
- **Checkmate Pattern Recognition**: Rook positioning for common mate patterns
- **Pawn Structure Analysis**: Isolated, doubled, passed pawn evaluation

*Note: Items in parking lot are for future consideration after core positional and search features are complete.*

## Contributing

This is primarily a learning project, but suggestions and educational discussions are welcome.

## License

*To be determined*

---

**Last Updated**: July 19, 2025  
**Version**: 0.0.08 (King Safety Engine)  
**Engine ID**: slowmate_0.0.08_king_safety  
**Status**: Tournament-ready with king safety evaluation and comprehensive strategic intelligence  

## Version History
- **0.0.08**: King Safety Implementation (castling rights, castling status, pawn shield)
- **0.0.07**: Game Phase Awareness (opening/middlegame/endgame PST adaptation)  
- **0.0.06**: Material Evaluation System (strategic piece value assessment)
- **0.0.05**: Intelligent Move Selection (checkmate detection, stalemate avoidance)
- **0.0.04**: UCI Production Integration (Nibbler.exe validated)
- **0.0.03**: UCI Protocol Implementation (full UCI compliance)
- **0.0.02**: Basic Engine Implementation (legal move generation, game completion)
- **0.0.01**: Project Setup and Foundation (documentation, architecture)
