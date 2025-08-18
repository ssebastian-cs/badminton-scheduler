"""
Unit tests for form validation and security.
"""

import pytest
from datetime import date, time, timedelta
from app.forms import (
    LoginForm, RegistrationForm, AvailabilityForm, 
    AvailabilityFilterForm, CommentForm
)
from app.models import User
from app import db


def assert_error_in_field(field, expected_error):
    """Helper function to check if error message is in field errors (handles periods)."""
    return any(expected_error in error for error in field.errors)


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


class TestAvailabilityForm:
    """Test cases for AvailabilityForm."""
    
    def test_valid_availability_form(self, app_context):
        """Test valid availability form data."""
        future_date = date.today() + timedelta(days=1)
        form_data = {
            'date': future_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is True
    
    def test_availability_form_future_date_validation(self, app_context):
        """Test future date validation."""
        # Past date
        past_date = date.today() - timedelta(days=1)
        form_data = {
            'date': past_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date must be in the future' in form.date.errors
        
        # Today's date
        today = date.today()
        form_data['date'] = today
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date must be in the future' in form.date.errors
    
    def test_availability_form_date_range_validation(self, app_context):
        """Test date range validation (not too far in future)."""
        # More than one year in future
        far_future_date = date.today() + timedelta(days=366)
        form_data = {
            'date': far_future_date,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Date cannot be more than one year in the future' in form.date.errors
    
    def test_availability_form_time_validation(self, app_context):
        """Test time validation."""
        future_date = date.today() + timedelta(days=1)
        
        # End time before start time
        form_data = {
            'date': future_date,
            'start_time': time(12, 0),
            'end_time': time(10, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be after start time' in form.end_time.errors
        
        # Same start and end time
        form_data['end_time'] = time(12, 0)
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be after start time' in form.end_time.errors
    
    def test_availability_form_time_range_validation(self, app_context):
        """Test reasonable time range validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Start time too early
        form_data = {
            'date': future_date,
            'start_time': time(5, 0),
            'end_time': time(7, 0),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Start time must be between 6:00 AM and 11:00 PM' in form.start_time.errors
        
        # End time too late
        form_data = {
            'date': future_date,
            'start_time': time(22, 0),
            'end_time': time(23, 30),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'End time must be between 6:00 AM and 11:59 PM' in form.end_time.errors
    
    def test_availability_form_duration_validation(self, app_context):
        """Test duration validation."""
        future_date = date.today() + timedelta(days=1)
        
        # Duration too long (more than 8 hours)
        form_data = {
            'date': future_date,
            'start_time': time(8, 0),
            'end_time': time(17, 0),  # 9 hours
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Availability duration cannot exceed 8 hours' in form.end_time.errors
        
        # Duration too short (less than 30 minutes)
        form_data = {
            'date': future_date,
            'start_time': time(10, 0),
            'end_time': time(10, 15),  # 15 minutes
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityForm(data=form_data)
            assert form.validate() is False
            assert 'Availability duration must be at least 30 minutes' in form.end_time.errors


class TestAvailabilityFilterForm:
    """Test cases for AvailabilityFilterForm."""
    
    def test_valid_filter_form(self, app_context):
        """Test valid filter form data."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=7)
        
        form_data = {
            'start_date': start_date,
            'end_date': end_date,
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityFilterForm(data=form_data)
            assert form.validate() is True
    
    def test_filter_form_date_range_validation(self, app_context):
        """Test date range validation."""
        # End date before start date
        form_data = {
            'start_date': date.today() + timedelta(days=7),
            'end_date': date.today(),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityFilterForm(data=form_data)
            assert form.validate() is False
            assert 'End date must be after start date' in form.end_date.errors
    
    def test_filter_form_date_limits(self, app_context):
        """Test date limits validation."""
        # Start date too far in past
        form_data = {
            'start_date': date.today() - timedelta(days=366),
            'end_date': date.today(),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityFilterForm(data=form_data)
            assert form.validate() is False
            assert 'Start date cannot be more than one year in the past' in form.start_date.errors
        
        # End date too far in future
        form_data = {
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=366),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityFilterForm(data=form_data)
            assert form.validate() is False
            assert 'End date cannot be more than one year in the future' in form.end_date.errors
    
    def test_filter_form_range_limit(self, app_context):
        """Test maximum date range validation."""
        # Range more than 90 days
        form_data = {
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=91),
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = AvailabilityFilterForm(data=form_data)
            assert form.validate() is False
            assert 'Date range cannot exceed 90 days' in form.end_date.errors


class TestCommentForm:
    """Test cases for CommentForm."""
    
    def test_valid_comment_form(self, app_context):
        """Test valid comment form data."""
        form_data = {
            'content': 'This is a valid comment',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is True
    
    def test_comment_form_empty_content(self, app_context):
        """Test empty content validation."""
        form_data = {
            'content': '',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is False
            assert 'Comment content is required' in form.content.errors
        
        # Whitespace-only content
        form_data['content'] = '   '
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is False
            assert 'Comment content cannot be empty' in form.content.errors
    
    def test_comment_form_length_validation(self, app_context):
        """Test content length validation."""
        # Content too long
        form_data = {
            'content': 'a' * 1001,
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is False
            assert 'Comment must be between 1 and 1000 characters' in form.content.errors
    
    def test_comment_form_security_validation(self, app_context):
        """Test security validation for malicious content."""
        malicious_contents = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            '<img src=x onerror=alert(1)>',
            'onclick=alert(1)',
            'onload=alert(1)'
        ]
        
        for malicious_content in malicious_contents:
            form_data = {
                'content': malicious_content,
                'csrf_token': 'test_token'
            }
            
            with app_context.test_request_context(data=form_data):
                form = CommentForm(data=form_data)
                assert form.validate() is False
                assert 'Comment contains invalid content' in form.content.errors
    
    def test_comment_form_spam_detection(self, app_context):
        """Test spam detection validation."""
        # Too many special characters
        form_data = {
            'content': '!@#$%^&*()_+{}|:"<>?[]\\;\',./',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is False
            assert 'Comment contains too many special characters' in form.content.errors
        
        # Repeated characters
        form_data['content'] = 'aaaaaaaaaaaaa'  # 13 repeated 'a's
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is False
            assert 'Comment contains invalid repeated characters' in form.content.errors
    
    def test_comment_form_content_sanitization(self, app_context):
        """Test content sanitization."""
        form_data = {
            'content': '  This is a comment with whitespace  ',
            'csrf_token': 'test_token'
        }
        
        with app_context.test_request_context(data=form_data):
            form = CommentForm(data=form_data)
            assert form.validate() is True
            # Content should be trimmed
            assert form.content.data == 'This is a comment with whitespace'