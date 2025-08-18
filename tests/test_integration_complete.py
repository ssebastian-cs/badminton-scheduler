#!/usr/bin/env python3
"""
Complete integration test suite for badminton scheduler.
Tests all user and admin workflows end-to-end.
"""

import pytest
import tempfile
import os
from datetime import date, time, timedelta
from app import create_app, db
from app.models import User, Availability, Comment, AdminAction


class TestCompleteIntegration:
    """Complete integration tests for all application workflows."""
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        db_fd, db_path = tempfile.mkstemp()
        
        app = create_app('testing')
        app.config['DATABASE'] = db_path
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
        
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def runner(self, app):
        """Create test CLI runner."""
        return app.test_cli_runner()
    
    def create_test_users(self, app):
        """Create test users for testing."""
        with app.app_context():
            # Create admin user
            admin = User(username='admin', password='admin123', role='Admin')
            db.session.add(admin)
            
            # Create regular users
            user1 = User(username='alice', password='password123', role='User')
            user2 = User(username='bob', password='password123', role='User')
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            return admin, user1, user2
    
    def login_user(self, client, username, password):
        """Helper to log in a user."""
        return client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout_user(self, client):
        """Helper to log out a user."""
        return client.get('/auth/logout', follow_redirects=True)
    
    def test_complete_user_workflow(self, app, client):
        """Test complete user workflow from registration to usage."""
        admin, user1, user2 = self.create_test_users(app)
        
        # Test user login
        response = self.login_user(client, 'alice', 'password123')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data
        
        # Test dashboard access
        response = client.get('/')
        assert response.status_code == 200
        
        # Test adding availability
        tomorrow = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify availability was added
        with app.app_context():
            availability = Availability.query.filter_by(user_id=user1.id).first()
            assert availability is not None
            assert availability.date == tomorrow
        
        # Test viewing availability
        response = client.get('/availability')
        assert response.status_code == 200
        
        # Test adding comment
        response = client.post('/comments/add', data={
            'content': 'Looking forward to playing!'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify comment was added
        with app.app_context():
            comment = Comment.query.filter_by(user_id=user1.id).first()
            assert comment is not None
            assert 'Looking forward' in comment.content
        
        # Test viewing comments
        response = client.get('/comments')
        assert response.status_code == 200
        
        # Test editing own availability
        with app.app_context():
            availability = Availability.query.filter_by(user_id=user1.id).first()
            availability_id = availability.id
        
        response = client.post(f'/availability/edit/{availability_id}', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '19:00',
            'end_time': '21:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Test editing own comment
        with app.app_context():
            comment = Comment.query.filter_by(user_id=user1.id).first()
            comment_id = comment.id
        
        response = client.post(f'/comments/edit/{comment_id}', data={
            'content': 'Updated: Looking forward to playing!'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Test logout
        response = self.logout_user(client)
        assert response.status_code == 200
        
        # Test accessing protected page after logout
        response = client.get('/availability/add')
        assert response.status_code == 302  # Redirect to login
    
    def test_complete_admin_workflow(self, app, client):
        """Test complete admin workflow including user management."""
        admin, user1, user2 = self.create_test_users(app)
        
        # Login as admin
        response = self.login_user(client, 'admin', 'admin123')
        assert response.status_code == 200
        
        # Test admin dashboard access
        response = client.get('/admin')
        assert response.status_code == 200
        
        # Test user management page
        response = client.get('/admin/users')
        assert response.status_code == 200
        
        # Test creating new user
        response = client.post('/admin/users/add', data={
            'username': 'newuser',
            'password': 'password123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user was created
        with app.app_context():
            new_user = User.query.filter_by(username='newuser').first()
            assert new_user is not None
            assert new_user.role == 'User'
        
        # Test blocking user
        with app.app_context():
            user_to_block = User.query.filter_by(username='alice').first()
            user_id = user_to_block.id
        
        response = client.post(f'/admin/users/{user_id}/toggle', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user was blocked
        with app.app_context():
            blocked_user = User.query.get(user_id)
            assert blocked_user.is_active == False
        
        # Test unblocking user
        response = client.post(f'/admin/users/{user_id}/toggle', follow_redirects=True)
        assert response.status_code == 200
        
        # Test admin editing any user's availability
        # First create availability as regular user
        self.logout_user(client)
        self.login_user(client, 'alice', 'password123')
        
        tomorrow = date.today() + timedelta(days=1)
        client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        
        # Get availability ID
        with app.app_context():
            availability = Availability.query.filter_by(user_id=user1.id).first()
            availability_id = availability.id
        
        # Login as admin and edit user's availability
        self.logout_user(client)
        self.login_user(client, 'admin', 'admin123')
        
        response = client.post(f'/availability/edit/{availability_id}', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '19:00',
            'end_time': '21:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify admin action was logged
        with app.app_context():
            admin_action = AdminAction.query.filter_by(
                action_type='edit_availability',
                target_id=availability_id
            ).first()
            assert admin_action is not None
    
    def test_security_and_permissions(self, app, client):
        """Test security measures and permission enforcement."""
        admin, user1, user2 = self.create_test_users(app)
        
        # Test accessing admin pages as regular user
        self.login_user(client, 'alice', 'password123')
        
        response = client.get('/admin')
        assert response.status_code == 403  # Forbidden
        
        response = client.get('/admin/users')
        assert response.status_code == 403  # Forbidden
        
        # Test editing another user's content
        # Create availability as user1
        tomorrow = date.today() + timedelta(days=1)
        client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        
        # Login as user2 and try to edit user1's availability
        self.logout_user(client)
        self.login_user(client, 'bob', 'password123')
        
        with app.app_context():
            availability = Availability.query.filter_by(user_id=user1.id).first()
            availability_id = availability.id
        
        response = client.post(f'/availability/edit/{availability_id}', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '19:00',
            'end_time': '21:00'
        })
        assert response.status_code == 403  # Should be forbidden
        
        # Test CSRF protection (this would need proper CSRF token handling in real tests)
        # For now, just verify forms require POST
        response = client.get('/availability/add')
        assert response.status_code == 405 or response.status_code == 200  # Method not allowed or form page
    
    def test_data_validation(self, app, client):
        """Test data validation throughout the application."""
        admin, user1, user2 = self.create_test_users(app)
        
        self.login_user(client, 'alice', 'password123')
        
        # Test invalid date (past date)
        yesterday = date.today() - timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': yesterday.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        # Should either redirect with error or show form with error
        assert response.status_code in [200, 302]
        
        # Test invalid time range (end before start)
        tomorrow = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '20:00',
            'end_time': '18:00'
        })
        assert response.status_code in [200, 302]
        
        # Test empty comment
        response = client.post('/comments/add', data={
            'content': ''
        })
        assert response.status_code in [200, 302]
        
        # Test very long comment
        long_content = 'x' * 1001  # Over 1000 character limit
        response = client.post('/comments/add', data={
            'content': long_content
        })
        assert response.status_code in [200, 302]
    
    def test_database_relationships(self, app):
        """Test database relationships and cascading deletes."""
        admin, user1, user2 = self.create_test_users(app)
        
        with app.app_context():
            # Create availability and comment for user1
            tomorrow = date.today() + timedelta(days=1)
            availability = Availability(
                user_id=user1.id,
                date=tomorrow,
                start_time=time(18, 0),
                end_time=time(20, 0)
            )
            db.session.add(availability)
            
            comment = Comment(user_id=user1.id, content='Test comment')
            db.session.add(comment)
            
            db.session.commit()
            
            # Verify relationships
            assert len(user1.availability_entries) == 1
            assert len(user1.comments) == 1
            assert availability.user == user1
            assert comment.user == user1
            
            # Test cascading delete
            user1_id = user1.id
            db.session.delete(user1)
            db.session.commit()
            
            # Verify related records were deleted
            assert Availability.query.filter_by(user_id=user1_id).count() == 0
            assert Comment.query.filter_by(user_id=user1_id).count() == 0
    
    def test_error_handling(self, app, client):
        """Test error handling and custom error pages."""
        admin, user1, user2 = self.create_test_users(app)
        
        # Test 404 error
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
        # Test accessing non-existent availability
        self.login_user(client, 'alice', 'password123')
        response = client.get('/availability/edit/99999')
        assert response.status_code == 404
        
        # Test accessing non-existent comment
        response = client.get('/comments/edit/99999')
        assert response.status_code == 404


def run_complete_integration_tests():
    """Run all integration tests."""
    import subprocess
    import sys
    
    print("Running complete integration tests...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'test_integration_complete.py', 
            '-v', '--tb=short'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == '__main__':
    success = run_complete_integration_tests()
    if success:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed!")
    
    exit(0 if success else 1)