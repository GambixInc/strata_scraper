# Strata Scraper - EC2 Docker Deployment Guide

## 📋 Overview

This guide provides a simple way to deploy the Strata Scraper backend on EC2 using Docker. Much simpler than the traditional deployment!

## 🏗️ Architecture

- **Container**: Docker with docker-compose
- **Application**: Flask 2.3.3 with Gunicorn
- **Database**: SQLite (persistent volume)
- **Reverse Proxy**: Nginx (optional, for SSL)
- **Process Manager**: Docker Compose

## 📦 Prerequisites

### AWS Requirements
- EC2 instance (t3.medium or larger recommended)
- Security Group with ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (App)
- Domain name (optional, for SSL)

### Instance Specifications
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 20GB minimum
- **CPU**: 2 vCPUs minimum

## 🚀 Quick Deployment (5 minutes!)

### 1. Launch EC2 Instance

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. Install Docker and Docker Compose

```bash
#!/bin/bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply docker group
exit
# SSH back in: ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Clone and Deploy

```bash
#!/bin/bash
# Clone your repository
git clone https://github.com/your-username/strata-scraper.git
cd strata-scraper

# Create environment file
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

# Create necessary directories
mkdir -p logs data scraped_data optimized_sites config

# Build and start the application
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f
```

### 4. Test the Deployment

```bash
# Test health endpoint
curl http://localhost:8080/api/health

# Test from outside (replace with your EC2 IP)
curl http://your-ec2-ip:8080/api/health
```

## 🔧 Optional: Add Nginx for SSL

### 1. Install Nginx

```bash
#!/bin/bash
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/strata-scraper > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/strata-scraper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. Configure Firewall

```bash
#!/bin/bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 🔄 Management Commands

### Start/Stop/Restart

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# View logs
docker-compose logs -f

# View status
docker-compose ps
```

### Update Application

```bash
#!/bin/bash
cd strata-scraper

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check status
docker-compose ps
```

### Backup Database

```bash
#!/bin/bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database from container
docker-compose exec strata-scraper cp /app/data/gambix_strata.db /app/backups/gambix_strata_$DATE.db

# Copy from container to host
docker cp strata-scraper:/app/backups/gambix_strata_$DATE.db $BACKUP_DIR/

# Compress backup
gzip $BACKUP_DIR/gambix_strata_$DATE.db

# Keep only last 7 days
find $BACKUP_DIR -name "*.db.gz" -mtime +7 -delete

echo "Backup completed: gambix_strata_$DATE.db.gz"
EOF

chmod +x backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * cd /home/ubuntu/strata-scraper && ./backup.sh") | crontab -
```

## 📊 Monitoring

### View Logs

```bash
# Application logs
docker-compose logs -f strata-scraper

# Nginx logs (if using Nginx)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Resources

```bash
# Docker resource usage
docker stats

# System resources
htop
df -h
free -h
```

### Health Check

```bash
# Test health endpoint
curl -f http://localhost:8080/api/health || echo "Health check failed"

# Create automated health check
cat > health_check.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/health)

if [ $response -eq 200 ]; then
    echo "$(date): Health check passed"
else
    echo "$(date): Health check failed (HTTP $response)"
    docker-compose restart
fi
EOF

chmod +x health_check.sh

# Add to crontab for health monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /home/ubuntu/strata-scraper && ./health_check.sh") | crontab -
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo netstat -tlnp | grep :8080
   sudo lsof -i :8080
   ```

2. **Container won't start**
   ```bash
   docker-compose logs strata-scraper
   docker-compose down
   docker-compose up --build
   ```

3. **Permission issues**
   ```bash
   sudo chown -R ubuntu:ubuntu /home/ubuntu/strata-scraper
   ```

4. **Database issues**
   ```bash
   # Check database file
   ls -la data/
   
   # Test database connection
   docker-compose exec strata-scraper python3 -c "from database import GambixStrataDatabase; db = GambixStrataDatabase(); print('DB OK')"
   ```

### Performance Tuning

1. **Increase resources in docker-compose.yml**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '4.0'
         memory: 4G
   ```

2. **Add Redis for caching**
   ```bash
   # Redis is already configured in docker-compose.yml
   # Just uncomment the redis service if needed
   ```

## 🔐 Security Considerations

1. **Update environment variables** with secure values
2. **Use HTTPS** with valid SSL certificates
3. **Regular security updates**
4. **Monitor logs** for suspicious activity
5. **Backup data** regularly
6. **Use strong passwords** and SSH keys
7. **Limit access** to necessary ports only

## 📞 Quick Commands Reference

```bash
# Start application
docker-compose up -d

# View logs
docker-compose logs -f

# Restart application
docker-compose restart

# Update application
git pull && docker-compose up -d --build

# Backup database
./backup.sh

# Health check
curl http://localhost:8080/api/health

# Stop application
docker-compose down
```

---

**That's it!** Your application should be running in about 5 minutes. Much simpler than the traditional deployment! 🎉

**Note**: Replace placeholder values (domain names, AWS credentials, etc.) with your actual configuration values before deployment.
