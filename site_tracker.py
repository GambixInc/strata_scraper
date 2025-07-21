import json
import os
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any

class SiteTracker:
    """
    A class to track scraped and optimized websites
    """
    
    def __init__(self, tracker_file: str = "site_tracker.json"):
        self.tracker_file = tracker_file
        self.data = self._load_tracker()
    
    def _load_tracker(self) -> Dict[str, Any]:
        """Load the tracker JSON file or create a new one if it doesn't exist"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Warning: Could not load {self.tracker_file}, creating new tracker")
                return self._create_new_tracker()
        else:
            return self._create_new_tracker()
    
    def _create_new_tracker(self) -> Dict[str, Any]:
        """Create a new tracker structure"""
        return {
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "total_sites_scraped": 0,
                "total_optimizations": 0
            },
            "sites": {}
        }
    
    def _save_tracker(self):
        """Save the tracker data to JSON file"""
        self.data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def _get_site_key(self, url: str) -> str:
        """Generate a unique key for a site based on its domain"""
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    
    def add_scraped_site(self, url: str, scraped_data: Dict[str, Any], saved_directory: str, user_email: Optional[str] = None) -> bool:
        """
        Add a newly scraped site to the tracker
        
        Args:
            url: The URL that was scraped
            scraped_data: The scraped data dictionary
            saved_directory: Path to the saved files
            user_email: Email of the user who scraped the site
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            site_key = self._get_site_key(url)
            
            # Create site entry if it doesn't exist
            if site_key not in self.data["sites"]:
                self.data["sites"][site_key] = {
                    "domain": site_key,
                    "first_scraped": datetime.now().isoformat(),
                    "scrapes": [],
                    "optimizations": []
                }
            
            # Add scrape record
            scrape_record = {
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "saved_directory": saved_directory,
                "user_email": user_email,
                "title": scraped_data.get('title', 'Unknown'),
                "stats": {
                    "links_count": len(scraped_data.get('links', [])),
                    "inline_styles_count": len(scraped_data.get('css_content', {}).get('inline_styles', [])),
                    "internal_stylesheets_count": len(scraped_data.get('css_content', {}).get('internal_stylesheets', [])),
                    "external_stylesheets_count": len(scraped_data.get('css_content', {}).get('external_stylesheets', [])),
                    "inline_scripts_count": len(scraped_data.get('js_content', {}).get('inline_scripts', [])),
                    "external_scripts_count": len(scraped_data.get('js_content', {}).get('external_scripts', []))
                }
            }
            
            self.data["sites"][site_key]["scrapes"].append(scrape_record)
            self.data["sites"][site_key]["last_scraped"] = datetime.now().isoformat()
            
            # Update metadata
            self.data["metadata"]["total_sites_scraped"] += 1
            
            self._save_tracker()
            return True
            
        except Exception as e:
            print(f"Error adding scraped site to tracker: {e}")
            return False
    
    def add_optimized_site(self, url: str, user_profile: str, optimized_directory: str) -> bool:
        """
        Add an optimized version to the tracker
        
        Args:
            url: The original URL that was optimized
            user_profile: The user profile used for optimization
            optimized_directory: Path to the optimized files
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            site_key = self._get_site_key(url)
            
            # Create site entry if it doesn't exist
            if site_key not in self.data["sites"]:
                self.data["sites"][site_key] = {
                    "domain": site_key,
                    "first_scraped": datetime.now().isoformat(),
                    "scrapes": [],
                    "optimizations": []
                }
            
            # Add optimization record
            optimization_record = {
                "original_url": url,
                "user_profile": user_profile,
                "optimized_at": datetime.now().isoformat(),
                "optimized_directory": optimized_directory
            }
            
            self.data["sites"][site_key]["optimizations"].append(optimization_record)
            self.data["sites"][site_key]["last_optimized"] = datetime.now().isoformat()
            
            # Update metadata
            self.data["metadata"]["total_optimizations"] += 1
            
            self._save_tracker()
            return True
            
        except Exception as e:
            print(f"Error adding optimized site to tracker: {e}")
            return False
    
    def is_site_scraped(self, url: str) -> bool:
        """
        Check if a site has been scraped before
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if site has been scraped, False otherwise
        """
        site_key = self._get_site_key(url)
        return site_key in self.data["sites"] and len(self.data["sites"][site_key]["scrapes"]) > 0
    
    def get_site_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific site
        
        Args:
            url: The URL to get info for
            
        Returns:
            Dict containing site information or None if not found
        """
        site_key = self._get_site_key(url)
        return self.data["sites"].get(site_key)
    
    def get_all_sites(self) -> Dict[str, Any]:
        """
        Get information about all tracked sites
        
        Returns:
            Dict containing all site information
        """
        return self.data["sites"]
    
    def get_site_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics about tracked sites
        
        Returns:
            Dict containing statistics
        """
        total_sites = len(self.data["sites"])
        total_scrapes = sum(len(site["scrapes"]) for site in self.data["sites"].values())
        total_optimizations = sum(len(site["optimizations"]) for site in self.data["sites"].values())
        
        # Get most recent activity
        all_activities = []
        for site_key, site_data in self.data["sites"].items():
            for scrape in site_data["scrapes"]:
                all_activities.append({
                    "type": "scrape",
                    "site": site_key,
                    "timestamp": scrape["scraped_at"],
                    "url": scrape["url"]
                })
            for optimization in site_data["optimizations"]:
                all_activities.append({
                    "type": "optimization",
                    "site": site_key,
                    "timestamp": optimization["optimized_at"],
                    "user_profile": optimization["user_profile"]
                })
        
        # Sort by timestamp (most recent first)
        all_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "total_sites": total_sites,
            "total_scrapes": total_scrapes,
            "total_optimizations": total_optimizations,
            "recent_activities": all_activities[:10],  # Last 10 activities
            "metadata": self.data["metadata"]
        }
    
    def search_sites(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for sites by domain or title
        
        Args:
            query: Search query string
            
        Returns:
            List of matching sites
        """
        results = []
        query_lower = query.lower()
        
        for site_key, site_data in self.data["sites"].items():
            # Search in domain
            if query_lower in site_key.lower():
                results.append(site_data)
                continue
            
            # Search in titles
            for scrape in site_data["scrapes"]:
                if query_lower in scrape.get("title", "").lower():
                    results.append(site_data)
                    break
        
        return results
    
    def get_sites_by_user_email(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Get all sites scraped by a specific user email
        
        Args:
            user_email: The user email to search for
            
        Returns:
            List of sites scraped by that user with metadata
        """
        results = []
        
        for site_key, site_data in self.data["sites"].items():
            user_scrapes = []
            for scrape in site_data["scrapes"]:
                if scrape.get("user_email") == user_email:
                    user_scrapes.append(scrape)
            
            if user_scrapes:
                # Get the latest scrape for this user
                latest_scrape = max(user_scrapes, key=lambda x: x["scraped_at"])
                
                results.append({
                    "url": latest_scrape["url"],
                    "domain": site_data["domain"],
                    "title": latest_scrape["title"],
                    "timestamp": latest_scrape["scraped_at"],
                    "saved_directory": latest_scrape["saved_directory"],
                    "category": "Website",  # Default category, could be enhanced
                    "status": "completed",  # Default status, could be enhanced
                    "pages_scraped": 1,  # Could be enhanced to count actual pages
                    "user_email": user_email
                })
        
        # Sort by timestamp, newest first
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results
    
    def get_sites_by_user_profile(self, user_profile: str) -> List[Dict[str, Any]]:
        """
        Get all sites optimized for a specific user profile
        
        Args:
            user_profile: The user profile to search for
            
        Returns:
            List of sites with optimizations for that profile
        """
        results = []
        
        for site_key, site_data in self.data["sites"].items():
            for optimization in site_data["optimizations"]:
                if optimization["user_profile"] == user_profile:
                    results.append(site_data)
                    break
        
        return results
    
    def export_summary(self) -> str:
        """
        Export a human-readable summary of all tracked sites
        
        Returns:
            String containing the summary
        """
        stats = self.get_site_stats()
        
        summary = f"""
🌐 Web Scraper Site Tracker Summary
{'=' * 50}

📊 Overall Statistics:
• Total Sites Tracked: {stats['total_sites']}
• Total Scrapes: {stats['total_scrapes']}
• Total Optimizations: {stats['total_optimizations']}
• Tracker Created: {stats['metadata']['created']}
• Last Updated: {stats['metadata']['last_updated']}

📂 Tracked Sites:
"""
        
        for site_key, site_data in self.data["sites"].items():
            summary += f"\n🔗 {site_key}\n"
            summary += f"   First Scraped: {site_data['first_scraped']}\n"
            summary += f"   Scrapes: {len(site_data['scrapes'])}\n"
            summary += f"   Optimizations: {len(site_data['optimizations'])}\n"
            
            if site_data['scrapes']:
                latest_scrape = site_data['scrapes'][-1]
                summary += f"   Latest Scrape: {latest_scrape['scraped_at']}\n"
                summary += f"   Title: {latest_scrape['title']}\n"
            
            if site_data['optimizations']:
                latest_opt = site_data['optimizations'][-1]
                summary += f"   Latest Optimization: {latest_opt['optimized_at']} ({latest_opt['user_profile']})\n"
        
        summary += f"\n🕒 Recent Activities:\n"
        for activity in stats['recent_activities'][:5]:
            if activity['type'] == 'scrape':
                summary += f"   📄 Scraped {activity['site']} at {activity['timestamp']}\n"
            else:
                summary += f"   🚀 Optimized {activity['site']} for {activity['user_profile']} at {activity['timestamp']}\n"
        
        return summary

# Global tracker instance
tracker = SiteTracker()

# Convenience functions
def add_scraped_site(url: str, scraped_data: Dict[str, Any], saved_directory: str, user_email: Optional[str] = None) -> bool:
    """Add a scraped site to the tracker"""
    return tracker.add_scraped_site(url, scraped_data, saved_directory, user_email)

def add_optimized_site(url: str, user_profile: str, optimized_directory: str) -> bool:
    """Add an optimized site to the tracker"""
    return tracker.add_optimized_site(url, user_profile, optimized_directory)

def is_site_scraped(url: str) -> bool:
    """Check if a site has been scraped"""
    return tracker.is_site_scraped(url)

def get_site_stats() -> Dict[str, Any]:
    """Get overall statistics"""
    return tracker.get_site_stats()

def export_summary() -> str:
    """Export a summary of all tracked sites"""
    return tracker.export_summary()

def get_sites_by_user_email(user_email: str) -> List[Dict[str, Any]]:
    """Get all sites scraped by a specific user email"""
    return tracker.get_sites_by_user_email(user_email) 