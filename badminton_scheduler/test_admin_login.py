#!/usr/bin/env python3
"""
Simple test to verify admin login functionality.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_admin_login():
    """Test admin login functionality."""
    print("Testing admin login...")
    
    # Test admin credentials
    admin_credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # Attempt login
        print(f"Attempting to login with admin credentials...")
        response = session.post(f"{BASE_URL}/auth/login", json=admin_credentials)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Admin login successful!")
            print(f"User info: {json.dumps(data, indent=2)}")
            
            # Test admin endpoint access
            print("\nTesting admin endpoint access...")
            admin_response = session.get(f"{BASE_URL}/api/admin/users")
            
            if admin_response.status_code == 200:
                users = admin_response.json()
                print(f"✓ Admin endpoint accessible! Found {len(users)} users.")
                for user in users:
                    print(f"  - {user['username']} ({'admin' if user['is_admin'] else 'user'})")
            else:
                print(f"✗ Admin endpoint failed: {admin_response.status_code}")
                print(f"Error: {admin_response.text}")
                
        else:
            print(f"✗ Admin login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Error response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the server is running at http://localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True

def test_regular_user_login():
    """Test regular user login functionality."""
    print("\n" + "="*50)
    print("Testing regular user login...")
    
    # Test regular user credentials
    user_credentials = {
        "username": "john_smith",
        "password": "password123"
    }
    
    session = requests.Session()
    
    try:
        # Attempt login
        print(f"Attempting to login with regular user credentials...")
        response = session.post(f"{BASE_URL}/auth/login", json=user_credentials)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Regular user login successful!")
            print(f"User info: {json.dumps(data, indent=2)}")
            
            # Test that regular user cannot access admin endpoints
            print("\nTesting admin endpoint restriction...")
            admin_response = session.get(f"{BASE_URL}/api/admin/users")
            
            if admin_response.status_code == 403:
                print("✓ Admin endpoint properly restricted for regular users!")
            else:
                print(f"✗ Admin endpoint should be restricted but got: {admin_response.status_code}")
                
        else:
            print(f"✗ Regular user login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Error response: {response.text}")
    
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True

def test_validation_sample():
    """Test a few validation cases."""
    print("\n" + "="*50)
    print("Testing validation (sample)...")
    
    session = requests.Session()
    
    # Login as regular user first
    user_credentials = {"username": "john_smith", "password": "password123"}
    login_response = session.post(f"{BASE_URL}/auth/login", json=user_credentials)
    
    if login_response.status_code != 200:
        print("✗ Could not login for validation test")
        return False
    
    # Test invalid time validation
    print("Testing invalid time validation...")
    invalid_data = {
        "date": "2025-08-15",
        "status": "available",
        "is_all_day": False,
        "time_start": "25:00",  # Invalid hour
        "time_end": "17:00"
    }
    
    response = session.post(f"{BASE_URL}/api/availability", json=invalid_data)
    
    if response.status_code == 400:
        error_data = response.json()
        print(f"✓ Invalid time properly rejected: {error_data.get('error', 'Unknown error')}")
    else:
        print(f"✗ Invalid time should be rejected but got: {response.status_code}")
    
    # Test invalid date validation
    print("Testing past date validation...")
    past_date_data = {
        "date": "2020-01-01",  # Past date
        "status": "available",
        "is_all_day": True
    }
    
    response = session.post(f"{BASE_URL}/api/availability", json=past_date_data)
    
    if response.status_code == 400:
        error_data = response.json()
        print(f"✓ Past date properly rejected: {error_data.get('error', 'Unknown error')}")
    else:
        print(f"✗ Past date should be rejected but got: {response.status_code}")
    
    return True

def main():
    """Run all tests."""
    print("Starting admin login and validation tests...\n")
    
    success = True
    success &= test_admin_login()
    success &= test_regular_user_login()
    success &= test_validation_sample()
    
    print("\n" + "="*50)
    if success:
        print("✓ All tests completed! Check results above.")
    else:
        print("✗ Some tests failed. Check results above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())