#!/usr/bin/env python3
"""
S3 Setup Script for Strata Scraper
Helps users configure S3 storage for the application
"""

import os
import sys
from dotenv import load_dotenv

def create_env_file():
    """Create or update .env file with S3 configuration"""
    env_file = '.env'
    
    # Load existing environment variables
    load_dotenv()
    
    print("🔧 S3 Configuration Setup")
    print("=" * 50)
    print("This script will help you configure S3 storage for the Strata Scraper.")
    print("You'll need your AWS access key ID, secret access key, and S3 bucket name.")
    print()
    
    # Get S3 configuration from user
    aws_access_key_id = input("Enter your AWS Access Key ID: ").strip()
    if not aws_access_key_id:
        print("❌ AWS Access Key ID is required")
        return False
    
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ").strip()
    if not aws_secret_access_key:
        print("❌ AWS Secret Access Key is required")
        return False
    
    s3_bucket_name = input("Enter your S3 bucket name: ").strip()
    if not s3_bucket_name:
        print("❌ S3 bucket name is required")
        return False
    
    aws_region = input("Enter your AWS region (default: us-east-1): ").strip() or "us-east-1"
    
    # Read existing .env file if it exists
    existing_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            existing_content = f.read()
    
    # Prepare new S3 configuration
    s3_config = f"""
# AWS S3 Configuration
AWS_ACCESS_KEY_ID={aws_access_key_id}
AWS_SECRET_ACCESS_KEY={aws_secret_access_key}
AWS_REGION={aws_region}
S3_BUCKET_NAME={s3_bucket_name}
S3_ENDPOINT_URL=https://s3.amazonaws.com
"""
    
    # Check if S3 config already exists
    if "AWS_ACCESS_KEY_ID" in existing_content:
        print("⚠️ S3 configuration already exists in .env file")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Setup cancelled")
            return False
        
        # Remove existing S3 config
        lines = existing_content.split('\n')
        new_lines = []
        skip_s3_section = False
        
        for line in lines:
            if line.startswith('# AWS S3 Configuration'):
                skip_s3_section = True
                continue
            elif skip_s3_section and (line.startswith('#') or line.strip() == ''):
                skip_s3_section = False
                new_lines.append(line)
            elif skip_s3_section and line.startswith('AWS_'):
                continue
            else:
                new_lines.append(line)
        
        existing_content = '\n'.join(new_lines)
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write(existing_content.rstrip() + '\n' + s3_config)
    
    print(f"✅ S3 configuration saved to {env_file}")
    return True

def test_configuration():
    """Test the S3 configuration"""
    print("\n🧪 Testing S3 Configuration...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if required variables are set
        required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        # Test S3 connection
        from s3_storage import get_s3_client, upload_file_to_s3, delete_files_in_s3
        get_s3_client()  # This will test the connection
        print("✅ S3 connection successful!")
        
        # Test basic upload
        test_content = "S3 configuration test"
        test_key = "test/setup_test.txt"
        
        if upload_file_to_s3(test_content, test_key):
            print("✅ Test upload successful!")
            
            # Clean up test file
            delete_files_in_s3("test/")
            print("✅ Test cleanup successful!")
            
            return True
        else:
            print("❌ Test upload failed")
            return False
            
    except ImportError:
        print("❌ S3 storage module not available. Install boto3: pip install boto3")
        return False
    except Exception as e:
        print(f"❌ S3 test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Strata Scraper S3 Setup")
    print("=" * 50)
    
    # Check if boto3 is installed
    try:
        import boto3
    except ImportError:
        print("❌ boto3 is not installed")
        print("Please install it first: pip install boto3")
        return False
    
    # Create configuration
    if not create_env_file():
        return False
    
    # Test configuration
    if test_configuration():
        print("\n🎉 S3 setup completed successfully!")
        print("\nYour scraped content will now be saved to S3.")
        print("Note: This application requires S3 for storage - no local fallback available.")
        return True
    else:
        print("\n⚠️ S3 setup completed with issues.")
        print("Please check your AWS credentials and bucket configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
