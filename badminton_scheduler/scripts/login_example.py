#!/usr/bin/env python3
"""
Example script showing how to log in programmatically
"""

import requests
import json

# Create a session to maintain cookies
session = requests.Session()

def login(username, password):
    """Login to the badminton scheduler API"""
    login_data = {
        "username": username,
        "password": password
    }
    
    response = session.post(
        "http://localhost:5000/auth/login",
        json=login_data
    )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Logged in successfully as {user_data['user']['username']}")
        print(f"   Admin: {user_data['user']['is_admin']}")
        return True
    else:
        print(f"❌ Login failed: {response.json().get('error', 'Unknown error')}")
        return False

def get_availability():
    """Get availability data (requires login)"""
    response = session.get("http://localhost:5000/api/availability")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data)} availability entries")
        return data
    else:
        print(f"❌ Failed to get availability: {response.status_code}")
        return None

def delete_availability(availability_id):
    """Delete an availability entry (requires login)"""
    response = session.delete(f"http://localhost:5000/api/availability/{availability_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Deleted availability entry: {result['message']}")
        return True
    else:
        error = response.json().get('error', 'Unknown error')
        print(f"❌ Failed to delete availability: {error}")
        return False

if __name__ == "__main__":
    # Example usage
    print("Badminton Scheduler API Login Example")
    print("=" * 40)
    
    # Login as regular user
    if login("john_smith", "password123"):
        # Get availability data
        availability_data = get_availability()
        
        if availability_data:
            print("\nYour availability entries:")
            for entry in availability_data:
                print(f"  - {entry['date']}: {entry['status']}")
                if not entry.get('is_all_day', True):
                    print(f"    Time: {entry.get('time_start', 'N/A')} - {entry.get('time_end', 'N/A')}")
    
    print("\n" + "=" * 40)
    
    # Login as admin
    if login("admin", "admin123"):
        print("Logged in as admin - you have additional privileges")