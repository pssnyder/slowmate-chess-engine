#!/usr/bin/env python3
"""
Quick test of the new executable with enhanced UCI options
"""

import subprocess
import time

def quick_uci_test():
    """Quick test of enhanced UCI options."""
    
    print("🧪 QUICK UCI TEST - NEW BUILD")
    print("=" * 40)
    
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
        
        print("📤 Sending 'uci' command...")
        if process.stdin:
            process.stdin.write("uci\n")
            process.stdin.flush()
            
        time.sleep(2)  # Give it time to respond
        
        print("📤 Sending 'quit' command...")
        if process.stdin:
            process.stdin.write("quit\n")
            process.stdin.flush()
        
        stdout, stderr = process.communicate(timeout=5)
        
        print("\n📥 UCI OPTIONS OUTPUT:")
        print("=" * 30)
        
        lines = stdout.split('\n')
        option_lines = [line for line in lines if 'option name' in line]
        
        print(f"Found {len(option_lines)} UCI options:")
        for line in option_lines:
            print(f"  {line.strip()}")
        
        if len(option_lines) > 10:
            print("✅ Enhanced UCI options working!")
        else:
            print("❌ Still only basic UCI options")
        
        # Check for evaluation values
        info_lines = [line for line in lines if 'score cp' in line]
        for line in info_lines:
            print(f"📊 {line.strip()}")
            
        return len(option_lines) > 10
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_uci_test()
    print(f"\n🎯 Result: {'Enhanced UCI working' if success else 'Still needs fixes'}")
