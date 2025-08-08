# Strata Scraper

A comprehensive web scraping and analysis tool that extracts website content, performs SEO analysis, and stores data in SQLite database.

## Features

- **Web Scraping**: Extract HTML, CSS, JavaScript, and links from websites
- **SEO Analysis**: Comprehensive SEO metadata extraction and analysis
- **Analytics Detection**: Identify tracking tools like Google Analytics, Facebook Pixel, etc.
- **Content Analysis**: Detailed content categorization and performance insights
- **SQLite Database**: Persistent data storage with structured tables
- **REST API**: Flask-based API for scraping and data retrieval
- **Docker Support**: Containerized deployment with Docker Compose

## Database Schema

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

## Installation

### Prerequisites
- Python 3.8+
- Docker and Docker Compose (for containerized deployment)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd strata_scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python server.py
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Access the application:
- Frontend: http://localhost:8080
- API: http://localhost:8080/api

## Usage

### Command Line

Run the main scraper directly:
```bash
python main.py
```

Test the database functionality:
```bash
python test_database.py
```

### API Endpoints

#### Scrape Website
```bash
POST /api/scrape
Content-Type: application/json

{
  "url": "https://example.com",
  "user_email": "user@example.com"
}
```

#### Get User Sites
```bash
GET /api/user-sites?email=user@example.com
```

#### Get Site Statistics
```bash
GET /api/tracker/stats
```

#### Get All Tracked Sites
```bash
GET /api/tracker/sites
```

#### Get Site Summary
```bash
GET /api/tracker/summary
```

#### List Scraped Files
```bash
GET /api/files
```

#### Health Check
```bash
GET /api/health
```

### Database Operations

The application provides a comprehensive database interface:

```python
from database import Database, add_scraped_site, get_site_stats

# Initialize database
db = Database("scraper_data.db")

# Add scraped site
add_scraped_site(url, scraped_data, saved_directory, user_email)

# Get statistics
stats = get_site_stats()
print(f"Total sites: {stats['total_sites']}")
print(f"Total scrapes: {stats['total_scrapes']}")
```

## File Structure

```
strata_scraper/
├── main.py              # Main scraping logic
├── server.py            # Flask API server
├── database.py          # SQLite database operations
├── site_tracker.py      # Legacy JSON tracker (deprecated)
├── test_database.py     # Database testing script
├── docker-compose.yml   # Docker configuration
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── scraper_data.db    # SQLite database file
├── scraped_sites/     # Scraped content files
├── optimized_sites/   # Optimized versions
└── logs/              # Application logs
```

## Data Storage

### SQLite Database
- **File**: `scraper_data.db`
- **Purpose**: Structured data storage for sites, scrapes, SEO metadata, and analytics
- **Persistence**: Mounted as volume in Docker for data persistence

### File Storage
- **Scraped Sites**: `scraped_sites/` directory with organized subdirectories
- **Optimized Sites**: `optimized_sites/` directory for enhanced versions
- **Logs**: `logs/` directory for application logs

## Analysis Features

### SEO Analysis
- Meta tags extraction and analysis
- Open Graph and Twitter Card detection
- Structured data identification
- Heading hierarchy analysis
- Image optimization assessment
- Link analysis (internal/external/social)
- Content analysis (word count, keyword density)

### Analytics Detection
- Google Analytics (GA4 and Universal Analytics)
- Facebook Pixel
- Google Tag Manager
- Hotjar
- Mixpanel
- Other tracking tools

### Performance Insights
- Page speed indicators
- Resource optimization opportunities
- Content quality assessment
- SEO recommendations

## Configuration

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

## Testing

Run the database test suite:
```bash
python test_database.py
```

This will test:
- Database initialization
- Adding scraped sites
- Adding optimizations
- Statistics retrieval
- Summary generation

## Migration from JSON Tracker

The application has been migrated from JSON-based tracking to SQLite database:

1. **Old System**: `site_tracker.json` file
2. **New System**: `scraper_data.db` SQLite database
3. **Benefits**: Better performance, data integrity, and query capabilities

The legacy `site_tracker.py` is kept for reference but is no longer used by the application.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information 
