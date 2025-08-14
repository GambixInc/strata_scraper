#!/bin/bash

echo "🚀 Starting Gambix Strata Production Server"
echo "=========================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp config/app.env.example .env
    echo "✅ Created .env file from example"
    echo "📝 Please edit .env file with your production settings"
    echo ""
fi

# Set production environment variables
export USE_DYNAMODB=true
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=gambix-strata-production
export DYNAMODB_TABLE_PREFIX=gambix_strata_
export DEBUG=false
export PORT=8080
export HOST=0.0.0.0

echo "🔧 Production Configuration:"
echo "   - Database: DynamoDB"
echo "   - Storage: S3 (gambix-strata-production)"
echo "   - Region: us-east-1"
echo "   - Port: 8080"
echo ""

# Check if AWS credentials are available
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "🔍 Checking AWS credentials..."
    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo "✅ AWS credentials found and working"
    else
        echo "⚠️  AWS credentials not found or not working"
        echo "   Make sure you have:"
        echo "   - AWS CLI configured, OR"
        echo "   - IAM role attached to EC2 instance, OR"
        echo "   - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY set"
    fi
fi

echo ""
echo "🌐 Starting server..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python3 server.py
