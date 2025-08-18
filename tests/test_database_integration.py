#!/usr/bin/env python3
"""
Integration test to verify database operations and relationships work correctly.
This script tests actual database operations with the models.
"""

import os
import sys
from datetime import date, time, datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Availability, Comment


def test_database_operations():
    """Test actual database operations with relationships."""
    print("Testing database operations and relationships...")
    
    try:
        # Create test users
        user1 = User(username="player1", password="password123", role="User")
        user2 = User(username="admin1", password="password123", role="Admin")
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        print("✓ Users created and saved to database")
        
        # Test user retrieval
        retrieved_user = User.query.filter_by(username="player1").first()
        if retrieved_user and retrieved_user.check_password("password123"):
            print("✓ User retrieval and password verification works")
        else:
            print("✗ User retrieval failed")
            return False
        
        # Create availability entries
        future_date1 = date.today() + timedelta(days=1)
        future_date2 = date.today() + timedelta(days=2)
        
        availability1 = Availability(
            user_id=user1.id,
            date=future_date1,
            start_time=time(9, 0),
            end_time=time(11, 0)
        )
        
        availability2 = Availability(
            user_id=user1.id,
            date=future_date2,
            start_time=time(14, 0),
            end_time=time(16, 0)
        )
        
        availability3 = Availability(
            user_id=user2.id,
            date=future_date1,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        
        db.session.add_all([availability1, availability2, availability3])
        db.session.commit()
        print("✓ Availability entries created and saved")
        
        # Test relationship queries
        user1_availability = user1.availability_entries
        if len(user1_availability) == 2:
            print("✓ User-Availability relationship works correctly")
        else:
            print(f"✗ Expected 2 availability entries for user1, got {len(user1_availability)}")
            return False
        
        # Test availability queries
        today_plus_one = Availability.query.filter_by(date=future_date1).all()
        if len(today_plus_one) == 2:
            print("✓ Date-based availability queries work")
        else:
            print(f"✗ Expected 2 availability entries for {future_date1}, got {len(today_plus_one)}")
            return False
        
        # Create comments
        comment1 = Comment(user_id=user1.id, content="Looking forward to playing tomorrow!")
        comment2 = Comment(user_id=user2.id, content="Courts are available from 9 AM")
        comment3 = Comment(user_id=user1.id, content="Anyone up for doubles?")
        
        db.session.add_all([comment1, comment2, comment3])
        db.session.commit()
        print("✓ Comments created and saved")
        
        # Test comment relationships
        user1_comments = user1.comments
        if len(user1_comments) == 2:
            print("✓ User-Comment relationship works correctly")
        else:
            print(f"✗ Expected 2 comments for user1, got {len(user1_comments)}")
            return False
        
        # Test comment queries with ordering
        all_comments = Comment.query.order_by(Comment.created_at.desc()).all()
        if len(all_comments) == 3:
            print("✓ Comment queries with ordering work")
        else:
            print(f"✗ Expected 3 total comments, got {len(all_comments)}")
            return False
        
        # Test update operations
        availability1.update(start_time=time(8, 30), end_time=time(10, 30))
        db.session.commit()
        
        updated_availability = Availability.query.get(availability1.id)
        if updated_availability.start_time == time(8, 30):
            print("✓ Availability update operations work")
        else:
            print("✗ Availability update failed")
            return False
        
        # Test comment updates
        comment1.update_content("Updated: Looking forward to playing tomorrow!")
        db.session.commit()
        
        updated_comment = Comment.query.get(comment1.id)
        if "Updated:" in updated_comment.content:
            print("✓ Comment update operations work")
        else:
            print("✗ Comment update failed")
            return False
        
        # Test cascade deletion (delete user should delete their availability and comments)
        user1_id = user1.id
        db.session.delete(user1)
        db.session.commit()
        
        # Check that user1's availability and comments are deleted
        remaining_availability = Availability.query.filter_by(user_id=user1_id).all()
        remaining_comments = Comment.query.filter_by(user_id=user1_id).all()
        
        if len(remaining_availability) == 0 and len(remaining_comments) == 0:
            print("✓ Cascade deletion works correctly")
        else:
            print(f"✗ Cascade deletion failed: {len(remaining_availability)} availability, {len(remaining_comments)} comments remain")
            return False
        
        # Verify admin user and their data still exist
        admin_user = User.query.filter_by(username="admin1").first()
        admin_availability = Availability.query.filter_by(user_id=admin_user.id).all()
        admin_comments = Comment.query.filter_by(user_id=admin_user.id).all()
        
        if admin_user and len(admin_availability) == 1 and len(admin_comments) == 1:
            print("✓ Other user data preserved after cascade deletion")
        else:
            print("✗ Other user data affected by cascade deletion")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Database operation failed: {e}")
        return False


def main():
    """Run database integration tests."""
    print("Starting database integration tests...\n")
    
    # Create Flask app context for testing
    app = create_app('development')
    
    with app.app_context():
        # Clean up any existing test data
        db.session.query(Comment).delete()
        db.session.query(Availability).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        success = test_database_operations()
        
        # Clean up test data
        db.session.query(Comment).delete()
        db.session.query(Availability).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        if success:
            print("\n🎉 All database integration tests passed!")
            return 0
        else:
            print("\n❌ Some database integration tests failed!")
            return 1


if __name__ == "__main__":
    sys.exit(main())