#!/bin/bash
# Install Python Dependencies

set -e  # Exit on any error

echo "📦 Installing Python dependencies for Strata Scraper..."

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in current directory"
    exit 1
fi

# Install dependencies
echo "🔧 Installing packages from requirements.txt..."
if pip3 install -r requirements.txt; then
    echo "✅ All dependencies installed successfully!"
    echo ""
    echo "📋 Installed packages:"
    pip3 list | grep -E "(boto3|dotenv|flask|requests|beautifulsoup4)"
    echo ""
    echo "🚀 You can now run:"
    echo "   ./configure_production.sh"
    echo "   or"
    echo "   ./deploy_to_production.sh"
else
    echo "❌ Failed to install dependencies"
    echo ""
    echo "💡 Troubleshooting:"
    echo "1. Check if pip3 is installed: which pip3"
    echo "2. Try upgrading pip: pip3 install --upgrade pip"
    echo "3. Check Python version: python3 --version"
    echo "4. Try installing with --user flag: pip3 install --user -r requirements.txt"
    exit 1
fi
