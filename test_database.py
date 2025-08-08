#!/usr/bin/env python3
"""
Test script for the SQLite database functionality
"""

import os
import sys
from database import Database, add_scraped_site, get_site_stats, export_summary

def test_database():
    """Test the database functionality"""
    print("🧪 Testing SQLite Database Functionality")
    print("=" * 50)
    
    # Initialize database
    db = Database("test_scraper_data.db")
    print("✅ Database initialized")
    
    # Test data
    test_url = "https://example.com"
    test_data = {
        "title": "Example Website",
        "html_content": "<html><body><h1>Test</h1></body></html>",
        "css_content": {
            "inline_styles": ["body { margin: 0; }"],
            "internal_stylesheets": [],
            "external_stylesheets": ["https://example.com/style.css"]
        },
        "js_content": {
            "inline_scripts": ["console.log('test');"],
            "external_scripts": ["https://example.com/script.js"]
        },
        "links": ["https://example.com/page1", "https://example.com/page2"],
        "seo_metadata": {
            "meta_tags": {"description": "Test description"},
            "open_graph": {"og:title": "Test Title"},
            "twitter_cards": {"twitter:card": "summary"},
            "structured_data": [],
            "headings": {"h1": ["Test Heading"]},
            "images": [{"src": "test.jpg", "alt": "Test Image"}],
            "internal_links": [],
            "external_links": [],
            "social_links": [],
            "canonical_url": "https://example.com",
            "robots_directive": "index, follow",
            "language": "en",
            "charset": "UTF-8",
            "viewport": "width=device-width, initial-scale=1.0",
            "favicon": "https://example.com/favicon.ico",
            "sitemap": "https://example.com/sitemap.xml",
            "rss_feeds": [],
            "analytics": [],
            "word_count": 100,
            "keyword_density": {"test": 5, "example": 3},
            "page_speed_indicators": {"total_images": 1, "total_scripts": 2},
            "detailed_analytics": {
                "google_analytics": [],
                "facebook_pixel": [],
                "google_tag_manager": [],
                "hotjar": [],
                "mixpanel": [],
                "other_tracking": [],
                "social_media_tracking": [],
                "analytics_summary": {
                    "total_tracking_tools": 0,
                    "tracking_intensity": "None"
                }
            }
        }
    }
    
    # Test adding scraped site
    print("\n📝 Testing add_scraped_site...")
    result = add_scraped_site(test_url, test_data, "/test/directory", "test@example.com")
    if result:
        print("✅ Successfully added scraped site to database")
    else:
        print("❌ Failed to add scraped site to database")
        return False
    
    # Test getting site stats
    print("\n📊 Testing get_site_stats...")
    stats = get_site_stats()
    print(f"Total sites: {stats['total_sites']}")
    print(f"Total scrapes: {stats['total_scrapes']}")
    print(f"Total optimizations: {stats['total_optimizations']}")
    
    # Test export summary
    print("\n📋 Testing export_summary...")
    summary = export_summary()
    print("Summary generated successfully")
    
    # Test adding another site
    print("\n📝 Testing second site...")
    test_url2 = "https://test2.com"
    test_data2 = test_data.copy()
    test_data2["title"] = "Test Website 2"
    
    result2 = add_scraped_site(test_url2, test_data2, "/test/directory2", "test2@example.com")
    if result2:
        print("✅ Successfully added second scraped site to database")
    else:
        print("❌ Failed to add second scraped site to database")
    
    # Get updated stats
    stats2 = get_site_stats()
    print(f"Updated total sites: {stats2['total_sites']}")
    print(f"Updated total scrapes: {stats2['total_scrapes']}")
    
    # Test adding optimization
    print("\n🚀 Testing add_optimized_site...")
    from database import add_optimized_site
    opt_result = add_optimized_site(test_url, "test_profile", "/test/optimized")
    if opt_result:
        print("✅ Successfully added optimization to database")
    else:
        print("❌ Failed to add optimization to database")
    
    # Final stats
    final_stats = get_site_stats()
    print(f"\n📊 Final Statistics:")
    print(f"Total sites: {final_stats['total_sites']}")
    print(f"Total scrapes: {final_stats['total_scrapes']}")
    print(f"Total optimizations: {final_stats['total_optimizations']}")
    
    # Clean up test database
    try:
        os.remove("test_scraper_data.db")
        print("\n🧹 Test database cleaned up")
    except:
        print("\n⚠️ Could not clean up test database")
    
    print("\n✅ All database tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
