# AWS Connectivity Test Script (PowerShell Version)
# Tests connections to various AWS services

# Configuration
$Region = $env:AWS_REGION
if (!$Region) { $Region = "us-east-1" }

$S3Bucket = $env:S3_BUCKET_NAME
if (!$S3Bucket) { $S3Bucket = "gambix-strata-production" }

$DynamoDBTablePrefix = $env:DYNAMODB_TABLE_PREFIX
if (!$DynamoDBTablePrefix) { $DynamoDBTablePrefix = "gambix_strata_prod" }

Write-Host "🔍 AWS Connectivity Test Script" -ForegroundColor Blue
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "S3 Bucket: $S3Bucket" -ForegroundColor Yellow
Write-Host "DynamoDB Prefix: $DynamoDBTablePrefix" -ForegroundColor Yellow
Write-Host ""

# Initialize counters
$TotalTests = 0
$PassedTests = 0
$FailedTests = 0

# Function to test AWS service connectivity
function Test-AWSService {
    param(
        [string]$ServiceName,
        [string]$TestCommand,
        [string]$Description
    )
    
    Write-Host "Testing $ServiceName..." -ForegroundColor Blue
    Write-Host $Description -ForegroundColor Yellow
    
    try {
        $result = Invoke-Expression $TestCommand 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $ServiceName : SUCCESS" -ForegroundColor Green
            $script:PassedTests++
            return $true
        } else {
            Write-Host "❌ $ServiceName : FAILED" -ForegroundColor Red
            $script:FailedTests++
            return $false
        }
    } catch {
        Write-Host "❌ $ServiceName : FAILED" -ForegroundColor Red
        $script:FailedTests++
        return $false
    }
}

# Test 1: AWS CLI and credentials
Write-Host "📋 Test 1: AWS CLI and Credentials" -ForegroundColor Blue
$TotalTests++

if (Test-AWSService -ServiceName "AWS CLI" -TestCommand "aws --version" -Description "Checking if AWS CLI is installed") {
    # Test passed
} else {
    Write-Host "💡 Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" -ForegroundColor Yellow
}

$TotalTests++
Test-AWSService -ServiceName "AWS Credentials" -TestCommand "aws sts get-caller-identity" -Description "Checking if AWS credentials are configured"

# Test 2: S3 Connectivity
Write-Host ""
Write-Host "📦 Test 2: S3 Connectivity" -ForegroundColor Blue
$TotalTests++
Test-AWSService -ServiceName "S3 List Buckets" -TestCommand "aws s3 ls" -Description "Listing S3 buckets"

$TotalTests++
Test-AWSService -ServiceName "S3 Bucket Access" -TestCommand "aws s3 ls s3://$S3Bucket" -Description "Accessing specific S3 bucket"

# Test 3: DynamoDB Connectivity
Write-Host ""
Write-Host "🗄️ Test 3: DynamoDB Connectivity" -ForegroundColor Blue
$TotalTests++
Test-AWSService -ServiceName "DynamoDB List Tables" -TestCommand "aws dynamodb list-tables --region $Region" -Description "Listing DynamoDB tables"

# Test 4: CloudWatch Connectivity
Write-Host ""
Write-Host "📊 Test 4: CloudWatch Connectivity" -ForegroundColor Blue
$TotalTests++
Test-AWSService -ServiceName "CloudWatch List Metrics" -TestCommand "aws cloudwatch list-metrics --region $Region --namespace AWS/EC2" -Description "Listing CloudWatch metrics"

# Test 5: Network Connectivity
Write-Host ""
Write-Host "🌐 Test 5: Network Connectivity" -ForegroundColor Blue
$TotalTests++
Test-AWSService -ServiceName "Internet Connectivity" -TestCommand "Invoke-WebRequest -Uri 'https://www.google.com' -TimeoutSec 5 -UseBasicParsing" -Description "Testing internet connectivity"

$TotalTests++
Test-AWSService -ServiceName "AWS API Connectivity" -TestCommand "Invoke-WebRequest -Uri 'https://s3.$Region.amazonaws.com' -TimeoutSec 5 -UseBasicParsing" -Description "Testing AWS API connectivity"

# Test 6: Detailed S3 Operations (if bucket exists)
Write-Host ""
Write-Host "🔍 Test 6: Detailed S3 Operations" -ForegroundColor Blue
try {
    $bucketExists = aws s3 ls s3://$S3Bucket 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ S3 bucket exists, testing operations..." -ForegroundColor Green
        
        # Test upload
        $TotalTests++
        Test-AWSService -ServiceName "S3 Upload" -TestCommand "echo 'test' | aws s3 cp - s3://$S3Bucket/test-connectivity.txt" -Description "Testing S3 upload"
        
        # Test download
        $TotalTests++
        Test-AWSService -ServiceName "S3 Download" -TestCommand "aws s3 cp s3://$S3Bucket/test-connectivity.txt -" -Description "Testing S3 download"
        
        # Clean up test file
        aws s3 rm s3://$S3Bucket/test-connectivity.txt 2>$null
    } else {
        Write-Host "⚠️ S3 bucket does not exist, skipping detailed S3 tests" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ S3 bucket does not exist, skipping detailed S3 tests" -ForegroundColor Yellow
}

# Test 7: DynamoDB Operations (if tables exist)
Write-Host ""
Write-Host "🔍 Test 7: DynamoDB Operations" -ForegroundColor Blue
try {
    $dynamoDBTables = aws dynamodb list-tables --region $Region --query "TableNames[?starts_with(@, '$DynamoDBTablePrefix')]" --output text 2>$null
    
    if ($dynamoDBTables -and $LASTEXITCODE -eq 0) {
        Write-Host "✅ DynamoDB tables found, testing operations..." -ForegroundColor Green
        $firstTable = ($dynamoDBTables -split "`n")[0]
        
        $TotalTests++
        Test-AWSService -ServiceName "DynamoDB Describe Table" -TestCommand "aws dynamodb describe-table --table-name $firstTable --region $Region" -Description "Testing DynamoDB table describe"
    } else {
        Write-Host "⚠️ No DynamoDB tables found with prefix '$DynamoDBTablePrefix'" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ No DynamoDB tables found with prefix '$DynamoDBTablePrefix'" -ForegroundColor Yellow
}

# Generate detailed report
Write-Host ""
Write-Host "📊 Test Summary" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor White
Write-Host "✅ Passed: $PassedTests" -ForegroundColor Green
Write-Host "❌ Failed: $FailedTests" -ForegroundColor Red
Write-Host "📋 Total: $TotalTests" -ForegroundColor Blue

if ($FailedTests -eq 0) {
    Write-Host ""
    Write-Host "🎉 All tests passed! Your environment has proper AWS connectivity." -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "⚠️ Some tests failed. Please check your AWS configuration." -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting Tips:" -ForegroundColor Yellow
    Write-Host "1. Check AWS credentials configuration (aws configure)" -ForegroundColor White
    Write-Host "2. Verify AWS region configuration" -ForegroundColor White
    Write-Host "3. Check if the S3 bucket and DynamoDB tables exist" -ForegroundColor White
    Write-Host "4. Ensure internet connectivity" -ForegroundColor White
    Write-Host "5. Verify IAM permissions for the services being tested" -ForegroundColor White
    exit 1
}
