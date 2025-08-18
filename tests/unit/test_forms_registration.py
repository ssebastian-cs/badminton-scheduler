"""
Unit tests for RegistrationForm.
"""

import pytest
from app.forms import RegistrationForm


class TestRegistrationForm:
    """Test cases for RegistrationForm."""
    
    def test_valid_registration_form(self, app_context, db_session):
        """Test valid registration form data."""
        form_data = {
            'username': 'newuser',
            'password': 'password123',
            'role': 'User',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is True
    
    def test_registration_form_username_uniqueness(self, app_context, db_session, test_user):
        """Test username uniqueness validation."""
        form_data = {
            'username': test_user.username,  # Existing username
            'password': 'password123',
            'role': 'User',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is False
            assert 'Username already exists' in form.username.errors[0]
    
    def test_registration_form_password_strength(self, app_context, db_session):
        """Test password strength validation."""
        # Too short
        form_data = {
            'username': 'testuser',
            'password': '12345',
            'role': 'User',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is False
            assert 'Password must be between 6 and 128 characters' in form.password.errors
        
        # No letters
        form_data['password'] = '123456'
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is False
            assert any('Password must contain at least one letter and one number' in error for error in form.password.errors)
        
        # No numbers
        form_data['password'] = 'password'
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is False
            assert 'Password must contain at least one letter and one number' in form.password.errors
    
    def test_registration_form_role_validation(self, app_context, db_session):
        """Test role validation."""
        # Valid roles
        for role in ['User', 'Admin']:
            form_data = {
                'username': f'testuser_{role.lower()}',
                'password': 'password123',
                'role': role,
                'csrf_token': 'test_token'
            }
            
            with app_context.test_request_context(data=form_data):
                form = RegistrationForm(data=form_data)
                assert form.validate() is True
        
        # Invalid role
        form_data = {
            'username': 'testuser',
            'password': 'password123',
            'role': 'InvalidRole',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = RegistrationForm(data=form_data)
            assert form.validate() is False