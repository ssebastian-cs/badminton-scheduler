#!/usr/bin/env python3
"""
Test script for Task 2 - Backend API enhancements for time support
Tests the enhanced POST /api/availability endpoint with time parameters.
"""

import json
import sys
import os
from datetime import date, timedelta

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User

def test_api_time_support():
    """Test the enhanced API with time support."""
    
    with app.app_context():
        # Create test client
        client = app.test_client()
        
        # Create or get test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
        
        # Login as test user
        login_response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        
        if login_response.status_code != 200:
            print("❌ Failed to login test user")
            return False
        
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        print("Testing API time support enhancements...\n")
        
        # Test 1: All-day availability (default behavior)
        print("Test 1: All-day availability")
        response = client.post('/api/availability', 
            json={
                'date': tomorrow,
                'status': 'available',
                'is_all_day': True,
                'play_preference': 'either',
                'notes': 'Available all day'
            },
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✅ Created all-day availability: {data}")
            assert data['is_all_day'] == True
            assert data['time_start'] is None
            assert data['time_end'] is None
        else:
            print(f"❌ Failed to create all-day availability: {response.status_code}")
            print(response.data.decode())
            return False
        
        # Test 2: Time-specific availability with separate start/end times
        print("\nTest 2: Time-specific availability (separate times)")
        day_after_tomorrow = (date.today() + timedelta(days=2)).isoformat()
        response = client.post('/api/availability',
            json={
                'date': day_after_tomorrow,
                'status': 'available',
                'is_all_day': False,
                'time_start': '7:00 PM',
                'time_end': '9:00 PM',
                'play_preference': 'either',
                'notes': 'Evening session'
            },
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✅ Created time-specific availability: {data}")
            assert data['is_all_day'] == False
            assert data['time_start'] == '19:00'
            assert data['time_end'] == '21:00'
        else:
            print(f"❌ Failed to create time-specific availability: {response.status_code}")
            print(response.data.decode())
            return False
        
        # Test 3: Time range format
        print("\nTest 3: Time range format")
        day_3 = (date.today() + timedelta(days=3)).isoformat()
        response = client.post('/api/availability',
            json={
                'date': day_3,
                'status': 'tentative',
                'is_all_day': False,
                'time_range': '19:00-21:00',
                'play_preference': 'drop_in',
                'notes': 'Using time range format'
            },
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✅ Created availability with time range: {data}")
            assert data['is_all_day'] == False
            assert data['time_start'] == '19:00'
            assert data['time_end'] == '21:00'
        else:
            print(f"❌ Failed to create availability with time range: {response.status_code}")
            print(response.data.decode())
            return False
        
        # Test 4: 12-hour format
        print("\nTest 4: 12-hour time format")
        day_4 = (date.today() + timedelta(days=4)).isoformat()
        response = client.post('/api/availability',
            json={
                'date': day_4,
                'status': 'available',
                'is_all_day': False,
                'time_range': '7-9 PM',
                'play_preference': 'book_court',
                'notes': '12-hour format test'
            },
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✅ Created availability with 12-hour format: {data}")
            assert data['is_all_day'] == False
            assert data['time_start'] == '19:00'
            assert data['time_end'] == '21:00'
        else:
            print(f"❌ Failed to create availability with 12-hour format: {response.status_code}")
            print(response.data.decode())
            return False
        
        # Test 5: Invalid time validation
        print("\nTest 5: Invalid time validation (end before start)")
        day_5 = (date.today() + timedelta(days=5)).isoformat()
        response = client.post('/api/availability',
            json={
                'date': day_5,
                'status': 'available',
                'is_all_day': False,
                'time_start': '9:00 PM',
                'time_end': '7:00 PM',
                'play_preference': 'either'
            },
            content_type='application/json'
        )
        
        if response.status_code == 400:
            error_data = json.loads(response.data)
            print(f"✅ Correctly rejected invalid time: {error_data}")
            assert 'End time must be after start time' in error_data['error']
        else:
            print(f"❌ Should have rejected invalid time: {response.status_code}")
            return False
        
        # Test 6: Invalid time format
        print("\nTest 6: Invalid time format validation")
        day_6 = (date.today() + timedelta(days=6)).isoformat()
        response = client.post('/api/availability',
            json={
                'date': day_6,
                'status': 'available',
                'is_all_day': False,
                'time_start': 'invalid_time',
                'play_preference': 'either'
            },
            content_type='application/json'
        )
        
        if response.status_code == 400:
            error_data = json.loads(response.data)
            print(f"✅ Correctly rejected invalid time format: {error_data}")
            assert 'Invalid time format' in error_data['error']
        else:
            print(f"❌ Should have rejected invalid time format: {response.status_code}")
            return False
        
        # Test 7: Get availability with enhanced time information
        print("\nTest 7: Get availability with enhanced time information")
        response = client.get('/api/availability')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✅ Retrieved {len(data)} availability entries with enhanced time info")
            
            # Check that entries have the new time fields
            for entry in data:
                print(f"  - Date: {entry['date']}, All-day: {entry['is_all_day']}, "
                      f"Start: {entry.get('time_start')}, End: {entry.get('time_end')}")
                assert 'is_all_day' in entry
                assert 'time_start' in entry
                assert 'time_end' in entry
        else:
            print(f"❌ Failed to retrieve availability: {response.status_code}")
            return False
        
        print("\n✅ All API time support tests passed!")
        return True

if __name__ == '__main__':
    success = test_api_time_support()
    if not success:
        sys.exit(1)
    print("\n🎉 Task 2 implementation verified successfully!")