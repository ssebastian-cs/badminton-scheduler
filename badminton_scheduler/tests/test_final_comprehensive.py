#!/usr/bin/env python3
"""
Final comprehensive test suite for availability enhancements.
Tests all new API endpoints and validation logic with proper session management.

Requirements covered:
- 2.6: User ownership validation for edit/delete operations
- 2.7: Past date protection for edit/delete operations  
- 3.8: Admin filtering functionality with date ranges
- 5.4: Data integrity and validation
"""

import pytest
import json
import sys
import os
from datetime import datetime, date, timedelta

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User, Availability

class TestFinalComprehensive:
    """Final comprehensive test class."""
    
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
    
    def create_test_users(self, test_app):
        """Create test users and return their IDs."""
        with test_app.app_context():
            # Create admin user
            admin = User(username='admin_test', email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create regular users
            user1 = User(username='user1_test', email='user1@test.com', is_admin=False)
            user1.set_password('user123')
            db.session.add(user1)
            
            user2 = User(username='user2_test', email='user2@test.com', is_admin=False)
            user2.set_password('user123')
            db.session.add(user2)
            
            db.session.commit()
            
            return {
                'admin_id': admin.id,
                'user1_id': user1.id,
                'user2_id': user2.id
            }
    
    def login_user(self, client, username, password):
        """Helper to log in a user."""
        response = client.post('/auth/login', 
                             data=json.dumps({'username': username, 'password': password}),
                             content_type='application/json')
        return response
    
    def create_test_availability(self, test_app, user_id, date_offset=7, **kwargs):
        """Helper to create test availability entry."""
        with test_app.app_context():
            avail_date = date.today() + timedelta(days=date_offset)
            defaults = {
                'user_id': user_id,
                'date': avail_date,
                'status': 'available',
                'play_preference': 'either',
                'notes': 'Test availability',
                'is_all_day': True
            }
            defaults.update(kwargs)
            
            availability = Availability(**defaults)
            db.session.add(availability)
            db.session.commit()
            return availability.id

    # ========== Basic Endpoint Tests ==========
    
    def test_endpoints_exist(self, client, test_app):
        """Test that all new endpoints exist and don't return 405 Method Not Allowed."""
        user_ids = self.create_test_users(test_app)
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Test PUT endpoint exists
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        assert response.status_code != 405
        
        # Test DELETE endpoint exists
        response = client.delete(f'/api/availability/{avail_id}')
        assert response.status_code != 405
        
        # Login admin for admin endpoint
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test admin filtering endpoint exists
        response = client.get('/api/admin/availability/filtered')
        assert response.status_code != 405

    # ========== User Ownership Validation Tests (Requirement 2.6) ==========
    
    def test_user_ownership_edit(self, client, test_app):
        """Test user ownership validation for edit operations."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for user1
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login as user2
        self.login_user(client, 'user2_test', 'user123')
        
        # Try to edit user1's availability
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'unauthorized' in data['error'].lower() or 'own' in data['error'].lower()
    
    def test_user_ownership_delete(self, client, test_app):
        """Test user ownership validation for delete operations."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for user1
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login as user2
        self.login_user(client, 'user2_test', 'user123')
        
        # Try to delete user1's availability
        response = client.delete(f'/api/availability/{avail_id}')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'unauthorized' in data['error'].lower() or 'own' in data['error'].lower()
    
    def test_admin_can_edit_any(self, client, test_app):
        """Test that admin can edit any user's availability."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for user1
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Admin should be able to edit any availability
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps({'status': 'not_available', 'notes': 'Updated by admin'}),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['availability']['status'] == 'not_available'
        assert data['availability']['notes'] == 'Updated by admin'
    
    def test_admin_can_delete_any(self, client, test_app):
        """Test that admin can delete any user's availability."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for user1
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Admin should be able to delete any availability
        response = client.delete(f'/api/availability/{avail_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'deleted' in data['message'].lower()

    # ========== Past Date Protection Tests (Requirement 2.7) ==========
    
    def test_past_date_protection_edit(self, client, test_app):
        """Test past date protection for edit operations."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for past date
        past_avail_id = self.create_test_availability(test_app, user_ids['user1_id'], date_offset=-1)
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Try to edit past availability
        response = client.put(f'/api/availability/{past_avail_id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'past' in data['error'].lower()
    
    def test_past_date_protection_delete(self, client, test_app):
        """Test past date protection for delete operations."""
        user_ids = self.create_test_users(test_app)
        
        # Create availability for past date
        past_avail_id = self.create_test_availability(test_app, user_ids['user1_id'], date_offset=-1)
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Try to delete past availability
        response = client.delete(f'/api/availability/{past_avail_id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'past' in data['error'].lower()

    # ========== Admin Filtering Tests (Requirement 3.8) ==========
    
    def test_admin_filtering_permission_required(self, client, test_app):
        """Test that admin permission is required for filtering endpoint."""
        self.create_test_users(test_app)
        
        # Login as regular user
        self.login_user(client, 'user1_test', 'user123')
        
        # Try to access admin filtering endpoint
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'admin' in data['error'].lower()
    
    def test_admin_filtering_basic_functionality(self, client, test_app):
        """Test basic admin filtering functionality."""
        user_ids = self.create_test_users(test_app)
        
        # Create test data
        self.create_test_availability(test_app, user_ids['user1_id'], date_offset=1)
        self.create_test_availability(test_app, user_ids['admin_id'], date_offset=2)
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test basic filtering endpoint
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'availability' in data
        assert 'pagination' in data
        assert 'filters' in data
        assert 'result_count' in data
        
        # Should have entries from both users
        assert len(data['availability']) >= 2
        
        # Verify user information is included
        for avail in data['availability']:
            assert 'username' in avail
            assert 'user_email' in avail
    
    def test_admin_filtering_date_range(self, client, test_app):
        """Test admin filtering with date ranges."""
        user_ids = self.create_test_users(test_app)
        
        # Create test data for different dates
        today = date.today()
        
        # Create availabilities for different dates
        with test_app.app_context():
            # Yesterday
            avail_yesterday = Availability(
                user_id=user_ids['user1_id'],
                date=today - timedelta(days=1),
                status='available',
                is_all_day=True
            )
            # Tomorrow
            avail_tomorrow = Availability(
                user_id=user_ids['user1_id'],
                date=today + timedelta(days=1),
                status='tentative',
                is_all_day=True
            )
            
            db.session.add_all([avail_yesterday, avail_tomorrow])
            db.session.commit()
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test filtering with start_date
        response = client.get(f'/api/admin/availability/filtered?start_date={today.isoformat()}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['filters']['start_date'] == today.isoformat()
        
        # All returned entries should be from today or later
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date >= today
    
    def test_admin_filtering_invalid_dates(self, client, test_app):
        """Test admin filtering with invalid date formats."""
        self.create_test_users(test_app)
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test invalid start_date format
        response = client.get('/api/admin/availability/filtered?start_date=invalid-date')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'date' in data['error'].lower()

    # ========== Data Integrity and Validation Tests (Requirement 5.4) ==========
    
    def test_status_validation(self, client, test_app):
        """Test availability status validation."""
        user_ids = self.create_test_users(test_app)
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Test valid statuses
        valid_statuses = ['available', 'tentative', 'not_available']
        
        for status in valid_statuses:
            response = client.put(f'/api/availability/{avail_id}',
                                data=json.dumps({'status': status}),
                                content_type='application/json')
            assert response.status_code == 200, f"Valid status failed: {status}"
        
        # Test invalid status
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps({'status': 'invalid_status'}),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_time_validation(self, client, test_app):
        """Test time format validation."""
        user_ids = self.create_test_users(test_app)
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Test valid time formats
        valid_time_data = {
            'time_start': '19:00',
            'time_end': '21:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps(valid_time_data),
                            content_type='application/json')
        assert response.status_code == 200
        
        # Test invalid time format
        invalid_time_data = {
            'time_start': 'invalid-time',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps(invalid_time_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_time_logic_validation(self, client, test_app):
        """Test time logic validation (end after start)."""
        user_ids = self.create_test_users(test_app)
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Test invalid time logic (end before start)
        invalid_logic_data = {
            'time_start': '21:00',
            'time_end': '19:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail_id}',
                            data=json.dumps(invalid_logic_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'after' in data['error'].lower()

    # ========== Error Handling Tests ==========
    
    def test_nonexistent_availability_handling(self, client, test_app):
        """Test handling of nonexistent availability entries."""
        self.create_test_users(test_app)
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Try to edit nonexistent availability
        response = client.put('/api/availability/99999',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
        
        # Try to delete nonexistent availability
        response = client.delete('/api/availability/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_unauthenticated_access_denied(self, client, test_app):
        """Test that unauthenticated users cannot edit/delete."""
        user_ids = self.create_test_users(test_app)
        avail_id = self.create_test_availability(test_app, user_ids['user1_id'])
        
        # Try to edit without authentication
        edit_response = client.put(f'/api/availability/{avail_id}',
                                 data=json.dumps({'status': 'tentative'}),
                                 content_type='application/json')
        
        assert edit_response.status_code in [401, 302]  # Unauthorized or redirect to login
        
        # Try to delete without authentication
        delete_response = client.delete(f'/api/availability/{avail_id}')
        
        assert delete_response.status_code in [401, 302]  # Unauthorized or redirect to login

    # ========== Integration Workflow Tests ==========
    
    def test_complete_edit_workflow(self, client, test_app):
        """Test complete edit workflow from creation to update."""
        user_ids = self.create_test_users(test_app)
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Step 1: Create availability
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_data = {
            'date': future_date,
            'status': 'available',
            'play_preference': 'either',
            'notes': 'Original notes',
            'is_all_day': True
        }
        
        create_response = client.post('/api/availability',
                                    data=json.dumps(create_data),
                                    content_type='application/json')
        
        assert create_response.status_code == 200
        created_avail = create_response.get_json()
        avail_id = created_avail['id']
        
        # Step 2: Edit the availability
        edit_data = {
            'status': 'tentative',
            'play_preference': 'book_court',
            'notes': 'Updated notes'
        }
        
        edit_response = client.put(f'/api/availability/{avail_id}',
                                 data=json.dumps(edit_data),
                                 content_type='application/json')
        
        assert edit_response.status_code == 200
        edited_avail = edit_response.get_json()['availability']
        
        # Verify changes
        assert edited_avail['status'] == 'tentative'
        assert edited_avail['play_preference'] == 'book_court'
        assert edited_avail['notes'] == 'Updated notes'
    
    def test_complete_delete_workflow(self, client, test_app):
        """Test complete delete workflow."""
        user_ids = self.create_test_users(test_app)
        
        # Login user
        self.login_user(client, 'user1_test', 'user123')
        
        # Step 1: Create availability
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_data = {
            'date': future_date,
            'status': 'available',
            'is_all_day': True
        }
        
        create_response = client.post('/api/availability',
                                    data=json.dumps(create_data),
                                    content_type='application/json')
        
        assert create_response.status_code == 200
        created_avail = create_response.get_json()
        avail_id = created_avail['id']
        
        # Step 2: Delete the availability
        delete_response = client.delete(f'/api/availability/{avail_id}')
        
        assert delete_response.status_code == 200
        delete_result = delete_response.get_json()
        assert 'message' in delete_result
        assert 'deleted' in delete_result['message'].lower()
        
        # Step 3: Verify deletion
        get_response = client.get('/api/availability')
        assert get_response.status_code == 200
        
        availabilities = get_response.get_json()
        deleted_avail = next((a for a in availabilities if a['id'] == avail_id), None)
        assert deleted_avail is None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])