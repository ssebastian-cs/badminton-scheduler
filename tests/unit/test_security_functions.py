"""
Unit tests for security functions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.security import (
    SecurityValidator, RateLimiter, validate_request_security,
    sanitize_form_data, log_security_event, secure_filename
)


class TestSecurityValidator:
    """Test SecurityValidator class methods."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = SecurityValidator.sanitize_string("Hello World")
        assert result == "Hello World"
        
        result = SecurityValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"
        
        result = SecurityValidator.sanitize_string("")
        assert result == ""
        
        result = SecurityValidator.sanitize_string(None)
        assert result is None
    
    def test_sanitize_string_html_escaping(self):
        """Test HTML escaping."""
        result = SecurityValidator.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        
        result = SecurityValidator.sanitize_string("Test & <test> \"quote\"")
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result
    
    def test_sanitize_string_length_limit(self):
        """Test length limiting."""
        long_string = "a" * 100
        result = SecurityValidator.sanitize_string(long_string, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_string_control_characters(self):
        """Test control character removal."""
        input_string = "Hello\x00World\x01Test\x1f"
        result = SecurityValidator.sanitize_string(input_string)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x1f" not in result
        assert "HelloWorldTest" == result
        
        # Test allowed control characters
        input_string = "Hello\tWorld\nTest"  # Removed \r for this test
        result = SecurityValidator.sanitize_string(input_string)
        assert "\t" in result
        assert "\n" in result
    
    def test_sanitize_string_allow_html(self):
        """Test HTML sanitization with allowed tags."""
        input_string = "<b>Bold</b> <script>alert('xss')</script> <i>Italic</i>"
        result = SecurityValidator.sanitize_string(input_string, allow_html=True)
        
        # Allowed tags should remain
        assert "<b>Bold</b>" in result
        assert "<i>Italic</i>" in result
        
        # Dangerous content should be removed
        assert "<script>" not in result
        assert "alert" not in result
    
    def test_validate_against_injection_safe_input(self):
        """Test safe input validation."""
        is_valid, error = SecurityValidator.validate_against_injection("normal text")
        assert is_valid is True
        assert error is None
    
    def test_validate_against_injection_sql(self):
        """Test SQL injection detection."""
        sql_patterns = [
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM users",
            "1' OR '1'='1",
            "admin'; DELETE FROM users; --",
            "1; EXEC xp_cmdshell('dir')"
        ]
        
        for pattern in sql_patterns:
            is_valid, error = SecurityValidator.validate_against_injection(pattern, check_sql=True)
            assert is_valid is False
            assert "SQL content" in error
    
    def test_validate_against_injection_xss(self):
        """Test XSS pattern detection."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "onload=alert(1)",
            "<iframe src=javascript:alert(1)></iframe>"
        ]
        
        for pattern in xss_patterns:
            is_valid, error = SecurityValidator.validate_against_injection(pattern, check_xss=True)
            assert is_valid is False
            assert "script content" in error
    
    def test_validate_against_injection_path_traversal(self):
        """Test path traversal detection."""
        path_patterns = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f",
            "..%2f",
            "..%5c"
        ]
        
        for pattern in path_patterns:
            is_valid, error = SecurityValidator.validate_against_injection(pattern, check_path=True)
            assert is_valid is False
            assert "path content" in error
    
    def test_validate_against_injection_selective_checks(self):
        """Test selective validation."""
        sql_pattern = "'; DROP TABLE users; --"
        
        # Only SQL check enabled
        is_valid, error = SecurityValidator.validate_against_injection(
            sql_pattern, check_sql=True, check_xss=False, check_path=False
        )
        assert is_valid is False
        
        # SQL check disabled
        is_valid, error = SecurityValidator.validate_against_injection(
            sql_pattern, check_sql=False, check_xss=True, check_path=True
        )
        assert is_valid is True
    
    def test_validate_username(self):
        """Test username validation."""
        # Valid usernames
        valid_usernames = ["user123", "test_user", "User_123", "abc"]
        for username in valid_usernames:
            is_valid, error = SecurityValidator.validate_username(username)
            assert is_valid is True
            assert error is None
        
        # Invalid usernames
        is_valid, error = SecurityValidator.validate_username("")
        assert is_valid is False
        assert "required" in error
        
        is_valid, error = SecurityValidator.validate_username("ab")
        assert is_valid is False
        assert "between 3 and 20 characters" in error
        
        is_valid, error = SecurityValidator.validate_username("a" * 21)
        assert is_valid is False
        assert "between 3 and 20 characters" in error
        
        invalid_usernames = ["user@name", "user name", "user-name", "user.name"]
        for username in invalid_usernames:
            is_valid, error = SecurityValidator.validate_username(username)
            assert is_valid is False
            assert "letters, numbers, and underscores" in error
    
    def test_validate_password_strength(self):
        """Test password strength validation."""
        # Valid passwords
        valid_passwords = ["password123", "Test123", "myPass1", "secure123"]
        for password in valid_passwords:
            is_valid, error = SecurityValidator.validate_password_strength(password)
            assert is_valid is True
            assert error is None
        
        # Invalid passwords
        is_valid, error = SecurityValidator.validate_password_strength("")
        assert is_valid is False
        assert "required" in error
        
        is_valid, error = SecurityValidator.validate_password_strength("12345")
        assert is_valid is False
        assert "between 6 and 128 characters" in error
        
        is_valid, error = SecurityValidator.validate_password_strength("a" * 129)
        assert is_valid is False
        assert "between 6 and 128 characters" in error
        
        is_valid, error = SecurityValidator.validate_password_strength("123456")
        assert is_valid is False
        assert "at least one letter and one number" in error
        
        is_valid, error = SecurityValidator.validate_password_strength("password")
        assert is_valid is False
        assert "at least one letter and one number" in error
        
        is_valid, error = SecurityValidator.validate_password_strength("pass\x00word")
        assert is_valid is False
        assert "invalid characters" in error
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token1 = SecurityValidator.generate_csrf_token()
        token2 = SecurityValidator.generate_csrf_token()
        
        assert token1 != token2
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) > 20
        assert len(token2) > 20
    
    def test_hash_sensitive_data(self):
        """Test sensitive data hashing."""
        data1 = "sensitive_data_123"
        data2 = "different_data_456"
        
        hash1 = SecurityValidator.hash_sensitive_data(data1)
        hash2 = SecurityValidator.hash_sensitive_data(data2)
        
        assert hash1 != hash2
        
        hash1_repeat = SecurityValidator.hash_sensitive_data(data1)
        assert hash1 == hash1_repeat
        
        assert len(hash1) == 16
        assert len(hash2) == 16


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter()
        identifier = "test_user"
        
        # Should not be rate limited initially
        assert limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60) is False
        
        # Add requests up to limit
        for i in range(4):
            assert limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60) is False
        
        # Should be rate limited after exceeding limit
        assert limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60) is True
    
    def test_rate_limiter_window_expiry(self):
        """Test rate limiting window expiry."""
        limiter = RateLimiter()
        identifier = "test_user"
        
        # Fill up the rate limit
        for i in range(5):
            limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60)
        
        # Should be rate limited
        assert limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60) is True
        
        # Mock time to simulate window expiry
        with patch('app.security.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(minutes=61)
            mock_datetime.utcnow.return_value = future_time
            
            # Should not be rate limited after window expires
            assert limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60) is False
    
    def test_rate_limiter_different_identifiers(self):
        """Test rate limiting with different identifiers."""
        limiter = RateLimiter()
        
        # Fill up rate limit for first identifier
        for i in range(5):
            limiter.is_rate_limited("user1", max_requests=5, window_minutes=60)
        
        # First identifier should be rate limited
        assert limiter.is_rate_limited("user1", max_requests=5, window_minutes=60) is True
        
        # Second identifier should not be affected
        assert limiter.is_rate_limited("user2", max_requests=5, window_minutes=60) is False
    
    def test_rate_limiter_blocking(self):
        """Test IP blocking functionality."""
        limiter = RateLimiter()
        identifier = "test_ip"
        
        # Should not be blocked initially
        assert limiter.is_blocked(identifier) is False
        
        # Severely exceed rate limit to trigger blocking
        for i in range(10):  # 2x the limit of 5
            limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60)
        
        # Should be blocked now
        assert limiter.is_blocked(identifier) is True
    
    def test_rate_limiter_block_expiry(self):
        """Test IP block expiry."""
        limiter = RateLimiter()
        identifier = "test_ip"
        
        # Trigger blocking
        for i in range(10):
            limiter.is_rate_limited(identifier, max_requests=5, window_minutes=60)
        
        assert limiter.is_blocked(identifier) is True
        
        # Mock time to simulate block expiry
        with patch('app.security.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(hours=2)
            mock_datetime.utcnow.return_value = future_time
            
            # Should not be blocked after expiry
            assert limiter.is_blocked(identifier) is False


class TestSecurityFunctions:
    """Test security utility functions."""
    
    def test_sanitize_form_data_valid(self, app_context):
        """Test form data sanitization with valid data."""
        form_data = {
            'username': 'testuser',
            'password': 'password123',
            'comment': 'This is a comment'
        }
        
        with app_context.test_request_context():
            result = sanitize_form_data(form_data)
            
            assert result['username'] == 'testuser'
            assert result['password'] == 'password123'
            assert result['comment'] == 'This is a comment'
    
    def test_sanitize_form_data_with_safe_html(self, app_context):
        """Test form data sanitization with safe HTML content."""
        form_data = {
            'content': 'Normal text content'
        }
        
        with app_context.test_request_context():
            result = sanitize_form_data(form_data)
            assert result['content'] == 'Normal text content'
    
    def test_sanitize_form_data_malicious_content(self, app_context):
        """Test form data sanitization with malicious content."""
        form_data = {
            'username': "'; DROP TABLE users; --"
        }
        
        with app_context.test_request_context():
            with pytest.raises(Exception):  # Should abort with 400
                sanitize_form_data(form_data)
    
    def test_sanitize_form_data_non_string_values(self, app_context):
        """Test form data sanitization with non-string values."""
        form_data = {
            'username': 'testuser',
            'age': 25,
            'active': True,
            'tags': ['tag1', 'tag2']
        }
        
        with app_context.test_request_context():
            result = sanitize_form_data(form_data)
            
            assert result['username'] == 'testuser'
            assert result['age'] == 25
            assert result['active'] is True
            assert result['tags'] == ['tag1', 'tag2']
    
    def test_log_security_event(self, app_context):
        """Test security event logging."""
        with app_context.test_request_context():
            with patch('app.security.current_app') as mock_app:
                mock_logger = MagicMock()
                mock_app.logger = mock_logger
                
                log_security_event('TEST_EVENT', 'Test details', 'WARNING')
                
                mock_logger.warning.assert_called_once()
                
                log_call_args = mock_logger.warning.call_args[0][0]
                assert 'TEST_EVENT' in log_call_args
                assert 'Test details' in log_call_args
                assert 'WARNING' in log_call_args
    
    def test_log_security_event_different_severities(self, app_context):
        """Test security event logging with different severities."""
        with app_context.test_request_context():
            with patch('app.security.current_app') as mock_app:
                mock_logger = MagicMock()
                mock_app.logger = mock_logger
                
                log_security_event('EVENT1', 'Details', 'INFO')
                mock_logger.info.assert_called_once()
                
                log_security_event('EVENT2', 'Details', 'WARNING')
                mock_logger.warning.assert_called_once()
                
                log_security_event('EVENT3', 'Details', 'ERROR')
                mock_logger.error.assert_called_once()
                
                log_security_event('EVENT4', 'Details', 'CRITICAL')
                mock_logger.critical.assert_called_once()
    
    def test_secure_filename(self):
        """Test filename security function."""
        # Normal filename
        result = secure_filename('document.pdf')
        assert result == 'document.pdf'
        
        # Filename with path components
        result = secure_filename('/path/to/document.pdf')
        assert result == 'document.pdf'
        
        result = secure_filename('..\\..\\document.pdf')
        assert result == 'document.pdf'
        
        # Filename with dangerous characters
        result = secure_filename('document<script>.pdf')
        assert result == 'documentscript.pdf'
        
        # Very long filename
        long_name = 'a' * 300 + '.pdf'
        result = secure_filename(long_name)
        assert len(result) <= 255
        assert result.endswith('.pdf')
        
        # Empty filename
        result = secure_filename('')
        assert result == ''
        
        # None filename
        result = secure_filename(None)
        assert result is None
    
    def test_validate_request_security_decorator_success(self, app_context):
        """Test request security validation decorator success case."""
        with app_context.test_request_context():
            with patch('app.security.rate_limiter') as mock_limiter:
                with patch('app.security.request') as mock_request:
                    mock_request.environ = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
                    mock_request.content_length = 1000
                    mock_request.headers = {}
                    
                    mock_limiter.is_blocked.return_value = False
                    mock_limiter.is_rate_limited.return_value = False
                    
                    @validate_request_security()
                    def test_view():
                        return "success"
                    
                    result = test_view()
                    assert result == "success"
    
    def test_validate_request_security_blocked_ip(self, app_context):
        """Test request security with blocked IP."""
        with app_context.test_request_context():
            with patch('app.security.rate_limiter') as mock_limiter:
                with patch('app.security.request') as mock_request:
                    mock_request.environ = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
                    
                    mock_limiter.is_blocked.return_value = True
                    
                    @validate_request_security()
                    def test_view():
                        return "success"
                    
                    with pytest.raises(Exception):  # Should abort with 429
                        test_view()
    
    def test_validate_request_security_rate_limited(self, app_context):
        """Test request security with rate limiting."""
        with app_context.test_request_context():
            with patch('app.security.rate_limiter') as mock_limiter:
                with patch('app.security.request') as mock_request:
                    mock_request.environ = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
                    
                    mock_limiter.is_blocked.return_value = False
                    mock_limiter.is_rate_limited.return_value = True
                    
                    @validate_request_security()
                    def test_view():
                        return "success"
                    
                    with pytest.raises(Exception):  # Should abort with 429
                        test_view()