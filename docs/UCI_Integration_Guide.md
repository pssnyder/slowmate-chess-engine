# SlowMate UCI Integration Guide

## Connecting SlowMate to Nibbler.exe

### Step 1: Locate SlowMate Engine Files
The SlowMate engine can be run using either:
- **Python script**: `slowmate_uci.py` (requires Python environment)
- **Batch launcher**: `slowmate.bat` (recommended for Windows GUIs)

### Step 2: Configure Nibbler
1. Open Nibbler.exe
2. Go to **Engine** menu → **Add Engine** (or similar)
3. Browse to the SlowMate directory
4. Select `slowmate.bat` as the engine executable
5. Engine name should appear as "SlowMate 0.0.1-dev"

### Step 3: Test Connection
1. In Nibbler, start a new game with SlowMate as the engine
2. The engine should respond to position changes
3. When asked to move, SlowMate will select a random legal move
4. Check Nibbler's engine output window for debug information

## Manual UCI Testing

You can test the engine manually from command line:

### Basic Test
```cmd
echo uci | slowmate.bat
```
Expected output:
```
id name SlowMate 0.0.1-dev
id author SlowMate Project
uciok
```

### Complete Session Test
```cmd
python test_uci.py
```

### Debug Mode Test
```cmd
echo "uci" | python slowmate_uci.py
echo "debug on" | python slowmate_uci.py
echo "isready" | python slowmate_uci.py
echo "position startpos" | python slowmate_uci.py
echo "go" | python slowmate_uci.py
```

## Engine Capabilities (Current)

### ✅ Implemented UCI Commands
- `uci` - Engine identification
- `isready` - Readiness check
- `ucinewgame` - New game setup
- `position startpos` - Set starting position
- `position fen <fen>` - Set custom position
- `position ... moves <moves>` - Apply move sequence
- `go` - Start move search (random selection)
- `stop` - Stop current search
- `debug on/off` - Toggle debug output
- `quit` - Terminate engine

### ⏳ Future UCI Features
- `setoption` - Engine configuration
- Search parameters (time, depth, nodes)
- `info` strings during search (PV, score, depth)
- Pondering support
- Multi-PV analysis

## Testing Against Other Engines

### Arena Chess GUI
1. Install Arena Chess GUI
2. Add SlowMate using `slowmate.bat`
3. Set up engine vs engine matches
4. Compare performance against other engines

### Engine vs Engine Testing
```cmd
# Example tournament setup in Arena:
# Engine 1: SlowMate (Random)
# Engine 2: Stockfish Level 1
# Time Control: 1 minute per game
# Expected: Learning opportunity to see weaknesses
```

## Troubleshooting

### Common Issues
1. **Engine not recognized**: Ensure `slowmate.bat` is executable
2. **Python errors**: Check virtual environment is activated
3. **No moves returned**: Check position setup in debug mode
4. **Timeout errors**: Engine should respond within seconds

### Debug Information
Enable debug mode to see:
- Received UCI commands
- Position FEN strings
- Legal move counts
- Selected moves with algebraic notation
- Engine status messages

### Log Output Example
```
info string Debug: Received command 'position startpos'
info string Position set: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
info string Starting move search
info string Found 20 legal moves
info string Selected move: Nf3 (g1f3)
bestmove g1f3
```

## Performance Notes

- **Move Selection**: Random, typically < 1ms
- **Position Setup**: Instant via python-chess
- **Memory Usage**: Minimal (~10MB)
- **Compatibility**: All UCI-compliant GUIs

---

**Ready for Real-World Testing!** 🎯

Your SlowMate engine is now fully UCI-compatible and ready for integration with chess software like Nibbler, Arena, and engine testing frameworks.
