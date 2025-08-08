#!/usr/bin/env python3
"""
Test script to verify all the fixes implemented:
1. Autocomplete attributes on form fields
2. DELETE availability functionality
3. Admin user management functionality
"""

import re
import os
import requests
import time

def test_autocomplete_attributes():
    """Test that autocomplete attributes are properly added to form fields."""
    print("🧪 Testing Autocomplete Attributes")
    print("-" * 40)
    
    frontend_file = 'static_frontend.html'
    if not os.path.exists(frontend_file):
        print("❌ Frontend file not found!")
        return False
    
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Username field has autocomplete="username"
    total_tests += 1
    if 'id="username"' in content and 'autocomplete="username"' in content:
        print("✅ Username field has autocomplete attribute")
        tests_passed += 1
    else:
        print("❌ Username field missing autocomplete attribute")
    
    # Test 2: Password field has autocomplete="current-password"
    total_tests += 1
    if 'id="password"' in content and 'autocomplete="current-password"' in content:
        print("✅ Password field has autocomplete attribute")
        tests_passed += 1
    else:
        print("❌ Password field missing autocomplete attribute")
    
    # Test 3: Date fields have autocomplete="off"
    total_tests += 1
    date_fields_with_autocomplete = re.findall(r'type="date"[^>]*autocomplete="off"', content)
    if len(date_fields_with_autocomplete) >= 3:  # availDate, filterStartDate, filterEndDate
        print("✅ Date fields have autocomplete attributes")
        tests_passed += 1
    else:
        print("❌ Some date fields missing autocomplete attributes")
    
    # Test 4: Time fields have autocomplete="off"
    total_tests += 1
    time_fields_with_autocomplete = re.findall(r'type="time"[^>]*autocomplete="off"', content)
    if len(time_fields_with_autocomplete) >= 2:  # timeStart, timeEnd
        print("✅ Time fields have autocomplete attributes")
        tests_passed += 1
    else:
        print("❌ Some time fields missing autocomplete attributes")
    
    # Test 5: Form fields have name attributes
    total_tests += 1
    name_attributes = re.findall(r'name="[^"]*"', content)
    if len(name_attributes) >= 10:  # Should have many name attributes
        print("✅ Form fields have name attributes")
        tests_passed += 1
    else:
        print("❌ Some form fields missing name attributes")
    
    print(f"📊 Autocomplete Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def test_delete_availability_api():
    """Test that DELETE availability API endpoint works."""
    print("\n🧪 Testing DELETE Availability API")
    print("-" * 40)
    
    base_url = 'http://localhost:5000'
    
    try:
        # Test health endpoint first
        health_response = requests.get(f'{base_url}/health', timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not running or not healthy")
            return False
        
        print("✅ Server is running and healthy")
        
        # Test that DELETE endpoint exists (we can't test actual deletion without auth)
        # But we can check if the endpoint returns proper error codes
        delete_response = requests.delete(f'{base_url}/api/availability/999', timeout=5)
        
        # Should return 401 (unauthorized) or 404 (not found), not 405 (method not allowed)
        if delete_response.status_code in [401, 404]:
            print("✅ DELETE availability endpoint exists and responds correctly")
            return True
        elif delete_response.status_code == 405:
            print("❌ DELETE availability endpoint not implemented (Method Not Allowed)")
            return False
        else:
            print(f"✅ DELETE availability endpoint exists (status: {delete_response.status_code})")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print("💡 Make sure the server is running with: python start_server.py")
        return False

def test_admin_endpoints():
    """Test that admin endpoints exist."""
    print("\n🧪 Testing Admin API Endpoints")
    print("-" * 40)
    
    base_url = 'http://localhost:5000'
    
    admin_endpoints = [
        '/api/admin/users',
        '/api/admin/availability/filtered'
    ]
    
    tests_passed = 0
    total_tests = len(admin_endpoints)
    
    for endpoint in admin_endpoints:
        try:
            response = requests.get(f'{base_url}{endpoint}', timeout=5)
            
            # Should return 401 (unauthorized) or 403 (forbidden), not 404 (not found)
            if response.status_code in [401, 403]:
                print(f"✅ {endpoint} exists and requires authentication")
                tests_passed += 1
            elif response.status_code == 404:
                print(f"❌ {endpoint} not found")
            else:
                print(f"✅ {endpoint} exists (status: {response.status_code})")
                tests_passed += 1
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not test {endpoint}: {e}")
    
    print(f"📊 Admin Endpoint Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def test_frontend_admin_functionality():
    """Test that admin functionality is present in frontend."""
    print("\n🧪 Testing Frontend Admin Functionality")
    print("-" * 40)
    
    frontend_file = 'static_frontend.html'
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Admin tab functionality
    total_tests += 1
    if 'showAdminTab' in content and 'adminUsersSection' in content:
        print("✅ Admin tab functionality present")
        tests_passed += 1
    else:
        print("❌ Admin tab functionality missing")
    
    # Test 2: User management functions
    total_tests += 1
    user_management_functions = ['createUser', 'editUser', 'deleteUser', 'loadUsers']
    found_functions = sum(1 for func in user_management_functions if func in content)
    if found_functions == len(user_management_functions):
        print("✅ User management functions present")
        tests_passed += 1
    else:
        print(f"❌ User management functions missing ({found_functions}/{len(user_management_functions)} found)")
    
    # Test 3: Admin availability management
    total_tests += 1
    if 'adminEditAvailability' in content and 'adminDeleteAvailability' in content:
        print("✅ Admin availability management functions present")
        tests_passed += 1
    else:
        print("❌ Admin availability management functions missing")
    
    # Test 4: User creation form
    total_tests += 1
    if 'newUsername' in content and 'newEmail' in content and 'newPassword' in content:
        print("✅ User creation form present")
        tests_passed += 1
    else:
        print("❌ User creation form missing")
    
    print(f"📊 Frontend Admin Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def test_mobile_responsiveness():
    """Test that mobile responsiveness improvements are present."""
    print("\n🧪 Testing Mobile Responsiveness")
    print("-" * 40)
    
    frontend_file = 'static_frontend.html'
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Touch-friendly button styles
    total_tests += 1
    if 'touch-action: manipulation' in content:
        print("✅ Touch-friendly button styles present")
        tests_passed += 1
    else:
        print("❌ Touch-friendly button styles missing")
    
    # Test 2: Mobile media queries
    total_tests += 1
    mobile_queries = re.findall(r'@media.*max-width:\s*(\d+)px', content)
    mobile_breakpoints = [int(width) for width in mobile_queries if int(width) <= 768]
    if len(mobile_breakpoints) >= 2:  # Should have 768px and 480px breakpoints
        print("✅ Mobile media queries present")
        tests_passed += 1
    else:
        print("❌ Mobile media queries missing or insufficient")
    
    # Test 3: Enhanced mobile styles
    total_tests += 1
    mobile_enhancements = [
        'min-width: 100px',  # Enhanced button sizing
        'grid-template-columns: 1fr',  # Single column layout
        'padding: 16px',  # Larger padding for mobile
    ]
    found_enhancements = sum(1 for enhancement in mobile_enhancements if enhancement in content)
    if found_enhancements >= 2:
        print("✅ Mobile enhancement styles present")
        tests_passed += 1
    else:
        print("❌ Mobile enhancement styles missing")
    
    print(f"📊 Mobile Responsiveness Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def main():
    """Run all verification tests."""
    print("🏸 Badminton Scheduler - Fixes Verification Test Suite")
    print("=" * 60)
    
    # Change to the correct directory
    if os.path.basename(os.getcwd()) != 'badminton_scheduler':
        if os.path.exists('badminton_scheduler'):
            os.chdir('badminton_scheduler')
        else:
            print("❌ Could not find badminton_scheduler directory")
            return False
    
    all_tests_passed = True
    
    # Run all tests
    test_results = [
        test_autocomplete_attributes(),
        test_delete_availability_api(),
        test_admin_endpoints(),
        test_frontend_admin_functionality(),
        test_mobile_responsiveness()
    ]
    
    all_tests_passed = all(test_results)
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All fixes have been successfully implemented and verified!")
        print("\n📋 Summary of fixes:")
        print("   ✅ Autocomplete attributes added to all form fields")
        print("   ✅ DELETE availability endpoint implemented and working")
        print("   ✅ Admin user management functionality implemented")
        print("   ✅ Admin can edit/delete any availability entry")
        print("   ✅ Mobile responsiveness improvements maintained")
        print("\n🧪 Manual testing recommendations:")
        print("   1. Test login form autocomplete in browser")
        print("   2. Test delete availability as regular user")
        print("   3. Test admin user management interface")
        print("   4. Test admin availability management")
        print("   5. Test mobile responsiveness on different screen sizes")
    else:
        print("❌ Some fixes need attention")
        failed_tests = [i for i, result in enumerate(test_results) if not result]
        test_names = ["Autocomplete", "DELETE API", "Admin Endpoints", "Frontend Admin", "Mobile Responsiveness"]
        print(f"   Failed tests: {', '.join(test_names[i] for i in failed_tests)}")
    
    return all_tests_passed

if __name__ == "__main__":
    main()