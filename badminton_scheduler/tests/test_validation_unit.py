#!/usr/bin/env python3
"""
Unit tests for validation logic and time parsing functions.
Tests all validation functions in isolation to ensure they work correctly.

Requirements covered:
- 5.1: Time format validation
- 5.2: Time logic validation  
- 5.4: Data integrity and validation
"""

import pytest
import sys
import os
from datetime import datetime, date, time, timedelta

# Add the current directory to the path so we can import from api
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import (
    parse_time_string,
    parse_time_range,
    validate_time_logic,
    validate_date_input,
    validate_availability_status,
    validate_play_preference,
    validate_notes,
    format_time_slot
)

class TestTimeParsingFunctions:
    """Unit tests for time parsing functions."""
    
    def test_parse_time_string_24_hour_format(self):
        """Test parsing 24-hour time format."""
        # Valid 24-hour formats
        assert parse_time_string("19:00") == time(19, 0)
        assert parse_time_string("07:30") == time(7, 30)
        assert parse_time_string("23:59") == time(23, 59)
        assert parse_time_string("00:00") == time(0, 0)
        assert parse_time_string("12:15") == time(12, 15)
        
        # With seconds
        assert parse_time_string("19:00:00") == time(19, 0, 0)
        assert parse_time_string("07:30:45") == time(7, 30, 45)
    
    def test_parse_time_string_12_hour_format(self):
        """Test parsing 12-hour time format."""
        # Valid 12-hour formats with minutes
        assert parse_time_string("7:00 PM") == time(19, 0)
        assert parse_time_string("7:30 AM") == time(7, 30)
        assert parse_time_string("12:15 PM") == time(12, 15)
        assert parse_time_string("12:15 AM") == time(0, 15)
        assert parse_time_string("11:59 PM") == time(23, 59)
        
        # Valid 12-hour formats without minutes
        assert parse_time_string("7PM") == time(19, 0)
        assert parse_time_string("7 AM") == time(7, 0)
        assert parse_time_string("12 PM") == time(12, 0)
        assert parse_time_string("12 AM") == time(0, 0)
    
    def test_parse_time_string_edge_cases(self):
        """Test edge cases for time string parsing."""
        # None and empty strings
        assert parse_time_string(None) is None
        assert parse_time_string("") is None
        assert parse_time_string("   ") is None
        
        # Case insensitive
        assert parse_time_string("7:00 pm") == time(19, 0)
        assert parse_time_string("7:00 PM") == time(19, 0)
        assert parse_time_string("7pm") == time(19, 0)
        assert parse_time_string("7PM") == time(19, 0)
    
    def test_parse_time_string_invalid_formats(self):
        """Test invalid time string formats."""
        invalid_times = [
            "25:00",  # Invalid hour
            "12:60",  # Invalid minute
            "12:30:60",  # Invalid second
            "13 PM",  # Invalid 12-hour format
            "0 AM",   # Invalid 12-hour format
            "invalid-time",
            "12:30:45:00",  # Too many components
            "abc:def",
            "12:",
            ":30",
            "12:30 XM",  # Invalid AM/PM
            "24:00",  # Invalid 24-hour
            "-1:00",  # Negative hour
            "12:-30", # Negative minute
        ]
        
        for invalid_time in invalid_times:
            with pytest.raises(ValueError):
                parse_time_string(invalid_time)
    
    def test_parse_time_string_input_validation(self):
        """Test input validation for time string parsing."""
        # Non-string inputs
        with pytest.raises(ValueError):
            parse_time_string(123)
        
        with pytest.raises(ValueError):
            parse_time_string(['7:00'])
        
        # Too long input
        with pytest.raises(ValueError):
            parse_time_string("a" * 25)
    
    def test_parse_time_range_same_period(self):
        """Test parsing time ranges with same AM/PM period."""
        # Same period ranges
        start, end = parse_time_range("7-9 PM")
        assert start == time(19, 0)
        assert end == time(21, 0)
        
        start, end = parse_time_range("8-11 AM")
        assert start == time(8, 0)
        assert end == time(11, 0)
        
        start, end = parse_time_range("10-12 PM")
        assert start == time(22, 0)
        assert end == time(0, 0)  # 12 AM = midnight
    
    def test_parse_time_range_24_hour_format(self):
        """Test parsing 24-hour format time ranges."""
        start, end = parse_time_range("19:00-21:00")
        assert start == time(19, 0)
        assert end == time(21, 0)
        
        start, end = parse_time_range("07:30-09:45")
        assert start == time(7, 30)
        assert end == time(9, 45)
        
        start, end = parse_time_range("23:00-23:59")
        assert start == time(23, 0)
        assert end == time(23, 59)
    
    def test_parse_time_range_mixed_formats(self):
        """Test parsing time ranges with mixed formats."""
        start, end = parse_time_range("7:00 PM - 9:00 PM")
        assert start == time(19, 0)
        assert end == time(21, 0)
        
        start, end = parse_time_range("7 PM - 9 PM")
        assert start == time(19, 0)
        assert end == time(21, 0)
        
        start, end = parse_time_range("19:00 - 21:00")
        assert start == time(19, 0)
        assert end == time(21, 0)
    
    def test_parse_time_range_invalid_formats(self):
        """Test invalid time range formats."""
        invalid_ranges = [
            "7-9",  # No AM/PM
            "25-26 PM",  # Invalid hours
            "7-6 PM",  # End before start
            "no-dash-here",
            "7--9 PM",  # Double dash
            "7-9-10 PM",  # Multiple dashes
            "- 9 PM",  # Missing start
            "7 PM -",  # Missing end
            "",  # Empty string
            "7 PM 9 PM",  # No separator
        ]
        
        for invalid_range in invalid_ranges:
            with pytest.raises(ValueError):
                parse_time_range(invalid_range)
    
    def test_parse_time_range_edge_cases(self):
        """Test edge cases for time range parsing."""
        # None and empty strings
        start, end = parse_time_range(None)
        assert start is None and end is None
        
        start, end = parse_time_range("")
        assert start is None and end is None
        
        start, end = parse_time_range("   ")
        assert start is None and end is None
    
    def test_parse_time_range_input_validation(self):
        """Test input validation for time range parsing."""
        # Non-string inputs
        with pytest.raises(ValueError):
            parse_time_range(123)
        
        # Too long input
        with pytest.raises(ValueError):
            parse_time_range("a" * 55)

class TestTimeLogicValidation:
    """Unit tests for time logic validation."""
    
    def test_validate_time_logic_valid_cases(self):
        """Test valid time logic scenarios."""
        # Both times provided, end after start
        assert validate_time_logic(time(19, 0), time(21, 0)) == True
        assert validate_time_logic(time(7, 30), time(9, 45)) == True
        assert validate_time_logic(time(23, 0), time(23, 59)) == True
        
        # Only start time provided
        assert validate_time_logic(time(19, 0), None) == True
        
        # Only end time provided
        assert validate_time_logic(None, time(21, 0)) == True
        
        # Neither time provided (all-day)
        assert validate_time_logic(None, None) == True
    
    def test_validate_time_logic_invalid_cases(self):
        """Test invalid time logic scenarios."""
        # End time before start time
        with pytest.raises(ValueError) as exc_info:
            validate_time_logic(time(21, 0), time(19, 0))
        assert "after" in str(exc_info.value).lower()
        
        # End time equal to start time
        with pytest.raises(ValueError) as exc_info:
            validate_time_logic(time(19, 0), time(19, 0))
        assert "after" in str(exc_info.value).lower()
    
    def test_validate_time_logic_edge_cases(self):
        """Test edge cases for time logic validation."""
        # Very short time spans (should be allowed)
        assert validate_time_logic(time(19, 0), time(19, 1)) == True
        
        # Midnight crossing (should be rejected in current implementation)
        with pytest.raises(ValueError):
            validate_time_logic(time(23, 0), time(1, 0))

class TestDateValidation:
    """Unit tests for date validation."""
    
    def test_validate_date_input_valid_dates(self):
        """Test valid date inputs."""
        assert validate_date_input("2025-08-15") == date(2025, 8, 15)
        assert validate_date_input("2025-01-01") == date(2025, 1, 1)
        assert validate_date_input("2025-12-31") == date(2025, 12, 31)
        assert validate_date_input("2024-02-29") == date(2024, 2, 29)  # Leap year
    
    def test_validate_date_input_invalid_formats(self):
        """Test invalid date formats."""
        invalid_dates = [
            "2025/08/15",  # Wrong separator
            "08-15-2025",  # Wrong order
            "2025-8-15",   # Missing zero padding (should still work)
            "2025-13-01",  # Invalid month
            "2025-02-30",  # Invalid day
            "2025-02-29",  # Not a leap year
            "invalid-date",
            "2025-08",     # Incomplete
            "2025-08-15-extra",  # Extra parts
        ]
        
        for invalid_date in invalid_dates:
            with pytest.raises(ValueError):
                validate_date_input(invalid_date)
    
    def test_validate_date_input_edge_cases(self):
        """Test edge cases for date validation."""
        # Empty and None inputs
        with pytest.raises(ValueError):
            validate_date_input("")
        
        with pytest.raises(ValueError):
            validate_date_input(None)
        
        # Non-string input
        with pytest.raises(ValueError):
            validate_date_input(20250815)
    
    def test_validate_date_input_range_limits(self):
        """Test date range limits."""
        # Dates too far in the past
        with pytest.raises(ValueError):
            validate_date_input("2019-01-01")
        
        # Dates too far in the future
        with pytest.raises(ValueError):
            validate_date_input("2031-01-01")
        
        # Valid range boundaries
        assert validate_date_input("2020-01-01") == date(2020, 1, 1)
        assert validate_date_input("2030-12-31") == date(2030, 12, 31)

class TestStatusValidation:
    """Unit tests for status validation."""
    
    def test_validate_availability_status_valid(self):
        """Test valid availability statuses."""
        valid_statuses = ['available', 'tentative', 'not_available']
        
        for status in valid_statuses:
            assert validate_availability_status(status) == status
    
    def test_validate_availability_status_invalid(self):
        """Test invalid availability statuses."""
        invalid_statuses = [
            'invalid_status',
            'Available',  # Wrong case
            'maybe',
            'yes',
            'no',
            '',
            None,
            123,
            ['available']
        ]
        
        for status in invalid_statuses:
            with pytest.raises(ValueError):
                validate_availability_status(status)

class TestPlayPreferenceValidation:
    """Unit tests for play preference validation."""
    
    def test_validate_play_preference_valid(self):
        """Test valid play preferences."""
        valid_preferences = ['drop_in', 'book_court', 'either']
        
        for preference in valid_preferences:
            assert validate_play_preference(preference) == preference
        
        # None should be allowed (optional field)
        assert validate_play_preference(None) is None
        assert validate_play_preference('') is None
    
    def test_validate_play_preference_invalid(self):
        """Test invalid play preferences."""
        invalid_preferences = [
            'invalid_preference',
            'drop-in',  # Wrong format
            'book court',  # Wrong format
            'both',
            'any',
            123,
            ['drop_in']
        ]
        
        for preference in invalid_preferences:
            with pytest.raises(ValueError):
                validate_play_preference(preference)

class TestNotesValidation:
    """Unit tests for notes validation."""
    
    def test_validate_notes_valid(self):
        """Test valid notes."""
        # Valid notes
        assert validate_notes("Valid notes") == "Valid notes"
        assert validate_notes("") is None
        assert validate_notes(None) is None
        assert validate_notes("   ") is None  # Whitespace only
        
        # Long but valid notes
        long_notes = "a" * 1000
        assert validate_notes(long_notes) == long_notes
    
    def test_validate_notes_invalid(self):
        """Test invalid notes."""
        # Too long
        with pytest.raises(ValueError):
            validate_notes("a" * 1001)
        
        # Malicious content
        with pytest.raises(ValueError):
            validate_notes("<script>alert('xss')</script>")
        
        with pytest.raises(ValueError):
            validate_notes("javascript:alert('xss')")
        
        # Non-string input
        with pytest.raises(ValueError):
            validate_notes(123)
        
        with pytest.raises(ValueError):
            validate_notes(['notes'])
    
    def test_validate_notes_sanitization(self):
        """Test notes sanitization."""
        # Whitespace trimming
        assert validate_notes("  notes  ") == "notes"
        assert validate_notes("\tnotes\n") == "notes"

class TestTimeSlotFormatting:
    """Unit tests for time slot formatting."""
    
    def test_format_time_slot_all_day(self):
        """Test formatting all-day time slots."""
        assert format_time_slot(None, None, True) is None
        assert format_time_slot(time(19, 0), time(21, 0), True) is None
        assert format_time_slot(None, None, False) is None
    
    def test_format_time_slot_time_range(self):
        """Test formatting time ranges."""
        result = format_time_slot(time(19, 0), time(21, 0), False)
        assert result == "19:00-21:00"
        
        result = format_time_slot(time(7, 30), time(9, 45), False)
        assert result == "07:30-09:45"
    
    def test_format_time_slot_single_times(self):
        """Test formatting single times."""
        # Start time only
        result = format_time_slot(time(19, 0), None, False)
        assert result == "19:00"
        
        # End time only
        result = format_time_slot(None, time(21, 0), False)
        assert result == "until 21:00"
    
    def test_format_time_slot_edge_cases(self):
        """Test edge cases for time slot formatting."""
        # Midnight times
        result = format_time_slot(time(0, 0), time(1, 0), False)
        assert result == "00:00-01:00"
        
        # Late night times
        result = format_time_slot(time(23, 30), time(23, 59), False)
        assert result == "23:30-23:59"

class TestValidationErrorMessages:
    """Unit tests for validation error messages."""
    
    def test_time_parsing_error_messages(self):
        """Test that time parsing errors have helpful messages."""
        try:
            parse_time_string("25:00")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "hour" in str(e).lower()
            assert "25" in str(e)
        
        try:
            parse_time_string("12:70")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "minute" in str(e).lower()
            assert "70" in str(e)
    
    def test_time_range_error_messages(self):
        """Test that time range errors have helpful messages."""
        try:
            parse_time_range("9-7 PM")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "after" in str(e).lower()
        
        try:
            parse_time_range("invalid-range")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "format" in str(e).lower()
    
    def test_date_validation_error_messages(self):
        """Test that date validation errors have helpful messages."""
        try:
            validate_date_input("2025/08/15")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "YYYY-MM-DD" in str(e)
        
        try:
            validate_date_input("2019-01-01")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "before" in str(e).lower()
    
    def test_status_validation_error_messages(self):
        """Test that status validation errors have helpful messages."""
        try:
            validate_availability_status("invalid_status")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "available" in str(e)
            assert "tentative" in str(e)
            assert "not_available" in str(e)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])