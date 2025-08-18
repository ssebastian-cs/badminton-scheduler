"""
Unit tests for utility functions.
"""

import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock
from app.utils import (
    admin_required, login_required_with_message, validate_future_date,
    validate_time_range, safe_get_record, safe_delete_record, safe_create_record,
    safe_update_record, check_record_ownership, sanitize_text_input,
    format_datetime_for_display, get_date_range_filter, log_user_activity,
    log_admin_action, get_admin_actions, ValidationHelper
)


class TestUtilityDecorators:
    """Test utility decorators."""
    
    def test_admin_required_authenticated_admin(self, app_context, test_admin):
        """Test admin_required decorator with authenticated admin."""
        with app_context.test_request_context():
            with patch('app.utils.current_user', test_admin):
                @admin_required
                def test_view():
                    return "success"
                
                result = test_view()
                assert result == "success"
    
    def test_admin_required_not_authenticated(self, app_context):
        """Test admin_required decorator with unauthenticated user."""
        with app_context.test_request_context():
            mock_user = MagicMock()
            mock_user.is_authenticated = False
            
            with patch('app.utils.current_user', mock_user):
                @admin_required
                def test_view():
                    return "success"
                
                # Should redirect to login
                with pytest.raises(Exception):  # Redirect exception
                    test_view()
    
    def test_admin_required_not_admin(self, app_context, test_user):
        """Test admin_required decorator with non-admin user."""
        with app_context.test_request_context():
            with patch('app.utils.current_user', test_user):
                @admin_required
                def test_view():
                    return "success"
                
                # Should return permission error
                result = test_view()
                assert result is not None  # Error handler response
    
    def test_login_required_with_message_authenticated(self, app_context, test_user):
        """Test login_required_with_message with authenticated user."""
        with app_context.test_request_context():
            with patch('app.utils.current_user', test_user):
                @login_required_with_message("Custom message")
                def test_view():
                    return "success"
                
                result = test_view()
                assert result == "success"
    
    def test_login_required_with_message_not_authenticated(self, app_context):
        """Test login_required_with_message with unauthenticated user."""
        with app_context.test_request_context():
            mock_user = MagicMock()
            mock_user.is_authenticated = False
            
            with patch('app.utils.current_user', mock_user):
                @login_required_with_message("Custom message")
                def test_view():
                    return "success"
                
                # Should redirect to login
                with pytest.raises(Exception):  # Redirect exception
                    test_view()


class TestValidationFunctions:
    """Test validation utility functions."""
    
    def test_validate_future_date_valid(self):
        """Test validate_future_date with valid future date."""
        tomorrow = date.today() + timedelta(days=1)
        is_valid, error = validate_future_date(tomorrow)
        assert is_valid is True
        assert error is None
    
    def test_validate_future_date_past(self):
        """Test validate_future_date with past date."""
        yesterday = date.today() - timedelta(days=1)
        is_valid, error = validate_future_date(yesterday)
        assert is_valid is False
        assert "future" in error
    
    def test_validate_future_date_today(self):
        """Test validate_future_date with today's date."""
        today = date.today()
        is_valid, error = validate_future_date(today)
        assert is_valid is False
        assert "future" in error
    
    def test_validate_future_date_string_format(self):
        """Test validate_future_date with string date."""
        tomorrow = date.today() + timedelta(days=1)
        date_string = tomorrow.strftime('%Y-%m-%d')
        is_valid, error = validate_future_date(date_string)
        assert is_valid is True
        assert error is None
    
    def test_validate_future_date_invalid_string(self):
        """Test validate_future_date with invalid string format."""
        is_valid, error = validate_future_date("invalid-date")
        assert is_valid is False
        assert "format" in error
    
    def test_validate_future_date_empty(self):
        """Test validate_future_date with empty value."""
        is_valid, error = validate_future_date(None)
        assert is_valid is False
        assert "required" in error
    
    def test_validate_time_range_valid(self):
        """Test validate_time_range with valid time range."""
        start_time = time(9, 0)
        end_time = time(17, 0)
        is_valid, error = validate_time_range(start_time, end_time)
        assert is_valid is True
        assert error is None
    
    def test_validate_time_range_invalid(self):
        """Test validate_time_range with invalid time range."""
        start_time = time(17, 0)
        end_time = time(9, 0)
        is_valid, error = validate_time_range(start_time, end_time)
        assert is_valid is False
        assert "after start time" in error
    
    def test_validate_time_range_equal(self):
        """Test validate_time_range with equal times."""
        start_time = time(9, 0)
        end_time = time(9, 0)
        is_valid, error = validate_time_range(start_time, end_time)
        assert is_valid is False
        assert "after start time" in error
    
    def test_validate_time_range_string_format(self):
        """Test validate_time_range with string times."""
        is_valid, error = validate_time_range("09:00", "17:00")
        assert is_valid is True
        assert error is None
    
    def test_validate_time_range_invalid_string(self):
        """Test validate_time_range with invalid string format."""
        is_valid, error = validate_time_range("invalid", "17:00")
        assert is_valid is False
        assert "format" in error
    
    def test_validate_time_range_missing_values(self):
        """Test validate_time_range with missing values."""
        is_valid, error = validate_time_range(None, time(17, 0))
        assert is_valid is False
        assert "required" in error


class TestDatabaseHelpers:
    """Test database helper functions."""
    
    def test_safe_get_record_exists(self, db_session, test_user):
        """Test safe_get_record with existing record."""
        from app.models import User
        
        record = safe_get_record(User, test_user.id)
        assert record is not None
        assert record.id == test_user.id
    
    def test_safe_get_record_not_exists(self, db_session):
        """Test safe_get_record with non-existing record."""
        from app.models import User
        
        record = safe_get_record(User, 99999)
        assert record is None
    
    def test_check_record_ownership_owner(self, test_user):
        """Test check_record_ownership with record owner."""
        mock_record = MagicMock()
        mock_record.user_id = test_user.id
        
        result = check_record_ownership(mock_record, test_user)
        assert result is True
    
    def test_check_record_ownership_admin(self, test_admin):
        """Test check_record_ownership with admin user."""
        mock_record = MagicMock()
        mock_record.user_id = 999  # Different user
        
        result = check_record_ownership(mock_record, test_admin, allow_admin=True)
        assert result is True
    
    def test_check_record_ownership_not_owner(self, test_user):
        """Test check_record_ownership with non-owner."""
        mock_record = MagicMock()
        mock_record.user_id = 999  # Different user
        
        result = check_record_ownership(mock_record, test_user)
        assert result is False
    
    def test_check_record_ownership_unauthenticated(self):
        """Test check_record_ownership with unauthenticated user."""
        mock_user = MagicMock()
        mock_user.is_authenticated = False
        mock_record = MagicMock()
        
        result = check_record_ownership(mock_record, mock_user)
        assert result is False


class TestTextUtilities:
    """Test text utility functions."""
    
    def test_sanitize_text_input_basic(self):
        """Test basic text sanitization."""
        result = sanitize_text_input("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_text_input_html_removal(self):
        """Test HTML tag removal."""
        result = sanitize_text_input("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_text_input_length_limit(self):
        """Test length limiting."""
        long_text = "a" * 100
        result = sanitize_text_input(long_text, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_text_input_dangerous_chars(self):
        """Test removal of dangerous characters."""
        result = sanitize_text_input('Hello"World<test>')
        assert '"' not in result
        assert '<' not in result
        assert '>' not in result
    
    def test_sanitize_text_input_empty(self):
        """Test empty input."""
        result = sanitize_text_input("")
        assert result == ""
    
    def test_sanitize_text_input_none(self):
        """Test None input."""
        result = sanitize_text_input(None)
        assert result == ""
    
    def test_format_datetime_for_display_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2023, 1, 1, 12, 30)
        result = format_datetime_for_display(dt)
        assert "2023-01-01 12:30" == result
    
    def test_format_datetime_for_display_date(self):
        """Test date formatting."""
        d = date(2023, 1, 1)
        result = format_datetime_for_display(d)
        assert "2023-01-01" == result
    
    def test_format_datetime_for_display_time(self):
        """Test time formatting."""
        t = time(12, 30)
        result = format_datetime_for_display(t)
        assert "12:30" == result
    
    def test_format_datetime_for_display_custom_format(self):
        """Test custom format string."""
        dt = datetime(2023, 1, 1, 12, 30)
        result = format_datetime_for_display(dt, "%Y/%m/%d")
        assert "2023/01/01" == result
    
    def test_format_datetime_for_display_empty(self):
        """Test empty input."""
        result = format_datetime_for_display(None)
        assert result == ""


class TestDateRangeFilter:
    """Test date range filter function."""
    
    def test_get_date_range_filter_today(self):
        """Test today filter."""
        start, end = get_date_range_filter('today')
        today = date.today()
        assert start == today
        assert end == today
    
    def test_get_date_range_filter_week(self):
        """Test week filter."""
        start, end = get_date_range_filter('week')
        today = date.today()
        
        # Should be Monday to Sunday
        days_since_monday = today.weekday()
        expected_start = today - timedelta(days=days_since_monday)
        expected_end = expected_start + timedelta(days=6)
        
        assert start == expected_start
        assert end == expected_end
    
    def test_get_date_range_filter_month(self):
        """Test month filter."""
        start, end = get_date_range_filter('month')
        today = date.today()
        
        # Should be first to last day of month
        expected_start = today.replace(day=1)
        assert start == expected_start
        assert end.month == today.month
    
    def test_get_date_range_filter_custom(self):
        """Test custom date range."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        start, end = get_date_range_filter('custom', start_date, end_date)
        assert start == start_date
        assert end == end_date
    
    def test_get_date_range_filter_custom_strings(self):
        """Test custom date range with strings."""
        start, end = get_date_range_filter('custom', '2023-01-01', '2023-01-31')
        assert start == date(2023, 1, 1)
        assert end == date(2023, 1, 31)
    
    def test_get_date_range_filter_invalid(self):
        """Test invalid filter type."""
        start, end = get_date_range_filter('invalid')
        today = date.today()
        assert start == today
        assert end == today


class TestValidationHelper:
    """Test ValidationHelper class."""
    
    def test_validate_availability_data_valid(self):
        """Test valid availability data."""
        tomorrow = date.today() + timedelta(days=1)
        start_time = time(9, 0)
        end_time = time(17, 0)
        
        is_valid, errors = ValidationHelper.validate_availability_data(
            tomorrow, start_time, end_time
        )
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_availability_data_invalid_date(self):
        """Test invalid date."""
        yesterday = date.today() - timedelta(days=1)
        start_time = time(9, 0)
        end_time = time(17, 0)
        
        is_valid, errors = ValidationHelper.validate_availability_data(
            yesterday, start_time, end_time
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("future" in error for error in errors)
    
    def test_validate_availability_data_invalid_time(self):
        """Test invalid time range."""
        tomorrow = date.today() + timedelta(days=1)
        start_time = time(17, 0)
        end_time = time(9, 0)
        
        is_valid, errors = ValidationHelper.validate_availability_data(
            tomorrow, start_time, end_time
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("after start time" in error for error in errors)
    
    def test_validate_comment_data_valid(self):
        """Test valid comment data."""
        content = "This is a valid comment."
        
        is_valid, errors, sanitized = ValidationHelper.validate_comment_data(content)
        assert is_valid is True
        assert len(errors) == 0
        assert sanitized == content
    
    def test_validate_comment_data_empty(self):
        """Test empty comment."""
        is_valid, errors, sanitized = ValidationHelper.validate_comment_data("")
        assert is_valid is False
        assert len(errors) > 0
        assert any("required" in error for error in errors)
        assert sanitized == ""
    
    def test_validate_comment_data_too_long(self):
        """Test comment too long."""
        long_content = "a" * 1001
        
        is_valid, errors, sanitized = ValidationHelper.validate_comment_data(
            long_content, max_length=1000
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("too long" in error for error in errors)