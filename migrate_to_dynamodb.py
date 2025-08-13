#!/usr/bin/env python3
"""
Migration script to transition from SQLite to DynamoDB
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from dynamodb_database import DynamoDBDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Migrate from SQLite to DynamoDB')
    parser.add_argument('--sqlite-path', type=str, default='gambix_strata.db',
                       help='Path to SQLite database file')
    parser.add_argument('--table-prefix', type=str, default='gambix_strata',
                       help='Prefix for DynamoDB table names')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without actually doing it')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Environment file to load')
    return parser.parse_args()

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    try:
        import boto3
        # Test AWS credentials by trying to create a client
        # This will use the AWS CLI credential chain automatically
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"AWS credentials verified - Account: {identity['Account']}, User: {identity['Arn']}")
        return True
    except Exception as e:
        logger.error(f"AWS credentials not found or invalid: {e}")
        logger.error("Please ensure AWS CLI is configured or IAM role is attached")
        return False

def check_sqlite_exists(sqlite_path):
    """Check if SQLite database exists"""
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        return False
    return True

def get_sqlite_stats(sqlite_path):
    """Get statistics about SQLite database"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error getting SQLite stats: {e}")
        return {}

def migrate_data(sqlite_path, table_prefix, dry_run=False):
    """Migrate data from SQLite to DynamoDB"""
    if dry_run:
        logger.info("DRY RUN MODE - No data will be actually migrated")
    
    try:
        # Initialize DynamoDB
        db = DynamoDBDatabase(table_prefix=table_prefix)
        
        if dry_run:
            logger.info("Would initialize DynamoDB tables...")
        else:
            logger.info("Initializing DynamoDB tables...")
            db.init_database()
        
        # Get SQLite stats
        stats = get_sqlite_stats(sqlite_path)
        logger.info("SQLite database statistics:")
        for table, count in stats.items():
            logger.info(f"  {table}: {count} records")
        
        if dry_run:
            logger.info("Would migrate data from SQLite to DynamoDB...")
            return True
        
        # Perform migration
        logger.info("Starting migration...")
        db.migrate_from_sqlite(sqlite_path)
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def main():
    """Main migration function"""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    logger.info("🚀 SQLite to DynamoDB Migration Tool")
    logger.info("=" * 50)
    
    # Check prerequisites
    if not check_aws_credentials():
        sys.exit(1)
    
    if not check_sqlite_exists(args.sqlite_path):
        sys.exit(1)
    
    # Show configuration
    logger.info(f"SQLite database: {args.sqlite_path}")
    logger.info(f"DynamoDB table prefix: {args.table_prefix}")
    logger.info(f"AWS Region: {os.getenv('AWS_REGION', 'Not set')}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("")
    
    # Confirm migration
    if not args.dry_run:
        response = input("Do you want to proceed with the migration? (y/N): ")
        if response.lower() != 'y':
            logger.info("Migration cancelled")
            sys.exit(0)
    
    # Perform migration
    success = migrate_data(args.sqlite_path, args.table_prefix, args.dry_run)
    
    if success:
        logger.info("✅ Migration completed successfully!")
        if not args.dry_run:
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Update your application to use DynamoDBDatabase instead of GambixStrataDatabase")
            logger.info("2. Test the application with the new database")
            logger.info("3. Once confirmed working, you can remove the SQLite database")
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
