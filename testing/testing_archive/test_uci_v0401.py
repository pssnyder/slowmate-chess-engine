#!/usr/bin/env python3
"""
Quick UCI Test for v0.4.01 - Verify Enhanced PV Output
"""

import subprocess
import time

def test_uci_interface():
    """Test the enhanced UCI interface."""
    
    print("🧪 Testing v0.4.01 UCI Interface with Enhanced PV Output")
    print("=" * 60)
    
    # Commands to send
    commands = [
        "uci",
        "isready", 
        "position startpos",
        "go depth 3",
        "quit"
    ]
    
    try:
        # Run the engine
        process = subprocess.Popen(
            ["builds/dist/slowmate_v0.4.01_UCI_STANDARDIZATION.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send commands
        input_text = "\n".join(commands) + "\n"
        stdout, stderr = process.communicate(input=input_text, timeout=10)
        
        print("📋 UCI Output:")
        print("-" * 40)
        print(stdout)
        
        if stderr:
            print("⚠️  Errors:")
            print(stderr)
        
        # Analyze output
        lines = stdout.split('\n')
        
        # Check for UCI compliance
        has_uciok = any('uciok' in line for line in lines)
        has_readyok = any('readyok' in line for line in lines)
        has_info_lines = any('info depth' in line for line in lines)
        has_pv = any('pv ' in line for line in lines)
        has_bestmove = any('bestmove' in line for line in lines)
        
        print("\n📊 Analysis:")
        print(f"✅ UCI OK: {has_uciok}")
        print(f"✅ Ready OK: {has_readyok}")
        print(f"✅ Info Lines: {has_info_lines}")
        print(f"✅ PV Output: {has_pv}")
        print(f"✅ Best Move: {has_bestmove}")
        
        # Count depth lines
        depth_lines = [line for line in lines if 'info depth' in line]
        print(f"📏 Depth lines found: {len(depth_lines)}")
        
        for line in depth_lines:
            print(f"   {line.strip()}")
        
        if len(depth_lines) >= 3 and has_pv:
            print("\n🎯 SUCCESS: Enhanced PV output working!")
            return True
        else:
            print("\n❌ ISSUE: PV output not complete")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_uci_interface()
    
    if success:
        print("\n🚀 v0.4.01 UCI STANDARDIZATION: READY!")
        print("✅ Professional UCI interface verified")
        print("✅ Enhanced PV output working")
        print("✅ Ready to proceed to v0.4.02 Time Management")
    else:
        print("\n⚠️  Issues found - manual verification needed")
