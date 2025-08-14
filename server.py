from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
# DynamoDB only - no SQLite imports needed
from main import simple_web_scraper, save_content_to_s3, get_safe_filename
from database_config import GambixStrataDatabase, add_scraped_site, add_optimized_site, get_site_stats, export_summary, get_sites_by_user_email, get_all_sites, USE_DYNAMODB
import json
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
from auth import require_auth, require_role
from typing import Dict

import sentry_sdk

def calculate_health_score(scraped_data: Dict) -> int:
    """Calculate a health score based on scraped data"""
    score = 100
    seo_data = scraped_data.get('seo_metadata', {})
    
    # Deduct points for missing elements
    if not scraped_data.get('title'):
        score -= 15
    if not seo_data.get('meta_description'):
        score -= 10
    if not seo_data.get('canonical_url'):
        score -= 5
    
    # Check images without alt text
    images = seo_data.get('images', [])
    images_without_alt = sum(1 for img in images if not img.get('alt'))
    if images_without_alt > 0:
        score -= min(10, images_without_alt * 2)
    
    # Check word count
    word_count = seo_data.get('word_count', 0)
    if word_count < 300:
        score -= 10
    elif word_count < 500:
        score -= 5
    
    # Check for tracking tools (too many can be bad)
    analytics = seo_data.get('analytics', [])
    if len(analytics) > 5:
        score -= 5
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))

sentry_sdk.init(
    dsn="https://ffde2275aa6db7e04c3e35413b820421@o4509488900276224.ingest.us.sentry.io/4509610363191296",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

load_dotenv()  # Load environment variables from .env file

# Replace hardcoded values with environment variables
PORT = int(os.getenv('PORT', 8080))
HOST = os.getenv('HOST', '0.0.0.0')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Add rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per hour"]  # Very lenient for development
)

# Configure security headers
Talisman(app, 
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'connect-src': "'self' http://localhost:5000",
    },
    force_https=False,  # Disable automatic HTTPS redirects
    force_https_permanent=False  # Disable permanent HTTPS redirects

)

# Configure logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/web_scraper.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Web Scraper startup')

# Initialize database tables on startup
def initialize_database():
    """Initialize database tables and ensure they exist"""
    try:
        db = GambixStrataDatabase()
        
        # DynamoDB tables are created automatically if they don't exist
        app.logger.info("DynamoDB tables will be created automatically if they don't exist")
            
    except Exception as e:
        app.logger.error(f"Error initializing database: {e}")

# Initialize database on startup
initialize_database()

def ensure_user_exists(email, request_user_data):
    """
    Helper function to ensure a user exists in the database.
    Creates the user if they don't exist.
    
    Args:
        email (str): User's email address
        request_user_data (dict): User data from request.current_user
        
    Returns:
        dict: User data from database
    """
    db = GambixStrataDatabase()
    
    # Try to get user from database first
    user_data = db.get_user_by_email(email)
    
    if not user_data:
        # Create user in database if they don't exist
        cognito_user_id = request_user_data.get('cognito_user_id')
        user_name = request_user_data.get('name') or email
        given_name = request_user_data.get('given_name')
        family_name = request_user_data.get('family_name')
        
        user_id = db.create_user(
            email=email,
            name=user_name,
            cognito_user_id=cognito_user_id,
            given_name=given_name,
            family_name=family_name
        )
        
        # Get the newly created user data
        user_data = db.get_user_by_email(email)
        app.logger.info(f"Created new user: {email} with ID: {user_id}")
    
    return user_data

# User Profile Endpoints (for AWS Cognito authenticated users)
@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get current user profile"""
    try:
        email = request.current_user['email']
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        
        if user_data:
            user_data.pop('password_hash', None)  # Remove password hash
            return jsonify({
                'success': True,
                'data': user_data
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        app.logger.error(f"Error getting user profile: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user profile'}), 500

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_user_profile():
    """Update current user profile"""
    try:
        email = request.current_user['email']
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        
        success = db.update_user_profile(user_data['user_id'], data)
        
        if success:
            # Get updated user data
            updated_user = db.get_user_by_email(email)
            if updated_user:
                updated_user.pop('password_hash', None)
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'data': updated_user
                })
        
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500
        
    except Exception as e:
        app.logger.error(f"Error updating user profile: {e}")
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500

# API Endpoints (must come before catch-all route)




@app.route('/api/scrape', methods=['POST'])
# @limiter.limit("10 per minute")  # Limit scraping requests - temporarily disabled
def scrape_website():
    """
    API endpoint to scrape a website
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
            
        url = data.get('url')
        user_email = data.get('user_email') # Get user_email from request data
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'error': 'Invalid URL format. URL must start with http:// or https://'}), 400
        
        # Call your existing scraper function
        scraped_data = simple_web_scraper(url)
        
        if scraped_data:
            try:
                # Save to S3 storage (production default)
                saved_location = None
                storage_type = None
                
                try:
                    # Use S3 storage for production
                    saved_location = save_content_to_s3(scraped_data, url)
                    if saved_location:
                        storage_type = 's3'
                        print(f"✅ Content saved to S3: {saved_location}")
                    else:
                        print(f"❌ Failed to save to S3")
                        return jsonify({
                            'success': False,
                            'error': 'Failed to save content to S3'
                        }), 500
                except Exception as s3_error:
                    print(f"❌ S3 storage failed: {s3_error}")
                    return jsonify({
                        'success': False,
                        'error': f'S3 storage failed: {str(s3_error)}'
                    }), 500
                
                # Add to site tracker
                if saved_location:
                    add_scraped_site(url, scraped_data, saved_location, user_email) # Pass user_email
                
                # Add the saved location and storage type to the response
                scraped_data['saved_location'] = saved_location
                scraped_data['storage_type'] = storage_type
                
                return jsonify({
                    'success': True,
                    'data': scraped_data,
                    'message': f'Content saved to {storage_type}: {saved_location}'
                })
            except Exception as save_error:
                print(f"Error saving content: {save_error}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to save content: {str(save_error)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to scrape the website. Please check the URL and try again.'
            }), 500
            
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_website():
    """
    API endpoint to create an optimized version of a scraped website
    """
    try:
        data = request.get_json()
        url = data.get('url')
        user_profile = data.get('user_profile', 'general')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # First scrape the website
        scraped_data = simple_web_scraper(url)
        
        if not scraped_data:
            return jsonify({
                'success': False,
                'error': 'Failed to scrape the website'
            }), 500
        
        # Create optimized version
        optimized_html = create_optimized_version(scraped_data, url, user_profile)
        
        # Save optimized version
        optimized_dir = save_optimized_version(optimized_html, url, user_profile)
        
        # Add to site tracker
        if optimized_dir:
            add_optimized_site(url, user_profile, optimized_dir)
        
        return jsonify({
            'success': True,
            'data': {
                'original_url': url,
                'user_profile': user_profile,
                'optimized_directory': optimized_dir
            },
            'message': f'Optimized version saved to: {optimized_dir}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/user-sites', methods=['GET'])
def get_user_sites():
    """
    API endpoint to get all sites scraped by a specific user
    """
    try:
        user_email = request.args.get('email')
        
        if not user_email:
            return jsonify({'success': False, 'error': 'Email parameter is required'}), 400
        
        # Get user's scraped sites
        user_sites = get_sites_by_user_email(user_email)
        
        return jsonify({
            'success': True,
            'sites': user_sites,
            'total_count': len(user_sites)
        })
        
    except Exception as e:
        print(f"Error fetching user sites: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

def create_optimized_version(scraped_data, url, user_profile):
    """
    Create an optimized version of the scraped website based on user profile
    """
    # This is a simplified optimization - you can expand this based on your needs
    title = scraped_data.get('title', 'Optimized Website')
    
    optimized_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Optimized for {user_profile}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        .optimization-info {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 4px solid #667eea;
        }}
        
        .original-content {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 1rem;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Optimized Website</h1>
            <p>Enhanced version optimized for: {user_profile}</p>
        </div>
        
        <div class="content">
            <div class="optimization-info">
                <h3>Optimization Details</h3>
                <p><strong>Original URL:</strong> {url}</p>
                <p><strong>User Profile:</strong> {user_profile}</p>
                <p><strong>Optimized On:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(scraped_data.get('links', []))}</div>
                    <div class="stat-label">Links Found</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(scraped_data.get('css_content', {}).get('inline_styles', []))}</div>
                    <div class="stat-label">Inline Styles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(scraped_data.get('css_content', {}).get('internal_stylesheets', []))}</div>
                    <div class="stat-label">Internal Stylesheets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(scraped_data.get('js_content', {}).get('inline_scripts', []))}</div>
                    <div class="stat-label">Inline Scripts</div>
                </div>
            </div>
            
            <h3>Original Content Preview</h3>
            <div class="original-content">
{scraped_data.get('html_content', 'No content available')[:2000]}...
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return optimized_html

def save_optimized_version(optimized_html, url, user_profile):
    """
    Save the optimized version to the optimized_sites folder
    """
    # Create optimized_sites directory if it doesn't exist
    optimized_dir = "optimized_sites"
    if not os.path.exists(optimized_dir):
        os.makedirs(optimized_dir)
    
    # Generate filename
    base_filename = get_safe_filename(url)
    site_dir = os.path.join(optimized_dir, f"{base_filename}_{user_profile}")
    
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)
    
    # Save optimized HTML
    html_file = os.path.join(site_dir, "index.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(optimized_html)
    
    # Save metadata
    metadata_file = os.path.join(site_dir, "metadata.json")
    metadata = {
        "original_url": url,
        "user_profile": user_profile,
        "optimized_at": datetime.now().isoformat(),
        "optimization_type": "general_enhancement"
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Optimized version saved to {site_dir}")
    return site_dir

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({'status': 'healthy', 'message': 'Web scraper server is running'})

@app.route('/api/files', methods=['GET'])
def list_files():
    """
    List all scraped and optimized files
    """
    try:
        scraped_files = []
        optimized_files = []
        
        # List scraped files
        if os.path.exists('scraped_sites'):
            for item in os.listdir('scraped_sites'):
                item_path = os.path.join('scraped_sites', item)
                if os.path.isdir(item_path):
                    scraped_files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'scraped'
                    })
        
        # List optimized files
        if os.path.exists('optimized_sites'):
            for item in os.listdir('optimized_sites'):
                item_path = os.path.join('optimized_sites', item)
                if os.path.isdir(item_path):
                    optimized_files.append({
                        'name': item,
                        'path': item_path,
                        'type': 'optimized'
                    })
        
        return jsonify({
            'success': True,
            'data': {
                'scraped_files': scraped_files,
                'optimized_files': optimized_files
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/tracker/stats', methods=['GET'])
def get_tracker_stats():
    """
    Get statistics from the site tracker
    """
    try:
        stats = get_site_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/tracker/summary', methods=['GET'])
def get_tracker_summary():
    """
    Get a human-readable summary of all tracked sites
    """
    try:
        summary = export_summary()
        return jsonify({
            'success': True,
            'data': {
                'summary': summary
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/tracker/sites', methods=['GET'])
def get_all_tracked_sites():
    """
    Get all tracked sites from the database
    """
    try:
        sites = get_all_sites()
        return jsonify({
            'success': True,
            'data': sites
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/sites', methods=['GET'])
def list_scraped_sites():
    """List all scraped site directories."""
    try:
        scraped_dir = 'scraped_sites'
        if not os.path.exists(scraped_dir):
            return jsonify({'success': True, 'sites': []})
        sites = [d for d in os.listdir(scraped_dir) if os.path.isdir(os.path.join(scraped_dir, d))]
        sites.sort(reverse=True)
        return jsonify({'success': True, 'sites': sites})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/report/<site>/<report_type>', methods=['GET'])
def get_report(site, report_type):
    """Serve a specific report file for a scraped site."""
    scraped_dir = os.path.join('scraped_sites', site)
    
    # Map report types to actual files
    if report_type == 'analysis':
        # For analysis, return the metadata.json restructured for dashboard compatibility
        file_path = os.path.join(scraped_dir, 'metadata.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                # Restructure data to match dashboard expectations
                seo_metadata = metadata.get('seo_metadata', {})
                analysis_data = {
                    'original_url': metadata.get('original_url'),
                    'scraped_at': metadata.get('scraped_at'),
                    'title': metadata.get('title'),
                    'stats': metadata.get('stats'),
                    'seo_metadata': seo_metadata,
                    # Flatten key metrics for dashboard compatibility
                    'word_count': seo_metadata.get('word_count', 0),
                    'top_keywords': seo_metadata.get('keyword_density', {}),
                    'page_speed_indicators': seo_metadata.get('page_speed_indicators', {})
                }
                return jsonify(analysis_data)
        else:
            return jsonify({'error': 'Analysis report not found'}), 404
    
    elif report_type == 'analytics':
        # For analytics, extract analytics data from metadata.json
        metadata_path = os.path.join(scraped_dir, 'metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                # Extract analytics data from SEO metadata
                seo_metadata = metadata.get('seo_metadata', {})
                analytics_data = {
                    'detailed_analytics': seo_metadata.get('detailed_analytics', {}),
                    'analytics': seo_metadata.get('analytics', [])
                }
                return jsonify(analytics_data)
        else:
            return jsonify({'error': 'Analytics report not found'}), 404
    
    elif report_type == 'metadata':
        file_path = os.path.join(scraped_dir, 'metadata.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({'error': 'Metadata not found'}), 404
    elif report_type == 'seo':
        file_path = os.path.join(scraped_dir, 'seo_report.txt')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify(f.read())
        else:
            return jsonify({'error': 'SEO report not found'}), 404
    
    else:
        return jsonify({'error': 'Invalid report type'}), 400



# Gambix Strata API Endpoints
@app.route('/api/gambix/users', methods=['POST'])
# @limiter.limit("10 per minute")  # Temporarily disabled
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        email = data.get('email')
        name = data.get('name')
        role = data.get('role', 'user')
        preferences = data.get('preferences')
        
        if not email or not name:
            return jsonify({'success': False, 'error': 'Email and name are required'}), 400
        
        db = GambixStrataDatabase()
        user_id = db.create_user(email, name, role, preferences)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User created successfully'
        })
    except Exception as e:
        app.logger.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': 'Failed to create user'}), 500

@app.route('/api/gambix/users/<email>', methods=['GET'])
def get_user_by_email(email):
    """Get user by email"""
    try:
        db = GambixStrataDatabase()
        user = db.get_user_by_email(email)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        })
    except Exception as e:
        app.logger.error(f"Error getting user: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user'}), 500

@app.route('/api/projects', methods=['POST'])
@require_auth
# @limiter.limit("10 per minute")  # Temporarily disabled
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        email = request.current_user['email']
        raw_domain = data.get('websiteUrl')  # Frontend sends websiteUrl
        
        # Normalize domain by removing protocol and www
        from urllib.parse import urlparse
        parsed = urlparse(raw_domain)
        domain = parsed.netloc.replace('www.', '') if parsed.netloc else raw_domain
        
        # Ensure domain is properly normalized (remove trailing slashes)
        domain = domain.rstrip('/')
        
        name = data.get('name') or domain  # Use domain as name if not provided
        category = data.get('category')
        description = data.get('description')
        
        # Create settings object with category and description
        settings = {
            'category': category,
            'description': description
        }
        
        if not domain:
            return jsonify({'success': False, 'error': 'Website URL is required'}), 400
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        user_id = user_data['user_id']
        
        project_id = db.create_project(user_id, domain, name, settings)
        
        # Automatically scrape the website after creating the project
        try:
            # Ensure domain has a protocol
            if not domain.startswith(('http://', 'https://')):
                domain_with_protocol = f"https://{domain}"
            else:
                domain_with_protocol = domain
            
            # Call the scraper function
            scraped_data = simple_web_scraper(domain_with_protocol)
            
            if scraped_data:
                # Save to S3 storage (production default)
                saved_location = None
                storage_type = None
                
                try:
                    # Use S3 storage for production
                    saved_location = save_content_to_s3(scraped_data, domain)
                    if saved_location:
                        storage_type = 's3'
                        app.logger.info(f"✅ Content saved to S3: {saved_location}")
                    else:
                        app.logger.warning(f"❌ Failed to save to S3 for {domain}")
                        saved_location = None
                except Exception as s3_error:
                    app.logger.error(f"❌ S3 storage failed for {domain}: {s3_error}")
                    saved_location = None
                
                if saved_location:
                    # Store the file path and storage type in the database
                    db.update_project_scraped_files(project_id, saved_location)
                    
                    # Update last_crawl timestamp
                    db.update_project_last_crawl(project_id)
                    
                    app.logger.info(f"Successfully scraped {domain} for project {project_id}, files saved to {storage_type}: {saved_location}")
                else:
                    app.logger.warning(f"Failed to save scraped files for {domain}")
            else:
                app.logger.warning(f"Failed to scrape {domain} for project {project_id}")
                
        except Exception as scrape_error:
            app.logger.error(f"Error during automatic scraping for project {project_id}: {scrape_error}")
            # Don't fail the project creation if scraping fails
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project_id,
                'message': 'Project created successfully and website scraped',
                'already_exists': False
            }
        })
    except Exception as e:
        app.logger.error(f"Error creating project: {e}")
        return jsonify({'success': False, 'error': 'Failed to create project'}), 500

@app.route('/api/projects', methods=['GET'])
@require_auth
# Removed rate limiting for frequently called endpoint
def get_user_projects():
    """Get all projects for current user"""
    try:
        email = request.current_user['email']
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        
        projects = db.get_user_projects(user_data['user_id'])
        
        # Transform projects to match frontend expectations
        transformed_projects = []
        for project in projects:
            transformed_project = {
                'id': project['project_id'],
                'url': project['domain'],
                'icon': 'fas fa-globe',
                'status': project['status'],
                'healthScore': project.get('overall_score', 0),
                'recommendations': 0,  # Will be calculated later
                'autoOptimize': project.get('auto_optimize', False),
                'lastUpdated': project.get('last_health_check', project['updated_at'])
            }
            transformed_projects.append(transformed_project)
        
        return jsonify({
            'success': True,
            'data': transformed_projects
        })
    except Exception as e:
        app.logger.error(f"Error getting user projects: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user projects'}), 500

@app.route('/api/gambix/projects/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id):
    """Get a single project by ID"""
    try:
        db = GambixStrataDatabase()
        project = db.get_project(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        return jsonify({
            'success': True,
            'data': project
        })
    except Exception as e:
        app.logger.error(f"Error getting project: {e}")
        return jsonify({'success': False, 'error': 'Failed to get project'}), 500

@app.route('/api/gambix/projects/<project_id>', methods=['DELETE'])
@require_auth
def delete_project(project_id):
    """Delete a project by ID"""
    try:
        email = request.current_user['email']
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        
        # Get the project to verify ownership
        project = db.get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Verify the project belongs to the current user
        if project['user_id'] != user_data['user_id']:
            return jsonify({'success': False, 'error': 'Unauthorized to delete this project'}), 403
        
        # Delete the project
        success = db.delete_project(project_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Project deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete project'}), 500
            
    except Exception as e:
        app.logger.error(f"Error deleting project: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete project'}), 500

@app.route('/api/gambix/projects/<project_id>/health', methods=['POST'])
# @limiter.limit("10 per minute")  # Temporarily disabled
def add_site_health(project_id):
    """Add site health metrics"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        db = GambixStrataDatabase()
        health_id = db.add_site_health(project_id, data)
        
        return jsonify({
            'success': True,
            'health_id': health_id,
            'message': 'Site health data added successfully'
        })
    except Exception as e:
        app.logger.error(f"Error adding site health: {e}")
        return jsonify({'success': False, 'error': 'Failed to add site health data'}), 500

@app.route('/api/gambix/projects/<project_id>/health', methods=['GET'])
def get_site_health(project_id):
    """Get site health data"""
    try:
        db = GambixStrataDatabase()
        health_data = db.get_latest_site_health(project_id)
        
        if not health_data:
            return jsonify({'success': False, 'error': 'No health data found'}), 404
        
        return jsonify({
            'success': True,
            'health_data': health_data
        })
    except Exception as e:
        app.logger.error(f"Error getting site health: {e}")
        return jsonify({'success': False, 'error': 'Failed to get site health data'}), 500

@app.route('/api/gambix/projects/<project_id>/scraped-data', methods=['GET'])
@require_auth
def get_project_scraped_data(project_id):
    """Get scraped data for a specific project from files"""
    try:
        db = GambixStrataDatabase()
        
        # Get project to verify ownership
        project = db.get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Verify project belongs to current user
        email = request.current_user['email']
        user_data = ensure_user_exists(email, request.current_user)
        if project['user_id'] != user_data['user_id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if project has scraped files
        scraped_files_path = project.get('scraped_files_path')
        if not scraped_files_path:
            return jsonify({
                'success': True,
                'data': {
                    'has_scraped_data': False,
                    'message': 'No scraped data available for this project'
                }
            })
        
        # Read scraped data from files
        try:
            # Handle both relative and absolute paths
            if scraped_files_path.startswith('s3://'):
                # S3 storage - we'll need to implement S3 file reading
                app.logger.warning(f"S3 storage not yet implemented for reading: {scraped_files_path}")
                return jsonify({
                    'success': True,
                    'data': {
                        'has_scraped_data': False,
                        'message': 'S3 storage reading not yet implemented'
                    }
                })
            else:
                # File path - resolve relative path to absolute
                if not os.path.isabs(scraped_files_path):
                    # If it's a relative path, make it absolute relative to the current working directory
                    scraped_files_path = os.path.abspath(scraped_files_path)
                
                app.logger.info(f"Reading scraped data from: {scraped_files_path}")
            
            # Read metadata.json
            metadata_path = os.path.join(scraped_files_path, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                app.logger.info(f"Successfully read metadata from: {metadata_path}")
            else:
                app.logger.warning(f"Metadata file not found: {metadata_path}")
                metadata = {}
            
            # Read seo_report.txt
            seo_report_path = os.path.join(scraped_files_path, 'seo_report.txt')
            seo_report = ""
            if os.path.exists(seo_report_path):
                with open(seo_report_path, 'r', encoding='utf-8') as f:
                    seo_report = f.read()
                app.logger.info(f"Successfully read SEO report from: {seo_report_path}")
            else:
                app.logger.warning(f"SEO report file not found: {seo_report_path}")
            
            # Extract key data from metadata
            seo_data = metadata.get('seo_metadata', {})
            
            scraped_data = {
                'has_scraped_data': True,
                'title': metadata.get('title', ''),
                'original_url': metadata.get('original_url', ''),
                'scraped_at': metadata.get('scraped_at', ''),
                'seo_report': seo_report,
                'word_count': seo_data.get('word_count', 0),
                'meta_description': seo_data.get('meta_description', ''),
                'images_count': len(seo_data.get('images', [])),
                'links_count': seo_data.get('links_count', 0),
                'h1_tags': seo_data.get('headings', {}).get('h1', []),
                'meta_tags': seo_data.get('meta_tags', {}),
                'stats': metadata.get('stats', {})
            }
            
            app.logger.info(f"Successfully processed scraped data for project {project_id}")
            return jsonify({
                'success': True,
                'data': scraped_data
            })
            
        except Exception as file_error:
            app.logger.error(f"Error reading scraped files: {file_error}")
            app.logger.error(f"Attempted path: {scraped_files_path}")
            return jsonify({
                'success': True,
                'data': {
                    'has_scraped_data': False,
                    'message': f'Error reading scraped data files: {str(file_error)}'
                }
            })
        
    except Exception as e:
        app.logger.error(f"Error getting project scraped data: {e}")
        return jsonify({'success': False, 'error': 'Failed to get project scraped data'}), 500

@app.route('/api/gambix/projects/<project_id>/pages', methods=['POST'])
# @limiter.limit("10 per minute")  # Temporarily disabled
def add_page(project_id):
    """Add a page to a project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        db = GambixStrataDatabase()
        page_id = db.add_page(project_id, data)
        
        return jsonify({
            'success': True,
            'page_id': page_id,
            'message': 'Page added successfully'
        })
    except Exception as e:
        app.logger.error(f"Error adding page: {e}")
        return jsonify({'success': False, 'error': 'Failed to add page'}), 500

@app.route('/api/gambix/projects/<project_id>/pages', methods=['GET'])
def get_project_pages(project_id):
    """Get all pages for a project"""
    try:
        db = GambixStrataDatabase()
        pages = db.get_project_pages(project_id)
        
        return jsonify({
            'success': True,
            'pages': pages
        })
    except Exception as e:
        app.logger.error(f"Error getting project pages: {e}")
        return jsonify({'success': False, 'error': 'Failed to get project pages'}), 500

@app.route('/api/gambix/projects/<project_id>/recommendations', methods=['POST'])
# @limiter.limit("10 per minute")  # Temporarily disabled
def add_recommendation(project_id):
    """Add a recommendation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        db = GambixStrataDatabase()
        recommendation_id = db.add_recommendation(project_id, data)
        
        return jsonify({
            'success': True,
            'recommendation_id': recommendation_id,
            'message': 'Recommendation added successfully'
        })
    except Exception as e:
        app.logger.error(f"Error adding recommendation: {e}")
        return jsonify({'success': False, 'error': 'Failed to add recommendation'}), 500

@app.route('/api/gambix/projects/<project_id>/recommendations', methods=['GET'])
def get_project_recommendations(project_id):
    """Get recommendations for a project"""
    try:
        status = request.args.get('status', 'pending')
        db = GambixStrataDatabase()
        recommendations = db.get_project_recommendations(project_id, status)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        app.logger.error(f"Error getting recommendations: {e}")
        return jsonify({'success': False, 'error': 'Failed to get recommendations'}), 500

@app.route('/api/gambix/recommendations/<recommendation_id>/status', methods=['PUT'])
def update_recommendation_status(recommendation_id):
    """Update recommendation status"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        status = data.get('status')
        if not status:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
        
        db = GambixStrataDatabase()
        db.update_recommendation_status(recommendation_id, status)
        
        return jsonify({
            'success': True,
            'message': 'Recommendation status updated successfully'
        })
    except Exception as e:
        app.logger.error(f"Error updating recommendation status: {e}")
        return jsonify({'success': False, 'error': 'Failed to update recommendation status'}), 500

@app.route('/api/gambix/alerts', methods=['POST'])
# @limiter.limit("10 per minute")  # Temporarily disabled
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        alert_data = {
            'project_id': data.get('project_id'),
            'type': data.get('type'),
            'title': data.get('title'),
            'description': data.get('description'),
            'priority': data.get('priority', 'medium'),
            'metadata': data.get('metadata')
        }
        
        if not user_id or not alert_data['title'] or not alert_data['description']:
            return jsonify({'success': False, 'error': 'User ID, title, and description are required'}), 400
        
        db = GambixStrataDatabase()
        alert_id = db.create_alert(user_id, alert_data)
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Alert created successfully'
        })
    except Exception as e:
        app.logger.error(f"Error creating alert: {e}")
        return jsonify({'success': False, 'error': 'Failed to create alert'}), 500

@app.route('/api/gambix/alerts/<user_id>', methods=['GET'])
def get_user_alerts(user_id):
    """Get alerts for a user"""
    try:
        status = request.args.get('status', 'active')
        db = GambixStrataDatabase()
        alerts = db.get_user_alerts(user_id, status)
        
        return jsonify({
            'success': True,
            'alerts': alerts
        })
    except Exception as e:
        app.logger.error(f"Error getting user alerts: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user alerts'}), 500

@app.route('/api/gambix/alerts/<alert_id>/dismiss', methods=['PUT'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    try:
        db = GambixStrataDatabase()
        db.dismiss_alert(alert_id)
        
        return jsonify({
            'success': True,
            'message': 'Alert dismissed successfully'
        })
    except Exception as e:
        app.logger.error(f"Error dismissing alert: {e}")
        return jsonify({'success': False, 'error': 'Failed to dismiss alert'}), 500

@app.route('/api/gambix/projects/<project_id>/statistics', methods=['GET'])
def get_project_statistics(project_id):
    """Get comprehensive statistics for a project"""
    try:
        db = GambixStrataDatabase()
        stats = db.get_project_statistics(project_id)
        
        if not stats:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        app.logger.error(f"Error getting project statistics: {e}")
        return jsonify({'success': False, 'error': 'Failed to get project statistics'}), 500

@app.route('/api/dashboard', methods=['GET'])
@require_auth
# Removed rate limiting for frequently called endpoint
def get_dashboard_data():
    """Get dashboard data for current user"""
    try:
        email = request.current_user['email']
        
        # Ensure user exists in database
        user_data = ensure_user_exists(email, request.current_user)
        
        dashboard_data = db.get_dashboard_data(user_data['user_id'])
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'success': False, 'error': 'Failed to get dashboard data'}), 500

@app.route('/api/gambix/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data_legacy(user_id):
    """Get dashboard data for a user (legacy endpoint)"""
    try:
        db = GambixStrataDatabase()
        dashboard_data = db.get_dashboard_data(user_id)
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'success': False, 'error': 'Failed to get dashboard data'}), 500

@app.route('/api/debug/project/<project_id>/files', methods=['GET'])
@require_auth
def debug_project_files(project_id):
    """Debug endpoint to check project file paths and existence"""
    try:
        db = GambixStrataDatabase()
        
        # Get project
        project = db.get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Verify project belongs to current user
        email = request.current_user['email']
        user_data = ensure_user_exists(email, request.current_user)
        if project['user_id'] != user_data['user_id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        scraped_files_path = project.get('scraped_files_path')
        
        debug_info = {
            'project_id': project_id,
            'project_name': project.get('name'),
            'domain': project.get('domain'),
            'scraped_files_path': scraped_files_path,
            'path_exists': False,
            'is_absolute': False,
            'current_working_dir': os.getcwd(),
            'files': []
        }
        
        if scraped_files_path:
            debug_info['is_absolute'] = os.path.isabs(scraped_files_path)
            
            # Resolve path
            if not os.path.isabs(scraped_files_path):
                resolved_path = os.path.abspath(scraped_files_path)
            else:
                resolved_path = scraped_files_path
            
            debug_info['resolved_path'] = resolved_path
            debug_info['path_exists'] = os.path.exists(resolved_path)
            
            if os.path.exists(resolved_path):
                # List files in directory
                try:
                    files = os.listdir(resolved_path)
                    debug_info['files'] = files
                    
                    # Check for specific files
                    metadata_path = os.path.join(resolved_path, 'metadata.json')
                    seo_report_path = os.path.join(resolved_path, 'seo_report.txt')
                    
                    debug_info['metadata_exists'] = os.path.exists(metadata_path)
                    debug_info['seo_report_exists'] = os.path.exists(seo_report_path)
                    
                except Exception as e:
                    debug_info['list_error'] = str(e)
        
        return jsonify({
            'success': True,
            'data': debug_info
        })
        
    except Exception as e:
        app.logger.error(f"Error in debug endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/gambix/projects/<project_id>/rescraper', methods=['POST'])
@require_auth
def rescrape_project(project_id):
    """Re-scrape a project if files are missing"""
    try:
        db = GambixStrataDatabase()
        
        # Get project to verify ownership
        project = db.get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Verify project belongs to current user
        email = request.current_user['email']
        user_data = ensure_user_exists(email, request.current_user)
        if project['user_id'] != user_data['user_id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        domain = project['domain']
        
        # Ensure domain has a protocol
        if not domain.startswith(('http://', 'https://')):
            domain_with_protocol = f"https://{domain}"
        else:
            domain_with_protocol = domain
        
        # Call the scraper function
        scraped_data = simple_web_scraper(domain_with_protocol)
        
        if scraped_data:
            # Save to S3 storage (production default)
            saved_location = None
            storage_type = None
            
            try:
                # Use S3 storage for production
                saved_location = save_content_to_s3(scraped_data, domain)
                if saved_location:
                    storage_type = 's3'
                    app.logger.info(f"✅ Content saved to S3: {saved_location}")
                else:
                    app.logger.warning(f"❌ Failed to save to S3 for {domain}")
                    saved_location = None
            except Exception as s3_error:
                app.logger.error(f"❌ S3 storage failed for {domain}: {s3_error}")
                saved_location = None
            
            if saved_location:
                # Store the file path and storage type in the database
                db.update_project_scraped_files(project_id, saved_location)
                
                # Update last_crawl timestamp
                db.update_project_last_crawl(project_id)
                
                app.logger.info(f"Successfully re-scraped {domain} for project {project_id}, files saved to {storage_type}: {saved_location}")
                
                return jsonify({
                    'success': True,
                    'message': f'Project re-scraped successfully. Files saved to {storage_type}.',
                    'saved_location': saved_location,
                    'storage_type': storage_type
                })
            else:
                app.logger.warning(f"Failed to save scraped files for {domain}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to save scraped files'
                }), 500
        else:
            app.logger.warning(f"Failed to scrape {domain} for project {project_id}")
            return jsonify({
                'success': False,
                'error': 'Failed to scrape the website'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error re-scraping project: {e}")
        return jsonify({'success': False, 'error': 'Failed to re-scrape project'}), 500

# Serve static files (HTML, CSS, JS) - Must be at the end
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path.startswith('api/'):
        # Let Flask routes handle API requests - return 404 if not handled
        return jsonify({'error': 'API endpoint not found'}), 404
    elif path.startswith('strata_design/') or path.startswith('static/'):
        # Let other routes handle static asset requests
        return app.send_static_file(path)
    return send_from_directory('strata_design', 'index.html')

if __name__ == '__main__':
    print("🌐 Starting Gambix Strata Web Scraper Server...")
    print(f"📱 Frontend will be available at: http://localhost:{PORT}")
    print(f"🔧 Legacy API endpoint: http://localhost:{PORT}/api/scrape")
    print(f"🚀 Optimize endpoint: http://localhost:{PORT}/api/optimize")
    print(f"📁 Files endpoint: http://localhost:{PORT}/api/files")
    print(f"📊 Tracker stats: http://localhost:{PORT}/api/tracker/stats")
    print(f"📋 Tracker summary: http://localhost:{PORT}/api/tracker/summary")
    print(f"💚 Health check: http://localhost:{PORT}/api/health")
    print(f"\n🎯 Gambix Strata API Endpoints:")
    print(f"   - Users: http://localhost:{PORT}/api/gambix/users")
    print(f"   - Projects: http://localhost:{PORT}/api/gambix/projects")
    print(f"   - Site Health: http://localhost:{PORT}/api/gambix/projects/<id>/health")
    print(f"   - Pages: http://localhost:{PORT}/api/gambix/projects/<id>/pages")
    print(f"   - Recommendations: http://localhost:{PORT}/api/gambix/projects/<id>/recommendations")
    print(f"   - Alerts: http://localhost:{PORT}/api/gambix/alerts")
    print(f"   - Dashboard: http://localhost:{PORT}/api/gambix/dashboard/<user_id>")
    print(f"\n📂 Storage Configuration:")
    print("   - Database: DynamoDB (gambix_strata_* tables)")
    print("   - Storage: S3 bucket (gambix-strata-production)")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=DEBUG, host=HOST, port=PORT) 