# SlowMate v0.1.01 Beta Testing Executable

**Executable**: slowmate_v0.1.01_beta.exe  
**Version**: 0.1.01 Beta - Tactical Enhancements Edition  
**Build Date**: July 20, 2025  
**File Size**: ~20MB (approximate)

## 🎯 Features Included

### Tactical Intelligence
- ✅ Modern SEE-based threat evaluation
- ✅ Advanced pawn structure analysis
- ✅ Queen development discipline
- ✅ Unified tactical combination logic

### Performance Validation
- ✅ Defeats v0.1.0 decisively (20-move forced resignation)
- ✅ Original tactical bug completely resolved
- ✅ Brilliant tactical execution (Nxf7, Nxh8 combinations)

## 🧪 Testing Instructions

### Basic Functionality Test
```cmd
slowmate_v0.1.01_beta.exe
```
- Should display engine info and start UCI mode
- Type `uci` to see engine identification
- Type `quit` to exit

### UCI Compatibility Test
Load in chess GUI (Arena, Lucas Chess, etc.):
- Engine Name: SlowMate 0.1.01
- Author: Pat Snyder
- Should be fully UCI compatible

### Strength Validation
- Test against other engines at similar levels
- Should demonstrate strong tactical play
- Should avoid premature queen development
- Should execute tactical combinations correctly

## 🐛 Known Test Scenarios

### Tactical Bug Verification
Test this position: `rnq2b2/p1k5/3p4/1p6/8/P3n3/1PPPPPB1/R1BQK3 w Q - 2 20`
- Engine should prefer **Bxa8** (tactical combination)
- Should NOT prefer **Bb7** (defensive retreat)
- This validates the tactical bug fix

### Queen Development Test
From starting position:
- Engine should prefer **Nf3, Nc3** over early queen moves
- Should avoid **Qh5, Qf3** type moves in opening
- Demonstrates queen discipline

## 📋 Expected Performance

- **Tactical Accuracy**: Significant improvement over v0.1.0
- **Opening Play**: Principled development, avoid queen traps  
- **Endgame**: Basic material evaluation with threat awareness
- **Search Speed**: Similar to v0.1.0 (no performance regression)

## 🏆 Success Criteria

This beta test is successful if:
1. **✅ Engine loads and responds to UCI commands**
2. **✅ Demonstrates tactical superiority in test positions**  
3. **✅ Shows proper queen development discipline**
4. **✅ No crashes or UCI compatibility issues**

---

**Status**: Ready for beta testing  
**Next Version**: v0.1.02 (Opening Book & Endgame Patterns)
