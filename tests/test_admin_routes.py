#!/usr/bin/env python3
"""
Test script to verify admin routes and functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import User
from flask import url_for

def test_admin_routes():
    """Test admin routes and access controls."""
    app = create_app('development')
    
    with app.app_context():
        with app.test_client() as client:
            # Create tables
            db.create_all()
            
            # Create admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin', password='admin123', role='Admin')
                db.session.add(admin_user)
                db.session.commit()
            
            # Create regular user
            regular_user = User.query.filter_by(username='regular').first()
            if regular_user:
                db.session.delete(regular_user)
                db.session.commit()
            
            regular_user = User(username='regular', password='regular123', role='User')
            db.session.add(regular_user)
            db.session.commit()
            
            print("✓ Test users created")
            
            # Test admin access without login (should redirect)
            response = client.get('/admin/')
            assert response.status_code == 302, "Should redirect when not logged in"
            print("✓ Admin routes protected when not logged in")
            
            # Login as regular user
            response = client.post('/auth/login', data={
                'username': 'regular',
                'password': 'regular123',
                'csrf_token': 'test'  # In testing, CSRF might be disabled
            }, follow_redirects=True)
            
            # Try to access admin routes as regular user (should be denied)
            response = client.get('/admin/')
            assert response.status_code == 302, "Regular user should be redirected from admin"
            print("✓ Admin routes protected from regular users")
            
            # Logout
            client.get('/auth/logout')
            
            # Login as admin (disable CSRF for testing)
            with client.session_transaction() as sess:
                sess['_fresh'] = True
            
            # Simulate login by setting session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test admin dashboard access
            response = client.get('/admin/')
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.data.decode()}")
            assert response.status_code == 200, "Admin should access dashboard"
            assert b'Admin Dashboard' in response.data, "Should show admin dashboard"
            print("✓ Admin dashboard accessible to admin users")
            
            # Test users list access
            response = client.get('/admin/users')
            assert response.status_code == 200, "Admin should access users list"
            assert b'User Management' in response.data, "Should show user management"
            print("✓ Users list accessible to admin users")
            
            # Test create user access
            response = client.get('/admin/users/create')
            assert response.status_code == 200, "Admin should access create user"
            assert b'Create New User' in response.data, "Should show create user form"
            print("✓ Create user form accessible to admin users")
            
            # Test user detail access
            response = client.get(f'/admin/users/{regular_user.id}')
            assert response.status_code == 200, "Admin should access user details"
            assert b'User Details' in response.data, "Should show user details"
            print("✓ User details accessible to admin users")
            
            print("\n✓ All admin route tests passed!")

if __name__ == '__main__':
    test_admin_routes()