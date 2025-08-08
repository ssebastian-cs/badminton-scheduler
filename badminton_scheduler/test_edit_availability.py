#!/usr/bin/env python3
"""
Test script for the edit availability API endpoint.
Tests the PUT /api/availability/{id} endpoint functionality.
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from run.py since that's where the models are defined
from run import app, db, User, Availability

def test_edit_availability_endpoint():
    """Test the edit availability API endpoint."""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Clear existing test data
        db.session.execute(db.text("DELETE FROM availability WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'testuser_edit%' OR username = 'testeditadmin')"))
        db.session.execute(db.text("DELETE FROM users WHERE username LIKE 'testuser_edit%' OR username = 'testeditadmin'"))
        db.session.commit()
        
        # Create test users with unique names
        user1 = User(username='testuser_edit1', email='testedit1@example.com')
        user1.set_password('password123')
        
        user2 = User(username='testuser_edit2', email='testedit2@example.com')
        user2.set_password('password123')
        
        admin_user = User(username='testeditadmin', email='testeditadmin@example.com', is_admin=True)
        admin_user.set_password('admin123')
        
        db.session.add_all([user1, user2, admin_user])
        db.session.commit()
        
        # Create test availability entries
        future_date = date.today() + timedelta(days=7)
        past_date = date.today() - timedelta(days=1)
        
        avail1 = Availability(
            user_id=user1.id,
            date=future_date,
            status='available',
            play_preference='either',
            notes='Original notes',
            time_slot='19:00-21:00'
        )
        
        avail2 = Availability(
            user_id=user2.id,
            date=future_date,
            status='tentative',
            play_preference='drop_in',
            notes='User 2 availability'
        )
        
        past_avail = Availability(
            user_id=user1.id,
            date=past_date,
            status='available',
            play_preference='either',
            notes='Past availability'
        )
        
        db.session.add_all([avail1, avail2, past_avail])
        db.session.commit()
        
        client = app.test_client()
        
        print("Testing Edit Availability API Endpoint")
        print("=" * 50)
        
        # Test 1: Update availability as owner
        print("\n1. Testing successful update by owner...")
        
        # Login as user1
        login_response = client.post('/auth/login',
                                   data=json.dumps({
                                       'username': 'testuser_edit1',
                                       'password': 'password123'
                                   }),
                                   content_type='application/json')
        
        update_data = {
            'status': 'tentative',
            'play_preference': 'book_court',
            'notes': 'Updated notes',
            'time_start': '18:00',
            'time_end': '20:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail1.id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print("✓ Successfully updated availability")
            print(f"  Status: {data['availability']['status']}")
            print(f"  Play Preference: {data['availability']['play_preference']}")
            print(f"  Notes: {data['availability']['notes']}")
            print(f"  Time Slot: {data['availability']['time_slot']}")
        else:
            print(f"✗ Failed: {response.get_json()}")
        
        # Test 2: Try to update another user's availability (should fail)
        print("\n2. Testing unauthorized update attempt...")
        response = client.put(f'/api/availability/{avail2.id}',
                            data=json.dumps({'status': 'available'}),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 403:
            print("✓ Correctly denied unauthorized access")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have been denied: {response.get_json()}")
        
        # Test 3: Try to update past date availability (should fail)
        print("\n3. Testing past date protection...")
        response = client.put(f'/api/availability/{past_avail.id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✓ Correctly prevented editing past date")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have been prevented: {response.get_json()}")
        
        # Test 4: Admin can update any user's availability
        print("\n4. Testing admin access...")
        
        # Login as admin user properly
        client.post('/auth/login',
                   data=json.dumps({
                       'username': 'testeditadmin',
                       'password': 'admin123'
                   }),
                   content_type='application/json')
        
        admin_update = {
            'status': 'not_available',
            'notes': 'Updated by admin'
        }
        
        response = client.put(f'/api/availability/{avail2.id}',
                            data=json.dumps(admin_update),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print("✓ Admin successfully updated user's availability")
            print(f"  Status: {data['availability']['status']}")
            print(f"  Notes: {data['availability']['notes']}")
        else:
            print(f"✗ Admin update failed: {response.get_json()}")
        
        # Test 5: Test nonexistent availability ID
        print("\n5. Testing nonexistent availability ID...")
        
        # Login as user1 again
        client.post('/auth/login',
                   data=json.dumps({
                       'username': 'testuser_edit1',
                       'password': 'password123'
                   }),
                   content_type='application/json')
        
        response = client.put('/api/availability/99999',
                            data=json.dumps({'status': 'available'}),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 404:
            print("✓ Correctly handled nonexistent ID")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have returned 404: {response.get_json()}")
        
        # Test 6: Test invalid time format
        print("\n6. Testing invalid time format...")
        invalid_time_data = {
            'time_start': 'invalid-time',
            'time_end': '20:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail1.id}',
                            data=json.dumps(invalid_time_data),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✓ Correctly rejected invalid time format")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have rejected invalid time: {response.get_json()}")
        
        # Test 7: Test invalid status value
        print("\n7. Testing invalid status value...")
        invalid_status_data = {
            'status': 'invalid_status'
        }
        
        response = client.put(f'/api/availability/{avail1.id}',
                            data=json.dumps(invalid_status_data),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✓ Correctly rejected invalid status")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have rejected invalid status: {response.get_json()}")
        
        # Test 8: Test time logic validation (end before start)
        print("\n8. Testing time logic validation...")
        invalid_time_logic = {
            'time_start': '20:00',
            'time_end': '18:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail1.id}',
                            data=json.dumps(invalid_time_logic),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✓ Correctly rejected invalid time logic")
            print(f"  Error: {response.get_json()['error']}")
        else:
            print(f"✗ Should have rejected invalid time logic: {response.get_json()}")
        
        # Test 9: Test updating to all-day availability
        print("\n9. Testing update to all-day availability...")
        all_day_data = {
            'status': 'available',
            'is_all_day': True,
            'notes': 'All day availability'
        }
        
        response = client.put(f'/api/availability/{avail1.id}',
                            data=json.dumps(all_day_data),
                            content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print("✓ Successfully updated to all-day availability")
            print(f"  Is All Day: {data['availability']['is_all_day']}")
            print(f"  Time Slot: {data['availability']['time_slot']}")
        else:
            print(f"✗ All-day update failed: {response.get_json()}")
        
        print("\n" + "=" * 50)
        print("Edit Availability API Endpoint Tests Complete")

if __name__ == '__main__':
    test_edit_availability_endpoint()