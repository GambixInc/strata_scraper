#!/bin/bash
# Configure Production Environment (EC2 with existing infrastructure)

set -e  # Exit on any error

echo "🔧 Configuring Strata Scraper for Production (EC2)"

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

# Step 1: Test AWS connectivity
echo "🔍 Testing AWS connectivity..."
if python3 -c "
import boto3
import os
try:
    # Test AWS credentials using STS
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f'✅ AWS credentials verified - Account: {identity[\"Account\"]}, User: {identity[\"Arn\"]}')
    
    # Test S3 access
    s3 = boto3.client('s3')
    s3.head_bucket(Bucket='$BUCKET_NAME')
    print('✅ S3 bucket accessible')
    
    # Test DynamoDB access
    dynamodb = boto3.resource('dynamodb')
    tables = list(dynamodb.tables.all())
    print(f'✅ DynamoDB accessible ({len(tables)} tables found)')
except Exception as e:
    print(f'❌ AWS connectivity failed: {e}')
    print('💡 Please ensure:')
    print('   - AWS CLI is configured (aws configure)')
    print('   - IAM role has proper permissions (if using EC2)')
    print('   - S3 bucket exists: $BUCKET_NAME')
    print('   - DynamoDB tables exist with prefix: $TABLE_PREFIX')
    exit(1)
"; then
    echo "✅ AWS connectivity test passed"
else
    echo "❌ AWS connectivity test failed"
    echo "💡 Please ensure:"
    echo "   - AWS CLI is configured: aws configure"
    echo "   - IAM role has proper permissions (if using EC2)"
    echo "   - S3 bucket exists: $BUCKET_NAME"
    echo "   - DynamoDB tables exist with prefix: $TABLE_PREFIX"
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

# Step 3: Update .env.production
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

# Note: AWS credentials are handled by AWS CLI or IAM roles
# No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY
EOF

echo "✅ Production configuration completed!"
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
echo "   # or if running directly:"
echo "   pkill -f 'python.*server.py' && python3 server.py &"
