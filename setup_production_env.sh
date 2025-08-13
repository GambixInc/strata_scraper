#!/bin/bash
# Setup Production Environment Script

echo "🔧 Setting up production environment..."

# Default values
DEFAULT_BUCKET="gambix-strata-production"
DEFAULT_PREFIX="gambix_strata_prod"
DEFAULT_REGION="us-east-1"

# Get user input
read -p "Enter S3 bucket name [$DEFAULT_BUCKET]: " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-$DEFAULT_BUCKET}

read -p "Enter DynamoDB table prefix [$DEFAULT_PREFIX]: " TABLE_PREFIX
TABLE_PREFIX=${TABLE_PREFIX:-$DEFAULT_PREFIX}

read -p "Enter AWS region [$DEFAULT_REGION]: " REGION
REGION=${REGION:-$DEFAULT_REGION}

# Create .env.production file
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

echo "✅ Production environment file created: .env.production"
echo ""
echo "📋 Configuration:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   DynamoDB Prefix: $TABLE_PREFIX"
echo "   AWS Region: $REGION"
echo ""
echo "🚀 Next steps:"
echo "   1. Run: ./configure_production.sh (recommended for EC2)"
echo "   2. Or run: ./deploy_to_production.sh (if infrastructure needs setup)"
echo "   3. Restart your application"
echo ""
echo "💡 To edit the configuration later:"
echo "   nano .env.production"
