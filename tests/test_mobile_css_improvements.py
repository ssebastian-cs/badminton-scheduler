#!/usr/bin/env python3
"""
Mobile CSS and JavaScript improvements tests.
Tests mobile responsiveness without requiring Selenium.
"""

import pytest
import os
import re
from pathlib import Path
from app import create_app


class TestMobileCSSImprovements:
    """Test mobile CSS improvements and responsiveness"""
    
    def test_bootstrap_custom_css_mobile_optimizations(self):
        """Test that bootstrap-custom.css contains mobile optimizations"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        assert css_file.exists(), "bootstrap-custom.css file should exist"
        
        content = css_file.read_text(encoding='utf-8')
        
        # Check for mobile media queries
        mobile_queries = [
            "@media (max-width: 768px)",
            "@media (min-width: 768px) and (max-width: 1024px)",
            "@media (hover: none) and (pointer: coarse)"
        ]
        
        for query in mobile_queries:
            assert query in content, f"Mobile media query missing: {query}"
        
        # Check for mobile-specific classes
        mobile_classes = [
            ".btn-mobile",
            ".form-control-mobile",
            ".mobile-card",
            ".touch-target"
        ]
        
        for css_class in mobile_classes:
            assert css_class in content, f"Mobile CSS class missing: {css_class}"
        
        # Check for touch-friendly sizing
        assert "min-height: 44px" in content, "Touch-friendly minimum height missing"
        assert "font-size: 16px" in content, "iOS zoom prevention font size missing"
        assert "touch-action: manipulation" in content, "Touch action optimization missing"
    
    def test_mobile_javascript_functionality(self):
        """Test that mobile.js contains required functionality"""
        js_file = Path("app/static/js/mobile.js")
        assert js_file.exists(), "mobile.js file should exist"
        
        content = js_file.read_text(encoding='utf-8')
        
        # Check for mobile initialization functions
        mobile_functions = [
            "initializeMobileMenu",
            "initializeTouchInteractions",
            "initializeMobileFormEnhancements",
            "initializeSwipeGestures",
            "initializeMobileViewport"
        ]
        
        for function in mobile_functions:
            assert function in content, f"Mobile function missing: {function}"
        
        # Check for enhanced swipe functionality
        swipe_functions = [
            "showSwipeActionHint",
            "clearSwipeActionHints",
            "showSwipeConfirmation"
        ]
        
        for function in swipe_functions:
            assert function in content, f"Swipe function missing: {function}"
        
        # Check for viewport handling
        viewport_functions = [
            "adjustLayoutForKeyboard",
            "scrollToFocusedElement",
            "updateViewportMetaTag"
        ]
        
        for function in viewport_functions:
            assert function in content, f"Viewport function missing: {function}"
    
    def test_base_template_mobile_meta_tags(self):
        """Test that base template has proper mobile meta tags"""
        template_file = Path("app/templates/base_bootstrap.html")
        assert template_file.exists(), "base_bootstrap.html template should exist"
        
        content = template_file.read_text(encoding='utf-8')
        
        # Check for viewport meta tag
        assert 'name="viewport"' in content, "Viewport meta tag missing"
        assert 'width=device-width' in content, "Device width viewport setting missing"
        assert 'initial-scale=1.0' in content, "Initial scale viewport setting missing"
        
        # Check for mobile JavaScript inclusion
        assert 'mobile.js' in content, "Mobile JavaScript not included"
        
        # Check for responsive navigation
        assert 'navbar-toggler' in content, "Mobile navigation toggle missing"
        assert 'navbar-collapse' in content, "Collapsible navigation missing"
    
    def test_mobile_responsive_navigation(self):
        """Test mobile responsive navigation elements"""
        template_file = Path("app/templates/base_bootstrap.html")
        content = template_file.read_text(encoding='utf-8')
        
        # Check for responsive brand text
        assert 'd-none d-sm-inline' in content, "Responsive brand text (full) missing"
        assert 'd-sm-none' in content, "Responsive brand text (short) missing"
        
        # Check for mobile menu structure
        assert 'data-bs-toggle="collapse"' in content, "Bootstrap collapse toggle missing"
        assert 'data-bs-target="#navbarNav"' in content, "Navigation target missing"
        
        # Check for responsive user info
        assert 'd-none d-md-inline' in content, "Responsive user info missing"
    
    def test_dashboard_mobile_layout(self):
        """Test dashboard mobile layout improvements"""
        template_file = Path("app/templates/dashboard_bootstrap.html")
        assert template_file.exists(), "dashboard_bootstrap.html template should exist"
        
        content = template_file.read_text(encoding='utf-8')
        
        # Check for mobile/desktop layout separation
        assert 'd-lg-none' in content, "Mobile-only layout missing"
        assert 'd-none d-lg-block' in content, "Desktop-only layout missing"
        
        # Check for responsive button layout
        assert 'flex-column flex-md-row' in content, "Responsive button stacking missing"
        
        # Check for mobile card classes
        assert 'mobile-card' in content, "Mobile card class missing"
        
        # Check for responsive grid
        assert 'col-12' in content, "Full-width mobile columns missing"
    
    def test_form_mobile_optimizations(self):
        """Test form mobile optimizations"""
        login_template = Path("app/templates/auth/login_bootstrap.html")
        assert login_template.exists(), "login_bootstrap.html template should exist"
        
        content = login_template.read_text(encoding='utf-8')
        
        # Check for mobile-friendly form classes
        assert 'form-control-mobile' in content, "Mobile form control class missing"
        assert 'btn-mobile' in content, "Mobile button class missing"
        
        # Check for responsive form layout
        assert 'col-12 col-md-6 col-lg-4' in content, "Responsive form container missing"
    
    def test_css_media_query_coverage(self):
        """Test CSS media query coverage for different screen sizes"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Extract all media queries
        media_queries = re.findall(r'@media[^{]+{', content)
        
        # Should have queries for different screen sizes
        breakpoints = ['768px', '1024px']
        
        for breakpoint in breakpoints:
            found = any(breakpoint in query for query in media_queries)
            assert found, f"Media query for {breakpoint} breakpoint missing"
        
        # Check for touch device queries
        touch_queries = [
            'hover: none',
            'pointer: coarse'
        ]
        
        for touch_query in touch_queries:
            assert touch_query in content, f"Touch device query missing: {touch_query}"
    
    def test_accessibility_improvements(self):
        """Test accessibility improvements in CSS"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Check for high contrast support
        assert 'prefers-contrast: high' in content, "High contrast media query missing"
        
        # Check for reduced motion support
        assert 'prefers-reduced-motion: reduce' in content, "Reduced motion media query missing"
        
        # Check for focus indicators
        assert 'box-shadow' in content, "Focus indicators missing"
        
        # Check for safe area support
        assert 'env(safe-area-inset' in content, "Safe area inset support missing"


class TestMobileJavaScriptFeatures:
    """Test mobile JavaScript features and functionality"""
    
    def test_mobile_menu_functionality(self):
        """Test mobile menu JavaScript functionality"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for menu initialization
        assert 'initializeMobileMenu' in content
        assert 'navbar-toggler' in content
        assert 'navbar-collapse' in content
        
        # Check for touch feedback
        assert 'touchstart' in content
        assert 'touchend' in content
        assert 'transform' in content
    
    def test_touch_interaction_enhancements(self):
        """Test touch interaction enhancements"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for touch event handling
        touch_events = ['touchstart', 'touchmove', 'touchend', 'touchcancel']
        
        for event in touch_events:
            assert event in content, f"Touch event missing: {event}"
        
        # Check for ripple effect
        assert 'createRippleEffect' in content
        assert 'ripple' in content
        
        # Check for touch feedback
        assert 'scale(0.98)' in content or 'scale(0.95)' in content
    
    def test_swipe_gesture_implementation(self):
        """Test swipe gesture implementation"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for swipe detection
        assert 'startX' in content and 'startY' in content
        assert 'currentX' in content and 'currentY' in content
        assert 'deltaX' in content and 'deltaY' in content
        
        # Check for swipe actions
        assert 'swipeThreshold' in content
        assert 'velocityThreshold' in content
        
        # Check for swipe feedback
        assert 'showSwipeActionHint' in content
        assert 'showSwipeConfirmation' in content
    
    def test_form_enhancements(self):
        """Test mobile form enhancements"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for iOS zoom prevention
        assert 'fontSize' in content
        assert '16px' in content
        
        # Check for keyboard handling
        assert 'virtual keyboard' in content.lower() or 'keyboard' in content
        assert 'scrollIntoView' in content
        
        # Check for form validation enhancements
        assert 'invalid' in content
        assert 'checkValidity' in content
    
    def test_viewport_handling(self):
        """Test viewport and orientation handling"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for viewport management
        assert 'initializeMobileViewport' in content
        assert 'orientationchange' in content
        assert 'resize' in content
        
        # Check for keyboard detection
        assert 'keyboard-open' in content
        assert 'heightDifference' in content
        
        # Check for safe area support
        assert 'safe-area-inset' in content


class TestMobileTemplateImprovements:
    """Test mobile template improvements"""
    
    def test_responsive_grid_classes(self):
        """Test responsive grid classes in templates"""
        templates_to_check = [
            "app/templates/dashboard_bootstrap.html",
            "app/templates/auth/login_bootstrap.html",
            "app/templates/availability/add_bootstrap.html"
        ]
        
        for template_path in templates_to_check:
            template_file = Path(template_path)
            if template_file.exists():
                content = template_file.read_text(encoding='utf-8')
                
                # Check for responsive column classes
                responsive_classes = ['col-12', 'col-md-', 'col-lg-']
                
                found_responsive = any(cls in content for cls in responsive_classes)
                assert found_responsive, f"Responsive grid classes missing in {template_path}"
    
    def test_mobile_button_classes(self):
        """Test mobile button classes in templates"""
        templates_to_check = [
            "app/templates/auth/login_bootstrap.html",
            "app/templates/dashboard_bootstrap.html"
        ]
        
        for template_path in templates_to_check:
            template_file = Path(template_path)
            if template_file.exists():
                content = template_file.read_text(encoding='utf-8')
                
                # Check for mobile button classes
                if 'btn' in content:
                    assert 'btn-mobile' in content, f"Mobile button class missing in {template_path}"
    
    def test_responsive_navigation_elements(self):
        """Test responsive navigation elements"""
        base_template = Path("app/templates/base_bootstrap.html")
        content = base_template.read_text(encoding='utf-8')
        
        # Check for responsive visibility classes that should be in base template
        responsive_visibility = [
            'd-none d-sm-inline',  # Full brand text
            'd-sm-none',           # Short brand text
            'd-none d-md-inline'   # User info text
        ]
        
        for visibility_class in responsive_visibility:
            assert visibility_class in content, f"Responsive visibility class missing: {visibility_class}"
        
        # Check for Bootstrap responsive navigation classes
        bootstrap_nav_classes = [
            'navbar-expand-lg',
            'navbar-toggler',
            'collapse navbar-collapse'
        ]
        
        for nav_class in bootstrap_nav_classes:
            assert nav_class in content, f"Bootstrap navigation class missing: {nav_class}"


class TestMobilePerformanceOptimizations:
    """Test mobile performance optimizations"""
    
    def test_css_optimizations(self):
        """Test CSS performance optimizations"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Check for hardware acceleration hints
        assert 'transform' in content, "Hardware acceleration transforms missing"
        
        # Check for efficient animations
        assert 'transition' in content, "CSS transitions missing"
        
        # Check for will-change optimizations (if any)
        # This is optional but good for performance
    
    def test_javascript_performance(self):
        """Test JavaScript performance optimizations"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Check for passive event listeners
        assert 'passive: true' in content, "Passive event listeners missing"
        
        # Check for requestAnimationFrame usage
        assert 'requestAnimationFrame' in content, "requestAnimationFrame optimization missing"
        
        # Check for debouncing/throttling (basic check)
        assert 'setTimeout' in content, "Event throttling mechanisms missing"
    
    def test_resource_loading_optimizations(self):
        """Test resource loading optimizations"""
        base_template = Path("app/templates/base_bootstrap.html")
        content = base_template.read_text(encoding='utf-8')
        
        # Check for proper script loading
        assert 'mobile.js' in content, "Mobile JavaScript not loaded"
        
        # Check for CSS loading
        assert 'bootstrap-custom.css' in content, "Custom CSS not loaded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])