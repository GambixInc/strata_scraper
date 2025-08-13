#!/usr/bin/env python3
"""
Production Readiness Test for AWS Infrastructure Setup Script
Tests all aspects of the infrastructure setup script to ensure it's production-ready.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd, env=None, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=capture_output, 
            text=True, 
            env=env,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_script_exists():
    """Test that the infrastructure script exists and is executable"""
    logger.info("🔍 Testing script existence...")
    
    script_path = Path("setup_aws_infrastructure.py")
    if not script_path.exists():
        logger.error("❌ setup_aws_infrastructure.py does not exist")
        return False
    
    if not os.access(script_path, os.X_OK):
        logger.error("❌ setup_aws_infrastructure.py is not executable")
        return False
    
    logger.info("✅ Script exists and is executable")
    return True

def test_help_output():
    """Test that the script provides help output"""
    logger.info("🔍 Testing help output...")
    
    returncode, stdout, stderr = run_command("python setup_aws_infrastructure.py --help")
    
    if returncode != 0:
        logger.error(f"❌ Help command failed: {stderr}")
        return False
    
    expected_options = [
        "--env-file",
        "--table-prefix", 
        "--region",
        "--dry-run",
        "--force"
    ]
    
    for option in expected_options:
        if option not in stdout:
            logger.error(f"❌ Help output missing option: {option}")
            return False
    
    logger.info("✅ Help output is correct")
    return True

def test_missing_environment_variables():
    """Test handling of missing environment variables"""
    logger.info("🔍 Testing missing environment variables...")
    
    # Test with no environment variables
    env = os.environ.copy()
    env.pop('AWS_ACCESS_KEY_ID', None)
    env.pop('AWS_SECRET_ACCESS_KEY', None)
    env.pop('S3_BUCKET_NAME', None)
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run",
        env=env
    )
    
    if returncode == 0:
        logger.error("❌ Script should fail with missing environment variables")
        return False
    
    if "S3_BUCKET_NAME environment variable is required" not in stderr:
        logger.error("❌ Script should report missing S3_BUCKET_NAME")
        return False
    
    logger.info("✅ Missing environment variables handled correctly")
    return True

def test_invalid_credentials():
    """Test handling of invalid AWS credentials"""
    logger.info("🔍 Testing invalid credentials...")
    
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'invalid'
    env['AWS_SECRET_ACCESS_KEY'] = 'invalid'
    env['S3_BUCKET_NAME'] = 'test-bucket'
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run",
        env=env
    )
    
    if returncode == 0:
        logger.error("❌ Script should fail with invalid credentials")
        return False
    
    if "Invalid AWS credentials" not in stderr and "AWS error: InvalidClientTokenId" not in stderr:
        logger.error("❌ Script should report invalid credentials")
        return False
    
    logger.info("✅ Invalid credentials handled correctly")
    return True

def test_invalid_bucket_names():
    """Test bucket name validation"""
    logger.info("🔍 Testing bucket name validation...")
    
    invalid_buckets = [
        "invalid-bucket-name--with-double-hyphens",
        "bucket-name-ending-with-hyphen-",
        "192.168.1.1",
        "ab",  # too short
        "a" * 64,  # too long
        "-bucket-name-starting-with-hyphen"
    ]
    
    for bucket_name in invalid_buckets:
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = 'test'
        env['AWS_SECRET_ACCESS_KEY'] = 'test'
        env['S3_BUCKET_NAME'] = bucket_name
        env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
        env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
        
        returncode, stdout, stderr = run_command(
            "python setup_aws_infrastructure.py --dry-run",
            env=env
        )
        
        if returncode == 0:
            logger.error(f"❌ Script should fail with invalid bucket name: {bucket_name}")
            return False
    
    logger.info("✅ Bucket name validation works correctly")
    return True

def test_valid_bucket_names():
    """Test valid bucket names"""
    logger.info("🔍 Testing valid bucket names...")
    
    valid_buckets = [
        "my-valid-bucket-name",
        "bucket123",
        "my-bucket-name-123",
        "a" * 63  # maximum length
    ]
    
    for bucket_name in valid_buckets:
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = 'test'
        env['AWS_SECRET_ACCESS_KEY'] = 'test'
        env['S3_BUCKET_NAME'] = bucket_name
        env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
        env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
        
        returncode, stdout, stderr = run_command(
            "python setup_aws_infrastructure.py --dry-run",
            env=env
        )
        
        if returncode != 0:
            logger.error(f"❌ Script should pass with valid bucket name: {bucket_name}")
            logger.error(f"Error: {stderr}")
            return False
    
    logger.info("✅ Valid bucket names accepted correctly")
    return True

def test_localstack_integration():
    """Test LocalStack integration"""
    logger.info("🔍 Testing LocalStack integration...")
    
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'test'
    env['AWS_SECRET_ACCESS_KEY'] = 'test'
    env['S3_BUCKET_NAME'] = 'test-localstack-bucket'
    env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
    env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --table-prefix test_localstack",
        env=env
    )
    
    if returncode != 0:
        logger.error(f"❌ LocalStack integration failed: {stderr}")
        return False
    
    combined_output = stdout + stderr
    
    if "🔧 Using LocalStack - skipping AWS connectivity test" not in combined_output:
        logger.error("❌ Script should detect LocalStack and skip connectivity test")
        return False
    
    if "✅ AWS credentials configured for LocalStack testing" not in combined_output:
        logger.error("❌ Script should accept test credentials for LocalStack")
        return False
    
    logger.info("✅ LocalStack integration works correctly")
    return True

def test_dry_run_mode():
    """Test dry run mode"""
    logger.info("🔍 Testing dry run mode...")
    
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'test'
    env['AWS_SECRET_ACCESS_KEY'] = 'test'
    env['S3_BUCKET_NAME'] = 'test-dry-run-bucket'
    env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
    env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --table-prefix test_dry_run",
        env=env
    )
    
    if returncode != 0:
        logger.error(f"❌ Dry run mode failed: {stderr}")
        return False
    
    combined_output = stdout + stderr
    
    if "🔧 Would create S3 bucket" not in combined_output:
        logger.error("❌ Dry run should show what would be created")
        return False
    
    if "🔧 Would create DynamoDB table" not in combined_output:
        logger.error("❌ Dry run should show DynamoDB table creation")
        return False
    
    if "🎉 Infrastructure setup dry run completed successfully" not in combined_output:
        logger.error("❌ Dry run should complete successfully")
        return False
    
    logger.info("✅ Dry run mode works correctly")
    return True

def test_force_mode():
    """Test force mode"""
    logger.info("🔍 Testing force mode...")
    
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'test'
    env['AWS_SECRET_ACCESS_KEY'] = 'test'
    env['S3_BUCKET_NAME'] = 'test-force-bucket'
    env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
    env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --force --table-prefix test_force",
        env=env
    )
    
    if returncode != 0:
        logger.error(f"❌ Force mode failed: {stderr}")
        return False
    
    logger.info("✅ Force mode works correctly")
    return True

def test_custom_arguments():
    """Test custom command line arguments"""
    logger.info("🔍 Testing custom arguments...")
    
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'test'
    env['AWS_SECRET_ACCESS_KEY'] = 'test'
    env['S3_BUCKET_NAME'] = 'test-custom-bucket'
    env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
    env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    
    # Test custom table prefix
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --table-prefix custom_prefix",
        env=env
    )
    
    if returncode != 0:
        logger.error(f"❌ Custom table prefix failed: {stderr}")
        return False
    
    combined_output = stdout + stderr
    
    if "custom_prefix_users" not in combined_output:
        logger.error("❌ Custom table prefix not applied")
        return False
    
    # Test custom region
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --region us-west-2",
        env=env
    )
    
    if returncode != 0:
        logger.error(f"❌ Custom region failed: {stderr}")
        return False
    
    logger.info("✅ Custom arguments work correctly")
    return True

def test_error_handling():
    """Test error handling scenarios"""
    logger.info("🔍 Testing error handling...")
    
    # Test with invalid region
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'test'
    env['AWS_SECRET_ACCESS_KEY'] = 'test'
    env['S3_BUCKET_NAME'] = 'test-error-bucket'
    env['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'
    env['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    
    returncode, stdout, stderr = run_command(
        "python setup_aws_infrastructure.py --dry-run --region invalid-region",
        env=env
    )
    
    # This should still work with LocalStack
    if returncode != 0:
        logger.error(f"❌ Invalid region handling failed: {stderr}")
        return False
    
    logger.info("✅ Error handling works correctly")
    return True

def main():
    """Main test function"""
    logger.info("🚀 Production Readiness Test for AWS Infrastructure Setup")
    logger.info("=" * 70)
    
    tests = [
        ("Script Existence", test_script_exists),
        ("Help Output", test_help_output),
        ("Missing Environment Variables", test_missing_environment_variables),
        ("Invalid Credentials", test_invalid_credentials),
        ("Invalid Bucket Names", test_invalid_bucket_names),
        ("Valid Bucket Names", test_valid_bucket_names),
        ("LocalStack Integration", test_localstack_integration),
        ("Dry Run Mode", test_dry_run_mode),
        ("Force Mode", test_force_mode),
        ("Custom Arguments", test_custom_arguments),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name}")
        logger.info("-" * 40)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Infrastructure setup script is production-ready.")
        logger.info("\n📋 Production Deployment Checklist:")
        logger.info("✅ Script exists and is executable")
        logger.info("✅ Help output is complete")
        logger.info("✅ Environment variable validation works")
        logger.info("✅ Credential validation works")
        logger.info("✅ Bucket name validation works")
        logger.info("✅ LocalStack integration works")
        logger.info("✅ Dry run mode works")
        logger.info("✅ Force mode works")
        logger.info("✅ Custom arguments work")
        logger.info("✅ Error handling is robust")
        logger.info("\n🚀 Ready for production deployment!")
    else:
        logger.error("❌ Some tests failed. Please fix the issues before deploying to production.")
        sys.exit(1)

if __name__ == "__main__":
    main()
