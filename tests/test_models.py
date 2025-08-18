#!/usr/bin/env python3
"""
Test script to verify the data models and their validation methods.
This script tests the core functionality of User, Availability, and Comment models.
"""

import os
import sys
from datetime import date, time, datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Availability, Comment


def test_user_model():
    """Test User model validation and methods."""
    print("Testing User model...")
    
    # Test valid user creation
    try:
        user = User(username="testuser", password="password123", role="User")
        print("✓ Valid user creation successful")
    except Exception as e:
        print(f"✗ Valid user creation failed: {e}")
        return False
    
    # Test password hashing
    if user.check_password("password123"):
        print("✓ Password hashing and verification works")
    else:
        print("✗ Password hashing and verification failed")
        return False
    
    # Test invalid password
    if not user.check_password("wrongpassword"):
        print("✓ Invalid password correctly rejected")
    else:
        print("✗ Invalid password incorrectly accepted")
        return False
    
    # Test admin role check
    admin_user = User(username="admin", password="password123", role="Admin")
    if admin_user.is_admin():
        print("✓ Admin role check works")
    else:
        print("✗ Admin role check failed")
        return False
    
    # Test username validation
    try:
        User(username="ab", password="password123")  # Too short
        print("✗ Short username validation failed")
        return False
    except ValueError:
        print("✓ Short username correctly rejected")
    
    try:
        User(username="a" * 25, password="password123")  # Too long
        print("✗ Long username validation failed")
        return False
    except ValueError:
        print("✓ Long username correctly rejected")
    
    # Test password validation
    try:
        User(username="testuser2", password="123")  # Too short
        print("✗ Short password validation failed")
        return False
    except ValueError:
        print("✓ Short password correctly rejected")
    
    # Test invalid role
    try:
        User(username="testuser3", password="password123", role="InvalidRole")
        print("✗ Invalid role validation failed")
        return False
    except ValueError:
        print("✓ Invalid role correctly rejected")
    
    return True


def test_availability_model():
    """Test Availability model validation and methods."""
    print("\nTesting Availability model...")
    
    # Create a test user first
    user = User(username="availuser", password="password123")
    
    # Test valid availability creation (future date)
    future_date = date.today() + timedelta(days=1)
    start_time = time(9, 0)
    end_time = time(11, 0)
    
    try:
        availability = Availability(
            user_id=1,  # Assuming user ID 1
            date=future_date,
            start_time=start_time,
            end_time=end_time
        )
        print("✓ Valid availability creation successful")
    except Exception as e:
        print(f"✗ Valid availability creation failed: {e}")
        return False
    
    # Test past date validation
    try:
        Availability(
            user_id=1,
            date=date.today() - timedelta(days=1),  # Past date
            start_time=start_time,
            end_time=end_time
        )
        print("✗ Past date validation failed")
        return False
    except ValueError:
        print("✓ Past date correctly rejected")
    
    # Test today's date validation
    try:
        Availability(
            user_id=1,
            date=date.today(),  # Today's date
            start_time=start_time,
            end_time=end_time
        )
        print("✗ Today's date validation failed")
        return False
    except ValueError:
        print("✓ Today's date correctly rejected")
    
    # Test invalid time range (end before start)
    try:
        Availability(
            user_id=1,
            date=future_date,
            start_time=time(11, 0),
            end_time=time(9, 0)  # End before start
        )
        print("✗ Invalid time range validation failed")
        return False
    except ValueError:
        print("✓ Invalid time range correctly rejected")
    
    # Test update method
    try:
        new_future_date = date.today() + timedelta(days=2)
        availability.update(date=new_future_date, start_time=time(10, 0), end_time=time(12, 0))
        print("✓ Availability update successful")
    except Exception as e:
        print(f"✗ Availability update failed: {e}")
        return False
    
    return True


def test_comment_model():
    """Test Comment model validation and methods."""
    print("\nTesting Comment model...")
    
    # Test valid comment creation
    try:
        comment = Comment(user_id=1, content="This is a test comment")
        print("✓ Valid comment creation successful")
    except Exception as e:
        print(f"✗ Valid comment creation failed: {e}")
        return False
    
    # Test empty content validation
    try:
        Comment(user_id=1, content="")
        print("✗ Empty content validation failed")
        return False
    except ValueError:
        print("✓ Empty content correctly rejected")
    
    # Test whitespace-only content validation
    try:
        Comment(user_id=1, content="   ")
        print("✗ Whitespace-only content validation failed")
        return False
    except ValueError:
        print("✓ Whitespace-only content correctly rejected")
    
    # Test content length validation
    try:
        Comment(user_id=1, content="x" * 1001)  # Too long
        print("✗ Long content validation failed")
        return False
    except ValueError:
        print("✓ Long content correctly rejected")
    
    # Test content update
    try:
        comment.update_content("Updated comment content")
        print("✓ Comment content update successful")
    except Exception as e:
        print(f"✗ Comment content update failed: {e}")
        return False
    
    return True


def main():
    """Run all model tests."""
    print("Starting model validation tests...\n")
    
    # Create Flask app context for testing
    app = create_app('development')
    
    with app.app_context():
        success = True
        
        # Run all tests
        success &= test_user_model()
        success &= test_availability_model()
        success &= test_comment_model()
        
        if success:
            print("\n🎉 All model tests passed!")
            return 0
        else:
            print("\n❌ Some model tests failed!")
            return 1


if __name__ == "__main__":
    sys.exit(main())