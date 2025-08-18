"""
Unit tests for LoginForm.
"""

import pytest
from app.forms import LoginForm


class TestLoginForm:
    """Test cases for LoginForm."""
    
    def test_valid_login_form(self, app_context):
        """Test valid login form data."""
        form_data = {
            'username': 'testuser',
            'password': 'password123',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = LoginForm(data=form_data)
            assert form.validate() is True
    
    def test_login_form_missing_username(self, app_context):
        """Test login form with missing username."""
        form_data = {
            'password': 'password123',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = LoginForm(data=form_data)
            assert form.validate() is False
            assert 'Username is required' in form.username.errors
    
    def test_login_form_missing_password(self, app_context):
        """Test login form with missing password."""
        form_data = {
            'username': 'testuser',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = LoginForm(data=form_data)
            assert form.validate() is False
            assert 'Password is required' in form.password.errors
    
    def test_login_form_username_length_validation(self, app_context):
        """Test username length validation."""
        # Too short
        form_data = {
            'username': 'ab',
            'password': 'password123',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = LoginForm(data=form_data)
            assert form.validate() is False
            assert 'Username must be between 3 and 20 characters' in form.username.errors
        
        # Too long
        form_data['username'] = 'a' * 21
        with app_context.test_request_context(data=form_data):
            form = LoginForm(data=form_data)
            assert form.validate() is False
            assert 'Username must be between 3 and 20 characters' in form.username.errors
    
    def test_login_form_username_format_validation(self, app_context):
        """Test username format validation."""
        invalid_usernames = ['user@name', 'user name', 'user-name', 'user.name']
        
        for username in invalid_usernames:
            form_data = {
                'username': username,
                'password': 'password123',
                'csrf_token': 'test_token'
            }
            
            with app_context.test_request_context(data=form_data):
                form = LoginForm(data=form_data)
                assert form.validate() is False
                assert 'Username can only contain letters, numbers, and underscores' in form.username.errors
    
    def test_login_form_security_validation(self, app_context):
        """Test security validation for malicious input."""
        malicious_inputs = [
            '<script>alert("xss")</script>',
            'user\'; DROP TABLE users; --',
            'user<img src=x onerror=alert(1)>',
            'user&lt;script&gt;'
        ]
        
        for malicious_input in malicious_inputs:
            form_data = {
                'username': malicious_input,
                'password': 'password123',
                'csrf_token': 'test_token'
            }
            
            with app_context.test_request_context(data=form_data):
                form = LoginForm(data=form_data)
                assert form.validate() is False