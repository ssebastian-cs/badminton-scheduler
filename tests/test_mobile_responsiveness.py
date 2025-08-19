#!/usr/bin/env python3
"""
Comprehensive mobile responsiveness tests for the badminton scheduler application.
Tests mobile layouts, touch interactions, and cross-browser compatibility.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app import create_app, db
from app.models import User, Availability
from datetime import datetime, date, time as dt_time
import os


class MobileTestConfig:
    """Configuration for mobile testing"""
    
    # Mobile device configurations
    MOBILE_DEVICES = {
        'iphone_se': {'width': 375, 'height': 667, 'user_agent': 'iPhone SE'},
        'iphone_12': {'width': 390, 'height': 844, 'user_agent': 'iPhone 12'},
        'samsung_galaxy': {'width': 360, 'height': 640, 'user_agent': 'Samsung Galaxy S20'},
        'ipad': {'width': 768, 'height': 1024, 'user_agent': 'iPad'},
        'tablet_landscape': {'width': 1024, 'height': 768, 'user_agent': 'Tablet Landscape'}
    }
    
    # Browser configurations
    BROWSERS = ['chrome', 'firefox']
    
    # Test URLs
    TEST_URLS = [
        '/auth/login',
        '/dashboard',
        '/availability/add',
        '/availability/my_availability',
        '/comments',
        '/admin/dashboard'
    ]


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Create test users
        admin_user = User(
            username='admin_test',
            password_hash='pbkdf2:sha256:260000$test$test_hash',
            role='Admin',
            is_active=True
        )
        regular_user = User(
            username='user_test',
            password_hash='pbkdf2:sha256:260000$test$test_hash',
            role='User',
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.add(regular_user)
        db.session.commit()
        
        # Create test availability
        test_availability = Availability(
            user_id=regular_user.id,
            date=date.today(),
            start_time=dt_time(9, 0),
            end_time=dt_time(11, 0)
        )
        db.session.add(test_availability)
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture(params=MobileTestConfig.BROWSERS)
def mobile_driver(request, app):
    """Create mobile browser driver for testing"""
    browser = request.param
    
    if browser == 'chrome':
        options = ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_experimental_option('mobileEmulation', {
            'deviceMetrics': {'width': 375, 'height': 667, 'pixelRatio': 2.0},
            'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        })
        driver = webdriver.Chrome(options=options)
    
    elif browser == 'firefox':
        options = FirefoxOptions()
        options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)
        # Set mobile viewport
        driver.set_window_size(375, 667)
    
    else:
        pytest.skip(f"Browser {browser} not supported")
    
    yield driver
    driver.quit()


@pytest.fixture
def desktop_driver():
    """Create desktop browser driver for comparison testing"""
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    
    yield driver
    driver.quit()


class TestMobileResponsiveness:
    """Test mobile responsiveness across different devices and browsers"""
    
    def test_mobile_viewport_meta_tag(self, mobile_driver, app):
        """Test that viewport meta tag is properly configured"""
        with app.test_client() as client:
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Check viewport meta tag
            viewport_meta = mobile_driver.find_element(By.XPATH, "//meta[@name='viewport']")
            viewport_content = viewport_meta.get_attribute('content')
            
            assert 'width=device-width' in viewport_content
            assert 'initial-scale=1.0' in viewport_content
    
    def test_mobile_navigation_menu(self, mobile_driver, app):
        """Test mobile navigation menu functionality"""
        with app.test_client() as client:
            # Login first
            self._login_user(mobile_driver, 'user_test', 'test_password')
            
            # Check mobile menu button exists
            menu_button = WebDriverWait(mobile_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "navbar-toggler"))
            )
            assert menu_button.is_displayed()
            
            # Check menu is initially collapsed
            nav_menu = mobile_driver.find_element(By.ID, "navbarNav")
            assert not nav_menu.is_displayed() or 'show' not in nav_menu.get_attribute('class')
            
            # Click menu button to expand
            menu_button.click()
            time.sleep(0.5)  # Wait for animation
            
            # Check menu is now visible
            WebDriverWait(mobile_driver, 5).until(
                lambda driver: 'show' in nav_menu.get_attribute('class')
            )
    
    def test_mobile_form_inputs(self, mobile_driver, app):
        """Test mobile form input behavior and styling"""
        with app.test_client() as client:
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Test login form inputs
            username_input = mobile_driver.find_element(By.NAME, "username")
            password_input = mobile_driver.find_element(By.NAME, "password")
            
            # Check input styling for mobile
            username_style = username_input.get_attribute('class')
            assert 'form-control-mobile' in username_style or 'form-control' in username_style
            
            # Check font size to prevent zoom on iOS
            username_font_size = mobile_driver.execute_script(
                "return window.getComputedStyle(arguments[0]).fontSize", username_input
            )
            font_size_px = int(username_font_size.replace('px', ''))
            assert font_size_px >= 16, "Font size should be at least 16px to prevent zoom on iOS"
            
            # Test touch interaction
            username_input.click()
            assert username_input == mobile_driver.switch_to.active_element
    
    def test_mobile_button_touch_targets(self, mobile_driver, app):
        """Test that buttons meet minimum touch target size requirements"""
        with app.test_client() as client:
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Find submit button
            submit_button = mobile_driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            
            # Check button dimensions
            button_size = submit_button.size
            assert button_size['height'] >= 44, "Button height should be at least 44px for touch accessibility"
            assert button_size['width'] >= 44, "Button width should be at least 44px for touch accessibility"
    
    def test_responsive_layout_breakpoints(self, mobile_driver, app):
        """Test responsive layout at different breakpoints"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Test different screen sizes
            screen_sizes = [
                (320, 568),  # iPhone SE
                (375, 667),  # iPhone 8
                (414, 896),  # iPhone 11
                (768, 1024), # iPad
                (1024, 768)  # Tablet landscape
            ]
            
            for width, height in screen_sizes:
                mobile_driver.set_window_size(width, height)
                time.sleep(0.5)  # Wait for layout adjustment
                
                # Check that content is not horizontally scrollable
                body_width = mobile_driver.execute_script("return document.body.scrollWidth")
                viewport_width = mobile_driver.execute_script("return window.innerWidth")
                
                assert body_width <= viewport_width + 20, f"Content overflows at {width}x{height}"
                
                # Check navigation is accessible
                if width < 768:  # Mobile breakpoint
                    menu_button = mobile_driver.find_element(By.CLASS_NAME, "navbar-toggler")
                    assert menu_button.is_displayed(), f"Mobile menu button not visible at {width}x{height}"
    
    def test_mobile_dashboard_layout(self, mobile_driver, app):
        """Test dashboard layout on mobile devices"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Check mobile-specific elements
            mobile_cards = mobile_driver.find_elements(By.CLASS_NAME, "mobile-card")
            desktop_grid = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-none.d-lg-block")
            mobile_list = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-lg-none")
            
            # On mobile, should show mobile layout
            assert len(mobile_list) > 0, "Mobile layout should be visible"
            
            # Check action buttons are stacked vertically on mobile
            action_buttons = mobile_driver.find_element(By.CSS_SELECTOR, ".d-flex.flex-column.flex-md-row")
            assert action_buttons.is_displayed()
    
    def test_mobile_form_submission(self, mobile_driver, app):
        """Test form submission on mobile devices"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/availability/add')
            
            # Fill out availability form
            date_input = mobile_driver.find_element(By.NAME, "date")
            start_time_input = mobile_driver.find_element(By.NAME, "start_time")
            end_time_input = mobile_driver.find_element(By.NAME, "end_time")
            
            # Test date picker on mobile
            date_input.click()
            date_input.send_keys("2024-12-25")
            
            # Test time inputs
            start_time_input.send_keys("09:00")
            end_time_input.send_keys("11:00")
            
            # Submit form
            submit_button = mobile_driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            submit_button.click()
            
            # Check for success or validation
            WebDriverWait(mobile_driver, 10).until(
                lambda driver: driver.current_url != 'http://localhost:5000/availability/add'
            )
    
    def test_mobile_touch_interactions(self, mobile_driver, app):
        """Test touch-specific interactions"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Test touch feedback on buttons
            buttons = mobile_driver.find_elements(By.CSS_SELECTOR, "button, .btn, a.btn")
            
            for button in buttons[:3]:  # Test first 3 buttons
                if button.is_displayed():
                    # Simulate touch start
                    ActionChains(mobile_driver).click_and_hold(button).perform()
                    time.sleep(0.1)
                    
                    # Check for visual feedback (transform or opacity change)
                    transform = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).transform", button
                    )
                    
                    ActionChains(mobile_driver).release().perform()
    
    def test_cross_browser_compatibility(self, app):
        """Test cross-browser compatibility for mobile"""
        browsers = ['chrome', 'firefox']
        
        for browser in browsers:
            if browser == 'chrome':
                options = ChromeOptions()
                options.add_argument('--headless')
                options.add_experimental_option('mobileEmulation', {
                    'deviceMetrics': {'width': 375, 'height': 667, 'pixelRatio': 2.0}
                })
                driver = webdriver.Chrome(options=options)
            else:
                options = FirefoxOptions()
                options.add_argument('--headless')
                driver = webdriver.Firefox(options=options)
                driver.set_window_size(375, 667)
            
            try:
                with app.test_client():
                    driver.get('http://localhost:5000/auth/login')
                    
                    # Test basic functionality
                    username_input = driver.find_element(By.NAME, "username")
                    password_input = driver.find_element(By.NAME, "password")
                    
                    assert username_input.is_displayed()
                    assert password_input.is_displayed()
                    
                    # Test CSS loading
                    body_bg = driver.execute_script(
                        "return window.getComputedStyle(document.body).backgroundColor"
                    )
                    assert body_bg != 'rgba(0, 0, 0, 0)', f"CSS not loading properly in {browser}"
                    
            finally:
                driver.quit()
    
    def test_mobile_accessibility(self, mobile_driver, app):
        """Test mobile accessibility features"""
        with app.test_client() as client:
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Check for proper ARIA labels
            form_inputs = mobile_driver.find_elements(By.CSS_SELECTOR, "input, button, select")
            
            for input_element in form_inputs:
                # Check for labels or aria-label
                input_id = input_element.get_attribute('id')
                aria_label = input_element.get_attribute('aria-label')
                
                if input_id:
                    try:
                        label = mobile_driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        assert label.is_displayed() or aria_label, f"Input {input_id} missing accessible label"
                    except NoSuchElementException:
                        assert aria_label, f"Input {input_id} missing accessible label"
            
            # Check color contrast (basic check)
            body_color = mobile_driver.execute_script(
                "return window.getComputedStyle(document.body).color"
            )
            body_bg = mobile_driver.execute_script(
                "return window.getComputedStyle(document.body).backgroundColor"
            )
            
            assert body_color != body_bg, "Text and background colors should be different"
    
    def test_mobile_performance(self, mobile_driver, app):
        """Test mobile performance metrics"""
        with app.test_client() as client:
            start_time = time.time()
            mobile_driver.get('http://localhost:5000/auth/login')
            load_time = time.time() - start_time
            
            # Page should load within reasonable time
            assert load_time < 5.0, f"Page load time {load_time:.2f}s exceeds 5 seconds"
            
            # Check for mobile-optimized resources
            css_links = mobile_driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
            js_scripts = mobile_driver.find_elements(By.CSS_SELECTOR, "script[src]")
            
            # Should have mobile-specific CSS
            mobile_css_found = False
            for link in css_links:
                href = link.get_attribute('href')
                if 'mobile' in href or 'bootstrap' in href:
                    mobile_css_found = True
                    break
            
            assert mobile_css_found, "Mobile-optimized CSS not found"
    
    def _login_user(self, driver, username, password):
        """Helper method to login a user"""
        driver.get('http://localhost:5000/auth/login')
        
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        
        username_input.send_keys(username)
        password_input.send_keys(password)
        submit_button.click()
        
        # Wait for redirect
        WebDriverWait(driver, 10).until(
            lambda driver: driver.current_url != 'http://localhost:5000/auth/login'
        )


class TestMobileLayoutFixes:
    """Test specific mobile layout fixes and enhancements"""
    
    def test_mobile_card_layout(self, mobile_driver, app):
        """Test mobile card layout improvements"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Check for mobile-specific card classes
            cards = mobile_driver.find_elements(By.CLASS_NAME, "card")
            
            for card in cards:
                if card.is_displayed():
                    # Check card has appropriate mobile styling
                    card_classes = card.get_attribute('class')
                    
                    # Should have mobile-friendly spacing
                    margin = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).margin", card
                    )
                    
                    # Cards should not be too wide on mobile
                    card_width = card.size['width']
                    viewport_width = mobile_driver.execute_script("return window.innerWidth")
                    
                    assert card_width <= viewport_width, "Card should not exceed viewport width"
    
    def test_mobile_navigation_improvements(self, mobile_driver, app):
        """Test mobile navigation improvements"""
        with app.test_client() as client:
            self._login_user(mobile_driver, 'user_test', 'test_password')
            
            # Test navigation brand text changes on mobile
            brand_element = mobile_driver.find_element(By.CLASS_NAME, "navbar-brand")
            
            # Check for responsive brand text
            full_text = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-none.d-sm-inline")
            short_text = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-sm-none")
            
            # On mobile, should show short text
            if mobile_driver.get_window_size()['width'] < 576:
                assert len(short_text) > 0, "Short brand text should be visible on mobile"
    
    def test_mobile_form_enhancements(self, mobile_driver, app):
        """Test mobile form enhancements"""
        with app.test_client() as client:
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Test form inputs have mobile-friendly classes
            inputs = mobile_driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            
            for input_element in inputs:
                if input_element.is_displayed():
                    input_classes = input_element.get_attribute('class')
                    
                    # Should have mobile-friendly styling
                    assert 'form-control' in input_classes, "Input should have form-control class"
                    
                    # Check minimum height for touch targets
                    height = input_element.size['height']
                    assert height >= 40, f"Input height {height}px should be at least 40px for touch"
    
    def _login_user(self, driver, username, password):
        """Helper method to login a user"""
        driver.get('http://localhost:5000/auth/login')
        
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        
        username_input.send_keys(username)
        password_input.send_keys(password)
        submit_button.click()
        
        # Wait for redirect
        WebDriverWait(driver, 10).until(
            lambda driver: driver.current_url != 'http://localhost:5000/auth/login'
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])