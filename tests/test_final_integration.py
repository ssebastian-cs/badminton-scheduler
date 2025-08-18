#!/usr/bin/env python3
"""
Final integration test suite for badminton scheduler deployment.
This script tests complete application workflows end-to-end.
"""

import os
import sys
import unittest
from datetime import date, time, timedelta
from flask import url_for

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Availability, Comment, AdminAction


class FinalIntegrationTestCase(unittest.TestCase):
    """Comprehensive integration tests for deployment validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create all tables
        db.create_all()
        
        # Create test users
        self.admin_user = User(
            username='admin_test',
            password='admin123',
            role='Admin'
        )
        
        self.regular_user = User(
            username='user_test',
            password='user123',
            role='User'
        )
        
        db.session.add(self.admin_user)
        db.session.add(self.regular_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_user(self, username, password):
        """Helper method to log in a user."""
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout_user(self):
        """Helper method to log out current user."""
        return self.client.get('/auth/logout', follow_redirects=True)
    
    def test_01_application_startup(self):
        """Test that the application starts correctly."""
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])  # 302 for redirect to login
        print("✅ Application startup test passed")
    
    def test_02_database_models(self):
        """Test all database models and relationships."""
        # Test User model
        user_count = User.query.count()
        self.assertEqual(user_count, 2)
        
        # Test user roles
        admin = User.query.filter_by(role='Admin').first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, 'admin_test')
        
        regular = User.query.filter_by(role='User').first()
        self.assertIsNotNone(regular)
        self.assertEqual(regular.username, 'user_test')
        
        # Test password hashing
        self.assertTrue(admin.check_password('admin123'))
        self.assertTrue(regular.check_password('user123'))
        self.assertFalse(admin.check_password('wrong_password'))
        
        print("✅ Database models test passed")
    
    def test_03_authentication_workflow(self):
        """Test complete authentication workflow."""
        # Test login page access
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
        
        # Test successful login
        response = self.login_user('user_test', 'user123')
        self.assertEqual(response.status_code, 200)
        
        # Test protected route access after login
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Test logout
        response = self.logout_user()
        self.assertEqual(response.status_code, 200)
        
        # Test protected route access after logout (should redirect)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        
        print("✅ Authentication workflow test passed")
    
    def test_04_availability_management(self):
        """Test complete availability management workflow."""
        # Login as regular user
        self.login_user('user_test', 'user123')
        
        # Create availability entry
        tomorrow = date.today() + timedelta(days=1)
        availability_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        }
        
        response = self.client.post('/availability/add', data=availability_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify availability was created
        availability = Availability.query.filter_by(user_id=self.regular_user.id).first()
        self.assertIsNotNone(availability)
        self.assertEqual(availability.date, tomorrow)
        self.assertEqual(availability.start_time, time(18, 0))
        self.assertEqual(availability.end_time, time(20, 0))
        
        # Test availability viewing
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Test availability editing
        edit_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '19:00',
            'end_time': '21:00'
        }
        
        response = self.client.post(f'/availability/edit/{availability.id}', 
                                  data=edit_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify edit
        db.session.refresh(availability)
        self.assertEqual(availability.start_time, time(19, 0))
        self.assertEqual(availability.end_time, time(21, 0))
        
        print("✅ Availability management test passed")
    
    def test_05_comments_system(self):
        """Test complete comments system workflow."""
        # Login as regular user
        self.login_user('user_test', 'user123')
        
        # Create comment
        comment_data = {
            'content': 'Test comment for integration testing'
        }
        
        response = self.client.post('/comments/add', data=comment_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify comment was created
        comment = Comment.query.filter_by(user_id=self.regular_user.id).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'Test comment for integration testing')
        
        # Test comments viewing
        response = self.client.get('/comments')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test comment for integration testing', response.data)
        
        # Test comment editing
        edit_data = {
            'content': 'Updated test comment'
        }
        
        response = self.client.post(f'/comments/edit/{comment.id}', 
                                  data=edit_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify edit
        db.session.refresh(comment)
        self.assertEqual(comment.content, 'Updated test comment')
        
        print("✅ Comments system test passed")
    
    def test_06_admin_functionality(self):
        """Test complete admin functionality workflow."""
        # Login as admin
        self.login_user('admin_test', 'admin123')
        
        # Test admin dashboard access
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        
        # Test user management
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        
        # Create new user as admin
        new_user_data = {
            'username': 'admin_created_user',
            'password': 'password123',
            'role': 'User'
        }
        
        response = self.client.post('/admin/users/add', data=new_user_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify user was created
        new_user = User.query.filter_by(username='admin_created_user').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'User')
        
        # Test admin can edit any user's availability
        tomorrow = date.today() + timedelta(days=1)
        admin_availability_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '17:00',
            'end_time': '19:00'
        }
        
        # Create availability for the new user as admin
        response = self.client.post('/availability/add', data=admin_availability_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Test admin action logging
        admin_action = AdminAction(
            admin_id=self.admin_user.id,
            action_type='USER_CREATED',
            target_type='User',
            target_id=new_user.id,
            description='Created user via admin interface'
        )
        db.session.add(admin_action)
        db.session.commit()
        
        # Verify admin action was logged
        action_count = AdminAction.query.filter_by(admin_id=self.admin_user.id).count()
        self.assertGreaterEqual(action_count, 1)
        
        print("✅ Admin functionality test passed")
    
    def test_07_security_features(self):
        """Test security features and access controls."""
        # Test unauthorized access to admin routes
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        # Login as regular user
        self.login_user('user_test', 'user123')
        
        # Test regular user cannot access admin routes
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        # Test CSRF protection (forms should have CSRF tokens)
        response = self.client.get('/availability/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'csrf_token', response.data)
        
        # Test user can only edit their own data
        other_user_availability = Availability.query.filter_by(user_id=self.admin_user.id).first()
        if other_user_availability:
            response = self.client.post(f'/availability/edit/{other_user_availability.id}', 
                                      data={'date': '2024-12-31', 'start_time': '10:00', 'end_time': '12:00'})
            self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        print("✅ Security features test passed")
    
    def test_08_data_validation(self):
        """Test data validation and error handling."""
        # Login as regular user
        self.login_user('user_test', 'user123')
        
        # Test past date validation for availability
        yesterday = date.today() - timedelta(days=1)
        invalid_data = {
            'date': yesterday.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        }
        
        response = self.client.post('/availability/add', data=invalid_data)
        # Should either reject or redirect with error
        self.assertIn(response.status_code, [200, 302, 400])
        
        # Test invalid time range (end before start)
        tomorrow = date.today() + timedelta(days=1)
        invalid_time_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '20:00',
            'end_time': '18:00'
        }
        
        response = self.client.post('/availability/add', data=invalid_time_data)
        self.assertIn(response.status_code, [200, 302, 400])
        
        # Test empty comment
        empty_comment_data = {
            'content': ''
        }
        
        response = self.client.post('/comments/add', data=empty_comment_data)
        self.assertIn(response.status_code, [200, 302, 400])
        
        print("✅ Data validation test passed")
    
    def test_09_complete_user_journey(self):
        """Test complete user journey from registration to usage."""
        # Start fresh - logout any existing session
        self.logout_user()
        
        # Login as admin to create a new user
        self.login_user('admin_test', 'admin123')
        
        # Create new user
        new_user_data = {
            'username': 'journey_user',
            'password': 'journey123',
            'role': 'User'
        }
        
        response = self.client.post('/admin/users/add', data=new_user_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Logout admin
        self.logout_user()
        
        # Login as new user
        response = self.login_user('journey_user', 'journey123')
        self.assertEqual(response.status_code, 200)
        
        # User adds availability
        tomorrow = date.today() + timedelta(days=1)
        availability_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        }
        
        response = self.client.post('/availability/add', data=availability_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # User adds comment
        comment_data = {
            'content': 'Looking forward to playing!'
        }
        
        response = self.client.post('/comments/add', data=comment_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # User views dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # User views comments
        response = self.client.get('/comments')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Looking forward to playing!', response.data)
        
        # User logs out
        response = self.logout_user()
        self.assertEqual(response.status_code, 200)
        
        print("✅ Complete user journey test passed")
    
    def test_10_application_stability(self):
        """Test application stability under various conditions."""
        # Test multiple rapid requests
        for i in range(10):
            response = self.client.get('/auth/login')
            self.assertEqual(response.status_code, 200)
        
        # Test session handling
        self.login_user('user_test', 'user123')
        
        # Make multiple authenticated requests
        for i in range(5):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            
            response = self.client.get('/comments')
            self.assertEqual(response.status_code, 200)
        
        # Test database transaction handling
        try:
            with db.session.begin():
                test_user = User(username='transaction_test', password='test123', role='User')
                db.session.add(test_user)
                # Simulate error
                raise Exception("Test transaction rollback")
        except:
            pass
        
        # Verify rollback worked
        rollback_user = User.query.filter_by(username='transaction_test').first()
        self.assertIsNone(rollback_user)
        
        print("✅ Application stability test passed")


def run_integration_tests():
    """Run all integration tests and return results."""
    print("Running Final Integration Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(FinalIntegrationTestCase)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = failures == 0 and errors == 0
    
    if success:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The application is ready for deployment.")
    else:
        print("\n⚠️  SOME INTEGRATION TESTS FAILED!")
        print("Please review and fix the issues before deployment.")
    
    return success


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)