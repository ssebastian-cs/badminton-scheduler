import pytest
import tempfile
import os
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        admin = User('admin', 'password123', 'Admin')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def regular_user(app):
    """Create a regular user for testing."""
    with app.app_context():
        user = User('testuser', 'password123', 'User')
        db.session.add(user)
        db.session.commit()
        return user


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign in to your account' in response.data
    
    def test_login_with_valid_credentials(self, client, regular_user):
        """Test login with valid credentials."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back, testuser!' in response.data
    
    def test_login_with_invalid_credentials(self, client, regular_user):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_with_blocked_user(self, client, app):
        """Test login with blocked user."""
        with app.app_context():
            blocked_user = User('blocked', 'password123', 'User')
            blocked_user.is_active = False
            db.session.add(blocked_user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'blocked',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Your account has been blocked' in response.data
    
    def test_logout(self, client, regular_user):
        """Test logout functionality."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'You have been logged out successfully' in response.data
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_admin_registration_requires_admin(self, client, regular_user):
        """Test that user registration requires admin privileges."""
        # Login as regular user
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        response = client.get('/auth/register')
        assert response.status_code == 302  # Should redirect due to lack of admin privileges
    
    def test_admin_can_access_registration(self, client, admin_user):
        """Test that admin can access registration page."""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create New User' in response.data
    
    def test_admin_can_create_user(self, client, admin_user):
        """Test that admin can create new users."""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'password123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'User newuser created successfully' in response.data
    
    def test_duplicate_username_validation(self, client, admin_user, regular_user):
        """Test that duplicate usernames are rejected."""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        response = client.post('/auth/register', data={
            'username': 'testuser',  # This user already exists
            'password': 'password123',
            'role': 'User'
        })
        assert response.status_code == 200
        assert b'Username already exists' in response.data


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_role_detection(self, app, admin_user):
        """Test admin role detection."""
        with app.app_context():
            user = User.query.filter_by(username='admin').first()
            assert user.is_admin() is True
    
    def test_user_role_detection(self, app, regular_user):
        """Test regular user role detection."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user.is_admin() is False
    
    def test_admin_dashboard_access(self, client, admin_user):
        """Test admin dashboard access."""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_regular_user_cannot_access_admin(self, client, regular_user):
        """Test that regular users cannot access admin areas."""
        # Login as regular user
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        response = client.get('/admin/')
        assert response.status_code == 302  # Should redirect due to lack of admin privileges


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User('testuser', 'password123', 'User')
            assert user.password_hash != 'password123'
            assert user.check_password('password123') is True
            assert user.check_password('wrongpassword') is False
    
    def test_password_validation(self, app):
        """Test password validation."""
        with app.app_context():
            with pytest.raises(ValueError):
                User('testuser', 'short', 'User')  # Too short password
            
            with pytest.raises(ValueError):
                User('testuser', '', 'User')  # Empty password


if __name__ == '__main__':
    pytest.main([__file__, '-v'])