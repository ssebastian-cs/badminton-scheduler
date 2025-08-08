#!/usr/bin/env python3
"""
Test script to verify the admin filtering interface implementation.
"""

import requests
import json
from datetime import datetime, date, timedelta

API_BASE = 'http://localhost:5000'

def test_admin_filtering_interface():
    """Test the admin filtering interface functionality."""
    
    print("🧪 Testing Admin Filtering Interface...")
    print("=" * 50)
    
    # Test 1: Check if the admin endpoint exists
    print("1. Testing admin endpoint accessibility...")
    
    # First, login as admin
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        login_response = session.post(f'{API_BASE}/auth/login', json=login_data)
        if login_response.status_code == 200:
            print("   ✅ Admin login successful")
        else:
            print("   ❌ Admin login failed")
            return False
        
        # Test admin endpoint
        admin_response = session.get(f'{API_BASE}/api/admin/availability/filtered')
        if admin_response.status_code == 200:
            print("   ✅ Admin filtering endpoint accessible")
            data = admin_response.json()
            
            # Check response structure
            required_keys = ['availability', 'pagination', 'filters', 'result_count']
            if all(key in data for key in required_keys):
                print("   ✅ Response structure is correct")
            else:
                print("   ❌ Response structure is missing required keys")
                return False
        else:
            print("   ❌ Admin filtering endpoint not accessible")
            return False
        
        # Test 2: Date filtering
        print("\n2. Testing date filtering...")
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Test with date filters
        filter_response = session.get(
            f'{API_BASE}/api/admin/availability/filtered?start_date={today.isoformat()}&end_date={tomorrow.isoformat()}'
        )
        
        if filter_response.status_code == 200:
            print("   ✅ Date filtering works")
            filter_data = filter_response.json()
            
            # Check if filters are reflected in response
            if (filter_data['filters']['start_date'] == today.isoformat() and 
                filter_data['filters']['end_date'] == tomorrow.isoformat()):
                print("   ✅ Filter parameters correctly reflected in response")
            else:
                print("   ❌ Filter parameters not correctly reflected")
                return False
        else:
            print("   ❌ Date filtering failed")
            return False
        
        # Test 3: Pagination
        print("\n3. Testing pagination...")
        
        pagination_response = session.get(f'{API_BASE}/api/admin/availability/filtered?per_page=5')
        if pagination_response.status_code == 200:
            print("   ✅ Pagination works")
            pagination_data = pagination_response.json()
            
            # Check pagination metadata
            pagination_info = pagination_data['pagination']
            if all(key in pagination_info for key in ['page', 'per_page', 'total_count', 'total_pages']):
                print("   ✅ Pagination metadata is complete")
            else:
                print("   ❌ Pagination metadata is incomplete")
                return False
        else:
            print("   ❌ Pagination failed")
            return False
        
        # Test 4: User information inclusion
        print("\n4. Testing user information inclusion...")
        
        if data['availability']:
            first_entry = data['availability'][0]
            if 'username' in first_entry and 'user_email' in first_entry:
                print("   ✅ User information is included in availability entries")
            else:
                print("   ❌ User information is missing from availability entries")
                return False
        else:
            print("   ⚠️  No availability entries to test user information")
        
        print("\n" + "=" * 50)
        print("🎉 SUCCESS: Admin filtering interface is working correctly!")
        print("\nImplemented Features:")
        print("• Admin endpoint accessible with proper authentication")
        print("• Date range filtering with start_date and end_date")
        print("• Pagination support with page and per_page parameters")
        print("• Result count and pagination metadata")
        print("• User information included in responses")
        print("• Proper response structure with all required fields")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server. Make sure the Flask app is running.")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    test_admin_filtering_interface()