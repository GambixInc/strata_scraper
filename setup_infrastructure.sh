#!/bin/bash

# AWS Infrastructure Setup Wrapper Script
# Uses EC2 IAM role credentials automatically

set -e

echo "🚀 Setting up AWS Infrastructure for Strata Scraper"
echo "=================================================="

# Check if Python and boto3 are available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Check if boto3 is installed
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "📦 Installing boto3..."
    pip3 install boto3 python-dotenv
fi

# Check if AWS CLI is working
echo "🔍 Testing AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not working"
    echo "💡 Make sure your EC2 instance has an IAM role attached"
    exit 1
fi

echo "✅ AWS credentials working"
aws sts get-caller-identity --output table

# Set default values
BUCKET_NAME="${S3_BUCKET_NAME:-gambix-strata-production}"
TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-gambix_strata_prod}"
REGION="${AWS_REGION:-us-east-1}"

echo ""
echo "📋 Configuration:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   DynamoDB Prefix: $TABLE_PREFIX"
echo "   AWS Region: $REGION"
echo ""

# Ask for confirmation
read -p "Do you want to proceed with creating the infrastructure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Setup cancelled"
    exit 1
fi

# Run the infrastructure setup
echo ""
echo "🔧 Creating AWS infrastructure..."
python3 setup_aws_infrastructure.py \
    --table-prefix "$TABLE_PREFIX" \
    --region "$REGION"

echo ""
echo "🎉 Infrastructure setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Test connectivity: ./test_aws_connectivity.sh"
echo "2. Run migration (if needed): python3 migrate_to_dynamodb.py --table-prefix $TABLE_PREFIX"
echo "3. Deploy application: docker-compose --profile production up -d"
