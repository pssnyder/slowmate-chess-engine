# SlowMate Chess Engine

A self-learning, incremental chess engine built in Python with emphasis on clarity, simplicity, and UCI compatibility.

## Project Philosophy

SlowMate is designed as a step-by-step learning project where each feature is implemented incrementally with clear documentation of the development process. This approach allows for:

- **Transparency**: Every decision and implementation step is documented
- **Self-Learning**: Engine analyzes its own games to build tactical knowledge
- **Maintainability**: Simple, readable code over complex optimizations
- **Modularity**: Features can be easily added, modified, or rolled back
- **Compatibility**: Built to UCI (Universal Chess Interface) standards for integration with chess software

## Current Status

🚀 **COMPLETE MOVE LIBRARY SYSTEM - Universal Chess Knowledge!** 🚀

**VISION v0.2.0**: SlowMate is evolving into a complete chess knowledge system with unified move library handling across all game phases - opening, middlegame, and endgame!

### Current Version: 0.2.0-dev (Complete Move Library System) 🔥 **IN DEVELOPMENT**
- **Engine ID**: slowmate_v0.2.0_complete_move_library
- **Development Goal**: **Universal move assistance for all game phases** (Target: July 21, 2025)
- **Architecture**: Unified knowledge base with intelligent phase detection and move selection
- **Status**: **ACTIVE DEVELOPMENT** - Building on proven middlegame tactics foundation 🚧

### Previous Milestone: 0.1.03 (Middlegame Tactics & Game Analysis) ✅ **COMPLETED**
- **Achievement**: Revolutionary game analysis utility and self-learning middlegame tactics system
- **Performance**: 3 discovered tactical patterns with 100% confidence, 1,625 cp average improvement
- **Release Package**: `builds/v0.1.03/slowmate_v0.1.03.exe` with complete documentation

## Implemented Features (Chronological Order)

### 1. Foundation & Setup (v0.0.01 - v0.0.02)
- ✅ **Project Architecture**: Foundation and documentation structure
- ✅ **Basic Engine**: Legal move generation and game completion via python-chess
- ✅ **Move Validation**: Automatic legal move validation and game state management

### 2. UCI Protocol & Integration (v0.0.03 - v0.0.04)  
- ✅ **UCI Compliance**: Full Universal Chess Interface protocol implementation
- ✅ **Nibbler Integration**: Production validation with professional chess software
- ✅ **Tournament Compatibility**: Engine identification and feature advertising

### 3. Core Intelligence (v0.0.05 - v0.0.06)
- ✅ **Intelligent Move Selection**: Checkmate detection and stalemate avoidance
- ✅ **Material Evaluation**: Strategic piece value assessment system

### 4. Positional Evaluation (v0.0.07 - v0.0.08)
- ✅ **Piece-Square Tables**: Game phase aware positioning evaluation
- ✅ **King Safety**: Castling rights, castling status, and pawn shield analysis

### 5. Advanced Search (v0.0.10 - v0.0.12)
- ✅ **Threat Analysis**: Comprehensive threat detection and tactical evaluation
- ✅ **Minimax Algorithm**: Multi-ply search with alpha-beta pruning
- ✅ **Quiescence Search**: Terminal position stability analysis
- ✅ **Enhanced UCI**: Real-time analysis with rich debugging information

### 6. Knowledge Base System (v0.1.01 - v0.1.02)
- ✅ **Opening Book**: Comprehensive opening theory with weighted preferences
- ✅ **Endgame Patterns**: KQ vs K, KR vs K, KRR vs K mate recognition
- ✅ **Knowledge Integration**: Priority-based move selection system
- ✅ **Performance**: 42.9% opening hit rate, 0.21ms average lookup

### 7. **REVOLUTIONARY SELF-LEARNING SYSTEM** (v0.1.03)
- ✅ **Game Analysis Utility**: Standalone tool for analyzing historical PGN games
- ✅ **Mathematical Analysis**: Statistical significance detection using standard deviation
- ✅ **Middlegame Tactics Library**: Confidence-weighted tactical pattern storage
- ✅ **Self-Discovery**: Engine learns from its own tournament victories
- ✅ **Adaptive Thresholds**: Dynamic evaluation criteria based on game characteristics

### 6. Tactical Mastery (v0.1.0 - v0.1.01) 
- ✅ **Tournament Victory**: First competitive win establishing baseline strength
- ✅ **SEE-Based Evaluation**: Modern Static Exchange Evaluation system
- ✅ **Tactical Revolution**: Complete system overhaul with unified combinations
- ✅ **Pawn Structure**: Advanced analysis with passed pawn bonuses
- ✅ **Queen Development**: Disciplined early game development logic

### 7. Knowledge Base Intelligence (v0.1.02) 🆕
- ✅ **Opening Book System**: Position-based lookup with weighted move selection
- ✅ **Opening Preferences**: White (London, Queen's Gambit, Vienna) / Black (Caro-Kann, French, Dutch, King's Indian)
- ✅ **Knowledge Coordinator**: Unified interface with priority-based move selection
- ✅ **Endgame Framework**: Strategic pattern recognition architecture (ready for expansion)
- ✅ **Performance Excellence**: 0.21ms average lookup, 42.9% hit rate, comprehensive testing

## Architecture Overview

### Core Components
```
slowmate/
├── engine.py              # Main UCI engine interface
├── intelligence.py        # Tactical evaluation and move selection
├── knowledge/             # Knowledge base system (NEW)
│   ├── opening_book.py    # Position-based opening lookup
│   ├── opening_weights.py # Preference weighting system
│   ├── endgame_patterns.py# Strategic endgame preparation
│   ├── endgame_tactics.py # Checkmate pattern recognition
│   └── knowledge_base.py  # Unified knowledge coordinator
└── data/
    ├── openings/          # Opening book data (JSON)
    └── endgames/          # Endgame pattern data (planned)
```

### Integration Flow
```
Move Selection Priority:
1. Endgame Tactics (immediate checkmates)
2. Opening Book (position-based with preferences)
3. Strategic Endgame Patterns (positional preparation)
4. Tactical Evaluation (SEE-based analysis)
5. Minimax Search (alpha-beta with quiescence)
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/pssnyder/slowmate_chess_engine.git
cd slowmate_chess_engine
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install python-chess
```

## Usage

### UCI Engine (Recommended)
```bash
python main.py
```
Then use UCI commands or integrate with chess GUI software like Nibbler, Arena, or Fritz.

### Direct Testing
```bash
# Run comprehensive knowledge base tests
python testing/test_knowledge_base.py

# Run opening book specific tests  
python testing/test_opening_book.py
```

## Testing

✅ **Production Validated**:
- **Knowledge Base**: 42.9% hit rate with comprehensive integration testing
- **Opening Book**: Weighted selection with anti-repetition variety
- **Performance**: 0.21ms average lookup (5x faster than 1ms target)
- **Nibbler.exe**: Full integration tested with complete games
- **UCI Compliance**: All protocol commands validated
- **Tournament Features**: Complete implementation for competitive play

## Future Development

### Phase 2: Complete Move Library Integration (v0.2.0 - Active Development)
- 🎯 **Universal Move Selection**: Unified system handling opening, middlegame, and endgame moves
- 🧠 **Intelligent Phase Detection**: Dynamic game state analysis for optimal move library selection
- ⚡ **Enhanced Performance**: Streamlined knowledge base with priority optimization
- 📊 **Advanced Analytics**: Comprehensive move usage statistics and success tracking
- 🔗 **Library Coordination**: Seamless integration between opening book, tactical patterns, and endgame knowledge

### Phase 3: Advanced Self-Learning Features (v0.3.0 - Planned)
- **Runtime Tactical Discovery**: Build tactics during live gameplay
- **Dynamic Opening Preferences**: Learn from game results to adjust opening repertoire
- **Pattern Clustering**: Group similar tactical themes for enhanced recognition
- **Multi-Game Analysis**: Cross-reference patterns across multiple game databases

### Phase 4: Competition Optimization (v0.4.0 - Planned)
- **Performance Optimization**: Memory efficiency, faster pattern lookups
- **Extended Search**: Deeper tactical horizon with pattern-guided extensions
- **Advanced Evaluation**: Position assessment influenced by learned patterns
- **Tournament Features**: Competition-ready optimizations and time management

## Contributing

This is primarily a learning project, but suggestions and educational discussions are welcome.

## License

*To be determined*

---

**Last Updated**: July 20, 2025  
**Current Version**: 0.2.0-dev (Complete Move Library System)  
**Engine ID**: slowmate_v0.2.0_complete_move_library  
**Status**: Active Development - Building unified move library system with intelligent phase detection

## Version History
- **0.2.0-dev**: Complete Move Library System (universal move assistance, intelligent phase detection, unified knowledge base)
- **0.1.03**: Self-Learning Middlegame Tactics (game analysis utility, confidence-weighted tactics, pattern discovery)
- **0.1.02**: Knowledge Base Implementation (opening book, knowledge coordinator, endgame framework)
- **0.1.01**: Tactical Enhancements (SEE-based evaluation, tactical revolution, pawn structure)
- **0.1.0**: Tournament Victory (first competitive win, baseline strength established)
- **0.0.12**: Enhanced UCI Integration (real-time analysis, rich debugging)
- **0.0.11**: Depth Search System (minimax, alpha-beta pruning, quiescence search)
- **0.0.10**: Tactical Intelligence (threat analysis, capture evaluation, attack patterns)
- **0.0.08**: King Safety Implementation (castling evaluation, pawn shield analysis)
- **0.0.07**: Game Phase Awareness (opening/middlegame/endgame PST adaptation)
- **0.0.06**: Material Evaluation System (strategic piece value assessment)
- **0.0.05**: Intelligent Move Selection (checkmate detection, stalemate avoidance)
- **0.0.04**: UCI Production Integration (Nibbler.exe validation)
- **0.0.03**: UCI Protocol Implementation (full UCI compliance)
- **0.0.02**: Basic Engine Implementation (legal move generation, game completion)
- **0.0.01**: Project Setup and Foundation (documentation, architecture)
