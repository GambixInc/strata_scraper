#!/usr/bin/env python3
"""
Local Test Script
Run this to test the test suite locally before Docker build
"""

import sys
import os

# Set test environment
os.environ['TEST_ENV'] = 'local'

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run tests
from tests.test_suite import run_tests

if __name__ == "__main__":
    print("🧪 Running Local Test Suite")
    print("=" * 50)
    
    # Run tests
    success = run_tests()
    
    # Exit with appropriate code
    if success:
        print("\n✅ All tests passed! Ready for Docker build.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Fix issues before Docker build.")
        sys.exit(1)
