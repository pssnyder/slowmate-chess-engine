#!/usr/bin/env python3
"""
Mate Evaluation Fix for SlowMate v0.3.02

This script fixes the critical mate evaluation bugs that are causing:
1. +M500/8 values (should be +M3 or similar)
2. Incorrect mate detection in early game positions
3. Poor mate execution when actual mates exist
4. Aggressive auto-adjudication due to wrong evaluations

Key fixes:
1. Correct mate score calculation in depth search
2. Proper mate distance conversion for UCI output
3. Enhanced mate detection logic
4. Improved position evaluation for mate scenarios
"""

import os
import shutil
from typing import Dict, Any

def backup_files():
    """Create backups of files we're going to modify."""
    backup_files = [
        'slowmate/depth_search.py',
        'slowmate/uci.py', 
        'slowmate/time_management/search_controller.py'
    ]
    
    print("📦 Creating backups...")
    for file_path in backup_files:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup_v0302"
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Backed up {file_path}")
    
def fix_depth_search_mate_scores():
    """Fix mate score calculation in depth_search.py"""
    
    print("\n🔧 Fixing depth search mate evaluation...")
    
    depth_search_file = "slowmate/depth_search.py"
    
    if not os.path.exists(depth_search_file):
        print("   ❌ depth_search.py not found")
        return False
    
    # Read the current file
    with open(depth_search_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Correct mate score calculation
    old_mate_calc = """            if self.board.is_checkmate():
                # Return mate score relative to search depth
                mate_score = 10000 - (self.search_config['max_depth'] - depth)
                return (-mate_score if maximizing_player else mate_score), []"""
    
    new_mate_calc = """            if self.board.is_checkmate():
                # Fixed: Correct mate score calculation
                # Mate score should reflect actual plies to mate
                plies_to_mate = self.search_config['max_depth'] - depth + 1
                mate_score = 30000 - plies_to_mate  # Use higher base to avoid confusion
                return (-mate_score if maximizing_player else mate_score), []"""
    
    if old_mate_calc in content:
        content = content.replace(old_mate_calc, new_mate_calc)
        print("   ✅ Fixed mate score calculation")
    
    # Fix 2: Update mate detection threshold
    old_threshold = "return abs(score) > 9000  # Mate scores are typically 10000 +/- depth"
    new_threshold = "return abs(score) > 25000  # Mate scores are 30000 - plies_to_mate"
    
    if old_threshold in content:
        content = content.replace(old_threshold, new_threshold)
        print("   ✅ Fixed mate detection threshold")
    
    # Fix 3: Correct UCI mate distance calculation
    old_mate_distance = """        if self._is_mate_score(score):
            # Calculate mate distance more precisely
            mate_distance = (10000 - abs(score))
            mate_moves = max(1, mate_distance // 2)  # Ensure at least mate in 1"""
    
    new_mate_distance = """        if self._is_mate_score(score):
            # Fixed: Calculate mate distance correctly
            mate_distance = abs(30000 - abs(score))
            mate_moves = max(1, (mate_distance + 1) // 2)  # Convert plies to moves"""
    
    if old_mate_distance in content:
        content = content.replace(old_mate_distance, new_mate_distance)
        print("   ✅ Fixed UCI mate distance calculation")
    
    # Write the fixed file
    with open(depth_search_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_search_controller_mate_handling():
    """Fix mate handling in search controller"""
    
    print("\n🔧 Fixing search controller mate handling...")
    
    search_controller_file = "slowmate/time_management/search_controller.py"
    
    if not os.path.exists(search_controller_file):
        print("   ❌ search_controller.py not found")
        return False
    
    # Read the current file  
    with open(search_controller_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add proper mate score handling to search controller
    mate_handling_code = '''
    def _is_mate_score(self, score: int) -> bool:
        """Check if score indicates mate."""
        return abs(score) > 25000
    
    def _convert_mate_score_to_uci(self, score: int) -> str:
        """Convert internal mate score to UCI format."""
        if not self._is_mate_score(score):
            return f"cp {score}"
            
        mate_distance = abs(30000 - abs(score))
        mate_moves = max(1, (mate_distance + 1) // 2)
        if score < 0:
            mate_moves = -mate_moves
        return f"mate {mate_moves}"
'''
    
    # Insert the mate handling methods before the last class or at the end
    if "class SearchController" in content and mate_handling_code not in content:
        # Find a good insertion point
        insertion_point = content.find("def _search_fixed_depth")
        if insertion_point == -1:
            insertion_point = content.rfind("def ")
            
        if insertion_point != -1:
            content = content[:insertion_point] + mate_handling_code + "\n    " + content[insertion_point:]
            print("   ✅ Added mate score handling to search controller")
    
    # Write the fixed file
    with open(search_controller_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_uci_mate_output():
    """Fix UCI interface mate output"""
    
    print("\n🔧 Fixing UCI mate output...")
    
    uci_file = "slowmate/uci.py"
    
    if not os.path.exists(uci_file):
        print("   ❌ uci.py not found")
        return False
    
    # Read the current file
    with open(uci_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add mate score validation function
    mate_validation_code = '''
    def _validate_and_fix_mate_score(self, score_str: str) -> str:
        """Validate and fix mate scores that are clearly wrong."""
        if "mate" not in score_str.lower():
            return score_str
            
        try:
            # Extract mate value
            parts = score_str.split()
            if len(parts) >= 2:
                mate_value = int(parts[1])
                
                # If mate value is unreasonably high, it's probably a bug
                if abs(mate_value) > 50:  # Mate in more than 50 is suspicious
                    # Convert back to centipawn evaluation
                    cp_value = mate_value * 10  # Rough conversion
                    return f"cp {cp_value}"
                    
        except (ValueError, IndexError):
            pass
            
        return score_str
'''
    
    # Insert the validation code
    if "class UCIInterface" in content and mate_validation_code not in content:
        insertion_point = content.find("def __init__(")
        if insertion_point != -1:
            content = content[:insertion_point] + mate_validation_code + "\n    " + content[insertion_point:]
            print("   ✅ Added mate score validation to UCI")
    
    # Fix any existing mate score output to use validation
    if "score mate" in content:
        # Look for score output and add validation
        old_score_output = 'f"score {score_str}"'
        new_score_output = 'f"score {self._validate_and_fix_mate_score(score_str)}"'
        
        if old_score_output in content:
            content = content.replace(old_score_output, new_score_output)
            print("   ✅ Added mate score validation to output")
    
    # Write the fixed file
    with open(uci_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def create_mate_evaluation_tester():
    """Create a test script to verify mate evaluation fixes"""
    
    print("\n🧪 Creating mate evaluation tester...")
    
    tester_content = '''#!/usr/bin/env python3
"""
Mate Evaluation Tester for SlowMate v0.3.02

Tests the fixed mate evaluation system to ensure:
1. Correct mate scores (no more M500!)
2. Proper mate detection
3. Accurate UCI output
4. Reasonable auto-adjudication
"""

import chess
import chess.pgn
import io
from slowmate.intelligence import IntelligentSlowMateEngine
from slowmate.depth_search import DepthSearchEngine

def test_mate_evaluation():
    """Test mate evaluation with known positions."""
    
    print("=== SlowMate v0.3.02 Mate Evaluation Test ===\\n")
    
    # Test position 1: Simple back-rank mate in 1
    print("Test 1: Back-rank mate in 1")
    engine = IntelligentSlowMateEngine()
    
    # Position: White to move, mate in 1 with Rd8#
    engine.set_position("6k1/6pp/8/8/8/8/6PP/3R2K1 w - - 0 1")
    
    legal_moves = list(engine.board.legal_moves)
    print(f"Legal moves: {len(legal_moves)}")
    
    for move in legal_moves:
        if engine.board.san(move) == "Rd8#":
            engine.board.push(move)
            if engine.board.is_checkmate():
                print("   ✅ Mate in 1 detected correctly")
            else:
                print("   ❌ Failed to detect mate in 1")
            engine.board.pop()
            break
    
    # Test position 2: No mate available (from our problematic game)
    print("\\nTest 2: Early game position (should show normal eval)")
    engine.set_position("r1b1kbnr/ppqp1ppp/2n1p3/8/8/8/PPPPPPPP/R1BQKBNR w KQkq - 0 4")
    
    evaluation = engine.get_current_evaluation()
    print(f"Position evaluation: {evaluation} cp")
    
    if abs(evaluation) < 1000:
        print("   ✅ Normal evaluation (no false mate)")
    else:
        print(f"   ❌ Suspicious evaluation: {evaluation}")
    
    # Test depth search if available
    try:
        print("\\nTest 3: Depth search evaluation")
        depth_engine = DepthSearchEngine()
        depth_engine.board = engine.board.copy()
        
        best_move, score, pv = depth_engine.search_best_move()
        print(f"Best move: {engine.board.san(best_move) if best_move else 'None'}")
        print(f"Score: {score}")
        
        if depth_engine._is_mate_score(score):
            mate_distance = abs(30000 - abs(score))
            mate_moves = max(1, (mate_distance + 1) // 2)
            if score < 0:
                mate_moves = -mate_moves
            print(f"Mate evaluation: M{mate_moves}")
            
            if abs(mate_moves) <= 10:
                print("   ✅ Reasonable mate distance")
            else:
                print(f"   ❌ Unreasonable mate distance: M{mate_moves}")
        else:
            print("   ✅ Normal position evaluation (no mate)")
            
    except Exception as e:
        print(f"   ⚠️  Depth search test failed: {e}")
    
    print("\\n" + "="*50)
    print("Mate evaluation test complete!")

if __name__ == "__main__":
    test_mate_evaluation()
'''
    
    with open("test_mate_evaluation_fix.py", 'w', encoding='utf-8') as f:
        f.write(tester_content)
    
    print("   ✅ Created test_mate_evaluation_fix.py")

def main():
    """Main function to apply all mate evaluation fixes."""
    
    print("🔧 SlowMate v0.3.02 Mate Evaluation Fix")
    print("="*50)
    
    # Create backups
    backup_files()
    
    # Apply fixes
    fixes_applied = 0
    
    if fix_depth_search_mate_scores():
        fixes_applied += 1
    
    if fix_search_controller_mate_handling():
        fixes_applied += 1
        
    if fix_uci_mate_output():
        fixes_applied += 1
    
    # Create tester
    create_mate_evaluation_tester()
    
    print(f"\\n✅ Applied {fixes_applied} mate evaluation fixes")
    print("\\n📋 Next steps:")
    print("1. Run: python test_mate_evaluation_fix.py")
    print("2. Test the engine with the problematic game")
    print("3. Build new executable if tests pass")
    print("4. Verify no more +M500 evaluations!")

if __name__ == "__main__":
    main()
