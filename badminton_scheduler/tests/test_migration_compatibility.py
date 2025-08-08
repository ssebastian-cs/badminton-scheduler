#!/usr/bin/env python3
"""
Test script for availability migration and backward compatibility.
This script tests that existing functionality remains unaffected after the migration.
"""

import sys
import json
from datetime import datetime, date, timedelta
from app import create_app
from models import db, User, Availability

def create_test_user():
    """Create a test user for testing purposes."""
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        test_user = User.query.filter_by(username='test_migration_user').first()
        if test_user:
            return test_user.id
        
        # Create test user
        test_user = User(
            username='test_migration_user',
            email='test_migration@example.com'
        )
        test_user.set_password('test_password')
        
        db.session.add(test_user)
        db.session.commit()
        
        return test_user.id

def test_legacy_api_compatibility():
    """Test that legacy API calls work without time parameters."""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("Testing legacy API compatibility...")
            
            # Create test user
            user_id = create_test_user()
            
            # Test 1: Create availability without time parameters (legacy format)
            legacy_data = {
                'date': (date.today() + timedelta(days=1)).isoformat(),
                'status': 'available',
                'play_preference': 'either',
                'notes': 'Legacy API test'
            }
            
            # Simulate login by setting user context
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user_id)
                sess['_fresh'] = True
            
            response = client.post('/api/availability', 
                                 data=json.dumps(legacy_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"  ❌ Legacy API call failed: {response.status_code}")
                print(f"     Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            availability_data = response_data.get('availability', {})
            
            # Verify that is_all_day defaults to True for legacy calls
            if not availability_data.get('is_all_day', False):
                print(f"  ❌ Legacy API call should default to is_all_day=True")
                return False
            
            print("  ✓ Legacy API call without time parameters works")
            
            # Test 2: Create availability with legacy time_slot field
            legacy_time_data = {
                'date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'available',
                'time_slot': '7:00 PM - 9:00 PM',
                'notes': 'Legacy time_slot test'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(legacy_time_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"  ❌ Legacy time_slot API call failed: {response.status_code}")
                print(f"     Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            availability_data = response_data.get('availability', {})
            
            # Verify that time_slot is parsed into structured fields
            if availability_data.get('is_all_day', True):
                print(f"  ❌ Legacy time_slot should set is_all_day=False")
                return False
            
            if not availability_data.get('time_start') or not availability_data.get('time_end'):
                print(f"  ❌ Legacy time_slot should be parsed into time_start and time_end")
                return False
            
            print("  ✓ Legacy time_slot field is parsed correctly")
            
            # Test 3: Retrieve availability and verify backward compatibility
            response = client.get('/api/availability')
            
            if response.status_code != 200:
                print(f"  ❌ GET availability failed: {response.status_code}")
                return False
            
            availability_list = response.get_json()
            
            # Verify all entries have the new fields
            for avail in availability_list:
                required_fields = ['time_start', 'time_end', 'is_all_day', 'updated_at']
                for field in required_fields:
                    if field not in avail:
                        print(f"  ❌ Missing field {field} in availability response")
                        return False
                
                # Verify time_slot is still included for backward compatibility
                if 'time_slot' not in avail:
                    print(f"  ❌ Missing time_slot field for backward compatibility")
                    return False
            
            print("  ✓ GET availability includes all required fields")
            
            return True

def test_new_api_features():
    """Test that new API features work correctly."""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("Testing new API features...")
            
            # Create test user
            user_id = create_test_user()
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user_id)
                sess['_fresh'] = True
            
            # Test 1: Create availability with new time fields
            new_data = {
                'date': (date.today() + timedelta(days=3)).isoformat(),
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
                print(f"  ❌ New API call failed: {response.status_code}")
                print(f"     Response: {response.get_json()}")
                return False
            
            response_data = response.get_json()
            availability_data = response_data.get('availability', {})
            
            # Verify new fields are set correctly
            if availability_data.get('is_all_day', True):
                print(f"  ❌ New API should set is_all_day=False")
                return False
            
            if availability_data.get('time_start') != '19:00':
                print(f"  ❌ time_start should be '19:00', got {availability_data.get('time_start')}")
                return False
            
            if availability_data.get('time_end') != '21:00':
                print(f"  ❌ time_end should be '21:00', got {availability_data.get('time_end')}")
                return False
            
            print("  ✓ New API with time fields works correctly")
            
            # Test 2: Create all-day availability with new API
            all_day_data = {
                'date': (date.today() + timedelta(days=4)).isoformat(),
                'status': 'available',
                'is_all_day': True,
                'notes': 'All-day test'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(all_day_data),
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"  ❌ All-day API call failed: {response.status_code}")
                return False
            
            response_data = response.get_json()
            availability_data = response_data.get('availability', {})
            
            # Verify all-day fields are set correctly
            if not availability_data.get('is_all_day', False):
                print(f"  ❌ All-day API should set is_all_day=True")
                return False
            
            if availability_data.get('time_start') is not None:
                print(f"  ❌ All-day availability should have time_start=None")
                return False
            
            if availability_data.get('time_end') is not None:
                print(f"  ❌ All-day availability should have time_end=None")
                return False
            
            print("  ✓ All-day availability works correctly")
            
            return True

def test_database_consistency():
    """Test that database entries are consistent after migration."""
    app = create_app()
    
    with app.app_context():
        print("Testing database consistency...")
        
        # Check that all availability entries have is_all_day set
        entries_without_all_day = Availability.query.filter(
            Availability.is_all_day.is_(None)
        ).count()
        
        if entries_without_all_day > 0:
            print(f"  ❌ {entries_without_all_day} entries have is_all_day=NULL")
            return False
        
        print("  ✓ All entries have is_all_day field set")
        
        # Check that all entries have updated_at set
        entries_without_updated_at = Availability.query.filter(
            Availability.updated_at.is_(None)
        ).count()
        
        if entries_without_updated_at > 0:
            print(f"  ❌ {entries_without_updated_at} entries have updated_at=NULL")
            return False
        
        print("  ✓ All entries have updated_at field set")
        
        # Check data consistency between time fields and is_all_day
        all_entries = Availability.query.all()
        
        for entry in all_entries:
            if entry.is_all_day:
                # All-day entries should not have specific times
                if entry.time_start is not None or entry.time_end is not None:
                    print(f"  ❌ All-day entry {entry.id} has specific times set")
                    return False
            else:
                # Time-specific entries should have at least one time set
                if entry.time_start is None and entry.time_end is None:
                    print(f"  ❌ Time-specific entry {entry.id} has no times set")
                    return False
        
        print("  ✓ Data consistency between time fields and is_all_day flag")
        
        return True

def cleanup_test_data():
    """Clean up test data created during testing."""
    app = create_app()
    
    with app.app_context():
        # Remove test user and associated availability entries
        test_user = User.query.filter_by(username='test_migration_user').first()
        if test_user:
            # Delete associated availability entries
            Availability.query.filter_by(user_id=test_user.id).delete()
            # Delete test user
            db.session.delete(test_user)
            db.session.commit()
            print("Test data cleaned up successfully")

def main():
    """Run all migration and compatibility tests."""
    print("=== Migration and Backward Compatibility Tests ===")
    print()
    
    try:
        # Test 1: Database consistency
        if not test_database_consistency():
            print("Database consistency test failed. Exiting.")
            return False
        
        print()
        
        # Test 2: Legacy API compatibility
        if not test_legacy_api_compatibility():
            print("Legacy API compatibility test failed. Exiting.")
            return False
        
        print()
        
        # Test 3: New API features
        if not test_new_api_features():
            print("New API features test failed. Exiting.")
            return False
        
        print()
        print("=== All tests passed! ===")
        print("✓ Database migration completed successfully")
        print("✓ Legacy API calls work without time parameters")
        print("✓ New time-specific features work correctly")
        print("✓ Backward compatibility maintained")
        
        return True
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return False
    
    finally:
        # Clean up test data
        cleanup_test_data()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)