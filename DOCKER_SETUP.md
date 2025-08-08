# Docker Setup Guide for Gambix Strata

## 🐳 Overview

This guide covers the complete Docker setup for the Gambix Strata platform, including development and production configurations.

## 🚀 Quick Start

### Development Setup (Basic)

```bash
# Start the basic application
docker compose up --build

# Access the application
# Frontend: http://localhost:8080
# API: http://localhost:8080/api/gambix
```

### Production Setup (Full Stack)

```bash
# Start with all production services
docker compose --profile production up --build

# Access services
# Application: http://localhost:8080
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

## 📋 Services Overview

### Core Services

| Service | Port | Description | Profile |
|---------|------|-------------|---------|
| `strata-scraper` | 8080 | Main application | default |
| `redis` | 6379 | Caching & rate limiting | production |
| `nginx` | 80/443 | Reverse proxy | production |
| `prometheus` | 9090 | Metrics collection | production |
| `grafana` | 3000 | Monitoring dashboards | production |

### Development vs Production

#### Development Mode
- Single container setup
- SQLite database
- In-memory rate limiting
- Basic logging

#### Production Mode
- Multi-container setup
- Redis for caching
- Nginx reverse proxy
- Prometheus + Grafana monitoring
- SSL/TLS support

## 🔧 Configuration

### Environment Variables

Copy the example environment file:
```bash
cp config/app.env.example config/app.env
```

Key configuration options:

```bash
# Database
DATABASE_TYPE=sqlite  # or mysql, dynamodb
DATABASE_PATH=/app/data/gambix_strata.db

# Security
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=*

# AWS (for DynamoDB)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# MySQL (for EC2)
MYSQL_HOST=your-mysql-host
MYSQL_DATABASE=gambix_strata
MYSQL_USER=your-user
MYSQL_PASSWORD=your-password
```

### Volume Mounts

The Docker setup includes these persistent volumes:

- `./data` → `/app/data` (Database files)
- `./logs` → `/app/logs` (Application logs)
- `./scraped_data` → `/app/scraped_data` (Scraped content)
- `./optimized_sites` → `/app/optimized_sites` (Optimized content)
- `./config` → `/app/config` (Configuration files)

## 🏗️ Production Deployment

### 1. SSL/TLS Setup

For production, configure SSL certificates:

```bash
# Place your certificates in nginx/ssl/
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem

# Update nginx.conf with your domain
sed -i 's/your-domain.com/your-actual-domain.com/g' nginx/nginx.conf
```

### 2. Environment Configuration

Create production environment file:
```bash
cp config/app.env.example config/app.env.prod
# Edit with production values
```

### 3. Start Production Stack

```bash
# Set environment file
export ENV_FILE=config/app.env.prod

# Start production stack
docker compose --profile production up -d
```

### 4. Health Checks

```bash
# Check application health
curl http://localhost/health

# Check all services
docker compose ps

# View logs
docker compose logs -f
```

## 📊 Monitoring Setup

### Prometheus Configuration

The Prometheus configuration (`monitoring/prometheus.yml`) includes:

- Application metrics scraping
- Redis monitoring
- Nginx metrics
- System metrics

### Grafana Dashboards

Pre-configured dashboards include:

- API request rates
- Response times
- Database connections
- Memory usage
- System metrics

Access Grafana at http://localhost:3000 (admin/admin)

## 🔄 Database Migration

### SQLite to MySQL

1. **Export current data**:
```bash
# Create SQL dump
docker compose exec strata-scraper sqlite3 /app/data/gambix_strata.db .dump > gambix_strata.sql
```

2. **Set up MySQL**:
```bash
# Add MySQL service to docker-compose.yml
# Update environment variables
DATABASE_TYPE=mysql
MYSQL_HOST=your-mysql-host
```

3. **Import data**:
```bash
# Convert and import
sed 's/INTEGER PRIMARY KEY AUTOINCREMENT/INT AUTO_INCREMENT PRIMARY KEY/g' gambix_strata.sql | mysql -h your-mysql-host -u your-user -p gambix_strata
```

### MySQL to DynamoDB

1. **Set up DynamoDB tables** based on `DATABASE_SCHEMA.md`
2. **Update environment variables**:
```bash
DATABASE_TYPE=dynamodb
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

3. **Run migration script** (custom implementation needed)

## 🛠️ Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker compose logs strata-scraper

# Check resource limits
docker stats

# Restart with fresh build
docker compose down
docker compose up --build
```

#### Database Connection Issues
```bash
# Check database file permissions
ls -la data/

# Verify database path
docker compose exec strata-scraper ls -la /app/data/

# Test database connection
docker compose exec strata-scraper python -c "from database import GambixStrataDatabase; db = GambixStrataDatabase(); print('DB OK')"
```

#### Port Conflicts
```bash
# Check what's using the port
lsof -i :8080

# Change port in docker-compose.yml
ports:
  - "8081:8080"  # Use port 8081 instead
```

### Performance Tuning

#### Resource Limits
Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for high load
      memory: 4G       # Increase for large datasets
```

#### Rate Limiting
Configure in `nginx/nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;  # Increase rate
```

#### Database Optimization
For MySQL:
```sql
-- Add indexes for common queries
CREATE INDEX idx_pages_project_status ON pages(project_id, status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority, status);
```

## 🔒 Security Considerations

### Production Security

1. **Change default passwords**:
   - Grafana admin password
   - Database passwords
   - Application secret key

2. **Enable SSL/TLS**:
   - Configure SSL certificates
   - Enable HTTPS redirects
   - Set security headers

3. **Network security**:
   - Use internal Docker networks
   - Restrict external access
   - Configure firewalls

4. **Access control**:
   - Implement authentication
   - Use API keys
   - Rate limiting

### Security Headers

Nginx includes security headers:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 📈 Scaling

### Horizontal Scaling

For high-traffic applications:

1. **Load Balancer**:
```yaml
# Add multiple application instances
strata-scraper-1:
  build: .
  environment:
    - INSTANCE_ID=1

strata-scraper-2:
  build: .
  environment:
    - INSTANCE_ID=2
```

2. **Database Scaling**:
   - Use MySQL read replicas
   - Implement connection pooling
   - Consider database sharding

3. **Caching**:
   - Redis cluster for high availability
   - Application-level caching
   - CDN for static content

### Vertical Scaling

Increase resource limits:
```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 8G
```

## 🧪 Testing

### Health Checks

```bash
# Application health
curl http://localhost:8080/api/health

# Database health
docker compose exec strata-scraper python -c "from database import GambixStrataDatabase; db = GambixStrataDatabase(); print('Database: OK')"

# All services health
docker compose ps
```

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test API endpoints
ab -n 1000 -c 10 http://localhost:8080/api/health
ab -n 100 -c 5 -p test-data.json -T application/json http://localhost:8080/api/gambix/users
```

### Monitoring Tests

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/targets

# Check Grafana dashboards
curl -u admin:admin http://localhost:3000/api/dashboards
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Redis Documentation](https://redis.io/documentation)

## 🆘 Support

For issues and questions:
1. Check the logs: `docker compose logs`
2. Verify configuration: `docker compose config`
3. Test individual services: `docker compose exec service-name command`
4. Review this documentation
5. Check the main README.md for application-specific issues
