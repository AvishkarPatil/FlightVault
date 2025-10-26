"""
Test Runner - Execute all FlightVault tests
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Discover and run all tests"""
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)