#!/bin/bash
# Unified deployment script for Strata Scraper

set -e  # Exit on any error

# Default to production
ENVIRONMENT=${1:-production}

echo "🚀 Deploying Strata Scraper ($ENVIRONMENT environment)"
echo ""

case $ENVIRONMENT in
  "production"|"prod")
    echo "📋 Production Configuration:"
    echo "   - S3 Storage: gambix-strata-production"
    echo "   - DynamoDB Tables: gambix_strata_*"
    echo "   - Port: 8080"
    echo "   - AWS IAM Role: Enabled"
    echo ""
    
    # Check AWS credentials
    echo "🔍 Checking AWS credentials..."
    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo "✅ AWS credentials verified"
        aws sts get-caller-identity
    else
        echo "❌ AWS credentials not found. Please ensure IAM role is attached."
        exit 1
    fi
    echo ""
    
    # Deploy production
    echo "🐳 Deploying production environment..."
    docker-compose --profile production up -d --build
    
    echo "✅ Production deployment completed!"
    echo "📱 Application available at: http://localhost:8080"
    ;;
    
  "development"|"dev")
    echo "📋 Development Configuration:"
    echo "   - Local Storage: SQLite + Local Files"
    echo "   - Port: 8081"
    echo "   - Debug Mode: Enabled"
    echo ""
    
    # Deploy development
    echo "🐳 Deploying development environment..."
    docker-compose --profile development up -d --build
    
    echo "✅ Development deployment completed!"
    echo "📱 Application available at: http://localhost:8081"
    ;;
    
  *)
    echo "❌ Invalid environment. Use 'production' or 'development'"
    echo ""
    echo "Usage:"
    echo "  ./deploy.sh production  # Deploy production (S3 + DynamoDB)"
    echo "  ./deploy.sh development # Deploy development (Local storage)"
    echo "  ./deploy.sh             # Deploy production (default)"
    exit 1
    ;;
esac

echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo "   Status: docker-compose ps"
