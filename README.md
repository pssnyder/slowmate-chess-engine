# SlowMate Chess Engine

A learning-focused, incremental chess engine built in Python with emphasis on clarity, simplicity, and UCI compatibility.

## Project Philosophy

SlowMate is designed as a step-by-step learning project where each feature is implemented incrementally with clear documentation of the development process. This approach allows for:

- **Transparency**: Every decision and implementation step is documented
- **Maintainability**: Simple, readable code over complex optimizations
- **Modularity**: Features can be easily added, modified, or rolled back
- **Compatibility**: Built to UCI (Universal Chess Interface) standards for integration with chess software

## Current Status

🚀 **Phase 2 Complete - UCI Compatible Engine!** 🚀

The engine is now fully UCI-compatible and ready for integration with chess GUIs like Nibbler, Arena, and testing against other engines like Stockfish!

### Completed Features
- ✅ Project structure and documentation setup
- ✅ Basic chess board representation (via python-chess)
- ✅ Move generation (20 legal moves from starting position)
- ✅ Legal move validation (automatic via python-chess)
- ✅ Game state management (checkmate, stalemate, draw detection)
- ✅ **UCI protocol implementation (Full compatibility!)**
- ⏳ Basic move evaluation (Phase 3 - search algorithms)
- ⏳ Basic search algorithm (Phase 3 - minimax/alpha-beta)

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
from slowmate.engine import SlowMateEngine

# Create new engine
engine = SlowMateEngine()

# Play random moves
while not engine.is_game_over():
    move = engine.play_random_move()
    print(f"Engine played: {move}")
    print(f"Status: {engine.get_game_status()}")

print(f"Game over: {engine.get_game_result()}")
```

### Current Features
- **UCI Protocol**: Full compatibility with chess GUIs (Nibbler, Arena, etc.)
- **Random Move Selection**: Selects legal moves randomly  
- **Complete Game Support**: Plays from start to checkmate/stalemate/draw
- **Real-time Transparency**: Shows legal move count and game status
- **Robust Game Logic**: Handles all chess rules via python-chess library
- **Engine Testing Ready**: Can compete against other engines like Stockfish

## Development Roadmap

See `/docs/` folder for detailed development timeline and decision history.

## Testing

The engine will be tested with:
- Unit tests for core functionality
- Integration with Arena Chess GUI
- Integration with Nibbler.exe for analysis
- Self-play testing for game completion validation

## Contributing

This is primarily a learning project, but suggestions and educational discussions are welcome.

## License

*To be determined*

---

**Last Updated**: July 19, 2025
**Version**: 0.0.1-dev (Phase 2 Complete - UCI Ready!)
**Next Steps**: See `UCI_Integration_Guide.md` for Nibbler setup instructions
