#!/usr/bin/env python3
"""
Simple test script to debug the web scraper
"""

import sys
import traceback
from main import simple_web_scraper

def test_scraper(url):
    """Test the scraper with a given URL"""
    print(f"Testing scraper with URL: {url}")
    print("=" * 50)
    
    try:
        # Test the scraper
        result = simple_web_scraper(url)
        
        if result:
            print("✅ Scraping successful!")
            print(f"Title: {result.get('title', 'No title')}")
            print(f"Links found: {len(result.get('links', []))}")
            print(f"CSS files: {len(result.get('css_content', {}).get('external_stylesheets', []))}")
            print(f"JS files: {len(result.get('js_content', {}).get('external_scripts', []))}")
            
            # Check SEO metadata
            seo = result.get('seo_metadata', {})
            if seo:
                print(f"Word count: {seo.get('word_count', 0)}")
                print(f"Meta tags: {len(seo.get('meta_tags', {}))}")
                print(f"Images: {len(seo.get('images', []))}")
                
                # Check analytics
                analytics = seo.get('detailed_analytics', {})
                if analytics:
                    summary = analytics.get('analytics_summary', {})
                    print(f"Tracking tools: {summary.get('total_tracking_tools', 0)}")
                    print(f"Tracking intensity: {summary.get('tracking_intensity', 'Unknown')}")
            
            return True
        else:
            print("❌ Scraping failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test URLs
    test_urls = [
        "https://www.example.com",
        "https://httpbin.org/html",
        "https://www.google.com"
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument as URL
        test_url = sys.argv[1]
        test_scraper(test_url)
    else:
        # Test with default URLs
        for url in test_urls:
            print(f"\nTesting: {url}")
            success = test_scraper(url)
            if success:
                print("✅ This URL works!")
                break
            else:
                print("❌ This URL failed, trying next...")
                print() 