#!/usr/bin/env python3
"""
Test API backward compatibility for availability endpoints.
"""

import sys
import json
from datetime import datetime, date, timedelta
from run import app, db, User, Availability

def test_api_backward_compatibility():
    """Test that API endpoints maintain backward compatibility."""
    
    with app.test_client() as client:
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            
            print("Testing API backward compatibility...")
            
            # Create a test user
            test_user = User.query.filter_by(username='api_test_user').first()
            if not test_user:
                test_user = User(username='api_test_user', email='apitest@example.com')
                test_user.set_password('password')
                db.session.add(test_user)
                db.session.commit()
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test 1: POST availability without time parameters (legacy format)
            print("  Test 1: POST availability without time parameters...")
            
            legacy_data = {
                'date': (date.today() + timedelta(days=1)).isoformat(),
                'status': 'available',
                'play_preference': 'either',
                'notes': 'Legacy API test'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(legacy_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"    ❌ Legacy API call failed: {response.status_code}")
                print(f"       Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            # Handle both response formats (wrapped and direct)
            availability_data = response_data.get('availability', response_data)
            
            # Verify that is_all_day defaults to True for legacy calls
            if not availability_data.get('is_all_day', False):
                print(f"    ❌ Legacy API call should default to is_all_day=True, got {availability_data.get('is_all_day')}")
                return False
            
            if availability_data.get('time_start') is not None:
                print(f"    ❌ Legacy API call should have time_start=None")
                return False
            
            if availability_data.get('time_end') is not None:
                print(f"    ❌ Legacy API call should have time_end=None")
                return False
            
            print("    ✓ Legacy API call without time parameters works")
            
            # Test 2: POST availability with new time fields
            print("  Test 2: POST availability with new time fields...")
            
            new_data = {
                'date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'available',
                'is_all_day': False,
                'time_start': '19:00',
                'time_end': '21:00',
                'notes': 'New API test'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(new_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"    ❌ New API call failed: {response.status_code}")
                print(f"       Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            # Handle both response formats (wrapped and direct)
            availability_data = response_data.get('availability', response_data)
            
            # Verify new fields are set correctly
            if availability_data.get('is_all_day', True):
                print(f"    ❌ New API should set is_all_day=False, got {availability_data.get('is_all_day')}")
                return False
            
            if availability_data.get('time_start') != '19:00':
                print(f"    ❌ time_start should be '19:00', got {availability_data.get('time_start')}")
                return False
            
            if availability_data.get('time_end') != '21:00':
                print(f"    ❌ time_end should be '21:00', got {availability_data.get('time_end')}")
                return False
            
            print("    ✓ New API with time fields works correctly")
            
            # Test 3: POST availability with legacy time_slot field
            print("  Test 3: POST availability with legacy time_slot field...")
            
            legacy_time_data = {
                'date': (date.today() + timedelta(days=3)).isoformat(),
                'status': 'available',
                'time_slot': '7:00 PM - 9:00 PM',
                'notes': 'Legacy time_slot test'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(legacy_time_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"    ❌ Legacy time_slot API call failed: {response.status_code}")
                print(f"       Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            # Handle both response formats (wrapped and direct)
            availability_data = response_data.get('availability', response_data)
            
            # Verify that time_slot is parsed into structured fields
            if availability_data.get('is_all_day', True):
                print(f"    ❌ Legacy time_slot should set is_all_day=False, got {availability_data.get('is_all_day')}")
                return False
            
            if not availability_data.get('time_start') or not availability_data.get('time_end'):
                print(f"    ❌ Legacy time_slot should be parsed into time_start and time_end")
                print(f"       Got time_start: {availability_data.get('time_start')}, time_end: {availability_data.get('time_end')}")
                return False
            
            # Verify time_slot is still included for backward compatibility
            if 'time_slot' not in availability_data:
                print(f"    ❌ time_slot field should be preserved for backward compatibility")
                return False
            
            print("    ✓ Legacy time_slot field is parsed correctly")
            
            # Test 4: GET availability and verify all fields are present
            print("  Test 4: GET availability includes all required fields...")
            
            response = client.get('/api/availability')
            
            if response.status_code != 200:
                print(f"    ❌ GET availability failed: {response.status_code}")
                return False
            
            availability_list = response.get_json()
            
            if not availability_list:
                print(f"    ❌ No availability entries returned")
                return False
            
            # Verify all entries have the required fields
            for avail in availability_list:
                required_fields = ['id', 'time_start', 'time_end', 'is_all_day', 'updated_at', 'time_slot']
                for field in required_fields:
                    if field not in avail:
                        print(f"    ❌ Missing field {field} in availability response")
                        return False
            
            print("    ✓ GET availability includes all required fields")
            
            # Test 5: Test that existing entries without time data are handled correctly
            print("  Test 5: Testing existing entries without time data...")
            
            # Create an entry directly in the database without time fields (simulating old data)
            old_entry = Availability(
                user_id=test_user.id,
                date=date.today() + timedelta(days=4),
                status='available',
                time_slot=None,
                time_start=None,
                time_end=None,
                is_all_day=None,  # Simulate old data
                notes='Old entry without time data'
            )
            
            db.session.add(old_entry)
            db.session.commit()
            
            # Retrieve via API and verify it's handled correctly
            response = client.get('/api/availability')
            availability_list = response.get_json()
            
            # Find our old entry
            old_entry_response = None
            for avail in availability_list:
                if avail.get('notes') == 'Old entry without time data':
                    old_entry_response = avail
                    break
            
            if not old_entry_response:
                print(f"    ❌ Old entry not found in API response")
                return False
            
            # Verify it's treated as all-day
            if not old_entry_response.get('is_all_day', False):
                print(f"    ❌ Old entry should be treated as all-day, got is_all_day={old_entry_response.get('is_all_day')}")
                return False
            
            print("    ✓ Existing entries without time data are handled correctly")
            
            # Clean up test data
            Availability.query.filter_by(user_id=test_user.id).delete()
            db.session.delete(test_user)
            db.session.commit()
            
            print("  Test data cleaned up")
            
            return True

def main():
    """Run the API backward compatibility test."""
    print("=== API Backward Compatibility Test ===")
    print()
    
    try:
        if test_api_backward_compatibility():
            print()
            print("=== All API backward compatibility tests passed! ===")
            print("✓ Legacy API calls work without time parameters")
            print("✓ New time-specific API calls work correctly")
            print("✓ Legacy time_slot field is parsed correctly")
            print("✓ GET API includes all required fields")
            print("✓ Existing entries without time data are handled correctly")
            return True
        else:
            print("❌ API backward compatibility tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)