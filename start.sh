#!/bin/bash

echo "🚀 Starting Gambix Strata (DynamoDB Only)"
echo "========================================"

# Set environment variables for DynamoDB
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=gambix-strata-production
export DYNAMODB_TABLE_PREFIX=gambix_strata_
export DEBUG=false
export PORT=8080
export HOST=0.0.0.0

# Ensure AWS region is set for all AWS services
echo "🔧 Setting AWS region: $AWS_REGION"

echo "🔧 Configuration:"
echo "   - Database: DynamoDB only"
echo "   - Storage: S3 (gambix-strata-production)"
echo "   - Region: us-east-1"
echo "   - Port: 8080"
echo ""

# Check if AWS credentials are available
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

echo ""
echo "🌐 Starting server..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python3 server.py
