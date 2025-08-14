#!/bin/bash
# Check AWS setup on EC2 instance

echo "🔍 Checking AWS setup on EC2 instance..."
echo ""

# Check if we're on EC2
echo "1. Checking if running on EC2..."
if curl -s http://169.254.169.254/latest/meta-data/instance-id > /dev/null 2>&1; then
    echo "✅ Running on EC2"
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    echo "   Instance ID: $INSTANCE_ID"
else
    echo "❌ Not running on EC2"
fi

# Check for IAM role
echo ""
echo "2. Checking for IAM role..."
if curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ > /dev/null 2>&1; then
    ROLE_NAME=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    echo "✅ IAM role found: $ROLE_NAME"
    echo "   The Docker container will automatically use this role"
else
    echo "❌ No IAM role attached to EC2 instance"
fi

# Check AWS CLI credentials
echo ""
echo "3. Checking AWS CLI credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS CLI credentials configured"
    aws sts get-caller-identity
else
    echo "❌ AWS CLI credentials not configured"
fi

# Check AWS credentials file
echo ""
echo "4. Checking AWS credentials file..."
if [ -f ~/.aws/credentials ]; then
    echo "✅ AWS credentials file exists: ~/.aws/credentials"
    echo "   The Docker container will mount this file"
else
    echo "❌ AWS credentials file not found"
fi

# Check AWS config file
echo ""
echo "5. Checking AWS config file..."
if [ -f ~/.aws/config ]; then
    echo "✅ AWS config file exists: ~/.aws/config"
    echo "   The Docker container will mount this file"
else
    echo "❌ AWS config file not found"
fi

echo ""
echo "📋 Summary:"
if curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ > /dev/null 2>&1; then
    echo "✅ IAM role available - Docker container will use this automatically"
elif [ -f ~/.aws/credentials ]; then
    echo "✅ AWS CLI credentials available - Docker container will mount these"
else
    echo "❌ No AWS credentials found - You'll need to set up credentials"
fi
