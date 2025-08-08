#!/usr/bin/env python3
"""
Comprehensive test suite for input validation and error handling.
Tests both backend API validation and edge cases.
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER = {"username": "john_smith", "password": "password123"}

def login():
    """Login and return session."""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return session

def test_time_validation():
    """Test comprehensive time format validation."""
    session = login()
    
    print("Testing time validation...")
    
    # Test cases: (time_start, time_end, expected_status, description)
    test_cases = [
        # Valid cases
        ("09:00", "17:00", 200, "Valid 24-hour format"),
        ("9:00", "17:00", 200, "Valid single-digit hour"),
        ("00:00", "23:59", 200, "Valid edge times"),
        
        # Invalid time formats
        ("25:00", "17:00", 400, "Invalid hour > 23"),
        ("09:60", "17:00", 400, "Invalid minutes > 59"),
        ("9", "17:00", 400, "Missing minutes"),
        ("abc", "17:00", 400, "Non-numeric time"),
        ("", "17:00", 400, "Empty start time"),
        
        # Invalid time logic
        ("17:00", "09:00", 400, "End time before start time"),
        ("17:00", "17:00", 400, "End time equals start time"),
        
        # Edge cases
        ("23:59", "23:58", 400, "End time 1 minute before start"),
        ("00:00", "00:01", 200, "Very short valid duration"),
    ]
    
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    for time_start, time_end, expected_status, description in test_cases:
        data = {
            "date": tomorrow,
            "status": "available",
            "is_all_day": False,
            "time_start": time_start,
            "time_end": time_end
        }
        
        response = session.post(f"{BASE_URL}/api/availability", json=data)
        
        if response.status_code == expected_status:
            print(f"✓ {description}: {response.status_code}")
        else:
            print(f"✗ {description}: Expected {expected_status}, got {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', 'Unknown error')}")

def test_date_validation():
    """Test comprehensive date validation."""
    session = login()
    
    print("\nTesting date validation...")
    
    # Test cases: (date, expected_status, description)
    test_cases = [
        # Valid cases
        ((date.today() + timedelta(days=1)).isoformat(), 200, "Tomorrow (valid future date)"),
        ((date.today() + timedelta(days=30)).isoformat(), 200, "30 days from now"),
        
        # Invalid formats
        ("2025-13-01", 400, "Invalid month > 12"),
        ("2025-02-30", 400, "Invalid day for February"),
        ("25-08-15", 400, "Wrong date format (YY-MM-DD)"),
        ("2025/08/15", 400, "Wrong separator (slashes)"),
        ("invalid-date", 400, "Non-date string"),
        ("", 400, "Empty date"),
        
        # Past dates
        ((date.today() - timedelta(days=1)).isoformat(), 400, "Yesterday (past date)"),
        ("2020-01-01", 400, "Far past date"),
        
        # Edge cases
        (date.today().isoformat(), 400, "Today (should be past by time of processing)"),
        ("2040-01-01", 400, "Far future date (outside reasonable range)"),
    ]
    
    for test_date, expected_status, description in test_cases:
        data = {
            "date": test_date,
            "status": "available",
            "is_all_day": True
        }
        
        response = session.post(f"{BASE_URL}/api/availability", json=data)
        
        if response.status_code == expected_status:
            print(f"✓ {description}: {response.status_code}")
        else:
            print(f"✗ {description}: Expected {expected_status}, got {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', 'Unknown error')}")

def test_field_validation():
    """Test validation of other fields."""
    session = login()
    
    print("\nTesting field validation...")
    
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    # Test cases: (data, expected_status, description)
    test_cases = [
        # Valid cases
        ({"date": tomorrow, "status": "available"}, 200, "Minimal valid data"),
        ({"date": tomorrow, "status": "tentative", "play_preference": "either"}, 200, "Valid with preference"),
        ({"date": tomorrow, "status": "not_available", "notes": "Valid note"}, 200, "Valid with notes"),
        
        # Invalid status
        ({"date": tomorrow, "status": "invalid_status"}, 400, "Invalid status value"),
        ({"date": tomorrow, "status": ""}, 400, "Empty status"),
        ({"date": tomorrow}, 400, "Missing status"),
        
        # Invalid play preference
        ({"date": tomorrow, "status": "available", "play_preference": "invalid"}, 400, "Invalid play preference"),
        
        # Invalid notes
        ({"date": tomorrow, "status": "available", "notes": "x" * 1001}, 400, "Notes too long (>1000 chars)"),
        ({"date": tomorrow, "status": "available", "notes": "<script>alert('xss')</script>"}, 400, "Malicious content in notes"),
        
        # Invalid data types
        ({"date": tomorrow, "status": "available", "is_all_day": "not_boolean"}, 400, "Invalid is_all_day type"),
        ({"date": tomorrow, "status": "available", "time_start": 123}, 400, "Invalid time_start type"),
    ]
    
    for data, expected_status, description in test_cases:
        response = session.post(f"{BASE_URL}/api/availability", json=data)
        
        if response.status_code == expected_status:
            print(f"✓ {description}: {response.status_code}")
        else:
            print(f"✗ {description}: Expected {expected_status}, got {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', 'Unknown error')}")

def test_admin_filter_validation():
    """Test admin filter validation."""
    session = login()
    
    print("\nTesting admin filter validation...")
    
    # Test cases: (params, expected_status, description)
    test_cases = [
        # Valid cases
        ({}, 200, "No filters (should work)"),
        ({"start_date": "2025-01-01"}, 200, "Valid start date only"),
        ({"end_date": "2025-12-31"}, 200, "Valid end date only"),
        ({"start_date": "2025-01-01", "end_date": "2025-12-31"}, 200, "Valid date range"),
        ({"page": "1", "per_page": "10"}, 200, "Valid pagination"),
        
        # Invalid date formats
        ({"start_date": "invalid-date"}, 400, "Invalid start date format"),
        ({"end_date": "2025-13-01"}, 400, "Invalid end date"),
        
        # Invalid date logic
        ({"start_date": "2025-12-31", "end_date": "2025-01-01"}, 400, "Start date after end date"),
        
        # Invalid pagination
        ({"page": "0"}, 400, "Invalid page number (0)"),
        ({"page": "-1"}, 400, "Negative page number"),
        ({"per_page": "0"}, 400, "Invalid per_page (0)"),
        ({"per_page": "1001"}, 400, "per_page too large"),
        
        # Edge cases
        ({"start_date": "2019-01-01"}, 400, "Date before minimum range"),
        ({"end_date": "2031-01-01"}, 400, "Date after maximum range"),
    ]
    
    for params, expected_status, description in test_cases:
        response = session.get(f"{BASE_URL}/api/admin/availability/filtered", params=params)
        
        if response.status_code == expected_status:
            print(f"✓ {description}: {response.status_code}")
        else:
            print(f"✗ {description}: Expected {expected_status}, got {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', 'Unknown error')}")

def test_malformed_requests():
    """Test handling of malformed requests."""
    session = login()
    
    print("\nTesting malformed request handling...")
    
    # Test cases: (data, content_type, expected_status, description)
    test_cases = [
        # Invalid JSON
        ("invalid json", "application/json", 400, "Invalid JSON syntax"),
        ("", "application/json", 400, "Empty request body"),
        (None, "application/json", 400, "Null request body"),
        
        # Wrong content type
        ('{"date": "2025-08-15", "status": "available"}', "text/plain", 400, "Wrong content type"),
        
        # Very large payload
        (json.dumps({"date": "2025-08-15", "status": "available", "notes": "x" * 10000}), "application/json", 400, "Oversized payload"),
    ]
    
    for data, content_type, expected_status, description in test_cases:
        headers = {"Content-Type": content_type}
        
        try:
            response = session.post(f"{BASE_URL}/api/availability", data=data, headers=headers)
            
            if response.status_code == expected_status:
                print(f"✓ {description}: {response.status_code}")
            else:
                print(f"✗ {description}: Expected {expected_status}, got {response.status_code}")
        except Exception as e:
            print(f"✗ {description}: Exception occurred - {str(e)}")

def main():
    """Run all validation tests."""
    print("Starting comprehensive validation tests...\n")
    
    try:
        test_time_validation()
        test_date_validation()
        test_field_validation()
        test_admin_filter_validation()
        test_malformed_requests()
        
        print("\n" + "="*50)
        print("Validation tests completed!")
        print("Review the results above to ensure all validations are working correctly.")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())