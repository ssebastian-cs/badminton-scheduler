#!/usr/bin/env python3
"""
Test script to verify error tracking functionality.
"""

import requests
import time
import json

def test_error_tracking():
    """Test the error tracking system by generating some errors."""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing error tracking system...")
    
    # Test 1: Generate a 404 error
    print("1. Testing 404 error...")
    try:
        response = requests.get(f"{base_url}/nonexistent-page")
        print(f"   404 response: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Test health endpoint
    print("2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Health status: {health_data.get('status')}")
            print(f"   Error count (last hour): {health_data.get('errors', {}).get('last_hour_count', 0)}")
        else:
            print(f"   Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Try to access admin without authentication (should get 403)
    print("3. Testing unauthorized admin access...")
    try:
        response = requests.get(f"{base_url}/admin/")
        print(f"   Admin access response: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Wait a moment for error tracking to process
    time.sleep(2)
    
    # Test 4: Check health again to see if errors were tracked
    print("4. Checking health after errors...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Health status: {health_data.get('status')}")
            print(f"   Error count (last hour): {health_data.get('errors', {}).get('last_hour_count', 0)}")
            print(f"   Critical errors: {health_data.get('errors', {}).get('critical_count', 0)}")
        else:
            print(f"   Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("Error tracking test completed!")

if __name__ == "__main__":
    test_error_tracking()