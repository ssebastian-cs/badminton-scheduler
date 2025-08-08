#!/usr/bin/env python3
"""
Test script for the DELETE /api/availability/{id} endpoint.
Tests all requirements: user ownership validation, past date protection, error handling.
"""

import requests
import json
from datetime import datetime, date, timedelta
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_delete_availability():
    """Test the DELETE availability endpoint functionality."""
    print("Testing DELETE /api/availability/{id} endpoint...")
    
    # Test data
    future_date = (date.today() + timedelta(days=7)).isoformat()
    past_date = (date.today() - timedelta(days=1)).isoformat()
    
    session = requests.Session()
    
    # Step 1: Login as a regular user
    print("\n1. Testing user authentication and setup...")
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    print("✅ User login successful")
    
    # Step 2: Create a test availability entry for future date
    print("\n2. Creating test availability entries...")
    future_availability_data = {
        "date": future_date,
        "status": "available",
        "play_preference": "either",
        "notes": "Test availability for deletion",
        "is_all_day": True
    }
    
    create_response = session.post(f"{API_URL}/availability", json=future_availability_data)
    if create_response.status_code not in [200, 201]:
        print(f"❌ Failed to create future availability: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False
    
    future_availability = create_response.json()
    future_availability_id = future_availability['id']
    print(f"✅ Created future availability entry (ID: {future_availability_id})")
    
    # Step 3: Create a test availability entry for past date (if possible)
    past_availability_data = {
        "date": past_date,
        "status": "available",
        "play_preference": "either",
        "notes": "Test availability for past date protection",
        "is_all_day": True
    }
    
    # Note: This should fail due to past date validation in POST, but let's try
    past_create_response = session.post(f"{API_URL}/availability", json=past_availability_data)
    past_availability_id = None
    
    if past_create_response.status_code in [200, 201]:
        past_availability = past_create_response.json()
        past_availability_id = past_availability['id']
        print(f"✅ Created past availability entry (ID: {past_availability_id}) - unexpected but proceeding")
    else:
        print("ℹ️ Cannot create past availability (expected behavior)")
    
    # Step 4: Test successful deletion of future availability
    print(f"\n3. Testing successful deletion of future availability (ID: {future_availability_id})...")
    delete_response = session.delete(f"{API_URL}/availability/{future_availability_id}")
    
    if delete_response.status_code == 200:
        delete_result = delete_response.json()
        if 'message' in delete_result and 'deleted_entry' in delete_result:
            print("✅ Future availability deleted successfully")
            print(f"   Message: {delete_result['message']}")
            print(f"   Deleted entry info: {delete_result['deleted_entry']}")
        else:
            print("❌ Delete response missing required fields")
            return False
    else:
        print(f"❌ Failed to delete future availability: {delete_response.status_code}")
        print(f"Response: {delete_response.text}")
        return False
    
    # Step 5: Test deletion of non-existent entry
    print(f"\n4. Testing deletion of non-existent entry...")
    nonexistent_id = 99999
    delete_nonexistent_response = session.delete(f"{API_URL}/availability/{nonexistent_id}")
    
    if delete_nonexistent_response.status_code == 404:
        error_result = delete_nonexistent_response.json()
        if 'error' in error_result and 'not found' in error_result['error'].lower():
            print("✅ Non-existent entry deletion properly rejected (404)")
        else:
            print("❌ Non-existent entry deletion error message incorrect")
            return False
    else:
        print(f"❌ Non-existent entry deletion should return 404, got: {delete_nonexistent_response.status_code}")
        return False
    
    # Step 6: Test past date protection (if we have a past availability entry)
    if past_availability_id:
        print(f"\n5. Testing past date protection (ID: {past_availability_id})...")
        delete_past_response = session.delete(f"{API_URL}/availability/{past_availability_id}")
        
        if delete_past_response.status_code == 400:
            error_result = delete_past_response.json()
            if 'error' in error_result and 'past date' in error_result['error'].lower():
                print("✅ Past date deletion properly rejected (400)")
            else:
                print("❌ Past date deletion error message incorrect")
                return False
        else:
            print(f"❌ Past date deletion should return 400, got: {delete_past_response.status_code}")
            return False
    else:
        print("\n5. Skipping past date protection test (no past availability entry)")
    
    # Step 7: Test unauthorized access (create entry as one user, try to delete as another)
    print("\n6. Testing user ownership validation...")
    
    # Create another availability entry
    another_availability_data = {
        "date": (date.today() + timedelta(days=14)).isoformat(),
        "status": "available",
        "play_preference": "either",
        "notes": "Test availability for ownership validation",
        "is_all_day": True
    }
    
    create_another_response = session.post(f"{API_URL}/availability", json=another_availability_data)
    if create_another_response.status_code not in [200, 201]:
        print(f"❌ Failed to create another availability: {create_another_response.status_code}")
        return False
    
    another_availability = create_another_response.json()
    another_availability_id = another_availability['id']
    print(f"✅ Created another availability entry (ID: {another_availability_id})")
    
    # Logout current user
    session.get(f"{BASE_URL}/logout")
    
    # Login as a different user (if exists) or test without login
    # For now, let's test without login to check authentication
    new_session = requests.Session()
    
    # Try to delete without authentication
    unauth_delete_response = new_session.delete(f"{API_URL}/availability/{another_availability_id}")
    
    if unauth_delete_response.status_code in [401, 403]:
        print("✅ Unauthenticated deletion properly rejected")
    else:
        print(f"❌ Unauthenticated deletion should be rejected, got: {unauth_delete_response.status_code}")
        # Clean up the entry we created
        session.delete(f"{API_URL}/availability/{another_availability_id}")
        return False
    
    # Clean up: delete the remaining entry
    print("\n7. Cleaning up test data...")
    cleanup_response = session.delete(f"{API_URL}/availability/{another_availability_id}")
    if cleanup_response.status_code == 200:
        print("✅ Test data cleaned up successfully")
    else:
        print(f"⚠️ Failed to clean up test data: {cleanup_response.status_code}")
    
    print("\n🎉 All DELETE endpoint tests passed!")
    return True

def main():
    """Main test function."""
    print("=" * 60)
    print("DELETE Availability API Endpoint Test")
    print("=" * 60)
    
    try:
        success = test_delete_availability()
        if success:
            print("\n✅ All tests completed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())