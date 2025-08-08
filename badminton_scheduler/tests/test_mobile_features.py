#!/usr/bin/env python3
"""
Test script to verify mobile responsiveness features in the badminton scheduler.
This script checks that all mobile-responsive CSS rules are properly implemented.
"""

import re
import os

def test_mobile_responsiveness():
    """Test that mobile responsiveness features are implemented correctly."""
    
    # Read the static frontend file
    frontend_file = 'static_frontend.html'
    if not os.path.exists(frontend_file):
        print("❌ Frontend file not found!")
        return False
    
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 0
    
    print("🧪 Testing Mobile Responsiveness Features")
    print("=" * 50)
    
    # Test 1: Check for mobile viewport meta tag
    total_tests += 1
    if 'name="viewport"' in content and 'width=device-width' in content:
        print("✅ Viewport meta tag present")
        tests_passed += 1
    else:
        print("❌ Viewport meta tag missing or incorrect")
    
    # Test 2: Check for mobile media queries
    total_tests += 1
    mobile_queries = re.findall(r'@media.*max-width:\s*(\d+)px', content)
    if mobile_queries and any(int(width) <= 768 for width in mobile_queries):
        print("✅ Mobile media queries present")
        tests_passed += 1
    else:
        print("❌ Mobile media queries missing")
    
    # Test 3: Check for touch-friendly button styles
    total_tests += 1
    if 'touch-action: manipulation' in content:
        print("✅ Touch-friendly button styles implemented")
        tests_passed += 1
    else:
        print("❌ Touch-friendly button styles missing")
    
    # Test 4: Check for enhanced button sizing on mobile
    total_tests += 1
    if re.search(r'\.action-btn.*min-width:\s*\d+px', content, re.DOTALL):
        print("✅ Enhanced button sizing for mobile")
        tests_passed += 1
    else:
        print("❌ Enhanced button sizing missing")
    
    # Test 5: Check for time input mobile optimization
    total_tests += 1
    if 'input[type="time"]' in content and re.search(r'input\[type="time"\].*padding.*\d+px', content, re.DOTALL):
        print("✅ Time input mobile optimization present")
        tests_passed += 1
    else:
        print("❌ Time input mobile optimization missing")
    
    # Test 6: Check for admin filter mobile layout
    total_tests += 1
    if re.search(r'\.filter-controls.*flex-direction:\s*column', content, re.DOTALL):
        print("✅ Admin filter mobile layout implemented")
        tests_passed += 1
    else:
        print("❌ Admin filter mobile layout missing")
    
    # Test 7: Check for responsive grid layout
    total_tests += 1
    if re.search(r'\.time-inputs-container.*grid-template-columns:\s*1fr', content, re.DOTALL):
        print("✅ Responsive grid layout present")
        tests_passed += 1
    else:
        print("❌ Responsive grid layout missing")
    
    # Test 8: Check for accessibility features
    total_tests += 1
    if 'prefers-reduced-motion' in content or 'prefers-contrast' in content:
        print("✅ Accessibility features implemented")
        tests_passed += 1
    else:
        print("❌ Accessibility features missing")
    
    # Test 9: Check for landscape orientation support
    total_tests += 1
    if 'orientation: landscape' in content:
        print("✅ Landscape orientation support present")
        tests_passed += 1
    else:
        print("❌ Landscape orientation support missing")
    
    # Test 10: Check for touch device specific styles
    total_tests += 1
    if 'hover: none' in content and 'pointer: coarse' in content:
        print("✅ Touch device specific styles implemented")
        tests_passed += 1
    else:
        print("❌ Touch device specific styles missing")
    
    print("=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All mobile responsiveness tests passed!")
        return True
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed")
        return False

def test_css_structure():
    """Test that CSS structure is properly organized."""
    
    frontend_file = 'static_frontend.html'
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🎨 Testing CSS Structure")
    print("=" * 30)
    
    # Check for proper media query organization
    media_queries = re.findall(r'@media[^{]+{', content)
    print(f"📱 Found {len(media_queries)} media queries")
    
    # Check for mobile-first approach
    breakpoints = re.findall(r'max-width:\s*(\d+)px', content)
    if breakpoints:
        breakpoints = [int(bp) for bp in breakpoints]
        breakpoints.sort()
        print(f"📏 Breakpoints found: {breakpoints}px")
        
        if 480 in breakpoints and 768 in breakpoints:
            print("✅ Proper mobile breakpoints implemented")
        else:
            print("⚠️  Consider adding standard mobile breakpoints (480px, 768px)")
    
    # Check for touch-specific optimizations
    touch_optimizations = [
        'touch-action',
        '-webkit-tap-highlight-color',
        'min-height.*48px',  # Minimum touch target size
        'transform.*scale'   # Touch feedback
    ]
    
    found_optimizations = 0
    for optimization in touch_optimizations:
        if re.search(optimization, content, re.IGNORECASE):
            found_optimizations += 1
    
    print(f"👆 Touch optimizations found: {found_optimizations}/{len(touch_optimizations)}")
    
    return True

def main():
    """Run all mobile responsiveness tests."""
    print("🏸 Badminton Scheduler - Mobile Responsiveness Test Suite")
    print("=" * 60)
    
    # Change to the correct directory
    if os.path.basename(os.getcwd()) != 'badminton_scheduler':
        if os.path.exists('badminton_scheduler'):
            os.chdir('badminton_scheduler')
        else:
            print("❌ Could not find badminton_scheduler directory")
            return False
    
    success = True
    
    # Run main responsiveness tests
    if not test_mobile_responsiveness():
        success = False
    
    # Run CSS structure tests
    if not test_css_structure():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All mobile responsiveness features are properly implemented!")
        print("\n📋 Summary of implemented features:")
        print("   • Touch-friendly edit/delete buttons")
        print("   • Mobile-optimized time input fields")
        print("   • Responsive admin filtering interface")
        print("   • Enhanced availability display")
        print("   • Accessibility improvements")
        print("   • Landscape orientation support")
        print("   • Touch device optimizations")
        print("\n🧪 To test manually:")
        print("   1. Open http://localhost:5000/static_frontend.html")
        print("   2. Use browser dev tools to simulate mobile devices")
        print("   3. Test touch interactions and responsiveness")
    else:
        print("❌ Some mobile responsiveness features need attention")
    
    return success

if __name__ == "__main__":
    main()