#!/bin/bash
# Test AWS connectivity from Docker container

echo "🔍 Testing AWS connectivity from Docker container..."

# Test AWS CLI credentials
echo "1. Testing AWS CLI credentials..."
docker exec strata-scraper aws sts get-caller-identity

# Test S3 access
echo ""
echo "2. Testing S3 bucket access..."
docker exec strata-scraper aws s3 ls s3://gambix-strata-production

# Test DynamoDB access
echo ""
echo "3. Testing DynamoDB table access..."
docker exec strata-scraper aws dynamodb list-tables --region us-east-1 | grep gambix_strata

# Test Python AWS SDK
echo ""
echo "4. Testing Python AWS SDK..."
docker exec strata-scraper python3 -c "
import boto3
import os

# Test S3
s3 = boto3.client('s3')
try:
    response = s3.list_objects_v2(Bucket='gambix-strata-production', MaxKeys=1)
    print('✅ S3 access successful')
except Exception as e:
    print(f'❌ S3 access failed: {e}')

# Test DynamoDB
dynamodb = boto3.resource('dynamodb')
try:
    tables = list(dynamodb.tables.all())
    gambix_tables = [table.name for table in tables if 'gambix_strata' in table.name]
    print(f'✅ DynamoDB access successful. Found {len(gambix_tables)} Gambix tables')
except Exception as e:
    print(f'❌ DynamoDB access failed: {e}')
"

echo ""
echo "✅ AWS connectivity test completed!"
