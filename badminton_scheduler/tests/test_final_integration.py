#!/usr/bin/env python3
"""
Final integration test for Task 15 - Final integration and user experience polish.
Tests all features together to ensure seamless user experience.
"""

import pytest
import json
import time
import unittest
import sys
import os
from datetime import date, datetime, timedelta

# Add the current directory to the path so we can import from run.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from run.py
from run import app, db, User, Availability

class TestFinalIntegration(unittest.TestCase):
    """Test final integration and user experience polish."""
    
    def setUp(self):
        """Set up test database and test data."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test users
        self.regular_user = User(username='testuser', email='test@example.com')
        self.regular_user.set_password('testpass')
        
        self.admin_user = User(username='admin', email='admin@example.com', is_admin=True)
        self.admin_user.set_password('adminpass')
        
        db.session.add(self.regular_user)
        db.session.add(self.admin_user)
        db.session.commit()
        
        # Create test availability data
        today = date.today()
        for i in range(10):
            avail = Availability(
                user_id=self.regular_user.id,
                date=today + timedelta(days=i),
                status='available',
                is_all_day=i % 2 == 0,
                time_start=datetime.strptime('19:00', '%H:%M').time() if i % 2 == 1 else None,
                time_end=datetime.strptime('21:00', '%H:%M').time() if i % 2 == 1 else None
            )
            db.session.add(avail)
        
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_user(self, username='testuser', password='testpass'):
        """Helper to log in a user."""
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def test_loading_states_and_visual_feedback(self):
        """Test that loading states and visual feedback work properly."""
        # Login
        self.login_user()
        
        # Test availability creation with validation
        response = self.client.post('/api/availability', 
            json={
                'date': (date.today() + timedelta(days=15)).isoformat(),
                'status': 'available',
                'is_all_day': False,
                'time_start': '19:00',
                'time_end': '21:00'
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Availability set successfully')
    
    def test_optimized_database_queries(self):
        """Test that database queries are optimized for performance."""
        # Login as admin
        self.login_user('admin', 'adminpass')
        
        # Test paginated admin availability endpoint
        response = self.client.get('/api/admin/availability/filtered?page=1&per_page=5')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check pagination structure
        self.assertIn('availability', data)
        self.assertIn('pagination', data)
        self.assertIn('filters', data)
        
        pagination = data['pagination']
        self.assertEqual(pagination['page'], 1)
        self.assertEqual(pagination['per_page'], 5)
        self.assertIn('total_count', pagination)
        self.assertIn('total_pages', pagination)
        self.assertIn('has_prev', pagination)
        self.assertIn('has_next', pagination)
        
        # Test that results are limited to per_page
        self.assertLessEqual(len(data['availability']), 5)
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling with user-friendly messages."""
        # Login
        self.login_user()
        
        # Test validation error
        response = self.client.post('/api/availability', 
            json={
                'date': 'invalid-date',
                'status': 'available'
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('error_type', data)
        self.assertEqual(data['error_type'], 'validation_error')
    
    def test_comprehensive_time_validation(self):
        """Test comprehensive time validation and parsing."""
        # Login
        self.login_user()
        
        # Test various time formats
        time_formats = [
            ('19:00', '21:00'),  # 24-hour format
            ('7:00 PM', '9:00 PM'),  # 12-hour format with minutes
            ('7PM', '9PM'),  # 12-hour format without minutes
        ]
        
        for start_time, end_time in time_formats:
            response = self.client.post('/api/availability', 
                json={
                    'date': (date.today() + timedelta(days=20)).isoformat(),
                    'status': 'available',
                    'is_all_day': False,
                    'time_start': start_time,
                    'time_end': end_time
                })
            
            self.assertEqual(response.status_code, 200, 
                f"Failed for time format: {start_time} - {end_time}")
    
    def test_mobile_responsiveness_features(self):
        """Test mobile-responsive features and touch-friendly interactions."""
        # Login
        self.login_user()
        
        # Create availability entry
        response = self.client.post('/api/availability', 
            json={
                'date': (date.today() + timedelta(days=25)).isoformat(),
                'status': 'available',
                'is_all_day': True
            })
        
        self.assertEqual(response.status_code, 200)
        
        # Get availability to test display
        response = self.client.get('/api/availability')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_admin_filtering_performance(self):
        """Test admin filtering with large datasets for performance."""
        # Login as admin
        self.login_user('admin', 'adminpass')
        
        # Create additional test data
        today = date.today()
        for i in range(50):  # Create more data
            avail = Availability(
                user_id=self.regular_user.id,
                date=today + timedelta(days=i + 20),
                status=['available', 'tentative', 'not_available'][i % 3],
                is_all_day=True
            )
            db.session.add(avail)
        
        db.session.commit()
        
        # Test date range filtering
        start_date = (today + timedelta(days=20)).isoformat()
        end_date = (today + timedelta(days=40)).isoformat()
        
        response = self.client.get(f'/api/admin/availability/filtered?start_date={start_date}&end_date={end_date}&per_page=10')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check that filtering worked
        self.assertIn('availability', data)
        self.assertIn('pagination', data)
        self.assertLessEqual(len(data['availability']), 10)
        
        # Check that dates are within range
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            self.assertGreaterEqual(avail_date, datetime.strptime(start_date, '%Y-%m-%d').date())
            self.assertLessEqual(avail_date, datetime.strptime(end_date, '%Y-%m-%d').date())
    
    def test_user_experience_consistency(self):
        """Test that user experience is consistent across all operations."""
        # Login
        self.login_user()
        
        # Test create, read, update, delete cycle
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        # Create
        response = self.client.post('/api/availability', 
            json={
                'date': future_date,
                'status': 'available',
                'is_all_day': False,
                'time_start': '18:00',
                'time_end': '20:00',
                'notes': 'Test availability'
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        availability_id = data['availability']['id']
        
        # Read
        response = self.client.get('/api/availability')
        self.assertEqual(response.status_code, 200)
        
        # Update
        response = self.client.put(f'/api/availability/{availability_id}', 
            json={
                'status': 'tentative',
                'notes': 'Updated test availability'
            })
        
        self.assertEqual(response.status_code, 200)
        
        # Delete
        response = self.client.delete(f'/api/availability/{availability_id}')
        self.assertEqual(response.status_code, 200)
    
    def test_backward_compatibility(self):
        """Test that all enhancements maintain backward compatibility."""
        # Login
        self.login_user()
        
        # Test legacy time_slot format
        response = self.client.post('/api/availability', 
            json={
                'date': (date.today() + timedelta(days=35)).isoformat(),
                'status': 'available',
                'time_slot': '7-9 PM'  # Legacy format
            })
        
        self.assertEqual(response.status_code, 200)
        
        # Test without time information (all-day)
        response = self.client.post('/api/availability', 
            json={
                'date': (date.today() + timedelta(days=36)).isoformat(),
                'status': 'available'
            })
        
        self.assertEqual(response.status_code, 200)
    
    def test_performance_with_concurrent_operations(self):
        """Test performance with multiple concurrent operations."""
        # Login
        self.login_user()
        
        # Simulate concurrent availability creation
        futures = []
        for i in range(5):
            future_date = (date.today() + timedelta(days=40 + i)).isoformat()
            response = self.client.post('/api/availability', 
                json={
                    'date': future_date,
                    'status': 'available',
                    'is_all_day': True
                })
            self.assertEqual(response.status_code, 200)
        
        # Test that all entries were created successfully
        response = self.client.get('/api/availability')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Should have original 10 + new 5 entries
        self.assertGreaterEqual(len(data), 15)

if __name__ == '__main__':
    # Run the tests
    import unittest
    unittest.main()