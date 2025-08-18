"""
Unit tests for CommentForm.
"""

import pytest
from app.forms import CommentForm


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