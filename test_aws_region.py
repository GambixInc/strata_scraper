#!/usr/bin/env python3
"""
Test AWS Region Configuration
Simple script to verify AWS region is properly set
"""

import os
import boto3

def test_aws_region():
    """Test AWS region configuration"""
    print("🔍 Testing AWS Region Configuration")
    print("=" * 40)
    
    # Check environment variable
    region = os.getenv('AWS_REGION', 'us-east-1')
    print(f"Environment AWS_REGION: {region}")
    
    # Test STS client
    try:
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"✅ STS client works with region: {region}")
        print(f"   Account: {identity['Account']}")
    except Exception as e:
        print(f"❌ STS client failed: {e}")
        return False
    
    # Test DynamoDB client
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        tables = list(dynamodb.tables.all())
        print(f"✅ DynamoDB client works with region: {region}")
        print(f"   Tables found: {len(tables)}")
    except Exception as e:
        print(f"❌ DynamoDB client failed: {e}")
        return False
    
    # Test S3 client
    try:
        s3 = boto3.client('s3', region_name=region)
        print(f"✅ S3 client works with region: {region}")
    except Exception as e:
        print(f"❌ S3 client failed: {e}")
        return False
    
    print("\n🎉 All AWS services working with region configuration!")
    return True

if __name__ == "__main__":
    success = test_aws_region()
    exit(0 if success else 1)
