#!/usr/bin/env python3
"""
Test script to diagnose file access issues for scraped website data
"""

import os
import json
import sqlite3
from urllib.parse import urlparse

def test_file_access():
    """Test file access for scraped data"""
    
    # Database path
    db_path = "gambix_strata.db"
    if os.path.exists("/app/data"):
        db_path = "/app/data/gambix_strata.db"
    
    print(f"Testing database: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all projects with scraped files
        cursor.execute("""
            SELECT project_id, domain, name, scraped_files_path, last_crawl
            FROM projects 
            WHERE scraped_files_path IS NOT NULL
            ORDER BY last_crawl DESC
        """)
        
        projects = cursor.fetchall()
        print(f"\nFound {len(projects)} projects with scraped files:")
        
        for project in projects:
            project_id, domain, name, scraped_files_path, last_crawl = project
            print(f"\n--- Project: {name} ({domain}) ---")
            print(f"Project ID: {project_id}")
            print(f"Scraped Files Path: {scraped_files_path}")
            print(f"Last Crawl: {last_crawl}")
            
            if scraped_files_path:
                # Check if path is absolute
                is_absolute = os.path.isabs(scraped_files_path)
                print(f"Path is absolute: {is_absolute}")
                
                # Resolve path
                if not is_absolute:
                    resolved_path = os.path.abspath(scraped_files_path)
                else:
                    resolved_path = scraped_files_path
                
                print(f"Resolved path: {resolved_path}")
                print(f"Path exists: {os.path.exists(resolved_path)}")
                
                if os.path.exists(resolved_path):
                    # List files
                    try:
                        files = os.listdir(resolved_path)
                        print(f"Files in directory: {files}")
                        
                        # Check for specific files
                        metadata_path = os.path.join(resolved_path, 'metadata.json')
                        seo_report_path = os.path.join(resolved_path, 'seo_report.txt')
                        
                        print(f"metadata.json exists: {os.path.exists(metadata_path)}")
                        print(f"seo_report.txt exists: {os.path.exists(seo_report_path)}")
                        
                        # Try to read metadata
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                print(f"✅ Successfully read metadata.json")
                                print(f"   Title: {metadata.get('title', 'N/A')}")
                                print(f"   Original URL: {metadata.get('original_url', 'N/A')}")
                                print(f"   Scraped at: {metadata.get('scraped_at', 'N/A')}")
                            except Exception as e:
                                print(f"❌ Error reading metadata.json: {e}")
                        
                        # Try to read SEO report
                        if os.path.exists(seo_report_path):
                            try:
                                with open(seo_report_path, 'r', encoding='utf-8') as f:
                                    seo_report = f.read()
                                print(f"✅ Successfully read seo_report.txt ({len(seo_report)} characters)")
                            except Exception as e:
                                print(f"❌ Error reading seo_report.txt: {e}")
                        
                    except Exception as e:
                        print(f"❌ Error listing directory: {e}")
                else:
                    print("❌ Directory does not exist!")
                    
                    # Check if it's a relative path issue
                    current_dir = os.getcwd()
                    print(f"Current working directory: {current_dir}")
                    
                    # Try to find the directory
                    if scraped_files_path.startswith('scraped_sites/'):
                        # Look for scraped_sites directory
                        possible_paths = [
                            os.path.join(current_dir, scraped_files_path),
                            os.path.join(current_dir, '..', scraped_files_path),
                            os.path.join(current_dir, '..', '..', scraped_files_path)
                        ]
                        
                        for path in possible_paths:
                            if os.path.exists(path):
                                print(f"✅ Found directory at: {path}")
                                break
                        else:
                            print("❌ Could not find directory in common locations")
            
            print("-" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_scraped_sites_directory():
    """Test the scraped_sites directory structure"""
    print("\n=== Testing scraped_sites directory ===")
    
    scraped_dir = "scraped_sites"
    print(f"Looking for directory: {scraped_dir}")
    print(f"Directory exists: {os.path.exists(scraped_dir)}")
    
    if os.path.exists(scraped_dir):
        try:
            subdirs = os.listdir(scraped_dir)
            print(f"Found {len(subdirs)} subdirectories:")
            
            for subdir in subdirs[:5]:  # Show first 5
                subdir_path = os.path.join(scraped_dir, subdir)
                if os.path.isdir(subdir_path):
                    files = os.listdir(subdir_path)
                    print(f"  {subdir}: {files}")
            
            if len(subdirs) > 5:
                print(f"  ... and {len(subdirs) - 5} more")
                
        except Exception as e:
            print(f"❌ Error reading scraped_sites directory: {e}")
    else:
        print("❌ scraped_sites directory not found!")

if __name__ == "__main__":
    print("🔍 File Access Diagnostic Tool")
    print("=" * 50)
    
    test_file_access()
    test_scraped_sites_directory()
    
    print("\n✅ Diagnostic complete!")
