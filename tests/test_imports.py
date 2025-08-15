#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

print("🧪 Testing imports...")

try:
    # Test main imports
    from main import simple_web_scraper, get_safe_filename
    print("   ✅ Main imports OK")
    
    # Test database imports
    from database_config import Database, GambixStrataDatabase
    print(f"   ✅ Database imports OK (DynamoDB only)")
    
    # Test S3 storage imports
    try:
        from s3_storage import S3Storage
        print("   ✅ S3 storage imports OK")
    except ImportError:
        print("   ⚠️  S3 storage not available (boto3 not installed)")
    
    # Test server imports
    from server import app
    print("   ✅ Server imports OK")
    
    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
