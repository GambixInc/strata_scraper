#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all test files in the tests directory
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n🧪 Running {test_file}...")
    print("=" * 60)
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status}: {test_file}")
        
        return success, result.stdout, result.stderr
        
    except Exception as e:
        print(f"❌ ERROR running {test_file}: {e}")
        return False, "", str(e)

def run_all_tests():
    """Run all test files in the tests directory"""
    print("🚀 Running All Tests")
    print("=" * 60)
    
    # Get all test files
    tests_dir = Path(__file__).parent
    test_files = [
        "test_suite.py",           # Main comprehensive test suite
        "test_auth.py",            # Authentication tests
        "test_cognito_auth.py",    # Cognito authentication tests
        # "test_database.py",        # Database tests (removed - DynamoDB only)
        "test_dynamodb.py",        # DynamoDB specific tests
        "test_s3_storage.py",      # S3 storage tests
        "test_routes.py",          # API route tests
        "test_tracker.py",         # Site tracker tests
        "test_imports.py",         # Import tests
        # "test_file_access.py",     # File access tests (removed - DynamoDB only)
        "test_production_readiness.py",  # Production readiness tests
        "test_infrastructure_production_readiness.py"  # Infrastructure tests
    ]
    
    results = []
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        
        if test_path.exists():
            success, stdout, stderr = run_test_file(str(test_path))
            results.append((test_file, success, stdout, stderr))
            if success:
                passed += 1
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((test_file, False, "", "File not found"))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    for test_file, success, stdout, stderr in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_file}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All test suites passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test file"""
    tests_dir = Path(__file__).parent
    test_path = tests_dir / test_name
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_name}")
        return False
    
    success, stdout, stderr = run_test_file(str(test_path))
    return success

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
