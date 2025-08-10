#!/usr/bin/env python3
"""
SlowMate v0.3.03 Critical Bug Investigation

The v0.3.02 fixes FAILED in actual gameplay. This script investigates:
1. Why +M500/8 values are still appearing in games
2. Why depth search isn't progressing (always /8)
3. Why PV lines aren't changing
4. Why evaluations are completely unrealistic

This is a CRITICAL debugging session before v0.3.03 development.
"""

import subprocess
import sys
import time
from pathlib import Path
import chess
import chess.pgn
import io

def analyze_problematic_game():
    """Analyze the specific positions that show +M500 in the PGN."""
    
    print("🚨 CRITICAL BUG INVESTIGATION")
    print("=" * 50)
    
    # Load the problematic game
    pgn_path = "games/20250722_endgame_enhancements_bad_mate_eval.pgn"
    
    try:
        with open(pgn_path, 'r') as f:
            pgn_content = f.read()
        
        print("📂 Loaded problematic PGN file")
        
        # Parse first game
        pgn_io = io.StringIO(pgn_content)
        game = chess.pgn.read_game(pgn_io)
        
        if not game:
            print("❌ Could not parse game")
            return False
        
        print(f"🎯 Analyzing game: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")
        
        # Find positions with +M500 evaluations
        board = game.board()
        problematic_positions = []
        
        move_num = 1
        for node in game.mainline():
            move = node.move
            comment = node.comment
            
            # Look for +M500 in comments
            if "+M500" in comment or "-M500" in comment:
                fen = board.fen()
                problematic_positions.append({
                    'move_num': move_num,
                    'move': move,
                    'comment': comment,
                    'fen': fen,
                    'position_desc': f"Move {move_num}: {move}"
                })
                
                if len(problematic_positions) >= 3:  # Get first 3 problematic positions
                    break
            
            board.push(move)
            if board.turn == chess.WHITE:
                move_num += 1
        
        print(f"\n🔍 Found {len(problematic_positions)} positions with +M500 errors")
        
        # Test these positions with current executable
        exe_path = Path("builds/v0.3.02/SlowMate_v0.3.02_Enhanced_Endgame.exe")
        
        if not exe_path.exists():
            exe_path = Path("dist/slowmate_v0.3.01-BETA.exe")
        
        if not exe_path.exists():
            print("❌ No executable found for testing")
            return False
        
        print(f"🧪 Testing positions with: {exe_path}")
        
        for i, pos in enumerate(problematic_positions):
            print(f"\n--- Test Position {i+1}: {pos['position_desc']} ---")
            print(f"FEN: {pos['fen']}")
            print(f"Original eval: {pos['comment']}")
            
            # Test position with engine
            success = test_position_with_engine(str(exe_path), pos['fen'])
            if not success:
                print("⚠️  Engine test failed - this may indicate the core problem")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing game: {e}")
        return False

def test_position_with_engine(exe_path, fen):
    """Test a specific position with the engine to see current behavior."""
    
    try:
        # Start engine
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send commands
        commands = [
            "uci",
            f"position fen {fen}",
            "go depth 4",  # Shallow depth to see progression
            "quit"
        ]
        
        print("📤 Testing position...")
        for cmd in commands[:-1]:  # Don't print quit
            print(f"   > {cmd}")
        
        for cmd in commands:
            if process.stdin:
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
            time.sleep(0.3)
        
        # Get output with timeout
        try:
            stdout, stderr = process.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            print("⏰ Engine timed out")
            process.kill()
            stdout, stderr = process.communicate()
        
        # Analyze output
        lines = stdout.split('\n')
        info_lines = [line for line in lines if line.startswith('info')]
        
        print(f"📥 Found {len(info_lines)} info lines")
        
        mate_found = False
        depth_progression = []
        
        for line in info_lines:
            if 'depth' in line and 'score' in line:
                print(f"📊 {line.strip()}")
                
                # Extract depth
                if 'depth' in line:
                    try:
                        depth_part = line.split('depth')[1].split()[0]
                        depth_progression.append(int(depth_part))
                    except:
                        pass
                
                # Check for mate scores
                if 'mate' in line:
                    mate_found = True
                    if 'mate 500' in line or 'mate 300' in line:
                        print("🚨 FOUND +M500 BUG IN OUTPUT!")
        
        # Analysis
        if depth_progression:
            print(f"🔍 Depth progression: {depth_progression}")
            if len(set(depth_progression)) == 1:
                print("⚠️  NO DEPTH PROGRESSION - Always same depth!")
            else:
                print("✅ Depth progression working")
        else:
            print("❌ No depth information found")
        
        if mate_found:
            print("⚠️  Mate scores found - may be problematic")
        else:
            print("✅ No mate scores (might be good)")
        
        return True
        
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False

def investigate_depth_search_module():
    """Check the depth search implementation for bugs."""
    
    print("\n🔍 INVESTIGATING DEPTH SEARCH MODULE")
    print("=" * 50)
    
    # Check if depth_search.py has issues
    try:
        with open("slowmate/depth_search.py", 'r') as f:
            content = f.read()
        
        print("📂 Analyzing depth_search.py")
        
        # Check for problematic patterns
        issues = []
        
        if "mate 500" in content.lower() or "30000" in content:
            issues.append("Found mate score constants that might be causing +M500")
        
        if content.count("depth") < 5:
            issues.append("Very few depth references - may not be implementing iterative deepening")
        
        if "iterative" not in content.lower():
            issues.append("No iterative deepening implementation found")
        
        if "pv" not in content.lower():
            issues.append("No PV (Principal Variation) handling found")
        
        # Check for infinite loops
        if content.count("while True") > content.count("break"):
            issues.append("Possible infinite loop risk")
        
        print(f"🚨 Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"   ❌ {issue}")
        
        if not issues:
            print("✅ No obvious issues found in depth_search.py")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Could not analyze depth_search.py: {e}")
        return False

def check_uci_implementation():
    """Check UCI output implementation."""
    
    print("\n🔍 INVESTIGATING UCI IMPLEMENTATION")
    print("=" * 50)
    
    try:
        with open("slowmate/uci.py", 'r') as f:
            content = f.read()
        
        print("📂 Analyzing uci.py")
        
        issues = []
        
        # Check for mate score handling
        if "mate" in content.lower():
            print("✅ Found mate score handling in UCI")
        else:
            issues.append("No mate score handling in UCI output")
        
        # Check for info depth output
        if "info depth" in content:
            print("✅ Found info depth output")
        else:
            issues.append("No info depth output implementation")
        
        # Check for PV output
        if "pv" in content.lower():
            print("✅ Found PV output")
        else:
            issues.append("No PV (Principal Variation) output")
        
        if issues:
            print(f"🚨 Found {len(issues)} UCI issues:")
            for issue in issues:
                print(f"   ❌ {issue}")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Could not analyze uci.py: {e}")
        return False

def main():
    """Main debugging function."""
    
    print("🚨 SlowMate v0.3.03 CRITICAL BUG INVESTIGATION")
    print("The v0.3.02 'fixes' FAILED in actual games!")
    print("=" * 60)
    
    # Step 1: Analyze the problematic game
    game_analyzed = analyze_problematic_game()
    
    # Step 2: Investigate depth search
    depth_ok = investigate_depth_search_module()
    
    # Step 3: Check UCI implementation
    uci_ok = check_uci_implementation()
    
    print("\n📋 INVESTIGATION SUMMARY")
    print("=" * 30)
    
    if game_analyzed:
        print("✅ Game analysis completed")
    else:
        print("❌ Game analysis failed")
    
    if depth_ok:
        print("✅ Depth search looks OK")
    else:
        print("❌ Depth search has issues")
    
    if uci_ok:
        print("✅ UCI implementation looks OK")
    else:
        print("❌ UCI implementation has issues")
    
    print("\n🎯 NEXT STEPS FOR v0.3.03:")
    print("1. Fix the actual root cause of +M500 values")
    print("2. Implement proper iterative deepening with depth progression")
    print("3. Add proper PV line updates during search")
    print("4. Fix evaluation system to give realistic scores")
    print("5. Test thoroughly before claiming fixes work!")
    
    if not (game_analyzed and depth_ok and uci_ok):
        print("\n🚨 CRITICAL ISSUES REMAIN - v0.3.02 IS NOT FIXED!")
        return False
    else:
        print("\n✅ Ready to proceed with v0.3.03 fixes")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
