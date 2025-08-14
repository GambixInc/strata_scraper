#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing imports...")
        
        # Test database imports
        print("1. Testing database imports...")
        from database_config import Database, GambixStrataDatabase, USE_DYNAMODB
        print(f"   ✅ Database imports OK (USE_DYNAMODB: {USE_DYNAMODB})")
        
        # Test main imports
        print("2. Testing main imports...")
        from main import simple_web_scraper, save_content_to_files, get_safe_filename
        print("   ✅ Main imports OK")
        
        # Test server imports
        print("3. Testing server imports...")
        from server import app
        print("   ✅ Server imports OK")
        
        # Test database initialization
        print("4. Testing database initialization...")
        db = GambixStrataDatabase()
        print("   ✅ Database initialization OK")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
