#!/usr/bin/env python3
"""
Simple API endpoint tests for availability enhancements.
Tests the actual HTTP endpoints without complex imports.

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

class TestAPIEndpoints:
    """Test class for API endpoints."""
    
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
        """Create another regular user."""
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

    # ========== Basic Endpoint Tests ==========
    
    def test_put_availability_endpoint_exists(self, client, regular_user, test_app):
        """Test that PUT /api/availability/{id} endpoint exists."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test endpoint exists (should not return 405 Method Not Allowed)
        response = client.put(f'/api/availability/{avail.id}',
                            data=json.dumps({'status': 'tentative'}),
                            content_type='application/json')
        
        assert response.status_code != 405  # Method should be allowed
        assert response.status_code in [200, 400, 403, 404]
    
    def test_delete_availability_endpoint_exists(self, client, regular_user, test_app):
        """Test that DELETE /api/availability/{id} endpoint exists."""
        # Create test availability
        avail = self.create_test_availability(test_app, regular_user.id)
        
        # Login user
        self.login_user(client, 'user_test', 'user123')
        
        # Test endpoint exists (should not return 405 Method Not Allowed)
        response = client.delete(f'/api/availability/{avail.id}')
        
        assert response.status_code != 405  # Method should be allowed
        assert response.status_code in [200, 400, 403, 404]
    
    def test_admin_filtered_endpoint_exists(self, client, admin_user):
        """Test that GET /api/admin/availability/filtered endpoint exists."""
        # Login admin
        self.login_user(client, 'admin_test', 'admin123')
        
        # Test endpoint exists (should not return 405 Method Not Allowed)
        response = client.get('/api/admin/availability/filtered')
        
        assert response.status_code != 405  # Method should be allowed
        assert response.status_code in [200, 400, 403]

    # ========== User Ownership Tests ==========
    
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

    # ========== Past Date Protection Tests ==========
    
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
    
    def test_admin_filtering_basic_functionality(self, client, admin_user, regular_user, test_app):
        """Test basic admin filtering functionality (Requirement 3.8)."""
        # Create test data
        self.create_test_availability(test_app, regular_user.id, date_offset=1)
        self.create_test_availability(test_app, admin_user.id, date_offset=2)
        
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
    
    def test_admin_filtering_date_range(self, client, admin_user, regular_user, test_app):
        """Test admin filtering with date ranges (Requirement 3.8)."""
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
            avail_tomorrow = Availability(
                user_id=regular_user.id,
                date=tomorrow,
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

    # ========== Error Handling Tests ==========
    
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

    # ========== Integration Workflow Tests ==========
    
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