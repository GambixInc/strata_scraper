#!/usr/bin/env python3
"""
Migration script to convert from JSON tracker to SQLite database
"""

import json
import os
import sys
from datetime import datetime
from database import Database, add_scraped_site, add_optimized_site

def migrate_json_to_sqlite(json_file_path: str, db_path: str = "scraper_data.db"):
    """
    Migrate data from JSON tracker to SQLite database
    
    Args:
        json_file_path: Path to the site_tracker.json file
        db_path: Path for the new SQLite database
    """
    print(f"🔄 Migrating from {json_file_path} to {db_path}")
    print("=" * 60)
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        print(f"❌ JSON file not found: {json_file_path}")
        return False
    
    # Initialize database
    db = Database(db_path)
    print("✅ Database initialized")
    
    try:
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"📊 Found {len(json_data.get('sites', {}))} sites in JSON tracker")
        
        # Migrate sites
        migrated_sites = 0
        migrated_scrapes = 0
        migrated_optimizations = 0
        
        for domain, site_data in json_data.get('sites', {}).items():
            print(f"\n🔗 Migrating site: {domain}")
            
            # Migrate scrapes
            for scrape in site_data.get('scrapes', []):
                try:
                    # Create minimal scraped_data structure for migration
                    scraped_data = {
                        'title': scrape.get('title', 'Unknown'),
                        'html_content': '',  # Not stored in JSON
                        'css_content': {
                            'inline_styles': [],
                            'internal_stylesheets': [],
                            'external_stylesheets': []
                        },
                        'js_content': {
                            'inline_scripts': [],
                            'external_scripts': []
                        },
                        'links': [],
                        'seo_metadata': {
                            'meta_tags': {},
                            'open_graph': {},
                            'twitter_cards': {},
                            'structured_data': [],
                            'headings': {},
                            'images': [],
                            'internal_links': [],
                            'external_links': [],
                            'social_links': [],
                            'canonical_url': None,
                            'robots_directive': None,
                            'language': None,
                            'charset': None,
                            'viewport': None,
                            'favicon': None,
                            'sitemap': None,
                            'rss_feeds': [],
                            'analytics': [],
                            'word_count': 0,
                            'keyword_density': {},
                            'page_speed_indicators': {},
                            'detailed_analytics': {
                                'google_analytics': [],
                                'facebook_pixel': [],
                                'google_tag_manager': [],
                                'hotjar': [],
                                'mixpanel': [],
                                'other_tracking': [],
                                'social_media_tracking': [],
                                'analytics_summary': {
                                    'total_tracking_tools': 0,
                                    'tracking_intensity': 'Unknown'
                                }
                            }
                        }
                    }
                    
                    # Add scrape to database
                    if add_scraped_site(
                        scrape['url'], 
                        scraped_data, 
                        scrape.get('saved_directory', ''), 
                        scrape.get('user_email')
                    ):
                        migrated_scrapes += 1
                        print(f"  ✅ Migrated scrape: {scrape['url']}")
                    else:
                        print(f"  ❌ Failed to migrate scrape: {scrape['url']}")
                        
                except Exception as e:
                    print(f"  ⚠️ Error migrating scrape: {e}")
            
            # Migrate optimizations
            for optimization in site_data.get('optimizations', []):
                try:
                    if add_optimized_site(
                        optimization['original_url'],
                        optimization['user_profile'],
                        optimization.get('optimized_directory', '')
                    ):
                        migrated_optimizations += 1
                        print(f"  ✅ Migrated optimization: {optimization['user_profile']}")
                    else:
                        print(f"  ❌ Failed to migrate optimization: {optimization['user_profile']}")
                        
                except Exception as e:
                    print(f"  ⚠️ Error migrating optimization: {e}")
            
            migrated_sites += 1
        
        # Print migration summary
        print(f"\n📊 Migration Summary")
        print("=" * 40)
        print(f"Sites migrated: {migrated_sites}")
        print(f"Scrapes migrated: {migrated_scrapes}")
        print(f"Optimizations migrated: {migrated_optimizations}")
        
        # Verify migration
        from database import get_site_stats
        stats = get_site_stats()
        print(f"\n📈 Database Statistics After Migration:")
        print(f"Total sites: {stats['total_sites']}")
        print(f"Total scrapes: {stats['total_scrapes']}")
        print(f"Total optimizations: {stats['total_optimizations']}")
        
        print(f"\n✅ Migration completed successfully!")
        print(f"📁 New database: {db_path}")
        print(f"💾 Original JSON file: {json_file_path}")
        print(f"\n💡 You can now safely remove the old JSON file if desired.")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def backup_json_file(json_file_path: str):
    """Create a backup of the JSON file before migration"""
    if not os.path.exists(json_file_path):
        return False
    
    backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(json_file_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"⚠️ Could not create backup: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 JSON to SQLite Migration Tool")
    print("=" * 50)
    
    # Default paths
    json_file = "site_tracker.json"
    db_file = "scraper_data.db"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    if len(sys.argv) > 2:
        db_file = sys.argv[2]
    
    print(f"Source JSON file: {json_file}")
    print(f"Target SQLite database: {db_file}")
    
    # Check if database already exists
    if os.path.exists(db_file):
        response = input(f"\n⚠️ Database {db_file} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Create backup
    print(f"\n📋 Creating backup of JSON file...")
    backup_json_file(json_file)
    
    # Perform migration
    print(f"\n🚀 Starting migration...")
    success = migrate_json_to_sqlite(json_file, db_file)
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"Your application is now using SQLite database: {db_file}")
    else:
        print(f"\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
