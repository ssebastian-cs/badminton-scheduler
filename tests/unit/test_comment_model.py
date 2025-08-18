"""
Unit tests for Comment model.
"""

import pytest
from app.models import Comment
from app import db


class TestCommentModel:
    """Test cases for Comment model."""
    
    def test_comment_creation_valid(self, app_context, test_user):
        """Test valid comment creation."""
        comment = Comment(user_id=test_user.id, content="This is a test comment")
        
        assert comment.user_id == test_user.id
        assert comment.content == "This is a test comment"
        assert comment.created_at is not None
    
    def test_comment_content_validation_empty(self, app_context, test_user):
        """Test empty content validation."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            Comment(user_id=test_user.id, content="")
        
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            Comment(user_id=test_user.id, content="   ")
    
    def test_comment_content_validation_length(self, app_context, test_user):
        """Test content length validation."""
        # Content too long
        with pytest.raises(ValueError, match="Comment must be between 1 and 1000 characters"):
            Comment(user_id=test_user.id, content="x" * 1001)
    
    def test_comment_content_validation_security(self, app_context, test_user):
        """Test content security validation."""
        malicious_contents = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            '<img src=x onerror=alert(1)>',
            'onclick=alert(1)',
            'onload=alert(1)'
        ]
        
        for malicious_content in malicious_contents:
            with pytest.raises(ValueError, match="Comment contains invalid content"):
                Comment(user_id=test_user.id, content=malicious_content)
    
    def test_comment_content_validation_spam(self, app_context, test_user):
        """Test spam detection validation."""
        # Too many special characters
        with pytest.raises(ValueError, match="Comment contains too many special characters"):
            Comment(user_id=test_user.id, content="!@#$%^&*()_+{}|:\"<>?[]\\;',./" * 2)
        
        # Repeated characters
        with pytest.raises(ValueError, match="Comment contains invalid repeated characters"):
            Comment(user_id=test_user.id, content="aaaaaaaaaaaaa")  # 13 repeated 'a's
    
    def test_comment_update_content(self, app_context, test_user):
        """Test comment content update."""
        comment = Comment(user_id=test_user.id, content="Original content")
        comment.update_content("Updated content")
        
        assert comment.content == "Updated content"
    
    def test_comment_content_sanitization(self, app_context, test_user):
        """Test content sanitization."""
        comment = Comment(user_id=test_user.id, content="  Content with whitespace  ")
        assert comment.content == "Content with whitespace"
    
    def test_comment_representation(self, app_context, test_user):
        """Test comment string representation."""
        comment = Comment(user_id=test_user.id, content="Test comment")
        expected_str = f"Comment by {test_user.username}: Test comment"
        assert str(comment) == expected_str