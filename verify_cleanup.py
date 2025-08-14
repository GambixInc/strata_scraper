#!/usr/bin/env python3
"""
Cleanup Verification Script
Verifies that all SQLite references have been properly removed from the codebase
"""

import os
import sys
import re

def check_file_for_sqlite_references(file_path):
    """Check a file for SQLite references"""
    issues = []
    
    # Skip the verification script itself
    if 'verify_cleanup.py' in file_path:
        return issues
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for SQLite imports
        if 'import sqlite3' in content:
            issues.append("Contains 'import sqlite3'")
            
        if 'from sqlite3' in content:
            issues.append("Contains 'from sqlite3'")
            
        # Check for SQLite database file references
        if '.db' in content and 'sqlite' in content.lower():
            issues.append("Contains SQLite database file references")
            
        # Check for SQLite-specific code patterns
        if 'sqlite3.connect' in content:
            issues.append("Contains 'sqlite3.connect'")
            
        if 'sqlite3.OperationalError' in content:
            issues.append("Contains 'sqlite3.OperationalError'")
            
        # Check for local storage references
        if 'save_content_to_files' in content:
            issues.append("Contains 'save_content_to_files'")
            
        if 'local storage' in content.lower():
            issues.append("Contains 'local storage' references")
            
        # Check for data directory references
        if 'data/' in content and '.db' in content:
            issues.append("Contains data directory with .db references")
            
    except Exception as e:
        issues.append(f"Error reading file: {e}")
        
    return issues

def check_python_files():
    """Check all Python files for SQLite references"""
    print("🔍 Checking Python files for SQLite references...")
    
    issues_found = False
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and git directories
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                issues = check_file_for_sqlite_references(file_path)
                
                if issues:
                    print(f"\n❌ {file_path}:")
                    for issue in issues:
                        print(f"   - {issue}")
                    issues_found = True
                else:
                    print(f"✅ {file_path}")
    
    return not issues_found

def check_database_config():
    """Check database configuration"""
    print("\n🔍 Checking database configuration...")
    
    try:
        from database_config import Database, GambixStrataDatabase
        
        # Check if we can import DynamoDB classes
        if Database and GambixStrataDatabase:
            print("✅ Database configuration imports successfully")
            return True
        else:
            print("❌ Database configuration import failed")
            return False
            
    except ImportError as e:
        print(f"❌ Database configuration import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Database configuration error: {e}")
        return False

def check_environment_variables():
    """Check environment variable configuration"""
    print("\n🔍 Checking environment variable configuration...")
    
    # Check if USE_DYNAMODB is still being set anywhere
    try:
        from database_config import USE_DYNAMODB
        print("❌ USE_DYNAMODB still exists in database_config")
        return False
    except ImportError:
        print("✅ USE_DYNAMODB properly removed from database_config")
        return True

def main():
    """Main verification function"""
    print("🚀 SQLite Cleanup Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python files
    if not check_python_files():
        all_checks_passed = False
    
    # Check database configuration
    if not check_database_config():
        all_checks_passed = False
    
    # Check environment variables
    if not check_environment_variables():
        all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All cleanup checks passed!")
        print("✅ SQLite has been completely removed from the codebase")
        return True
    else:
        print("❌ Some cleanup issues found")
        print("   Please review the issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
