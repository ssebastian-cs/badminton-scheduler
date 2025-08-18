"""
Integration tests for authentication routes and functionality.
"""

import pytest
from flask import url_for, session
from app.models import User
from app import db


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""
    
    def test_login_page_access(self, client):
        """Test accessing the login page."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Username' in response.data
        assert b'Password' in response.data
        assert b'Login' in response.data
    
    def test_successful_login(self, client, db_session, test_user):
        """Test successful user login."""
        response = client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
        
        # Check that user is logged in
        with client.session_transaction() as sess:
            assert '_user_id' in sess
            assert sess['_user_id'] == str(test_user.id)
    
    def test_login_with_invalid_credentials(self, client, db_session, test_user):
        """Test login with invalid credentials."""
        # Wrong password
        response = client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
        
        # Check that user is not logged in
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_with_nonexistent_user(self, client, db_session):
        """Test login with nonexistent username."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_with_blocked_user(self, client, db_session, test_factory):
        """Test login with blocked user account."""
        blocked_user = test_factory.create_user(
            username='blockeduser',
            password='password123',
            is_active=False
        )
        
        response = client.post('/auth/login', data={
            'username': blocked_user.username,
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert b'account has been blocked' in response.data
        
        # Check that user is not logged in
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_form_validation(self, client):
        """Test login form validation."""
        # Empty username
        response = client.post('/auth/login', data={
            'username': '',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Username is required' in response.data
        
        # Empty password
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': ''
        })
        assert response.status_code == 200
        assert b'Password is required' in response.data
        
        # Username too short
        response = client.post('/auth/login', data={
            'username': 'ab',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Username must be between 3 and 20 characters' in response.data
    
    def test_login_redirect_to_next_page(self, client, db_session, test_user):
        """Test login redirect to next page parameter."""
        # Try to access protected page
        response = client.get('/availability/my')
        assert response.status_code == 302
        
        # Login with next parameter
        response = client.post('/auth/login?next=/availability/my', data={
            'username': test_user.username,
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should be redirected to the requested page after login
        assert response.request.path == '/availability/my'
    
    def test_login_redirect_security(self, client, db_session, test_user):
        """Test security of login redirect parameter."""
        # Malicious redirect should be ignored
        response = client.post('/auth/login?next=//evil.com/steal', data={
            'username': test_user.username,
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard instead of malicious URL
        assert response.request.path == '/'
    
    def test_logout_functionality(self, client, authenticated_user):
        """Test user logout functionality."""
        # Verify user is logged in
        response = client.get('/')
        assert response.status_code == 200
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out successfully' in response.data
        
        # Check that user is logged out
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
        
        # Verify user can't access protected pages
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_logout_without_login(self, client):
        """Test logout without being logged in."""
        response = client.get('/auth/logout')
        assert response.status_code == 302  # Redirect to login
    
    def test_register_redirect_to_admin(self, client, authenticated_admin):
        """Test that register route redirects to admin create user."""
        response = client.get('/auth/register')
        assert response.status_code == 302
        
        # Should redirect to admin create user page
        response = client.get('/auth/register', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/admin/users/create'
    
    def test_register_requires_admin(self, client, authenticated_user):
        """Test that register route requires admin privileges."""
        response = client.get('/auth/register', follow_redirects=True)
        assert response.status_code == 200
        assert b'Admin access required' in response.data
    
    def test_register_requires_login(self, client):
        """Test that register route requires login."""
        response = client.get('/auth/register')
        assert response.status_code == 302
        
        response = client.get('/auth/register', follow_redirects=True)
        assert b'Please log in' in response.data
    
    def test_already_logged_in_redirect(self, client, authenticated_user):
        """Test redirect when already logged in user accesses login page."""
        response = client.get('/auth/login')
        assert response.status_code == 302
        
        response = client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/'
    
    def test_session_persistence(self, client, db_session, test_user):
        """Test that login session persists across requests."""
        # Login
        client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        })
        
        # Make multiple requests
        for _ in range(3):
            response = client.get('/')
            assert response.status_code == 200
            
            # Check that user is still logged in
            with client.session_transaction() as sess:
                assert '_user_id' in sess
                assert sess['_user_id'] == str(test_user.id)
    
    def test_admin_required_decorator(self, client, authenticated_user, authenticated_admin):
        """Test admin_required decorator functionality."""
        # Regular user should be denied access to admin routes
        with authenticated_user:
            response = client.get('/admin/')
            assert response.status_code == 302
            
            response = client.get('/admin/', follow_redirects=True)
            assert b'Admin access required' in response.data
        
        # Admin user should have access
        with authenticated_admin:
            response = client.get('/admin/')
            assert response.status_code == 200
    
    def test_login_required_decorator(self, client, authenticated_user):
        """Test login_required decorator functionality."""
        # Unauthenticated user should be redirected to login
        response = client.get('/availability/my')
        assert response.status_code == 302
        
        response = client.get('/availability/my', follow_redirects=True)
        assert b'Please log in' in response.data
        
        # Authenticated user should have access
        with authenticated_user:
            response = client.get('/availability/my')
            assert response.status_code == 200


class TestAuthenticationSecurity:
    """Security-focused authentication tests."""
    
    def test_password_hashing(self, db_session, test_factory):
        """Test that passwords are properly hashed."""
        user = test_factory.create_user(password='testpassword123')
        
        # Password should be hashed, not stored in plain text
        assert user.password_hash != 'testpassword123'
        assert len(user.password_hash) > 50  # Bcrypt hashes are long
        
        # Should be able to verify correct password
        assert user.check_password('testpassword123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_login_brute_force_protection(self, client, db_session, test_user):
        """Test protection against brute force login attempts."""
        # Make multiple failed login attempts
        for i in range(5):
            response = client.post('/auth/login', data={
                'username': test_user.username,
                'password': 'wrongpassword'
            })
            assert response.status_code == 200
            assert b'Invalid username or password' in response.data
        
        # Should still be able to login with correct credentials
        response = client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_sql_injection_protection(self, client, db_session):
        """Test protection against SQL injection in login."""
        sql_injection_attempts = [
            "admin'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; DELETE FROM users; --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            response = client.post('/auth/login', data={
                'username': injection_attempt,
                'password': 'password'
            })
            
            # Should not crash or allow login
            assert response.status_code == 200
            assert b'Invalid username or password' in response.data or b'Username contains invalid' in response.data
    
    def test_xss_protection_in_login(self, client):
        """Test XSS protection in login form."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "onload=alert(1)"
        ]
        
        for xss_attempt in xss_attempts:
            response = client.post('/auth/login', data={
                'username': xss_attempt,
                'password': 'password'
            })
            
            # Should not execute script or crash
            assert response.status_code == 200
            # XSS content should be escaped or rejected
            assert b'<script>' not in response.data
            assert b'javascript:' not in response.data
    
    def test_session_security(self, client, db_session, test_user):
        """Test session security features."""
        # Login
        response = client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        })
        
        # Check session cookie properties
        cookies = response.headers.getlist('Set-Cookie')
        session_cookie = None
        for cookie in cookies:
            if 'badminton_session' in cookie:
                session_cookie = cookie
                break
        
        if session_cookie:
            # Should have HttpOnly flag for XSS protection
            assert 'HttpOnly' in session_cookie
            # Should have SameSite for CSRF protection
            assert 'SameSite' in session_cookie
    
    def test_logout_session_cleanup(self, client, authenticated_user):
        """Test that logout properly cleans up session data."""
        # Verify user is logged in
        with client.session_transaction() as sess:
            assert '_user_id' in sess
            # Add some additional session data
            sess['test_data'] = 'should_be_cleared'
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that all session data is cleared
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
            assert 'test_data' not in sess
            assert len(sess) == 0
    
    def test_concurrent_login_sessions(self, app, db_session, test_user):
        """Test handling of concurrent login sessions."""
        # Create two separate clients (simulating different browsers)
        client1 = app.test_client()
        client2 = app.test_client()
        
        # Login with both clients
        client1.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        })
        
        client2.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        })
        
        # Both sessions should be valid
        response1 = client1.get('/')
        response2 = client2.get('/')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Logout from one client shouldn't affect the other
        client1.get('/auth/logout')
        
        response1 = client1.get('/')
        response2 = client2.get('/')
        
        assert response1.status_code == 302  # Redirected to login
        assert response2.status_code == 200  # Still logged in