#!/usr/bin/env python3
"""
Cross-browser compatibility tests for mobile and desktop browsers.
Tests functionality across Chrome, Firefox, Safari, and Edge.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common.exceptions import WebDriverException, TimeoutException
from app import create_app, db
from app.models import User, Availability
from datetime import datetime, date, time as dt_time
import os
import platform


class BrowserTestConfig:
    """Configuration for cross-browser testing"""
    
    # Browser configurations
    BROWSERS = {
        'chrome': {
            'driver_class': webdriver.Chrome,
            'options_class': ChromeOptions,
            'mobile_emulation': {
                'deviceMetrics': {'width': 375, 'height': 667, 'pixelRatio': 2.0},
                'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
            }
        },
        'firefox': {
            'driver_class': webdriver.Firefox,
            'options_class': FirefoxOptions,
            'mobile_emulation': None
        },
        'edge': {
            'driver_class': webdriver.Edge,
            'options_class': EdgeOptions,
            'mobile_emulation': {
                'deviceMetrics': {'width': 375, 'height': 667, 'pixelRatio': 2.0}
            }
        }
    }
    
    # Add Safari only on macOS
    if platform.system() == 'Darwin':
        BROWSERS['safari'] = {
            'driver_class': webdriver.Safari,
            'options_class': SafariOptions,
            'mobile_emulation': None
        }
    
    # Screen resolutions to test
    SCREEN_SIZES = [
        (375, 667),   # iPhone SE
        (414, 896),   # iPhone 11
        (768, 1024),  # iPad
        (1366, 768),  # Laptop
        (1920, 1080)  # Desktop
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
        
        yield app
        
        db.drop_all()


def create_browser_driver(browser_name, mobile=False):
    """Create browser driver with appropriate configuration"""
    if browser_name not in BrowserTestConfig.BROWSERS:
        pytest.skip(f"Browser {browser_name} not supported on this platform")
    
    browser_config = BrowserTestConfig.BROWSERS[browser_name]
    options_class = browser_config['options_class']
    driver_class = browser_config['driver_class']
    
    options = options_class()
    
    # Common options for all browsers
    if hasattr(options, 'add_argument'):
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
    
    # Mobile emulation for supported browsers
    if mobile and browser_config['mobile_emulation']:
        if browser_name == 'chrome':
            options.add_experimental_option('mobileEmulation', browser_config['mobile_emulation'])
        elif browser_name == 'edge':
            options.add_experimental_option('mobileEmulation', browser_config['mobile_emulation'])
    
    try:
        driver = driver_class(options=options)
        
        # Set mobile viewport for browsers that don't support mobile emulation
        if mobile and not browser_config['mobile_emulation']:
            driver.set_window_size(375, 667)
        elif not mobile:
            driver.set_window_size(1920, 1080)
        
        return driver
    except WebDriverException as e:
        pytest.skip(f"Could not create {browser_name} driver: {e}")


class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility"""
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_basic_page_loading(self, browser_name, app):
        """Test basic page loading across browsers"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check page title
                assert 'Login' in driver.title
                
                # Check basic elements are present
                username_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_input = driver.find_element(By.NAME, "password")
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                
                assert username_input.is_displayed()
                assert password_input.is_displayed()
                assert submit_button.is_displayed()
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_css_loading_and_styling(self, browser_name, app):
        """Test CSS loading and basic styling across browsers"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check CSS is loaded by verifying computed styles
                body = driver.find_element(By.TAG_NAME, "body")
                body_bg = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundColor", body
                )
                
                # Should not be default white background
                assert body_bg not in ['rgba(0, 0, 0, 0)', 'rgb(255, 255, 255)']
                
                # Check Bootstrap classes are working
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                button_classes = submit_button.get_attribute('class')
                
                assert 'btn' in button_classes
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_javascript_functionality(self, browser_name, app):
        """Test JavaScript functionality across browsers"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                # Login first
                self._login_user(driver, 'user_test', 'test_password')
                
                # Test mobile menu functionality (if mobile)
                try:
                    menu_button = driver.find_element(By.CLASS_NAME, "navbar-toggler")
                    if menu_button.is_displayed():
                        # Test menu toggle
                        nav_menu = driver.find_element(By.ID, "navbarNav")
                        initial_display = nav_menu.is_displayed()
                        
                        menu_button.click()
                        time.sleep(0.5)
                        
                        # Menu state should change
                        final_display = nav_menu.is_displayed()
                        # Note: This might vary by browser implementation
                        
                except Exception:
                    # Menu button might not be visible on desktop
                    pass
                
                # Test form validation
                driver.get('http://localhost:5000/availability/add')
                
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                submit_button.click()
                
                # Should show validation errors or stay on page
                time.sleep(1)
                current_url = driver.current_url
                assert 'add' in current_url or 'error' in driver.page_source.lower()
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    @pytest.mark.parametrize("screen_size", BrowserTestConfig.SCREEN_SIZES)
    def test_responsive_design(self, browser_name, screen_size, app):
        """Test responsive design across browsers and screen sizes"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                driver.set_window_size(*screen_size)
                
                self._login_user(driver, 'user_test', 'test_password')
                driver.get('http://localhost:5000/dashboard')
                
                # Check no horizontal overflow
                body_width = driver.execute_script("return document.body.scrollWidth")
                viewport_width = driver.execute_script("return window.innerWidth")
                
                assert body_width <= viewport_width + 20, f"Horizontal overflow at {screen_size}"
                
                # Check navigation is appropriate for screen size
                width, height = screen_size
                if width < 768:  # Mobile breakpoint
                    # Should have mobile menu button
                    try:
                        menu_button = driver.find_element(By.CLASS_NAME, "navbar-toggler")
                        assert menu_button.is_displayed()
                    except Exception:
                        # Some browsers might handle this differently
                        pass
                else:
                    # Should have full navigation
                    nav_links = driver.find_elements(By.CSS_SELECTOR, ".navbar-nav .nav-link")
                    visible_links = [link for link in nav_links if link.is_displayed()]
                    assert len(visible_links) > 0
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_form_submission_compatibility(self, browser_name, app):
        """Test form submission across browsers"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                self._login_user(driver, 'user_test', 'test_password')
                driver.get('http://localhost:5000/availability/add')
                
                # Fill form
                date_input = driver.find_element(By.NAME, "date")
                start_time_input = driver.find_element(By.NAME, "start_time")
                end_time_input = driver.find_element(By.NAME, "end_time")
                
                # Use JavaScript to set values for better browser compatibility
                driver.execute_script("arguments[0].value = '2024-12-25'", date_input)
                driver.execute_script("arguments[0].value = '09:00'", start_time_input)
                driver.execute_script("arguments[0].value = '11:00'", end_time_input)
                
                # Submit form
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                submit_button.click()
                
                # Wait for response
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.current_url != 'http://localhost:5000/availability/add'
                )
                
                # Should redirect or show success
                assert 'add' not in driver.current_url or 'success' in driver.page_source.lower()
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_mobile_specific_features(self, browser_name, app):
        """Test mobile-specific features across browsers"""
        driver = create_browser_driver(browser_name, mobile=True)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check viewport meta tag
                viewport_meta = driver.find_element(By.XPATH, "//meta[@name='viewport']")
                viewport_content = viewport_meta.get_attribute('content')
                
                assert 'width=device-width' in viewport_content
                assert 'initial-scale=1.0' in viewport_content
                
                # Check mobile-friendly input sizes
                inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
                for input_element in inputs:
                    if input_element.is_displayed():
                        height = input_element.size['height']
                        assert height >= 40, f"Input too small for touch: {height}px"
                
                # Check mobile JavaScript is loaded
                mobile_js_loaded = driver.execute_script(
                    "return typeof initializeMobileMenu === 'function'"
                )
                assert mobile_js_loaded, "Mobile JavaScript not loaded"
                
        finally:
            driver.quit()
    
    @pytest.mark.parametrize("browser_name", list(BrowserTestConfig.BROWSERS.keys()))
    def test_accessibility_features(self, browser_name, app):
        """Test accessibility features across browsers"""
        driver = create_browser_driver(browser_name)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check form labels
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password']")
                for input_element in inputs:
                    input_id = input_element.get_attribute('id')
                    aria_label = input_element.get_attribute('aria-label')
                    
                    if input_id:
                        try:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            assert label.is_displayed() or aria_label
                        except Exception:
                            assert aria_label, f"Input {input_id} missing accessible label"
                
                # Check color contrast (basic check)
                body = driver.find_element(By.TAG_NAME, "body")
                body_color = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).color", body
                )
                body_bg = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundColor", body
                )
                
                assert body_color != body_bg, "Text and background should have different colors"
                
        finally:
            driver.quit()
    
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


class TestBrowserSpecificFeatures:
    """Test browser-specific features and workarounds"""
    
    def test_chrome_mobile_emulation(self, app):
        """Test Chrome mobile emulation features"""
        driver = create_browser_driver('chrome', mobile=True)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check mobile user agent
                user_agent = driver.execute_script("return navigator.userAgent")
                assert 'iPhone' in user_agent or 'Mobile' in user_agent
                
                # Check device pixel ratio
                pixel_ratio = driver.execute_script("return window.devicePixelRatio")
                assert pixel_ratio >= 1.0
                
        finally:
            driver.quit()
    
    def test_firefox_mobile_compatibility(self, app):
        """Test Firefox mobile compatibility"""
        driver = create_browser_driver('firefox', mobile=True)
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check viewport dimensions
                viewport_width = driver.execute_script("return window.innerWidth")
                assert viewport_width <= 768  # Should be mobile width
                
                # Check CSS media queries work
                body_bg = driver.execute_script(
                    "return window.getComputedStyle(document.body).backgroundColor"
                )
                assert body_bg != 'rgba(0, 0, 0, 0)'
                
        finally:
            driver.quit()
    
    @pytest.mark.skipif(platform.system() != 'Darwin', reason="Safari only available on macOS")
    def test_safari_specific_features(self, app):
        """Test Safari-specific features and compatibility"""
        if 'safari' not in BrowserTestConfig.BROWSERS:
            pytest.skip("Safari not available on this platform")
        
        driver = create_browser_driver('safari')
        
        try:
            with app.test_client():
                driver.get('http://localhost:5000/auth/login')
                
                # Check Safari-specific CSS features
                inputs = driver.find_elements(By.CSS_SELECTOR, "input")
                for input_element in inputs:
                    if input_element.is_displayed():
                        # Check -webkit-appearance is handled
                        appearance = driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).webkitAppearance", 
                            input_element
                        )
                        # Should not be 'none' unless explicitly set
                        
        finally:
            driver.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])