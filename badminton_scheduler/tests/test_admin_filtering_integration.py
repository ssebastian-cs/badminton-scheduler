#!/usr/bin/env python3
"""
Integration tests for admin filtering functionality.
Tests the complete admin filtering workflow with various scenarios.

Requirements covered:
- 3.1: Admin access to availability view with filtering
- 3.2: Date range filtering (start_date and end_date)
- 3.3: Filtered results display with user information
- 3.4: Result count and pagination support
- 3.7: Entry count and date range information display
- 3.8: Admin filtering functionality testing
"""

import pytest
import json
import sys
import os
from datetime import datetime, date, timedelta

# Add the current directory to the path so we can import run
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User, Availability

class TestAdminFilteringIntegration:
    """Integration tests for admin filtering functionality."""
    
    @pytest.fixture
    def test_app(self):
        """Create test app with in-memory database."""
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
            admin = User(username='admin_filter', email='admin@filter.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            return admin
    
    @pytest.fixture
    def regular_users(self, test_app):
        """Create multiple regular users for testing."""
        with test_app.app_context():
            users = []
            for i in range(3):
                user = User(
                    username=f'user{i}_filter',
                    email=f'user{i}@filter.com',
                    is_admin=False
                )
                user.set_password('user123')
                db.session.add(user)
                users.append(user)
            
            db.session.commit()
            return users
    
    @pytest.fixture
    def comprehensive_availability_data(self, test_app, admin_user, regular_users):
        """Create comprehensive availability data for testing."""
        with test_app.app_context():
            today = date.today()
            availabilities = []
            
            # Create availability entries for different dates and users
            date_offsets = [-7, -3, -1, 0, 1, 3, 7, 14, 30]
            statuses = ['available', 'tentative', 'not_available']
            time_slots = [None, '19:00-21:00', '7:00 PM', 'until 20:00']
            
            all_users = [admin_user] + regular_users
            
            for i, offset in enumerate(date_offsets):
                avail_date = today + timedelta(days=offset)
                user = all_users[i % len(all_users)]
                status = statuses[i % len(statuses)]
                time_slot = time_slots[i % len(time_slots)]
                
                # Determine time fields based on time_slot
                time_start = None
                time_end = None
                is_all_day = True
                
                if time_slot:
                    is_all_day = False
                    if time_slot == '19:00-21:00':
                        time_start = datetime.strptime('19:00', '%H:%M').time()
                        time_end = datetime.strptime('21:00', '%H:%M').time()
                    elif time_slot == '7:00 PM':
                        time_start = datetime.strptime('19:00', '%H:%M').time()
                    elif time_slot == 'until 20:00':
                        time_end = datetime.strptime('20:00', '%H:%M').time()
                
                availability = Availability(
                    user_id=user.id,
                    date=avail_date,
                    status=status,
                    play_preference='either',
                    notes=f'Test availability {i}',
                    time_slot=time_slot,
                    time_start=time_start,
                    time_end=time_end,
                    is_all_day=is_all_day
                )
                
                db.session.add(availability)
                availabilities.append(availability)
            
            db.session.commit()
            return availabilities
    
    def login_admin(self, client):
        """Helper to log in admin user."""
        response = client.post('/auth/login', 
                             data=json.dumps({'username': 'admin_filter', 'password': 'admin123'}),
                             content_type='application/json')
        return response
    
    def login_regular_user(self, client, username='user0_filter'):
        """Helper to log in regular user."""
        response = client.post('/auth/login', 
                             data=json.dumps({'username': username, 'password': 'user123'}),
                             content_type='application/json')
        return response

    # ========== Basic Functionality Tests ==========
    
    def test_admin_filtering_endpoint_basic_access(self, client, admin_user, comprehensive_availability_data):
        """Test basic access to admin filtering endpoint (Requirement 3.1)."""
        # Login as admin
        self.login_admin(client)
        
        # Access admin filtering endpoint
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'availability' in data
        assert 'pagination' in data
        assert 'filters' in data
        assert 'result_count' in data
        
        # Verify availability data includes user information (Requirement 3.3)
        for avail in data['availability']:
            assert 'id' in avail
            assert 'username' in avail
            assert 'user_email' in avail
            assert 'date' in avail
            assert 'status' in avail
            assert 'time_start' in avail
            assert 'time_end' in avail
            assert 'is_all_day' in avail
    
    def test_admin_permission_enforcement(self, client, regular_users, comprehensive_availability_data):
        """Test that admin permission is required."""
        # Login as regular user
        self.login_regular_user(client)
        
        # Try to access admin filtering endpoint
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'admin' in data['error'].lower()
    
    def test_unauthenticated_access_denied(self, client, comprehensive_availability_data):
        """Test that unauthenticated access is denied."""
        # Don't login
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login

    # ========== Date Range Filtering Tests ==========
    
    def test_start_date_filtering(self, client, admin_user, comprehensive_availability_data):
        """Test filtering with start_date parameter (Requirement 3.2)."""
        # Login as admin
        self.login_admin(client)
        
        today = date.today()
        start_date = today.isoformat()
        
        # Filter from today onwards
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify filter is applied
        assert data['filters']['start_date'] == start_date
        
        # Verify all results are from start_date onwards
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date >= today, f"Date {avail_date} should be >= {today}"
        
        # Verify result count is accurate (Requirement 3.7)
        assert data['result_count'] == len(data['availability'])
        assert data['result_count'] > 0  # Should have future entries
    
    def test_end_date_filtering(self, client, admin_user, comprehensive_availability_data):
        """Test filtering with end_date parameter (Requirement 3.2)."""
        # Login as admin
        self.login_admin(client)
        
        today = date.today()
        end_date = today.isoformat()
        
        # Filter up to today
        response = client.get(f'/api/admin/availability/filtered?end_date={end_date}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify filter is applied
        assert data['filters']['end_date'] == end_date
        
        # Verify all results are up to end_date
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date <= today, f"Date {avail_date} should be <= {today}"
        
        # Verify result count is accurate
        assert data['result_count'] == len(data['availability'])
        assert data['result_count'] > 0  # Should have past/current entries
    
    def test_date_range_filtering(self, client, admin_user, comprehensive_availability_data):
        """Test filtering with both start_date and end_date (Requirement 3.2)."""
        # Login as admin
        self.login_admin(client)
        
        today = date.today()
        start_date = (today - timedelta(days=2)).isoformat()
        end_date = (today + timedelta(days=2)).isoformat()
        
        # Filter within date range
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}&end_date={end_date}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify filters are applied
        assert data['filters']['start_date'] == start_date
        assert data['filters']['end_date'] == end_date
        
        # Verify all results are within date range
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert start_date_obj <= avail_date <= end_date_obj, \
                f"Date {avail_date} should be between {start_date_obj} and {end_date_obj}"
        
        # Verify result count
        assert data['result_count'] == len(data['availability'])
    
    def test_no_results_in_date_range(self, client, admin_user, comprehensive_availability_data):
        """Test filtering with date range that has no results."""
        # Login as admin
        self.login_admin(client)
        
        # Use a future date range with no data
        start_date = (date.today() + timedelta(days=100)).isoformat()
        end_date = (date.today() + timedelta(days=110)).isoformat()
        
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}&end_date={end_date}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return empty results
        assert data['availability'] == []
        assert data['result_count'] == 0
        assert data['pagination']['total_count'] == 0

    # ========== Pagination Tests ==========
    
    def test_pagination_functionality(self, client, admin_user, comprehensive_availability_data):
        """Test pagination support (Requirement 3.4)."""
        # Login as admin
        self.login_admin(client)
        
        # Test default pagination
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify pagination structure
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'per_page' in pagination
        assert 'total_count' in pagination
        assert 'total_pages' in pagination
        
        # Default values
        assert pagination['page'] == 1
        assert pagination['per_page'] == 50  # Default per_page
        assert pagination['total_count'] >= len(data['availability'])
        
        # Test custom page size
        response = client.get('/api/admin/availability/filtered?per_page=3')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['pagination']['per_page'] == 3
        assert len(data['availability']) <= 3
    
    def test_pagination_with_filtering(self, client, admin_user, comprehensive_availability_data):
        """Test pagination combined with date filtering."""
        # Login as admin
        self.login_admin(client)
        
        today = date.today()
        start_date = (today - timedelta(days=10)).isoformat()
        
        # Get filtered results with pagination
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}&per_page=2')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify pagination and filtering work together
        assert data['pagination']['per_page'] == 2
        assert len(data['availability']) <= 2
        assert data['filters']['start_date'] == start_date
        
        # Verify all results respect the date filter
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date >= start_date_obj

    # ========== Data Integrity and Validation Tests ==========
    
    def test_invalid_date_format_handling(self, client, admin_user, comprehensive_availability_data):
        """Test handling of invalid date formats."""
        # Login as admin
        self.login_admin(client)
        
        # Test invalid start_date
        response = client.get('/api/admin/availability/filtered?start_date=invalid-date')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'date' in data['error'].lower()
        
        # Test invalid end_date
        response = client.get('/api/admin/availability/filtered?end_date=2025/08/01')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'date' in data['error'].lower()
    
    def test_invalid_date_range_logic(self, client, admin_user, comprehensive_availability_data):
        """Test validation of date range logic."""
        # Login as admin
        self.login_admin(client)
        
        today = date.today()
        start_date = (today + timedelta(days=1)).isoformat()
        end_date = today.isoformat()
        
        # start_date after end_date should fail
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}&end_date={end_date}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'start date' in data['error'].lower() and 'end date' in data['error'].lower()
    
    def test_pagination_parameter_validation(self, client, admin_user, comprehensive_availability_data):
        """Test validation of pagination parameters."""
        # Login as admin
        self.login_admin(client)
        
        # Test invalid page number
        response = client.get('/api/admin/availability/filtered?page=0')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'page' in data['error'].lower()
        
        # Test invalid per_page (too small)
        response = client.get('/api/admin/availability/filtered?per_page=0')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
        # Test invalid per_page (too large)
        response = client.get('/api/admin/availability/filtered?per_page=1001')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    # ========== Time Information Parsing Tests ==========
    
    def test_time_information_parsing(self, client, admin_user, comprehensive_availability_data):
        """Test that time information is properly parsed and included."""
        # Login as admin
        self.login_admin(client)
        
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Find entries with different time configurations
        all_day_found = False
        time_range_found = False
        single_time_found = False
        
        for avail in data['availability']:
            # All entries should have time fields
            assert 'time_start' in avail
            assert 'time_end' in avail
            assert 'is_all_day' in avail
            
            if avail['is_all_day']:
                all_day_found = True
                assert avail['time_start'] is None
                assert avail['time_end'] is None
            elif avail['time_start'] and avail['time_end']:
                time_range_found = True
                # Validate time format
                assert ':' in avail['time_start']
                assert ':' in avail['time_end']
            elif avail['time_start'] or avail['time_end']:
                single_time_found = True
        
        # Should have found different types of time configurations
        assert all_day_found or time_range_found or single_time_found

    # ========== User Information Tests ==========
    
    def test_user_information_included(self, client, admin_user, comprehensive_availability_data):
        """Test that user information is included in results (Requirement 3.3)."""
        # Login as admin
        self.login_admin(client)
        
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify user information is included
        for avail in data['availability']:
            assert 'username' in avail
            assert 'user_email' in avail
            
            # Verify username format
            assert '_filter' in avail['username']  # Our test users have this suffix
            
            # Verify email format
            assert '@filter.com' in avail['user_email']  # Our test users have this domain
    
    def test_multiple_users_data_aggregation(self, client, admin_user, comprehensive_availability_data):
        """Test that data from multiple users is properly aggregated."""
        # Login as admin
        self.login_admin(client)
        
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Collect unique usernames
        usernames = set(avail['username'] for avail in data['availability'])
        
        # Should have entries from multiple users
        assert len(usernames) > 1
        
        # Should include admin and regular users
        admin_entries = [avail for avail in data['availability'] if avail['username'] == 'admin_filter']
        user_entries = [avail for avail in data['availability'] if 'user' in avail['username']]
        
        assert len(admin_entries) > 0
        assert len(user_entries) > 0

    # ========== Result Ordering Tests ==========
    
    def test_result_ordering_consistency(self, client, admin_user, comprehensive_availability_data):
        """Test that results are ordered consistently."""
        # Login as admin
        self.login_admin(client)
        
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check ordering (should be by date descending, then by username)
        prev_date = None
        prev_username = None
        
        for avail in data['availability']:
            current_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            current_username = avail['username']
            
            if prev_date is not None:
                # Date should be descending or equal
                assert current_date <= prev_date, \
                    f"Date ordering issue: {current_date} should be <= {prev_date}"
                
                # If same date, username should be in order
                if current_date == prev_date and prev_username is not None:
                    assert current_username >= prev_username, \
                        f"Username ordering issue: {current_username} should be >= {prev_username}"
            
            prev_date = current_date
            prev_username = current_username

    # ========== Performance and Edge Cases ==========
    
    def test_large_date_range_handling(self, client, admin_user, comprehensive_availability_data):
        """Test handling of large date ranges."""
        # Login as admin
        self.login_admin(client)
        
        # Very large date range
        start_date = (date.today() - timedelta(days=365)).isoformat()
        end_date = (date.today() + timedelta(days=365)).isoformat()
        
        response = client.get(f'/api/admin/availability/filtered?start_date={start_date}&end_date={end_date}')
        
        # Should handle gracefully (might be slow but shouldn't error)
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return all our test data
        assert data['result_count'] > 0
    
    def test_edge_case_dates(self, client, admin_user, comprehensive_availability_data):
        """Test edge case dates."""
        # Login as admin
        self.login_admin(client)
        
        # Test with today's date
        today = date.today().isoformat()
        
        response = client.get(f'/api/admin/availability/filtered?start_date={today}&end_date={today}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should only return today's entries (if any)
        for avail in data['availability']:
            assert avail['date'] == today

if __name__ == '__main__':
    pytest.main([__file__, '-v'])