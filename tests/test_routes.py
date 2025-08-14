#!/usr/bin/env python3
"""
Test script to check route registration
"""

from server import app

def test_routes():
    """Test if routes are properly registered"""
    
    print("Testing Route Registration")
    print("=" * 40)
    
    # Check all routes
    print("\nAll registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.methods}")
    
    # Check specifically for auth routes
    print("\nAuthentication routes:")
    auth_routes = [rule for rule in app.url_map.iter_rules() if 'api/auth' in rule.rule]
    for rule in auth_routes:
        print(f"{rule.rule} -> {rule.methods}")
    
    # Check if catch-all route is in the right place
    print("\nCatch-all route:")
    catch_all_routes = [rule for rule in app.url_map.iter_rules() if rule.rule == '/' or rule.rule == '/<path:path>']
    for rule in catch_all_routes:
        print(f"{rule.rule} -> {rule.methods}")

if __name__ == "__main__":
    test_routes()
