#!/usr/bin/env python3
"""
Simple Test Runner
Runs all tests from the root directory
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main test suite
from tests.test_suite import run_tests

if __name__ == "__main__":
    print("🚀 Starting Main Test Suite")
    print("=" * 50)
    
    # Run main test suite
    success = run_tests()
    
    # Exit with appropriate code
    if success:
        print("\n✅ All tests passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed! Fix issues before deployment.")
        sys.exit(1)
