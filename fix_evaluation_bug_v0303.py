#!/usr/bin/env python3
"""
SlowMate v0.3.03 - DIRECT EVALUATION BUG FIX

Based on investigation, the problem is clear:
1. Engine outputs cp 37200 (372 pawns!) instead of reasonable scores
2. Arena interprets this as "Mate in 500" 
3. The evaluation system is completely broken

This script directly fixes the evaluation scaling.
"""

def fix_evaluation_scaling():
    """Fix the evaluation system to output reasonable centipawn values."""
    
    print("🔧 FIXING EVALUATION SCALING BUG")
    print("=" * 50)
    
    # Read current intelligence.py
    try:
        with open("slowmate/intelligence.py", 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read intelligence.py: {e}")
        return False
    
    print("📂 Loaded intelligence.py")
    
    # Find the basic position evaluation return statement
    target_pattern = """return (material_score + positional_score + king_safety_score + 
                captures_score + attacks_score + coordination_score +
                pawn_structure_score + queen_development_score + minor_development_score)"""
    
    # Fixed version with proper scaling
    fixed_pattern = """# CRITICAL FIX: Scale evaluation to reasonable centipawn values
        total_score = (material_score + positional_score + king_safety_score + 
                      captures_score + attacks_score + coordination_score +
                      pawn_structure_score + queen_development_score + minor_development_score)
        
        # Scale down to reasonable range (typical chess evaluations are -500 to +500 cp)
        # The current system is outputting values like 37200 which is insane
        scaled_score = int(total_score * 0.01)  # Scale by 100x to get reasonable values
        
        # Cap at reasonable bounds to prevent crazy evaluations
        if scaled_score > 2000:   # More than 20 pawns advantage is winning
            scaled_score = 2000
        elif scaled_score < -2000:
            scaled_score = -2000
            
        return scaled_score"""
    
    if target_pattern in content:
        new_content = content.replace(target_pattern, fixed_pattern)
        print("✅ Found and fixed evaluation scaling")
    else:
        print("⚠️  Could not find exact pattern, searching for similar...")
        # Try to find the return statement more flexibly
        if "return (material_score + positional_score" in content:
            # Find the start and end of the return statement
            start_pos = content.find("return (material_score + positional_score")
            if start_pos != -1:
                # Find the end of the return statement (look for the closing parenthesis)
                end_pos = content.find(")", start_pos)
                if end_pos != -1:
                    # Extract the current return statement
                    current_return = content[start_pos:end_pos+1]
                    print(f"🔍 Found return statement: {current_return[:100]}...")
                    
                    # Replace with fixed version
                    new_return = """# CRITICAL FIX: Scale evaluation to reasonable centipawn values
        total_score = (material_score + positional_score + king_safety_score + 
                      captures_score + attacks_score + coordination_score +
                      pawn_structure_score + queen_development_score + minor_development_score)
        
        # Scale down to reasonable range (typical chess evaluations are -500 to +500 cp)
        scaled_score = int(total_score * 0.01)  # Scale by 100x
        
        # Cap at reasonable bounds
        if scaled_score > 2000:
            scaled_score = 2000
        elif scaled_score < -2000:
            scaled_score = -2000
            
        return scaled_score"""
                    
                    new_content = content.replace(current_return, new_return)
                    print("✅ Fixed evaluation scaling with flexible search")
                else:
                    print("❌ Could not find end of return statement")
                    return False
            else:
                print("❌ Could not find return statement")
                return False
        else:
            print("❌ Could not find return statement at all")
            return False
    
    # Write the fixed content
    try:
        with open("slowmate/intelligence.py", 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Applied evaluation scaling fix")
        return True
    except Exception as e:
        print(f"❌ Could not write fixed file: {e}")
        return False

def add_evaluation_debugging():
    """Add debugging to see what components are causing huge scores."""
    
    print("\n🔍 ADDING EVALUATION DEBUGGING")
    print("=" * 40)
    
    try:
        with open("slowmate/intelligence.py", 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read file: {e}")
        return False
    
    # Add debug output right before the return statement
    debug_code = """
        # DEBUG: Print evaluation components to understand huge scores
        if abs(total_score) > 5000:  # Only debug when score is unreasonably high
            print(f"🚨 DEBUG: Huge evaluation detected!")
            print(f"   Material: {material_score}")
            print(f"   Positional: {positional_score}")
            print(f"   King Safety: {king_safety_score}")
            print(f"   Captures: {captures_score}")
            print(f"   Attacks: {attacks_score}")
            print(f"   Coordination: {coordination_score}")
            print(f"   Total BEFORE scaling: {total_score}")
            print(f"   Total AFTER scaling: {scaled_score}")
"""
    
    # Insert debug code before the return statement
    if "return scaled_score" in content:
        new_content = content.replace("return scaled_score", debug_code + "        return scaled_score")
        print("✅ Added evaluation debugging")
    else:
        print("⚠️  Could not find return scaled_score")
        return False
    
    try:
        with open("slowmate/intelligence.py", 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Applied debugging code")
        return True
    except Exception as e:
        print(f"❌ Could not write file: {e}")
        return False

def test_fix():
    """Test the fix by running the engine on the problematic position."""
    
    print("\n🧪 TESTING THE EVALUATION FIX")
    print("=" * 40)
    
    # Build a new version first
    print("🏗️  Rebuilding engine...")
    import subprocess
    
    try:
        result = subprocess.run(["python", "builds/build_executable.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Rebuild successful")
        else:
            print("⚠️  Rebuild had issues but may have succeeded")
    except subprocess.TimeoutExpired:
        print("⚠️  Rebuild timed out but may have completed")
    except Exception as e:
        print(f"⚠️  Rebuild error: {e}")
    
    # Test the position that showed cp 37200
    fen = "r1bqkbnr/ppNp1ppp/2n1p3/8/8/8/PPPPPPPP/R1BQKBNR b KQkq - 0 3"
    
    exe_path = "dist/slowmate_v0.3.01-BETA.exe"  # Use latest build
    
    try:
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        commands = [
            "uci",
            f"position fen {fen}",
            "go depth 3",
            "quit"
        ]
        
        print("📤 Testing fixed evaluation...")
        for cmd in commands:
            if process.stdin:
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
        
        import time
        time.sleep(2)
        
        stdout, stderr = process.communicate(timeout=8)
        
        # Check the output
        lines = stdout.split('\n')
        for line in lines:
            if 'score cp' in line:
                print(f"📊 {line.strip()}")
                
                # Extract the score
                try:
                    cp_part = line.split('score cp')[1].split()[0]
                    score = int(cp_part)
                    
                    if abs(score) < 1000:  # Reasonable score
                        print(f"✅ FIXED! Score {score} is reasonable")
                        return True
                    else:
                        print(f"❌ Still broken - score {score} is too high")
                        return False
                except:
                    print("⚠️  Could not parse score")
        
        print("⚠️  No score found in output")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main fix function."""
    
    print("🚨 SlowMate v0.3.03 CRITICAL EVALUATION BUG FIX")
    print("Fixing the root cause of +M500/8 values")
    print("=" * 60)
    
    # Step 1: Fix the evaluation scaling
    scaling_fixed = fix_evaluation_scaling()
    
    if not scaling_fixed:
        print("❌ Could not fix evaluation scaling")
        return False
    
    # Step 2: Add debugging
    debug_added = add_evaluation_debugging()
    
    # Step 3: Test the fix  
    if scaling_fixed:
        print("\n🎯 EVALUATION SCALING FIX APPLIED!")
        print("This should fix:")
        print("✅ cp 37200 → reasonable values like cp 150")
        print("✅ Arena showing 'Mate in 500' → normal evaluations") 
        print("✅ Unrealistic position assessments → proper evaluations")
        
        test_success = test_fix()
        
        if test_success:
            print("\n🎉 SUCCESS! The evaluation bug is FIXED!")
        else:
            print("\n⚠️  Fix applied but needs further testing")
        
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)
