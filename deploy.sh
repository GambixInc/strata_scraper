#!/bin/bash

# Strata Scraper API - EC2 Docker Deployment Script
# This script ONLY deploys the API/backend service, leaving nginx untouched
# Usage: ./deploy.sh [production|development]

set -e

ENVIRONMENT=${1:-development}
echo "🚀 Deploying Strata Scraper API in $ENVIRONMENT mode..."
echo "⚠️  This deployment will ONLY affect the API service (strata-scraper)"
echo "⚠️  Nginx and other services will remain untouched"
echo "☁️  S3 storage integration is included (with automatic local fallback)"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data scraped_data optimized_sites config backups

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    echo "💡 Tip: For S3 storage, update AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME"
    cat > .env << EOF
# Application Configuration
PORT=8080
HOST=0.0.0.0
DEBUG=False
FLASK_ENV=production

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=/app/data/gambix_strata.db

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000

# Rate Limiting
RATE_LIMIT_STORAGE_URL=memory://

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/app/logs/web_scraper.log

# AWS S3 Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
S3_BUCKET_NAME=your-s3-bucket-name
S3_ENDPOINT_URL=https://s3.amazonaws.com

# Application Settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/app/scraped_data
ALLOWED_EXTENSIONS=html,css,js,json,txt

# Performance Settings
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
EOF
    echo "⚠️  Please update the .env file with your actual configuration values!"
fi

# Stop only the strata-scraper service
echo "🛑 Stopping strata-scraper service..."
docker-compose stop strata-scraper || true
docker-compose rm -f strata-scraper || true

# Build and start only the strata-scraper service
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting strata-scraper in production mode..."
    docker-compose up -d --build strata-scraper
else
    echo "🔧 Starting strata-scraper in development mode..."
    docker-compose up -d --build strata-scraper
fi

# Wait for containers to be ready
echo "⏳ Waiting for containers to be ready..."
sleep 10

# Check health
echo "🏥 Checking application health..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Strata Scraper API is healthy!"
else
    echo "❌ Strata Scraper API health check failed. Check logs with: docker-compose logs strata-scraper"
    exit 1
fi

# Check AWS infrastructure
echo "☁️ Checking AWS infrastructure..."
if [ -f .env ]; then
    if grep -q "your-aws-access-key-id" .env || grep -q "your-s3-bucket-name" .env; then
        echo "⚠️  AWS configuration appears to be using default values"
        echo "💡 To enable AWS services, update your .env file with actual AWS credentials"
        echo "💡 Or run: python setup_aws_infrastructure.py --dry-run"
    else
        echo "✅ AWS configuration appears to be set up"
        echo "💡 Test infrastructure with: python setup_aws_infrastructure.py --dry-run"
        echo "💡 Create infrastructure with: python setup_aws_infrastructure.py"
    fi
else
    echo "⚠️  No .env file found - AWS services will not be available"
fi

# Show status
echo "📊 Strata Scraper service status:"
docker-compose ps strata-scraper

echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f strata-scraper"
echo "  Restart: docker-compose restart strata-scraper"
echo "  Stop: docker-compose stop strata-scraper"
echo "  Update: git pull && ./deploy.sh production"

echo "🎉 Strata Scraper API deployment complete!"
echo "🌐 API is running on http://localhost:8080"
echo "🔍 Health check: http://localhost:8080/api/health"
echo "☁️ S3 storage: Configured (with local fallback)"
echo "⚠️  Note: This deployment only affects the API service. Nginx configuration remains unchanged."
