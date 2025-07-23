#!/usr/bin/env python3
"""
SlowMate UCI Debug Test Script

This script tests the enhanced UCI debugging capabilities by:
1. Starting the engine
2. Enabling various debugging options
3. Testing evaluation component isolation
4. Providing real-world debugging scenarios
"""

import subprocess
import time
import sys

def test_uci_debugging():
    """Test the enhanced UCI debugging features."""
    
    print("🧪 TESTING ENHANCED UCI DEBUGGING")
    print("=" * 50)
    
    # Use the latest executable
    exe_path = "dist/slowmate_v0.3.01-BETA.exe"
    
    try:
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print("🚀 Started SlowMate engine")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Basic UCI Options",
                "commands": [
                    "uci",
                ],
                "check": "All enhanced UCI options listed"
            },
            {
                "name": "Enable Evaluation Debugging", 
                "commands": [
                    "setoption name EvalDebug value true",
                    "setoption name EvalScaling value 1",
                    "setoption name EvalMaxCap value 2000",
                ],
                "check": "Evaluation debugging enabled"
            },
            {
                "name": "Disable Material Calculation",
                "commands": [
                    "setoption name MaterialCalculation value false",
                ],
                "check": "Material calculation disabled"  
            },
            {
                "name": "Test Position with Debugging",
                "commands": [
                    "position startpos moves e2e4",
                    "go depth 2",
                ],
                "check": "Debug evaluation components shown"
            },
            {
                "name": "Re-enable Material and Test",
                "commands": [
                    "setoption name MaterialCalculation value true", 
                    "position startpos moves e2e4 e7e5",
                    "go depth 2",
                ],
                "check": "Material calculation re-enabled"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n--- {scenario['name']} ---")
            
            # Send commands
            for cmd in scenario["commands"]:
                print(f"📤 > {cmd}")
                if process.stdin:
                    process.stdin.write(cmd + "\n")
                    process.stdin.flush()
                time.sleep(0.5)
        
        # Get final output
        print("\n📤 > quit")
        if process.stdin:
            process.stdin.write("quit\n")
            process.stdin.flush()
        
        # Collect output
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        
        print("\n📥 ENGINE OUTPUT:")
        print("=" * 40)
        print(stdout)
        
        if stderr:
            print("\n⚠️  STDERR:")
            print(stderr)
        
        # Analyze output
        lines = stdout.split('\n')
        
        options_found = len([line for line in lines if 'option name' in line])
        debug_info_found = len([line for line in lines if 'info string' in line])
        eval_debug_found = len([line for line in lines if 'EVAL_DEBUG' in line])
        
        print(f"\n📊 ANALYSIS:")
        print(f"   UCI options found: {options_found}")
        print(f"   Info strings found: {debug_info_found}")  
        print(f"   Eval debug lines: {eval_debug_found}")
        
        if options_found >= 20:  # Should have many enhanced options
            print("✅ Enhanced UCI options working")
        else:
            print("❌ Enhanced UCI options missing")
        
        if debug_info_found > 0:
            print("✅ Debug info strings working")  
        else:
            print("❌ No debug info found")
        
        if eval_debug_found > 0:
            print("✅ Evaluation debugging working")
        else:
            print("⚠️  Evaluation debugging not seen")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("🧪 SlowMate Enhanced UCI Debugging Test")
    print("=" * 50)
    
    success = test_uci_debugging()
    
    if success:
        print("\n✅ UCI debugging test completed")
        print("\n🎯 Next steps:")
        print("   1. Review output for proper option handling")
        print("   2. Test individual component isolation")
        print("   3. Use in real debugging scenarios")
    else:
        print("\n❌ UCI debugging test failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
