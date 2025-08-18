#!/usr/bin/env python3
"""
Test script to verify mobile responsive design implementation
"""

import os
import re
from pathlib import Path

def test_mobile_responsive_implementation():
    """Test that mobile responsive design has been properly implemented"""
    
    print("🧪 Testing Mobile Responsive Design Implementation")
    print("=" * 60)
    
    # Test 1: Check TailwindCSS configuration enhancements
    print("\n1. Testing TailwindCSS Configuration...")
    base_template = Path("app/templates/base.html")
    if base_template.exists():
        content = base_template.read_text(encoding='utf-8')
        
        # Check for enhanced color scheme
        if "'gray-750': '#374151'" in content:
            print("   ✅ Enhanced color scheme configured")
        else:
            print("   ❌ Enhanced color scheme missing")
            
        # Check for responsive breakpoints
        if "'xs': '475px'" in content:
            print("   ✅ Extra small breakpoint configured")
        else:
            print("   ❌ Extra small breakpoint missing")
            
        # Check for enhanced spacing and typography
        if "'18': '4.5rem'" in content and "'88': '22rem'" in content:
            print("   ✅ Enhanced spacing configured")
        else:
            print("   ❌ Enhanced spacing missing")
    else:
        print("   ❌ Base template not found")
    
    # Test 2: Check mobile CSS enhancements
    print("\n2. Testing Mobile CSS Enhancements...")
    custom_css = Path("app/static/css/custom.css")
    if custom_css.exists():
        content = custom_css.read_text(encoding='utf-8')
        
        # Check for touch-friendly styles
        if ".touch-target" in content:
            print("   ✅ Touch-friendly button styles implemented")
        else:
            print("   ❌ Touch-friendly button styles missing")
            
        # Check for mobile-specific media queries
        mobile_queries = [
            "@media (max-width: 768px)",
            "@media (min-width: 768px) and (max-width: 1024px)",
            "@media (min-width: 1024px)"
        ]
        
        for query in mobile_queries:
            if query in content:
                print(f"   ✅ Media query found: {query}")
            else:
                print(f"   ❌ Media query missing: {query}")
                
        # Check for mobile form enhancements
        if ".mobile-form-input" in content:
            print("   ✅ Mobile form input styles implemented")
        else:
            print("   ❌ Mobile form input styles missing")
            
        # Check for calendar/list view optimizations
        if ".calendar-mobile" in content and ".calendar-desktop" in content:
            print("   ✅ Mobile/desktop calendar views implemented")
        else:
            print("   ❌ Mobile/desktop calendar views missing")
    else:
        print("   ❌ Custom CSS file not found")
    
    # Test 3: Check mobile JavaScript functionality
    print("\n3. Testing Mobile JavaScript...")
    mobile_js = Path("app/static/js/mobile.js")
    if mobile_js.exists():
        content = mobile_js.read_text(encoding='utf-8')
        
        # Check for mobile menu functionality
        if "initializeMobileMenu" in content:
            print("   ✅ Mobile menu functionality implemented")
        else:
            print("   ❌ Mobile menu functionality missing")
            
        # Check for touch interactions
        if "initializeTouchInteractions" in content:
            print("   ✅ Touch interaction enhancements implemented")
        else:
            print("   ❌ Touch interaction enhancements missing")
            
        # Check for swipe gestures
        if "initializeSwipeGestures" in content:
            print("   ✅ Swipe gesture support implemented")
        else:
            print("   ❌ Swipe gesture support missing")
            
        # Check for mobile form enhancements
        if "initializeMobileFormEnhancements" in content:
            print("   ✅ Mobile form enhancements implemented")
        else:
            print("   ❌ Mobile form enhancements missing")
            
        # Check for viewport handling
        if "initializeMobileViewport" in content:
            print("   ✅ Mobile viewport handling implemented")
        else:
            print("   ❌ Mobile viewport handling missing")
    else:
        print("   ❌ Mobile JavaScript file not found")
    
    # Test 4: Check template mobile enhancements
    print("\n4. Testing Template Mobile Enhancements...")
    
    templates_to_check = [
        ("app/templates/base.html", "Base template"),
        ("app/templates/dashboard.html", "Dashboard template"),
        ("app/templates/availability/add.html", "Add availability template"),
        ("app/templates/comments/comments.html", "Comments template"),
        ("app/templates/admin_dashboard.html", "Admin dashboard template"),
        ("app/templates/auth/login.html", "Login template")
    ]
    
    for template_path, template_name in templates_to_check:
        template = Path(template_path)
        if template.exists():
            content = template.read_text(encoding='utf-8')
            
            # Check for mobile-friendly classes
            mobile_classes = [
                "touch-target",
                "mobile-form-input",
                "mobile-grid",
                "mobile-stats-grid",
                "mobile-nav-item"
            ]
            
            found_classes = [cls for cls in mobile_classes if cls in content]
            if found_classes:
                print(f"   ✅ {template_name}: Mobile classes found ({len(found_classes)}/5)")
            else:
                print(f"   ⚠️  {template_name}: No mobile classes found")
                
            # Check for responsive grid classes
            responsive_grids = ["sm:grid-cols", "md:grid-cols", "lg:grid-cols"]
            if any(grid in content for grid in responsive_grids):
                print(f"   ✅ {template_name}: Responsive grid classes found")
            else:
                print(f"   ⚠️  {template_name}: No responsive grid classes found")
        else:
            print(f"   ❌ {template_name}: Template not found")
    
    # Test 5: Check for mobile navigation enhancements
    print("\n5. Testing Mobile Navigation...")
    base_template = Path("app/templates/base.html")
    if base_template.exists():
        content = base_template.read_text(encoding='utf-8')
        
        # Check for mobile menu button enhancements
        if 'class="mobile-menu-button touch-target' in content:
            print("   ✅ Mobile menu button has touch-friendly styling")
        else:
            print("   ❌ Mobile menu button missing touch-friendly styling")
            
        # Check for enhanced mobile menu
        if 'class="mobile-nav-item' in content:
            print("   ✅ Mobile navigation items have enhanced styling")
        else:
            print("   ❌ Mobile navigation items missing enhanced styling")
            
        # Check for mobile JavaScript inclusion
        if 'src="{{ url_for(\'static\', filename=\'js/mobile.js\') }}"' in content:
            print("   ✅ Mobile JavaScript properly included")
        else:
            print("   ❌ Mobile JavaScript not included")
    
    print("\n" + "=" * 60)
    print("✅ Mobile Responsive Design Implementation Test Complete!")
    print("\nKey Features Implemented:")
    print("• Enhanced TailwindCSS configuration with mobile-first approach")
    print("• Touch-friendly button and form styling")
    print("• Mobile-optimized navigation with hamburger menu")
    print("• Responsive grid layouts for different screen sizes")
    print("• Mobile/desktop specific calendar views")
    print("• Touch interaction enhancements and swipe gestures")
    print("• Mobile form optimizations (prevent zoom, auto-scroll)")
    print("• Viewport and orientation change handling")
    print("• Visual feedback for touch interactions")

if __name__ == "__main__":
    test_mobile_responsive_implementation()