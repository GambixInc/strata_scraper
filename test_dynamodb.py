#!/usr/bin/env python3
"""
Test script for DynamoDB database implementation
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
    parser = argparse.ArgumentParser(description='Test DynamoDB database functionality')
    parser.add_argument('--table-prefix', type=str, default='gambix_strata_test',
                       help='Prefix for DynamoDB table names')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Environment file to load')
    return parser.parse_args()

def test_user_operations(db):
    """Test user-related operations"""
    logger.info("🧪 Testing User Operations...")
    
    # Create a test user
    user_id = db.create_user(
        email="test@example.com",
        name="Test User",
        password="testpassword123",
        role="user"
    )
    logger.info(f"✅ Created user with ID: {user_id}")
    
    # Get user by ID
    user = db.get_user(user_id)
    if user and user['email'] == "test@example.com":
        logger.info("✅ Get user by ID works")
    else:
        logger.error("❌ Get user by ID failed")
        return False
    
    # Get user by email
    user_by_email = db.get_user_by_email("test@example.com")
    if user_by_email and user_by_email['user_id'] == user_id:
        logger.info("✅ Get user by email works")
    else:
        logger.error("❌ Get user by email failed")
        return False
    
    # Test authentication
    auth_user = db.authenticate_user("test@example.com", "testpassword123")
    if auth_user and auth_user['user_id'] == user_id:
        logger.info("✅ User authentication works")
    else:
        logger.error("❌ User authentication failed")
        return False
    
    # Test failed authentication
    failed_auth = db.authenticate_user("test@example.com", "wrongpassword")
    if not failed_auth:
        logger.info("✅ Failed authentication correctly rejected")
    else:
        logger.error("❌ Failed authentication should have been rejected")
        return False
    
    return True

def test_project_operations(db):
    """Test project-related operations"""
    logger.info("🧪 Testing Project Operations...")
    
    # Create a test user first
    user_id = db.create_user(
        email="project_test@example.com",
        name="Project Test User",
        role="user"
    )
    
    # Create a test project
    project_id = db.create_project(
        user_id=user_id,
        domain="example.com",
        name="Test Project",
        settings={"auto_optimize": True}
    )
    logger.info(f"✅ Created project with ID: {project_id}")
    
    # Get project by ID
    project = db.get_project(project_id)
    if project and project['domain'] == "example.com":
        logger.info("✅ Get project by ID works")
    else:
        logger.error("❌ Get project by ID failed")
        return False
    
    # Get user projects
    user_projects = db.get_user_projects(user_id)
    if user_projects and len(user_projects) > 0:
        logger.info(f"✅ Get user projects works (found {len(user_projects)} projects)")
    else:
        logger.error("❌ Get user projects failed")
        return False
    
    # Get project by user and domain
    project_by_domain = db.get_project_by_user_and_domain(user_id, "example.com")
    if project_by_domain and project_by_domain['project_id'] == project_id:
        logger.info("✅ Get project by user and domain works")
    else:
        logger.error("❌ Get project by user and domain failed")
        return False
    
    # Update project status
    db.update_project_status(project_id, "inactive")
    updated_project = db.get_project(project_id)
    if updated_project and updated_project['status'] == "inactive":
        logger.info("✅ Update project status works")
    else:
        logger.error("❌ Update project status failed")
        return False
    
    return True

def test_site_health_operations(db):
    """Test site health operations"""
    logger.info("🧪 Testing Site Health Operations...")
    
    # Create test user and project
    user_id = db.create_user(
        email="health_test@example.com",
        name="Health Test User",
        role="user"
    )
    project_id = db.create_project(
        user_id=user_id,
        domain="health-test.com",
        name="Health Test Project"
    )
    
    # Add site health data
    health_data = {
        'overall_score': 85,
        'technical_seo': 90,
        'content_seo': 80,
        'performance': 75,
        'internal_linking': 85,
        'visual_ux': 90,
        'authority_backlinks': 70,
        'crawl_data': {"pages_crawled": 10, "errors": 0}
    }
    
    health_id = db.add_site_health(project_id, health_data)
    logger.info(f"✅ Added site health with ID: {health_id}")
    
    # Get latest site health
    latest_health = db.get_latest_site_health(project_id)
    if latest_health and latest_health['overall_score'] == 85:
        logger.info("✅ Get latest site health works")
    else:
        logger.error("❌ Get latest site health failed")
        return False
    
    # Get site health history
    health_history = db.get_site_health_history(project_id)
    if health_history and len(health_history) > 0:
        logger.info(f"✅ Get site health history works (found {len(health_history)} records)")
    else:
        logger.error("❌ Get site health history failed")
        return False
    
    return True

def test_recommendation_operations(db):
    """Test recommendation operations"""
    logger.info("🧪 Testing Recommendation Operations...")
    
    # Create test user and project
    user_id = db.create_user(
        email="rec_test@example.com",
        name="Recommendation Test User",
        role="user"
    )
    project_id = db.create_project(
        user_id=user_id,
        domain="rec-test.com",
        name="Recommendation Test Project"
    )
    
    # Add recommendation
    recommendation_data = {
        'category': 'SEO',
        'issue': 'Missing meta descriptions',
        'recommendation': 'Add meta descriptions to all pages',
        'priority': 'high',
        'impact_score': 75,
        'guidelines': ['Use 150-160 characters', 'Include target keywords']
    }
    
    rec_id = db.add_recommendation(project_id, recommendation_data)
    logger.info(f"✅ Added recommendation with ID: {rec_id}")
    
    # Get project recommendations
    recommendations = db.get_project_recommendations(project_id, 'pending')
    if recommendations and len(recommendations) > 0:
        logger.info(f"✅ Get project recommendations works (found {len(recommendations)} recommendations)")
    else:
        logger.error("❌ Get project recommendations failed")
        return False
    
    # Update recommendation status
    db.update_recommendation_status(rec_id, 'accepted')
    updated_recs = db.get_project_recommendations(project_id, 'accepted')
    if updated_recs and len(updated_recs) > 0:
        logger.info("✅ Update recommendation status works")
    else:
        logger.error("❌ Update recommendation status failed")
        return False
    
    return True

def test_dashboard_operations(db):
    """Test dashboard operations"""
    logger.info("🧪 Testing Dashboard Operations...")
    
    # Create test user and project
    user_id = db.create_user(
        email="dashboard_test@example.com",
        name="Dashboard Test User",
        role="user"
    )
    project_id = db.create_project(
        user_id=user_id,
        domain="dashboard-test.com",
        name="Dashboard Test Project"
    )
    
    # Add some test data
    db.add_site_health(project_id, {'overall_score': 80})
    db.add_recommendation(project_id, {
        'category': 'Performance',
        'issue': 'Slow loading',
        'recommendation': 'Optimize images',
        'priority': 'medium'
    })
    
    # Get dashboard data
    dashboard_data = db.get_dashboard_data(user_id)
    if dashboard_data and 'total_projects' in dashboard_data:
        logger.info(f"✅ Get dashboard data works (found {dashboard_data['total_projects']} projects)")
    else:
        logger.error("❌ Get dashboard data failed")
        return False
    
    # Get project statistics
    project_stats = db.get_project_statistics(project_id)
    if project_stats and 'total_pages' in project_stats:
        logger.info("✅ Get project statistics works")
    else:
        logger.error("❌ Get project statistics failed")
        return False
    
    return True

def main():
    """Main test function"""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    logger.info("🚀 DynamoDB Database Test Suite")
    logger.info("=" * 50)
    
    # Check AWS credentials
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        logger.error("❌ AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        sys.exit(1)
    
    try:
        # Initialize database
        logger.info(f"Initializing DynamoDB with table prefix: {args.table_prefix}")
        db = DynamoDBDatabase(table_prefix=args.table_prefix)
        
        # Run tests
        tests = [
            test_user_operations,
            test_project_operations,
            test_site_health_operations,
            test_recommendation_operations,
            test_dashboard_operations
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test(db):
                    passed += 1
                    logger.info(f"✅ {test.__name__} PASSED")
                else:
                    logger.error(f"❌ {test.__name__} FAILED")
            except Exception as e:
                logger.error(f"❌ {test.__name__} FAILED with exception: {e}")
        
        logger.info("=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! DynamoDB implementation is working correctly.")
        else:
            logger.error("❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
