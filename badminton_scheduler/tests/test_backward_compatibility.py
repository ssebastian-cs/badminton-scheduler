#!/usr/bin/env python3
"""
Simple test script to verify backward compatibility.
"""

import sys
import json
from datetime import datetime, date, timedelta
from run import app, db, User, Availability

def test_backward_compatibility():
    """Test that existing functionality remains unaffected."""
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("Testing backward compatibility...")
        
        # Test 1: Create availability without time parameters (should default to all-day)
        print("  Test 1: Creating all-day availability...")
        
        # Create a test user if it doesn't exist
        test_user = User.query.filter_by(username='test_user').first()
        if not test_user:
            test_user = User(username='test_user', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        
        # Create availability entry without time fields (legacy behavior)
        availability = Availability(
            user_id=test_user.id,
            date=date.today() + timedelta(days=1),
            status='available',
            notes='Test all-day availability'
        )
        
        db.session.add(availability)
        db.session.commit()
        
        # Verify defaults are set correctly
        assert availability.is_all_day == True, f"Expected is_all_day=True, got {availability.is_all_day}"
        assert availability.time_start is None, f"Expected time_start=None, got {availability.time_start}"
        assert availability.time_end is None, f"Expected time_end=None, got {availability.time_end}"
        assert availability.updated_at is not None, f"Expected updated_at to be set"
        
        print("    ✓ All-day availability defaults work correctly")
        
        # Test 2: Create availability with time fields
        print("  Test 2: Creating time-specific availability...")
        
        from datetime import time
        availability2 = Availability(
            user_id=test_user.id,
            date=date.today() + timedelta(days=2),
            time_start=time(19, 0),  # 7:00 PM
            time_end=time(21, 0),    # 9:00 PM
            is_all_day=False,
            status='available',
            notes='Test time-specific availability'
        )
        
        db.session.add(availability2)
        db.session.commit()
        
        # Verify time fields are set correctly
        assert availability2.is_all_day == False, f"Expected is_all_day=False, got {availability2.is_all_day}"
        assert availability2.time_start == time(19, 0), f"Expected time_start=19:00, got {availability2.time_start}"
        assert availability2.time_end == time(21, 0), f"Expected time_end=21:00, got {availability2.time_end}"
        
        print("    ✓ Time-specific availability works correctly")
        
        # Test 3: Test to_dict method includes all fields
        print("  Test 3: Testing to_dict method...")
        
        result_dict = availability.to_dict()
        required_fields = ['id', 'user_id', 'date', 'time_slot', 'time_start', 'time_end', 'is_all_day', 'status', 'created_at', 'updated_at']
        
        for field in required_fields:
            assert field in result_dict, f"Missing field {field} in to_dict result"
        
        # Verify all-day entry values
        assert result_dict['is_all_day'] == True, f"Expected is_all_day=True in dict"
        assert result_dict['time_start'] is None, f"Expected time_start=None in dict"
        assert result_dict['time_end'] is None, f"Expected time_end=None in dict"
        
        print("    ✓ to_dict method includes all required fields")
        
        # Test time-specific entry
        result_dict2 = availability2.to_dict()
        assert result_dict2['is_all_day'] == False, f"Expected is_all_day=False in dict"
        assert result_dict2['time_start'] == '19:00', f"Expected time_start='19:00' in dict, got {result_dict2['time_start']}"
        assert result_dict2['time_end'] == '21:00', f"Expected time_end='21:00' in dict, got {result_dict2['time_end']}"
        
        print("    ✓ Time-specific to_dict works correctly")
        
        # Test 4: Test unique constraints work
        print("  Test 4: Testing unique constraints...")
        
        # Try to create duplicate all-day entry (should be allowed with new constraint)
        try:
            availability3 = Availability(
                user_id=test_user.id,
                date=date.today() + timedelta(days=3),
                time_start=time(19, 0),
                time_end=time(21, 0),
                is_all_day=False,
                status='available'
            )
            db.session.add(availability3)
            
            # Try to create another entry with same time slot (should fail)
            availability4 = Availability(
                user_id=test_user.id,
                date=date.today() + timedelta(days=3),
                time_start=time(19, 0),
                time_end=time(21, 0),
                is_all_day=False,
                status='tentative'
            )
            db.session.add(availability4)
            db.session.commit()
            
            print("    ❌ Unique constraint should have prevented duplicate time slots")
            return False
            
        except Exception as e:
            # This is expected - rollback and continue
            db.session.rollback()
            print("    ✓ Unique constraints work correctly")
        
        # Clean up test data
        Availability.query.filter_by(user_id=test_user.id).delete()
        db.session.delete(test_user)
        db.session.commit()
        
        print("  Test data cleaned up")
        
        return True

def main():
    """Run the backward compatibility test."""
    print("=== Backward Compatibility Test ===")
    print()
    
    try:
        if test_backward_compatibility():
            print()
            print("=== All backward compatibility tests passed! ===")
            print("✓ Default values work correctly")
            print("✓ New time fields work correctly") 
            print("✓ to_dict method includes all fields")
            print("✓ Unique constraints work as expected")
            print("✓ Existing functionality remains unaffected")
            return True
        else:
            print("❌ Backward compatibility tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)