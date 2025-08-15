#!/usr/bin/env python3
"""
Script to update existing projects to use S3 paths instead of local paths
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamodb_database import DynamoDBDatabase

def update_project_paths():
    """Update existing projects to use S3 paths"""
    
    print("🔄 Updating project paths to use S3...")
    
    try:
        # Initialize database
        db = DynamoDBDatabase()
        
        # Get all projects
        all_projects = []
        
        # Get projects for all users (we'll need to iterate through users)
        # For now, let's check if we can get projects directly
        try:
            # Try to get all projects (this might not work depending on your DynamoDB setup)
            # We'll need to handle this differently
            print("⚠️  This script needs to be run with specific project IDs")
            print("   Please provide the project ID you want to update")
            return
        except Exception as e:
            print(f"Error getting all projects: {e}")
            return
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return

def update_specific_project(project_id):
    """Update a specific project to use S3 path"""
    
    print(f"🔄 Updating project {project_id}...")
    
    try:
        # Initialize database
        db = DynamoDBDatabase()
        
        # Get the project
        project = db.get_project(project_id)
        if not project:
            print(f"❌ Project {project_id} not found")
            return False
        
        current_path = project.get('scraped_files_path', '')
        print(f"Current path: {current_path}")
        
        # Check if it's already an S3 path
        if current_path.startswith('s3://'):
            print(f"✅ Project {project_id} already uses S3 path")
            return True
        
        # Convert local path to S3 path
        if current_path and not current_path.startswith('s3://'):
            # Handle different path formats:
            # 1. Full local path: "/home/ubuntu/strata_scraper/scraped_sites/_python.org_20250815_031130_918_762855c9"
            # 2. Relative path: "scraped_sites/_python.org_20250815_031130_918_762855c9"
            # 3. Just directory name: "_python.org_20250815_031130_918_762855c9"
            
            # Extract the directory name from the path
            if '/' in current_path:
                # If it's a full path, get the last part
                dir_name = os.path.basename(current_path)
            elif current_path.startswith('scraped_sites/'):
                # If it's a relative path starting with scraped_sites/
                dir_name = current_path.split('/')[-1]
            else:
                # If it's just the directory name
                dir_name = current_path
            
            # Construct full S3 path
            bucket_name = os.getenv('S3_BUCKET_NAME', 'gambix-strata-production')
            s3_path = f"s3://{bucket_name}/scraped_sites/{dir_name}"
            
            print(f"Converting: {current_path} -> {s3_path}")
            
            # Update the project
            db.update_project_scraped_files(project_id, s3_path)
            
            print(f"✅ Successfully updated project {project_id}")
            return True
        else:
            print(f"⚠️  Project {project_id} has no scraped_files_path")
            return False
            
    except Exception as e:
        print(f"❌ Error updating project {project_id}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        update_specific_project(project_id)
    else:
        print("Usage: python3 update_project_paths.py <project_id>")
        print("Example: python3 update_project_paths.py 182ccf22-517b-433a-a6eb-9e491c594d14")
