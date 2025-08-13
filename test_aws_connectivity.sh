#!/bin/bash

# AWS Connectivity Test Script
# Tests connections to various AWS services from EC2 instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET_NAME:-gambix-strata-production}"
DYNAMODB_TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-gambix_strata_prod}"

echo -e "${BLUE}🔍 AWS Connectivity Test Script${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}S3 Bucket: $S3_BUCKET${NC}"
echo -e "${YELLOW}DynamoDB Prefix: $DYNAMODB_TABLE_PREFIX${NC}"
echo ""

# Function to test AWS service connectivity
test_aws_service() {
    local service_name=$1
    local test_command=$2
    local description=$3
    
    echo -e "${BLUE}Testing $service_name...${NC}"
    echo -e "${YELLOW}$description${NC}"
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name: SUCCESS${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name: FAILED${NC}"
        return 1
    fi
}

# Function to test with detailed output
test_aws_service_detailed() {
    local service_name=$1
    local test_command=$2
    local description=$3
    
    echo -e "${BLUE}Testing $service_name...${NC}"
    echo -e "${YELLOW}$description${NC}"
    
    if eval "$test_command" 2>&1; then
        echo -e "${GREEN}✅ $service_name: SUCCESS${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name: FAILED${NC}"
        return 1
    fi
}

# Initialize counters
total_tests=0
passed_tests=0
failed_tests=0

# Test 1: AWS CLI and credentials
echo -e "${BLUE}📋 Test 1: AWS CLI and Credentials${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "AWS CLI" "aws --version" "Checking if AWS CLI is installed"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

total_tests=$((total_tests + 1))
if test_aws_service "AWS Credentials" "aws sts get-caller-identity" "Checking if AWS credentials are configured"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 2: S3 Connectivity
echo ""
echo -e "${BLUE}📦 Test 2: S3 Connectivity${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "S3 List Buckets" "aws s3 ls" "Listing S3 buckets"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

total_tests=$((total_tests + 1))
if test_aws_service "S3 Bucket Access" "aws s3 ls s3://$S3_BUCKET" "Accessing specific S3 bucket"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 3: DynamoDB Connectivity
echo ""
echo -e "${BLUE}🗄️ Test 3: DynamoDB Connectivity${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "DynamoDB List Tables" "aws dynamodb list-tables --region $REGION" "Listing DynamoDB tables"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 4: CloudWatch Connectivity
echo ""
echo -e "${BLUE}📊 Test 4: CloudWatch Connectivity${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "CloudWatch List Metrics" "aws cloudwatch list-metrics --region $REGION --namespace AWS/EC2" "Listing CloudWatch metrics"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 5: EC2 Metadata
echo ""
echo -e "${BLUE}🖥️ Test 5: EC2 Instance Metadata${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "EC2 Metadata" "curl -s http://169.254.169.254/latest/meta-data/instance-id" "Accessing EC2 instance metadata"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 6: IAM Role
echo ""
echo -e "${BLUE}🔐 Test 6: IAM Role and Permissions${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "IAM Role" "curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/" "Checking IAM role"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 7: Network Connectivity
echo ""
echo -e "${BLUE}🌐 Test 7: Network Connectivity${NC}"
total_tests=$((total_tests + 1))
if test_aws_service "Internet Connectivity" "curl -s --connect-timeout 5 https://www.google.com" "Testing internet connectivity"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

total_tests=$((total_tests + 1))
if test_aws_service "AWS API Connectivity" "curl -s --connect-timeout 5 https://s3.$REGION.amazonaws.com" "Testing AWS API connectivity"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 8: Detailed S3 Operations (if bucket exists)
echo ""
echo -e "${BLUE}🔍 Test 8: Detailed S3 Operations${NC}"
if aws s3 ls s3://$S3_BUCKET > /dev/null 2>&1; then
    echo -e "${GREEN}✅ S3 bucket exists, testing operations...${NC}"
    
    # Test upload
    total_tests=$((total_tests + 1))
    if test_aws_service "S3 Upload" "echo 'test' | aws s3 cp - s3://$S3_BUCKET/test-connectivity.txt" "Testing S3 upload"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test download
    total_tests=$((total_tests + 1))
    if test_aws_service "S3 Download" "aws s3 cp s3://$S3_BUCKET/test-connectivity.txt -" "Testing S3 download"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Clean up test file
    aws s3 rm s3://$S3_BUCKET/test-connectivity.txt > /dev/null 2>&1 || true
else
    echo -e "${YELLOW}⚠️ S3 bucket does not exist, skipping detailed S3 tests${NC}"
fi

# Test 9: DynamoDB Operations (if tables exist)
echo ""
echo -e "${BLUE}🔍 Test 9: DynamoDB Operations${NC}"
DYNAMODB_TABLES=$(aws dynamodb list-tables --region $REGION --query "TableNames[?starts_with(@, '$DYNAMODB_TABLE_PREFIX')]" --output text 2>/dev/null || echo "")

if [ -n "$DYNAMODB_TABLES" ]; then
    echo -e "${GREEN}✅ DynamoDB tables found, testing operations...${NC}"
    FIRST_TABLE=$(echo "$DYNAMODB_TABLES" | head -n1)
    
    total_tests=$((total_tests + 1))
    if test_aws_service "DynamoDB Describe Table" "aws dynamodb describe-table --table-name $FIRST_TABLE --region $REGION" "Testing DynamoDB table describe"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
else
    echo -e "${YELLOW}⚠️ No DynamoDB tables found with prefix '$DYNAMODB_TABLE_PREFIX'${NC}"
fi

# Generate detailed report
echo ""
echo -e "${BLUE}📊 Test Summary${NC}"
echo "================================"
echo -e "${GREEN}✅ Passed: $passed_tests${NC}"
echo -e "${RED}❌ Failed: $failed_tests${NC}"
echo -e "${BLUE}📋 Total: $total_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! Your EC2 instance has proper AWS connectivity.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ Some tests failed. Please check your IAM permissions and network configuration.${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting Tips:${NC}"
    echo "1. Check IAM role permissions for the EC2 instance"
    echo "2. Verify security group rules allow outbound HTTPS (443)"
    echo "3. Ensure VPC has internet connectivity (NAT Gateway or Internet Gateway)"
    echo "4. Check if the S3 bucket and DynamoDB tables exist"
    echo "5. Verify AWS region configuration"
    exit 1
fi
