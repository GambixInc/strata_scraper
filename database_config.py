#!/usr/bin/env python3
"""
Database Configuration
Switches between SQLite and DynamoDB based on environment variables
"""

import os

# Check if we should use DynamoDB
USE_DYNAMODB = os.getenv('USE_DYNAMODB', 'false').lower() == 'true'

if USE_DYNAMODB:
    from dynamodb_database import DynamoDBDatabase as Database
    from dynamodb_database import (
        add_scraped_site, 
        add_optimized_site, 
        get_site_stats, 
        export_summary, 
        get_sites_by_user_email, 
        get_all_sites,
        GambixStrataDatabase
    )
else:
    from database import Database, GambixStrataDatabase
    from database import (
        add_scraped_site, 
        add_optimized_site, 
        get_site_stats, 
        export_summary, 
        get_sites_by_user_email, 
        get_all_sites
    )

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
