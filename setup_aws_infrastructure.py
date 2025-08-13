#!/usr/bin/env python3
"""
AWS Infrastructure Setup Script
Creates S3 bucket and DynamoDB tables for the Strata Scraper application.
This script should only be run once during initial setup.
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
    parser = argparse.ArgumentParser(description='Setup AWS infrastructure for Strata Scraper')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Environment file to load')
    parser.add_argument('--table-prefix', type=str, default='gambix_strata',
                       help='DynamoDB table prefix')
    parser.add_argument('--region', type=str, default=None,
                       help='AWS region (overrides environment variable)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually doing it')
    parser.add_argument('--force', action='store_true',
                       help='Force recreation of existing resources')
    return parser.parse_args()

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    logger.info("🔍 Checking AWS Credentials...")
    
    # Check if we're using LocalStack
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL') or os.getenv('S3_ENDPOINT_URL')
    is_localstack = endpoint_url and 'localhost' in endpoint_url
    
    if is_localstack:
        logger.info("✅ AWS credentials configured for LocalStack testing")
        return True
    
    # For production, rely on AWS CLI's automatic credential detection
    # This includes IAM roles, AWS CLI profiles, and environment variables
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"✅ AWS credentials detected - Account: {identity['Account']}")
        return True
    except Exception as e:
        logger.error(f"❌ AWS credentials not found or invalid: {e}")
        logger.info("💡 Make sure you have:")
        logger.info("   1. IAM role attached to EC2 instance, OR")
        logger.info("   2. AWS CLI configured (aws configure), OR")
        logger.info("   3. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False

def validate_bucket_name(bucket_name):
    """Validate S3 bucket name for production use"""
    logger.info(f"🔍 Validating S3 bucket name: {bucket_name}")
    
    # S3 bucket naming rules
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        logger.error(f"❌ Bucket name must be between 3 and 63 characters long")
        return False
    
    if not bucket_name[0].isalnum():
        logger.error(f"❌ Bucket name must start with a letter or number")
        return False
    
    if bucket_name[-1] == '-':
        logger.error(f"❌ Bucket name cannot end with a hyphen")
        return False
    
    if not all(c.isalnum() or c == '-' for c in bucket_name):
        logger.error(f"❌ Bucket name can only contain lowercase letters, numbers, and hyphens")
        return False
    
    # Check for uppercase letters (S3 bucket names must be lowercase)
    if any(c.isupper() for c in bucket_name):
        logger.error(f"❌ Bucket name must be lowercase")
        return False
    
    # Check for consecutive hyphens
    if '--' in bucket_name:
        logger.error(f"❌ Bucket name cannot contain consecutive hyphens")
        return False
    
    # Check for IP address format
    import re
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
        logger.error(f"❌ Bucket name cannot be formatted as an IP address")
        return False
    
    logger.info(f"✅ S3 bucket name is valid")
    return True

def validate_table_prefix(table_prefix):
    """Validate DynamoDB table prefix for production use"""
    logger.info(f"🔍 Validating DynamoDB table prefix: {table_prefix}")
    
    # DynamoDB table naming rules
    if len(table_prefix) < 1 or len(table_prefix) > 255:
        logger.error(f"❌ Table prefix must be between 1 and 255 characters long")
        return False
    
    # Check for valid characters (a-z, A-Z, 0-9, '_', '-', '.')
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', table_prefix):
        logger.error(f"❌ Table prefix can only contain letters, numbers, underscores, hyphens, and dots")
        return False
    
    # Check for reserved words or problematic patterns
    reserved_words = ['aws', 'amazon', 'dynamodb', 'table', 'index']
    if table_prefix.lower() in reserved_words:
        logger.warning(f"⚠️  Table prefix '{table_prefix}' is a reserved word")
    
    logger.info(f"✅ DynamoDB table prefix is valid")
    return True

def test_aws_connectivity():
    """Test AWS connectivity"""
    logger.info("🔍 Testing AWS Connectivity...")
    
    try:
        # Check if we're using LocalStack
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL') or os.getenv('S3_ENDPOINT_URL')
        if endpoint_url and 'localhost' in endpoint_url:
            logger.info("🔧 Using LocalStack - skipping AWS connectivity test")
            return True
        
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"✅ AWS connectivity successful - Account: {identity['Account']}")
        return True
    except NoCredentialsError:
        logger.error("❌ No AWS credentials found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnrecognizedClientException':
            logger.error("❌ Invalid AWS credentials")
        else:
            logger.error(f"❌ AWS error: {error_code}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def setup_s3_bucket(bucket_name, region, dry_run=False, force=False):
    """Create S3 bucket if it doesn't exist"""
    logger.info(f"🔍 Setting up S3 bucket: {bucket_name}")
    
    try:
        # Check for LocalStack endpoint
        endpoint_url = os.getenv('S3_ENDPOINT_URL')
        if endpoint_url:
            s3 = boto3.client('s3', endpoint_url=endpoint_url)
        else:
            s3 = boto3.client('s3')
        
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            if force:
                logger.warning(f"⚠️  Bucket {bucket_name} already exists, but force flag is set")
            else:
                logger.info(f"✅ S3 bucket {bucket_name} already exists")
                return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"📦 S3 bucket {bucket_name} does not exist")
            else:
                logger.error(f"❌ Error checking S3 bucket: {e}")
                return False
        
        if dry_run:
            logger.info(f"🔧 Would create S3 bucket: {bucket_name}")
            return True
        
        # Create bucket
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Wait for bucket to be available
        logger.info(f"⏳ Waiting for S3 bucket {bucket_name} to be available...")
        s3.get_waiter('bucket_exists').wait(Bucket=bucket_name)
        
        logger.info(f"✅ S3 bucket {bucket_name} created successfully")
        
        # Set up bucket configuration
        setup_s3_bucket_configuration(s3, bucket_name, dry_run)
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            logger.warning(f"⚠️  Bucket {bucket_name} already exists (owned by another account)")
            return False
        elif error_code == 'BucketAlreadyOwnedByYou':
            logger.info(f"✅ S3 bucket {bucket_name} already exists and is owned by you")
            return True
        else:
            logger.error(f"❌ Error creating S3 bucket: {error_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error creating S3 bucket: {e}")
        return False

def setup_s3_bucket_configuration(s3_client, bucket_name, dry_run=False):
    """Configure S3 bucket with proper settings"""
    logger.info(f"🔧 Configuring S3 bucket: {bucket_name}")
    
    if dry_run:
        logger.info(f"🔧 Would configure S3 bucket: {bucket_name}")
        return
    
    try:
        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Set up lifecycle policy (optional - keep for 30 days)
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'DeleteOldVersions',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
                },
                {
                    'ID': 'DeleteIncompleteMultipartUploads',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 7}
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        
        logger.info(f"✅ S3 bucket {bucket_name} configured successfully")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not configure S3 bucket settings: {e}")

def setup_dynamodb_tables(table_prefix, region, dry_run=False, force=False):
    """Create DynamoDB tables if they don't exist"""
    logger.info(f"🔍 Setting up DynamoDB tables with prefix: {table_prefix}")
    
    try:
        # Check for LocalStack endpoint
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
        if endpoint_url:
            dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
            client = boto3.client('dynamodb', endpoint_url=endpoint_url)
        else:
            dynamodb = boto3.resource('dynamodb')
            client = boto3.client('dynamodb')
        
        # Define table schemas
        tables = {
            'users': {
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'email', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'email-index',
                        'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'projects': {
                'KeySchema': [{'AttributeName': 'project_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'domain', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-projects-index',
                        'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'user-domain-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'domain', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'site_health': {
                'KeySchema': [{'AttributeName': 'health_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'health_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'project-health-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'pages': {
                'KeySchema': [{'AttributeName': 'page_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'page_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'project-pages-index',
                        'KeySchema': [{'AttributeName': 'project_id', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'recommendations': {
                'KeySchema': [{'AttributeName': 'recommendation_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'recommendation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'project-recommendations-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'status', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'alerts': {
                'KeySchema': [{'AttributeName': 'alert_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'alert_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-alerts-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'status', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            'optimizations': {
                'KeySchema': [{'AttributeName': 'optimization_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'optimization_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'project-optimizations-index',
                        'KeySchema': [{'AttributeName': 'project_id', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            }
        }
        
        created_tables = []
        existing_tables = []
        
        for table_suffix, schema in tables.items():
            table_name = f"{table_prefix}_{table_suffix}"
            
            # Check if table exists
            try:
                client.describe_table(TableName=table_name)
                if force:
                    logger.warning(f"⚠️  Table {table_name} already exists, but force flag is set")
                else:
                    logger.info(f"✅ DynamoDB table {table_name} already exists")
                    existing_tables.append(table_name)
                    continue
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"📋 DynamoDB table {table_name} does not exist")
                else:
                    logger.error(f"❌ Error checking table {table_name}: {e}")
                    continue
            
            if dry_run:
                logger.info(f"🔧 Would create DynamoDB table: {table_name}")
                created_tables.append(table_name)
                continue
            
            # Create table
            try:
                table_config = {
                    'TableName': table_name,
                    'KeySchema': schema['KeySchema'],
                    'AttributeDefinitions': schema['AttributeDefinitions'],
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
                
                if 'GlobalSecondaryIndexes' in schema:
                    table_config['GlobalSecondaryIndexes'] = schema['GlobalSecondaryIndexes']
                
                table = dynamodb.create_table(**table_config)
                
                # Wait for table to be created and active
                logger.info(f"⏳ Waiting for DynamoDB table {table_name} to be active...")
                waiter = table.meta.client.get_waiter('table_exists')
                waiter.wait(
                    TableName=table_name,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 60}
                )
                
                logger.info(f"✅ DynamoDB table {table_name} created successfully")
                created_tables.append(table_name)
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceInUseException':
                    logger.warning(f"⚠️  Table {table_name} is being created by another process")
                    existing_tables.append(table_name)
                elif error_code == 'LimitExceededException':
                    logger.error(f"❌ DynamoDB table limit exceeded. Please contact AWS support or delete unused tables.")
                    return False
                elif error_code == 'ValidationException':
                    logger.error(f"❌ Invalid table configuration for {table_name}: {e.response['Error']['Message']}")
                    return False
                else:
                    logger.error(f"❌ Error creating table {table_name}: {error_code}")
                    return False
        
        if created_tables:
            logger.info(f"✅ Created {len(created_tables)} DynamoDB tables: {', '.join(created_tables)}")
        
        if existing_tables:
            logger.info(f"ℹ️  Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error setting up DynamoDB tables: {e}")
        return False

def verify_infrastructure(bucket_name, table_prefix):
    """Verify that all infrastructure is properly set up"""
    logger.info("🔍 Verifying infrastructure setup...")
    
    try:
        # Verify S3 bucket
        endpoint_url = os.getenv('S3_ENDPOINT_URL')
        if endpoint_url:
            s3 = boto3.client('s3', endpoint_url=endpoint_url)
        else:
            s3 = boto3.client('s3')
        try:
            s3.head_bucket(Bucket=bucket_name)
            logger.info(f"✅ S3 bucket {bucket_name} is accessible")
        except ClientError:
            logger.error(f"❌ S3 bucket {bucket_name} is not accessible")
            return False
        
        # Verify DynamoDB tables
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
        if endpoint_url:
            client = boto3.client('dynamodb', endpoint_url=endpoint_url)
        else:
            client = boto3.client('dynamodb')
        table_names = [
            f"{table_prefix}_users",
            f"{table_prefix}_projects", 
            f"{table_prefix}_site_health",
            f"{table_prefix}_pages",
            f"{table_prefix}_recommendations",
            f"{table_prefix}_alerts",
            f"{table_prefix}_optimizations"
        ]
        
        accessible_tables = []
        for table_name in table_names:
            try:
                client.describe_table(TableName=table_name)
                accessible_tables.append(table_name)
            except ClientError:
                logger.error(f"❌ DynamoDB table {table_name} is not accessible")
        
        if len(accessible_tables) == len(table_names):
            logger.info(f"✅ All {len(accessible_tables)} DynamoDB tables are accessible")
            return True
        else:
            logger.error(f"❌ Only {len(accessible_tables)}/{len(table_names)} tables are accessible")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying infrastructure: {e}")
        return False

def main():
    """Main infrastructure setup function"""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    logger.info("🚀 AWS Infrastructure Setup for Strata Scraper")
    logger.info("=" * 60)
    
    # Get configuration
    bucket_name = os.getenv('S3_BUCKET_NAME')
    region = args.region or os.getenv('AWS_REGION', 'us-east-1')
    
    if not bucket_name or not bucket_name.strip():
        logger.error("❌ S3_BUCKET_NAME environment variable is required")
        sys.exit(1)
    
    # Strip whitespace from bucket name
    bucket_name = bucket_name.strip()
    
    logger.info(f"📋 Configuration:")
    logger.info(f"   S3 Bucket: {bucket_name}")
    logger.info(f"   DynamoDB Prefix: {args.table_prefix}")
    logger.info(f"   AWS Region: {region}")
    logger.info(f"   Dry Run: {args.dry_run}")
    logger.info(f"   Force: {args.force}")
    logger.info("")
    
    # Check prerequisites
    if not check_aws_credentials():
        sys.exit(1)
    
    if not validate_bucket_name(bucket_name):
        sys.exit(1)
    
    if not validate_table_prefix(args.table_prefix):
        sys.exit(1)
    
    if not test_aws_connectivity():
        sys.exit(1)
    
    # Setup infrastructure
    success = True
    
    # Setup S3 bucket
    if not setup_s3_bucket(bucket_name, region, args.dry_run, args.force):
        success = False
    
    # Setup DynamoDB tables
    if not setup_dynamodb_tables(args.table_prefix, region, args.dry_run, args.force):
        success = False
    
    # Verify setup (only if not dry run)
    if not args.dry_run and success:
        if not verify_infrastructure(bucket_name, args.table_prefix):
            success = False
    
    logger.info("\n" + "=" * 60)
    
    if success:
        if args.dry_run:
            logger.info("🎉 Infrastructure setup dry run completed successfully!")
            logger.info("💡 Run without --dry-run to actually create the infrastructure")
        else:
            logger.info("🎉 AWS infrastructure setup completed successfully!")
            logger.info("\n📋 Next Steps:")
            logger.info("1. Run migration: python migrate_to_dynamodb.py")
            logger.info("2. Test application: python test_dynamodb.py")
            logger.info("3. Deploy application: docker compose -f docker-compose.prod.yml up -d")
    else:
        logger.error("❌ Infrastructure setup failed!")
        logger.info("\n🔧 Troubleshooting:")
        logger.info("1. Check AWS credentials and permissions")
        logger.info("2. Verify region settings")
        logger.info("3. Check for naming conflicts")
        sys.exit(1)

if __name__ == "__main__":
    main()
