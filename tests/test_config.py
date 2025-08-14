#!/usr/bin/env python3
"""
Test Configuration
Handles different test environments and configurations
"""

import os

# Test environment configuration
TEST_CONFIG = {
    'database': {
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
    # Always use DynamoDB configuration
    return {
        'database': TEST_CONFIG['database']['dynamodb'],
        's3': TEST_CONFIG['s3'],
        'scraping': TEST_CONFIG['scraping']
    }

def setup_test_environment():
    """Set up test environment variables"""
    config = get_test_config()
    
    # Set database configuration (DynamoDB only)
    os.environ['AWS_REGION'] = config['database']['aws_region']
    os.environ['DYNAMODB_TABLE_PREFIX'] = config['database']['table_prefix']
    
    # Set S3 configuration
    os.environ['S3_BUCKET_NAME'] = config['s3']['bucket_name']
    os.environ['S3_ENDPOINT_URL'] = 'https://s3.amazonaws.com'
    
    # Set other test environment variables
    os.environ['TEST_ENV'] = 'true'
    os.environ['DEBUG'] = 'true'
