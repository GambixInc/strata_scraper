# Strata Scraper - EC2 Deployment Guide

## 📋 Overview

This guide provides step-by-step instructions for deploying the Strata Scraper backend application on an Amazon EC2 instance. The application is a Flask-based web scraper with SQLite database, AWS Cognito authentication, and comprehensive API endpoints.

## 🏗️ Architecture

- **Framework**: Flask 2.3.3
- **Database**: SQLite (Gambix Strata Database)
- **Authentication**: AWS Cognito
- **Web Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Process Manager**: Systemd
- **Monitoring**: Sentry SDK
- **Rate Limiting**: Flask-Limiter

## 📦 Prerequisites

### AWS Requirements
- EC2 instance (t3.medium or larger recommended)
- Security Group with ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (App)
- IAM role with Cognito permissions (if using AWS Cognito)
- Domain name (optional, for SSL)

### Instance Specifications
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 20GB minimum
- **CPU**: 2 vCPUs minimum

## 🚀 Deployment Steps

### 1. Launch EC2 Instance

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. Update System and Install Dependencies

```bash
#!/bin/bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and system dependencies
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y nginx
sudo apt install -y git curl wget unzip
sudo apt install -y build-essential libxml2-dev libxslt-dev
sudo apt install -y supervisor

# Install Node.js (for potential frontend deployment)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application directory
sudo mkdir -p /opt/strata-scraper
sudo chown ubuntu:ubuntu /opt/strata-scraper
```

### 3. Clone and Setup Application

```bash
#!/bin/bash
cd /opt/strata-scraper

# Clone your repository (replace with your actual repo URL)
git clone https://github.com/your-username/strata-scraper.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data scraped_data optimized_sites config
```

### 4. Environment Configuration

```bash
#!/bin/bash
# Create environment file
cat > /opt/strata-scraper/.env << EOF
# Application Configuration
PORT=8080
HOST=127.0.0.1
DEBUG=False
FLASK_ENV=production

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=/opt/strata-scraper/data/gambix_strata.db

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000

# Rate Limiting
RATE_LIMIT_STORAGE_URL=memory://

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/opt/strata-scraper/logs/web_scraper.log

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Application Settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/opt/strata-scraper/scraped_data
ALLOWED_EXTENSIONS=html,css,js,json,txt

# Performance Settings
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
EOF

# Set proper permissions
chmod 600 /opt/strata-scraper/.env
```

### 5. Gunicorn Configuration

```bash
#!/bin/bash
# Create Gunicorn configuration
cat > /opt/strata-scraper/gunicorn.conf.py << EOF
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/opt/strata-scraper/logs/gunicorn_access.log"
errorlog = "/opt/strata-scraper/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "strata-scraper"

# User and group
user = "ubuntu"
group = "ubuntu"

# Preload app for better performance
preload_app = True

# SSL (if using HTTPS directly)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
EOF
```

### 6. Systemd Service Configuration

```bash
#!/bin/bash
# Create systemd service file
sudo tee /etc/systemd/system/strata-scraper.service > /dev/null << EOF
[Unit]
Description=Strata Scraper Flask Application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/strata-scraper
Environment=PATH=/opt/strata-scraper/venv/bin
ExecStart=/opt/strata-scraper/venv/bin/gunicorn --config gunicorn.conf.py server:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/strata-scraper/logs /opt/strata-scraper/data /opt/strata-scraper/scraped_data /opt/strata-scraper/optimized_sites

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable strata-scraper
```

### 7. Nginx Configuration

```bash
#!/bin/bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/strata-scraper > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=scrape:10m rate=2r/s;

    # Logging
    access_log /var/log/nginx/strata-scraper_access.log;
    error_log /var/log/nginx/strata-scraper_error.log;

    # Client max body size
    client_max_body_size 16M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    # API routes with rate limiting
    location /api/scrape {
        limit_req zone=scrape burst=5 nodelay;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Other API routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8080/api/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files (if serving frontend)
    location / {
        root /opt/strata-scraper/strata_design;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ \.(env|py|pyc|log)$ {
        deny all;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/strata-scraper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 8. SSL Certificate (Optional but Recommended)

```bash
#!/bin/bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add this line: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 9. Firewall Configuration

```bash
#!/bin/bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

### 10. Start the Application

```bash
#!/bin/bash
# Start the application
sudo systemctl start strata-scraper

# Check status
sudo systemctl status strata-scraper

# View logs
sudo journalctl -u strata-scraper -f
```

## 🔧 Monitoring and Maintenance

### 1. Log Management

```bash
#!/bin/bash
# Create log rotation configuration
sudo tee /etc/logrotate.d/strata-scraper > /dev/null << EOF
/opt/strata-scraper/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload strata-scraper
    endscript
}
EOF
```

### 2. Database Backup Script

```bash
#!/bin/bash
# Create backup script
cat > /opt/strata-scraper/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/strata-scraper/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/opt/strata-scraper/data/gambix_strata.db"

mkdir -p $BACKUP_DIR

# Backup database
cp $DB_FILE $BACKUP_DIR/gambix_strata_$DATE.db

# Compress backup
gzip $BACKUP_DIR/gambix_strata_$DATE.db

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db.gz" -mtime +7 -delete

echo "Backup completed: gambix_strata_$DATE.db.gz"
EOF

chmod +x /opt/strata-scraper/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/strata-scraper/backup.sh") | crontab -
```

### 3. Health Check Script

```bash
#!/bin/bash
# Create health check script
cat > /opt/strata-scraper/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8080/api/health"
LOG_FILE="/opt/strata-scraper/logs/health_check.log"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -eq 200 ]; then
    echo "$(date): Health check passed" >> $LOG_FILE
else
    echo "$(date): Health check failed (HTTP $response)" >> $LOG_FILE
    # Restart service if health check fails
    sudo systemctl restart strata-scraper
fi
EOF

chmod +x /opt/strata-scraper/health_check.sh

# Add to crontab for health monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/strata-scraper/health_check.sh") | crontab -
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status strata-scraper
   sudo journalctl -u strata-scraper -n 50
   ```

2. **Permission issues**
   ```bash
   sudo chown -R ubuntu:ubuntu /opt/strata-scraper
   sudo chmod -R 755 /opt/strata-scraper
   ```

3. **Port conflicts**
   ```bash
   sudo netstat -tlnp | grep :8080
   sudo lsof -i :8080
   ```

4. **Database issues**
   ```bash
   # Check database file
   ls -la /opt/strata-scraper/data/
   
   # Test database connection
   python3 -c "from database import GambixStrataDatabase; db = GambixStrataDatabase(); print('DB OK')"
   ```

### Performance Tuning

1. **Increase worker processes**
   ```bash
   # Edit gunicorn.conf.py
   workers = multiprocessing.cpu_count() * 2 + 1
   ```

2. **Optimize Nginx**
   ```bash
   # Edit /etc/nginx/nginx.conf
   worker_processes auto;
   worker_connections 1024;
   ```

3. **Monitor resource usage**
   ```bash
   htop
   df -h
   free -h
   ```

## 📊 Monitoring Setup

### 1. Basic Monitoring with htop
```bash
sudo apt install -y htop
htop
```

### 2. Application Metrics
```bash
# Monitor application logs
tail -f /opt/strata-scraper/logs/web_scraper.log

# Monitor Nginx logs
tail -f /var/log/nginx/strata-scraper_access.log
tail -f /var/log/nginx/strata-scraper_error.log
```

### 3. System Monitoring
```bash
# Install monitoring tools
sudo apt install -y iotop iostat

# Monitor disk I/O
iotop

# Monitor CPU and memory
iostat -x 1
```

## 🔄 Deployment Updates

### 1. Update Application
```bash
#!/bin/bash
cd /opt/strata-scraper

# Backup current version
cp -r . ../strata-scraper-backup-$(date +%Y%m%d_%H%M%S)

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart strata-scraper

# Check status
sudo systemctl status strata-scraper
```

### 2. Rollback Script
```bash
#!/bin/bash
BACKUP_DIR="/opt/strata-scraper-backup-*"
LATEST_BACKUP=$(ls -td $BACKUP_DIR | head -1)

if [ -n "$LATEST_BACKUP" ]; then
    sudo systemctl stop strata-scraper
    rm -rf /opt/strata-scraper
    cp -r $LATEST_BACKUP /opt/strata-scraper
    sudo systemctl start strata-scraper
    echo "Rolled back to: $LATEST_BACKUP"
else
    echo "No backup found"
fi
```

## 🔐 Security Considerations

1. **Update environment variables** with secure values
2. **Use HTTPS** with valid SSL certificates
3. **Regular security updates**
4. **Monitor logs** for suspicious activity
5. **Backup data** regularly
6. **Use strong passwords** and SSH keys
7. **Limit access** to necessary ports only

## 📞 Support

For issues and support:
1. Check application logs: `/opt/strata-scraper/logs/`
2. Check system logs: `sudo journalctl -u strata-scraper`
3. Check Nginx logs: `/var/log/nginx/`
4. Monitor system resources: `htop`, `df -h`

---

**Note**: Replace placeholder values (domain names, AWS credentials, etc.) with your actual configuration values before deployment.
