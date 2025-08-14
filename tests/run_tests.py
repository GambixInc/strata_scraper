#!/usr/bin/env python3
"""
Test Runner Script
Runs the comprehensive test suite and exits with appropriate code
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run tests
from tests.test_suite import run_tests

if __name__ == "__main__":
    print("🚀 Starting Test Suite")
    print("=" * 50)
    
    # Run tests
    success = run_tests()
    
    # Exit with appropriate code
    if success:
        print("\n✅ All tests passed! Build can proceed.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Build should fail.")
        sys.exit(1)
