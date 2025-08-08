#!/usr/bin/env python3
"""
Simple script to test the API endpoints.
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_api():
    """Test the main API endpoints."""
    
    print("Testing Badminton Scheduler API...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return
    
    # Test main endpoint
    try:
        response = requests.get(f'{BASE_URL}/')
        print(f"✓ Main endpoint: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Main endpoint failed: {e}")
    
    # Test login
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
        print(f"✓ Login test: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
            
            # Store session for further tests
            session = requests.Session()
            session.post(f'{BASE_URL}/auth/login', json=login_data)
            
            # Test getting current user
            me_response = session.get(f'{BASE_URL}/auth/me')
            print(f"✓ Get current user: {me_response.status_code}")
            if me_response.status_code == 200:
                print(f"  Response: {me_response.json()}")
            
            # Test getting availability
            avail_response = session.get(f'{BASE_URL}/api/availability')
            print(f"✓ Get availability: {avail_response.status_code}")
            if avail_response.status_code == 200:
                data = avail_response.json()
                print(f"  Found {len(data)} availability entries")
            
            # Test getting feedback
            feedback_response = session.get(f'{BASE_URL}/api/feedback')
            print(f"✓ Get feedback: {feedback_response.status_code}")
            if feedback_response.status_code == 200:
                data = feedback_response.json()
                print(f"  Found {len(data)} feedback entries")
        
    except Exception as e:
        print(f"✗ Login test failed: {e}")
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == '__main__':
    test_api()