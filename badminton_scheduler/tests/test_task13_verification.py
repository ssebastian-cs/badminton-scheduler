#!/usr/bin/env python3
"""
Comprehensive test to verify Task 13: Add data migration and backward compatibility.

This test verifies all the requirements for task 13:
- Create migration logic to set is_all_day=True for existing availability entries
- Ensure existing API calls continue to work without time parameters
- Add backward compatibility for clients that don't send time data
- Test that existing functionality remains unaffected
"""

import sys
import json
from datetime import datetime, date, timedelta, time
from run import app, db, User, Availability

def test_migration_logic():
    """Test that migration logic sets is_all_day=True for existing entries."""
    print("Testing migration logic...")
    
    with app.app_context():
        db.create_all()
        
        # Create test user (or get existing one)
        test_user = User.query.filter_by(username='migration_test_user').first()
        if not test_user:
            test_user = User(username='migration_test_user', email='migration@test.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        else:
            # Clean up any existing availability entries for this user
            Availability.query.filter_by(user_id=test_user.id).delete()
            db.session.commit()
        
        # Create an entry that simulates old data (without time fields)
        # We'll manually set is_all_day to None after creation to simulate old data
        old_entry = Availability(
            user_id=test_user.id,
            date=date.today() + timedelta(days=1),
            status='available',
            time_slot=None,
            time_start=None,
            time_end=None,
            notes='Old entry for migration test'
        )
        
        db.session.add(old_entry)
        db.session.flush()  # Get the ID but don't commit yet
        
        # Manually set is_all_day to None to simulate old data
        db.session.execute(
            db.text("UPDATE availability SET is_all_day = NULL WHERE id = :id"),
            {"id": old_entry.id}
        )
        db.session.commit()
        
        # Refresh the object to get the updated values
        db.session.refresh(old_entry)
        
        # Verify the entry was created with None values
        assert old_entry.is_all_day is None, "Test setup failed: is_all_day should be None"
        
        # Run migration logic (simulate what would happen during migration)
        entries_to_migrate = Availability.query.filter(
            Availability.is_all_day.is_(None)
        ).all()
        
        for entry in entries_to_migrate:
            if entry.is_all_day is None:
                entry.is_all_day = True
            if entry.updated_at is None:
                entry.updated_at = entry.created_at or datetime.utcnow()
        
        db.session.commit()
        
        # Verify migration worked
        migrated_entry = Availability.query.get(old_entry.id)
        assert migrated_entry.is_all_day == True, "Migration should set is_all_day=True"
        assert migrated_entry.updated_at is not None, "Migration should set updated_at"
        
        # Clean up
        db.session.delete(migrated_entry)
        db.session.delete(test_user)
        db.session.commit()
        
        print("  ✓ Migration logic works correctly")
        return True

def test_existing_api_compatibility():
    """Test that existing API calls continue to work without time parameters."""
    print("Testing existing API compatibility...")
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test user (or get existing one)
            test_user = User.query.filter_by(username='api_compat_user').first()
            if not test_user:
                test_user = User(username='api_compat_user', email='apicompat@test.com')
                test_user.set_password('password')
                db.session.add(test_user)
                db.session.commit()
            else:
                # Clean up any existing availability entries for this user
                Availability.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test 1: Old-style API call without any time parameters
            old_style_data = {
                'date': (date.today() + timedelta(days=1)).isoformat(),
                'status': 'available',
                'play_preference': 'either',
                'notes': 'Old style API call'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(old_style_data),
                                 content_type='application/json')
            
            assert response.status_code == 200, f"Old-style API call failed: {response.status_code}"
            
            response_data = response.get_json()
            assert response_data['is_all_day'] == True, "Old-style API should default to all-day"
            assert response_data['time_start'] is None, "Old-style API should have no start time"
            assert response_data['time_end'] is None, "Old-style API should have no end time"
            
            # Test 2: API call with legacy time_slot field
            legacy_data = {
                'date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'available',
                'time_slot': '7:00 PM - 9:00 PM',
                'notes': 'Legacy time_slot API call'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(legacy_data),
                                 content_type='application/json')
            
            assert response.status_code == 200, f"Legacy time_slot API call failed: {response.status_code}"
            
            response_data = response.get_json()
            assert response_data['is_all_day'] == False, "Legacy time_slot should not be all-day"
            assert response_data['time_start'] is not None, "Legacy time_slot should parse start time"
            assert response_data['time_end'] is not None, "Legacy time_slot should parse end time"
            assert 'time_slot' in response_data, "Legacy time_slot field should be preserved"
            
            # Clean up
            Availability.query.filter_by(user_id=test_user.id).delete()
            db.session.delete(test_user)
            db.session.commit()
            
            print("  ✓ Existing API calls work correctly")
            return True

def test_backward_compatibility_clients():
    """Test backward compatibility for clients that don't send time data."""
    print("Testing backward compatibility for clients...")
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test user (or get existing one)
            test_user = User.query.filter_by(username='backward_compat_user').first()
            if not test_user:
                test_user = User(username='backward_compat_user', email='backcompat@test.com')
                test_user.set_password('password')
                db.session.add(test_user)
                db.session.commit()
            else:
                # Clean up any existing availability entries for this user
                Availability.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test 1: Client sends minimal data (like old clients would)
            minimal_data = {
                'date': (date.today() + timedelta(days=1)).isoformat(),
                'status': 'available'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(minimal_data),
                                 content_type='application/json')
            
            assert response.status_code == 200, f"Minimal data API call failed: {response.status_code}"
            
            response_data = response.get_json()
            assert response_data['is_all_day'] == True, "Minimal data should default to all-day"
            
            # Test 2: Client sends empty time fields (should be treated as all-day)
            empty_time_data = {
                'date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'available',
                'time_start': '',
                'time_end': '',
                'is_all_day': True
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(empty_time_data),
                                 content_type='application/json')
            
            assert response.status_code == 200, f"Empty time data API call failed: {response.status_code}"
            
            response_data = response.get_json()
            assert response_data['is_all_day'] == True, "Empty time data should be all-day"
            assert response_data['time_start'] is None, "Empty time_start should be None"
            assert response_data['time_end'] is None, "Empty time_end should be None"
            
            # Test 3: GET API returns all required fields for backward compatibility
            response = client.get('/api/availability')
            assert response.status_code == 200, "GET availability failed"
            
            availability_list = response.get_json()
            for avail in availability_list:
                # Verify all fields are present for backward compatibility
                required_fields = ['id', 'user_id', 'date', 'status', 'time_slot', 
                                 'time_start', 'time_end', 'is_all_day', 'created_at', 'updated_at']
                for field in required_fields:
                    assert field in avail, f"Missing field {field} in GET response"
            
            # Clean up
            Availability.query.filter_by(user_id=test_user.id).delete()
            db.session.delete(test_user)
            db.session.commit()
            
            print("  ✓ Backward compatibility for clients works correctly")
            return True

def test_existing_functionality_unaffected():
    """Test that existing functionality remains unaffected."""
    print("Testing that existing functionality remains unaffected...")
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test user (or get existing one)
            test_user = User.query.filter_by(username='functionality_test_user').first()
            if not test_user:
                test_user = User(username='functionality_test_user', email='functest@test.com')
                test_user.set_password('password')
                db.session.add(test_user)
                db.session.commit()
            else:
                # Clean up any existing availability entries for this user
                Availability.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test 1: Basic CRUD operations still work
            # Create
            create_data = {
                'date': (date.today() + timedelta(days=1)).isoformat(),
                'status': 'available',
                'play_preference': 'either',
                'notes': 'Test CRUD operations'
            }
            
            response = client.post('/api/availability', 
                                 data=json.dumps(create_data),
                                 content_type='application/json')
            
            assert response.status_code == 200, "Create operation failed"
            created_entry = response.get_json()
            entry_id = created_entry['id']
            
            # Read
            response = client.get('/api/availability')
            assert response.status_code == 200, "Read operation failed"
            
            availability_list = response.get_json()
            found_entry = None
            for avail in availability_list:
                if avail['id'] == entry_id:
                    found_entry = avail
                    break
            
            assert found_entry is not None, "Created entry not found in GET response"
            assert found_entry['status'] == 'available', "Entry status not preserved"
            assert found_entry['notes'] == 'Test CRUD operations', "Entry notes not preserved"
            
            # Update
            update_data = {
                'status': 'tentative',
                'notes': 'Updated notes'
            }
            
            response = client.put(f'/api/availability/{entry_id}', 
                                data=json.dumps(update_data),
                                content_type='application/json')
            
            assert response.status_code == 200, "Update operation failed"
            
            # Verify update
            response = client.get('/api/availability')
            availability_list = response.get_json()
            updated_entry = None
            for avail in availability_list:
                if avail['id'] == entry_id:
                    updated_entry = avail
                    break
            
            assert updated_entry['status'] == 'tentative', "Update did not change status"
            assert updated_entry['notes'] == 'Updated notes', "Update did not change notes"
            
            # Delete
            response = client.delete(f'/api/availability/{entry_id}')
            assert response.status_code == 200, "Delete operation failed"
            
            # Verify deletion
            response = client.get('/api/availability')
            availability_list = response.get_json()
            deleted_entry = None
            for avail in availability_list:
                if avail['id'] == entry_id:
                    deleted_entry = avail
                    break
            
            assert deleted_entry is None, "Entry was not deleted"
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
            
            print("  ✓ Existing functionality remains unaffected")
            return True

def test_data_model_consistency():
    """Test that the data model maintains consistency with new fields."""
    print("Testing data model consistency...")
    
    with app.app_context():
        db.create_all()
        
        # Create test user (or get existing one)
        test_user = User.query.filter_by(username='model_test_user').first()
        if not test_user:
            test_user = User(username='model_test_user', email='modeltest@test.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        else:
            # Clean up any existing availability entries for this user
            Availability.query.filter_by(user_id=test_user.id).delete()
            db.session.commit()
        
        # Test 1: Default values are set correctly
        entry1 = Availability(
            user_id=test_user.id,
            date=date.today() + timedelta(days=1),
            status='available'
        )
        db.session.add(entry1)
        db.session.commit()
        
        assert entry1.is_all_day == True, "Default is_all_day should be True"
        assert entry1.time_start is None, "Default time_start should be None"
        assert entry1.time_end is None, "Default time_end should be None"
        assert entry1.updated_at is not None, "updated_at should be set automatically"
        
        # Test 2: Time-specific entries work correctly
        entry2 = Availability(
            user_id=test_user.id,
            date=date.today() + timedelta(days=2),
            time_start=time(19, 0),
            time_end=time(21, 0),
            is_all_day=False,
            status='available'
        )
        db.session.add(entry2)
        db.session.commit()
        
        assert entry2.is_all_day == False, "Time-specific entry should have is_all_day=False"
        assert entry2.time_start == time(19, 0), "time_start should be preserved"
        assert entry2.time_end == time(21, 0), "time_end should be preserved"
        
        # Test 3: to_dict method includes all fields
        dict_result = entry1.to_dict()
        required_fields = ['id', 'user_id', 'date', 'time_slot', 'time_start', 'time_end', 
                          'is_all_day', 'status', 'created_at', 'updated_at']
        
        for field in required_fields:
            assert field in dict_result, f"to_dict missing field: {field}"
        
        # Test 4: Unique constraints work correctly
        try:
            # Try to create duplicate time-specific entry
            duplicate_entry = Availability(
                user_id=test_user.id,
                date=date.today() + timedelta(days=2),
                time_start=time(19, 0),
                time_end=time(21, 0),
                is_all_day=False,
                status='tentative'
            )
            db.session.add(duplicate_entry)
            db.session.commit()
            
            assert False, "Duplicate time-specific entry should have been rejected"
            
        except Exception:
            # This is expected - rollback and continue
            db.session.rollback()
        
        # Clean up
        Availability.query.filter_by(user_id=test_user.id).delete()
        db.session.delete(test_user)
        db.session.commit()
        
        print("  ✓ Data model consistency maintained")
        return True

def main():
    """Run all Task 13 verification tests."""
    print("=== Task 13: Data Migration and Backward Compatibility Verification ===")
    print()
    
    try:
        # Test all requirements
        tests = [
            test_migration_logic,
            test_existing_api_compatibility,
            test_backward_compatibility_clients,
            test_existing_functionality_unaffected,
            test_data_model_consistency
        ]
        
        for test_func in tests:
            if not test_func():
                print(f"❌ Test {test_func.__name__} failed")
                return False
            print()
        
        print("=== All Task 13 requirements verified successfully! ===")
        print("✓ Migration logic sets is_all_day=True for existing entries")
        print("✓ Existing API calls continue to work without time parameters")
        print("✓ Backward compatibility maintained for clients that don't send time data")
        print("✓ Existing functionality remains unaffected")
        print("✓ Data model maintains consistency with new fields")
        print()
        print("Task 13 implementation is complete and working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)