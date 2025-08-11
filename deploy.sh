#!/bin/bash

# Strata Scraper - EC2 Docker Deployment Script
# Usage: ./deploy.sh [production|development]

set -e

ENVIRONMENT=${1:-development}
echo "🚀 Deploying Strata Scraper in $ENVIRONMENT mode..."

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

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

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

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Build and start containers
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting production stack..."
    docker-compose --profile production up -d --build
else
    echo "🔧 Starting development stack..."
    docker-compose up -d --build
fi

# Wait for containers to be ready
echo "⏳ Waiting for containers to be ready..."
sleep 10

# Check health
echo "🏥 Checking application health..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Application is healthy!"
else
    echo "❌ Application health check failed. Check logs with: docker-compose logs"
    exit 1
fi

# Show status
echo "📊 Container status:"
docker-compose ps

echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Restart: docker-compose restart"
echo "  Stop: docker-compose down"
echo "  Update: git pull && docker-compose up -d --build"

echo "🎉 Deployment complete! Your application is running on http://localhost:8080"
