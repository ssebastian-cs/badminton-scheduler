#!/usr/bin/env python3
"""
Frontend-only test for Task 6: Frontend time input functionality.
This test verifies that the frontend HTML and JavaScript are correctly implemented.
"""

import re
from pathlib import Path

def test_frontend_implementation():
    """Test that all required frontend components are implemented."""
    
    html_file = Path(__file__).parent / 'static_frontend.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    def check_requirement(description, condition, error_msg=""):
        nonlocal tests_passed, total_tests
        total_tests += 1
        if condition:
            print(f"✅ {description}")
            tests_passed += 1
        else:
            print(f"❌ {description} - {error_msg}")
    
    # Requirement 1.1: Time input fields
    check_requirement(
        "Time input fields (start time, end time) added to availability form",
        'id="timeStart"' in html_content and 'id="timeEnd"' in html_content and 'type="time"' in html_content,
        "Missing time input fields"
    )
    
    # Requirement 1.2: All-day checkbox toggle
    check_requirement(
        "All-day checkbox toggle implemented",
        'id="allDayCheck"' in html_content and 'onchange="toggleTimeInputs()"' in html_content,
        "Missing all-day checkbox or toggle function"
    )
    
    check_requirement(
        "Toggle function shows/hides time inputs",
        'function toggleTimeInputs()' in html_content and 'timeInputs.classList.add(\'hidden\')' in html_content,
        "Toggle function not properly implemented"
    )
    
    # Requirement 4.1: Client-side time format validation
    check_requirement(
        "Client-side time format validation implemented",
        'function validateTimeInputs()' in html_content,
        "Time validation function not found"
    )
    
    check_requirement(
        "Validation checks for required time fields",
        'Start time is required when not all-day' in html_content and 'End time is required when not all-day' in html_content,
        "Required field validation messages not found"
    )
    
    check_requirement(
        "Validation checks end time after start time",
        'End time must be after start time' in html_content and 'endTime <= startTime' in html_content,
        "Time order validation not implemented"
    )
    
    # Requirement 4.6: Form submission includes time data
    check_requirement(
        "Form submission logic updated to include time data",
        'is_all_day: allDayCheck.checked' in html_content,
        "All-day flag not included in form submission"
    )
    
    check_requirement(
        "Form submission includes time fields when not all-day",
        'requestBody.time_start = timeStart' in html_content and 'requestBody.time_end = timeEnd' in html_content,
        "Time fields not included in form submission"
    )
    
    check_requirement(
        "Form validation called before submission",
        'validateTimeInputs()' in html_content and 'Please fix the time input errors' in html_content,
        "Form validation not called before submission"
    )
    
    # Additional UI/UX requirements
    check_requirement(
        "Error message elements for time validation",
        'id="timeStartError"' in html_content and 'id="timeEndError"' in html_content,
        "Error message elements not found"
    )
    
    check_requirement(
        "CSS styling for time input section",
        'time-input-section' in html_content and 'checkbox-label' in html_content,
        "CSS styling for time inputs not found"
    )
    
    check_requirement(
        "Responsive design for time inputs",
        '@media (max-width: 480px)' in html_content and 'time-inputs-container' in html_content,
        "Responsive design not implemented"
    )
    
    check_requirement(
        "Time display formatting in availability list",
        'formatTime(item.time_start)' in html_content and 'formatTime(item.time_end)' in html_content,
        "Time formatting not implemented in display"
    )
    
    check_requirement(
        "Form reset functionality includes time inputs",
        'toggleTimeInputs()' in html_content and ('allDayCheck.checked = true' in html_content or 'allDayCheck\').checked = true' in html_content),
        "Form reset not properly implemented"
    )
    
    # Check JavaScript syntax and structure
    check_requirement(
        "JavaScript functions are properly structured",
        html_content.count('function ') >= 6,  # Should have multiple functions
        "Not enough JavaScript functions found"
    )
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All frontend requirements for Task 6 are successfully implemented!")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} requirements still need to be addressed.")
        return False

def test_javascript_syntax():
    """Test that the JavaScript syntax is valid by checking for common patterns."""
    
    html_file = Path(__file__).parent / 'static_frontend.html'
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract JavaScript content
    script_match = re.search(r'<script>(.*?)</script>', html_content, re.DOTALL)
    if not script_match:
        print("❌ No JavaScript section found")
        return False
    
    js_content = script_match.group(1)
    
    # Check for balanced braces
    open_braces = js_content.count('{')
    close_braces = js_content.count('}')
    
    if open_braces != close_braces:
        print(f"❌ Unbalanced braces: {open_braces} open, {close_braces} close")
        return False
    
    # Check for balanced parentheses in function definitions
    function_pattern = r'function\s+\w+\s*\([^)]*\)\s*{'
    functions = re.findall(function_pattern, js_content)
    
    if len(functions) < 5:  # Should have at least 5 functions
        print(f"❌ Not enough functions found: {len(functions)}")
        return False
    
    print("✅ JavaScript syntax appears to be valid")
    return True

if __name__ == '__main__':
    print("Testing Task 6: Frontend Time Input Implementation")
    print("=" * 60)
    
    try:
        frontend_ok = test_frontend_implementation()
        syntax_ok = test_javascript_syntax()
        
        if frontend_ok and syntax_ok:
            print("\n🎉 Task 6 implementation is complete and correct!")
            exit(0)
        else:
            print("\n❌ Task 6 implementation needs fixes.")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)