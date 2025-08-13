import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class S3Storage:
    """
    A class to handle S3 storage operations for scraped website content
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL', 'https://s3.amazonaws.com')
        
        # Validate required environment variables
        if not self.bucket_name:
            raise ValueError("Missing required S3 environment variable: S3_BUCKET_NAME")
        
        # Initialize S3 client using AWS CLI credential chain
        # This will automatically use IAM roles, AWS CLI credentials, or environment variables
        self.s3_client = boto3.client(
            's3',
            region_name=self.aws_region,
            endpoint_url=self.endpoint_url
        )
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test S3 connection and bucket access"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise ValueError(f"S3 connection error: {e}")
        except NoCredentialsError:
            raise ValueError("AWS credentials not found")
        except Exception as e:
            raise ValueError(f"Unexpected S3 error: {e}")
    
    def upload_file_content(self, content: str, s3_key: str, content_type: str = 'text/plain') -> bool:
        """
        Upload file content to S3
        
        Args:
            content: The content to upload
            s3_key: The S3 key (path) for the file
            content_type: The MIME type of the content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            logger.info(f"Successfully uploaded {s3_key} to S3")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {s3_key} to S3: {e}")
            return False
    
    def upload_json_content(self, data: Dict[str, Any], s3_key: str) -> bool:
        """
        Upload JSON data to S3
        
        Args:
            data: The JSON data to upload
            s3_key: The S3 key (path) for the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            return self.upload_file_content(json_content, s3_key, 'application/json')
        except Exception as e:
            logger.error(f"Failed to upload JSON {s3_key} to S3: {e}")
            return False
    
    def save_scraped_content_to_s3(self, scraped_data: Dict[str, Any], url: str, base_filename: Optional[str] = None) -> Optional[str]:
        """
        Save scraped content to S3 bucket
        
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
            if not self.upload_file_content(scraped_data['html_content'], html_key, 'text/html'):
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
            if not self.upload_file_content(css_content, css_key, 'text/css'):
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
            if not self.upload_file_content(js_content, js_key, 'application/javascript'):
                logger.error(f"Failed to upload JavaScript content for {url}")
                return None
            
            # Save links
            links_content = f"Links found on: {url}\n"
            links_content += f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            links_content += "=" * 50 + "\n\n"
            for i, link in enumerate(scraped_data['links'], 1):
                links_content += f"{i}. {link}\n"
            
            links_key = f"{s3_prefix}/links.txt"
            if not self.upload_file_content(links_content, links_key, 'text/plain'):
                logger.error(f"Failed to upload links for {url}")
                return None
            
            # Save metadata as JSON
            metadata = {
                "original_url": url,
                "scraped_at": datetime.now().isoformat(),
                "title": scraped_data['title'],
                "s3_location": f"s3://{self.bucket_name}/{s3_prefix}",
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
            if not self.upload_json_content(metadata, metadata_key):
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
            if not self.upload_file_content(seo_report_content, seo_report_key, 'text/plain'):
                logger.error(f"Failed to upload SEO report for {url}")
                return None
            
            logger.info(f"Successfully saved all scraped content to S3: s3://{self.bucket_name}/{s3_prefix}")
            return s3_prefix
            
        except Exception as e:
            logger.error(f"Error saving scraped content to S3 for {url}: {e}")
            return None
    
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file from S3
        
        Args:
            s3_key: The S3 key of the file
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None
    
    def list_files_in_prefix(self, prefix: str) -> list:
        """
        List all files in a specific S3 prefix
        
        Args:
            prefix: The S3 prefix to list files from
            
        Returns:
            list: List of file keys in the prefix
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            logger.error(f"Failed to list files in prefix {prefix}: {e}")
            return []
    
    def delete_files_in_prefix(self, prefix: str) -> bool:
        """
        Delete all files in a specific S3 prefix
        
        Args:
            prefix: The S3 prefix to delete files from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # List all objects in the prefix
            objects = self.list_files_in_prefix(prefix)
            
            if not objects:
                logger.info(f"No files found in prefix {prefix}")
                return True
            
            # Delete objects
            delete_objects = [{'Key': obj} for obj in objects]
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': delete_objects}
            )
            
            logger.info(f"Successfully deleted {len(objects)} files from prefix {prefix}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete files in prefix {prefix}: {e}")
            return False
