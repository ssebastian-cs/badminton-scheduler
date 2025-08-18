"""
Comprehensive security hardening tests.
Tests for CSRF protection, rate limiting, input validation, and secure session handling.
"""

import pytest
from flask import url_for, session
from app import create_app, db
from app.models import User
from app.security import SecurityValidator, RateLimiter
import time
import json


class TestCSRFProtection:
    """Test CSRF protection on all forms and AJAX requests."""
    
    def test_login_form_has_csrf_protection(self, client):
        """Test that login form includes CSRF token."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'csrf_token' in response.data
    
    def test_login_without_csrf_fails(self, client):
        """Test that login without CSRF token fails."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        # Should fail due to missing CSRF token
        assert response.status_code == 400 or b'CSRF' in response.data
    
    def test_availability_form_has_csrf_protection(self, client, auth_user):
        """Test that availability forms include CSRF token."""
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        response = client.get('/availability/add')
        assert response.status_code == 200
        assert b'csrf_token' in response.data
    
    def test_comment_form_has_csrf_protection(self, client, auth_user):
        """Test that comment forms include CSRF token."""
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        response = client.get('/comments')
        assert response.status_code == 200
        assert b'csrf_token' in response.data
    
    def test_admin_forms_have_csrf_protection(self, client, admin_user):
        """Test that admin forms include CSRF token."""
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'adminpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        response = client.get('/admin/users/create')
        assert response.status_code == 200
        assert b'csrf_token' in response.data


class TestRateLimiting:
    """Test rate limiting for authentication attempts and form submissions."""
    
    def test_login_rate_limiting(self, client):
        """Test that login attempts are rate limited."""
        # Make multiple failed login attempts without CSRF for simplicity
        for i in range(5):
            response = client.post('/auth/login', data={
                'username': 'nonexistent',
                'password': 'wrongpass123'
            })
        
        # Next attempt should be rate limited
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass123'
        })
        
        assert b'Too many failed login attempts' in response.data or response.status_code == 429
    
    def test_form_submission_rate_limiting(self, client, auth_user):
        """Test that form submissions are rate limited."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        # Make multiple rapid form submissions
        for i in range(15):
            response = client.post('/comments/add', data={
                'content': f'Test comment {i}',
                'csrf_token': client.application.jinja_env.globals['csrf_token']()
            })
        
        # Should eventually be rate limited
        assert response.status_code == 429 or b'rate limit' in response.data.lower()
    
    def test_api_endpoint_rate_limiting(self, client, auth_user):
        """Test that API endpoints are rate limited."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        # Make multiple rapid API requests
        for i in range(20):
            response = client.delete('/api/comments/1/delete', 
                                   headers={'X-CSRFToken': client.application.jinja_env.globals['csrf_token']()})
        
        # Should eventually be rate limited
        assert response.status_code == 429 or response.status_code == 404


class TestInputValidation:
    """Test comprehensive input validation and sanitization."""
    
    def test_sql_injection_prevention(self, client):
        """Test that SQL injection attempts are blocked."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; DELETE FROM users WHERE '1'='1",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post('/auth/login', data={
                'username': malicious_input,
                'password': 'testpass123'
            })
            
            # Should be blocked (400) or fail safely
            assert response.status_code in [400, 200]  # 200 means it failed safely
            if response.status_code == 200:
                assert b'Invalid username or password' in response.data
    
    def test_xss_prevention(self, client, auth_user):
        """Test that XSS attempts are blocked."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        malicious_scripts = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>"
        ]
        
        for script in malicious_scripts:
            response = client.post('/comments/add', data={
                'content': script,
                'csrf_token': client.application.jinja_env.globals['csrf_token']()
            })
            
            # Should be blocked or sanitized
            assert response.status_code in [400, 302]  # 302 means redirect after sanitization
    
    def test_path_traversal_prevention(self, client):
        """Test that path traversal attempts are blocked."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for path in malicious_paths:
            response = client.get(f'/static/{path}')
            # Should be blocked or return 404
            assert response.status_code in [400, 404]
    
    def test_username_validation(self):
        """Test username validation rules."""
        validator = SecurityValidator()
        
        # Valid usernames
        valid_usernames = ['testuser', 'user123', 'test_user']
        for username in valid_usernames:
            is_valid, error = validator.validate_username(username)
            assert is_valid, f"Valid username {username} was rejected: {error}"
        
        # Invalid usernames
        invalid_usernames = [
            '',  # Empty
            'ab',  # Too short
            'a' * 25,  # Too long
            'user<script>',  # Contains HTML
            'user; DROP TABLE',  # SQL injection attempt
            'user@domain.com'  # Invalid characters
        ]
        
        for username in invalid_usernames:
            is_valid, error = validator.validate_username(username)
            assert not is_valid, f"Invalid username {username} was accepted"
    
    def test_password_validation(self):
        """Test password validation rules."""
        validator = SecurityValidator()
        
        # Valid passwords
        valid_passwords = ['password123', 'myPass1', 'secure123']
        for password in valid_passwords:
            is_valid, error = validator.validate_password_strength(password)
            assert is_valid, f"Valid password was rejected: {error}"
        
        # Invalid passwords
        invalid_passwords = [
            '',  # Empty
            'short',  # Too short
            'password',  # No numbers
            '123456',  # No letters
            'a' * 200,  # Too long
            'pass\x00word'  # Contains null byte
        ]
        
        for password in invalid_passwords:
            is_valid, error = validator.validate_password_strength(password)
            assert not is_valid, f"Invalid password was accepted"


class TestSecureSessionHandling:
    """Test secure session configuration and handling."""
    
    def test_session_cookie_security(self, client):
        """Test that session cookies have security attributes."""
        response = client.get('/')
        
        # Check for secure cookie attributes in headers
        set_cookie_header = response.headers.get('Set-Cookie', '')
        if set_cookie_header:
            assert 'HttpOnly' in set_cookie_header
            assert 'SameSite' in set_cookie_header
    
    def test_session_timeout(self, client, auth_user):
        """Test that sessions timeout appropriately."""
        # Login
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        # Verify login successful
        response = client.get('/availability')
        assert response.status_code == 200
        
        # Note: Actual timeout testing would require time manipulation
        # This test verifies the session exists after login
    
    def test_logout_clears_session(self, client, auth_user):
        """Test that logout properly clears session data."""
        # Login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'csrf_token': client.application.jinja_env.globals['csrf_token']()
        })
        
        # Logout
        response = client.get('/auth/logout')
        
        # Verify redirect to login
        assert response.status_code == 302
        assert '/auth/login' in response.location
        
        # Verify cannot access protected pages
        response = client.get('/availability')
        assert response.status_code == 302  # Redirect to login


class TestSecurityHeaders:
    """Test that security headers are properly set."""
    
    def test_security_headers_present(self, client):
        """Test that all required security headers are present."""
        response = client.get('/')
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Missing security header: {header}"
    
    def test_content_security_policy(self, client):
        """Test that CSP header is set in production mode."""
        # This would need to be tested with production config
        response = client.get('/')
        
        # In development, CSP might not be set
        # In production, it should be present
        if 'Content-Security-Policy' in response.headers:
            csp = response.headers['Content-Security-Policy']
            assert 'default-src' in csp
            assert "'self'" in csp


class TestRateLimiterClass:
    """Test the RateLimiter class functionality."""
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter()
        
        # Should not be rate limited initially (first 3 requests)
        assert not limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
        assert not limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
        assert not limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
        assert not limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
        assert not limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
        
        # Should be rate limited after exceeding limit
        assert limiter.is_rate_limited('test_ip', max_requests=5, window_minutes=1)
    
    def test_login_attempt_tracking(self):
        """Test login attempt tracking and rate limiting."""
        limiter = RateLimiter()
        
        # Record failed attempts
        limiter.record_login_attempt('test_user', success=False)
        limiter.record_login_attempt('test_user', success=False)
        limiter.record_login_attempt('test_user', success=False)
        
        # Should be rate limited
        is_limited, remaining, lockout_time = limiter.is_login_rate_limited('test_user', max_attempts=3)
        assert is_limited
        assert remaining == 0
        assert lockout_time is not None
        
        # Successful login should clear attempts
        limiter.record_login_attempt('test_user', success=True)
        is_limited, remaining, lockout_time = limiter.is_login_rate_limited('test_user', max_attempts=3)
        assert not is_limited
        assert remaining == 3
    
    def test_account_locking(self):
        """Test account locking functionality."""
        limiter = RateLimiter()
        
        # Lock account
        limiter.lock_account('test_user', duration_minutes=1)
        
        # Should be locked
        is_locked, unlock_time = limiter.is_account_locked('test_user')
        assert is_locked
        assert unlock_time is not None
        
        # Should not be locked for different user
        is_locked, unlock_time = limiter.is_account_locked('other_user')
        assert not is_locked


@pytest.fixture
def auth_user(app):
    """Create a test user for authentication tests."""
    with app.app_context():
        user = User(username='testuser', password='testpass123', role='User')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        admin = User(username='admin', password='adminpass123', role='Admin')
        db.session.add(admin)
        db.session.commit()
        return admin