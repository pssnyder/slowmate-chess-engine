"""
SlowMate Chess Engine - Test Runner
Version: 1.0.0-BETA
"""

import unittest
import sys
import os

def run_tests():
    """Run all test suites."""
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to the Python path
    project_root = os.path.dirname(test_dir)
    sys.path.insert(0, project_root)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(test_dir, 'core_tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Add integration tests
    integration_dir = os.path.join(test_dir, 'integration_tests')
    suite.addTests(loader.discover(integration_dir, pattern='test_*.py'))
    
    # Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if tests passed, 1 if any failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
