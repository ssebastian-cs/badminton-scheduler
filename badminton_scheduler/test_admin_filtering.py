#!/usr/bin/env python3
"""
Test suite for admin date filtering API endpoint.
Tests the GET /api/admin/availability/filtered endpoint functionality.
"""

import pytest
import json
import sys
import os
from datetime import datetime, date, timedelta

# Add the current directory to the path so we can import run
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User, Availability

class TestAdminFiltering:
    """Test class for admin filtering functionality."""
    
    @pytest.fixture
    def test_app(self):
        """Create test app."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return test_app.test_client()
    
    @pytest.fixture
    def admin_user(self, test_app):
        """Create admin user."""
        with test_app.app_context():
            admin = User(username='admin', email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            return admin
    
    @pytest.fixture
    def regular_user(self, test_app):
        """Create regular user."""
        with test_app.app_context():
            user = User(username='user1', email='user1@test.com', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def sample_availability(self, test_app, admin_user, regular_user):
        """Create sample availability data."""
        with test_app.app_context():
            today = date.today()
            
            # Create availability entries for different dates
            availabilities = [
                # Today's entries
                Availability(user_id=admin_user.id, date=today, status='available', time_slot='19:00-21:00'),
                Availability(user_id=regular_user.id, date=today, status='tentative', time_slot=None),
                
                # Yesterday's entries
                Availability(user_id=admin_user.id, date=today - timedelta(days=1), status='not_available', time_slot='18:00-20:00'),
                Availability(user_id=regular_user.id, date=today - timedelta(days=1), status='available', time_slot='7:00 PM'),
                
                # Tomorrow's entries
                Availability(user_id=admin_user.id, date=today + timedelta(days=1), status='available', time_slot=None),
                Availability(user_id=regular_user.id, date=today + timedelta(days=1), status='tentative', time_slot='until 20:00'),
                
                # Next week's entries
                Availability(user_id=admin_user.id, date=today + timedelta(days=7), status='available', time_slot='19:00-22:00'),
                Availability(user_id=regular_user.id, date=today + timedelta(days=7), status='not_available', time_slot=None),
            ]
            
            for avail in availabilities:
                db.session.add(avail)
            
            db.session.commit()
            return availabilities
    
    def login_user(self, client, username, password):
        """Helper to log in a user."""
        response = client.post('/auth/login', 
                             data=json.dumps({'username': username, 'password': password}),
                             content_type='application/json')
        return response
    
    def test_admin_filtering_endpoint_exists(self, client, admin_user, sample_availability):
        """Test that the admin filtering endpoint exists and is accessible."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        # Test endpoint exists
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'availability' in data
        assert 'pagination' in data
        assert 'filters' in data
        assert 'result_count' in data
    
    def test_admin_permission_required(self, client, regular_user, sample_availability):
        """Test that admin permission is required to access the endpoint."""
        # Login as regular user
        self.login_user(client, 'user1', 'user123')
        
        # Try to access admin endpoint
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 403
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Admin access required' in data['error']
    
    def test_unauthenticated_access_denied(self, client, sample_availability):
        """Test that unauthenticated users cannot access the endpoint."""
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 401  # Unauthorized
    
    def test_date_range_filtering(self, client, admin_user, sample_availability):
        """Test date range filtering functionality."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Test filtering with start_date only
        response = client.get(f'/api/admin/availability/filtered?start_date={today.isoformat()}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['filters']['start_date'] == today.isoformat()
        
        # All returned entries should be from today or later
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date >= today
        
        # Test filtering with end_date only
        response = client.get(f'/api/admin/availability/filtered?end_date={today.isoformat()}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['filters']['end_date'] == today.isoformat()
        
        # All returned entries should be from today or earlier
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date <= today
        
        # Test filtering with both start_date and end_date
        response = client.get(f'/api/admin/availability/filtered?start_date={yesterday.isoformat()}&end_date={tomorrow.isoformat()}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['filters']['start_date'] == yesterday.isoformat()
        assert data['filters']['end_date'] == tomorrow.isoformat()
        
        # All returned entries should be within the date range
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert yesterday <= avail_date <= tomorrow
    
    def test_invalid_date_formats(self, client, admin_user, sample_availability):
        """Test handling of invalid date formats."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        # Test invalid start_date format
        response = client.get('/api/admin/availability/filtered?start_date=invalid-date')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid start_date format' in data['error']
        
        # Test invalid end_date format
        response = client.get('/api/admin/availability/filtered?end_date=2025/08/01')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid end_date format' in data['error']
    
    def test_invalid_date_range_logic(self, client, admin_user, sample_availability):
        """Test validation of date range logic."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Test start_date after end_date
        response = client.get(f'/api/admin/availability/filtered?start_date={tomorrow.isoformat()}&end_date={today.isoformat()}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Start date must be before or equal to end date' in data['error']
    
    def test_pagination_functionality(self, client, admin_user, sample_availability):
        """Test pagination support."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        # Test default pagination
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 50  # Default per_page
        assert 'total_count' in data['pagination']
        assert 'total_pages' in data['pagination']
        
        # Test custom page size
        response = client.get('/api/admin/availability/filtered?per_page=2')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['pagination']['per_page'] == 2
        assert len(data['availability']) <= 2
        
        # Test specific page
        response = client.get('/api/admin/availability/filtered?page=1&per_page=3')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 3
    
    def test_pagination_validation(self, client, admin_user, sample_availability):
        """Test pagination parameter validation."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        # Test invalid page number
        response = client.get('/api/admin/availability/filtered?page=0')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Page number must be positive' in data['error']
        
        # Test invalid per_page (too small)
        response = client.get('/api/admin/availability/filtered?per_page=0')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Per page must be between 1 and 1000' in data['error']
        
        # Test invalid per_page (too large)
        response = client.get('/api/admin/availability/filtered?per_page=1001')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Per page must be between 1 and 1000' in data['error']
    
    def test_nonexistent_page(self, client, admin_user, sample_availability):
        """Test handling of nonexistent pages."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        # Request a page that doesn't exist
        response = client.get('/api/admin/availability/filtered?page=999&per_page=10')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Page 999 does not exist' in data['error']
    
    def test_user_information_included(self, client, admin_user, sample_availability):
        """Test that user information is included in the response."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check that user information is included
        for avail in data['availability']:
            assert 'username' in avail
            assert 'user_email' in avail
            assert avail['username'] in ['admin', 'user1']
            assert '@test.com' in avail['user_email']
    
    def test_time_information_parsing(self, client, admin_user, sample_availability):
        """Test that time information is properly parsed and included."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check that time information is properly parsed
        for avail in data['availability']:
            assert 'time_start' in avail
            assert 'time_end' in avail
            assert 'is_all_day' in avail
            
            # If time_slot exists, check parsing
            if avail.get('time_slot'):
                if '-' in avail['time_slot'] and not avail['time_slot'].startswith('until'):
                    # Should have both start and end times
                    assert avail['time_start'] is not None
                    assert avail['time_end'] is not None
                    assert avail['is_all_day'] is False
                elif avail['time_slot'].startswith('until'):
                    # Should have only end time
                    assert avail['time_start'] is None
                    assert avail['time_end'] is not None
                    assert avail['is_all_day'] is False
            else:
                # All-day availability
                assert avail['is_all_day'] is True
    
    def test_result_count_accuracy(self, client, admin_user, sample_availability):
        """Test that result count is accurate."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check that result_count matches actual results
        assert data['result_count'] == len(data['availability'])
        
        # Check that total_count is reasonable
        assert data['pagination']['total_count'] >= data['result_count']
    
    def test_ordering_consistency(self, client, admin_user, sample_availability):
        """Test that results are ordered consistently."""
        # Login as admin
        self.login_user(client, 'admin', 'admin123')
        
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check that results are ordered by date (descending) and username
        prev_date = None
        prev_username = None
        
        for avail in data['availability']:
            current_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            current_username = avail['username']
            
            if prev_date is not None:
                # Date should be descending or equal
                assert current_date <= prev_date
                
                # If same date, username should be in order
                if current_date == prev_date and prev_username is not None:
                    assert current_username >= prev_username
            
            prev_date = current_date
            prev_username = current_username

if __name__ == '__main__':
    pytest.main([__file__, '-v'])