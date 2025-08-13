# 🚀 Production Deployment Guide - DynamoDB

This guide provides step-by-step instructions for deploying the Strata Scraper with DynamoDB in production.

## 📋 Prerequisites

### 1. AWS Account Setup
- AWS account with appropriate permissions
- IAM user or role with DynamoDB permissions
- AWS credentials configured

### 2. Required AWS Permissions
Your IAM user/role needs the following DynamoDB permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DeleteTable",
                "dynamodb:DescribeTable",
                "dynamodb:ListTables",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/gambix_strata_*",
                "arn:aws:dynamodb:*:*:table/gambix_strata_*/index/*"
            ]
        }
    ]
}
```

## 🔧 Environment Configuration

### 1. Create Production Environment File
Create a `.env.production` file with the following variables:

```bash
# Server Configuration
PORT=8080
HOST=0.0.0.0
DEBUG=False
FLASK_ENV=production

# AWS Configuration
AWS_ACCESS_KEY_ID=your-production-access-key
AWS_SECRET_ACCESS_KEY=your-production-secret-key
AWS_REGION=us-east-1

# DynamoDB Configuration
DYNAMODB_TABLE_PREFIX=gambix_strata

# S3 Configuration (Optional)
S3_BUCKET_NAME=your-production-s3-bucket
S3_ENDPOINT_URL=https://s3.amazonaws.com

# Security Configuration
SECRET_KEY=your-super-secret-production-key
CORS_ORIGINS=https://your-production-domain.com

# Database Configuration (for migration)
DATABASE_PATH=gambix_strata.db
```

### 2. Validate Configuration
Run the production readiness test:

```bash
python test_production_readiness.py --env-file .env.production
```

**Expected Result**: All 7 tests should pass ✅

## 🏗️ AWS Infrastructure Setup

### 1. Test Infrastructure Setup (Dry Run)
```bash
python setup_aws_infrastructure.py \
  --env-file .env.production \
  --table-prefix gambix_strata \
  --dry-run
```

### 2. Create AWS Resources
```bash
python setup_aws_infrastructure.py \
  --env-file .env.production \
  --table-prefix gambix_strata
```

### 3. Verify Infrastructure
```bash
python setup_aws_infrastructure.py \
  --env-file .env.production \
  --table-prefix gambix_strata \
  --dry-run
```

**Expected Result**: 
- ✅ S3 bucket created and accessible
- ✅ 7 DynamoDB tables created and accessible
- ✅ All infrastructure verified

## 🗄️ Database Migration

### 1. Test Migration (Dry Run)
```bash
python migrate_to_dynamodb.py \
  --env-file .env.production \
  --table-prefix gambix_strata \
  --dry-run
```

### 2. Perform Migration
```bash
python migrate_to_dynamodb.py \
  --env-file .env.production \
  --table-prefix gambix_strata
```

### 3. Verify Migration
```bash
python test_dynamodb.py \
  --env-file .env.production \
  --table-prefix gambix_strata
```

## 🐳 Docker Deployment

### 1. Build Production Image
```bash
docker build -t strata-scraper:production .
```

### 2. Deploy with Docker Compose
```bash
# Set environment variables
export $(cat .env.production | xargs)

# Deploy
docker compose -f docker-compose.prod.yml --profile production up -d
```

### 3. Verify Deployment
```bash
# Check container status
docker compose -f docker-compose.prod.yml --profile production ps

# Check logs
docker compose -f docker-compose.prod.yml --profile production logs -f strata-scraper

# Test health endpoint
curl http://localhost:8080/api/health
```

## ☁️ AWS Deployment Options

### Option 1: EC2 with Docker
```bash
# On EC2 instance
git clone <your-repo>
cd strata_scraper
cp .env.production .env
docker compose -f docker-compose.prod.yml --profile production up -d
```

### Option 2: ECS/Fargate
```bash
# Create ECS cluster and task definition
# Use docker-compose.prod.yml as reference
# Set environment variables in ECS task definition
```

### Option 3: Kubernetes
```bash
# Create Kubernetes deployment
# Use environment variables from .env.production
# Set up secrets for AWS credentials
```

## 🔍 Monitoring and Verification

### 1. Application Health
```bash
# Health check
curl http://your-domain:8080/api/health

# API test
curl -X POST http://your-domain:8080/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 2. DynamoDB Monitoring
- Check AWS CloudWatch for DynamoDB metrics
- Monitor table read/write capacity
- Set up alarms for errors

### 3. Application Logs
```bash
# View application logs
docker compose -f docker-compose.prod.yml --profile production logs -f strata-scraper

# Check for errors
docker compose -f docker-compose.prod.yml --profile production logs strata-scraper | grep ERROR
```

## 🔒 Security Considerations

### 1. AWS Credentials
- Use IAM roles instead of access keys when possible
- Rotate access keys regularly
- Use least privilege principle

### 2. Environment Variables
- Never commit `.env.production` to version control
- Use AWS Secrets Manager for sensitive data
- Encrypt environment variables in transit

### 3. Network Security
- Use VPC for private subnets
- Configure security groups appropriately
- Enable HTTPS/TLS

## 🚨 Troubleshooting

### Common Issues

#### 1. DynamoDB Connection Errors
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test DynamoDB connectivity
aws dynamodb list-tables
```

#### 2. Permission Errors
```bash
# Verify IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name your-username
```

#### 3. Container Issues
```bash
# Check container logs
docker compose -f docker-compose.prod.yml --profile production logs strata-scraper

# Restart container
docker compose -f docker-compose.prod.yml --profile production restart strata-scraper
```

### Debug Commands
```bash
# Test DynamoDB implementation
python test_dynamodb.py --env-file .env.production

# Check production readiness
python test_production_readiness.py --env-file .env.production

# Verify migration
python migrate_to_dynamodb.py --env-file .env.production --dry-run
```

## 📊 Performance Optimization

### 1. DynamoDB Settings
- Use on-demand billing for unpredictable workloads
- Set up auto-scaling for predictable workloads
- Use Global Secondary Indexes for complex queries

### 2. Application Settings
- Configure connection pooling
- Use batch operations when possible
- Implement caching strategies

### 3. Monitoring
- Set up CloudWatch dashboards
- Monitor DynamoDB throttling
- Track application performance metrics

## 🔄 Rollback Plan

### 1. Database Rollback
```bash
# If migration fails, you can continue using SQLite
# Update application to use GambixStrataDatabase instead of DynamoDBDatabase
```

### 2. Application Rollback
```bash
# Revert to previous Docker image
docker compose -f docker-compose.prod.yml --profile production down
docker tag strata-scraper:previous strata-scraper:production
docker compose -f docker-compose.prod.yml --profile production up -d
```

## ✅ Deployment Checklist

- [ ] AWS credentials configured and tested
- [ ] DynamoDB permissions granted
- [ ] Environment variables set in `.env.production`
- [ ] Production readiness test passes (7/7)
- [ ] Migration completed successfully
- [ ] DynamoDB implementation tested
- [ ] Docker image built and tested
- [ ] Application deployed and running
- [ ] Health checks passing
- [ ] Monitoring and logging configured
- [ ] Security measures implemented

## 📞 Support

If you encounter issues during deployment:

1. Check the troubleshooting section above
2. Review application logs
3. Verify AWS permissions and credentials
4. Test with LocalStack for local debugging
5. Contact your DevOps team or AWS support

---

**🎉 Congratulations!** Your Strata Scraper is now running in production with DynamoDB! 🚀
