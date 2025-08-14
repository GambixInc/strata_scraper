#!/bin/bash
# Production Deployment Script for S3 + DynamoDB

set -e  # Exit on any error

echo "🚀 Deploying Strata Scraper to Production (S3 + DynamoDB)"

# Configuration
BUCKET_NAME="${S3_BUCKET_NAME:-gambix-strata-production}"
TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-gambix_strata_prod}"
REGION="${AWS_REGION:-us-east-1}"

echo "📋 Configuration:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   DynamoDB Prefix: $TABLE_PREFIX"
echo "   AWS Region: $REGION"
echo ""

# Step 1: Check AWS credentials
echo "🔍 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS credentials are configured"
    aws sts get-caller-identity
else
    echo "❌ AWS credentials not found. Please configure AWS CLI:"
    echo "   aws configure"
    exit 1
fi

# Step 2: Check if infrastructure exists
echo "🔍 Checking AWS infrastructure..."
if python3 setup_aws_infrastructure.py --table-prefix "$TABLE_PREFIX" --dry-run; then
    echo "✅ AWS infrastructure is accessible"
else
    echo "⚠️  AWS infrastructure check failed. Creating infrastructure..."
    python3 setup_aws_infrastructure.py --table-prefix "$TABLE_PREFIX"
fi

# Step 3: Test S3 connectivity
echo "🔍 Testing S3 connectivity..."
if aws s3 ls "s3://$BUCKET_NAME" > /dev/null 2>&1; then
    echo "✅ S3 bucket is accessible"
else
    echo "❌ S3 bucket not accessible. Please ensure:"
    echo "   - S3 bucket exists: $BUCKET_NAME"
    echo "   - IAM role has S3 permissions"
    exit 1
fi

# Step 4: Test DynamoDB connectivity
echo "🔍 Testing DynamoDB connectivity..."
if python3 test_dynamodb.py; then
    echo "✅ DynamoDB is accessible"
else
    echo "❌ DynamoDB not accessible. Please ensure:"
    echo "   - DynamoDB tables exist with prefix: $TABLE_PREFIX"
    echo "   - IAM role has DynamoDB permissions"
    exit 1
fi

# Step 5: Deploy with Docker
echo "🐳 Deploying with Docker..."
if docker-compose -f docker-compose.prod.yml up -d --build; then
    echo "✅ Docker deployment completed successfully"
else
    echo "❌ Docker deployment failed"
    exit 1
fi

echo "✅ Production deployment completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Test the application: curl http://localhost:8080/api/health"
echo "2. Test project creation: curl -X POST http://localhost:8080/api/projects"
echo "3. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   Restart: docker-compose -f docker-compose.prod.yml restart"
echo "   Stop: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "📊 Storage:"
echo "   - Files: S3 bucket $BUCKET_NAME"
echo "   - Database: DynamoDB tables with prefix $TABLE_PREFIX"
