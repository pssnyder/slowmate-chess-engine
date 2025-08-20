# SlowMate v0.3.01 - Opening Book Validation & Enhancement Plan

## Current State Analysis

### ✅ Functional Components
- Basic position lookup (16 positions)  
- Weighted move selection
- Performance optimization (0.03ms average)
- Integration with preference system

### ❌ Critical Gaps Identified
1. **Insufficient Depth**: Mainlines only 2-3 moves deep (need 8-10)
2. **Missing Sidelines**: 0 sideline positions (need 5-8 moves for major variations)
3. **Missing Edge Cases**: 0 edge cases (need 1-2 alternates per opening)
4. **Incomplete Coverage**: Major openings like QG Accepted have no book moves

## v0.3.01 Enhancement Requirements

### Target Coverage (per user requirements):
- **Mainlines**: 8-10 moves for each major opening
- **Sidelines**: 5-8 moves for major variations  
- **Alternates**: 1-2 alternatives per opening
- **Preferred Openings**: +1-2 additional moves deep

### Priority Openings to Complete:

#### White Preferred:
1. **London System** (d4, Nf3, Bf4 line)
2. **Queen's Gambit** (d4, c4 lines) 
3. **Vienna Game** (e4, Nc3 line)

#### Black Responses:
1. **Caro-Kann** (vs e4: c6)
2. **French Defense** (vs e4: e6)
3. **Dutch Defense** (vs d4: f5)
4. **King's Indian** (vs d4: Nf6, g6)

### Implementation Plan:
1. **Expand mainlines.json** - Add deep lines for each opening
2. **Create sidelines.json** - Major variations and alternatives
3. **Create edge_cases.json** - Challenging/tricky positions
4. **Enhanced testing** - Verify depth and coverage
5. **Dev candidate build** - Test executable for functional verification

## Success Criteria:
- Mainlines: 8-10 moves deep for all major openings
- Sidelines: 5-8 moves for key variations
- Edge cases: 1-2 alternatives per opening  
- Test coverage: 90%+ of expected opening positions
- Performance: Maintain <1ms average lookup time
