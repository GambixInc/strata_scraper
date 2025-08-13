#!/bin/bash
# Production Deployment Script for EC2 with IAM Role

set -e  # Exit on any error

echo "🚀 Deploying Strata Scraper to Production (EC2 with IAM Role)"

# Load environment variables from .env.production if it exists
if [ -f ".env.production" ]; then
    echo "📋 Loading environment from .env.production"
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "⚠️  .env.production not found, using defaults"
fi

# Configuration
BUCKET_NAME="${S3_BUCKET_NAME:-gambix-strata-production}"
TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-gambix_strata_prod}"
REGION="${AWS_REGION:-us-east-1}"

echo "📋 Configuration:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   DynamoDB Prefix: $TABLE_PREFIX"
echo "   AWS Region: $REGION"
echo ""

# Step 1: Create AWS Infrastructure
echo "🏗️ Creating AWS Infrastructure..."
python setup_aws_infrastructure.py --table-prefix "$TABLE_PREFIX"

# Step 2: Migrate data if SQLite database exists
if [ -f "gambix_strata.db" ]; then
    echo "🗄️ Migrating data from SQLite to DynamoDB..."
    python migrate_to_dynamodb.py --table-prefix "$TABLE_PREFIX"
else
    echo "ℹ️ No SQLite database found, skipping migration"
fi

# Step 3: Set environment to use DynamoDB
export USE_DYNAMODB=true
export S3_BUCKET_NAME="$BUCKET_NAME"
export DYNAMODB_TABLE_PREFIX="$TABLE_PREFIX"

echo "✅ Production deployment completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Restart your application to use DynamoDB"
echo "2. Test the application: curl http://localhost:8080/api/health"
echo "3. Monitor logs for any issues"
echo ""
echo "🔧 To restart your application:"
echo "   sudo systemctl restart your-app-service"
echo "   # or if using Docker:"
echo "   docker compose -f docker-compose.prod.yml --profile production up -d"
