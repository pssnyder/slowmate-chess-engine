"""
Simple UCI test to verify the basic functionality works.
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slowmate.uci_main import UCIMain


def test_basic_uci():
    """Test basic UCI functionality."""
    print("Testing basic UCI functionality...")
    
    try:
        uci_main = UCIMain(debug_mode=True)
        
        # Test UCI initialization
        response = uci_main.test_uci_command("uci")
        print(f"UCI response: {response}")
        
        # Test position setting
        response = uci_main.test_uci_command("position startpos")
        print(f"Position response: {response}")
        
        # Test isready
        response = uci_main.test_uci_command("isready")
        print(f"Ready response: {response}")
        
        # Test a simple search with very short time
        print("Testing search...")
        response = uci_main.test_uci_command("go movetime 500")
        print(f"Search response: {response}")
        
        return True
        
    except Exception as e:
        print(f"Error during basic UCI test: {e}")
        return False


def test_fen_position():
    """Test setting a specific FEN position."""
    print("\nTesting FEN position...")
    
    try:
        uci_main = UCIMain(debug_mode=True)
        
        # Test a simple tactical position
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        
        response = uci_main.test_uci_command("uci")
        response = uci_main.test_uci_command(f"position fen {fen}")
        print(f"FEN position set: {response}")
        
        response = uci_main.test_uci_command("go movetime 1000")
        print(f"Search result: {response}")
        
        return True
        
    except Exception as e:
        print(f"Error during FEN test: {e}")
        return False


if __name__ == "__main__":
    success1 = test_basic_uci()
    success2 = test_fen_position()
    
    if success1 and success2:
        print("\n✅ Basic UCI tests passed!")
    else:
        print("\n❌ Some UCI tests failed!")
