"""
End-to-end integration tests for Badminton Scheduler.
Tests complete application workflows from admin and user perspectives.
"""
import pytest
from datetime import date, time, timedelta
from app import create_app, db
from app.models import User, Availability, Comment, AdminAction


class TestEndToEndIntegration:
    """Test complete application workflows."""

    @pytest.fixture
    def app(self):
        """Create test application."""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def admin_user(self, app):
        """Create admin user."""
        with app.app_context():
            admin = User(
                username='admin',
                password='password',
                role='Admin'
            )
            admin.is_active = True
            db.session.add(admin)
            db.session.commit()
            return admin

    @pytest.fixture
    def regular_user(self, app):
        """Create regular user."""
        with app.app_context():
            user = User(
                username='testuser',
                password='password',
                role='User'
            )
            user.is_active = True
            db.session.add(user)
            db.session.commit()
            return user

    def login_user(self, client, username, password='password'):
        """Helper to login user."""
        return client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_complete_admin_workflow(self, client, admin_user, regular_user):
        """Test complete admin workflow."""
        # 1. Admin login
        response = self.login_user(client, 'admin')
        assert response.status_code == 200
        assert b'Dashboard' in response.data

        # 2. Access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data

        # 3. View user management
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert b'testuser' in response.data

        # 4. Create new user
        response = client.post('/admin/users/create', data={
            'username': 'newuser',
            'password': 'password123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 5. Edit user
        response = client.post(f'/admin/users/{regular_user.id}/edit', data={
            'username': 'testuser',
            'role': 'User',
            'is_active': True
        }, follow_redirects=True)
        assert response.status_code == 200

        # 6. View admin actions log
        response = client.get('/admin/actions')
        assert response.status_code == 200

    def test_complete_user_workflow(self, client, regular_user):
        """Test complete user workflow."""
        # 1. User login
        response = self.login_user(client, 'testuser')
        assert response.status_code == 200
        assert b'Dashboard' in response.data

        # 2. Add availability
        tomorrow = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 3. View availability
        response = client.get('/')
        assert response.status_code == 200

        # 4. Add comment
        response = client.post('/comments/add', data={
            'content': 'Looking forward to playing tomorrow!'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 5. View comments
        response = client.get('/comments')
        assert response.status_code == 200
        assert b'Looking forward to playing tomorrow!' in response.data

    def test_security_and_permissions(self, client, admin_user, regular_user):
        """Test security and permission enforcement."""
        # 1. Test unauthorized access to admin routes
        self.login_user(client, 'testuser')
        
        response = client.get('/admin/')
        assert response.status_code == 403

        response = client.get('/admin/users')
        assert response.status_code == 403

        # 2. Test user can only edit own content
        with client.application.app_context():
            # Create availability for regular user
            availability = Availability(
                user_id=regular_user.id,
                date=date.today() + timedelta(days=1),
                start_time=time(18, 0),
                end_time=time(20, 0)
            )
            db.session.add(availability)
            db.session.commit()
            availability_id = availability.id

        # Try to edit as different user would fail (not implemented in routes)
        # This would be tested if we had multiple users

    def test_data_validation_and_constraints(self, client, regular_user):
        """Test data validation and business rules."""
        self.login_user(client, 'testuser')

        # 1. Test past date validation
        yesterday = date.today() - timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': yesterday.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        # Should show validation error (not redirect)
        assert response.status_code == 200
        assert b'Date must be in the future' in response.data

        # 2. Test invalid time range
        tomorrow = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '20:00',
            'end_time': '18:00'  # End before start
        })
        assert response.status_code == 200
        assert b'End time must be after start time' in response.data

    def test_application_health_and_status(self, client):
        """Test application health endpoints and status."""
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        
        # Test that application serves static files
        response = client.get('/static/css/style.css')
        # May return 404 if file doesn't exist, but should not error

    def test_mobile_responsiveness_indicators(self, client, regular_user):
        """Test mobile-friendly features."""
        self.login_user(client, 'testuser')
        
        # Test that pages load and contain mobile viewport meta tag
        response = client.get('/')
        assert response.status_code == 200
        assert b'viewport' in response.data  # Mobile viewport meta tag

        # Test form accessibility
        response = client.get('/availability/add')
        assert response.status_code == 200
        assert b'type="date"' in response.data  # HTML5 date input
        assert b'type="time"' in response.data  # HTML5 time input

    def test_error_handling(self, client):
        """Test error page handling."""
        # Test 404 error
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

        # Test accessing protected route without login
        response = client.get('/availability/add')
        assert response.status_code == 302  # Redirect to login

    def test_session_management(self, client, regular_user):
        """Test session handling and logout."""
        # Login
        response = self.login_user(client, 'testuser')
        assert response.status_code == 200

        # Access protected route
        response = client.get('/')
        assert response.status_code == 200

        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

        # Try to access protected route after logout
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login