#!/bin/bash

echo "🧪 Starting Gambix Strata Development Server"
echo "==========================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp config/app.env.example .env
    echo "✅ Created .env file from example"
    echo "📝 Please edit .env file with your development settings"
    echo ""
fi

# Set development environment variables
export USE_DYNAMODB=false
export DEBUG=true
export PORT=8080
export HOST=0.0.0.0

echo "🔧 Development Configuration:"
echo "   - Database: SQLite (local)"
echo "   - Storage: Local files"
echo "   - Debug: Enabled"
echo "   - Port: 8080"
echo ""

echo "🌐 Starting development server..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python3 server.py
