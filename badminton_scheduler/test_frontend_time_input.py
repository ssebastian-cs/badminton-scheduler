#!/usr/bin/env python3
"""
Test script to verify the frontend time input functionality.
This test checks that the HTML contains the required time input elements.
"""

import re
from pathlib import Path

def test_frontend_time_input():
    """Test that the frontend HTML contains the required time input elements."""
    
    # Read the HTML file
    html_file = Path(__file__).parent / 'static_frontend.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Test 1: Check for all-day checkbox
    assert 'id="allDayCheck"' in html_content, "All-day checkbox not found"
    assert 'onchange="toggleTimeInputs()"' in html_content, "Toggle function not attached to checkbox"
    
    # Test 2: Check for time input fields
    assert 'id="timeStart"' in html_content, "Start time input not found"
    assert 'id="timeEnd"' in html_content, "End time input not found"
    assert 'type="time"' in html_content, "Time input type not found"
    
    # Test 3: Check for error message elements
    assert 'id="timeStartError"' in html_content, "Start time error element not found"
    assert 'id="timeEndError"' in html_content, "End time error element not found"
    
    # Test 4: Check for JavaScript functions
    assert 'function toggleTimeInputs()' in html_content, "toggleTimeInputs function not found"
    assert 'function validateTimeInputs()' in html_content, "validateTimeInputs function not found"
    assert 'function formatTime(' in html_content, "formatTime function not found"
    
    # Test 5: Check for CSS classes
    assert 'time-input-section' in html_content, "Time input section CSS not found"
    assert 'checkbox-label' in html_content, "Checkbox label CSS not found"
    assert 'time-inputs-container' in html_content, "Time inputs container CSS not found"
    assert 'field-error' in html_content, "Field error CSS not found"
    
    # Test 6: Check that form submission includes time data
    assert 'is_all_day: allDayCheck.checked' in html_content, "All-day flag not included in form submission"
    assert 'requestBody.time_start = timeStart' in html_content, "Start time not included in form submission"
    assert 'requestBody.time_end = timeEnd' in html_content, "End time not included in form submission"
    
    # Test 7: Check for validation logic
    assert 'validateTimeInputs()' in html_content, "Validation not called in form submission"
    assert 'End time must be after start time' in html_content, "Time validation message not found"
    
    # Test 8: Check for time display in availability list
    assert 'formatTime(item.time_start)' in html_content, "Time formatting not used in display"
    assert 'item.is_all_day' in html_content, "All-day check not used in display"
    
    print("✅ All frontend time input tests passed!")
    return True

def test_time_validation_logic():
    """Test the time validation logic patterns in the JavaScript."""
    
    html_file = Path(__file__).parent / 'static_frontend.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for proper validation patterns
    validation_patterns = [
        r'if \(!timeStart\.value\)',  # Start time required check
        r'if \(!timeEnd\.value\)',    # End time required check
        r'endTime <= startTime',      # End time after start time check
        r'classList\.add\(\'field-error\'\)',  # Error styling
        r'classList\.remove\(\'field-error\'\)',  # Error clearing
    ]
    
    for pattern in validation_patterns:
        assert re.search(pattern, html_content), f"Validation pattern not found: {pattern}"
    
    print("✅ Time validation logic tests passed!")
    return True

def test_css_responsive_design():
    """Test that responsive design CSS is present."""
    
    html_file = Path(__file__).parent / 'static_frontend.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for responsive design patterns
    responsive_patterns = [
        r'@media \(max-width: 480px\)',  # Mobile breakpoint
        r'grid-template-columns: 1fr',   # Single column on mobile
        r'time-inputs-container',        # Container for time inputs
    ]
    
    for pattern in responsive_patterns:
        assert re.search(pattern, html_content), f"Responsive design pattern not found: {pattern}"
    
    print("✅ Responsive design tests passed!")
    return True

if __name__ == '__main__':
    try:
        test_frontend_time_input()
        test_time_validation_logic()
        test_css_responsive_design()
        print("\n🎉 All tests passed! Frontend time input functionality is properly implemented.")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)