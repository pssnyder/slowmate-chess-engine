# 02 - Architecture Decisions

**Date**: July 19, 2025  
**Status**: ✅ Complete  
**Phase**: Architecture Definition  
**Version**: 0.0.02 (included in basic engine)  
**Engine ID**: slowmate_0.0.02_basic_engine  

## Decisions Made

### Chess Board Representation
✅ **Board Storage**: 8x8 array format  
✅ **Piece Notation**: String-based with lowercase color + piece letter  
- Format: `'wp'` (white pawn), `'wn'` (white knight), `'wk'` (white king)  
- Format: `'bp'` (black pawn), `'br'` (black rook), `'bb'` (black bishop)  
- **Rationale**: Debugging visibility outweighs conversion overhead; compact yet readable

### Initial Engine Architecture
✅ **Search Algorithm**: Random selection from legal moves only  
✅ **Evaluation Function**: None initially - pure random selection  
✅ **Primary Goal**: Validate move generation and basic engine interface  
- **Rationale**: Establish foundation before adding complexity; test infrastructure first

### Debugging Strategy
✅ **Logging Approach**: Minimal in-code logging, rely on VS Code debugging tools  
✅ **Testing Philosophy**: Individual component testing before integration  
✅ **Integration Monitoring**: Selective dump statements of critical variables during testing only  
- **Rationale**: Keep code lightweight; avoid debugging solutions becoming performance problems

### Development Environment & Dependencies
✅ **Python Version**: Use most stable version for required chess libraries  
✅ **Library Philosophy**: Leverage existing chess, math, statistical, and utility libraries  
✅ **Core Principle**: Engine focuses on "thinking," not rule enforcement  
- **Key Libraries to Evaluate**:
  - `python-chess`: For board representation, move validation, game rules
  - Standard mathematical/statistical libraries as needed
  - Visualization libraries for debugging board states

### Design Philosophy Reinforcement
✅ **Don't Reinvent the Wheel**: Use proven libraries for standard chess operations  
✅ **Compute Focus**: Reserve processing power for original patterns and play styles  
✅ **Stability Priority**: Remove any library that causes debugging conflicts  
✅ **Performance Priority**: Offload standard operations to optimized libraries

## Technical Specifications

### Board Representation Details
```python
# Empty square: '' (empty string)
# White pieces: 'wp', 'wr', 'wn', 'wb', 'wq', 'wk'
# Black pieces: 'bp', 'br', 'bn', 'bb', 'bq', 'bk'
# 8x8 array: board[rank][file] where rank 0 = rank 1, file 0 = a-file
```

### Move Format (To Be Refined)
- Initial: Leverage python-chess move objects
- Engine Internal: Convert to/from library format as needed
- UCI Output: Standard algebraic notation via library conversion

### Random Move Selection Algorithm
```python
# Pseudocode
def select_move(board_state):
    legal_moves = get_all_legal_moves(board_state)
    return random.choice(legal_moves)
```

## Next Steps
1. Research and select optimal Python chess library (`python-chess` primary candidate)
2. Set up Python project structure with dependencies
3. Implement basic board representation using selected library
4. Create random move selection engine
5. Implement basic UCI interface stub
6. Test with simple chess positions

## Library Evaluation Criteria
- **Performance**: Optimized move generation and validation
- **Documentation**: Clear, comprehensive documentation
- **UCI Compatibility**: Support for UCI protocol
- **Maintenance**: Active development and community support
- **Debugging**: Does not interfere with VS Code debugging

## Risk Mitigation
- **Library Conflicts**: Quick removal protocol if debugging issues arise
- **Complexity Creep**: Maintain focus on random selection until interface proven
- **Performance**: Monitor library overhead vs. benefit

---

**Status**: ✅ Complete - Ready for implementation  
**Next Doc**: `03_library_setup.md` (after library research and selection)
