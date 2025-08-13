# Strata Scraper

A comprehensive web scraping and analysis tool that extracts website content, performs SEO analysis, and stores data in SQLite database.

## 🚀 Quick Start (Recommended)

The easiest way to run this project is using Docker:

```bash
# 1. Clone the repository
git clone <repository-url>
cd strata_scraper

# 2. Start the application with Docker
docker compose up --build

# 3. Access the application
# Frontend: http://localhost:8080
# Legacy API: http://localhost:8080/api
# Gambix Strata API: http://localhost:8080/api/gambix

# 4. (Optional) Run migration to set up new database schema
python migrate_to_gambix_strata.py --sample
```

## Features

- **Web Scraping**: Extract HTML, CSS, JavaScript, and links from websites
- **SEO Analysis**: Comprehensive SEO metadata extraction and analysis
- **Analytics Detection**: Identify tracking tools like Google Analytics, Facebook Pixel, etc.
- **Content Analysis**: Detailed content categorization and performance insights
- **SQLite Database**: Persistent data storage with structured tables
- **S3 Storage**: Cloud storage for scraped content (with local fallback)
- **REST API**: Flask-based API for scraping and data retrieval
- **Docker Support**: Containerized deployment with Docker Compose

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- Docker Desktop installed and running
- Git (for cloning the repository)

### For Local Development
- Python 3.8+
- pip (Python package manager)
- Git (for cloning the repository)

## 🛠️ Installation & Setup

### Option 1: Docker Deployment (Recommended)

This is the easiest and most reliable way to run the project:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd strata_scraper
   ```

2. **Start the application:**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   - **Frontend**: http://localhost:8080
   - **API Documentation**: http://localhost:8080/api
   - **Health Check**: http://localhost:8080/api/health

4. **Stop the application:**
   ```bash
   docker compose down
   ```

5. **Run in background:**
   ```bash
   docker compose up -d --build
   ```

### Option 2: Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd strata_scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python server.py
   ```

4. **Access the application:**
   - **Frontend**: http://localhost:8080
   - **API**: http://localhost:8080/api

## ☁️ S3 Storage Configuration (Optional)

The application can store scraped content in AWS S3 instead of local files. This is useful for production deployments and provides better scalability.

### 1. AWS Setup

1. **Create an S3 bucket** in your AWS account
2. **Create an IAM user** with S3 access permissions
3. **Generate access keys** for the IAM user

### 2. Environment Configuration

Add the following variables to your `.env` file or environment:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
S3_ENDPOINT_URL=https://s3.amazonaws.com
```

### 3. IAM Permissions

Your IAM user needs the following S3 permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

### 4. Testing S3 Integration

```bash
# Test with your S3 configuration
python test_s3_storage.py
```

### 5. How It Works

- **Automatic Fallback**: If S3 is not configured or fails, the app automatically falls back to local storage
- **File Organization**: Scraped content is organized in S3 with the structure: `scraped_sites/{domain}_{timestamp}_{uuid}/`
- **Content Types**: All scraped files (HTML, CSS, JS, metadata) are uploaded with appropriate MIME types
- **Presigned URLs**: The system can generate temporary download URLs for S3 files

### 6. Storage Comparison

| Feature | Local Storage | S3 Storage |
|---------|---------------|------------|
| **Scalability** | Limited by disk space | Virtually unlimited |
| **Durability** | Depends on local backup | 99.999999999% (11 9's) |
| **Access** | Direct file access | HTTP/HTTPS access |
| **Cost** | Free (disk space) | Pay per use |
| **Backup** | Manual | Automatic |
| **Sharing** | File system dependent | Global access |

## 🎯 How to Use

### 1. Database Migration (New Users)

If you're setting up the project for the first time or want to use the new Gambix Strata schema:

```bash
# Create new database with sample data
python migrate_to_gambix_strata.py --sample

# Or migrate from existing database
python migrate_to_gambix_strata.py --old-db scraper_data.db --new-db gambix_strata.db
```

### 2. Gambix Strata API Usage

The new Gambix Strata API provides comprehensive website optimization management:

#### Create a User
```bash
curl -X POST http://localhost:8080/api/gambix/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "preferences": {
      "notifications": true,
      "auto_optimize": false
    }
  }'
```

#### Create a Project
```bash
curl -X POST http://localhost:8080/api/gambix/projects \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "domain": "example.com",
    "name": "Example Website",
    "settings": {
      "crawl_frequency": "daily",
      "optimization_threshold": 70
    }
  }'
```

#### Add Site Health Data
```bash
curl -X POST http://localhost:8080/api/gambix/projects/project-uuid/health \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

#### Get Dashboard Data
```bash
curl http://localhost:8080/api/gambix/dashboard/user-uuid
```

### 3. Basic Web Scraping

#### Via API (Recommended)
```bash
# Scrape a website
curl -X POST http://localhost:8080/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "user_email": "your-email@example.com"
  }'
```

#### Via Python Script
```python
from main import scrape_website

# Scrape a website
result = scrape_website("https://example.com", "your-email@example.com")
print(f"Scraped: {result['url']}")
print(f"Files saved to: {result['saved_directory']}")
```

### 2. View Scraped Data

#### Check API Endpoints
```bash
# Get all scraped sites
curl http://localhost:8080/api/tracker/sites

# Get statistics
curl http://localhost:8080/api/tracker/stats

# Get summary
curl http://localhost:8080/api/tracker/summary

# List scraped files
curl http://localhost:8080/api/files
```

#### Check Local Files
```bash
# View scraped content
ls -la scraped_data/

# View database
ls -la data/scraper_data.db

# View logs
ls -la logs/
```

### 3. Database Operations

```python
from database import Database, get_site_stats, get_all_sites

# Initialize database
db = Database()

# Get statistics
stats = get_site_stats()
print(f"Total sites scraped: {stats['total_sites']}")
print(f"Total scrapes: {stats['total_scrapes']}")

# Get all sites
sites = get_all_sites()
for site in sites['sites']:
    print(f"Domain: {site['domain']}")
    print(f"Last scraped: {site['last_scraped']}")
```

### 4. Testing the Application

```bash
# Test database functionality
python test_database.py

# Test scraping functionality
python test_scraping.py

# Test tracker functionality
python test_tracker.py
```

## 📊 API Reference

### Gambix Strata API Endpoints

#### User Management
- `POST /api/gambix/users` - Create a new user
- `GET /api/gambix/users/<email>` - Get user by email

#### Project Management
- `POST /api/gambix/projects` - Create a new project
- `GET /api/gambix/projects/<user_id>` - Get all projects for a user

#### Site Health
- `POST /api/gambix/projects/<project_id>/health` - Add site health metrics
- `GET /api/gambix/projects/<project_id>/health` - Get latest site health data

#### Page Management
- `POST /api/gambix/projects/<project_id>/pages` - Add a page to a project
- `GET /api/gambix/projects/<project_id>/pages` - Get all pages for a project

#### Recommendations
- `POST /api/gambix/projects/<project_id>/recommendations` - Add a recommendation
- `GET /api/gambix/projects/<project_id>/recommendations` - Get project recommendations
- `PUT /api/gambix/recommendations/<recommendation_id>/status` - Update recommendation status

#### Alerts
- `POST /api/gambix/alerts` - Create a new alert
- `GET /api/gambix/alerts/<user_id>` - Get alerts for a user
- `PUT /api/gambix/alerts/<alert_id>/dismiss` - Dismiss an alert

#### Analytics
- `GET /api/gambix/projects/<project_id>/statistics` - Get project statistics
- `GET /api/gambix/dashboard/<user_id>` - Get dashboard data for a user

### Legacy API Endpoints

#### POST /api/scrape
Scrape a website and store the data.

**Request:**
```json
{
  "url": "https://example.com",
  "user_email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "saved_directory": "scraped_data/example.com_20231201_123456",
  "message": "Website scraped successfully"
}
```

#### GET /api/tracker/stats
Get overall statistics.

**Response:**
```json
{
  "total_sites": 15,
  "total_scrapes": 45,
  "total_optimizations": 8,
  "recent_activity": "2023-12-01 12:34:56"
}
```

#### GET /api/tracker/sites
Get all tracked sites.

**Response:**
```json
{
  "sites": [
    {
      "id": 1,
      "domain": "example.com",
      "first_scraped": "2023-11-01 10:00:00",
      "last_scraped": "2023-12-01 12:34:56",
      "scrape_count": 3
    }
  ]
}
```

#### GET /api/user-sites?email=user@example.com
Get sites scraped by a specific user.

#### GET /api/files
List all scraped files and directories.

#### GET /api/health
Health check endpoint.

### Error Handling

All API endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## 📁 File Structure

```
strata_scraper/
├── main.py              # Main scraping logic
├── server.py            # Flask API server
├── database.py          # SQLite database operations
├── site_tracker.py      # Legacy JSON tracker (deprecated)
├── test_database.py     # Database testing script
├── test_scraping.py     # Scraping testing script
├── test_tracker.py      # Tracker testing script
├── docker-compose.yml   # Docker configuration
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── data/              # Database directory (Docker)
│   └── scraper_data.db # SQLite database file
├── scraped_data/      # Scraped content files
├── logs/              # Application logs
└── optimized_sites/   # Optimized versions (if any)
```

## 🔍 What Gets Scraped

### Content Extraction
- **HTML Structure**: Complete HTML markup
- **CSS Files**: External and inline stylesheets
- **JavaScript**: External and inline scripts
- **Images**: Image URLs and metadata
- **Links**: Internal, external, and social media links

### SEO Analysis
- **Meta Tags**: Title, description, keywords, robots
- **Open Graph**: Social media optimization tags
- **Twitter Cards**: Twitter-specific meta tags
- **Structured Data**: JSON-LD, Microdata, RDFa
- **Headings**: H1-H6 hierarchy analysis
- **Canonical URLs**: Duplicate content prevention
- **Sitemaps**: XML sitemap detection

### Analytics Detection
- **Google Analytics**: GA4 and Universal Analytics
- **Facebook Pixel**: Social media tracking
- **Google Tag Manager**: GTM containers
- **Hotjar**: User behavior tracking
- **Mixpanel**: Event tracking
- **Other Tools**: Various marketing and analytics platforms

### Performance Metrics
- **Word Count**: Content length analysis
- **Link Count**: Internal/external link ratios
- **Resource Count**: CSS, JS, image statistics
- **Content Size**: Page size in MB
- **Loading Indicators**: Performance hints

## 🗄️ Database Schema

The application uses SQLite with the following tables:

### Sites Table
- `id`: Primary key
- `domain`: Website domain
- `first_scraped`: First scrape timestamp
- `last_scraped`: Last scrape timestamp
- `last_optimized`: Last optimization timestamp
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Scrapes Table
- `id`: Primary key
- `site_id`: Foreign key to sites table
- `url`: Scraped URL
- `title`: Page title
- `scraped_at`: Scrape timestamp
- `saved_directory`: Directory where files are saved
- `user_email`: User who initiated the scrape
- Various statistics (links_count, word_count, etc.)

### SEO Metadata Table
- `id`: Primary key
- `scrape_id`: Foreign key to scrapes table
- `meta_tags`: JSON field for meta tags
- `open_graph`: JSON field for Open Graph tags
- `twitter_cards`: JSON field for Twitter Card tags
- `structured_data`: JSON field for structured data
- `headings`: JSON field for heading structure
- `images`: JSON field for image data
- `internal_links`: JSON field for internal links
- `external_links`: JSON field for external links
- `social_links`: JSON field for social media links
- Various SEO fields (canonical_url, robots_directive, etc.)

### Analytics Data Table
- `id`: Primary key
- `scrape_id`: Foreign key to scrapes table
- `google_analytics`: JSON field for Google Analytics data
- `facebook_pixel`: JSON field for Facebook Pixel data
- `google_tag_manager`: JSON field for GTM data
- `hotjar`: JSON field for Hotjar data
- `mixpanel`: JSON field for Mixpanel data
- `other_tracking`: JSON field for other tracking tools
- `social_media_tracking`: JSON field for social tracking
- `analytics_summary`: JSON field for analytics summary
- `tracking_intensity`: Tracking intensity level

### Optimizations Table
- `id`: Primary key
- `site_id`: Foreign key to sites table
- `original_url`: Original URL that was optimized
- `user_profile`: User profile used for optimization
- `optimized_at`: Optimization timestamp
- `optimized_directory`: Directory where optimized files are saved
- `optimization_type`: Type of optimization performed

## ⚙️ Configuration

### Environment Variables
- `PORT`: Server port (default: 8080)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Debug mode (default: False)

### Docker Configuration
The `docker-compose.yml` file configures:
- Port mapping (8080:8080)
- Volume mounts for data persistence
- Health checks
- Automatic restarts

## 🧪 Testing

### Run All Tests
```bash
# Test database functionality
python test_database.py

# Test scraping functionality
python test_scraping.py

# Test tracker functionality
python test_tracker.py
```

### Test Database Operations
The database test suite verifies:
- Database initialization
- Adding scraped sites
- Adding optimizations
- Statistics retrieval
- Summary generation

## 🔧 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# If Docker daemon is not running
open -a Docker

# If port 8080 is already in use
# Change the port in docker-compose.yml
ports:
  - "8081:8080"  # Use port 8081 instead
```

#### Database Issues
```bash
# Reset database (Docker)
docker compose down
rm -rf data/
docker compose up --build

# Reset database (Local)
rm scraper_data.db
python server.py
```

#### Permission Issues
```bash
# Fix directory permissions
chmod -R 755 data/ logs/ scraped_data/
```

### Logs
Check application logs:
```bash
# Docker logs
docker compose logs

# Local logs
tail -f logs/app.log
```

## 📈 Use Cases

### 1. SEO Analysis
- Analyze competitor websites
- Track SEO changes over time
- Identify missing meta tags
- Monitor structured data implementation

### 2. Content Research
- Extract content from multiple sources
- Analyze content structure and quality
- Track content updates
- Monitor link building opportunities

### 3. Analytics Research
- Identify tracking tools used by competitors
- Monitor analytics implementation
- Track marketing technology adoption
- Analyze user tracking patterns

### 4. Performance Monitoring
- Track website performance changes
- Monitor resource optimization
- Analyze loading speed factors
- Identify optimization opportunities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation above
2. Review existing issues in the repository
3. Create a new issue with detailed information including:
   - Operating system
   - Python/Docker version
   - Error messages
   - Steps to reproduce

## 🔄 Migration from JSON Tracker

The application has been migrated from JSON-based tracking to SQLite database:

1. **Old System**: `site_tracker.json` file
2. **New System**: `scraper_data.db` SQLite database
3. **Benefits**: Better performance, data integrity, and query capabilities

The legacy `site_tracker.py` is kept for reference but is no longer used by the application. 
