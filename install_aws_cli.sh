#!/bin/bash

# AWS CLI v2 Installation Script for Ubuntu
# This script installs AWS CLI v2 and verifies the installation

set -e

echo "🔧 Installing AWS CLI v2 on Ubuntu..."

# Check if AWS CLI is already installed
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is already installed:"
    aws --version
    exit 0
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install required dependencies
echo "📦 Installing dependencies..."
sudo apt install -y curl unzip

# Download AWS CLI v2
echo "⬇️ Downloading AWS CLI v2..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip the installer
echo "📁 Extracting AWS CLI..."
unzip awscliv2.zip

# Install AWS CLI
echo "🔧 Installing AWS CLI..."
sudo ./aws/install

# Clean up
echo "🧹 Cleaning up..."
rm -rf awscliv2.zip aws/

# Verify installation
echo "✅ Verifying installation..."
aws --version

# Test AWS credentials (if IAM role is configured)
echo ""
echo "🔐 Testing AWS credentials..."
if aws sts get-caller-identity; then
    echo "✅ AWS credentials are working!"
    echo ""
    echo "📋 Identity information:"
    aws sts get-caller-identity --output table
else
    echo "⚠️ AWS credentials not configured or IAM role not attached"
    echo ""
    echo "🔧 To configure AWS credentials manually:"
    echo "   aws configure"
    echo ""
    echo "🔧 Or attach an IAM role to your EC2 instance:"
    echo "   1. Go to EC2 Console"
    echo "   2. Select your instance"
    echo "   3. Actions > Security > Modify IAM role"
    echo "   4. Attach a role with appropriate permissions"
fi

echo ""
echo "🎉 AWS CLI installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Run the connectivity test: ./test_aws_connectivity.sh"
echo "2. If credentials fail, configure IAM role or run: aws configure"
