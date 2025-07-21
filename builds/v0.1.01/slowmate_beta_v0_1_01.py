#!/usr/bin/env python3
"""
SlowMate Chess Engine v0.1.01 Beta - Main Executable
Tactical Enhancements Edition

This executable contains the enhanced tactical intelligence system with:
- Modern SEE-based threat evaluation
- Advanced pawn structure analysis  
- Queen development discipline
- Unified tactical combination logic

Usage: python slowmate_beta_v0_1_01.py
"""

import sys
import os

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slowmate.engine import SlowMateEngine
from slowmate.intelligence import IntelligentSlowMateEngine
from slowmate.uci import UCIInterface

def main():
    """Main entry point for SlowMate v0.1.01 Beta"""
    print("SlowMate Chess Engine v0.1.01 Beta - Tactical Enhancements Edition")
    print("==================================================================")
    print("Features: SEE-based evaluation, Pawn structure, Queen discipline")
    print("Build Date: July 20, 2025")
    print("==================================================================")
    
    try:
        # Create UCI interface (includes the engine)
        uci_interface = UCIInterface()
        
        print("Engine initialized successfully!")
        print("Starting UCI mode...")
        print("Type 'uci' to begin or 'quit' to exit")
        print("")
        
        # Start UCI communication loop
        uci_interface.run()
        
    except KeyboardInterrupt:
        print("\nShutting down SlowMate...")
    except Exception as e:
        print(f"Error starting SlowMate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
