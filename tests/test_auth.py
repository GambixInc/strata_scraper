#!/usr/bin/env python3
"""
Test script for authentication system
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_authentication():
    """Test the complete authentication flow"""
    
    print("Testing Authentication System")
    print("=" * 40)
    
    # Test 1: Register a new user
    print("\n1. Testing user registration...")
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        register_result = response.json()
        token = register_result['data']['token']
        print(f"✅ Registration successful. Token: {token[:20]}...")
    else:
        print("❌ Registration failed")
        return
    
    # Test 2: Login with the same user
    print("\n2. Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        login_result = response.json()
        token = login_result['data']['token']
        print(f"✅ Login successful. Token: {token[:20]}...")
    else:
        print("❌ Login failed")
        return
    
    # Test 3: Get user profile
    print("\n3. Testing get user profile...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Get profile successful")
    else:
        print("❌ Get profile failed")
    
    # Test 4: Create a project
    print("\n4. Testing project creation...")
    project_data = {
        "websiteUrl": "https://example.com",
        "category": "Technology",
        "description": "Test project"
    }
    
    response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Project creation successful")
    else:
        print("❌ Project creation failed")
    
    # Test 5: Get user projects
    print("\n5. Testing get user projects...")
    
    response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Get projects successful")
    else:
        print("❌ Get projects failed")
    
    # Test 6: Get dashboard data
    print("\n6. Testing get dashboard data...")
    
    response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Get dashboard successful")
    else:
        print("❌ Get dashboard failed")
    
    # Test 7: Test invalid token
    print("\n7. Testing invalid token...")
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=invalid_headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        print("✅ Invalid token correctly rejected")
    else:
        print("❌ Invalid token not properly handled")
    
    print("\n" + "=" * 40)
    print("Authentication system test completed!")

if __name__ == "__main__":
    test_authentication()
