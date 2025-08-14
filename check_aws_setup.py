#!/usr/bin/env python3
"""
AWS Setup Checker
Verifies that AWS credentials and services are properly configured
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def check_aws_credentials():
    """Check if AWS credentials are available"""
    print("🔍 Checking AWS credentials...")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials found")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Please configure AWS CLI or set environment variables:")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
        print("   - AWS_REGION")
        return False
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return False

def check_dynamodb_access():
    """Check DynamoDB access"""
    print("\n🔍 Checking DynamoDB access...")
    
    try:
        # Get region from environment or use default
        region = os.getenv('AWS_REGION', 'us-east-1')
        print(f"   Using AWS region: {region}")
        
        dynamodb = boto3.resource('dynamodb', region_name=region)
        # Try to list tables to verify access
        tables = list(dynamodb.tables.all())
        print(f"✅ DynamoDB access verified ({len(tables)} tables found)")
        return True
    except Exception as e:
        print(f"❌ DynamoDB access error: {e}")
        return False

def check_s3_access():
    """Check S3 access"""
    print("\n🔍 Checking S3 access...")
    
    bucket_name = os.getenv('S3_BUCKET_NAME', 'gambix-strata-production')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        s3 = boto3.client('s3', region_name=region)
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket access verified: {bucket_name}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ S3 bucket not found: {bucket_name}")
            print("   Please create the bucket or check the bucket name")
        elif error_code == '403':
            print(f"❌ S3 bucket access denied: {bucket_name}")
            print("   Please check your IAM permissions")
        else:
            print(f"❌ S3 access error: {e}")
        return False
    except Exception as e:
        print(f"❌ S3 access error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 AWS Setup Checker")
    print("=" * 50)
    
    # Check credentials
    if not check_aws_credentials():
        print("\n❌ AWS setup incomplete - credentials required")
        return False
    
    # Check DynamoDB
    if not check_dynamodb_access():
        print("\n❌ AWS setup incomplete - DynamoDB access required")
        return False
    
    # Check S3
    if not check_s3_access():
        print("\n❌ AWS setup incomplete - S3 access required")
        return False
    
    print("\n🎉 AWS setup verified successfully!")
    print("   Your application is ready to run")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
