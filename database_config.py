#!/usr/bin/env python3
"""
Database Configuration
Uses DynamoDB for all database operations
"""

import os

# Always use DynamoDB
USE_DYNAMODB = True

# Import DynamoDB database manager
from dynamodb_database import DynamoDBDatabase
from dynamodb_database import (
    add_scraped_site, 
    add_optimized_site, 
    get_site_stats, 
    export_summary, 
    get_sites_by_user_email, 
    get_all_sites,
    GambixStrataDatabase
)

# Use DynamoDBDatabase as the main Database class
Database = DynamoDBDatabase

# Export the database class and functions
__all__ = [
    'Database',
    'GambixStrataDatabase', 
    'add_scraped_site',
    'add_optimized_site',
    'get_site_stats',
    'export_summary',
    'get_sites_by_user_email',
    'get_all_sites',
    'USE_DYNAMODB'
]
