# Gambix Strata Database Setup Guide

## 🎯 Overview

This guide covers the setup and usage of the new Gambix Strata database schema, which provides a comprehensive platform for website optimization management. The system supports both SQLite (development) and can be easily migrated to MySQL on EC2 and DynamoDB for production.

## 🚀 Quick Setup

### 1. Database Migration

```bash
# Create new database with sample data
python migrate_to_gambix_strata.py --sample

# Or migrate from existing database
python migrate_to_gambix_strata.py --old-db data/scraper_data.db --new-db data/gambix_strata.db
```

### 2. Start the Application

```bash
# Using Docker (Recommended)
docker compose up --build

# Or locally
python server.py
```

## 📊 Database Schema

The Gambix Strata database includes the following tables:

### Core Tables
- **users** - User accounts and authentication
- **projects** - Website projects and settings
- **site_health** - Site health metrics and scores
- **pages** - Individual page information
- **recommendations** - Optimization recommendations
- **alerts** - System alerts and notifications
- **optimization_history** - Track optimization actions

### Key Features
- **UUID-based primary keys** for scalability
- **JSON fields** for flexible data storage
- **Foreign key relationships** for data integrity
- **Comprehensive indexing** for performance
- **Timestamp tracking** for all records

## 🔌 API Endpoints

### User Management
```bash
# Create user
POST /api/gambix/users
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "preferences": {
    "notifications": true,
    "auto_optimize": false
  }
}

# Get user by email
GET /api/gambix/users/user@example.com
```

### Project Management
```bash
# Create project
POST /api/gambix/projects
{
  "user_id": "user-uuid",
  "domain": "example.com",
  "name": "Example Website",
  "settings": {
    "crawl_frequency": "daily",
    "optimization_threshold": 70
  }
}

# Get user projects
GET /api/gambix/projects/user-uuid
```

### Site Health
```bash
# Add health metrics
POST /api/gambix/projects/project-uuid/health
{
  "overall_score": 75,
  "technical_seo": 80,
  "content_seo": 70,
  "performance": 85,
  "internal_linking": 90,
  "visual_ux": 65,
  "authority_backlinks": 60,
  "total_impressions": 5000,
  "total_engagements": 2000,
  "total_conversions": 150,
  "crawl_data": {
    "healthy_pages": 15,
    "broken_pages": 2,
    "pages_with_issues": 3,
    "total_pages": 20
  }
}

# Get latest health data
GET /api/gambix/projects/project-uuid/health
```

### Pages
```bash
# Add page
POST /api/gambix/projects/project-uuid/pages
{
  "page_url": "https://example.com/home",
  "title": "Home Page",
  "word_count": 800,
  "load_time": 2.1,
  "meta_description": "Welcome to our website",
  "h1_tags": ["Welcome to Example"],
  "images_count": 5,
  "links_count": 12
}

# Get project pages
GET /api/gambix/projects/project-uuid/pages
```

### Recommendations
```bash
# Add recommendation
POST /api/gambix/projects/project-uuid/recommendations
{
  "page_url": "https://example.com/home",
  "category": "content_seo",
  "issue": "Page content is too thin",
  "recommendation": "Expand the home page content to provide more value to visitors.",
  "priority": "high",
  "impact_score": 85,
  "guidelines": [
    "Add more detailed content sections",
    "Include customer testimonials",
    "Add a clear call-to-action"
  ]
}

# Get recommendations
GET /api/gambix/projects/project-uuid/recommendations?status=pending

# Update recommendation status
PUT /api/gambix/recommendations/recommendation-uuid/status
{
  "status": "implemented"
}
```

### Alerts
```bash
# Create alert
POST /api/gambix/alerts
{
  "user_id": "user-uuid",
  "project_id": "project-uuid",
  "type": "low_site_health",
  "title": "Site Health Below Threshold",
  "description": "example.com has a site health of only 68%",
  "priority": "medium",
  "metadata": {
    "site_health_score": 68,
    "recommendations_count": 74
  }
}

# Get user alerts
GET /api/gambix/alerts/user-uuid?status=active

# Dismiss alert
PUT /api/gambix/alerts/alert-uuid/dismiss
```

### Analytics
```bash
# Get project statistics
GET /api/gambix/projects/project-uuid/statistics

# Get dashboard data
GET /api/gambix/dashboard/user-uuid
```

## 🗄️ Database Operations

### Python Usage

```python
from database import GambixStrataDatabase

# Initialize database
db = GambixStrataDatabase('data/gambix_strata.db')

# Create user
user_id = db.create_user("user@example.com", "John Doe", "user")

# Create project
project_id = db.create_project(user_id, "example.com", "Example Website")

# Add site health
health_id = db.add_site_health(project_id, {
    'overall_score': 75,
    'technical_seo': 80,
    'content_seo': 70,
    'performance': 85
})

# Add page
page_id = db.add_page(project_id, {
    'page_url': 'https://example.com/home',
    'title': 'Home Page',
    'word_count': 800
})

# Add recommendation
rec_id = db.add_recommendation(project_id, {
    'page_url': 'https://example.com/home',
    'category': 'content_seo',
    'issue': 'Page content is too thin',
    'recommendation': 'Expand content',
    'priority': 'high',
    'impact_score': 85
})

# Get dashboard data
dashboard = db.get_dashboard_data(user_id)
```

## 🔄 Migration to Production

### SQLite to MySQL (EC2)

1. **Export SQLite data**:
```bash
# Create SQL dump
sqlite3 data/gambix_strata.db .dump > gambix_strata.sql
```

2. **Set up MySQL on EC2**:
```bash
# Install MySQL
sudo apt update
sudo apt install mysql-server

# Create database
mysql -u root -p
CREATE DATABASE gambix_strata;
```

3. **Import data**:
```bash
# Convert and import
sed 's/INTEGER PRIMARY KEY AUTOINCREMENT/INT AUTO_INCREMENT PRIMARY KEY/g' gambix_strata.sql | mysql -u root -p gambix_strata
```

### MySQL to DynamoDB

1. **Set up DynamoDB tables** based on the schema in `DATABASE_SCHEMA.md`
2. **Use AWS DMS** or custom migration scripts
3. **Update application code** to use DynamoDB SDK

## 📈 Performance Considerations

### SQLite (Development)
- **File-based**: No network latency
- **Single-threaded**: Good for development
- **No concurrent users**: Limited scalability

### MySQL (EC2)
- **Multi-threaded**: Better concurrency
- **Network latency**: Consider connection pooling
- **Indexing**: Optimize for common queries

### DynamoDB (Production)
- **Serverless**: Auto-scaling
- **Global distribution**: Low latency worldwide
- **Cost optimization**: Use on-demand or provisioned capacity

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
DATABASE_TYPE=sqlite  # or mysql, dynamodb
DATABASE_PATH=data/gambix_strata.db
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=gambix_strata
MYSQL_USER=root
MYSQL_PASSWORD=password

# AWS configuration (for DynamoDB)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Docker Configuration
The Docker setup automatically:
- Creates necessary directories
- Mounts data volumes for persistence
- Sets up health checks
- Configures networking

## 🧪 Testing

### Database Tests
```bash
# Test database functionality
python -c "
from database import GambixStrataDatabase
db = GambixStrataDatabase('data/gambix_strata.db')
print('Database test passed')
"
```

### API Tests
```bash
# Test API endpoints
curl -X POST http://localhost:8080/api/gambix/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'

curl http://localhost:8080/api/gambix/users/test@example.com
```

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8080/api/health

# Database health
python -c "
from database import GambixStrataDatabase
db = GambixStrataDatabase()
print('Database connection: OK')
"
```

### Logs
```bash
# Application logs
tail -f logs/web_scraper.log

# Docker logs
docker compose logs -f
```

## 🚀 Deployment Checklist

### Development
- [ ] Database migration completed
- [ ] Sample data created
- [ ] API endpoints tested
- [ ] Docker container running

### EC2 Deployment
- [ ] MySQL installed and configured
- [ ] Database imported
- [ ] Application configured for MySQL
- [ ] SSL certificates installed
- [ ] Firewall configured

### DynamoDB Migration
- [ ] DynamoDB tables created
- [ ] Data migration completed
- [ ] Application updated for DynamoDB
- [ ] Performance testing completed
- [ ] Cost optimization configured

## 🆘 Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check file permissions
   - Verify database path
   - Ensure directory exists

2. **Migration failures**:
   - Check old database format
   - Verify file paths
   - Review error logs

3. **API errors**:
   - Check request format
   - Verify authentication
   - Review server logs

### Support
- Check the main README.md for detailed documentation
- Review API endpoint documentation
- Check server logs for error details
- Use the health check endpoints for diagnostics

## 📚 Additional Resources

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Complete schema documentation
- [README.md](README.md) - Main project documentation
- [migrate_to_gambix_strata.py](migrate_to_gambix_strata.py) - Migration script
- [database.py](database.py) - Database implementation
- [server.py](server.py) - API server implementation
