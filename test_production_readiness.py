#!/usr/bin/env python3
"""
Production Readiness Test for DynamoDB Setup
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test production readiness for DynamoDB')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Environment file to load')
    parser.add_argument('--table-prefix', type=str, default='gambix_strata',
                       help='DynamoDB table prefix')
    return parser.parse_args()

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    logger.info("🔍 Checking AWS Credentials...")
    
    try:
        # Test AWS credentials by trying to create a client
        # This will use the AWS CLI credential chain automatically
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"✅ AWS credentials verified - Account: {identity['Account']}, User: {identity['Arn']}")
        return True
    except Exception as e:
        logger.error(f"❌ AWS credentials not found or invalid: {e}")
        logger.error("Please ensure AWS CLI is configured or IAM role is attached")
        return False

def test_aws_connectivity():
    """Test AWS connectivity and permissions"""
    logger.info("🔍 Testing AWS Connectivity...")
    
    try:
        # Test basic AWS connectivity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"✅ AWS connectivity successful - Account: {identity['Account']}")
        
        # Test DynamoDB connectivity
        dynamodb = boto3.client('dynamodb')
        dynamodb.list_tables()
        logger.info("✅ DynamoDB connectivity successful")
        
        return True
        
    except NoCredentialsError:
        logger.error("❌ No AWS credentials found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnrecognizedClientException':
            logger.error("❌ Invalid AWS credentials")
        elif error_code == 'AccessDenied':
            logger.error("❌ Insufficient AWS permissions")
        else:
            logger.error(f"❌ AWS error: {error_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_dynamodb_permissions(table_prefix):
    """Test DynamoDB permissions by attempting to create a test table"""
    logger.info("🔍 Testing DynamoDB Permissions...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        test_table_name = f"{table_prefix}_test_permissions"
        
        # Try to create a test table
        table = dynamodb.create_table(
            TableName=test_table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        
        # Wait for table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=test_table_name)
        logger.info(f"✅ DynamoDB table creation successful: {test_table_name}")
        
        # Clean up - delete the test table
        table.delete()
        table.meta.client.get_waiter('table_not_exists').wait(TableName=test_table_name)
        logger.info(f"✅ DynamoDB table deletion successful: {test_table_name}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            logger.error("❌ Insufficient DynamoDB permissions")
        elif error_code == 'ResourceInUseException':
            logger.warning(f"⚠️  Test table already exists: {test_table_name}")
            return True
        else:
            logger.error(f"❌ DynamoDB error: {error_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected DynamoDB error: {e}")
        return False

def test_dynamodb_implementation(table_prefix):
    """Test the DynamoDB implementation"""
    logger.info("🔍 Testing DynamoDB Implementation...")
    
    try:
        from dynamodb_database import DynamoDBDatabase
        
        # Initialize database
        db = DynamoDBDatabase(table_prefix=f"{table_prefix}_test")
        logger.info("✅ DynamoDB implementation initialized successfully")
        
        # Test basic operations
        user_id = db.create_user(
            email="prod_test@example.com",
            name="Production Test User",
            role="user"
        )
        logger.info(f"✅ User creation successful: {user_id}")
        
        # Clean up
        # Note: We don't have a delete_user method, but that's okay for this test
        
        return True
        
    except ImportError:
        logger.error("❌ DynamoDB implementation not found")
        return False
    except Exception as e:
        logger.error(f"❌ DynamoDB implementation error: {e}")
        return False

def check_environment_configuration():
    """Check environment configuration"""
    logger.info("🔍 Checking Environment Configuration...")
    
    # Check required environment variables
    required_vars = {
        'AWS_ACCESS_KEY_ID': 'AWS Access Key ID',
        'AWS_SECRET_ACCESS_KEY': 'AWS Secret Access Key',
        'AWS_REGION': 'AWS Region',
        'DYNAMODB_TABLE_PREFIX': 'DynamoDB Table Prefix'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        elif 'your-' in value or 'placeholder' in value:
            logger.warning(f"⚠️  {var} appears to be a placeholder value")
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ Environment configuration is complete")
    return True

def check_docker_configuration():
    """Check Docker configuration for production"""
    logger.info("🔍 Checking Docker Configuration...")
    
    # Check if docker-compose.prod.yml exists
    if not os.path.exists('docker-compose.prod.yml'):
        logger.error("❌ docker-compose.prod.yml not found")
        return False
    
    # Check if Dockerfile exists
    if not os.path.exists('Dockerfile'):
        logger.error("❌ Dockerfile not found")
        return False
    
    logger.info("✅ Docker configuration files found")
    return True

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("🔍 Checking Dependencies...")
    
    required_packages = [
        'boto3'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    logger.info("✅ All required dependencies are available")
    return True

def main():
    """Main production readiness test"""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    logger.info("🚀 Production Readiness Test for DynamoDB")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Configuration", check_environment_configuration),
        ("Dependencies", check_dependencies),
        ("Docker Configuration", check_docker_configuration),
        ("AWS Credentials", check_aws_credentials),
        ("AWS Connectivity", test_aws_connectivity),
        ("DynamoDB Permissions", lambda: test_dynamodb_permissions(args.table_prefix)),
        ("DynamoDB Implementation", lambda: test_dynamodb_implementation(args.table_prefix))
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
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Production Readiness Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! DynamoDB is ready for production.")
        logger.info("\n📋 Production Deployment Checklist:")
        logger.info("✅ Environment variables configured")
        logger.info("✅ AWS credentials valid")
        logger.info("✅ DynamoDB permissions granted")
        logger.info("✅ Dependencies installed")
        logger.info("✅ Docker configuration ready")
        logger.info("\n🚀 Ready to deploy!")
    else:
        logger.error("❌ Some tests failed. Please fix the issues before deploying to production.")
        logger.info("\n🔧 Next Steps:")
        logger.info("1. Configure valid AWS credentials")
        logger.info("2. Grant necessary DynamoDB permissions")
        logger.info("3. Update environment variables")
        logger.info("4. Install missing dependencies")
        sys.exit(1)

if __name__ == "__main__":
    main()
