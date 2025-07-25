#!/usr/bin/env python3
"""
Test script for the site tracker functionality
"""

import requests
import json
import time
from site_tracker import export_summary, get_site_stats

def test_tracker_functionality():
    """Test the site tracker functionality"""
    
    print("🧪 Testing Site Tracker Functionality")
    print("=" * 50)
    
    # Test URLs to scrape and track
    test_urls = [
        "https://www.dogsonthecurb.com/",
        "https://www.example.com/",
        "https://httpbin.org/html"
    ]
    
    user_profiles = ["general", "foodie_event_planner", "tech_enthusiast"]
    
    base_url = "http://localhost:5000/api"
    
    print("\n📊 Current Tracker Stats:")
    try:
        response = requests.get(f"{base_url}/tracker/stats")
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"   • Total Sites: {stats['total_sites']}")
            print(f"   • Total Scrapes: {stats['total_scrapes']}")
            print(f"   • Total Optimizations: {stats['total_optimizations']}")
        else:
            print("   ❌ Could not fetch stats")
    except Exception as e:
        print(f"   ❌ Error fetching stats: {e}")
    
    print("\n🔗 Testing Site Scraping and Tracking:")
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Testing URL: {url}")
        
        # Scrape the site
        try:
            print("   📄 Scraping...")
            response = requests.post(f"{base_url}/scrape", 
                                   json={"url": url},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"   ✅ Scraped successfully")
                    print(f"   📁 Saved to: {result['data']['saved_directory']}")
                    
                    # Create optimized versions for different user profiles
                    for profile in user_profiles[:2]:  # Only test first 2 profiles
                        print(f"   🚀 Creating optimization for: {profile}")
                        opt_response = requests.post(f"{base_url}/optimize",
                                                   json={
                                                       "url": url,
                                                       "user_profile": profile
                                                   },
                                                   timeout=30)
                        
                        if opt_response.status_code == 200:
                            opt_result = opt_response.json()
                            if opt_result['success']:
                                print(f"   ✅ Optimized for {profile}")
                                print(f"   📁 Saved to: {opt_result['data']['optimized_directory']}")
                            else:
                                print(f"   ❌ Optimization failed: {opt_result['error']}")
                        else:
                            print(f"   ❌ Optimization request failed: {opt_response.status_code}")
                    
                else:
                    print(f"   ❌ Scraping failed: {result['error']}")
            else:
                print(f"   ❌ Scraping request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print("\n📋 Final Tracker Summary:")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/tracker/summary")
        if response.status_code == 200:
            summary = response.json()['data']['summary']
            print(summary)
        else:
            print("❌ Could not fetch summary")
    except Exception as e:
        print(f"❌ Error fetching summary: {e}")
    
    print("\n🔗 All Tracked Sites:")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/tracker/sites")
        if response.status_code == 200:
            sites = response.json()['data']
            if sites:
                for domain, site_data in sites.items():
                    print(f"🔗 {domain}")
                    print(f"   📄 Scrapes: {len(site_data['scrapes'])}")
                    print(f"   🚀 Optimizations: {len(site_data['optimizations'])}")
                    print(f"   📅 First scraped: {site_data['first_scraped']}")
                    if site_data['scrapes']:
                        latest = site_data['scrapes'][-1]
                        print(f"   📄 Latest scrape: {latest['scraped_at']}")
                        print(f"   📝 Title: {latest['title']}")
                    print()
            else:
                print("No sites tracked yet.")
        else:
            print("❌ Could not fetch sites")
    except Exception as e:
        print(f"❌ Error fetching sites: {e}")

def test_tracker_api_endpoints():
    """Test all tracker API endpoints"""
    
    print("\n🔧 Testing Tracker API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api"
    endpoints = [
        "/tracker/stats",
        "/tracker/summary", 
        "/tracker/sites"
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 Testing: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"   ✅ Success")
                    if endpoint == "/tracker/stats":
                        data = result['data']
                        print(f"   📊 Total sites: {data['total_sites']}")
                        print(f"   📊 Total scrapes: {data['total_scrapes']}")
                        print(f"   📊 Total optimizations: {data['total_optimizations']}")
                    elif endpoint == "/tracker/sites":
                        sites = result['data']
                        print(f"   🔗 Sites tracked: {len(sites)}")
                else:
                    print(f"   ❌ API Error: {result['error']}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Request Error: {e}")

def show_tracker_file_info():
    """Show information about the tracker JSON file"""
    
    print("\n📄 Tracker File Information")
    print("=" * 50)
    
    try:
        with open("site_tracker.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"📁 File: site_tracker.json")
        print(f"📊 Version: {data['metadata']['version']}")
        print(f"📅 Created: {data['metadata']['created']}")
        print(f"🔄 Last Updated: {data['metadata']['last_updated']}")
        print(f"📈 Total Sites Scraped: {data['metadata']['total_sites_scraped']}")
        print(f"🚀 Total Optimizations: {data['metadata']['total_optimizations']}")
        print(f"🔗 Sites Tracked: {len(data['sites'])}")
        
        if data['sites']:
            print("\n📋 Tracked Sites:")
            for domain, site_data in data['sites'].items():
                print(f"   🔗 {domain}")
                print(f"      📄 Scrapes: {len(site_data['scrapes'])}")
                print(f"      🚀 Optimizations: {len(site_data['optimizations'])}")
                
    except FileNotFoundError:
        print("❌ site_tracker.json not found")
    except Exception as e:
        print(f"❌ Error reading tracker file: {e}")

if __name__ == "__main__":
    print("🚀 Starting Site Tracker Tests")
    print("Make sure the server is running on http://localhost:5000")
    print()
    
    # Test API endpoints first
    test_tracker_api_endpoints()
    
    # Show current tracker file info
    show_tracker_file_info()
    
    # Test full functionality
    test_tracker_functionality()
    
    print("\n✅ Tracker tests completed!")
    print("\n💡 You can now:")
    print("   • View the tracker in the web interface at http://localhost:5000")
    print("   • Check the 'Tracker' tab for statistics and summaries")
    print("   • See all tracked sites and their optimization history")
    print("   • The site_tracker.json file contains all tracking data")
