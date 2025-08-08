# Gambix Strata - Database Schema

This document outlines the database structure for the Gambix Strata platform, designed to support both DynamoDB (production) and SQLite (development/testing).

## Overview

The platform manages website optimization projects, user accounts, site health monitoring, and automated optimization recommendations. The database is designed to be flexible and scalable, supporting both NoSQL (DynamoDB) and SQL (SQLite) implementations.

## Core Entities

### 1. Users
**Purpose**: Store user account information and authentication details

#### DynamoDB Structure
```json
{
  "PK": "USER#user_id",
  "SK": "PROFILE#user_id",
  "GSI1PK": "EMAIL#user_email",
  "GSI1SK": "USER#user_id",
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "Olivia Rhye",
  "role": "admin|user|viewer",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z",
  "is_active": true,
  "preferences": {
    "notifications": true,
    "auto_optimize": false,
    "theme": "light"
  }
}
```

#### SQLite Structure
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'user', 'viewer')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    preferences TEXT -- JSON string
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### 2. Projects/Websites
**Purpose**: Store website information and project settings

#### DynamoDB Structure
```json
{
  "PK": "USER#user_id",
  "SK": "PROJECT#project_id",
  "GSI1PK": "DOMAIN#domain_name",
  "GSI1SK": "PROJECT#project_id",
  "project_id": "uuid",
  "user_id": "uuid",
  "domain": "inthebox.io",
  "name": "InTheBox Website",
  "status": "active|inactive|needs_attention",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_crawl": "2024-01-01T00:00:00Z",
  "auto_optimize": true,
  "settings": {
    "crawl_frequency": "daily",
    "optimization_threshold": 70,
    "notification_emails": ["user@example.com"]
  }
}
```

#### SQLite Structure
```sql
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN ('active', 'inactive', 'needs_attention')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_crawl TIMESTAMP,
    auto_optimize BOOLEAN DEFAULT 0,
    settings TEXT, -- JSON string
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_domain ON projects(domain);
CREATE INDEX idx_projects_status ON projects(status);
```

### 3. Site Health Metrics
**Purpose**: Store overall site health scores and performance metrics

#### DynamoDB Structure
```json
{
  "PK": "PROJECT#project_id",
  "SK": "HEALTH#timestamp",
  "GSI1PK": "DOMAIN#domain_name",
  "GSI1SK": "HEALTH#timestamp",
  "project_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z",
  "overall_score": 80,
  "technical_seo": 85,
  "content_seo": 78,
  "performance": 75,
  "internal_linking": 92,
  "visual_ux": 76,
  "authority_backlinks": 78,
  "total_impressions": 6000,
  "total_engagements": 2340,
  "total_conversions": 1700,
  "crawl_data": {
    "healthy_pages": 3,
    "broken_pages": 1,
    "pages_with_issues": 5,
    "total_pages": 9
  }
}
```

#### SQLite Structure
```sql
CREATE TABLE site_health (
    health_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_score INTEGER CHECK(overall_score >= 0 AND overall_score <= 100),
    technical_seo INTEGER,
    content_seo INTEGER,
    performance INTEGER,
    internal_linking INTEGER,
    visual_ux INTEGER,
    authority_backlinks INTEGER,
    total_impressions INTEGER DEFAULT 0,
    total_engagements INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    crawl_data TEXT, -- JSON string
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_site_health_project_id ON site_health(project_id);
CREATE INDEX idx_site_health_timestamp ON site_health(timestamp);
```

### 4. Pages
**Purpose**: Store individual page information and status

#### DynamoDB Structure
```json
{
  "PK": "PROJECT#project_id",
  "SK": "PAGE#page_url",
  "GSI1PK": "STATUS#status",
  "GSI1SK": "PAGE#page_url",
  "project_id": "uuid",
  "page_url": "https://inthebox.io/home",
  "title": "Home Page",
  "status": "healthy|broken|has_issues",
  "last_crawled": "2024-01-01T00:00:00Z",
  "word_count": 1500,
  "load_time": 2.3,
  "meta_description": "Welcome to InTheBox...",
  "h1_tags": ["Welcome to InTheBox"],
  "images_count": 5,
  "links_count": 12
}
```

#### SQLite Structure
```sql
CREATE TABLE pages (
    page_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    title TEXT,
    status TEXT CHECK(status IN ('healthy', 'broken', 'has_issues')) DEFAULT 'healthy',
    last_crawled TIMESTAMP,
    word_count INTEGER DEFAULT 0,
    load_time REAL,
    meta_description TEXT,
    h1_tags TEXT, -- JSON array
    images_count INTEGER DEFAULT 0,
    links_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_pages_project_id ON pages(project_id);
CREATE INDEX idx_pages_status ON pages(status);
CREATE INDEX idx_pages_url ON pages(page_url);
```

### 5. Recommendations
**Purpose**: Store optimization recommendations for pages and sites

#### DynamoDB Structure
```json
{
  "PK": "PROJECT#project_id",
  "SK": "RECOMMENDATION#recommendation_id",
  "GSI1PK": "PAGE#page_url",
  "GSI1SK": "RECOMMENDATION#recommendation_id",
  "GSI2PK": "CATEGORY#category",
  "GSI2SK": "RECOMMENDATION#recommendation_id",
  "recommendation_id": "uuid",
  "project_id": "uuid",
  "page_url": "https://inthebox.io/home",
  "category": "content_seo|technical_seo|performance|internal_linking|visual_ux|authority",
  "issue": "Page content is too thin with insufficient depth",
  "recommendation": "Expand content to provide comprehensive coverage...",
  "priority": "high|medium|low",
  "status": "pending|accepted|implemented|dismissed",
  "created_at": "2024-01-01T00:00:00Z",
  "implemented_at": null,
  "impact_score": 85,
  "guidelines": [
    "Aim for at least 1,500 words of quality content",
    "Include relevant keywords naturally",
    "Add supporting images, videos, or infographics"
  ]
}
```

#### SQLite Structure
```sql
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    page_url TEXT,
    category TEXT CHECK(category IN ('content_seo', 'technical_seo', 'performance', 'internal_linking', 'visual_ux', 'authority')),
    issue TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('pending', 'accepted', 'implemented', 'dismissed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    implemented_at TIMESTAMP,
    impact_score INTEGER CHECK(impact_score >= 0 AND impact_score <= 100),
    guidelines TEXT, -- JSON array
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_recommendations_project_id ON recommendations(project_id);
CREATE INDEX idx_recommendations_category ON recommendations(category);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority);
```

### 6. Alerts/Notifications
**Purpose**: Store system alerts and user notifications

#### DynamoDB Structure
```json
{
  "PK": "USER#user_id",
  "SK": "ALERT#alert_id",
  "GSI1PK": "PROJECT#project_id",
  "GSI1SK": "ALERT#alert_id",
  "alert_id": "uuid",
  "user_id": "uuid",
  "project_id": "uuid",
  "type": "low_site_health|high_priority_recommendation|crawl_complete",
  "title": "Low Site Health",
  "description": "art.ai has a site health of only 68%",
  "priority": "high|medium|low",
  "status": "active|dismissed|resolved",
  "created_at": "2024-01-01T00:00:00Z",
  "dismissed_at": null,
  "metadata": {
    "site_health_score": 68,
    "recommendations_count": 74
  }
}
```

#### SQLite Structure
```sql
CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    type TEXT CHECK(type IN ('low_site_health', 'high_priority_recommendation', 'crawl_complete')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('active', 'dismissed', 'resolved')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMP,
    metadata TEXT, -- JSON string
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_project_id ON alerts(project_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_priority ON alerts(priority);
```

### 7. Optimization History
**Purpose**: Track optimization actions and their results

#### DynamoDB Structure
```json
{
  "PK": "PROJECT#project_id",
  "SK": "OPTIMIZATION#optimization_id",
  "GSI1PK": "PAGE#page_url",
  "GSI1SK": "OPTIMIZATION#optimization_id",
  "optimization_id": "uuid",
  "project_id": "uuid",
  "page_url": "https://inthebox.io/home",
  "recommendation_id": "uuid",
  "action": "content_expanded|meta_updated|images_optimized",
  "before_score": 75,
  "after_score": 85,
  "implemented_at": "2024-01-01T00:00:00Z",
  "implemented_by": "user_id",
  "changes": {
    "word_count_before": 800,
    "word_count_after": 1500,
    "images_added": 3
  }
}
```

#### SQLite Structure
```sql
CREATE TABLE optimization_history (
    optimization_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    page_url TEXT,
    recommendation_id TEXT,
    action TEXT NOT NULL,
    before_score INTEGER,
    after_score INTEGER,
    implemented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    implemented_by TEXT,
    changes TEXT, -- JSON string
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id),
    FOREIGN KEY (implemented_by) REFERENCES users(user_id)
);

CREATE INDEX idx_optimization_history_project_id ON optimization_history(project_id);
CREATE INDEX idx_optimization_history_page_url ON optimization_history(page_url);
CREATE INDEX idx_optimization_history_implemented_at ON optimization_history(implemented_at);
```

## Indexes and Performance

### DynamoDB Global Secondary Indexes (GSI)
1. **GSI1**: Email-based user lookup
2. **GSI2**: Domain-based project lookup
3. **GSI3**: Status-based filtering
4. **GSI4**: Category-based recommendation filtering

### SQLite Indexes
- Primary keys on all tables
- Foreign key indexes for joins
- Status and priority indexes for filtering
- Timestamp indexes for time-based queries

## Data Access Patterns

### Common Queries
1. **User Dashboard**: Get user's projects with latest health scores
2. **Project Details**: Get project with all pages and recommendations
3. **Recommendations**: Get recommendations by category/priority
4. **Alerts**: Get active alerts for user
5. **Health History**: Get site health trends over time

### DynamoDB Query Patterns
```javascript
// Get user's projects
dynamodb.query({
  TableName: 'gambix-strata',
  KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
  ExpressionAttributeValues: {
    ':pk': 'USER#user_id',
    ':sk': 'PROJECT#'
  }
});

// Get project health metrics
dynamodb.query({
  TableName: 'gambix-strata',
  KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
  ExpressionAttributeValues: {
    ':pk': 'PROJECT#project_id',
    ':sk': 'HEALTH#'
  },
  ScanIndexForward: false,
  Limit: 1
});
```

### SQLite Query Patterns
```sql
-- Get user's projects with latest health
SELECT p.*, sh.overall_score, sh.timestamp as last_health_check
FROM projects p
LEFT JOIN (
    SELECT project_id, overall_score, timestamp,
           ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY timestamp DESC) as rn
    FROM site_health
) sh ON p.project_id = sh.project_id AND sh.rn = 1
WHERE p.user_id = ?;

-- Get recommendations by priority
SELECT * FROM recommendations 
WHERE project_id = ? AND status = 'pending'
ORDER BY 
    CASE priority 
        WHEN 'high' THEN 1 
        WHEN 'medium' THEN 2 
        WHEN 'low' THEN 3 
    END,
    impact_score DESC;
```

## Migration Strategy

### Development to Production
1. **SQLite → DynamoDB**: Use AWS DMS or custom migration scripts
2. **Data Validation**: Ensure data integrity during migration
3. **Rollback Plan**: Maintain SQLite backup during transition

### Schema Evolution
1. **DynamoDB**: Add new attributes without schema changes
2. **SQLite**: Use ALTER TABLE for new columns
3. **Versioning**: Track schema versions for compatibility

## Security Considerations

### DynamoDB
- IAM roles and policies
- Encryption at rest and in transit
- VPC endpoints for private access

### SQLite
- File-level encryption
- Access control through application layer
- Regular backups

## Backup and Recovery

### DynamoDB
- Point-in-time recovery
- On-demand backups
- Cross-region replication

### SQLite
- File-based backups
- Automated backup scripts
- Version control for schema changes
