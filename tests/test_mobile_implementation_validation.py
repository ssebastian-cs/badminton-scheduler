#!/usr/bin/env python3
"""
Mobile implementation validation tests.
Validates that mobile responsiveness features are properly implemented.
"""

import pytest
import os
import re
from pathlib import Path
from app import create_app, db
from app.models import User, Availability
from datetime import datetime, date, time as dt_time


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Create test users
        admin_user = User(
            username='admin_test',
            password='test123',
            role='Admin'
        )
        regular_user = User(
            username='user_test',
            password='test123',
            role='User'
        )
        
        db.session.add(admin_user)
        db.session.add(regular_user)
        db.session.commit()
        
        yield app
        
        db.drop_all()


class TestMobileImplementationValidation:
    """Validate mobile implementation completeness"""
    
    def test_mobile_css_implementation_complete(self):
        """Test that mobile CSS implementation is complete"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        assert css_file.exists(), "Bootstrap custom CSS file should exist"
        
        content = css_file.read_text(encoding='utf-8')
        
        # Required mobile features
        required_features = [
            # Media queries
            "@media (max-width: 768px)",
            "@media (min-width: 768px) and (max-width: 1024px)",
            "@media (hover: none) and (pointer: coarse)",
            
            # Mobile classes
            ".btn-mobile",
            ".form-control-mobile",
            ".mobile-card",
            ".touch-target",
            
            # Touch optimizations
            "min-height: 44px",
            "font-size: 16px",
            "touch-action: manipulation",
            
            # Accessibility
            "prefers-contrast: high",
            "prefers-reduced-motion: reduce",
            
            # Safe area support
            "env(safe-area-inset"
        ]
        
        for feature in required_features:
            assert feature in content, f"Required mobile CSS feature missing: {feature}"
        
        print("✅ Mobile CSS implementation complete")
    
    def test_mobile_javascript_implementation_complete(self):
        """Test that mobile JavaScript implementation is complete"""
        js_file = Path("app/static/js/mobile.js")
        assert js_file.exists(), "Mobile JavaScript file should exist"
        
        content = js_file.read_text(encoding='utf-8')
        
        # Required JavaScript features
        required_features = [
            # Core functions
            "initializeMobileMenu",
            "initializeTouchInteractions",
            "initializeMobileFormEnhancements",
            "initializeSwipeGestures",
            "initializeMobileViewport",
            
            # Touch events
            "touchstart",
            "touchmove",
            "touchend",
            "touchcancel",
            
            # Swipe functionality
            "showSwipeActionHint",
            "clearSwipeActionHints",
            "showSwipeConfirmation",
            
            # Viewport handling
            "adjustLayoutForKeyboard",
            "scrollToFocusedElement",
            "updateViewportMetaTag",
            
            # Performance optimizations
            "passive: true",
            "requestAnimationFrame"
        ]
        
        for feature in required_features:
            assert feature in content, f"Required mobile JavaScript feature missing: {feature}"
        
        print("✅ Mobile JavaScript implementation complete")
    
    def test_mobile_template_implementation_complete(self):
        """Test that mobile template implementation is complete"""
        templates_to_check = [
            ("app/templates/base_bootstrap.html", [
                'name="viewport"',
                'width=device-width',
                'initial-scale=1.0',
                'navbar-toggler',
                'navbar-collapse',
                'd-none d-sm-inline',
                'd-sm-none',
                'mobile.js'
            ]),
            ("app/templates/dashboard_bootstrap.html", [
                'd-lg-none',
                'd-none d-lg-block',
                'flex-column flex-md-row',
                'mobile-card',
                'col-12'
            ]),
            ("app/templates/auth/login_bootstrap.html", [
                'form-control-mobile',
                'btn-mobile',
                'col-12 col-md-6 col-lg-4'
            ])
        ]
        
        for template_path, required_features in templates_to_check:
            template_file = Path(template_path)
            if template_file.exists():
                content = template_file.read_text(encoding='utf-8')
                
                for feature in required_features:
                    assert feature in content, f"Required mobile template feature missing in {template_path}: {feature}"
        
        print("✅ Mobile template implementation complete")
    
    def test_mobile_responsiveness_coverage(self):
        """Test mobile responsiveness coverage across breakpoints"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Check breakpoint coverage
        breakpoints = {
            '768px': 'Mobile breakpoint',
            '1024px': 'Tablet breakpoint'
        }
        
        for breakpoint, description in breakpoints.items():
            assert breakpoint in content, f"{description} ({breakpoint}) not found in CSS"
        
        # Check responsive utilities
        responsive_utilities = [
            'col-12',  # Full width on mobile
            'col-md-',  # Medium breakpoint
            'col-lg-',  # Large breakpoint
            'd-none',   # Hide elements
            'd-sm-',    # Small breakpoint visibility
            'd-md-',    # Medium breakpoint visibility
            'd-lg-'     # Large breakpoint visibility
        ]
        
        # Check templates for responsive utilities
        template_files = [
            "app/templates/dashboard_bootstrap.html",
            "app/templates/auth/login_bootstrap.html"
        ]
        
        for template_path in template_files:
            template_file = Path(template_path)
            if template_file.exists():
                template_content = template_file.read_text(encoding='utf-8')
                
                found_utilities = [util for util in responsive_utilities if util in template_content]
                assert len(found_utilities) > 0, f"No responsive utilities found in {template_path}"
        
        print("✅ Mobile responsiveness coverage complete")
    
    def test_touch_interaction_implementation(self):
        """Test touch interaction implementation"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Touch interaction features
        touch_features = [
            'createRippleEffect',
            'transform: scale(',
            'transition:',
            'animation:',
            'touchstart',
            'touchend'
        ]
        
        for feature in touch_features:
            assert feature in content, f"Touch interaction feature missing: {feature}"
        
        # Check CSS for touch feedback
        css_file = Path("app/static/css/bootstrap-custom.css")
        css_content = css_file.read_text(encoding='utf-8')
        
        css_touch_features = [
            'scale(0.98)',
            'transform',
            'transition'
        ]
        
        for feature in css_touch_features:
            assert feature in css_content, f"CSS touch feedback feature missing: {feature}"
        
        print("✅ Touch interaction implementation complete")
    
    def test_form_mobile_optimization_implementation(self):
        """Test form mobile optimization implementation"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Form optimization features
        form_features = [
            'fontSize',
            '16px',
            'scrollIntoView',
            'keyboard',
            'focus',
            'blur',
            'checkValidity'
        ]
        
        for feature in form_features:
            assert feature in content, f"Form optimization feature missing: {feature}"
        
        # Check CSS for form optimizations
        css_file = Path("app/static/css/bootstrap-custom.css")
        css_content = css_file.read_text(encoding='utf-8')
        
        css_form_features = [
            'form-control-mobile',
            'min-height: 44px',
            'font-size: 16px'
        ]
        
        for feature in css_form_features:
            assert feature in css_content, f"CSS form optimization feature missing: {feature}"
        
        print("✅ Form mobile optimization implementation complete")
    
    def test_accessibility_implementation(self):
        """Test accessibility implementation"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Accessibility features
        accessibility_features = [
            'prefers-contrast: high',
            'prefers-reduced-motion: reduce',
            'box-shadow',
            'focus',
            'env(safe-area-inset'
        ]
        
        for feature in accessibility_features:
            assert feature in content, f"Accessibility feature missing: {feature}"
        
        print("✅ Accessibility implementation complete")
    
    def test_performance_optimization_implementation(self):
        """Test performance optimization implementation"""
        js_file = Path("app/static/js/mobile.js")
        content = js_file.read_text(encoding='utf-8')
        
        # Performance features
        performance_features = [
            'passive: true',
            'requestAnimationFrame',
            'setTimeout',
            'transition'
        ]
        
        for feature in performance_features:
            assert feature in content, f"Performance optimization feature missing: {feature}"
        
        print("✅ Performance optimization implementation complete")
    
    def test_cross_browser_compatibility_features(self):
        """Test cross-browser compatibility features"""
        css_file = Path("app/static/css/bootstrap-custom.css")
        content = css_file.read_text(encoding='utf-8')
        
        # Cross-browser features
        browser_features = [
            '-webkit-',
            'transform',
            'transition',
            '@supports'
        ]
        
        for feature in browser_features:
            assert feature in content, f"Cross-browser compatibility feature missing: {feature}"
        
        print("✅ Cross-browser compatibility features complete")
    
    def test_mobile_layout_fixes_implementation(self):
        """Test mobile layout fixes implementation"""
        templates_with_mobile_fixes = [
            "app/templates/dashboard_bootstrap.html",
            "app/templates/base_bootstrap.html",
            "app/templates/auth/login_bootstrap.html"
        ]
        
        mobile_layout_classes = [
            'd-lg-none',      # Mobile-only content
            'd-none d-lg-block',  # Desktop-only content
            'flex-column flex-md-row',  # Responsive flex direction
            'col-12',         # Full width on mobile
            'mobile-card'     # Mobile-specific card styling
        ]
        
        found_classes = set()
        
        for template_path in templates_with_mobile_fixes:
            template_file = Path(template_path)
            if template_file.exists():
                content = template_file.read_text(encoding='utf-8')
                
                for css_class in mobile_layout_classes:
                    if css_class in content:
                        found_classes.add(css_class)
        
        # Should find most of the mobile layout classes
        assert len(found_classes) >= 3, f"Not enough mobile layout classes found. Found: {found_classes}"
        
        print("✅ Mobile layout fixes implementation complete")


class TestMobileFeatureIntegration:
    """Test mobile feature integration"""
    
    def test_mobile_navigation_integration(self, app):
        """Test mobile navigation integration"""
        with app.test_client() as client:
            # Test login page (no auth required)
            response = client.get('/auth/login')
            assert response.status_code == 200
            
            # Check for mobile elements that should be present on login page
            html_content = response.get_data(as_text=True)
            
            mobile_elements = [
                'viewport',
                'mobile.js',
                'bootstrap-custom.css'
            ]
            
            for element in mobile_elements:
                assert element in html_content, f"Mobile element missing: {element}"
        
        print("✅ Mobile navigation integration working")
    
    def test_mobile_form_integration(self, app):
        """Test mobile form integration"""
        with app.test_client() as client:
            response = client.get('/auth/login')
            assert response.status_code == 200
            
            html_content = response.get_data(as_text=True)
            
            mobile_form_elements = [
                'form-control-mobile',
                'btn-mobile',
                'viewport'
            ]
            
            for element in mobile_form_elements:
                assert element in html_content, f"Mobile form element missing: {element}"
        
        print("✅ Mobile form integration working")
    
    def test_mobile_css_loading(self, app):
        """Test mobile CSS loading"""
        with app.test_client() as client:
            response = client.get('/static/css/bootstrap-custom.css')
            assert response.status_code == 200
            
            css_content = response.get_data(as_text=True)
            
            # Check for mobile CSS content
            assert '@media (max-width: 768px)' in css_content
            assert '.btn-mobile' in css_content
            assert 'touch-action: manipulation' in css_content
        
        print("✅ Mobile CSS loading working")
    
    def test_mobile_js_loading(self, app):
        """Test mobile JavaScript loading"""
        with app.test_client() as client:
            response = client.get('/static/js/mobile.js')
            assert response.status_code == 200
            
            js_content = response.get_data(as_text=True)
            
            # Check for mobile JavaScript content
            assert 'initializeMobileMenu' in js_content
            assert 'touchstart' in js_content
            assert 'swipe' in js_content.lower()
        
        print("✅ Mobile JavaScript loading working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])