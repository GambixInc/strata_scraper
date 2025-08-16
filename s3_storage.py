import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

# Global S3 client - initialized once
_s3_client = None
_bucket_name = None

def get_s3_client():
    """Get or create S3 client using AWS credentials"""
    global _s3_client, _bucket_name
    
    if _s3_client is None:
        try:
            # Get configuration from environment
            aws_region = os.getenv('AWS_REGION', 'us-east-1')
            _bucket_name = os.getenv('S3_BUCKET_NAME')
            
            if not _bucket_name:
                raise ValueError("Missing required S3 environment variable: S3_BUCKET_NAME")
            
            # Create S3 client - boto3 will automatically use AWS credentials
            _s3_client = boto3.client('s3', region_name=aws_region)
            
            # Test connection
            _s3_client.head_bucket(Bucket=_bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {_bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    return _s3_client, _bucket_name

def upload_file_to_s3(content: str, s3_key: str, content_type: str = 'text/plain') -> bool:
    """Upload file content to S3"""
    try:
        s3_client, bucket_name = get_s3_client()
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType=content_type
        )
        logger.info(f"Successfully uploaded {s3_key} to S3")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {s3_key} to S3: {e}")
        return False

def upload_json_to_s3(data: Dict[str, Any], s3_key: str) -> bool:
    """Upload JSON data to S3"""
    try:
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        return upload_file_to_s3(json_content, s3_key, 'application/json')
    except Exception as e:
        logger.error(f"Failed to upload JSON {s3_key} to S3: {e}")
        return False

def read_file_from_s3(s3_key: str) -> Optional[str]:
    """Read file content from S3"""
    try:
        s3_client, bucket_name = get_s3_client()
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        logger.info(f"Successfully read file from S3: {s3_key}")
        return content
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"File not found in S3: {s3_key}")
            return None
        else:
            logger.error(f"Failed to read file from S3 {s3_key}: {e}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error reading file from S3 {s3_key}: {e}")
        return None

def read_json_from_s3(s3_key: str) -> Optional[Dict[str, Any]]:
    """Read JSON content from S3"""
    try:
        content = read_file_from_s3(s3_key)
        if content:
            return json.loads(content)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from S3 {s3_key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading JSON from S3 {s3_key}: {e}")
        return None

def list_files_in_s3(prefix: str) -> list:
    """List all files in a specific S3 prefix"""
    try:
        s3_client, bucket_name = get_s3_client()
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except Exception as e:
        logger.error(f"Failed to list files in prefix {prefix}: {e}")
        return []

def delete_files_in_s3(prefix: str) -> bool:
    """Delete all files in a specific S3 prefix"""
    try:
        s3_client, bucket_name = get_s3_client()
        objects = list_files_in_s3(prefix)
        
        if not objects:
            logger.info(f"No files found in prefix {prefix}")
            return True
        
        # Delete objects
        delete_objects = [{'Key': obj} for obj in objects]
        s3_client.delete_objects(
            Bucket=bucket_name,
            Delete={'Objects': delete_objects}
        )
        
        logger.info(f"Successfully deleted {len(objects)} files from prefix {prefix}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete files in prefix {prefix}: {e}")
        return False

def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned URL for downloading a file from S3"""
    try:
        s3_client, bucket_name = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
        return None

def file_exists_in_s3(s3_key: str) -> bool:
    """Check if a file exists in S3"""
    try:
        s3_client, bucket_name = get_s3_client()
        s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.error(f"Error checking file existence in S3 {s3_key}: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error checking file existence in S3 {s3_key}: {e}")
        return False

def save_scraped_content_to_s3(scraped_data: Dict[str, Any], url: str, base_filename: Optional[str] = None) -> Optional[str]:
    """
    Save scraped content to S3 bucket using simple functions
    
    Args:
        scraped_data: The scraped data dictionary
        url: The original URL that was scraped
        base_filename: Optional base filename, if not provided will be generated from URL
        
    Returns:
        str: The S3 prefix (directory) where files were saved, or None if failed
    """
    if not scraped_data:
        logger.warning("No data to save to S3")
        return None
    
    # Generate filename from URL if not provided
    if not base_filename:
        from main import get_safe_filename
        base_filename = get_safe_filename(url)
    
    # Create S3 prefix (directory structure)
    s3_prefix = f"scraped_sites/{base_filename}"
    
    try:
        # Save HTML content
        html_key = f"{s3_prefix}/index.html"
        if not upload_file_to_s3(scraped_data['html_content'], html_key, 'text/html'):
            logger.error(f"Failed to upload HTML content for {url}")
            return None
        
        # Save CSS content
        css_content = "/* === INLINE STYLES === */\n"
        for i, style in enumerate(scraped_data['css_content']['inline_styles']):
            css_content += f"\n/* --- Inline Style {i+1} --- */\n"
            css_content += style
            css_content += "\n"
        
        css_content += "\n\n/* === INTERNAL STYLESHEETS === */\n"
        for i, style in enumerate(scraped_data['css_content']['internal_stylesheets']):
            css_content += f"\n/* --- Internal Stylesheet {i+1} --- */\n"
            css_content += style
            css_content += "\n"
        
        css_content += "\n\n/* === EXTERNAL STYLESHEETS === */\n"
        for i, link in enumerate(scraped_data['css_content']['external_stylesheets']):
            css_content += f"/* {i+1}. {link} */\n"
        
        css_key = f"{s3_prefix}/styles.css"
        if not upload_file_to_s3(css_content, css_key, 'text/css'):
            logger.error(f"Failed to upload CSS content for {url}")
            return None
        
        # Save JavaScript content
        js_content = "// === INLINE SCRIPTS ===\n"
        for i, script in enumerate(scraped_data['js_content']['inline_scripts']):
            js_content += f"\n// --- Inline Script {i+1} ---\n"
            js_content += script
            js_content += "\n"
        
        js_content += "\n\n// === EXTERNAL SCRIPTS ===\n"
        for i, link in enumerate(scraped_data['js_content']['external_scripts']):
            js_content += f"// {i+1}. {link}\n"
        
        js_key = f"{s3_prefix}/scripts.js"
        if not upload_file_to_s3(js_content, js_key, 'application/javascript'):
            logger.error(f"Failed to upload JavaScript content for {url}")
            return None
        
        # Save links
        links_content = f"Links found on: {url}\n"
        links_content += f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        links_content += "=" * 50 + "\n\n"
        for i, link in enumerate(scraped_data['links'], 1):
            links_content += f"{i}. {link}\n"
        
        links_key = f"{s3_prefix}/links.txt"
        if not upload_file_to_s3(links_content, links_key, 'text/plain'):
            logger.error(f"Failed to upload links for {url}")
            return None
        
        # Save metadata as JSON
        _, bucket_name = get_s3_client()
        metadata = {
            "original_url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": scraped_data['title'],
            "s3_location": f"s3://{bucket_name}/{s3_prefix}",
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
        
        metadata_key = f"{s3_prefix}/metadata.json"
        if not upload_json_to_s3(metadata, metadata_key):
            logger.error(f"Failed to upload metadata for {url}")
            return None
        
        # Save detailed SEO report
        seo_report_content = f"SEO Analysis Report for: {url}\n"
        seo_report_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        seo_report_content += "=" * 80 + "\n\n"
        
        seo_data = scraped_data.get('seo_metadata', {})
        if seo_data:
            seo_report_content += "META TAGS:\n"
            for tag, value in seo_data.get('meta_tags', {}).items():
                seo_report_content += f"  {tag}: {value}\n"
            
            seo_report_content += "\nOPEN GRAPH TAGS:\n"
            for tag, value in seo_data.get('open_graph', {}).items():
                seo_report_content += f"  {tag}: {value}\n"
            
            seo_report_content += "\nTWITTER CARD TAGS:\n"
            for tag, value in seo_data.get('twitter_cards', {}).items():
                seo_report_content += f"  {tag}: {value}\n"
        
        seo_report_key = f"{s3_prefix}/seo_report.txt"
        if not upload_file_to_s3(seo_report_content, seo_report_key, 'text/plain'):
            logger.error(f"Failed to upload SEO report for {url}")
            return None
        
        logger.info(f"Successfully saved all scraped content to S3: s3://{bucket_name}/{s3_prefix}")
        return s3_prefix
        
    except Exception as e:
        logger.error(f"Error saving scraped content to S3 for {url}: {e}")
        return None

# Legacy S3Storage class for backward compatibility
class S3Storage:
    """
    Legacy wrapper class for backward compatibility.
    Use the direct functions instead for new code.
    """
    
    def __init__(self):
        # Initialize the global S3 client
        get_s3_client()
        _, self.bucket_name = get_s3_client()
    
    def upload_file_content(self, content: str, s3_key: str, content_type: str = 'text/plain') -> bool:
        return upload_file_to_s3(content, s3_key, content_type)
    
    def upload_json_content(self, data: Dict[str, Any], s3_key: str) -> bool:
        return upload_json_to_s3(data, s3_key)
    
    def save_scraped_content_to_s3(self, scraped_data: Dict[str, Any], url: str, base_filename: Optional[str] = None) -> Optional[str]:
        return save_scraped_content_to_s3(scraped_data, url, base_filename)
    
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        return generate_presigned_url(s3_key, expires_in)
    
    def list_files_in_prefix(self, prefix: str) -> list:
        return list_files_in_s3(prefix)
    
    def delete_files_in_prefix(self, prefix: str) -> bool:
        return delete_files_in_s3(prefix)
    
    def read_file_content(self, s3_key: str) -> Optional[str]:
        return read_file_from_s3(s3_key)
    
    def read_json_content(self, s3_key: str) -> Optional[Dict[str, Any]]:
        return read_json_from_s3(s3_key)
    
    def file_exists(self, s3_key: str) -> bool:
        return file_exists_in_s3(s3_key)
