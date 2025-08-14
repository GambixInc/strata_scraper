#!/usr/bin/env python3
"""
Database Configuration
Uses DynamoDB for all database operations
"""

import os

# Import DynamoDB database manager
from dynamodb_database import DynamoDBDatabase

# Use DynamoDBDatabase as the main Database class
Database = DynamoDBDatabase
GambixStrataDatabase = DynamoDBDatabase

# Export the database class
__all__ = [
    'Database',
    'GambixStrataDatabase'
]
