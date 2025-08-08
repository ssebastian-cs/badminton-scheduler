#!/usr/bin/env python3
"""
Test script for time-enhanced availability API endpoints.
Tests the new time parsing and validation functionality.
"""

import sys
import os
from datetime import time
import re

# Copy the functions from api.py for testing
def parse_time_string(time_str):
    """Parse various time formats and return a time object."""
    if not time_str:
        return None
    
    time_str = time_str.strip().upper()
    
    # Handle common time formats
    time_patterns = [
        # 24-hour format: "19:00", "7:30"
        (r'^(\d{1,2}):(\d{2})$', lambda m: time(int(m.group(1)), int(m.group(2)))),
        # 12-hour format: "7:00 PM", "7PM", "7:30 AM"
        (r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', lambda m: time(
            int(m.group(1)) % 12 + (12 if m.group(3) == 'PM' else 0), 
            int(m.group(2))
        )),
        (r'^(\d{1,2})\s*(AM|PM)$', lambda m: time(
            int(m.group(1)) % 12 + (12 if m.group(2) == 'PM' else 0), 
            0
        )),
    ]
    
    for pattern, converter in time_patterns:
        match = re.match(pattern, time_str)
        if match:
            try:
                return converter(match)
            except ValueError:
                continue
    
    raise ValueError(f"Invalid time format: {time_str}")

def parse_time_range(time_range_str):
    """Parse time range strings like '7-9 PM', '19:00-21:00', '7:00 PM - 9:00 PM'."""
    if not time_range_str:
        return None, None
    
    # Handle range formats
    range_patterns = [
        # "7-9 PM", "7-9AM"
        r'^(\d{1,2})-(\d{1,2})\s*(AM|PM)$',
        # "7:00-9:00", "19:00-21:00"
        r'^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$',
        # "7:00 PM - 9:00 PM", "7 PM - 9 PM"
        r'^(.+?)\s*-\s*(.+)$'
    ]
    
    time_range_str = time_range_str.strip().upper()
    
    # Try specific range patterns first
    match = re.match(r'^(\d{1,2})-(\d{1,2})\s*(AM|PM)$', time_range_str)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        period = match.group(3)
        
        if period == 'PM' and start_hour != 12:
            start_hour += 12
        if period == 'PM' and end_hour != 12:
            end_hour += 12
        if period == 'AM' and start_hour == 12:
            start_hour = 0
        if period == 'AM' and end_hour == 12:
            end_hour = 0
            
        return time(start_hour, 0), time(end_hour, 0)
    
    # Try 24-hour range format
    match = re.match(r'^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$', time_range_str)
    if match:
        start_time = time(int(match.group(1)), int(match.group(2)))
        end_time = time(int(match.group(3)), int(match.group(4)))
        return start_time, end_time
    
    # Try general range split
    match = re.match(r'^(.+?)\s*-\s*(.+)$', time_range_str)
    if match:
        try:
            start_time = parse_time_string(match.group(1))
            end_time = parse_time_string(match.group(2))
            return start_time, end_time
        except ValueError:
            pass
    
    raise ValueError(f"Invalid time range format: {time_range_str}")

def validate_time_logic(start_time, end_time):
    """Validate that end time is after start time."""
    if start_time and end_time:
        if end_time <= start_time:
            raise ValueError("End time must be after start time")
    return True

def format_time_slot(start_time, end_time, is_all_day=False):
    """Format time information into a time_slot string for storage."""
    if is_all_day or (not start_time and not end_time):
        return None  # All day availability
    
    if start_time and end_time:
        return f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
    elif start_time:
        return f"{start_time.strftime('%H:%M')}"
    elif end_time:
        return f"until {end_time.strftime('%H:%M')}"
    
    return None

def test_parse_time_string():
    """Test various time string formats."""
    print("Testing parse_time_string...")
    
    # Test 24-hour format
    assert parse_time_string("19:00") == time(19, 0)
    assert parse_time_string("7:30") == time(7, 30)
    assert parse_time_string("00:00") == time(0, 0)
    
    # Test 12-hour format
    assert parse_time_string("7:00 PM") == time(19, 0)
    assert parse_time_string("7:30 AM") == time(7, 30)
    assert parse_time_string("12:00 PM") == time(12, 0)
    assert parse_time_string("12:00 AM") == time(0, 0)
    assert parse_time_string("7 PM") == time(19, 0)
    assert parse_time_string("7 AM") == time(7, 0)
    
    # Test invalid formats
    try:
        parse_time_string("25:00")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    try:
        parse_time_string("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✓ parse_time_string tests passed")

def test_parse_time_range():
    """Test time range parsing."""
    print("Testing parse_time_range...")
    
    # Test range formats
    start, end = parse_time_range("7-9 PM")
    assert start == time(19, 0)
    assert end == time(21, 0)
    
    start, end = parse_time_range("19:00-21:00")
    assert start == time(19, 0)
    assert end == time(21, 0)
    
    start, end = parse_time_range("7:00 PM - 9:00 PM")
    assert start == time(19, 0)
    assert end == time(21, 0)
    
    start, end = parse_time_range("7 AM - 9 AM")
    assert start == time(7, 0)
    assert end == time(9, 0)
    
    print("✓ parse_time_range tests passed")

def test_validate_time_logic():
    """Test time validation logic."""
    print("Testing validate_time_logic...")
    
    # Valid times
    assert validate_time_logic(time(19, 0), time(21, 0)) == True
    assert validate_time_logic(time(7, 0), time(9, 0)) == True
    assert validate_time_logic(None, time(9, 0)) == True
    assert validate_time_logic(time(7, 0), None) == True
    assert validate_time_logic(None, None) == True
    
    # Invalid times
    try:
        validate_time_logic(time(21, 0), time(19, 0))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    try:
        validate_time_logic(time(19, 0), time(19, 0))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✓ validate_time_logic tests passed")

def test_format_time_slot():
    """Test time slot formatting."""
    print("Testing format_time_slot...")
    
    # Test various combinations
    assert format_time_slot(time(19, 0), time(21, 0), False) == "19:00-21:00"
    assert format_time_slot(time(7, 30), None, False) == "07:30"
    assert format_time_slot(None, time(21, 0), False) == "until 21:00"
    assert format_time_slot(None, None, True) == None
    assert format_time_slot(time(19, 0), time(21, 0), True) == None
    
    print("✓ format_time_slot tests passed")

def run_all_tests():
    """Run all tests."""
    print("Running time API tests...\n")
    
    try:
        test_parse_time_string()
        test_parse_time_range()
        test_validate_time_logic()
        test_format_time_slot()
        
        print("\n✅ All tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)