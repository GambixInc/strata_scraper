#!/usr/bin/env python3
"""
Test Configuration
Handles different test environments and configurations
"""

import os

# Test environment configuration
TEST_CONFIG = {
    'database': {
        'sqlite': {
            'use_dynamodb': False,
            'db_path': ':memory:'  # Use in-memory database for tests
        },
        'dynamodb': {
            'use_dynamodb': True,
            'aws_region': 'us-east-1',
            'table_prefix': 'test_'
        }
    },
    's3': {
        'bucket_name': 'test-bucket',
        'region': 'us-east-1'
    },
    'scraping': {
        'test_url': 'https://httpbin.org/html',
        'timeout': 10
    }
}

def get_test_config():
    """Get test configuration based on environment"""
    # Check if we're in a test environment
    test_env = os.getenv('TEST_ENV', 'default')
    
    if test_env == 'docker':
        # Docker environment - use production-like settings
        return {
            'database': TEST_CONFIG['database']['dynamodb'],
            's3': TEST_CONFIG['s3'],
            'scraping': TEST_CONFIG['scraping']
        }
    else:
        # Local development environment
        return {
            'database': TEST_CONFIG['database']['sqlite'],
            's3': TEST_CONFIG['s3'],
            'scraping': TEST_CONFIG['scraping']
        }

def setup_test_environment():
    """Set up test environment variables"""
    config = get_test_config()
    
    # Set database configuration
    if config['database']['use_dynamodb']:
        os.environ['USE_DYNAMODB'] = 'true'
        os.environ['AWS_REGION'] = config['database']['aws_region']
        os.environ['DYNAMODB_TABLE_PREFIX'] = config['database']['table_prefix']
    else:
        os.environ['USE_DYNAMODB'] = 'false'
    
    # Set S3 configuration
    os.environ['S3_BUCKET_NAME'] = config['s3']['bucket_name']
    os.environ['S3_ENDPOINT_URL'] = 'https://s3.amazonaws.com'
    
    # Set other test environment variables
    os.environ['TEST_ENV'] = 'true'
    os.environ['DEBUG'] = 'true'
