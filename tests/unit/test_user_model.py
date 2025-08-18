"""
Unit tests for User model.
"""

import pytest
from app.models import User
from app import db


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation_valid(self, app_context):
        """Test valid user creation."""
        user = User(username="testuser", password="password123", role="User")
        assert user.username == "testuser"
        assert user.role == "User"
        assert user.is_active is True
    
    def test_password_hashing(self, app_context):
        """Test password hashing and verification."""
        user = User(username="testuser", password="password123")
        assert user.check_password("password123") is True
        assert user.check_password("wrongpassword") is False
    
    def test_admin_role_check(self, app_context):
        """Test admin role checking."""
        admin_user = User(username="admin", password="password123", role="Admin")
        regular_user = User(username="user", password="password123", role="User")
        
        assert admin_user.is_admin() is True
        assert regular_user.is_admin() is False
    
    def test_username_validation_length(self, app_context):
        """Test username length validation."""
        # Too short
        with pytest.raises(ValueError, match="Username must be between 3 and 20 characters"):
            User(username="ab", password="password123")
        
        # Too long
        with pytest.raises(ValueError, match="Username must be between 3 and 20 characters"):
            User(username="a" * 25, password="password123")
    
    def test_username_validation_format(self, app_context):
        """Test username format validation."""
        invalid_usernames = ["user@name", "user name", "user-name", "user.name"]
        
        for username in invalid_usernames:
            with pytest.raises(ValueError, match="Username can only contain letters, numbers, and underscores"):
                User(username=username, password="password123")
    
    def test_password_validation_length(self, app_context):
        """Test password length validation."""
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            User(username="testuser", password="123")
    
    def test_password_validation_strength(self, app_context):
        """Test password strength validation."""
        # No letters
        with pytest.raises(ValueError, match="Password must contain at least one letter and one number"):
            User(username="testuser", password="123456")
        
        # No numbers
        with pytest.raises(ValueError, match="Password must contain at least one letter and one number"):
            User(username="testuser", password="password")
    
    def test_role_validation(self, app_context):
        """Test role validation."""
        with pytest.raises(ValueError, match="Role must be either 'User' or 'Admin'"):
            User(username="testuser", password="password123", role="InvalidRole")
    
    def test_user_representation(self, app_context):
        """Test user string representation."""
        user = User(username="testuser", password="password123")
        assert str(user) == "testuser"
        assert repr(user) == "<User testuser>"