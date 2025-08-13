#!/usr/bin/env python3
"""
Test script for S3 storage functionality
"""

import os
import json
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test S3 storage functionality')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Environment file to load (default: .env)')
    return parser.parse_args()

# Parse arguments
args = parse_args()

# Load environment variables
load_dotenv(args.env_file)

def test_s3_connection():
    """Test S3 connection and basic functionality"""
    try:
        from s3_storage import S3Storage
        
        print("🔧 Testing S3 connection...")
        s3_storage = S3Storage()
        print("✅ S3 connection successful!")
        
        # Test basic upload
        test_content = "This is a test file for S3 storage"
        test_key = f"test/test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        print(f"📤 Uploading test file: {test_key}")
        if s3_storage.upload_file_content(test_content, test_key):
            print("✅ Test file uploaded successfully!")
            
            # Test presigned URL generation
            print("🔗 Generating presigned URL...")
            presigned_url = s3_storage.get_file_url(test_key)
            if presigned_url:
                print(f"✅ Presigned URL generated: {presigned_url[:50]}...")
            else:
                print("❌ Failed to generate presigned URL")
            
            # Test JSON upload
            test_json = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "message": "S3 storage test successful"
            }
            json_key = f"test/test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            print(f"📤 Uploading test JSON: {json_key}")
            if s3_storage.upload_json_content(test_json, json_key):
                print("✅ Test JSON uploaded successfully!")
            else:
                print("❌ Failed to upload test JSON")
            
            # Test listing files
            print("📋 Listing files in test prefix...")
            files = s3_storage.list_files_in_prefix("test/")
            if files:
                print(f"✅ Found {len(files)} files in test prefix")
                for file in files:
                    print(f"  - {file}")
            else:
                print("ℹ️ No files found in test prefix")
            
            return True
        else:
            print("❌ Failed to upload test file")
            return False
            
    except ImportError:
        print("❌ S3 storage module not available. Install boto3: pip install boto3")
        return False
    except Exception as e:
        print(f"❌ S3 test failed: {e}")
        return False

def test_scraped_content_save():
    """Test saving scraped content to S3"""
    try:
        from s3_storage import S3Storage
        
        print("\n🔧 Testing scraped content save...")
        s3_storage = S3Storage()
        
        # Create mock scraped data
        mock_scraped_data = {
            'title': 'Test Website',
            'html_content': '<html><head><title>Test</title></head><body><h1>Hello World</h1></body></html>',
            'css_content': {
                'inline_styles': ['body { margin: 0; }'],
                'internal_stylesheets': ['h1 { color: blue; }'],
                'external_stylesheets': ['https://example.com/style.css']
            },
            'js_content': {
                'inline_scripts': ['console.log("Hello");'],
                'external_scripts': ['https://example.com/script.js']
            },
            'links': ['https://example.com', 'https://test.com'],
            'seo_metadata': {
                'meta_tags': {'description': 'Test description'},
                'open_graph': {'og:title': 'Test Title'},
                'twitter_cards': {'twitter:card': 'summary'}
            }
        }
        
        test_url = "https://test.example.com"
        s3_prefix = s3_storage.save_scraped_content_to_s3(mock_scraped_data, test_url)
        
        if s3_prefix:
            print(f"✅ Scraped content saved to S3: {s3_prefix}")
            
            # List the saved files
            files = s3_storage.list_files_in_prefix(s3_prefix)
            if files:
                print(f"📋 Saved files:")
                for file in files:
                    print(f"  - {file}")
            else:
                print("❌ No files found in saved prefix")
            
            return True
        else:
            print("❌ Failed to save scraped content to S3")
            return False
            
    except Exception as e:
        print(f"❌ Scraped content test failed: {e}")
        return False

def main():
    """Run all S3 tests"""
    print("🚀 Starting S3 Storage Tests")
    print("=" * 50)
    
    # Check AWS credentials using CLI credential chain
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials verified - Account: {identity['Account']}, User: {identity['Arn']}")
    except Exception as e:
        print(f"❌ AWS credentials not found or invalid: {e}")
        print("Please ensure AWS CLI is configured or IAM role is attached")
        return False
    
    # Check required environment variables
    if not os.getenv('S3_BUCKET_NAME'):
        print("❌ Missing required environment variable: S3_BUCKET_NAME")
        print("Please set S3_BUCKET_NAME in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    
    # Run tests
    connection_success = test_s3_connection()
    content_save_success = test_scraped_content_save()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  S3 Connection: {'✅ PASS' if connection_success else '❌ FAIL'}")
    print(f"  Content Save: {'✅ PASS' if content_save_success else '❌ FAIL'}")
    
    if connection_success and content_save_success:
        print("\n🎉 All S3 tests passed! Your S3 integration is working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check your S3 configuration.")
        return False

if __name__ == "__main__":
    main()
