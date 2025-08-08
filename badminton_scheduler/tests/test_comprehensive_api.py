#!/usr/bin/env python3
"""
Comprehensive test suite for availability enhancements API endpoints.
Tests all new API endpoints, validation logic, edit/delete workflows, admin filtering,
and permission checking scenarios.

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

# Add the current directory to the path so we can import run
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User, Availability

class TestComprehensiveAPI:
    """Comprehensive test class for all availability enhancement features."""
    
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
            admin = User(username='admin_test', email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            return admin
    
    @pytest.fixture
    def regular_user(self, test_app):
        """Create regular user."""
        with test_app.app_context():
            user = User(username='user_test', email='user@test.com', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def another_user(self, test_app):
        """Create another regular user for ownership testing."""
        with test_app.app_context():
            user = User(username='user2_test', email='user2@test.com', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            return user
    
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
            return availability

    # ========== Unit Tests for New API Endpoints ==========
    
    def test_put_availability_endpoint_exists(self, client, regular_user, test_app):
        """Test that PUT /api/availability/{id} endpoint exists."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test endpoint exists
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code in [200, 400, 403, 404]  # Should not be 405 (Method Not Allowed)
    
    def test_delete_availability_endpoint_exists(self, client, regular_user, test_app):
        """Test that DELETE /api/availability/{id} endpoint exists."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test endpoint exists
        response = client.delete(f'/api/availability/{avail.id}')
        
        assert response.status_code in [200, 400, 403, 404]  # Should not be 405 (Method Not Allowed)
    
    def test_admin_filtered_endpoint_exists(self, client, admin_user):
        """Test that GET /api/admin/availability/filtered endpoint exists."""
        # Login admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test endpoint exists
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code in [200, 400, 403]  # Should not be 405 (Method Not Allowed)

    # ========== Validation Logic Tests ==========
    
    def test_time_format_validation(self, client, regular_user, test_app):
        """Test comprehensive time format validation."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test valid time formats
        valid_times = [
            {'time_start': '19:00', 'time_end': '21:00'},
            {'time_start': '7:00 PM', 'time_end': '9:00 PM'},
            {'time_start': '7PM', 'time_end': '9PM'},
            {'time_range': '7-9 PM'},
            {'time_range': '19:00-21:00'},
        ]
        
        for time_data in valid_times:
            time_data.update({'is_all_day': False})
            response = client.put(f'/api/availability/{avail.id}',
                                data=json.dumps(time_data),
                                content_type='application/json')
            assert response.status_code == 200, f"Valid time format failed: {time_data}"
        
        # Test invalid time formats
        invalid_times = [
            {'time_start': 'invalid-time', 'is_all_day': False},
            {'time_start': '25:00', 'is_all_day': False},
            {'time_start': '12:70', 'is_all_day': False},
            {'time_range': 'not-a-time-range', 'is_all_day': False},
            {'time_range': '25:00-26:00', 'is_all_day': False},
        ]
        
        for time_data in invalid_times:
            response = client.put(f'/api/availability/{avail.id}',
                                data=json.dumps(time_data),
                                content_type='application/json')
            assert response.status_code == 400, f"Invalid time format should fail: {time_data}"
            
            data = response.get_json()
            assert 'error' in data
    
    def test_time_logic_validation(self, client, regular_user, test_app):
        """Test time logic validation (end after start)."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test invalid time logic (end before start)
        invalid_logic_data = {
            'time_start': '21:00',
            'time_end': '19:00',
            'is_all_day': False
        }
        
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps(invalid_logic_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'after' in data['error'].lower()
    
    def test_status_validation(self, client, regular_user, test_app):
        """Test availability status validation."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test valid statuses
        valid_statuses = ['available', 'tentative', 'not_available']
        
        for status in valid_statuses:
            response = client.put(f'/api/availability/{avail.id}',
                                data=json.dumps({'status': status}),
                                content_type='application/json')
            assert response.status_code == 200, f"Valid status failed: {status}"
        
        # Test invalid status
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'status': 'invalid_status'}),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'invalid status' in data['error'].lower()
    
    def test_play_preference_validation(self, client, regular_user, test_app):
        """Test play preference validation."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test valid preferences
        valid_preferences = ['drop_in', 'book_court', 'either', None]
        
        for preference in valid_preferences:
            data = {'play_preference': preference} if preference else {}
            response = client.put(f'/api/availability/{avail.id}',
                                data=json.dumps(data),
                                content_type='application/json')
            assert response.status_code == 200, f"Valid preference failed: {preference}"
        
        # Test invalid preference
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'play_preference': 'invalid_preference'}),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    # ========== Edit/Delete Workflow Integration Tests ==========
    
    def test_complete_edit_workflow(self, client, regular_user, test_app):
        """Test complete edit workflow from creation to update."""
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
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
        created_avail = create_response.get_json()['availability']
        avail_id = created_avail['id']
        
        # Step 2: Edit the availability
        edit_data = {
            'status': 'tentative',
            'play_preference': 'book_court',
            'notes': 'Updated notes',
            'time_start': '19:00',
            'time_end': '21:00',
            'is_all_day': False
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
        assert edited_avail['is_all_day'] == False
        
        # Step 3: Verify changes persist
        get_response = client.get('/api/availability')
        assert get_response.status_code == 200
        
        availabilities = get_response.get_json()
        updated_avail = next((a for a in availabilities if a['id'] == avail_id), None)
        assert updated_avail is not None
        assert updated_avail['status'] == 'tentative'
    
    def test_complete_delete_workflow(self, client, regular_user, test_app):
        """Test complete delete workflow."""
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
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
        created_avail = create_response.get_json()['availability']
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

    # ========== Permission Checking Tests ==========
    
    def test_user_ownership_validation_edit(self, client, regular_user, another_user, test_app):
        """Test user ownership validation for edit operations (Requirement 2.6)."""
        # Create availability for user1
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login as user2
        self.login_user(client, 'user2_test', 'user123')
        
        # Try to edit user1's availability
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'unauthorized' in data['error'].lower() or 'own' in data['error'].lower()
    
    def test_user_ownership_validation_delete(self, client, regular_user, another_user, test_app):
        """Test user ownership validation for delete operations (Requirement 2.6)."""
        # Create availability for user1
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login as user2
        self.login_user(client, 'user2_test', 'user123')
        
        # Try to delete user1's availability
        response = client.delete(f'/api/availability/{avail.id}')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'unauthorized' in data['error'].lower() or 'own' in data['error'].lower()
    
    def test_admin_can_edit_any_availability(self, client, admin_user, regular_user, test_app):
        """Test that admin can edit any user's availability."""
        # Create availability for regular user
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Admin should be able to edit any availability
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'status': 'not_available', 'notes': 'Updated by admin'}),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['availability']['status'] == 'not_available'
        assert data['availability']['notes'] == 'Updated by admin'
    
    def test_admin_can_delete_any_availability(self, client, admin_user, regular_user, test_app):
        """Test that admin can delete any user's availability."""
        # Create availability for regular user
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Admin should be able to delete any availability
        response = client.delete(f'/api/availability/{avail.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'deleted' in data['message'].lower()
    
    def test_past_date_protection_edit(self, client, regular_user, test_app):
        """Test past date protection for edit operations (Requirement 2.7)."""
        # Create availability for past date
        past_avail = self.create_test_availability(test_app, regular_user.id, date_offset=-1)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Try to edit past availability
        response = client.put(f'/api/availability/{past_avail.id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'past' in data['error'].lower()
    
    def test_past_date_protection_delete(self, client, regular_user, test_app):
        """Test past date protection for delete operations (Requirement 2.7)."""
        # Create availability for past date
        past_avail = self.create_test_availability(test_app, regular_user.id, date_offset=-1)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Try to delete past availability
        response = client.delete(f'/api/availability/{past_avail.id}')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'past' in data['error'].lower()
    
    def test_unauthenticated_access_denied(self, client, regular_user, test_app):
        """Test that unauthenticated users cannot edit/delete."""
        # Create availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Try to edit without authentication
        edit_response = client.put(f'/api/availability/{avail.id}',
                                 data=json.dumps({'status': 'tentative'}),
                                 content_type='application/json')
        
        assert edit_response.status_code in [401, 302]  # Unauthorized or redirect to login
        
        # Try to delete without authentication
        delete_response = client.delete(f'/api/availability/{avail.id}')
        
        assert delete_response.status_code in [401, 302]  # Unauthorized or redirect to login

    # ========== Admin Filtering Tests ==========
    
    def test_admin_filtering_permission_required(self, client, regular_user):
        """Test that admin permission is required for filtering endpoint (Requirement 3.8)."""
        # Login as regular user
        self.login_user(client, 'user_test', 'user123')
        
        # Try to access admin filtering endpoint
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'admin' in data['error'].lower()
    
    def test_admin_filtering_date_ranges(self, client, admin_user, regular_user, test_app):
        """Test admin filtering with various date ranges (Requirement 3.8)."""
        # Create test data for different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Create availabilities for different dates
        with test_app.app_context():
            avail_yesterday = Availability(
                user_id=regular_user.id,
                date=yesterday,
                status='available',
                is_all_day=True
            )
            avail_today = Availability(
                user_id=regular_user.id,
                date=today,
                status='tentative',
                is_all_day=True
            )
            avail_tomorrow = Availability(
                user_id=regular_user.id,
                date=tomorrow,
                status='not_available',
                is_all_day=True
            )
            
            db.session.add_all([avail_yesterday, avail_today, avail_tomorrow])
            db.session.commit()
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test filtering with start_date only
        response = client.get(f'/api/admin/availability/filtered?start_date={today.isoformat()}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'availability' in data
        assert 'filters' in data
        assert data['filters']['start_date'] == today.isoformat()
        
        # All returned entries should be from today or later
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date >= today
        
        # Test filtering with end_date only
        response = client.get(f'/api/admin/availability/filtered?end_date={today.isoformat()}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['filters']['end_date'] == today.isoformat()
        
        # All returned entries should be from today or earlier
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert avail_date <= today
        
        # Test filtering with both dates
        response = client.get(f'/api/admin/availability/filtered?start_date={yesterday.isoformat()}&end_date={tomorrow.isoformat()}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['filters']['start_date'] == yesterday.isoformat()
        assert data['filters']['end_date'] == tomorrow.isoformat()
        
        # All returned entries should be within range
        for avail in data['availability']:
            avail_date = datetime.strptime(avail['date'], '%Y-%m-%d').date()
            assert yesterday <= avail_date <= tomorrow
    
    def test_admin_filtering_invalid_dates(self, client, admin_user):
        """Test admin filtering with invalid date formats."""
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test invalid start_date format
        response = client.get('/api/admin/availability/filtered?start_date=invalid-date')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'date' in data['error'].lower()
        
        # Test invalid end_date format
        response = client.get('/api/admin/availability/filtered?end_date=2025/08/01')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'date' in data['error'].lower()
    
    def test_admin_filtering_pagination(self, client, admin_user, regular_user, test_app):
        """Test admin filtering pagination functionality."""
        # Create multiple availability entries
        with test_app.app_context():
            for i in range(10):
                avail = Availability(
                    user_id=regular_user.id,
                    date=date.today() + timedelta(days=i),
                    status='available',
                    is_all_day=True
                )
                db.session.add(avail)
            db.session.commit()
        
        # Login as admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test pagination
        response = client.get('/api/admin/availability/filtered?per_page=5')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['per_page'] == 5
        assert len(data['availability']) <= 5
        assert 'total_count' in data['pagination']
        assert 'total_pages' in data['pagination']

    # ========== Error Handling Scenarios ==========
    
    def test_nonexistent_availability_edit(self, client, regular_user):
        """Test editing nonexistent availability entry."""
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Try to edit nonexistent availability
        response = client.put('/api/availability/99999',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_nonexistent_availability_delete(self, client, regular_user):
        """Test deleting nonexistent availability entry."""
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Try to delete nonexistent availability
        response = client.delete('/api/availability/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_invalid_json_data(self, client, regular_user, test_app):
        """Test handling of invalid JSON data."""
        # Create availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Send invalid JSON
        response = client.put(f'/api/availability/{avail.id}',
                            data='invalid json',
                            content_type='application/json')
        
        assert response.status_code == 400
    
    def test_empty_request_body(self, client, regular_user, test_app):
        """Test handling of empty request body."""
        # Create availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Send empty request
        response = client.put(f'/api/availability/{avail.id}',
                            data='',
                            content_type='application/json')
        
        assert response.status_code == 400

    # ========== Data Integrity Tests ==========
    
    def test_concurrent_edit_handling(self, client, regular_user, test_app):
        """Test handling of concurrent edits (basic data integrity)."""
        # Create availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Simulate concurrent edits by making multiple requests
        edit_data1 = {'status': 'tentative', 'notes': 'Edit 1'}
        edit_data2 = {'status': 'not_available', 'notes': 'Edit 2'}
        
        response1 = client.put(f'/api/availability/{avail.id}',
                             data=json.dumps(edit_data1),
                             content_type='application/json')
        
        response2 = client.put(f'/api/availability/{avail.id}',
                             data=json.dumps(edit_data2),
                             content_type='application/json')
        
        # Both should succeed (last one wins)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify final state
        get_response = client.get('/api/availability')
        availabilities = get_response.get_json()
        updated_avail = next((a for a in availabilities if a['id'] == avail.id), None)
        assert updated_avail['status'] == 'not_available'
        assert updated_avail['notes'] == 'Edit 2'
    
    def test_database_constraint_handling(self, client, regular_user, test_app):
        """Test handling of database constraints."""
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Create availability with specific time slot
        future_date = (date.today() + timedelta(days=7)).isoformat()
        create_data = {
            'date': future_date,
            'status': 'available',
            'time_start': '19:00',
            'time_end': '21:00',
            'is_all_day': False
        }
        
        # First creation should succeed
        response1 = client.post('/api/availability',
                              data=json.dumps(create_data),
                              content_type='application/json')
        assert response1.status_code == 200
        
        # Second creation with same time slot should either succeed (update) or fail gracefully
        response2 = client.post('/api/availability',
                              data=json.dumps(create_data),
                              content_type='application/json')
        assert response2.status_code in [200, 400, 409]  # Success, validation error, or conflict

if __name__ == '__main__':
    pytest.main([__file__, '-v'])