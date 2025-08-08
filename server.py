from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from main import simple_web_scraper, save_content_to_files, get_safe_filename
from database import GambixStrataDatabase, add_scraped_site, add_optimized_site, get_site_stats, export_summary, get_sites_by_user_email, get_all_sites
import json
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler

import sentry_sdk

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
    default_limits=["200 per day", "50 per hour"]
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

# Serve static files (HTML, CSS, JS)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path.startswith('api/') or path.startswith('strata_design/') or path.startswith('static/'):
        # Let other routes handle API and static asset requests
        return app.send_static_file(path)
    return send_from_directory('strata_design', 'index.html')

@app.route('/api/scrape', methods=['POST'])
@limiter.limit("10 per minute")  # Limit scraping requests
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
                # Save the scraped content to files
                saved_dir = save_content_to_files(scraped_data, url)
                
                # Add to site tracker
                if saved_dir:
                    add_scraped_site(url, scraped_data, saved_dir, user_email) # Pass user_email
                
                # Add the saved directory path to the response
                scraped_data['saved_directory'] = saved_dir
                
                return jsonify({
                    'success': True,
                    'data': scraped_data,
                    'message': f'Content saved to: {saved_dir}'
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
@limiter.limit("10 per minute")
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

@app.route('/api/gambix/projects', methods=['POST'])
@limiter.limit("10 per minute")
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        domain = data.get('domain')
        name = data.get('name')
        settings = data.get('settings')
        
        if not user_id or not domain or not name:
            return jsonify({'success': False, 'error': 'User ID, domain, and name are required'}), 400
        
        db = GambixStrataDatabase()
        project_id = db.create_project(user_id, domain, name, settings)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'message': 'Project created successfully'
        })
    except Exception as e:
        app.logger.error(f"Error creating project: {e}")
        return jsonify({'success': False, 'error': 'Failed to create project'}), 500

@app.route('/api/gambix/projects/<user_id>', methods=['GET'])
def get_user_projects(user_id):
    """Get all projects for a user"""
    try:
        db = GambixStrataDatabase()
        projects = db.get_user_projects(user_id)
        
        return jsonify({
            'success': True,
            'projects': projects
        })
    except Exception as e:
        app.logger.error(f"Error getting user projects: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user projects'}), 500

@app.route('/api/gambix/projects/<project_id>/health', methods=['POST'])
@limiter.limit("10 per minute")
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

@app.route('/api/gambix/projects/<project_id>/pages', methods=['POST'])
@limiter.limit("10 per minute")
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
@limiter.limit("10 per minute")
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
@limiter.limit("10 per minute")
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

@app.route('/api/gambix/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    """Get dashboard data for a user"""
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
    print(f"\n📂 Files will be saved to:")
    print("   - scraped_data/ (original scraped content)")
    print("   - optimized_sites/ (optimized versions)")
    print("   - data/gambix_strata.db (Gambix Strata SQLite database)")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=DEBUG, host=HOST, port=PORT) 