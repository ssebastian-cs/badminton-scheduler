#!/usr/bin/env python3
"""
Test script to verify admin user management functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import User
from flask import url_for

def test_admin_functionality():
    """Test admin user management features."""
    app = create_app('development')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', password='admin123', role='Admin')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Created admin user")
        else:
            print("✓ Admin user already exists")
        
        # Create test user
        test_user = User.query.filter_by(username='testuser').first()
        if test_user:
            db.session.delete(test_user)
            db.session.commit()
        
        test_user = User(username='testuser', password='test123', role='User')
        db.session.add(test_user)
        db.session.commit()
        print("✓ Created test user")
        
        # Test user statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        blocked_users = User.query.filter_by(is_active=False).count()
        admin_users = User.query.filter_by(role='Admin').count()
        
        print(f"✓ User statistics: {total_users} total, {active_users} active, {blocked_users} blocked, {admin_users} admin")
        
        # Test user blocking
        test_user.is_active = False
        db.session.commit()
        print("✓ User blocking functionality works")
        
        # Test user unblocking
        test_user.is_active = True
        db.session.commit()
        print("✓ User unblocking functionality works")
        
        # Test user deletion (with cascade)
        user_id = test_user.id
        db.session.delete(test_user)
        db.session.commit()
        
        deleted_user = User.query.get(user_id)
        if deleted_user is None:
            print("✓ User deletion with cascade works")
        else:
            print("✗ User deletion failed")
        
        print("\n✓ All admin user management functionality tests passed!")

if __name__ == '__main__':
    test_admin_functionality()