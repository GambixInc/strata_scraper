import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

class Database:
    """SQLite database manager for the web scraper project"""
    
    def __init__(self, db_path: str = "scraper_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    first_scraped TEXT NOT NULL,
                    last_scraped TEXT,
                    last_optimized TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create scrapes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    scraped_at TEXT NOT NULL,
                    saved_directory TEXT,
                    user_email TEXT,
                    links_count INTEGER DEFAULT 0,
                    inline_styles_count INTEGER DEFAULT 0,
                    internal_stylesheets_count INTEGER DEFAULT 0,
                    external_stylesheets_count INTEGER DEFAULT 0,
                    inline_scripts_count INTEGER DEFAULT 0,
                    external_scripts_count INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    content_size_mb REAL DEFAULT 0,
                    FOREIGN KEY (site_id) REFERENCES sites (id)
                )
            ''')
            
            # Create optimizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER NOT NULL,
                    original_url TEXT NOT NULL,
                    user_profile TEXT NOT NULL,
                    optimized_at TEXT NOT NULL,
                    optimized_directory TEXT,
                    optimization_type TEXT DEFAULT 'general_enhancement',
                    FOREIGN KEY (site_id) REFERENCES sites (id)
                )
            ''')
            
            # Create seo_metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seo_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scrape_id INTEGER NOT NULL,
                    meta_tags TEXT,  -- JSON
                    open_graph TEXT,  -- JSON
                    twitter_cards TEXT,  -- JSON
                    structured_data TEXT,  -- JSON
                    headings TEXT,  -- JSON
                    images TEXT,  -- JSON
                    internal_links TEXT,  -- JSON
                    external_links TEXT,  -- JSON
                    social_links TEXT,  -- JSON
                    canonical_url TEXT,
                    robots_directive TEXT,
                    language TEXT,
                    charset TEXT,
                    viewport TEXT,
                    favicon TEXT,
                    sitemap TEXT,
                    rss_feeds TEXT,  -- JSON
                    analytics TEXT,  -- JSON
                    word_count INTEGER DEFAULT 0,
                    keyword_density TEXT,  -- JSON
                    page_speed_indicators TEXT,  -- JSON
                    detailed_analytics TEXT,  -- JSON
                    FOREIGN KEY (scrape_id) REFERENCES scrapes (id)
                )
            ''')
            
            # Create analytics_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scrape_id INTEGER NOT NULL,
                    google_analytics TEXT,  -- JSON
                    facebook_pixel TEXT,  -- JSON
                    google_tag_manager TEXT,  -- JSON
                    hotjar TEXT,  -- JSON
                    mixpanel TEXT,  -- JSON
                    other_tracking TEXT,  -- JSON
                    social_media_tracking TEXT,  -- JSON
                    analytics_summary TEXT,  -- JSON
                    tracking_intensity TEXT,
                    FOREIGN KEY (scrape_id) REFERENCES scrapes (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sites_domain ON sites (domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapes_site_id ON scrapes (site_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapes_user_email ON scrapes (user_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapes_scraped_at ON scrapes (scraped_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_optimizations_site_id ON optimizations (site_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_seo_metadata_scrape_id ON seo_metadata (scrape_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_data_scrape_id ON analytics_data (scrape_id)')
            
            conn.commit()
    
    def _get_site_key(self, url: str) -> str:
        """Generate a unique key for a site based on its domain"""
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    
    def add_scraped_site(self, url: str, scraped_data: Dict[str, Any], saved_directory: str, user_email: Optional[str] = None) -> bool:
        """Add a newly scraped site to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                site_key = self._get_site_key(url)
                now = datetime.now().isoformat()
                
                # Check if site exists, create if not
                cursor.execute('SELECT id FROM sites WHERE domain = ?', (site_key,))
                site_result = cursor.fetchone()
                
                if site_result:
                    site_id = site_result[0]
                    # Update last_scraped
                    cursor.execute('UPDATE sites SET last_scraped = ?, updated_at = ? WHERE id = ?', 
                                 (now, now, site_id))
                else:
                    # Create new site
                    cursor.execute('''
                        INSERT INTO sites (domain, first_scraped, last_scraped, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (site_key, now, now, now, now))
                    site_id = cursor.lastrowid
                
                # Add scrape record
                seo_data = scraped_data.get('seo_metadata', {})
                stats = {
                    'links_count': len(scraped_data.get('links', [])),
                    'inline_styles_count': len(scraped_data.get('css_content', {}).get('inline_styles', [])),
                    'internal_stylesheets_count': len(scraped_data.get('css_content', {}).get('internal_stylesheets', [])),
                    'external_stylesheets_count': len(scraped_data.get('css_content', {}).get('external_stylesheets', [])),
                    'inline_scripts_count': len(scraped_data.get('js_content', {}).get('inline_scripts', [])),
                    'external_scripts_count': len(scraped_data.get('js_content', {}).get('external_scripts', []))
                }
                
                cursor.execute('''
                    INSERT INTO scrapes (
                        site_id, url, title, scraped_at, saved_directory, user_email,
                        links_count, inline_styles_count, internal_stylesheets_count,
                        external_stylesheets_count, inline_scripts_count, external_scripts_count,
                        word_count, content_size_mb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    site_id, url, scraped_data.get('title', 'Unknown'), now, saved_directory, user_email,
                    stats['links_count'], stats['inline_styles_count'], stats['internal_stylesheets_count'],
                    stats['external_stylesheets_count'], stats['inline_scripts_count'], stats['external_scripts_count'],
                    seo_data.get('word_count', 0), len(scraped_data.get('html_content', '').encode('utf-8')) / (1024 * 1024)
                ))
                
                scrape_id = cursor.lastrowid
                
                # Add SEO metadata
                if seo_data:
                    cursor.execute('''
                        INSERT INTO seo_metadata (
                            scrape_id, meta_tags, open_graph, twitter_cards, structured_data,
                            headings, images, internal_links, external_links, social_links,
                            canonical_url, robots_directive, language, charset, viewport,
                            favicon, sitemap, rss_feeds, analytics, word_count,
                            keyword_density, page_speed_indicators, detailed_analytics
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scrape_id,
                        json.dumps(seo_data.get('meta_tags', {})),
                        json.dumps(seo_data.get('open_graph', {})),
                        json.dumps(seo_data.get('twitter_cards', {})),
                        json.dumps(seo_data.get('structured_data', [])),
                        json.dumps(seo_data.get('headings', {})),
                        json.dumps(seo_data.get('images', [])),
                        json.dumps(seo_data.get('internal_links', [])),
                        json.dumps(seo_data.get('external_links', [])),
                        json.dumps(seo_data.get('social_links', [])),
                        seo_data.get('canonical_url'),
                        seo_data.get('robots_directive'),
                        seo_data.get('language'),
                        seo_data.get('charset'),
                        seo_data.get('viewport'),
                        seo_data.get('favicon'),
                        seo_data.get('sitemap'),
                        json.dumps(seo_data.get('rss_feeds', [])),
                        json.dumps(seo_data.get('analytics', [])),
                        seo_data.get('word_count', 0),
                        json.dumps(seo_data.get('keyword_density', {})),
                        json.dumps(seo_data.get('page_speed_indicators', {})),
                        json.dumps(seo_data.get('detailed_analytics', {}))
                    ))
                
                # Add analytics data
                analytics_data = seo_data.get('detailed_analytics', {})
                if analytics_data:
                    cursor.execute('''
                        INSERT INTO analytics_data (
                            scrape_id, google_analytics, facebook_pixel, google_tag_manager,
                            hotjar, mixpanel, other_tracking, social_media_tracking,
                            analytics_summary, tracking_intensity
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scrape_id,
                        json.dumps(analytics_data.get('google_analytics', [])),
                        json.dumps(analytics_data.get('facebook_pixel', [])),
                        json.dumps(analytics_data.get('google_tag_manager', [])),
                        json.dumps(analytics_data.get('hotjar', [])),
                        json.dumps(analytics_data.get('mixpanel', [])),
                        json.dumps(analytics_data.get('other_tracking', [])),
                        json.dumps(analytics_data.get('social_media_tracking', [])),
                        json.dumps(analytics_data.get('analytics_summary', {})),
                        analytics_data.get('analytics_summary', {}).get('tracking_intensity', 'Unknown')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding scraped site to database: {e}")
            return False
    
    def add_optimized_site(self, url: str, user_profile: str, optimized_directory: str) -> bool:
        """Add an optimized version to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                site_key = self._get_site_key(url)
                now = datetime.now().isoformat()
                
                # Get site ID
                cursor.execute('SELECT id FROM sites WHERE domain = ?', (site_key,))
                site_result = cursor.fetchone()
                
                if not site_result:
                    # Create site if it doesn't exist
                    cursor.execute('''
                        INSERT INTO sites (domain, first_scraped, last_optimized, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (site_key, now, now, now, now))
                    site_id = cursor.lastrowid
                else:
                    site_id = site_result[0]
                    # Update last_optimized
                    cursor.execute('UPDATE sites SET last_optimized = ?, updated_at = ? WHERE id = ?', 
                                 (now, now, site_id))
                
                # Add optimization record
                cursor.execute('''
                    INSERT INTO optimizations (
                        site_id, original_url, user_profile, optimized_at, optimized_directory
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (site_id, url, user_profile, now, optimized_directory))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding optimized site to database: {e}")
            return False
    
    def is_site_scraped(self, url: str) -> bool:
        """Check if a site has been scraped before"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                site_key = self._get_site_key(url)
                cursor.execute('SELECT COUNT(*) FROM scrapes s JOIN sites st ON s.site_id = st.id WHERE st.domain = ?', (site_key,))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"Error checking if site is scraped: {e}")
            return False
    
    def get_site_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific site"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                site_key = self._get_site_key(url)
                
                cursor.execute('''
                    SELECT s.*, 
                           COUNT(sc.id) as scrapes_count,
                           COUNT(op.id) as optimizations_count
                    FROM sites s
                    LEFT JOIN scrapes sc ON s.id = sc.site_id
                    LEFT JOIN optimizations op ON s.id = op.site_id
                    WHERE s.domain = ?
                    GROUP BY s.id
                ''', (site_key,))
                
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    site_data = dict(zip(columns, result))
                    
                    # Get latest scrape
                    cursor.execute('''
                        SELECT * FROM scrapes 
                        WHERE site_id = ? 
                        ORDER BY scraped_at DESC 
                        LIMIT 1
                    ''', (site_data['id'],))
                    
                    latest_scrape = cursor.fetchone()
                    if latest_scrape:
                        scrape_columns = [desc[0] for desc in cursor.description]
                        site_data['latest_scrape'] = dict(zip(scrape_columns, latest_scrape))
                    
                    return site_data
                return None
                
        except Exception as e:
            print(f"Error getting site info: {e}")
            return None
    
    def get_all_sites(self) -> Dict[str, Any]:
        """Get information about all tracked sites"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT s.*, 
                           COUNT(sc.id) as scrapes_count,
                           COUNT(op.id) as optimizations_count
                    FROM sites s
                    LEFT JOIN scrapes sc ON s.id = sc.site_id
                    LEFT JOIN optimizations op ON s.id = op.site_id
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC
                ''')
                
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                sites = {}
                for result in results:
                    site_data = dict(zip(columns, result))
                    sites[site_data['domain']] = site_data
                
                return sites
                
        except Exception as e:
            print(f"Error getting all sites: {e}")
            return {}
    
    def get_site_stats(self) -> Dict[str, Any]:
        """Get overall statistics about tracked sites"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic stats
                cursor.execute('SELECT COUNT(*) FROM sites')
                total_sites = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM scrapes')
                total_scrapes = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM optimizations')
                total_optimizations = cursor.fetchone()[0]
                
                # Get recent activities
                cursor.execute('''
                    SELECT 'scrape' as type, s.domain, sc.scraped_at as timestamp, sc.url
                    FROM scrapes sc
                    JOIN sites s ON sc.site_id = s.id
                    UNION ALL
                    SELECT 'optimization' as type, s.domain, op.optimized_at as timestamp, op.original_url as url
                    FROM optimizations op
                    JOIN sites s ON op.site_id = s.id
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')
                
                recent_activities = []
                for row in cursor.fetchall():
                    recent_activities.append({
                        'type': row[0],
                        'site': row[1],
                        'timestamp': row[2],
                        'url': row[3]
                    })
                
                return {
                    'total_sites': total_sites,
                    'total_scrapes': total_scrapes,
                    'total_optimizations': total_optimizations,
                    'recent_activities': recent_activities,
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat(),
                        'version': '2.0',
                        'total_sites_scraped': total_sites,
                        'total_optimizations': total_optimizations
                    }
                }
                
        except Exception as e:
            print(f"Error getting site stats: {e}")
            return {}
    
    def get_sites_by_user_email(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all sites scraped by a specific user email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT s.domain, sc.url, sc.title, sc.scraped_at, sc.saved_directory
                    FROM scrapes sc
                    JOIN sites s ON sc.site_id = s.id
                    WHERE sc.user_email = ?
                    ORDER BY sc.scraped_at DESC
                ''', (user_email,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'url': row[1],
                        'domain': row[0],
                        'title': row[2],
                        'timestamp': row[3],
                        'saved_directory': row[4],
                        'category': 'Website',
                        'status': 'completed',
                        'pages_scraped': 1,
                        'user_email': user_email
                    })
                
                return results
                
        except Exception as e:
            print(f"Error getting sites by user email: {e}")
            return []
    
    def search_sites(self, query: str) -> List[Dict[str, Any]]:
        """Search for sites by domain or title"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT s.*, sc.title
                    FROM sites s
                    JOIN scrapes sc ON s.id = sc.site_id
                    WHERE s.domain LIKE ? OR sc.title LIKE ?
                    ORDER BY s.updated_at DESC
                ''', (f'%{query}%', f'%{query}%'))
                
                results = []
                for row in cursor.fetchall():
                    columns = [desc[0] for desc in cursor.description]
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            print(f"Error searching sites: {e}")
            return []
    
    def export_summary(self) -> str:
        """Export a human-readable summary of all tracked sites"""
        try:
            stats = self.get_site_stats()
            
            summary = f"""
🌐 Web Scraper Database Summary
{'=' * 50}

📊 Overall Statistics:
• Total Sites Tracked: {stats['total_sites']}
• Total Scrapes: {stats['total_scrapes']}
• Total Optimizations: {stats['total_optimizations']}
• Database Created: {stats['metadata']['created']}
• Last Updated: {stats['metadata']['last_updated']}

📂 Tracked Sites:
"""
            
            sites = self.get_all_sites()
            for domain, site_data in sites.items():
                summary += f"\n🔗 {domain}\n"
                summary += f"   First Scraped: {site_data['first_scraped']}\n"
                summary += f"   Scrapes: {site_data['scrapes_count']}\n"
                summary += f"   Optimizations: {site_data['optimizations_count']}\n"
                summary += f"   Last Updated: {site_data['updated_at']}\n"
            
            summary += f"\n🕒 Recent Activities:\n"
            for activity in stats['recent_activities'][:5]:
                if activity['type'] == 'scrape':
                    summary += f"   📄 Scraped {activity['site']} at {activity['timestamp']}\n"
                else:
                    summary += f"   🚀 Optimized {activity['site']} at {activity['timestamp']}\n"
            
            return summary
            
        except Exception as e:
            print(f"Error exporting summary: {e}")
            return "Error generating summary"

# Global database instance
db = Database()

# Convenience functions
def add_scraped_site(url: str, scraped_data: Dict[str, Any], saved_directory: str, user_email: Optional[str] = None) -> bool:
    """Add a scraped site to the database"""
    return db.add_scraped_site(url, scraped_data, saved_directory, user_email)

def add_optimized_site(url: str, user_profile: str, optimized_directory: str) -> bool:
    """Add an optimized site to the database"""
    return db.add_optimized_site(url, user_profile, optimized_directory)

def is_site_scraped(url: str) -> bool:
    """Check if a site has been scraped"""
    return db.is_site_scraped(url)

def get_site_stats() -> Dict[str, Any]:
    """Get overall statistics"""
    return db.get_site_stats()

def export_summary() -> str:
    """Export a summary of all tracked sites"""
    return db.export_summary()

def get_sites_by_user_email(user_email: str) -> List[Dict[str, Any]]:
    """Get all sites scraped by a specific user email"""
    return db.get_sites_by_user_email(user_email)

def get_all_sites() -> Dict[str, Any]:
    """Get all tracked sites"""
    return db.get_all_sites()
