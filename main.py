import requests
from bs4 import BeautifulSoup
import collections
import re
import os
from urllib.parse import urlparse, urljoin
import json
from datetime import datetime

# Suppress the InsecureRequestWarning when using verify=False (not recommended for production)
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def calculate_tracking_intensity(analytics_data):
    """Calculate tracking intensity based on number of tools."""
    total_tools = (
        len(analytics_data.get('google_analytics', [])) +
        len(analytics_data.get('facebook_pixel', [])) +
        len(analytics_data.get('google_tag_manager', [])) +
        len(analytics_data.get('hotjar', [])) +
        len(analytics_data.get('mixpanel', [])) +
        len(analytics_data.get('other_tracking', []))
    )
    
    if total_tools == 0:
        return 'None'
    elif total_tools == 1:
        return 'Light'
    elif total_tools <= 3:
        return 'Moderate'
    elif total_tools <= 5:
        return 'Heavy'
    else:
        return 'Very Heavy'

def extract_seo_metadata(soup, url):
    """
    Extract comprehensive SEO metadata from a webpage.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        url (str): The original URL being scraped
        
    Returns:
        dict: Dictionary containing comprehensive SEO metadata
    """
    seo_data = {
        'meta_tags': {},
        'open_graph': {},
        'twitter_cards': {},
        'structured_data': [],
        'headings': {},
        'images': [],
        'internal_links': [],
        'external_links': [],
        'canonical_url': None,
        'robots_directive': None,
        'language': None,
        'charset': None,
        'viewport': None,
        'favicon': None,
        'sitemap': None,
        'rss_feeds': [],
        'social_links': [],
        'analytics': [],
        'word_count': 0,
        'keyword_density': {},
        'page_speed_indicators': {},
        'detailed_analytics': {}
    }
    
    # Extract meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name', meta.get('property', ''))
        content = meta.get('content', '')
        
        if name:
            seo_data['meta_tags'][name] = content
            
            # Categorize meta tags
            if name.startswith('og:'):
                seo_data['open_graph'][name] = content
            elif name.startswith('twitter:'):
                seo_data['twitter_cards'][name] = content
            elif name == 'robots':
                seo_data['robots_directive'] = content
            elif name == 'viewport':
                seo_data['viewport'] = content
            elif name == 'charset':
                seo_data['charset'] = content
            elif name == 'language':
                seo_data['language'] = content
    
    # Extract canonical URL
    canonical = soup.find('link', rel='canonical')
    if canonical:
        seo_data['canonical_url'] = canonical.get('href')
    
    # Extract favicon
    favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
    if favicon:
        seo_data['favicon'] = favicon.get('href')
    
    # Extract sitemap
    sitemap = soup.find('link', rel='sitemap')
    if sitemap:
        seo_data['sitemap'] = sitemap.get('href')
    
    # Extract RSS feeds
    for rss in soup.find_all('link', rel='alternate'):
        if rss.get('type') in ['application/rss+xml', 'application/atom+xml']:
            seo_data['rss_feeds'].append({
                'href': rss.get('href'),
                'title': rss.get('title'),
                'type': rss.get('type')
            })
    
    # Extract structured data (JSON-LD, Microdata, RDFa)
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            structured_data = json.loads(script.string)
            seo_data['structured_data'].append(structured_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Extract headings hierarchy
    for i in range(1, 7):
        headings = soup.find_all(f'h{i}')
        seo_data['headings'][f'h{i}'] = [h.get_text(strip=True) for h in headings]
    
    # Extract images with alt text and dimensions
    for img in soup.find_all('img'):
        img_data = {
            'src': img.get('src'),
            'alt': img.get('alt', ''),
            'title': img.get('title', ''),
            'width': img.get('width'),
            'height': img.get('height'),
            'loading': img.get('loading', ''),
            'decoding': img.get('decoding', '')
        }
        seo_data['images'].append(img_data)
    
    # Extract and categorize links
    base_url = urlparse(url)
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        link_text = link.get_text(strip=True)
        
        # Resolve relative URLs
        if href.startswith('/'):
            full_url = urljoin(url, href)
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = urljoin(url, href)
        
        link_data = {
            'href': href,
            'full_url': full_url,
            'text': link_text,
            'title': link.get('title', ''),
            'rel': link.get('rel', []),
            'target': link.get('target', '')
        }
        
        # Categorize links
        link_parsed = urlparse(full_url)
        if link_parsed.netloc == base_url.netloc:
            seo_data['internal_links'].append(link_data)
        else:
            seo_data['external_links'].append(link_data)
            
            # Detect social media links
            social_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
                            'youtube.com', 'tiktok.com', 'pinterest.com', 'reddit.com']
            if any(social in link_parsed.netloc for social in social_domains):
                seo_data['social_links'].append(link_data)
    
    # Extract analytics and tracking scripts
    analytics_patterns = ['google-analytics', 'gtag', 'ga(', 'googletagmanager', 
                         'facebook', 'fbq', 'pixel', 'hotjar', 'mixpanel']
    
    for script in soup.find_all('script'):
        script_content = script.string or ''
        script_src = script.get('src', '')
        
        for pattern in analytics_patterns:
            if pattern in script_content.lower() or pattern in script_src.lower():
                seo_data['analytics'].append({
                    'type': pattern,
                    'src': script_src,
                    'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content
                })
                break
    
    # Extract detailed analytics data
    seo_data['detailed_analytics'] = extract_analytics_data(soup, url)
    
    # Calculate word count and keyword density
    text_content = soup.get_text()
    words = re.findall(r'\b\w+\b', text_content.lower())
    seo_data['word_count'] = len(words)
    
    # Calculate keyword density (top 20 words)
    word_freq = collections.Counter(words)
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs'}
    
    filtered_words = {word: count for word, count in word_freq.items() 
                     if word not in stop_words and len(word) > 2}
    
    # Get top 20 keywords by frequency
    top_keywords = dict(sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:20])
    seo_data['keyword_density'] = top_keywords
    
    # Page speed indicators
    seo_data['page_speed_indicators'] = {
        'total_images': len(seo_data['images']),
        'images_without_alt': len([img for img in seo_data['images'] if not img['alt']]),
        'total_scripts': len(soup.find_all('script')),
        'total_stylesheets': len(soup.find_all('link', rel='stylesheet')),
        'inline_styles': len(soup.find_all(attrs={'style': True})),
        'total_links': len(seo_data['internal_links']) + len(seo_data['external_links'])
    }
    
    return seo_data

def simple_web_scraper(url):
    """
    A web scraper that fetches the content of a URL and extracts HTML, CSS, JS, links, and SEO metadata.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        dict: A dictionary containing the page title, HTML content, CSS content, 
              JavaScript content, links, and comprehensive SEO metadata.
              Returns None if there's an error fetching the page.
    """
    print(f"Attempting to scrape: {url}")  
    try:
        # Send a GET request to the URL.
        # verify=False is used here to bypass SSL certificate verification for simplicity.
        # In a production environment, you should handle SSL certificates properly.
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the page title
        page_title = soup.title.string if soup.title else "No title found"

        # Extract HTML content
        html_content = response.text

        # Extract CSS content
        css_content = []
        
        # Get inline styles from style attributes
        inline_styles = []
        for element in soup.find_all(attrs={'style': True}):
            inline_styles.append(element['style'])
        
        # Get internal stylesheets
        internal_styles = []
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                internal_styles.append(style_tag.string)
        
        # Get external stylesheets
        external_stylesheets = []
        for link_tag in soup.find_all('link', rel='stylesheet'):
            if link_tag.get('href'):
                external_stylesheets.append(link_tag['href'])
        
        css_content = {
            'inline_styles': inline_styles,
            'internal_stylesheets': internal_styles,
            'external_stylesheets': external_stylesheets
        }

        # Extract JavaScript content
        js_content = []
        
        # Get inline scripts
        inline_scripts = []
        for script_tag in soup.find_all('script'):
            if script_tag.string:
                inline_scripts.append(script_tag.string)
        
        # Get external scripts
        external_scripts = []
        for script_tag in soup.find_all('script', src=True):
            external_scripts.append(script_tag['src'])
        
        js_content = {
            'inline_scripts': inline_scripts,
            'external_scripts': external_scripts
        }

        # Find all 'a' (anchor) tags and extract their 'href' attribute
        links = []
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            links.append(link)

        # Extract comprehensive SEO metadata with error handling
        try:
            seo_metadata = extract_seo_metadata(soup, url)
        except Exception as seo_error:
            print(f"Warning: Error extracting SEO metadata: {seo_error}")
            # Provide a basic SEO metadata structure if extraction fails
            seo_metadata = {
                'meta_tags': {},
                'open_graph': {},
                'twitter_cards': {},
                'structured_data': [],
                'headings': {},
                'images': [],
                'internal_links': [],
                'external_links': [],
                'canonical_url': None,
                'robots_directive': None,
                'language': None,
                'charset': None,
                'viewport': None,
                'favicon': None,
                'sitemap': None,
                'rss_feeds': [],
                'social_links': [],
                'analytics': [],
                'word_count': 0,
                'keyword_density': {},
                'page_speed_indicators': {},
                'detailed_analytics': {}
            }

        print(f"Successfully scraped: {url}")
        return {
            "title": page_title,
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "links": links,
            "seo_metadata": seo_metadata
        }

    except requests.exceptions.Timeout:
        print(f"Error: Timeout while fetching {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Error: Connection error while fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} while fetching {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while scraping {url}: {e}")
        return None

def get_safe_filename(url):
    """
    Convert a URL to a safe filename for saving files.
    
    Args:
        url (str): The URL to convert
        
    Returns:
        str: A safe filename
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.replace('/', '_').replace('\\', '_')
    if not path or path == '_':
        path = 'home'
    else:
        path = path.lstrip('_')
    
    # Add timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{domain}_{path}_{timestamp}"

def save_content_to_files(scraped_data, url, base_filename=None):
    """
    Save the scraped content to separate files in the scraped_sites folder.
    
    Args:
        scraped_data (dict): The scraped data dictionary
        url (str): The original URL that was scraped
        base_filename (str): Optional base filename, if not provided will be generated from URL
    """
    if not scraped_data:
        print("No data to save.")
        return None
    
    # Create scraped_sites directory if it doesn't exist
    scraped_dir = "scraped_sites"
    if not os.path.exists(scraped_dir):
        os.makedirs(scraped_dir)
    
    # Generate filename from URL if not provided
    if not base_filename:
        base_filename = get_safe_filename(url)
    
    # Create a subdirectory for this specific scrape
    site_dir = os.path.join(scraped_dir, base_filename)
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)
    
    # Save HTML content
    html_file = os.path.join(site_dir, "index.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(scraped_data['html_content'])
    print(f"HTML content saved to {html_file}")
    
    # Save CSS content
    css_file = os.path.join(site_dir, "styles.css")
    with open(css_file, "w", encoding="utf-8") as f:
        f.write("/* === INLINE STYLES === */\n")
        for i, style in enumerate(scraped_data['css_content']['inline_styles']):
            f.write(f"\n/* --- Inline Style {i+1} --- */\n")
            f.write(style)
            f.write("\n")
        
        f.write("\n\n/* === INTERNAL STYLESHEETS === */\n")
        for i, style in enumerate(scraped_data['css_content']['internal_stylesheets']):
            f.write(f"\n/* --- Internal Stylesheet {i+1} --- */\n")
            f.write(style)
            f.write("\n")
        
        f.write("\n\n/* === EXTERNAL STYLESHEETS === */\n")
        for i, link in enumerate(scraped_data['css_content']['external_stylesheets']):
            f.write(f"/* {i+1}. {link} */\n")
    
    print(f"CSS content saved to {css_file}")
    
    # Save JavaScript content
    js_file = os.path.join(site_dir, "scripts.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write("// === INLINE SCRIPTS ===\n")
        for i, script in enumerate(scraped_data['js_content']['inline_scripts']):
            f.write(f"\n// --- Inline Script {i+1} ---\n")
            f.write(script)
            f.write("\n")
        
        f.write("\n\n// === EXTERNAL SCRIPTS ===\n")
        for i, link in enumerate(scraped_data['js_content']['external_scripts']):
            f.write(f"// {i+1}. {link}\n")
    
    print(f"JavaScript content saved to {js_file}")
    
    # Save links
    links_file = os.path.join(site_dir, "links.txt")
    with open(links_file, "w", encoding="utf-8") as f:
        f.write(f"Links found on: {url}\n")
        f.write(f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for i, link in enumerate(scraped_data['links'], 1):
            f.write(f"{i}. {link}\n")
    
    print(f"Links saved to {links_file}")
    
    # Save metadata as JSON
    metadata_file = os.path.join(site_dir, "metadata.json")
    metadata = {
        "original_url": url,
        "scraped_at": datetime.now().isoformat(),
        "title": scraped_data['title'],
        "stats": {
            "links_count": len(scraped_data['links']),
            "inline_styles_count": len(scraped_data['css_content']['inline_styles']),
            "internal_stylesheets_count": len(scraped_data['css_content']['internal_stylesheets']),
            "external_stylesheets_count": len(scraped_data['css_content']['external_stylesheets']),
            "inline_scripts_count": len(scraped_data['js_content']['inline_scripts']),
            "external_scripts_count": len(scraped_data['js_content']['external_scripts'])
        },
        "seo_metadata": scraped_data.get('seo_metadata', {})
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to {metadata_file}")
    
    # Save detailed SEO report
    seo_report_file = os.path.join(site_dir, "seo_report.txt")
    with open(seo_report_file, "w", encoding="utf-8") as f:
        f.write(f"SEO Analysis Report for: {url}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        seo_data = scraped_data.get('seo_metadata', {})
        
        # Basic SEO Info
        f.write("BASIC SEO INFORMATION\n")
        f.write("-" * 40 + "\n")
        f.write(f"Title: {scraped_data['title']}\n")
        f.write(f"Canonical URL: {seo_data.get('canonical_url', 'Not found')}\n")
        f.write(f"Robots Directive: {seo_data.get('robots_directive', 'Not found')}\n")
        f.write(f"Language: {seo_data.get('language', 'Not specified')}\n")
        f.write(f"Charset: {seo_data.get('charset', 'Not specified')}\n")
        f.write(f"Viewport: {seo_data.get('viewport', 'Not specified')}\n")
        f.write(f"Favicon: {seo_data.get('favicon', 'Not found')}\n")
        f.write(f"Sitemap: {seo_data.get('sitemap', 'Not found')}\n\n")
        
        # Meta Tags
        f.write("META TAGS\n")
        f.write("-" * 40 + "\n")
        for name, content in seo_data.get('meta_tags', {}).items():
            f.write(f"{name}: {content}\n")
        f.write("\n")
        
        # Open Graph
        if seo_data.get('open_graph'):
            f.write("OPEN GRAPH TAGS\n")
            f.write("-" * 40 + "\n")
            for name, content in seo_data['open_graph'].items():
                f.write(f"{name}: {content}\n")
            f.write("\n")
        
        # Twitter Cards
        if seo_data.get('twitter_cards'):
            f.write("TWITTER CARD TAGS\n")
            f.write("-" * 40 + "\n")
            for name, content in seo_data['twitter_cards'].items():
                f.write(f"{name}: {content}\n")
            f.write("\n")
        
        # Headings Structure
        f.write("HEADINGS STRUCTURE\n")
        f.write("-" * 40 + "\n")
        for level in range(1, 7):
            headings = seo_data.get('headings', {}).get(f'h{level}', [])
            if headings:
                f.write(f"H{level} Headings ({len(headings)}):\n")
                for i, heading in enumerate(headings, 1):
                    f.write(f"  {i}. {heading}\n")
                f.write("\n")
        
        # Images Analysis
        f.write("IMAGES ANALYSIS\n")
        f.write("-" * 40 + "\n")
        images = seo_data.get('images', [])
        f.write(f"Total Images: {len(images)}\n")
        images_without_alt = len([img for img in images if not img['alt']])
        f.write(f"Images without Alt Text: {images_without_alt}\n")
        f.write(f"Alt Text Coverage: {((len(images) - images_without_alt) / len(images) * 100):.1f}%\n\n")
        
        # Links Analysis
        f.write("LINKS ANALYSIS\n")
        f.write("-" * 40 + "\n")
        internal_links = seo_data.get('internal_links', [])
        external_links = seo_data.get('external_links', [])
        social_links = seo_data.get('social_links', [])
        
        f.write(f"Internal Links: {len(internal_links)}\n")
        f.write(f"External Links: {len(external_links)}\n")
        f.write(f"Social Media Links: {len(social_links)}\n")
        f.write(f"Total Links: {len(internal_links) + len(external_links)}\n\n")
        
        # Content Analysis
        f.write("CONTENT ANALYSIS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Word Count: {seo_data.get('word_count', 0):,}\n")
        
        # Keyword Density
        keywords = seo_data.get('keyword_density', {})
        if keywords:
            f.write("Top Keywords (by frequency):\n")
            for i, (word, count) in enumerate(list(keywords.items())[:10], 1):
                f.write(f"  {i}. {word}: {count} times\n")
        f.write("\n")
        
        # Analytics Detection
        analytics = seo_data.get('analytics', [])
        if analytics:
            f.write("ANALYTICS & TRACKING\n")
            f.write("-" * 40 + "\n")
            for analytic in analytics:
                f.write(f"Type: {analytic['type']}\n")
                if analytic['src']:
                    f.write(f"Source: {analytic['src']}\n")
                f.write("\n")
        
        # Page Speed Indicators
        speed_indicators = seo_data.get('page_speed_indicators', {})
        f.write("PAGE SPEED INDICATORS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Scripts: {speed_indicators.get('total_scripts', 0)}\n")
        f.write(f"Total Stylesheets: {speed_indicators.get('total_stylesheets', 0)}\n")
        f.write(f"Inline Styles: {speed_indicators.get('inline_styles', 0)}\n")
        f.write(f"Total Links: {speed_indicators.get('total_links', 0)}\n")
        f.write(f"Total Images: {speed_indicators.get('total_images', 0)}\n")
        f.write(f"Images without Alt: {speed_indicators.get('images_without_alt', 0)}\n\n")
        
        # Structured Data
        structured_data = seo_data.get('structured_data', [])
        if structured_data:
            f.write("STRUCTURED DATA\n")
            f.write("-" * 40 + "\n")
            f.write(f"Found {len(structured_data)} structured data blocks\n")
            for i, data in enumerate(structured_data, 1):
                f.write(f"Block {i}: {type(data).__name__}\n")
        f.write("\n")
        
        # RSS Feeds
        rss_feeds = seo_data.get('rss_feeds', [])
        if rss_feeds:
            f.write("RSS FEEDS\n")
            f.write("-" * 40 + "\n")
            for feed in rss_feeds:
                f.write(f"Type: {feed['type']}\n")
                f.write(f"Title: {feed['title']}\n")
                f.write(f"URL: {feed['href']}\n\n")
    
    print(f"SEO Report saved to {seo_report_file}")
    
    return site_dir

def analyze_scraped_content(scraped_data):
    """
    Analyze and categorize the scraped content to provide insights about what was extracted.
    
    Args:
        scraped_data (dict): The scraped data dictionary
        
    Returns:
        dict: Analysis results with categorizations and insights
    """
    analysis = {
        'content_overview': {},
        'seo_analysis': {},
        'technical_analysis': {},
        'content_categorization': {},
        'link_analysis': {},
        'media_analysis': {},
        'performance_insights': {},
        'recommendations': []
    }
    
    # Content Overview
    html_content = scraped_data.get('html_content', '')
    analysis['content_overview'] = {
        'total_characters': len(html_content),
        'total_words': len(html_content.split()),
        'content_size_mb': len(html_content.encode('utf-8')) / (1024 * 1024),
        'title': scraped_data.get('title', 'No title'),
        'has_title': bool(scraped_data.get('title')),
        'title_length': len(scraped_data.get('title', '')),
        'title_optimal': 50 <= len(scraped_data.get('title', '')) <= 60
    }
    
    # SEO Analysis
    seo_data = scraped_data.get('seo_metadata', {})
    analysis['seo_analysis'] = {
        'meta_tags_count': len(seo_data.get('meta_tags', {})),
        'open_graph_tags': len(seo_data.get('open_graph', {})),
        'twitter_cards': len(seo_data.get('twitter_cards', {})),
        'structured_data_blocks': len(seo_data.get('structured_data', [])),
        'canonical_url': bool(seo_data.get('canonical_url')),
        'robots_directive': bool(seo_data.get('robots_directive')),
        'favicon': bool(seo_data.get('favicon')),
        'sitemap': bool(seo_data.get('sitemap')),
        'word_count': seo_data.get('word_count', 0),
        'content_richness': 'High' if seo_data.get('word_count', 0) > 1000 else 'Medium' if seo_data.get('word_count', 0) > 300 else 'Low'
    }
    
    # Technical Analysis
    css_data = scraped_data.get('css_content', {})
    js_data = scraped_data.get('js_content', {})
    analysis['technical_analysis'] = {
        'inline_styles': len(css_data.get('inline_styles', [])),
        'internal_stylesheets': len(css_data.get('internal_stylesheets', [])),
        'external_stylesheets': len(css_data.get('external_stylesheets', [])),
        'inline_scripts': len(js_data.get('inline_scripts', [])),
        'external_scripts': len(js_data.get('external_scripts', [])),
        'total_scripts': len(js_data.get('inline_scripts', [])) + len(js_data.get('external_scripts', [])),
        'total_styles': len(css_data.get('inline_styles', [])) + len(css_data.get('internal_stylesheets', [])) + len(css_data.get('external_stylesheets', [])),
        'uses_external_resources': bool(css_data.get('external_stylesheets') or js_data.get('external_scripts')),
        'has_inline_code': bool(css_data.get('inline_styles') or js_data.get('inline_scripts'))
    }
    
    # Content Categorization
    headings = seo_data.get('headings', {})
    total_headings = sum(len(h) for h in headings.values())
    
    # Analyze heading structure
    heading_structure = {}
    for level in range(1, 7):
        count = len(headings.get(f'h{level}', []))
        if count > 0:
            heading_structure[f'H{level}'] = count
    
    # Determine content type based on structure
    content_type = 'Unknown'
    if total_headings == 0:
        content_type = 'Simple Page'
    elif len(headings.get('h1', [])) == 1 and total_headings <= 5:
        content_type = 'Landing Page'
    elif total_headings > 10:
        content_type = 'Content-Rich Page'
    elif len(headings.get('h2', [])) > 3:
        content_type = 'Article/Blog Post'
    elif len(headings.get('h3', [])) > 5:
        content_type = 'Product/Service Page'
    
    analysis['content_categorization'] = {
        'content_type': content_type,
        'heading_structure': heading_structure,
        'total_headings': total_headings,
        'has_h1': bool(headings.get('h1')),
        'has_h2': bool(headings.get('h2')),
        'has_h3': bool(headings.get('h3')),
        'heading_hierarchy_optimal': len(headings.get('h1', [])) == 1 and len(headings.get('h2', [])) > 0,
        'content_depth': 'Deep' if total_headings > 15 else 'Medium' if total_headings > 5 else 'Shallow'
    }
    
    # Link Analysis
    internal_links = seo_data.get('internal_links', [])
    external_links = seo_data.get('external_links', [])
    social_links = seo_data.get('social_links', [])
    
    # Categorize links by type
    link_categories = {
        'navigation': [],
        'content': [],
        'social': [],
        'external_references': [],
        'calls_to_action': []
    }
    
    for link in internal_links + external_links:
        text = link.get('text', '').lower()
        href = link.get('href', '').lower()
        
        # Categorize based on text and URL patterns
        if any(word in text for word in ['home', 'menu', 'about', 'contact', 'services']):
            link_categories['navigation'].append(link)
        elif any(word in text for word in ['read more', 'learn more', 'click here', 'view']):
            link_categories['calls_to_action'].append(link)
        elif any(word in href for word in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']):
            link_categories['social'].append(link)
        elif link in external_links:
            link_categories['external_references'].append(link)
        else:
            link_categories['content'].append(link)
    
    analysis['link_analysis'] = {
        'total_links': len(internal_links) + len(external_links),
        'internal_links': len(internal_links),
        'external_links': len(external_links),
        'social_links': len(social_links),
        'link_categories': {k: len(v) for k, v in link_categories.items()},
        'link_distribution': {
            'internal_ratio': len(internal_links) / max(len(internal_links) + len(external_links), 1),
            'external_ratio': len(external_links) / max(len(internal_links) + len(external_links), 1),
            'social_ratio': len(social_links) / max(len(internal_links) + len(external_links), 1)
        },
        'has_social_presence': bool(social_links),
        'link_quality': 'Good' if len(internal_links) > len(external_links) else 'Needs Improvement'
    }
    
    # Media Analysis
    images = seo_data.get('images', [])
    images_with_alt = len([img for img in images if img.get('alt')])
    images_without_alt = len(images) - images_with_alt
    
    analysis['media_analysis'] = {
        'total_images': len(images),
        'images_with_alt': images_with_alt,
        'images_without_alt': images_without_alt,
        'alt_text_coverage': (images_with_alt / len(images) * 100) if images else 0,
        'lazy_loading_images': len([img for img in images if img.get('loading') == 'lazy']),
        'responsive_images': len([img for img in images if img.get('width') and img.get('height')]),
        'media_richness': 'High' if len(images) > 10 else 'Medium' if len(images) > 3 else 'Low',
        'seo_optimized_images': images_with_alt / len(images) if images else 0
    }
    
    # Performance Insights
    speed_indicators = seo_data.get('page_speed_indicators', {})
    analysis['performance_insights'] = {
        'total_scripts': speed_indicators.get('total_scripts', 0),
        'total_stylesheets': speed_indicators.get('total_stylesheets', 0),
        'inline_styles': speed_indicators.get('inline_styles', 0),
        'total_images': speed_indicators.get('total_images', 0),
        'images_without_alt': speed_indicators.get('images_without_alt', 0),
        'performance_score': calculate_performance_score(speed_indicators),
        'optimization_opportunities': identify_optimization_opportunities(speed_indicators, seo_data)
    }
    
    # Generate Recommendations
    analysis['recommendations'] = generate_recommendations(analysis)
    
    return analysis

def calculate_performance_score(speed_indicators):
    """Calculate a performance score based on various indicators."""
    score = 100
    
    # Deduct points for performance issues
    if speed_indicators.get('total_scripts', 0) > 20:
        score -= 20
    elif speed_indicators.get('total_scripts', 0) > 10:
        score -= 10
    
    if speed_indicators.get('inline_styles', 0) > 50:
        score -= 15
    elif speed_indicators.get('inline_styles', 0) > 20:
        score -= 7
    
    if speed_indicators.get('images_without_alt', 0) > 0:
        score -= 10
    
    return max(score, 0)

def identify_optimization_opportunities(speed_indicators, seo_data):
    """Identify specific optimization opportunities."""
    opportunities = []
    
    if speed_indicators.get('total_scripts', 0) > 15:
        opportunities.append("Consider reducing the number of scripts")
    
    if speed_indicators.get('inline_styles', 0) > 30:
        opportunities.append("Move inline styles to external stylesheets")
    
    if speed_indicators.get('images_without_alt', 0) > 0:
        opportunities.append("Add alt text to all images for better SEO")
    
    if seo_data.get('word_count', 0) < 300:
        opportunities.append("Consider adding more content for better SEO")
    
    if not seo_data.get('canonical_url'):
        opportunities.append("Add canonical URL to prevent duplicate content issues")
    
    if not seo_data.get('sitemap'):
        opportunities.append("Consider adding a sitemap for better search engine indexing")
    
    return opportunities

def generate_recommendations(analysis):
    """Generate actionable recommendations based on analysis."""
    recommendations = []
    
    # SEO Recommendations
    if analysis['seo_analysis']['word_count'] < 300:
        recommendations.append("📝 Add more content - aim for at least 300 words for better SEO")
    
    if not analysis['seo_analysis']['canonical_url']:
        recommendations.append("🔗 Add canonical URL to prevent duplicate content issues")
    
    if analysis['media_analysis']['alt_text_coverage'] < 80:
        recommendations.append("🖼️ Improve image alt text coverage - aim for 100%")
    
    if not analysis['seo_analysis']['favicon']:
        recommendations.append("🎨 Add a favicon for better brand recognition")
    
    # Performance Recommendations
    if analysis['performance_insights']['total_scripts'] > 15:
        recommendations.append("⚡ Reduce number of scripts to improve page load speed")
    
    if analysis['performance_insights']['inline_styles'] > 30:
        recommendations.append("🎨 Move inline styles to external stylesheets")
    
    # Content Recommendations
    if not analysis['content_categorization']['heading_hierarchy_optimal']:
        recommendations.append("📋 Optimize heading hierarchy - use one H1 and proper H2-H6 structure")
    
    if analysis['link_analysis']['link_distribution']['external_ratio'] > 0.5:
        recommendations.append("🔗 Balance internal vs external links - prioritize internal linking")
    
    if analysis['seo_analysis']['content_richness'] == 'Low':
        recommendations.append("📚 Enhance content depth with more detailed information")
    
    # Social Media Recommendations
    if not analysis['link_analysis']['has_social_presence']:
        recommendations.append("📱 Add social media links for better engagement")
    
    return recommendations

def print_detailed_analysis(analysis):
    """Print a detailed analysis of the scraped content."""
    print("\n" + "="*80)
    print("📊 DETAILED CONTENT ANALYSIS & CATEGORIZATION")
    print("="*80)
    
    # Content Overview
    print("\n📋 CONTENT OVERVIEW")
    print("-" * 40)
    overview = analysis['content_overview']
    print(f"Content Type: {overview['content_size_mb']:.2f} MB")
    print(f"Total Characters: {overview['total_characters']:,}")
    print(f"Total Words: {overview['total_words']:,}")
    print(f"Title: '{overview['title']}' ({overview['title_length']} chars)")
    print(f"Title Optimal: {'✅' if overview['title_optimal'] else '❌'}")
    
    # SEO Analysis
    print("\n🔍 SEO ANALYSIS")
    print("-" * 40)
    seo = analysis['seo_analysis']
    print(f"Content Richness: {seo['content_richness']}")
    print(f"Word Count: {seo['word_count']:,}")
    print(f"Meta Tags: {seo['meta_tags_count']}")
    print(f"Open Graph Tags: {seo['open_graph_tags']}")
    print(f"Twitter Cards: {seo['twitter_cards']}")
    print(f"Structured Data: {seo['structured_data_blocks']} blocks")
    print(f"Canonical URL: {'✅' if seo['canonical_url'] else '❌'}")
    print(f"Robots Directive: {'✅' if seo['robots_directive'] else '❌'}")
    print(f"Favicon: {'✅' if seo['favicon'] else '❌'}")
    print(f"Sitemap: {'✅' if seo['sitemap'] else '❌'}")
    
    # Content Categorization
    print("\n📂 CONTENT CATEGORIZATION")
    print("-" * 40)
    content = analysis['content_categorization']
    print(f"Content Type: {content['content_type']}")
    print(f"Content Depth: {content['content_depth']}")
    print(f"Total Headings: {content['total_headings']}")
    print(f"Heading Structure: {content['heading_structure']}")
    print(f"Has H1: {'✅' if content['has_h1'] else '❌'}")
    print(f"Has H2: {'✅' if content['has_h2'] else '❌'}")
    print(f"Has H3: {'✅' if content['has_h3'] else '❌'}")
    print(f"Heading Hierarchy Optimal: {'✅' if content['heading_hierarchy_optimal'] else '❌'}")
    
    # Link Analysis
    print("\n🔗 LINK ANALYSIS")
    print("-" * 40)
    links = analysis['link_analysis']
    print(f"Total Links: {links['total_links']}")
    print(f"Internal Links: {links['internal_links']}")
    print(f"External Links: {links['external_links']}")
    print(f"Social Links: {links['social_links']}")
    print(f"Link Quality: {links['link_quality']}")
    print(f"Social Presence: {'✅' if links['has_social_presence'] else '❌'}")
    print(f"Link Categories:")
    for category, count in links['link_categories'].items():
        print(f"  - {category.replace('_', ' ').title()}: {count}")
    
    # Media Analysis
    print("\n🖼️ MEDIA ANALYSIS")
    print("-" * 40)
    media = analysis['media_analysis']
    print(f"Total Images: {media['total_images']}")
    print(f"Images with Alt Text: {media['images_with_alt']}")
    print(f"Images without Alt Text: {media['images_without_alt']}")
    print(f"Alt Text Coverage: {media['alt_text_coverage']:.1f}%")
    print(f"Lazy Loading Images: {media['lazy_loading_images']}")
    print(f"Responsive Images: {media['responsive_images']}")
    print(f"Media Richness: {media['media_richness']}")
    
    # Technical Analysis
    print("\n⚙️ TECHNICAL ANALYSIS")
    print("-" * 40)
    tech = analysis['technical_analysis']
    print(f"Total Scripts: {tech['total_scripts']}")
    print(f"Total Styles: {tech['total_styles']}")
    print(f"External Resources: {'✅' if tech['uses_external_resources'] else '❌'}")
    print(f"Inline Code: {'✅' if tech['has_inline_code'] else '❌'}")
    print(f"External Stylesheets: {tech['external_stylesheets']}")
    print(f"External Scripts: {tech['external_scripts']}")
    
    # Performance Insights
    print("\n⚡ PERFORMANCE INSIGHTS")
    print("-" * 40)
    perf = analysis['performance_insights']
    print(f"Performance Score: {perf['performance_score']}/100")
    print(f"Total Scripts: {perf['total_scripts']}")
    print(f"Total Stylesheets: {perf['total_stylesheets']}")
    print(f"Inline Styles: {perf['inline_styles']}")
    print(f"Images without Alt: {perf['images_without_alt']}")
    
    if perf['optimization_opportunities']:
        print(f"\nOptimization Opportunities:")
        for opportunity in perf['optimization_opportunities']:
            print(f"  • {opportunity}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    if analysis['recommendations']:
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"{i}. {rec}")
    else:
        print("✅ No major issues found! The page appears to be well-optimized.")
    
    print("\n" + "="*80)

def extract_analytics_data(soup, url):
    """
    Extract detailed analytics and tracking information from a webpage.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        url (str): The original URL being scraped
        
    Returns:
        dict: Detailed analytics information
    """
    analytics_data = {
        'google_analytics': [],
        'facebook_pixel': [],
        'google_tag_manager': [],
        'hotjar': [],
        'mixpanel': [],
        'other_tracking': [],
        'social_media_tracking': [],
        'ecommerce_tracking': [],
        'conversion_tracking': [],
        'heatmap_tracking': [],
        'session_recording': [],
        'analytics_summary': {}
    }
    
    # Extract all script tags
    scripts = soup.find_all('script')
    
    for script in scripts:
        script_content = script.string or ''
        script_src = script.get('src', '')
        
        # Google Analytics (GA4 and Universal Analytics)
        if 'gtag' in script_content or 'ga(' in script_content or 'google-analytics' in script_src:
            ga_info = extract_google_analytics_info(script_content, script_src)
            if ga_info:
                analytics_data['google_analytics'].append(ga_info)
        
        # Google Tag Manager
        elif 'googletagmanager' in script_content or 'googletagmanager' in script_src:
            gtm_info = extract_gtm_info(script_content, script_src)
            if gtm_info:
                analytics_data['google_tag_manager'].append(gtm_info)
        
        # Facebook Pixel
        elif 'fbq' in script_content or 'facebook' in script_src:
            fb_info = extract_facebook_pixel_info(script_content, script_src)
            if fb_info:
                analytics_data['facebook_pixel'].append(fb_info)
        
        # Hotjar
        elif 'hotjar' in script_content or 'hotjar' in script_src:
            hj_info = extract_hotjar_info(script_content, script_src)
            if hj_info:
                analytics_data['hotjar'].append(hj_info)
        
        # Mixpanel
        elif 'mixpanel' in script_content or 'mixpanel' in script_src:
            mp_info = extract_mixpanel_info(script_content, script_src)
            if mp_info:
                analytics_data['mixpanel'].append(mp_info)
        
        # Other common tracking tools
        elif any(tool in script_content.lower() for tool in ['clarity', 'crazyegg', 'optimizely', 'vwo', 'abtasty']):
            other_info = {
                'type': 'other_tracking',
                'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
                'src': script_src
            }
            analytics_data['other_tracking'].append(other_info)
    
    # Extract meta tags for tracking
    for meta in soup.find_all('meta'):
        name = meta.get('name', meta.get('property', ''))
        content = meta.get('content', '')
        
        if 'facebook' in name.lower() or 'fb:' in name.lower():
            analytics_data['social_media_tracking'].append({
                'type': 'facebook_meta',
                'name': name,
                'content': content
            })
        elif 'twitter' in name.lower():
            analytics_data['social_media_tracking'].append({
                'type': 'twitter_meta',
                'name': name,
                'content': content
            })
    
    # Generate analytics summary
    analytics_data['analytics_summary'] = {
        'total_tracking_tools': (
            len(analytics_data['google_analytics']) +
            len(analytics_data['facebook_pixel']) +
            len(analytics_data['google_tag_manager']) +
            len(analytics_data['hotjar']) +
            len(analytics_data['mixpanel']) +
            len(analytics_data['other_tracking'])
        ),
        'has_google_analytics': bool(analytics_data['google_analytics']),
        'has_facebook_pixel': bool(analytics_data['facebook_pixel']),
        'has_gtm': bool(analytics_data['google_tag_manager']),
        'has_hotjar': bool(analytics_data['hotjar']),
        'has_mixpanel': bool(analytics_data['mixpanel']),
        'has_social_tracking': bool(analytics_data['social_media_tracking']),
        'tracking_intensity': calculate_tracking_intensity(analytics_data)
    }
    
    return analytics_data

def extract_google_analytics_info(script_content, script_src):
    """Extract Google Analytics specific information."""
    import re
    
    ga_info = {
        'type': 'google_analytics',
        'version': 'unknown',
        'tracking_id': None,
        'measurement_id': None,
        'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
        'src': script_src
    }
    
    # Look for GA4 measurement ID (G-XXXXXXXXXX)
    ga4_match = re.search(r'G-[A-Z0-9]{10}', script_content)
    if ga4_match:
        ga_info['measurement_id'] = ga4_match.group()
        ga_info['version'] = 'GA4'
    
    # Look for Universal Analytics tracking ID (UA-XXXXXXXX-X)
    ua_match = re.search(r'UA-[0-9]+-[0-9]+', script_content)
    if ua_match:
        ga_info['tracking_id'] = ua_match.group()
        ga_info['version'] = 'Universal Analytics'
    
    # Look for gtag configuration
    gtag_match = re.search(r'gtag\([\'"](config|js)[\'"],\s*[\'"](G-[A-Z0-9]{10}|UA-[0-9]+-[0-9]+)[\'"]', script_content)
    if gtag_match:
        if not ga_info['measurement_id'] and not ga_info['tracking_id']:
            id_match = re.search(r'G-[A-Z0-9]{10}|UA-[0-9]+-[0-9]+', gtag_match.group())
            if id_match:
                if id_match.group().startswith('G-'):
                    ga_info['measurement_id'] = id_match.group()
                    ga_info['version'] = 'GA4'
                else:
                    ga_info['tracking_id'] = id_match.group()
                    ga_info['version'] = 'Universal Analytics'
    
    return ga_info if (ga_info['tracking_id'] or ga_info['measurement_id']) else None

def extract_gtm_info(script_content, script_src):
    """Extract Google Tag Manager specific information."""
    import re
    
    gtm_info = {
        'type': 'google_tag_manager',
        'container_id': None,
        'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
        'src': script_src
    }
    
    # Look for GTM container ID (GTM-XXXXXXX)
    gtm_match = re.search(r'GTM-[A-Z0-9]{7}', script_content)
    if gtm_match:
        gtm_info['container_id'] = gtm_match.group()
    
    return gtm_info if gtm_info['container_id'] else None

def extract_facebook_pixel_info(script_content, script_src):
    """Extract Facebook Pixel specific information."""
    import re
    
    fb_info = {
        'type': 'facebook_pixel',
        'pixel_id': None,
        'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
        'src': script_src
    }
    
    # Look for Facebook Pixel ID (usually 9-15 digits)
    pixel_match = re.search(r'fbq\([\'"]init[\'"],\s*[\'"]([0-9]{9,15})[\'"]', script_content)
    if pixel_match:
        fb_info['pixel_id'] = pixel_match.group(1)
    
    return fb_info if fb_info['pixel_id'] else None

def extract_hotjar_info(script_content, script_src):
    """Extract Hotjar specific information."""
    import re
    
    hj_info = {
        'type': 'hotjar',
        'site_id': None,
        'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
        'src': script_src
    }
    
    # Look for Hotjar site ID
    hj_match = re.search(r'hjid:\s*([0-9]+)', script_content)
    if hj_match:
        hj_info['site_id'] = hj_match.group(1)
    
    return hj_info if hj_info['site_id'] else None

def extract_mixpanel_info(script_content, script_src):
    """Extract Mixpanel specific information."""
    import re
    
    mp_info = {
        'type': 'mixpanel',
        'project_token': None,
        'content_preview': script_content[:200] + '...' if len(script_content) > 200 else script_content,
        'src': script_src
    }
    
    # Look for Mixpanel project token
    mp_match = re.search(r'mixpanel\.init\([\'"]([a-zA-Z0-9]{32})[\'"]', script_content)
    if mp_match:
        mp_info['project_token'] = mp_match.group(1)
    
    return mp_info if mp_info['project_token'] else None

def print_analytics_report(analytics_data):
    """Print a detailed analytics report."""
    print("\n" + "="*80)
    print("📊 ANALYTICS & TRACKING ANALYSIS")
    print("="*80)
    
    summary = analytics_data['analytics_summary']
    
    print(f"\n📈 TRACKING OVERVIEW")
    print("-" * 40)
    print(f"Total Tracking Tools: {summary['total_tracking_tools']}")
    print(f"Tracking Intensity: {summary['tracking_intensity']}")
    print(f"Google Analytics: {'✅' if summary['has_google_analytics'] else '❌'}")
    print(f"Facebook Pixel: {'✅' if summary['has_facebook_pixel'] else '❌'}")
    print(f"Google Tag Manager: {'✅' if summary['has_gtm'] else '❌'}")
    print(f"Hotjar: {'✅' if summary['has_hotjar'] else '❌'}")
    print(f"Mixpanel: {'✅' if summary['has_mixpanel'] else '❌'}")
    print(f"Social Tracking: {'✅' if summary['has_social_tracking'] else '❌'}")
    
    # Google Analytics Details
    if analytics_data['google_analytics']:
        print(f"\n🔍 GOOGLE ANALYTICS DETAILS")
        print("-" * 40)
        for i, ga in enumerate(analytics_data['google_analytics'], 1):
            print(f"Instance {i}:")
            print(f"  Version: {ga['version']}")
            if ga['tracking_id']:
                print(f"  Tracking ID: {ga['tracking_id']}")
            if ga['measurement_id']:
                print(f"  Measurement ID: {ga['measurement_id']}")
            print(f"  Source: {'Inline Script' if not ga['src'] else 'External Script'}")
    
    # Facebook Pixel Details
    if analytics_data['facebook_pixel']:
        print(f"\n📘 FACEBOOK PIXEL DETAILS")
        print("-" * 40)
        for i, fb in enumerate(analytics_data['facebook_pixel'], 1):
            print(f"Pixel {i}:")
            print(f"  Pixel ID: {fb['pixel_id']}")
            print(f"  Source: {'Inline Script' if not fb['src'] else 'External Script'}")
    
    # Google Tag Manager Details
    if analytics_data['google_tag_manager']:
        print(f"\n🏷️ GOOGLE TAG MANAGER DETAILS")
        print("-" * 40)
        for i, gtm in enumerate(analytics_data['google_tag_manager'], 1):
            print(f"GTM {i}:")
            print(f"  Container ID: {gtm['container_id']}")
            print(f"  Source: {'Inline Script' if not gtm['src'] else 'External Script'}")
    
    # Hotjar Details
    if analytics_data['hotjar']:
        print(f"\n🔥 HOTJAR DETAILS")
        print("-" * 40)
        for i, hj in enumerate(analytics_data['hotjar'], 1):
            print(f"Hotjar {i}:")
            print(f"  Site ID: {hj['site_id']}")
            print(f"  Source: {'Inline Script' if not hj['src'] else 'External Script'}")
    
    # Mixpanel Details
    if analytics_data['mixpanel']:
        print(f"\n📊 MIXPANEL DETAILS")
        print("-" * 40)
        for i, mp in enumerate(analytics_data['mixpanel'], 1):
            print(f"Mixpanel {i}:")
            print(f"  Project Token: {mp['project_token']}")
            print(f"  Source: {'Inline Script' if not mp['src'] else 'External Script'}")
    
    # Social Media Tracking
    if analytics_data['social_media_tracking']:
        print(f"\n📱 SOCIAL MEDIA TRACKING")
        print("-" * 40)
        for tracking in analytics_data['social_media_tracking']:
            print(f"Type: {tracking['type']}")
            print(f"Name: {tracking['name']}")
            print(f"Content: {tracking['content']}")
    
    # Other Tracking Tools
    if analytics_data['other_tracking']:
        print(f"\n🔧 OTHER TRACKING TOOLS")
        print("-" * 40)
        for i, other in enumerate(analytics_data['other_tracking'], 1):
            print(f"Tool {i}:")
            print(f"  Type: {other['type']}")
            if other['src']:
                print(f"  Source: {other['src']}")
    
    # Privacy and Performance Insights
    print(f"\n🔒 PRIVACY & PERFORMANCE INSIGHTS")
    print("-" * 40)
    if summary['tracking_intensity'] in ['Heavy', 'Very Heavy']:
        print("⚠️  High tracking intensity detected - may impact privacy and performance")
    elif summary['tracking_intensity'] == 'Moderate':
        print("⚖️  Moderate tracking - balanced approach")
    elif summary['tracking_intensity'] == 'Light':
        print("✅ Light tracking - minimal impact")
    else:
        print("✅ No tracking detected")
    
    if summary['total_tracking_tools'] > 3:
        print("💡 Consider consolidating tracking tools for better performance")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    # Example Usage:
    # You can change this URL to any website you want to scrape.
    # Be mindful of the website's terms of service and robots.txt file before scraping.
    # target_url = "https://coordleapp.com/" # Replace with your target URL
    target_url = "https://www.dogsonthecurb.com/"

    scraped_data = simple_web_scraper(target_url)

    if scraped_data:
        # Perform comprehensive analysis and categorization
        analysis_results = analyze_scraped_content(scraped_data)
        
        # Print detailed analysis
        print_detailed_analysis(analysis_results)
        
        # Print detailed analytics report
        seo_data = scraped_data.get('seo_metadata', {})
        if seo_data.get('detailed_analytics'):
            print_analytics_report(seo_data['detailed_analytics'])
        
        # Save content to files in scraped_sites folder
        saved_dir = save_content_to_files(scraped_data, target_url)
        if saved_dir:
            print(f"\n📁 All files saved to: {saved_dir}")
        
        # Save analysis results as JSON
        analysis_file = os.path.join(saved_dir, "content_analysis.json")
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2)
        print(f"📊 Content analysis saved to: {analysis_file}")
        
        # Save detailed analytics data
        if seo_data.get('detailed_analytics'):
            analytics_file = os.path.join(saved_dir, "analytics_data.json")
            with open(analytics_file, "w", encoding="utf-8") as f:
                json.dump(seo_data['detailed_analytics'], f, indent=2)
            print(f"📈 Analytics data saved to: {analytics_file}")
        
        # Print a quick summary of key findings
        print(f"\n🔍 QUICK SUMMARY")
        print("-" * 40)
        print(f"Content Type: {analysis_results['content_categorization']['content_type']}")
        print(f"Word Count: {analysis_results['seo_analysis']['word_count']:,}")
        print(f"Performance Score: {analysis_results['performance_insights']['performance_score']}/100")
        print(f"SEO Issues Found: {len(analysis_results['recommendations'])}")
        print(f"Images with Alt Text: {analysis_results['media_analysis']['alt_text_coverage']:.1f}%")
        print(f"Link Quality: {analysis_results['link_analysis']['link_quality']}")
        
        # Analytics summary
        if seo_data.get('detailed_analytics'):
            analytics_summary = seo_data['detailed_analytics']['analytics_summary']
            print(f"Tracking Tools: {analytics_summary['total_tracking_tools']} ({analytics_summary['tracking_intensity']})")
            print(f"Google Analytics: {'✅' if analytics_summary['has_google_analytics'] else '❌'}")
            print(f"Facebook Pixel: {'✅' if analytics_summary['has_facebook_pixel'] else '❌'}")
        
    else:
        print("\n❌ Failed to scrape the target URL.") 
        