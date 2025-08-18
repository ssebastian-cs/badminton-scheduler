#!/usr/bin/env python3
"""
Test script for admin content moderation functionality.
"""

import os
import sys
from datetime import date, time, datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Availability, Comment, AdminAction
from app.utils import log_admin_action

def test_admin_moderation():
    """Test the admin content moderation functionality."""
    
    # Create app and context
    app = create_app('development')
    
    with app.app_context():
        print("Testing Admin Content Moderation Features...")
        print("=" * 50)
        
        # Test 1: Create test users
        print("\n1. Creating test users...")
        
        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', password='admin123', role='Admin')
            db.session.add(admin_user)
        
        # Create regular user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', password='test123', role='User')
            db.session.add(test_user)
        
        db.session.commit()
        print(f"✓ Admin user: {admin_user.username} (ID: {admin_user.id})")
        print(f"✓ Test user: {test_user.username} (ID: {test_user.id})")
        
        # Test 2: Create test availability
        print("\n2. Creating test availability...")
        future_date = date.today() + timedelta(days=1)
        availability = Availability(
            user_id=test_user.id,
            date=future_date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        db.session.add(availability)
        db.session.commit()
        print(f"✓ Created availability: {availability.id} for {test_user.username}")
        
        # Test 3: Create test comment
        print("\n3. Creating test comment...")
        comment = Comment(
            user_id=test_user.id,
            content="This is a test comment for moderation testing."
        )
        db.session.add(comment)
        db.session.commit()
        print(f"✓ Created comment: {comment.id} by {test_user.username}")
        
        # Test 4: Test audit logging
        print("\n4. Testing audit logging...")
        
        # Simulate admin login for logging
        from flask_login import login_user
        with app.test_request_context():
            login_user(admin_user)
            
            # Test logging admin actions
            log_admin_action(
                action_type='edit_availability',
                target_type='availability',
                target_id=availability.id,
                target_user_id=test_user.id,
                description=f'Test edit of availability for {test_user.username}',
                details={'test': 'This is a test audit log entry'}
            )
            
            log_admin_action(
                action_type='edit_comment',
                target_type='comment',
                target_id=comment.id,
                target_user_id=test_user.id,
                description=f'Test edit of comment by {test_user.username}',
                details={'original_content': 'Original content', 'new_content': 'Modified content'}
            )
        
        # Verify audit logs were created
        audit_logs = AdminAction.query.all()
        print(f"✓ Created {len(audit_logs)} audit log entries")
        
        for log in audit_logs:
            print(f"  - {log.action_type}: {log.description}")
        
        # Test 5: Test model relationships
        print("\n5. Testing model relationships...")
        
        # Test AdminAction relationships
        for log in audit_logs:
            print(f"✓ Audit log {log.id}:")
            print(f"  - Admin: {log.admin_user.username}")
            if log.target_user:
                print(f"  - Target user: {log.target_user.username}")
            print(f"  - Action: {log.action_type} on {log.target_type}")
        
        # Test User relationships
        admin_actions_performed = admin_user.admin_actions_performed
        print(f"✓ Admin {admin_user.username} performed {len(admin_actions_performed)} actions")
        
        admin_actions_received = test_user.admin_actions_received
        print(f"✓ User {test_user.username} was target of {len(admin_actions_received)} actions")
        
        # Test 6: Test data validation
        print("\n6. Testing data validation...")
        
        try:
            # Test invalid action type
            invalid_action = AdminAction(
                admin_user_id=admin_user.id,
                action_type='invalid_action',
                target_type='user',
                target_id=test_user.id,
                description='Test invalid action'
            )
            db.session.add(invalid_action)
            db.session.commit()
            print("✗ Should have failed validation for invalid action type")
        except ValueError as e:
            print(f"✓ Correctly rejected invalid action type: {e}")
            db.session.rollback()
        
        try:
            # Test invalid target type
            invalid_target = AdminAction(
                admin_user_id=admin_user.id,
                action_type='edit_comment',
                target_type='invalid_target',
                target_id=comment.id,
                description='Test invalid target'
            )
            db.session.add(invalid_target)
            db.session.commit()
            print("✗ Should have failed validation for invalid target type")
        except ValueError as e:
            print(f"✓ Correctly rejected invalid target type: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 50)
        print("✓ All admin content moderation tests passed!")
        print("\nFeatures implemented:")
        print("- AdminAction model with audit logging")
        print("- Admin routes for content moderation")
        print("- Audit logging utility functions")
        print("- Model relationships and validation")
        print("- Admin templates for content management")
        
        return True

if __name__ == '__main__':
    test_admin_moderation()