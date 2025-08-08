#!/usr/bin/env python3
"""
Migration script to transition from the old database schema to the new Gambix Strata schema.
This script will help migrate existing data and set up the new database structure.
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

class DatabaseMigrator:
    """Migrate from old database schema to new Gambix Strata schema"""
    
    def __init__(self, old_db_path: str = "data/scraper_data.db", new_db_path: str = "data/gambix_strata.db"):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.backup_path = f"{old_db_path}.backup"
    
    def create_backup(self):
        """Create a backup of the old database"""
        if os.path.exists(self.old_db_path):
            shutil.copy2(self.old_db_path, self.backup_path)
            print(f"✅ Backup created: {self.backup_path}")
        else:
            print("⚠️  No old database found to backup")
    
    def check_old_database(self) -> bool:
        """Check if old database exists and has data"""
        if not os.path.exists(self.old_db_path):
            print("❌ Old database not found")
            return False
        
        try:
            with sqlite3.connect(self.old_db_path) as conn:
                cursor = conn.cursor()
                
                # Check if old tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                old_tables = ['sites', 'scrapes', 'optimizations', 'seo_metadata', 'analytics_data']
                existing_old_tables = [table for table in old_tables if table in tables]
                
                if not existing_old_tables:
                    print("❌ No old schema tables found")
                    return False
                
                print(f"✅ Found old database with tables: {existing_old_tables}")
                
                # Count records
                for table in existing_old_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count} records")
                
                return True
                
        except Exception as e:
            print(f"❌ Error checking old database: {e}")
            return False
    
    def migrate_users(self):
        """Migrate user data from old database"""
        print("\n🔄 Migrating users...")
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_cursor = old_conn.cursor()
                
                # Get unique user emails from scrapes
                old_cursor.execute("SELECT DISTINCT user_email FROM scrapes WHERE user_email IS NOT NULL")
                user_emails = [row[0] for row in old_cursor.fetchall()]
                
                if not user_emails:
                    print("   No user emails found in old database")
                    return
                
                # Create new database connection
                from database import GambixStrataDatabase
                new_db = GambixStrataDatabase(self.new_db_path)
                
                migrated_users = 0
                for email in user_emails:
                    # Check if user already exists
                    existing_user = new_db.get_user_by_email(email)
                    if not existing_user:
                        user_id = new_db.create_user(email, f"User {email}", 'user')
                        migrated_users += 1
                        print(f"   Created user: {email}")
                    else:
                        print(f"   User already exists: {email}")
                
                print(f"✅ Migrated {migrated_users} users")
                
        except Exception as e:
            print(f"❌ Error migrating users: {e}")
    
    def migrate_projects(self):
        """Migrate sites to projects"""
        print("\n🔄 Migrating sites to projects...")
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_cursor = old_conn.cursor()
                
                # Get all sites
                old_cursor.execute("SELECT * FROM sites")
                sites = old_cursor.fetchall()
                
                if not sites:
                    print("   No sites found in old database")
                    return
                
                # Get column names
                columns = [description[0] for description in old_cursor.description]
                
                from database import GambixStrataDatabase
                new_db = GambixStrataDatabase(self.new_db_path)
                
                migrated_projects = 0
                for site in sites:
                    site_data = dict(zip(columns, site))
                    
                    # Create a default user if none exists
                    users = new_db.get_user_by_email("default@migration.com")
                    if not users:
                        user_id = new_db.create_user("default@migration.com", "Migration User", 'user')
                    else:
                        user_id = users['user_id']
                    
                    # Create project
                    project_id = new_db.create_project(
                        user_id=user_id,
                        domain=site_data['domain'],
                        name=f"{site_data['domain']} Website",
                        settings={
                            'migrated_from': 'old_schema',
                            'original_site_id': site_data['id'],
                            'first_scraped': site_data['first_scraped'],
                            'last_scraped': site_data['last_scraped']
                        }
                    )
                    
                    migrated_projects += 1
                    print(f"   Created project: {site_data['domain']}")
                
                print(f"✅ Migrated {migrated_projects} projects")
                
        except Exception as e:
            print(f"❌ Error migrating projects: {e}")
    
    def migrate_pages(self):
        """Migrate scrapes to pages"""
        print("\n🔄 Migrating scrapes to pages...")
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_cursor = old_conn.cursor()
                
                # Get all scrapes with site information
                old_cursor.execute("""
                    SELECT s.*, st.domain 
                    FROM scrapes s 
                    JOIN sites st ON s.site_id = st.id
                """)
                scrapes = old_cursor.fetchall()
                
                if not scrapes:
                    print("   No scrapes found in old database")
                    return
                
                # Get column names
                columns = [description[0] for description in old_cursor.description]
                
                from database import GambixStrataDatabase
                new_db = GambixStrataDatabase(self.new_db_path)
                
                migrated_pages = 0
                for scrape in scrapes:
                    scrape_data = dict(zip(columns, scrape))
                    
                    # Find the corresponding project
                    projects = new_db.get_user_projects("default@migration.com")
                    project = next((p for p in projects if p['domain'] == scrape_data['domain']), None)
                    
                    if not project:
                        print(f"   Skipping scrape for {scrape_data['domain']} - no project found")
                        continue
                    
                    # Create page data
                    page_data = {
                        'page_url': scrape_data['url'],
                        'title': scrape_data['title'] or 'Unknown',
                        'status': 'healthy',
                        'last_crawled': scrape_data['scraped_at'],
                        'word_count': scrape_data['word_count'] or 0,
                        'links_count': scrape_data['links_count'] or 0,
                        'images_count': 0,  # Not available in old schema
                        'meta_description': '',  # Not available in old schema
                        'h1_tags': []  # Not available in old schema
                    }
                    
                    new_db.add_page(project['project_id'], page_data)
                    migrated_pages += 1
                    print(f"   Created page: {scrape_data['url']}")
                
                print(f"✅ Migrated {migrated_pages} pages")
                
        except Exception as e:
            print(f"❌ Error migrating pages: {e}")
    
    def migrate_seo_data(self):
        """Migrate SEO metadata to recommendations"""
        print("\n🔄 Migrating SEO metadata to recommendations...")
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_cursor = old_conn.cursor()
                
                # Check if seo_metadata table exists
                old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seo_metadata'")
                if not old_cursor.fetchone():
                    print("   No SEO metadata table found")
                    return
                
                # Get SEO metadata with scrape information
                old_cursor.execute("""
                    SELECT sm.*, s.url, st.domain 
                    FROM seo_metadata sm
                    JOIN scrapes s ON sm.scrape_id = s.id
                    JOIN sites st ON s.site_id = st.id
                """)
                seo_records = old_cursor.fetchall()
                
                if not seo_records:
                    print("   No SEO metadata found")
                    return
                
                # Get column names
                columns = [description[0] for description in old_cursor.description]
                
                from database import GambixStrataDatabase
                new_db = GambixStrataDatabase(self.new_db_path)
                
                migrated_recommendations = 0
                for record in seo_records:
                    seo_data = dict(zip(columns, record))
                    
                    # Find the corresponding project
                    projects = new_db.get_user_projects("default@migration.com")
                    project = next((p for p in projects if p['domain'] == seo_data['domain']), None)
                    
                    if not project:
                        continue
                    
                    # Create recommendations based on SEO data
                    recommendations = self._generate_recommendations_from_seo(seo_data)
                    
                    for rec in recommendations:
                        new_db.add_recommendation(project['project_id'], rec)
                        migrated_recommendations += 1
                
                print(f"✅ Migrated {migrated_recommendations} recommendations")
                
        except Exception as e:
            print(f"❌ Error migrating SEO data: {e}")
    
    def _generate_recommendations_from_seo(self, seo_data: Dict) -> List[Dict]:
        """Generate recommendations from old SEO metadata"""
        recommendations = []
        
        # Parse JSON fields
        meta_tags = json.loads(seo_data.get('meta_tags', '{}'))
        headings = json.loads(seo_data.get('headings', '{}'))
        
        # Check for missing meta description
        if not meta_tags.get('description'):
            recommendations.append({
                'page_url': seo_data['url'],
                'category': 'technical_seo',
                'issue': 'Missing meta description',
                'recommendation': 'Add a compelling meta description to improve search engine visibility and click-through rates.',
                'priority': 'high',
                'impact_score': 85,
                'guidelines': [
                    'Keep meta description between 150-160 characters',
                    'Include primary keywords naturally',
                    'Make it compelling and action-oriented'
                ]
            })
        
        # Check for missing H1 tags
        if not headings.get('h1'):
            recommendations.append({
                'page_url': seo_data['url'],
                'category': 'content_seo',
                'issue': 'Missing H1 heading',
                'recommendation': 'Add a clear, descriptive H1 heading to improve content structure and SEO.',
                'priority': 'medium',
                'impact_score': 70,
                'guidelines': [
                    'Use only one H1 per page',
                    'Include primary keywords',
                    'Make it descriptive and engaging'
                ]
            })
        
        # Check for low word count
        word_count = seo_data.get('word_count', 0)
        if word_count < 300:
            recommendations.append({
                'page_url': seo_data['url'],
                'category': 'content_seo',
                'issue': f'Low word count ({word_count} words)',
                'recommendation': 'Expand content to provide more value and improve search rankings.',
                'priority': 'medium',
                'impact_score': 75,
                'guidelines': [
                    'Aim for at least 300-500 words',
                    'Include relevant keywords naturally',
                    'Provide comprehensive information'
                ]
            })
        
        return recommendations
    
    def create_sample_data(self):
        """Create sample data for testing the new schema"""
        print("\n🔄 Creating sample data...")
        
        try:
            from database import GambixStrataDatabase
            db = GambixStrataDatabase(self.new_db_path)
            
            # Create sample user
            user_id = db.create_user("demo@example.com", "Demo User", "admin")
            print(f"   Created demo user: demo@example.com")
            
            # Create sample project
            project_id = db.create_project(
                user_id=user_id,
                domain="example.com",
                name="Example Website",
                settings={
                    'crawl_frequency': 'daily',
                    'optimization_threshold': 70,
                    'notification_emails': ['demo@example.com']
                }
            )
            print(f"   Created sample project: example.com")
            
            # Add sample site health
            health_id = db.add_site_health(project_id, {
                'overall_score': 75,
                'technical_seo': 80,
                'content_seo': 70,
                'performance': 85,
                'internal_linking': 90,
                'visual_ux': 65,
                'authority_backlinks': 60,
                'total_impressions': 5000,
                'total_engagements': 2000,
                'total_conversions': 150,
                'crawl_data': {
                    'healthy_pages': 15,
                    'broken_pages': 2,
                    'pages_with_issues': 3,
                    'total_pages': 20
                }
            })
            print(f"   Added sample site health data")
            
            # Add sample pages
            sample_pages = [
                {
                    'page_url': 'https://example.com/home',
                    'title': 'Home Page',
                    'word_count': 800,
                    'load_time': 2.1,
                    'meta_description': 'Welcome to our website',
                    'h1_tags': ['Welcome to Example'],
                    'images_count': 5,
                    'links_count': 12
                },
                {
                    'page_url': 'https://example.com/about',
                    'title': 'About Us',
                    'word_count': 1200,
                    'load_time': 1.8,
                    'meta_description': 'Learn more about our company',
                    'h1_tags': ['About Our Company'],
                    'images_count': 3,
                    'links_count': 8
                }
            ]
            
            for page_data in sample_pages:
                db.add_page(project_id, page_data)
            print(f"   Added {len(sample_pages)} sample pages")
            
            # Add sample recommendations
            sample_recommendations = [
                {
                    'page_url': 'https://example.com/home',
                    'category': 'content_seo',
                    'issue': 'Page content is too thin',
                    'recommendation': 'Expand the home page content to provide more value to visitors.',
                    'priority': 'high',
                    'impact_score': 85,
                    'guidelines': [
                        'Add more detailed content sections',
                        'Include customer testimonials',
                        'Add a clear call-to-action'
                    ]
                },
                {
                    'page_url': 'https://example.com/about',
                    'category': 'technical_seo',
                    'issue': 'Missing structured data',
                    'recommendation': 'Add JSON-LD structured data to improve search engine understanding.',
                    'priority': 'medium',
                    'impact_score': 70,
                    'guidelines': [
                        'Add Organization schema',
                        'Include contact information',
                        'Add breadcrumb navigation'
                    ]
                }
            ]
            
            for rec_data in sample_recommendations:
                db.add_recommendation(project_id, rec_data)
            print(f"   Added {len(sample_recommendations)} sample recommendations")
            
            # Add sample alert
            alert_id = db.create_alert(user_id, {
                'project_id': project_id,
                'type': 'low_site_health',
                'title': 'Site Health Below Threshold',
                'description': 'example.com has a site health score of 75%, which is below the recommended threshold.',
                'priority': 'medium',
                'metadata': {
                    'site_health_score': 75,
                    'recommendations_count': 2
                }
            })
            print(f"   Added sample alert")
            
            print("✅ Sample data created successfully")
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
    
    def run_migration(self, create_sample: bool = False):
        """Run the complete migration process"""
        print("🚀 Starting Gambix Strata Database Migration")
        print("=" * 50)
        
        # Create backup
        self.create_backup()
        
        # Check old database
        if not self.check_old_database():
            print("\n⚠️  No old database to migrate. Creating new database with sample data...")
            if create_sample:
                self.create_sample_data()
            return
        
        # Run migration steps
        self.migrate_users()
        self.migrate_projects()
        self.migrate_pages()
        self.migrate_seo_data()
        
        if create_sample:
            self.create_sample_data()
        
        print("\n✅ Migration completed successfully!")
        print(f"📁 New database: {self.new_db_path}")
        print(f"📁 Backup: {self.backup_path}")
        
        # Show migration summary
        self.show_migration_summary()
    
    def show_migration_summary(self):
        """Show summary of migrated data"""
        print("\n📊 Migration Summary:")
        print("-" * 30)
        
        try:
            from database import GambixStrataDatabase
            db = GambixStrataDatabase(self.new_db_path)
            
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                tables = ['users', 'projects', 'pages', 'recommendations', 'alerts', 'site_health']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table.capitalize()}: {count}")
                
        except Exception as e:
            print(f"❌ Error showing summary: {e}")

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate to Gambix Strata Database Schema')
    parser.add_argument('--old-db', default='scraper_data.db', help='Path to old database')
    parser.add_argument('--new-db', default='gambix_strata.db', help='Path to new database')
    parser.add_argument('--sample', action='store_true', help='Create sample data')
    parser.add_argument('--backup-only', action='store_true', help='Only create backup')
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator(args.old_db, args.new_db)
    
    if args.backup_only:
        migrator.create_backup()
        return
    
    migrator.run_migration(create_sample=args.sample)

if __name__ == "__main__":
    main()
