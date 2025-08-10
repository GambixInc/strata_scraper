#!/usr/bin/env python3
"""
Test script for AWS Cognito authentication system
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_cognito_authentication():
    """Test the AWS Cognito authentication flow"""
    
    print("Testing AWS Cognito Authentication System")
    print("=" * 50)
    
    # Test 1: Get user profile (requires valid Cognito token)
    print("\n1. Testing get user profile...")
    print("Note: This requires a valid AWS Cognito token in the Authorization header")
    print("Expected: 401 Unauthorized (no token) or 200 OK (with valid token)")
    
    response = requests.get(f"{BASE_URL}/api/user/profile")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected request without token")
    else:
        print(f"Response: {response.json()}")
    
    # Test 2: Get user projects (requires valid Cognito token)
    print("\n2. Testing get user projects...")
    print("Expected: 401 Unauthorized (no token) or 200 OK (with valid token)")
    
    response = requests.get(f"{BASE_URL}/api/projects")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected request without token")
    else:
        print(f"Response: {response.json()}")
    
    # Test 3: Get dashboard data (requires valid Cognito token)
    print("\n3. Testing get dashboard data...")
    print("Expected: 401 Unauthorized (no token) or 200 OK (with valid token)")
    
    response = requests.get(f"{BASE_URL}/api/dashboard")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected request without token")
    else:
        print(f"Response: {response.json()}")
    
    # Test 4: Create project (requires valid Cognito token)
    print("\n4. Testing create project...")
    print("Expected: 401 Unauthorized (no token) or 200 OK (with valid token)")
    
    project_data = {
        "websiteUrl": "https://example.com",
        "category": "Technology",
        "description": "Test project"
    }
    
    response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected request without token")
    else:
        print(f"Response: {response.json()}")
    
    # Test 5: Test with invalid token
    print("\n5. Testing with invalid token...")
    print("Expected: 401 Unauthorized")
    
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected invalid token")
    else:
        print(f"Response: {response.json()}")
    
    print("\n" + "=" * 50)
    print("AWS Cognito authentication system test completed!")
    print("\nTo test with a real Cognito token:")
    print("1. Get a valid token from your AWS Cognito setup")
    print("2. Use it in the Authorization header: 'Bearer <token>'")
    print("3. Run the tests again")

if __name__ == "__main__":
    test_cognito_authentication()
