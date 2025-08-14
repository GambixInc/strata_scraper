# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs strata_design

# Create a simple frontend if it doesn't exist
RUN echo '<!DOCTYPE html><html><head><title>Strata Scraper</title></head><body><h1>Strata Scraper API</h1><p>Use /api/scrape endpoint to scrape websites</p></body></html>' > strata_design/scraper_frontend.html

# Run tests during build - this will fail the build if tests don't pass
RUN echo "🧪 Running comprehensive test suite during Docker build..." && \
    python tests/test_suite.py

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV DEBUG=False

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/health || exit 1

# Run the application
CMD ["python", "server.py"] 