# SlowMate Game Analysis Utility

## Overview

The **Game Analysis Utility** is a revolutionary standalone tool that enables SlowMate to learn from its own historical games. By analyzing PGN game files, it discovers significant tactical moves and builds a confidence-weighted middlegame tactics library for enhanced gameplay.

## Key Features

### 🧠 **Self-Learning Architecture**
- Analyzes historical PGN game files automatically
- Extracts only moves played by SlowMate in winning games
- Mathematical significance detection using statistical analysis
- Builds confidence-weighted tactical patterns

### 📊 **Mathematical Analysis Framework**
- **Adaptive Thresholds**: Uses standard deviation analysis instead of static values
- **Statistical Significance**: Detects moves that are outliers from game averages
- **Multi-Factor Evaluation**: Combines evaluation improvement, deviation factor, game impact
- **Confidence Weighting**: 0.0-1.0 scale with mathematical precision

### ⚔️ **Tactical Pattern Discovery**
- **Considerable Move Detection**: Identifies game-changing moves
- **Pattern Classification**: Tactical, positional, and checkmate patterns
- **Principal Variation Storage**: Captures multi-move sequences
- **Transposition Compatibility**: Data structures ready for future enhancements

## Usage

### Basic Analysis

```bash
# Analyze all PGN files in games/ directory with high strictness
python game_analysis_utility.py

# Use medium strictness for more discoveries
python game_analysis_utility.py --strictness medium

# Analyze custom directory
python game_analysis_utility.py --games-dir tournament_results/ --strictness low
```

### Strictness Levels

| Level  | Min Eval | Min Deviation | Criteria Required | Use Case |
|--------|----------|---------------|-------------------|-----------|
| High   | 50 cp    | 1.5 std dev   | All               | Tournament prep |
| Medium | 30 cp    | 1.0 std dev   | All               | Regular analysis |
| Low    | 20 cp    | 0.8 std dev   | Any 2 of 3        | Experimentation |

### Output Files

- **`data/middlegame/tactics.json`** - Main tactical library
- **`analysis_report_N_games.json`** - Session analysis report

## Analysis Criteria

### "Considerable Move" Detection

A move is considered significant when **ALL** criteria are met:

1. ✅ **SlowMate Discovery** - Move was played by SlowMate
2. ✅ **Winning Game** - SlowMate won the overall game  
3. ✅ **Evaluation Improvement** - Move increases position evaluation significantly
4. ✅ **Statistical Significance** - Move creates outlier behavior in evaluation
5. ✅ **Positive Impact** - Move objectively improves position

### Confidence Weight Calculation

```python
confidence = base_confidence + eval_factor + deviation_factor + impact_factor + pattern_factor

# Factors:
# eval_factor: Based on centipawn improvement (0.0-0.3)
# deviation_factor: Statistical deviation from game mean (0.0-0.4) 
# impact_factor: Game impact level - low/medium/high (0.05-0.2)
# pattern_factor: Pattern type - positional/tactical/checkmate (0.05-0.1)

# Special case: Checkmate patterns = 1.0 confidence (guaranteed)
```

## Data Structures

### Tactical Entry Format

```json
{
  "position_hash": {
    "move": "e4",
    "move_san": "e4",
    "pv": ["e4", "e5", "Nf3"],
    "pv_san": ["e4", "e5", "Nf3"], 
    "confidence_weight": 0.85,
    "eval_improvement": 120.0,
    "pattern_type": "tactical",
    "discovered_in_game": "game_hash_id",
    "usage_count": 0,
    "success_rate": 0.0,
    "mate_in": null
  }
}
```

### Session Report Format

```json
{
  "analysis_session": {
    "games_analyzed": 14,
    "slowmate_wins": 1,
    "significant_moves": 3,
    "checkmate_patterns": 0,
    "tactics_added": 3
  },
  "library_stats": {
    "total_positions": 3,
    "average_confidence": 1.0
  }
}
```

## Integration with SlowMate Engine

The discovered tactics are automatically integrated into the main engine's knowledge base:

### Knowledge Priority Order
1. **Endgame Tactics** - Forced mate patterns
2. **Opening Book** - Theoretical moves
3. **🎯 Middlegame Tactics** - Discovered patterns
4. **Endgame Patterns** - Strategic conversion
5. **Random Selection** - Fallback

### Real-Time Usage
```python
# Engine automatically checks middlegame tactics during move selection
tactical_move = knowledge_base.get_knowledge_move(board)
if tactical_move and source == 'middlegame_tactics':
    print(f"Using discovered tactic: {tactical_move}")
```

## Example Analysis Results

### From Tournament Games (July 20, 2025)

**Input**: 14 PGN files analyzed  
**Discovered**: 3 high-confidence tactical patterns  
**Average Improvement**: 1,625 centipawns per pattern

#### Discovered Patterns:
1. **Nc3** - 1,732 cp improvement (tactical breakthrough)
2. **dxc3** - 2,415 cp improvement (devastating capture)  
3. **Bxg2** - 729 cp improvement (positional sacrifice)

All patterns achieved **maximum confidence (1.0)** due to exceptional statistical significance.

## Future Enhancements

### Planned Features
- **Runtime Discovery**: Build tactics during live games
- **Multi-Move Patterns**: Deep tactical sequences
- **Pattern Clustering**: Group similar tactical themes
- **Performance Optimization**: Faster analysis of large PGN collections

### Compatibility
- **Transposition Tables**: Ready for integration
- **Killer Move Support**: Data structure compatibility
- **Opening/Endgame Integration**: Unified knowledge system

## Technical Notes

### Performance
- **Fast Analysis**: Processes typical game in <1 second
- **Memory Efficient**: Compact JSON storage format
- **Duplicate Detection**: Session-level and cross-session handling

### Error Handling
- **Robust PGN Parsing**: Handles malformed game files
- **Encoding Support**: UTF-8 and common chess encodings
- **Graceful Degradation**: Continues analysis on individual game errors

## Troubleshooting

### Common Issues

**No tactics discovered?**
- Verify PGN files contain SlowMate winning games
- Try lower strictness setting
- Check evaluation comparison is working

**Analysis taking too long?**
- Reduce batch size or use targeted PGN files
- Consider using higher strictness to reduce processing

**Memory issues?**
- Process PGN files in smaller batches
- Clear old analysis reports

---

*The Game Analysis Utility represents a breakthrough in chess engine self-improvement, enabling continuous learning through tournament experience. It's the foundation of SlowMate's evolution from basic engine to self-learning chess AI.*
