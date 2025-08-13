#!/bin/bash

# Docker Logs Backup Script
# Copies today's logs from running containers to a backup location

set -e

# Configuration
BACKUP_DIR="./logs/backup"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="strata-scraper"

echo "📋 Docker Logs Backup Script"
echo "Date: $DATE"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Container '$CONTAINER_NAME' is not running"
    echo "💡 Start the container first: docker-compose up -d"
    exit 1
fi

echo "✅ Container '$CONTAINER_NAME' is running"

# Create today's backup directory
TODAY_BACKUP_DIR="$BACKUP_DIR/$DATE"
mkdir -p "$TODAY_BACKUP_DIR"

echo "📁 Creating backup directory: $TODAY_BACKUP_DIR"

# Function to backup logs with different time ranges
backup_logs() {
    local time_range=$1
    local filename=$2
    local description=$3
    
    echo "📄 Backing up $description..."
    
    if docker logs --since "$time_range" "$CONTAINER_NAME" > "$TODAY_BACKUP_DIR/$filename" 2>&1; then
        local size=$(wc -l < "$TODAY_BACKUP_DIR/$filename")
        echo "   ✅ $filename ($size lines)"
    else
        echo "   ❌ Failed to backup $filename"
    fi
}

# Backup different time ranges
backup_logs "24h" "logs_24h_$TIMESTAMP.txt" "last 24 hours"
backup_logs "1h" "logs_1h_$TIMESTAMP.txt" "last 1 hour"
backup_logs "1d" "logs_today_$TIMESTAMP.txt" "today's logs"

# Also backup all logs (since container start)
echo "📄 Backing up all logs since container start..."
if docker logs "$CONTAINER_NAME" > "$TODAY_BACKUP_DIR/logs_all_$TIMESTAMP.txt" 2>&1; then
    local size=$(wc -l < "$TODAY_BACKUP_DIR/logs_all_$TIMESTAMP.txt")
    echo "   ✅ logs_all_$TIMESTAMP.txt ($size lines)"
else
    echo "   ❌ Failed to backup all logs"
fi

# Create a summary file
SUMMARY_FILE="$TODAY_BACKUP_DIR/backup_summary_$TIMESTAMP.txt"
cat > "$SUMMARY_FILE" << EOF
Docker Logs Backup Summary
=========================
Date: $DATE
Timestamp: $TIMESTAMP
Container: $CONTAINER_NAME
Backup Directory: $TODAY_BACKUP_DIR

Files Created:
$(ls -la "$TODAY_BACKUP_DIR"/*.txt 2>/dev/null | awk '{print $9, "(" $5 " bytes)"}' || echo "No log files found")

Container Status:
$(docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

System Info:
$(uname -a)
$(docker --version)
EOF

echo ""
echo "📊 Backup Summary:"
echo "   📁 Backup location: $TODAY_BACKUP_DIR"
echo "   📄 Files created:"
ls -la "$TODAY_BACKUP_DIR"/*.txt 2>/dev/null | awk '{print "      " $9 " (" $5 " bytes)"}' || echo "      No log files found"
echo "   📋 Summary file: backup_summary_$TIMESTAMP.txt"

echo ""
echo "✅ Log backup completed successfully!"
echo ""
echo "🔍 To view the logs:"
echo "   cat $TODAY_BACKUP_DIR/logs_24h_$TIMESTAMP.txt"
echo "   cat $TODAY_BACKUP_DIR/logs_1h_$TIMESTAMP.txt"
echo ""
echo "🧹 To clean old backups (older than 7 days):"
echo "   find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +"
