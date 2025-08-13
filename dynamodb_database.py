import boto3
import json
import os
import uuid
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class DynamoDBDatabase:
    """DynamoDB database manager for the Gambix Strata platform"""
    
    def __init__(self, table_prefix: str = "gambix_strata"):
        self.table_prefix = table_prefix
        
        # Get endpoint URL from environment (for LocalStack testing)
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
        
        if endpoint_url:
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
            self.client = boto3.client('dynamodb', endpoint_url=endpoint_url)
        else:
            # Get region from environment or use default
            region = os.getenv('AWS_REGION', 'us-east-1')
            self.dynamodb = boto3.resource('dynamodb', region_name=region)
            self.client = boto3.client('dynamodb', region_name=region)
        
        # Table names
        self.users_table_name = f"{table_prefix}_users"
        self.projects_table_name = f"{table_prefix}_projects"
        self.site_health_table_name = f"{table_prefix}_site_health"
        self.pages_table_name = f"{table_prefix}_pages"
        self.recommendations_table_name = f"{table_prefix}_recommendations"
        self.alerts_table_name = f"{table_prefix}_alerts"
        self.optimizations_table_name = f"{table_prefix}_optimizations"
        
        # Table references
        self.users_table = self.dynamodb.Table(self.users_table_name)
        self.projects_table = self.dynamodb.Table(self.projects_table_name)
        self.site_health_table = self.dynamodb.Table(self.site_health_table_name)
        self.pages_table = self.dynamodb.Table(self.pages_table_name)
        self.recommendations_table = self.dynamodb.Table(self.recommendations_table_name)
        self.alerts_table = self.dynamodb.Table(self.alerts_table_name)
        self.optimizations_table = self.dynamodb.Table(self.optimizations_table_name)
        
        self.init_database()
    
    def init_database(self):
        """Initialize DynamoDB tables if they don't exist"""
        tables_to_create = [
            self._create_users_table,
            self._create_projects_table,
            self._create_site_health_table,
            self._create_pages_table,
            self._create_recommendations_table,
            self._create_alerts_table,
            self._create_optimizations_table
        ]
        
        for create_table_func in tables_to_create:
            try:
                create_table_func()
            except Exception as e:
                logger.warning(f"Table creation failed: {e}")
    
    def _create_users_table(self):
        """Create users table"""
        try:
            self.dynamodb.create_table(
                TableName=self.users_table_name,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'email', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'email-index',
                        'KeySchema': [
                            {'AttributeName': 'email', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.users_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_projects_table(self):
        """Create projects table"""
        try:
            self.dynamodb.create_table(
                TableName=self.projects_table_name,
                KeySchema=[
                    {'AttributeName': 'project_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'domain', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user-projects-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'user-domain-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'domain', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.projects_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_site_health_table(self):
        """Create site health table"""
        try:
            self.dynamodb.create_table(
                TableName=self.site_health_table_name,
                KeySchema=[
                    {'AttributeName': 'health_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'health_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'project-health-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.site_health_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_pages_table(self):
        """Create pages table"""
        try:
            self.dynamodb.create_table(
                TableName=self.pages_table_name,
                KeySchema=[
                    {'AttributeName': 'page_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'page_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'project-pages-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.pages_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_recommendations_table(self):
        """Create recommendations table"""
        try:
            self.dynamodb.create_table(
                TableName=self.recommendations_table_name,
                KeySchema=[
                    {'AttributeName': 'recommendation_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'recommendation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'project-recommendations-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'status', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.recommendations_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_alerts_table(self):
        """Create alerts table"""
        try:
            self.dynamodb.create_table(
                TableName=self.alerts_table_name,
                KeySchema=[
                    {'AttributeName': 'alert_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'alert_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user-alerts-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'status', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.alerts_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _create_optimizations_table(self):
        """Create optimizations table"""
        try:
            self.dynamodb.create_table(
                TableName=self.optimizations_table_name,
                KeySchema=[
                    {'AttributeName': 'optimization_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'optimization_id', 'AttributeType': 'S'},
                    {'AttributeName': 'project_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'project-optimizations-index',
                        'KeySchema': [
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info(f"Created table: {self.optimizations_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        return str(uuid.uuid4())
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string"""
        if data is None:
            return None
        return json.dumps(data)
    
    def _deserialize_json(self, json_str: str) -> Any:
        """Deserialize JSON string to data"""
        if json_str is None:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat()
    
    # User operations
    def create_user(self, email: str, name: str, password: str = None, role: str = 'user', preferences: Dict = None) -> str:
        """Create a new user"""
        user_id = self._generate_id()
        
        item = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,
            'created_at': self._get_timestamp(),
            'updated_at': self._get_timestamp(),
            'is_active': True
        }
        
        if password:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            item['password_hash'] = password_hash.decode('utf-8')
        
        if preferences:
            item['preferences'] = self._serialize_json(preferences)
        
        try:
            self.users_table.put_item(Item=item)
            return user_id
        except ClientError as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            item = response.get('Item')
            if item:
                if 'preferences' in item:
                    item['preferences'] = self._deserialize_json(item['preferences'])
                return item
            return None
        except ClientError as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            response = self.users_table.query(
                IndexName='email-index',
                KeyConditionExpression='#email = :email',
                ExpressionAttributeNames={'#email': 'email'},
                ExpressionAttributeValues={':email': email}
            )
            items = response.get('Items', [])
            if items:
                item = items[0]
                if 'preferences' in item:
                    item['preferences'] = self._deserialize_json(item['preferences'])
                return item
            return None
        except ClientError as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not user.get('password_hash'):
            return None
        
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update last login
                self.update_user_login(user['user_id'])
                return user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
        
        return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update user profile"""
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': self._get_timestamp()}
        
        for key, value in profile_data.items():
            if key in ['name', 'email', 'role', 'is_active']:
                update_expression += f", {key} = :{key}"
                expression_values[f':{key}'] = value
        
        if 'preferences' in profile_data:
            update_expression += ", preferences = :preferences"
            expression_values[':preferences'] = self._serialize_json(profile_data['preferences'])
        
        try:
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def update_user_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET last_login = :last_login",
                ExpressionAttributeValues={':last_login': self._get_timestamp()}
            )
        except ClientError as e:
            logger.error(f"Error updating user login: {e}")
    
    # Project operations
    def create_project(self, user_id: str, domain: str, name: str, settings: Dict = None) -> str:
        """Create a new project"""
        project_id = self._generate_id()
        
        item = {
            'project_id': project_id,
            'user_id': user_id,
            'domain': domain,
            'name': name,
            'status': 'active',
            'created_at': self._get_timestamp(),
            'updated_at': self._get_timestamp(),
            'auto_optimize': False
        }
        
        if settings:
            item['settings'] = self._serialize_json(settings)
        
        try:
            self.projects_table.put_item(Item=item)
            return project_id
        except ClientError as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get all projects for a user"""
        try:
            response = self.projects_table.query(
                IndexName='user-projects-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False  # Most recent first
            )
            
            items = response.get('Items', [])
            for item in items:
                if 'settings' in item:
                    item['settings'] = self._deserialize_json(item['settings'])
            
            return items
        except ClientError as e:
            logger.error(f"Error getting user projects: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        try:
            response = self.projects_table.get_item(Key={'project_id': project_id})
            item = response.get('Item')
            if item and 'settings' in item:
                item['settings'] = self._deserialize_json(item['settings'])
            return item
        except ClientError as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    def get_project_by_user_and_domain(self, user_id: str, domain: str) -> Optional[Dict]:
        """Get project by user ID and domain"""
        try:
            response = self.projects_table.query(
                IndexName='user-domain-index',
                KeyConditionExpression='user_id = :user_id AND #domain = :domain',
                ExpressionAttributeNames={'#domain': 'domain'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':domain': domain
                }
            )
            
            items = response.get('Items', [])
            if items:
                item = items[0]
                if 'settings' in item:
                    item['settings'] = self._deserialize_json(item['settings'])
                return item
            return None
        except ClientError as e:
            logger.error(f"Error getting project by user and domain: {e}")
            return None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        try:
            self.projects_table.delete_item(Key={'project_id': project_id})
            return True
        except ClientError as e:
            logger.error(f"Error deleting project: {e}")
            return False
    
    def update_project_status(self, project_id: str, status: str):
        """Update project status"""
        try:
            self.projects_table.update_item(
                Key={'project_id': project_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': self._get_timestamp()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating project status: {e}")
    
    def update_project_scraped_files(self, project_id: str, scraped_files_path: str):
        """Update project's scraped files path"""
        try:
            self.projects_table.update_item(
                Key={'project_id': project_id},
                UpdateExpression="SET scraped_files_path = :path, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':path': scraped_files_path,
                    ':updated_at': self._get_timestamp()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating project scraped files: {e}")
    
    def update_project_last_crawl(self, project_id: str):
        """Update project's last crawl timestamp"""
        try:
            self.projects_table.update_item(
                Key={'project_id': project_id},
                UpdateExpression="SET last_crawl = :last_crawl, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':last_crawl': self._get_timestamp(),
                    ':updated_at': self._get_timestamp()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating project last crawl: {e}")
    
    # Site health operations
    def add_site_health(self, project_id: str, health_data: Dict) -> str:
        """Add site health data"""
        health_id = self._generate_id()
        
        item = {
            'health_id': health_id,
            'project_id': project_id,
            'timestamp': self._get_timestamp(),
            'overall_score': health_data.get('overall_score', 0),
            'technical_seo': health_data.get('technical_seo', 0),
            'content_seo': health_data.get('content_seo', 0),
            'performance': health_data.get('performance', 0),
            'internal_linking': health_data.get('internal_linking', 0),
            'visual_ux': health_data.get('visual_ux', 0),
            'authority_backlinks': health_data.get('authority_backlinks', 0),
            'total_impressions': health_data.get('total_impressions', 0),
            'total_engagements': health_data.get('total_engagements', 0),
            'total_conversions': health_data.get('total_conversions', 0)
        }
        
        if 'crawl_data' in health_data:
            item['crawl_data'] = self._serialize_json(health_data['crawl_data'])
        
        try:
            self.site_health_table.put_item(Item=item)
            return health_id
        except ClientError as e:
            logger.error(f"Error adding site health: {e}")
            raise
    
    def get_latest_site_health(self, project_id: str) -> Optional[Dict]:
        """Get latest site health data for a project"""
        try:
            response = self.site_health_table.query(
                IndexName='project-health-index',
                KeyConditionExpression='project_id = :project_id',
                ExpressionAttributeValues={':project_id': project_id},
                ScanIndexForward=False,  # Most recent first
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                item = items[0]
                if 'crawl_data' in item:
                    item['crawl_data'] = self._deserialize_json(item['crawl_data'])
                return item
            return None
        except ClientError as e:
            logger.error(f"Error getting latest site health: {e}")
            return None
    
    def get_site_health_history(self, project_id: str, limit: int = 30) -> List[Dict]:
        """Get site health history for a project"""
        try:
            response = self.site_health_table.query(
                IndexName='project-health-index',
                KeyConditionExpression='project_id = :project_id',
                ExpressionAttributeValues={':project_id': project_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            items = response.get('Items', [])
            for item in items:
                if 'crawl_data' in item:
                    item['crawl_data'] = self._deserialize_json(item['crawl_data'])
            
            return items
        except ClientError as e:
            logger.error(f"Error getting site health history: {e}")
            return []
    
    # Page operations
    def add_page(self, project_id: str, page_data: Dict) -> str:
        """Add a page to a project"""
        page_id = self._generate_id()
        
        item = {
            'page_id': page_id,
            'project_id': project_id,
            'page_url': page_data.get('page_url', ''),
            'title': page_data.get('title', ''),
            'status': page_data.get('status', 'healthy'),
            'last_crawled': self._get_timestamp(),
            'word_count': page_data.get('word_count', 0),
            'load_time': page_data.get('load_time', 0.0),
            'meta_description': page_data.get('meta_description', ''),
            'images_count': page_data.get('images_count', 0),
            'links_count': page_data.get('links_count', 0)
        }
        
        if 'h1_tags' in page_data:
            item['h1_tags'] = self._serialize_json(page_data['h1_tags'])
        
        try:
            self.pages_table.put_item(Item=item)
            return page_id
        except ClientError as e:
            logger.error(f"Error adding page: {e}")
            raise
    
    def get_project_pages(self, project_id: str) -> List[Dict]:
        """Get all pages for a project"""
        try:
            response = self.pages_table.query(
                IndexName='project-pages-index',
                KeyConditionExpression='project_id = :project_id',
                ExpressionAttributeValues={':project_id': project_id}
            )
            
            items = response.get('Items', [])
            for item in items:
                if 'h1_tags' in item:
                    item['h1_tags'] = self._deserialize_json(item['h1_tags'])
            
            return items
        except ClientError as e:
            logger.error(f"Error getting project pages: {e}")
            return []
    
    # Recommendation operations
    def add_recommendation(self, project_id: str, recommendation_data: Dict) -> str:
        """Add a recommendation to a project"""
        recommendation_id = self._generate_id()
        
        item = {
            'recommendation_id': recommendation_id,
            'project_id': project_id,
            'category': recommendation_data.get('category', ''),
            'issue': recommendation_data.get('issue', ''),
            'recommendation': recommendation_data.get('recommendation', ''),
            'status': recommendation_data.get('status', 'pending'),
            'priority': recommendation_data.get('priority', 'medium'),
            'impact_score': recommendation_data.get('impact_score', 50),
            'created_at': self._get_timestamp(),
            'updated_at': self._get_timestamp()
        }
        
        if 'guidelines' in recommendation_data:
            item['guidelines'] = self._serialize_json(recommendation_data['guidelines'])
        
        try:
            self.recommendations_table.put_item(Item=item)
            return recommendation_id
        except ClientError as e:
            logger.error(f"Error adding recommendation: {e}")
            raise
    
    def get_project_recommendations(self, project_id: str, status: str = 'pending') -> List[Dict]:
        """Get recommendations for a project"""
        try:
            response = self.recommendations_table.query(
                IndexName='project-recommendations-index',
                KeyConditionExpression='project_id = :project_id AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':project_id': project_id,
                    ':status': status
                }
            )
            
            items = response.get('Items', [])
            for item in items:
                if 'guidelines' in item:
                    item['guidelines'] = self._deserialize_json(item['guidelines'])
            
            return items
        except ClientError as e:
            logger.error(f"Error getting project recommendations: {e}")
            return []
    
    def update_recommendation_status(self, recommendation_id: str, status: str):
        """Update recommendation status"""
        try:
            self.recommendations_table.update_item(
                Key={'recommendation_id': recommendation_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': self._get_timestamp()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating recommendation status: {e}")
    
    # Alert operations
    def create_alert(self, user_id: str, alert_data: Dict) -> str:
        """Create an alert for a user"""
        alert_id = self._generate_id()
        
        item = {
            'alert_id': alert_id,
            'user_id': user_id,
            'title': alert_data.get('title', ''),
            'description': alert_data.get('description', ''),
            'alert_type': alert_data.get('alert_type', 'info'),
            'priority': alert_data.get('priority', 'medium'),
            'status': alert_data.get('status', 'active'),
            'created_at': self._get_timestamp()
        }
        
        try:
            self.alerts_table.put_item(Item=item)
            return alert_id
        except ClientError as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    def get_user_alerts(self, user_id: str, status: str = 'active') -> List[Dict]:
        """Get alerts for a user"""
        try:
            response = self.alerts_table.query(
                IndexName='user-alerts-index',
                KeyConditionExpression='user_id = :user_id AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':status': status
                }
            )
            
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    def dismiss_alert(self, alert_id: str):
        """Dismiss an alert"""
        try:
            self.alerts_table.update_item(
                Key={'alert_id': alert_id},
                UpdateExpression="SET #status = :status, dismissed_at = :dismissed_at",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'dismissed',
                    ':dismissed_at': self._get_timestamp()
                }
            )
        except ClientError as e:
            logger.error(f"Error dismissing alert: {e}")
    
    # Optimization operations
    def add_optimization(self, project_id: str, optimization_data: Dict) -> str:
        """Add an optimization record"""
        optimization_id = self._generate_id()
        
        item = {
            'optimization_id': optimization_id,
            'project_id': project_id,
            'optimization_type': optimization_data.get('optimization_type', ''),
            'description': optimization_data.get('description', ''),
            'created_at': self._get_timestamp()
        }
        
        if 'changes_made' in optimization_data:
            item['changes_made'] = self._serialize_json(optimization_data['changes_made'])
        
        if 'performance_impact' in optimization_data:
            item['performance_impact'] = self._serialize_json(optimization_data['performance_impact'])
        
        try:
            self.optimizations_table.put_item(Item=item)
            return optimization_id
        except ClientError as e:
            logger.error(f"Error adding optimization: {e}")
            raise
    
    def get_optimization_history(self, project_id: str, limit: int = 50) -> List[Dict]:
        """Get optimization history for a project"""
        try:
            response = self.optimizations_table.query(
                IndexName='project-optimizations-index',
                KeyConditionExpression='project_id = :project_id',
                ExpressionAttributeValues={':project_id': project_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            items = response.get('Items', [])
            for item in items:
                if 'changes_made' in item:
                    item['changes_made'] = self._deserialize_json(item['changes_made'])
                if 'performance_impact' in item:
                    item['performance_impact'] = self._deserialize_json(item['performance_impact'])
            
            return items
        except ClientError as e:
            logger.error(f"Error getting optimization history: {e}")
            return []
    
    # Statistics and dashboard operations
    def get_project_statistics(self, project_id: str) -> Dict:
        """Get comprehensive statistics for a project"""
        try:
            # Get latest health data
            latest_health = self.get_latest_site_health(project_id)
            
            # Get pages count
            pages = self.get_project_pages(project_id)
            
            # Get recommendations count
            pending_recommendations = self.get_project_recommendations(project_id, 'pending')
            
            # Get optimizations count
            optimizations = self.get_optimization_history(project_id, 100)
            
            stats = {
                'project_id': project_id,
                'total_pages': len(pages),
                'pending_recommendations': len(pending_recommendations),
                'total_optimizations': len(optimizations),
                'latest_health_score': latest_health.get('overall_score', 0) if latest_health else 0,
                'last_crawl': latest_health.get('timestamp') if latest_health else None
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {}
    
    def get_dashboard_data(self, user_id: str) -> Dict:
        """Get dashboard data for a user"""
        try:
            # Get user projects
            projects = self.get_user_projects(user_id)
            
            # Get user alerts
            alerts = self.get_user_alerts(user_id, 'active')
            
            dashboard_data = {
                'user_id': user_id,
                'total_projects': len(projects),
                'active_projects': len([p for p in projects if p.get('status') == 'active']),
                'total_alerts': len(alerts),
                'projects': []
            }
            
            # Add project statistics
            for project in projects[:10]:  # Limit to 10 most recent
                project_stats = self.get_project_statistics(project['project_id'])
                project['statistics'] = project_stats
                dashboard_data['projects'].append(project)
            
            return dashboard_data
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    # Migration helper
    def migrate_from_sqlite(self, sqlite_db_path: str):
        """Migrate data from SQLite database"""
        import sqlite3
        
        try:
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # Migrate users
            cursor = sqlite_conn.execute("SELECT * FROM users")
            for row in cursor.fetchall():
                user_data = dict(row)
                if 'password_hash' in user_data and user_data['password_hash']:
                    # User already exists, skip
                    continue
                
                self.create_user(
                    email=user_data['email'],
                    name=user_data['name'],
                    role=user_data.get('role', 'user'),
                    preferences=self._deserialize_json(user_data.get('preferences'))
                )
            
            # Migrate projects
            cursor = sqlite_conn.execute("SELECT * FROM projects")
            for row in cursor.fetchall():
                project_data = dict(row)
                self.create_project(
                    user_id=project_data['user_id'],
                    domain=project_data['domain'],
                    name=project_data['name'],
                    settings=self._deserialize_json(project_data.get('settings'))
                )
            
            sqlite_conn.close()
            logger.info("Migration from SQLite completed successfully")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise
