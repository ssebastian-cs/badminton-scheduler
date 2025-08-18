#!/usr/bin/env python3
"""
Comprehensive test suite for security validation and form protection.
Tests all security measures implemented in task 10.
"""

import pytest
import sys
import os
from datetime import date, time, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import User, Availability, Comment
from app.forms import LoginForm, RegistrationForm, AvailabilityForm, CommentForm
from app.security import SecurityValidator, sanitize_form_data, RateLimiter
from flask import Flask
from werkzeug.test import Client


class TestSecurityValidation:
    """Test security validation functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create tables
        db.create_all()
        
        # Create test user
        self.test_user = User(username='testuser', password='testpass123', role='User')
        db.session.add(self.test_user)
        db.session.commit()
    
    def teardown_method(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_csrf_protection_enabled(self):
        """Test that CSRF protection is enabled."""
        with self.app.test_request_context():
            # Check that CSRF is configured
            assert self.app.config.get('WTF_CSRF_ENABLED', True) is True
            assert 'csrf' in self.app.extensions
    
    def test_session_security_configuration(self):
        """Test that session security is properly configured."""
        config = self.app.config
        
        # Check session security settings
        assert config.get('SESSION_COOKIE_HTTPONLY') is True
        assert config.get('SESSION_COOKIE_SAMESITE') == 'Lax'
        assert config.get('SESSION_COOKIE_NAME') == 'badminton_session'
        assert config.get('PERMANENT_SESSION_LIFETIME') is not None
    
    def test_security_validator_username(self):
        """Test username validation."""
        # Valid usernames
        valid, msg = SecurityValidator.validate_username('testuser')
        assert valid is True
        assert msg is None
        
        valid, msg = SecurityValidator.validate_username('user_123')
        assert valid is True
        
        # Invalid usernames
        valid, msg = SecurityValidator.validate_username('')
        assert valid is False
        assert 'required' in msg.lower()
        
        valid, msg = SecurityValidator.validate_username('ab')
        assert valid is False
        assert 'between 3 and 20' in msg
        
        valid, msg = SecurityValidator.validate_username('user@domain')
        assert valid is False
        assert 'letters, numbers, and underscores' in msg
        
        valid, msg = SecurityValidator.validate_username('user<script>')
        assert valid is False
        assert 'invalid content' in msg.lower()
    
    def test_security_validator_password(self):
        """Test password validation."""
        # Valid passwords
        valid, msg = SecurityValidator.validate_password_strength('password123')
        assert valid is True
        assert msg is None
        
        # Invalid passwords
        valid, msg = SecurityValidator.validate_password_strength('')
        assert valid is False
        assert 'required' in msg.lower()
        
        valid, msg = SecurityValidator.validate_password_strength('short')
        assert valid is False
        assert 'at least 6 characters' in msg
        
        valid, msg = SecurityValidator.validate_password_strength('password')
        assert valid is False
        assert 'letter and one number' in msg
        
        valid, msg = SecurityValidator.validate_password_strength('password\x00')
        assert valid is False
        assert 'invalid characters' in msg
    
    def test_injection_validation(self):
        """Test SQL injection and XSS validation."""
        # SQL injection patterns
        valid, msg = SecurityValidator.validate_against_injection("'; DROP TABLE users; --")
        assert valid is False
        assert 'malicious SQL' in msg
        
        valid, msg = SecurityValidator.validate_against_injection("UNION SELECT * FROM users")
        assert valid is False
        assert 'malicious SQL' in msg
        
        # XSS patterns
        valid, msg = SecurityValidator.validate_against_injection("<script>alert('xss')</script>")
        assert valid is False
        assert 'malicious script' in msg
        
        valid, msg = SecurityValidator.validate_against_injection("javascript:alert('xss')")
        assert valid is False
        assert 'malicious script' in msg
        
        # Path traversal
        valid, msg = SecurityValidator.validate_against_injection("../../../etc/passwd")
        assert valid is False
        assert 'malicious path' in msg
        
        # Valid input
        valid, msg = SecurityValidator.validate_against_injection("This is normal text")
        assert valid is True
        assert msg is None
    
    def test_input_sanitization(self):
        """Test input sanitization functions."""
        # HTML escaping
        sanitized = SecurityValidator.sanitize_string("<script>alert('xss')</script>")
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
        
        # Length limiting
        long_string = 'a' * 1000
        sanitized = SecurityValidator.sanitize_string(long_string, max_length=100)
        assert len(sanitized) == 100
        
        # Whitespace stripping
        sanitized = SecurityValidator.sanitize_string('  test  ')
        assert sanitized == 'test'
        
        # Control character removal
        sanitized = SecurityValidator.sanitize_string('test\x00\x01string')
        assert '\x00' not in sanitized
        assert '\x01' not in sanitized
    
    def test_rate_limiter(self):
        """Test rate limiting functionality."""
        limiter = RateLimiter()
        
        # Test normal usage
        for i in range(5):
            assert limiter.is_rate_limited('test_ip', max_requests=10, window_minutes=60) is False
        
        # Test rate limiting
        for i in range(15):
            limiter.is_rate_limited('test_ip2', max_requests=10, window_minutes=60)
        
        # Should be rate limited now
        assert limiter.is_rate_limited('test_ip2', max_requests=10, window_minutes=60) is True
        
        # Test blocking for excessive requests
        for i in range(25):
            limiter.is_rate_limited('test_ip3', max_requests=10, window_minutes=60)
        
        assert limiter.is_blocked('test_ip3') is True
    
    def test_form_validation_login(self):
        """Test login form validation."""
        with self.app.test_request_context():
            # Valid form
            form = LoginForm(data={'username': 'testuser', 'password': 'testpass123'})
            assert form.validate() is True
            
            # Invalid username format
            form = LoginForm(data={'username': 'test@user', 'password': 'testpass123'})
            assert form.validate() is False
            assert any('letters, numbers, and underscores' in str(error) for error in form.username.errors)
            
            # Empty fields
            form = LoginForm(data={'username': '', 'password': ''})
            assert form.validate() is False
            assert form.username.errors
            assert form.password.errors
    
    def test_form_validation_registration(self):
        """Test registration form validation."""
        with self.app.test_request_context():
            # Valid form
            form = RegistrationForm(data={
                'username': 'newuser',
                'password': 'newpass123',
                'role': 'User'
            })
            assert form.validate() is True
            
            # Duplicate username
            form = RegistrationForm(data={
                'username': 'testuser',  # Already exists
                'password': 'newpass123',
                'role': 'User'
            })
            assert form.validate() is False
            assert any('already exists' in str(error) for error in form.username.errors)
            
            # Weak password
            form = RegistrationForm(data={
                'username': 'newuser2',
                'password': 'weak',
                'role': 'User'
            })
            assert form.validate() is False
            assert any('letter and one number' in str(error) for error in form.password.errors)
    
    def test_form_validation_availability(self):
        """Test availability form validation."""
        with self.app.test_request_context():
            tomorrow = date.today() + timedelta(days=1)
            
            # Valid form
            form = AvailabilityForm(data={
                'date': tomorrow,
                'start_time': time(10, 0),
                'end_time': time(12, 0)
            })
            assert form.validate() is True
            
            # Past date
            form = AvailabilityForm(data={
                'date': date.today() - timedelta(days=1),
                'start_time': time(10, 0),
                'end_time': time(12, 0)
            })
            assert form.validate() is False
            assert any('future' in str(error) for error in form.date.errors)
            
            # End time before start time
            form = AvailabilityForm(data={
                'date': tomorrow,
                'start_time': time(12, 0),
                'end_time': time(10, 0)
            })
            assert form.validate() is False
            assert any('after start time' in str(error) for error in form.end_time.errors)
            
            # Unreasonable time range
            form = AvailabilityForm(data={
                'date': tomorrow,
                'start_time': time(2, 0),  # 2 AM
                'end_time': time(3, 0)
            })
            assert form.validate() is False
            assert any('between 6:00 AM and 11:00 PM' in str(error) for error in form.start_time.errors)
    
    def test_form_validation_comment(self):
        """Test comment form validation."""
        with self.app.test_request_context():
            # Valid form
            form = CommentForm(data={'content': 'This is a valid comment.'})
            assert form.validate() is True
            
            # Empty content
            form = CommentForm(data={'content': ''})
            assert form.validate() is False
            assert form.content.errors
            
            # Too long content
            long_content = 'a' * 1001
            form = CommentForm(data={'content': long_content})
            assert form.validate() is False
            assert any('1000 characters' in str(error) for error in form.content.errors)
            
            # Malicious content
            form = CommentForm(data={'content': '<script>alert("xss")</script>'})
            assert form.validate() is False
            assert any('invalid content' in str(error) for error in form.content.errors)
    
    def test_form_data_sanitization(self):
        """Test form data sanitization."""
        with self.app.test_request_context():
            # Normal data
            data = {'username': 'testuser', 'comment': 'Normal comment'}
            sanitized = sanitize_form_data(data)
            assert sanitized['username'] == 'testuser'
            assert sanitized['comment'] == 'Normal comment'
            
            # Data with HTML
            data = {'comment': '<b>Bold text</b>'}
            sanitized = sanitize_form_data(data)
            assert '<b>' not in sanitized['comment']
            assert '&lt;b&gt;' in sanitized['comment']
    
    def test_security_headers_configuration(self):
        """Test security headers in production mode."""
        # This would be tested in production mode
        # For now, just verify the configuration exists
        prod_app = create_app('production')
        with prod_app.app_context():
            # Check that Talisman is configured
            assert 'talisman' in prod_app.extensions
    
    def test_database_security_measures(self):
        """Test database security configuration."""
        # Check SQLAlchemy configuration
        config = self.app.config
        engine_options = config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
        
        assert 'pool_pre_ping' in engine_options
        assert 'pool_recycle' in engine_options
        assert 'connect_args' in engine_options
    
    def test_error_handling_security(self):
        """Test that error pages don't leak sensitive information."""
        # Test 404 error
        response = self.client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'error' not in response.data.lower() or b'not found' in response.data.lower()
        
        # Test that stack traces are not exposed
        assert b'Traceback' not in response.data
        assert b'File "' not in response.data


def run_security_tests():
    """Run all security tests."""
    print("Running comprehensive security validation tests...")
    
    # Create test instance
    test_instance = TestSecurityValidation()
    
    # List of test methods
    test_methods = [
        'test_csrf_protection_enabled',
        'test_session_security_configuration',
        'test_security_validator_username',
        'test_security_validator_password',
        'test_injection_validation',
        'test_input_sanitization',
        'test_rate_limiter',
        'test_form_validation_login',
        'test_form_validation_registration',
        'test_form_validation_availability',
        'test_form_validation_comment',
        'test_form_data_sanitization',
        'test_security_headers_configuration',
        'test_database_security_measures',
        'test_error_handling_security'
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"Running {test_method}...")
            test_instance.setup_method()
            getattr(test_instance, test_method)()
            test_instance.teardown_method()
            print(f"✓ {test_method} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {test_method} FAILED: {str(e)}")
            failed += 1
            try:
                test_instance.teardown_method()
            except:
                pass
    
    print(f"\nSecurity Test Results:")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All security tests passed! The application has comprehensive security measures in place.")
        return True
    else:
        print(f"\n⚠️  {failed} security tests failed. Please review the implementation.")
        return False


if __name__ == '__main__':
    success = run_security_tests()
    sys.exit(0 if success else 1)