import sqlite3
import json
import os
import uuid
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

class GambixStrataDatabase:
    """SQLite database manager for the Gambix Strata platform"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use data directory if it exists (Docker environment), otherwise use current directory
            if os.path.exists("/app/data"):
                self.db_path = "/app/data/gambix_strata.db"
            else:
                self.db_path = "gambix_strata.db"
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with the Gambix Strata schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create users table with password field
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    cognito_user_id TEXT UNIQUE, -- AWS Cognito UUID
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    given_name TEXT,
                    family_name TEXT,
                    password_hash TEXT,
                    role TEXT CHECK(role IN ('admin', 'user', 'viewer')) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    preferences TEXT -- JSON string
                )
            ''')
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
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
                    scraped_files_path TEXT, -- Path to scraped files directory
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, domain)
                )
            ''')
            
            # Create site_health table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_health (
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
                )
            ''')
            
            # Create pages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pages (
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
                )
            ''')
            
            # Create recommendations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    issue TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    guidelines TEXT, -- JSON array
                    status TEXT CHECK(status IN ('pending', 'accepted', 'dismissed')) DEFAULT 'pending',
                    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
                    impact_score INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    alert_type TEXT CHECK(alert_type IN ('info', 'warning', 'error', 'success')) DEFAULT 'info',
                    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
                    status TEXT CHECK(status IN ('active', 'dismissed')) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dismissed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Create optimizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimizations (
                    optimization_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    optimization_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    changes_made TEXT, -- JSON string
                    performance_impact TEXT, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            ''')
            
            # Create indexes for better performance
            self._create_indexes(cursor)
            
            # Add missing columns to existing tables
            self._migrate_schema(cursor)
            
            # Migrate user data to new schema
            self._migrate_user_data(cursor)
            
            conn.commit()
    
    def _create_indexes(self, cursor):
        """Create all necessary indexes for performance"""
        indexes = [
            # Users indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            
            # Projects indexes
            "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_domain ON projects(domain)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            
            # Site health indexes
            "CREATE INDEX IF NOT EXISTS idx_site_health_project_id ON site_health(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_site_health_timestamp ON site_health(timestamp)",
            
            # Pages indexes
            "CREATE INDEX IF NOT EXISTS idx_pages_project_id ON pages(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_pages_status ON pages(status)",
            "CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(page_url)",
            
            # Recommendations indexes
            "CREATE INDEX IF NOT EXISTS idx_recommendations_project_id ON recommendations(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_recommendations_category ON recommendations(category)",
            "CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status)",
            "CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON recommendations(priority)",
            
            # Alerts indexes
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority)",
            
            # Optimization history indexes
            "CREATE INDEX IF NOT EXISTS idx_optimization_history_project_id ON optimizations(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_optimization_history_page_url ON optimizations(optimization_type)",
            "CREATE INDEX IF NOT EXISTS idx_optimization_history_implemented_at ON optimizations(created_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def _migrate_schema(self, cursor):
        """Migrate existing database schema to add missing columns"""
        try:
            # Add impact_score column to recommendations table if it doesn't exist
            cursor.execute("PRAGMA table_info(recommendations)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'impact_score' not in columns:
                cursor.execute("ALTER TABLE recommendations ADD COLUMN impact_score INTEGER DEFAULT 50")
                print("Added impact_score column to recommendations table")
            
            # Add scraped_files_path column to projects table if it doesn't exist
            cursor.execute("PRAGMA table_info(projects)")
            project_columns = [column[1] for column in cursor.fetchall()]
            if 'scraped_files_path' not in project_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN scraped_files_path TEXT")
                print("Added scraped_files_path column to projects table")
            
            # Only run domain normalization and duplicate removal if there are existing projects
            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            
            if project_count > 0:
                # Normalize existing domains by removing protocol and www
                cursor.execute("SELECT project_id, domain FROM projects")
                projects = cursor.fetchall()
                
                for project_id, old_domain in projects:
                    # Normalize domain
                    from urllib.parse import urlparse
                    parsed = urlparse(old_domain)
                    new_domain = parsed.netloc.replace('www.', '') if parsed.netloc else old_domain
                    
                    if new_domain != old_domain:
                        cursor.execute("UPDATE projects SET domain = ? WHERE project_id = ?", (new_domain, project_id))
                        print(f"Normalized domain: {old_domain} -> {new_domain}")
                
                # Handle duplicate projects by keeping only the most recent one per user/domain
                try:
                    cursor.execute("""
                        DELETE FROM projects 
                        WHERE project_id NOT IN (
                            SELECT MAX(project_id) 
                            FROM projects 
                            GROUP BY user_id, domain
                        )
                    """)
                    print("Removed duplicate projects, keeping most recent ones")
                except Exception as e:
                    print(f"Warning: Could not remove duplicates: {e}")
            else:
                print("No existing projects found, skipping domain normalization and duplicate removal")
            
            # Add unique constraint if it doesn't exist
            try:
                cursor.execute("PRAGMA index_list(projects)")
                indexes = [index[1] for index in cursor.fetchall()]
                if 'idx_projects_user_domain_unique' not in indexes:
                    cursor.execute("CREATE UNIQUE INDEX idx_projects_user_domain_unique ON projects(user_id, domain)")
                    print("Added unique constraint on user_id and domain")
            except Exception as e:
                print(f"Warning: Could not add unique constraint: {e}")
                
        except Exception as e:
            print(f"Migration error: {e}")
    
    def _migrate_user_data(self, cursor):
        """Migrate existing user data to new schema with real user information"""
        try:
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # If new columns don't exist, add them
            if 'cognito_user_id' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN cognito_user_id TEXT UNIQUE")
                print("Added cognito_user_id column to users table")
            
            if 'given_name' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN given_name TEXT")
                print("Added given_name column to users table")
            
            if 'family_name' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN family_name TEXT")
                print("Added family_name column to users table")
            
            # Check for users with UUID-like emails (likely Cognito UUIDs)
            cursor.execute("""
                SELECT user_id, email, name 
                FROM users 
                WHERE email LIKE '%-%-%-%-%' 
                AND email NOT LIKE '%@%'
            """)
            cognito_users = cursor.fetchall()
            
            if cognito_users:
                print(f"Found {len(cognito_users)} users with Cognito UUIDs as emails")
                print("These users will need to be updated with real information from Cognito tokens")
                
                for user_id, email, name in cognito_users:
                    print(f"  User ID: {user_id}")
                    print(f"  Current email (Cognito UUID): {email}")
                    print(f"  Current name: {name}")
                    print("  → This user needs to be updated with real email/name from Cognito")
            
        except Exception as e:
            print(f"User data migration error: {e}")
    
    def _generate_id(self) -> str:
        """Generate a UUID for primary keys"""
        return str(uuid.uuid4())
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string"""
        if data is None:
            return None
        return json.dumps(data)
    
    def _deserialize_json(self, json_str: str) -> Any:
        """Deserialize JSON string to data"""
        if json_str is None:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
    
    # User Management
    def create_user(self, email: str, name: str, password: str = None, role: str = 'user', 
                   cognito_user_id: str = None, given_name: str = None, family_name: str = None, 
                   preferences: Dict = None) -> str:
        """Create a new user"""
        user_id = self._generate_id()
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, cognito_user_id, email, name, given_name, family_name, 
                                 password_hash, role, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, cognito_user_id, email, name, given_name, family_name, 
                  password_hash, role, self._serialize_json(preferences)))
            conn.commit()
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                user_data = dict(zip(columns, row))
                user_data['preferences'] = self._deserialize_json(user_data['preferences'])
                return user_data
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                user_data = dict(zip(columns, row))
                user_data['preferences'] = self._deserialize_json(user_data['preferences'])
                return user_data
        return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if user and user.get('password_hash'):
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update last login
                self.update_user_login(user['user_id'])
                # Remove password hash from response
                user.pop('password_hash', None)
                return user
        return None

    def update_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update user profile information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                update_fields = []
                params = []
                
                if 'name' in profile_data:
                    update_fields.append('name = ?')
                    params.append(profile_data['name'])
                
                if 'preferences' in profile_data:
                    update_fields.append('preferences = ?')
                    params.append(self._serialize_json(profile_data['preferences']))
                
                if update_fields:
                    update_fields.append('updated_at = CURRENT_TIMESTAMP')
                    params.append(user_id)
                    
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                    return True
            return False
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def update_user_login(self, user_id: str):
        """Update user's last login time"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    # Project Management
    def create_project(self, user_id: str, domain: str, name: str, settings: Dict = None) -> str:
        """Create a new project or return existing project for same domain"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if project already exists for this user and domain
            cursor.execute('''
                SELECT project_id FROM projects 
                WHERE user_id = ? AND domain = ?
            ''', (user_id, domain))
            
            existing_project = cursor.fetchone()
            
            if existing_project:
                # Project already exists, return existing project ID
                project_id = existing_project[0]
                
                # Update the existing project with new settings if provided
                if settings:
                    cursor.execute('''
                        UPDATE projects 
                        SET name = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ?
                    ''', (name, self._serialize_json(settings), project_id))
                    conn.commit()
                
                return project_id
            else:
                # Create new project
                project_id = self._generate_id()
                try:
                    cursor.execute('''
                        INSERT INTO projects (project_id, user_id, domain, name, settings)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (project_id, user_id, domain, name, self._serialize_json(settings)))
                    conn.commit()
                    return project_id
                except sqlite3.IntegrityError:
                    # If we get here, it means another process created the project between our check and insert
                    # Get the existing project ID
                    cursor.execute('''
                        SELECT project_id FROM projects 
                        WHERE user_id = ? AND domain = ?
                    ''', (user_id, domain))
                    existing = cursor.fetchone()
                    if existing:
                        return existing[0]
                    else:
                        raise Exception("Failed to create project due to constraint violation")
    
    def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get all projects for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, sh.overall_score, sh.timestamp as last_health_check
                FROM projects p
                LEFT JOIN (
                    SELECT project_id, overall_score, timestamp,
                           ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY timestamp DESC) as rn
                    FROM site_health
                ) sh ON p.project_id = sh.project_id AND sh.rn = 1
                WHERE p.user_id = ?
                ORDER BY p.updated_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            projects = []
            for row in rows:
                project_data = dict(zip(columns, row))
                project_data['settings'] = self._deserialize_json(project_data['settings'])
                projects.append(project_data)
            return projects
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                project_data = dict(zip(columns, row))
                project_data['settings'] = self._deserialize_json(project_data['settings'])
                return project_data
        return None
    
    def get_project_by_user_and_domain(self, user_id: str, domain: str) -> Optional[Dict]:
        """Get project by user ID and domain (with domain normalization)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Normalize the input domain
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            normalized_domain = parsed.netloc.replace('www.', '') if parsed.netloc else domain
            
            # Get all projects for this user
            cursor.execute('SELECT * FROM projects WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                columns = [description[0] for description in cursor.description]
                project_data = dict(zip(columns, row))
                
                # Normalize the stored domain
                stored_domain = project_data['domain']
                parsed_stored = urlparse(stored_domain)
                normalized_stored = parsed_stored.netloc.replace('www.', '') if parsed_stored.netloc else stored_domain
                
                # Compare normalized domains
                if normalized_domain == normalized_stored:
                    project_data['settings'] = self._deserialize_json(project_data['settings'])
                    return project_data
            
        return None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its associated data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete associated data first (due to foreign key constraints)
                # Delete site health data
                cursor.execute('DELETE FROM site_health WHERE project_id = ?', (project_id,))
                
                # Delete pages
                cursor.execute('DELETE FROM pages WHERE project_id = ?', (project_id,))
                
                # Delete recommendations
                cursor.execute('DELETE FROM recommendations WHERE project_id = ?', (project_id,))
                
                # Delete optimizations
                cursor.execute('DELETE FROM optimizations WHERE project_id = ?', (project_id,))
                
                # Note: alerts table uses user_id, not project_id, so we don't delete alerts
                # They are user-specific, not project-specific
                
                # Finally delete the project
                cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting project {project_id}: {e}")
            return False
    
    def update_project_status(self, project_id: str, status: str):
        """Update project status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            ''', (status, project_id))
            conn.commit()
    
    def update_project_scraped_files(self, project_id: str, scraped_files_path: str):
        """Update project with scraped files path"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET scraped_files_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            ''', (scraped_files_path, project_id))
            conn.commit()
    
    def update_project_last_crawl(self, project_id: str):
        """Update project last crawl timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET last_crawl = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            ''', (project_id,))
            conn.commit()
    
    # Site Health Management
    def add_site_health(self, project_id: str, health_data: Dict) -> str:
        """Add site health metrics"""
        health_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO site_health (
                    health_id, project_id, overall_score, technical_seo, content_seo,
                    performance, internal_linking, visual_ux, authority_backlinks,
                    total_impressions, total_engagements, total_conversions, crawl_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                health_id, project_id,
                health_data.get('overall_score'),
                health_data.get('technical_seo'),
                health_data.get('content_seo'),
                health_data.get('performance'),
                health_data.get('internal_linking'),
                health_data.get('visual_ux'),
                health_data.get('authority_backlinks'),
                health_data.get('total_impressions', 0),
                health_data.get('total_engagements', 0),
                health_data.get('total_conversions', 0),
                self._serialize_json(health_data.get('crawl_data'))
            ))
            conn.commit()
        return health_id
    
    def get_latest_site_health(self, project_id: str) -> Optional[Dict]:
        """Get the latest site health for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM site_health 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (project_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                health_data = dict(zip(columns, row))
                health_data['crawl_data'] = self._deserialize_json(health_data['crawl_data'])
                return health_data
        return None
    
    def get_site_health_history(self, project_id: str, limit: int = 30) -> List[Dict]:
        """Get site health history for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM site_health 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (project_id, limit))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            history = []
            for row in rows:
                health_data = dict(zip(columns, row))
                health_data['crawl_data'] = self._deserialize_json(health_data['crawl_data'])
                history.append(health_data)
            return history
    
    # Page Management
    def add_page(self, project_id: str, page_data: Dict) -> str:
        """Add a page to a project"""
        page_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pages (
                    page_id, project_id, page_url, title, status, last_crawled,
                    word_count, load_time, meta_description, h1_tags, images_count, links_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page_id, project_id,
                page_data.get('page_url'),
                page_data.get('title'),
                page_data.get('status', 'healthy'),
                page_data.get('last_crawled'),
                page_data.get('word_count', 0),
                page_data.get('load_time'),
                page_data.get('meta_description'),
                self._serialize_json(page_data.get('h1_tags')),
                page_data.get('images_count', 0),
                page_data.get('links_count', 0)
            ))
            conn.commit()
        return page_id
    
    def get_project_pages(self, project_id: str) -> List[Dict]:
        """Get all pages for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pages 
                WHERE project_id = ? 
                ORDER BY last_crawled DESC
            ''', (project_id,))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            pages = []
            for row in rows:
                page_data = dict(zip(columns, row))
                page_data['h1_tags'] = self._deserialize_json(page_data['h1_tags'])
                pages.append(page_data)
            return pages
    
    # Recommendations Management
    def add_recommendation(self, project_id: str, recommendation_data: Dict) -> str:
        """Add a recommendation"""
        recommendation_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recommendations (
                    recommendation_id, project_id, category, issue,
                    recommendation, guidelines, priority, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation_id, project_id,
                recommendation_data.get('category'),
                recommendation_data.get('issue'),
                recommendation_data.get('recommendation'),
                self._serialize_json(recommendation_data.get('guidelines')),
                recommendation_data.get('priority', 'medium'),
                recommendation_data.get('status', 'pending')
            ))
            conn.commit()
        return recommendation_id
    
    def get_project_recommendations(self, project_id: str, status: str = 'pending') -> List[Dict]:
        """Get recommendations for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM recommendations 
                WHERE project_id = ? AND status = ?
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    impact_score DESC
            ''', (project_id, status))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            recommendations = []
            for row in rows:
                rec_data = dict(zip(columns, row))
                rec_data['guidelines'] = self._deserialize_json(rec_data['guidelines'])
                recommendations.append(rec_data)
            return recommendations
    
    def update_recommendation_status(self, recommendation_id: str, status: str):
        """Update recommendation status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status == 'implemented':
                cursor.execute('''
                    UPDATE recommendations 
                    SET status = ?, implemented_at = CURRENT_TIMESTAMP
                    WHERE recommendation_id = ?
                ''', (status, recommendation_id))
            else:
                cursor.execute('''
                    UPDATE recommendations 
                    SET status = ?
                    WHERE recommendation_id = ?
                ''', (status, recommendation_id))
            conn.commit()
    
    # Alerts Management
    def create_alert(self, user_id: str, alert_data: Dict) -> str:
        """Create a new alert"""
        alert_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (
                    alert_id, user_id, title, description, alert_type, priority, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id, user_id,
                alert_data.get('title'),
                alert_data.get('description'),
                alert_data.get('alert_type', 'info'),
                alert_data.get('priority', 'medium'),
                alert_data.get('status', 'active')
            ))
            conn.commit()
        return alert_id
    
    def get_user_alerts(self, user_id: str, status: str = 'active') -> List[Dict]:
        """Get alerts for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM alerts 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            ''', (user_id, status))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            alerts = []
            for row in rows:
                alert_data = dict(zip(columns, row))
                alerts.append(alert_data)
            return alerts
    
    def dismiss_alert(self, alert_id: str):
        """Dismiss an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET status = 'dismissed', dismissed_at = CURRENT_TIMESTAMP
                WHERE alert_id = ?
            ''', (alert_id,))
            conn.commit()
    
    # Optimization History
    def add_optimization(self, project_id: str, optimization_data: Dict) -> str:
        """Add optimization history entry"""
        optimization_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO optimizations (
                    optimization_id, project_id, optimization_type, description,
                    changes_made, performance_impact
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                optimization_id, project_id,
                optimization_data.get('optimization_type'),
                optimization_data.get('description'),
                self._serialize_json(optimization_data.get('changes_made')),
                self._serialize_json(optimization_data.get('performance_impact'))
            ))
            conn.commit()
        return optimization_id
    
    def get_optimization_history(self, project_id: str, limit: int = 50) -> List[Dict]:
        """Get optimization history for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM optimizations 
                WHERE project_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (project_id, limit))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            history = []
            for row in rows:
                opt_data = dict(zip(columns, row))
                opt_data['changes_made'] = self._deserialize_json(opt_data['changes_made'])
                opt_data['performance_impact'] = self._deserialize_json(opt_data['performance_impact'])
                history.append(opt_data)
            return history
    
    # Statistics and Analytics
    def get_project_statistics(self, project_id: str) -> Dict:
        """Get comprehensive statistics for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get basic project info
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            project_row = cursor.fetchone()
            if not project_row:
                return None
            
            # Get page counts by status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM pages 
                WHERE project_id = ? 
                GROUP BY status
            ''', (project_id,))
            page_stats = dict(cursor.fetchall())
            
            # Get recommendation counts by priority
            cursor.execute('''
                SELECT priority, COUNT(*) as count 
                FROM recommendations 
                WHERE project_id = ? AND status = 'pending'
                GROUP BY priority
            ''', (project_id,))
            rec_stats = dict(cursor.fetchall())
            
            # Get latest health score
            cursor.execute('''
                SELECT overall_score, timestamp 
                FROM site_health 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (project_id,))
            health_row = cursor.fetchone()
            
            return {
                'project_id': project_id,
                'pages': {
                    'total': sum(page_stats.values()),
                    'healthy': page_stats.get('healthy', 0),
                    'broken': page_stats.get('broken', 0),
                    'has_issues': page_stats.get('has_issues', 0)
                },
                'recommendations': {
                    'high_priority': rec_stats.get('high', 0),
                    'medium_priority': rec_stats.get('medium', 0),
                    'low_priority': rec_stats.get('low', 0)
                },
                'health_score': health_row[0] if health_row else None,
                'last_health_check': health_row[1] if health_row else None
            }
    
    def get_dashboard_data(self, user_id: str) -> Dict:
        """Get dashboard data for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get user's projects with latest health scores
            projects = self.get_user_projects(user_id)
            
            # Get active alerts count
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE user_id = ? AND status = 'active'
            ''', (user_id,))
            active_alerts = cursor.fetchone()[0]
            
            # Get total recommendations across all projects
            cursor.execute('''
                SELECT COUNT(*) FROM recommendations r
                JOIN projects p ON r.project_id = p.project_id
                WHERE p.user_id = ? AND r.status = 'pending'
            ''', (user_id,))
            total_recommendations = cursor.fetchone()[0]
            
            return {
                'projects': projects,
                'active_alerts': active_alerts,
                'total_recommendations': total_recommendations,
                'total_projects': len(projects)
            }

    def add_recommendations_from_scrape(self, project_id: str, scraped_data: Dict) -> List[str]:
        """Add recommendations based on scraped data analysis"""
        recommendations = []
        
        # Analyze scraped data and create recommendations
        seo_data = scraped_data.get('seo_metadata', {})
        
        # Check for missing meta description
        if not seo_data.get('meta_description'):
            rec_id = self.add_recommendation(project_id, {
                'category': 'SEO',
                'issue': 'Missing Meta Description',
                'recommendation': 'Add a meta description to improve search engine visibility',
                'priority': 'high',
                'impact_score': 85
            })
            recommendations.append(rec_id)
        
        # Check for missing title
        if not scraped_data.get('title'):
            rec_id = self.add_recommendation(project_id, {
                'category': 'SEO',
                'issue': 'Missing Page Title',
                'recommendation': 'Add a descriptive page title for better SEO',
                'priority': 'high',
                'impact_score': 90
            })
            recommendations.append(rec_id)
        
        # Check for images without alt text
        images = seo_data.get('images', [])
        images_without_alt = sum(1 for img in images if not img.get('alt'))
        if images_without_alt > 0:
            rec_id = self.add_recommendation(project_id, {
                'category': 'Accessibility',
                'issue': f'{images_without_alt} Images Missing Alt Text',
                'recommendation': 'Add alt text to all images for better accessibility and SEO',
                'priority': 'medium',
                'impact_score': 70
            })
            recommendations.append(rec_id)
        
        # Check for low word count
        word_count = seo_data.get('word_count', 0)
        if word_count < 300:
            rec_id = self.add_recommendation(project_id, {
                'category': 'Content',
                'issue': 'Low Word Count',
                'recommendation': f'Increase content length. Current: {word_count} words. Aim for 300+ words.',
                'priority': 'medium',
                'impact_score': 75
            })
            recommendations.append(rec_id)
        
        return recommendations

# Legacy compatibility functions
def add_scraped_site(url: str, scraped_data: Dict[str, Any], saved_directory: str, user_email: Optional[str] = None) -> bool:
    """Legacy function for backward compatibility"""
    db = GambixStrataDatabase()
    
    # Create user if email provided
    user_id = None
    if user_email:
        user = db.get_user_by_email(user_email)
        if not user:
            user_id = db.create_user(user_email, f"User {user_email}", 'user')
        else:
            user_id = user['user_id']
    
    # Extract domain from URL
    domain = urlparse(url).netloc
    
    # Create project if it doesn't exist
    projects = db.get_user_projects(user_id) if user_id else []
    project = next((p for p in projects if p['domain'] == domain), None)
    
    if not project and user_id:
        project_id = db.create_project(user_id, domain, f"{domain} Website")
    elif project:
        project_id = project['project_id']
    else:
        return False
    
    # Add page data
    page_data = {
        'page_url': url,
        'title': scraped_data.get('title', ''),
        'word_count': scraped_data.get('word_count', 0),
        'meta_description': scraped_data.get('meta_description', ''),
        'h1_tags': scraped_data.get('h1_tags', []),
        'images_count': scraped_data.get('images_count', 0),
        'links_count': scraped_data.get('links_count', 0),
        'status': 'healthy'
    }
    
    db.add_page(project_id, page_data)
    return True

    def add_recommendation(self, project_id: str, recommendation_data: Dict) -> str:
        """Add a single recommendation"""
        recommendation_id = self._generate_id()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recommendations (
                    recommendation_id, project_id, category, issue, recommendation,
                    priority, impact_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation_id, project_id,
                recommendation_data.get('category'),
                recommendation_data.get('issue'),
                recommendation_data.get('recommendation'),
                recommendation_data.get('priority', 'medium'),
                recommendation_data.get('impact_score', 50),
                'pending'
            ))
            conn.commit()
        return recommendation_id

def add_optimized_site(url: str, user_profile: str, optimized_directory: str) -> bool:
    """Legacy function for backward compatibility"""
    db = GambixStrataDatabase()
    
    # This would need to be implemented based on your optimization logic
    # For now, just return True
    return True

def get_site_stats() -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    db = GambixStrataDatabase()
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Get total projects
        cursor.execute('SELECT COUNT(*) FROM projects')
        total_projects = cursor.fetchone()[0]
        
        # Get total pages
        cursor.execute('SELECT COUNT(*) FROM pages')
        total_pages = cursor.fetchone()[0]
        
        # Get total recommendations
        cursor.execute('SELECT COUNT(*) FROM recommendations')
        total_recommendations = cursor.fetchone()[0]
        
        return {
            'total_projects': total_projects,
            'total_pages': total_pages,
            'total_recommendations': total_recommendations,
            'database_type': 'Gambix Strata SQLite'
        }

def export_summary() -> str:
    """Legacy function for backward compatibility"""
    stats = get_site_stats()
    return f"""
Gambix Strata Database Summary
=============================
Total Projects: {stats['total_projects']}
Total Pages: {stats['total_pages']}
Total Recommendations: {stats['total_recommendations']}
Database Type: {stats['database_type']}
"""

def get_sites_by_user_email(user_email: str) -> List[Dict]:
    """Legacy function for backward compatibility"""
    db = GambixStrataDatabase()
    user = db.get_user_by_email(user_email)
    if user:
        return db.get_user_projects(user['user_id'])
    return []

def get_all_sites() -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    db = GambixStrataDatabase()
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.email as user_email
            FROM projects p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC
        ''')
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        sites = []
        for row in rows:
            site_data = dict(zip(columns, row))
            site_data['settings'] = db._deserialize_json(site_data['settings'])
            sites.append(site_data)
        
        return {
            'sites': sites,
            'total': len(sites)
        }

# Initialize database instance - commented out to avoid startup errors
# db = GambixStrataDatabase()
