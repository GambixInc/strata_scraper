#!/bin/bash
# Production Deployment Script for EC2 with IAM Role

set -e  # Exit on any error

echo "🚀 Deploying Strata Scraper to Production (EC2 with IAM Role)"

# Step 0: Install Python dependencies
echo "📦 Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "💡 Try installing manually: pip3 install -r requirements.txt"
    exit 1
fi

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

# Step 1: Check if infrastructure exists (optional)
echo "🔍 Checking AWS infrastructure..."
if python3 setup_aws_infrastructure.py --table-prefix "$TABLE_PREFIX" --dry-run; then
    echo "✅ AWS infrastructure is accessible"
else
    echo "⚠️  AWS infrastructure check failed. Please ensure:"
    echo "   - IAM role has proper permissions"
    echo "   - S3 bucket exists: $BUCKET_NAME"
    echo "   - DynamoDB tables exist with prefix: $TABLE_PREFIX"
    echo ""
    echo "💡 To create infrastructure (if needed):"
    echo "   python3 setup_aws_infrastructure.py --table-prefix $TABLE_PREFIX"
    exit 1
fi

# Step 2: Migrate data if SQLite database exists
if [ -f "gambix_strata.db" ]; then
    echo "🗄️ Migrating data from SQLite to DynamoDB..."
    if python3 migrate_to_dynamodb.py --table-prefix "$TABLE_PREFIX"; then
        echo "✅ Migration completed successfully"
    else
        echo "⚠️  Migration failed. You can run it manually:"
        echo "   python3 migrate_to_dynamodb.py --table-prefix $TABLE_PREFIX"
    fi
else
    echo "ℹ️ No SQLite database found, skipping migration"
fi

# Step 3: Update .env.production with current settings
echo "📝 Updating .env.production..."
cat > .env.production << EOF
# Application Settings
PORT=8080
HOST=0.0.0.0
DEBUG=False
FLASK_ENV=production

# S3 Configuration
S3_BUCKET_NAME=$BUCKET_NAME
S3_ENDPOINT_URL=https://s3.amazonaws.com

# DynamoDB Configuration
DYNAMODB_TABLE_PREFIX=$TABLE_PREFIX
AWS_REGION=$REGION

# Database Switch
USE_DYNAMODB=true
EOF

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
