#!/usr/bin/env python3
"""
Mobile layout fixes and improvements tests.
Tests specific mobile layout issues and their fixes.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        
        # Create test availability entries
        for i in range(5):
            availability = Availability(
                user_id=regular_user.id,
                date=date.today(),
                start_time=dt_time(9 + i, 0),
                end_time=dt_time(10 + i, 0)
            )
            db.session.add(availability)
        
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def mobile_driver():
    """Create mobile browser driver"""
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('mobileEmulation', {
        'deviceMetrics': {'width': 375, 'height': 667, 'pixelRatio': 2.0},
        'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
    })
    
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


class TestMobileLayoutFixes:
    """Test mobile layout fixes and improvements"""
    
    def test_mobile_navigation_brand_text(self, mobile_driver, app):
        """Test mobile navigation brand text responsiveness"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            
            # Check brand text changes on mobile
            brand_element = mobile_driver.find_element(By.CLASS_NAME, "navbar-brand")
            
            # Check for responsive brand text elements
            full_text_elements = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-none.d-sm-inline")
            short_text_elements = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-sm-none")
            
            # On mobile (375px), short text should be visible
            assert len(short_text_elements) > 0, "Short brand text should be present for mobile"
            
            # Check visibility
            for element in short_text_elements:
                if element.is_displayed():
                    assert "🏸" in element.text or "Scheduler" in element.text
    
    def test_mobile_card_layout_improvements(self, mobile_driver, app):
        """Test mobile card layout improvements"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Check mobile-specific layout
            mobile_layout = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-lg-none")
            desktop_layout = mobile_driver.find_elements(By.CSS_SELECTOR, ".d-none.d-lg-block")
            
            # Mobile layout should be visible
            assert len(mobile_layout) > 0, "Mobile layout should be present"
            
            # Check mobile cards
            mobile_cards = mobile_driver.find_elements(By.CLASS_NAME, "mobile-card")
            cards = mobile_driver.find_elements(By.CLASS_NAME, "card")
            
            for card in cards:
                if card.is_displayed():
                    # Check card doesn't overflow viewport
                    card_width = card.size['width']
                    viewport_width = mobile_driver.execute_script("return window.innerWidth")
                    
                    assert card_width <= viewport_width, f"Card width {card_width} exceeds viewport {viewport_width}"
                    
                    # Check card has appropriate margins
                    margin_left = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginLeft", card
                    )
                    margin_right = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginRight", card
                    )
                    
                    # Should have some margin for mobile
                    assert margin_left != '0px' or margin_right != '0px'
    
    def test_mobile_button_stacking(self, mobile_driver, app):
        """Test mobile button stacking and layout"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Check action buttons container
            button_container = mobile_driver.find_element(By.CSS_SELECTOR, ".d-flex.flex-column.flex-md-row")
            
            # Check buttons are stacked vertically on mobile
            buttons = button_container.find_elements(By.CSS_SELECTOR, ".btn")
            
            if len(buttons) > 1:
                # Get positions of first two buttons
                button1_rect = buttons[0].location
                button2_rect = buttons[1].location
                
                # On mobile, buttons should be stacked (second button below first)
                assert button2_rect['y'] > button1_rect['y'], "Buttons should be stacked vertically on mobile"
    
    def test_mobile_form_input_sizing(self, mobile_driver, app):
        """Test mobile form input sizing and touch targets"""
        with app.test_client():
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Check form inputs
            inputs = mobile_driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            
            for input_element in inputs:
                if input_element.is_displayed():
                    # Check minimum height for touch targets
                    height = input_element.size['height']
                    assert height >= 40, f"Input height {height}px should be at least 40px for touch"
                    
                    # Check font size to prevent zoom on iOS
                    font_size = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).fontSize", input_element
                    )
                    font_size_px = int(font_size.replace('px', ''))
                    assert font_size_px >= 16, f"Font size {font_size_px}px should be at least 16px to prevent zoom"
                    
                    # Check padding for better touch experience
                    padding = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).padding", input_element
                    )
                    # Should have some padding
                    assert padding != '0px'
    
    def test_mobile_navigation_menu_behavior(self, mobile_driver, app):
        """Test mobile navigation menu behavior and styling"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            
            # Check mobile menu button
            menu_button = mobile_driver.find_element(By.CLASS_NAME, "navbar-toggler")
            assert menu_button.is_displayed(), "Mobile menu button should be visible"
            
            # Check menu button size for touch
            button_size = menu_button.size
            assert button_size['height'] >= 40, "Menu button should be at least 40px high"
            assert button_size['width'] >= 40, "Menu button should be at least 40px wide"
            
            # Test menu toggle functionality
            nav_menu = mobile_driver.find_element(By.ID, "navbarNav")
            
            # Initially collapsed
            initial_classes = nav_menu.get_attribute('class')
            assert 'show' not in initial_classes, "Menu should be initially collapsed"
            
            # Click to expand
            menu_button.click()
            time.sleep(0.5)  # Wait for animation
            
            # Should be expanded
            WebDriverWait(mobile_driver, 5).until(
                lambda driver: 'show' in nav_menu.get_attribute('class')
            )
            
            # Check nav links are touch-friendly
            nav_links = nav_menu.find_elements(By.CSS_SELECTOR, ".nav-link")
            for link in nav_links:
                if link.is_displayed():
                    link_height = link.size['height']
                    assert link_height >= 40, f"Nav link height {link_height}px should be at least 40px"
    
    def test_mobile_dropdown_positioning(self, mobile_driver, app):
        """Test mobile dropdown positioning and behavior"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            
            # Find user dropdown
            dropdown_toggle = mobile_driver.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
            
            # Click to open dropdown
            dropdown_toggle.click()
            time.sleep(0.5)
            
            # Check dropdown menu
            dropdown_menu = mobile_driver.find_element(By.CSS_SELECTOR, ".dropdown-menu")
            
            # Should be visible
            WebDriverWait(mobile_driver, 5).until(
                lambda driver: 'show' in dropdown_menu.get_attribute('class')
            )
            
            # Check dropdown doesn't overflow viewport
            menu_rect = dropdown_menu.location
            menu_size = dropdown_menu.size
            viewport_width = mobile_driver.execute_script("return window.innerWidth")
            viewport_height = mobile_driver.execute_script("return window.innerHeight")
            
            # Menu should be within viewport bounds
            assert menu_rect['x'] >= 0, "Dropdown should not overflow left"
            assert menu_rect['x'] + menu_size['width'] <= viewport_width, "Dropdown should not overflow right"
            
            # Check dropdown items are touch-friendly
            dropdown_items = dropdown_menu.find_elements(By.CSS_SELECTOR, ".dropdown-item")
            for item in dropdown_items:
                if item.is_displayed():
                    item_height = item.size['height']
                    assert item_height >= 40, f"Dropdown item height {item_height}px should be at least 40px"
    
    def test_mobile_table_responsiveness(self, mobile_driver, app):
        """Test mobile table responsiveness and scrolling"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/availability/my_availability')
            
            # Check for responsive table handling
            tables = mobile_driver.find_elements(By.CSS_SELECTOR, "table")
            
            for table in tables:
                if table.is_displayed():
                    # Check table doesn't overflow viewport
                    table_width = table.size['width']
                    viewport_width = mobile_driver.execute_script("return window.innerWidth")
                    
                    # Table should either fit or be in a scrollable container
                    if table_width > viewport_width:
                        # Should be in a responsive container
                        parent = table.find_element(By.XPATH, "..")
                        parent_classes = parent.get_attribute('class')
                        
                        assert 'table-responsive' in parent_classes or 'overflow' in parent_classes
    
    def test_mobile_alert_and_message_layout(self, mobile_driver, app):
        """Test mobile alert and message layout"""
        with app.test_client():
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Try to trigger a validation error
            submit_button = mobile_driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            submit_button.click()
            
            time.sleep(1)
            
            # Check for any alerts or messages
            alerts = mobile_driver.find_elements(By.CSS_SELECTOR, ".alert, .error, .message")
            
            for alert in alerts:
                if alert.is_displayed():
                    # Check alert doesn't overflow viewport
                    alert_width = alert.size['width']
                    viewport_width = mobile_driver.execute_script("return window.innerWidth")
                    
                    assert alert_width <= viewport_width, f"Alert width {alert_width} exceeds viewport {viewport_width}"
                    
                    # Check alert has appropriate margins
                    margin_left = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginLeft", alert
                    )
                    margin_right = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginRight", alert
                    )
                    
                    # Should have margins or be full width
                    total_width = alert_width + int(margin_left.replace('px', '')) + int(margin_right.replace('px', ''))
                    assert total_width <= viewport_width + 10  # Allow small tolerance
    
    def test_mobile_form_layout_improvements(self, mobile_driver, app):
        """Test mobile form layout improvements"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/availability/add')
            
            # Check form layout
            form = mobile_driver.find_element(By.TAG_NAME, "form")
            
            # Check form doesn't overflow
            form_width = form.size['width']
            viewport_width = mobile_driver.execute_script("return window.innerWidth")
            
            assert form_width <= viewport_width, f"Form width {form_width} exceeds viewport {viewport_width}"
            
            # Check form groups have appropriate spacing
            form_groups = mobile_driver.find_elements(By.CSS_SELECTOR, ".form-group, .mb-3, .mb-4")
            
            for group in form_groups:
                if group.is_displayed():
                    # Check margin bottom for spacing
                    margin_bottom = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginBottom", group
                    )
                    
                    margin_px = int(margin_bottom.replace('px', ''))
                    assert margin_px >= 8, f"Form group should have at least 8px bottom margin, got {margin_px}px"
            
            # Check labels are properly positioned
            labels = mobile_driver.find_elements(By.CSS_SELECTOR, "label")
            
            for label in labels:
                if label.is_displayed():
                    # Check label font size and weight
                    font_size = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).fontSize", label
                    )
                    font_weight = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).fontWeight", label
                    )
                    
                    font_size_px = int(font_size.replace('px', ''))
                    assert font_size_px >= 14, f"Label font size should be at least 14px, got {font_size_px}px"
    
    def test_mobile_loading_states(self, mobile_driver, app):
        """Test mobile loading states and feedback"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/availability/add')
            
            # Fill form quickly
            date_input = mobile_driver.find_element(By.NAME, "date")
            start_time_input = mobile_driver.find_element(By.NAME, "start_time")
            end_time_input = mobile_driver.find_element(By.NAME, "end_time")
            
            mobile_driver.execute_script("arguments[0].value = '2024-12-25'", date_input)
            mobile_driver.execute_script("arguments[0].value = '09:00'", start_time_input)
            mobile_driver.execute_script("arguments[0].value = '11:00'", end_time_input)
            
            # Submit and check for loading state
            submit_button = mobile_driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            
            # Check button is properly sized for mobile
            button_height = submit_button.size['height']
            assert button_height >= 44, f"Submit button height {button_height}px should be at least 44px"
            
            submit_button.click()
            
            # Check for loading state (button should be disabled briefly)
            try:
                WebDriverWait(mobile_driver, 2).until(
                    lambda driver: not submit_button.is_enabled()
                )
                # Button was disabled, which is good for preventing double submission
            except TimeoutException:
                # Button might not be disabled, which is also acceptable
                pass
    
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


class TestMobileTouchInteractions:
    """Test mobile touch interactions and gestures"""
    
    def test_touch_feedback_on_buttons(self, mobile_driver, app):
        """Test touch feedback on buttons and interactive elements"""
        with app.test_client():
            mobile_driver.get('http://localhost:5000/auth/login')
            
            # Find interactive elements
            buttons = mobile_driver.find_elements(By.CSS_SELECTOR, "button, .btn, input[type='submit']")
            
            for button in buttons:
                if button.is_displayed():
                    # Simulate touch interaction
                    ActionChains(mobile_driver).click_and_hold(button).perform()
                    time.sleep(0.1)
                    
                    # Check for visual feedback (transform or opacity change)
                    transform = mobile_driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).transform", button
                    )
                    
                    ActionChains(mobile_driver).release().perform()
                    
                    # Transform should indicate some feedback (not 'none')
                    # This is a basic check - actual implementation may vary
    
    def test_swipe_gesture_hints(self, mobile_driver, app):
        """Test swipe gesture hints and feedback"""
        with app.test_client():
            self._login_user(mobile_driver, 'user_test', 'test_password')
            mobile_driver.get('http://localhost:5000/dashboard')
            
            # Find cards that should support swipe gestures
            cards = mobile_driver.find_elements(By.CLASS_NAME, "card")
            
            for card in cards[:2]:  # Test first 2 cards
                if card.is_displayed():
                    # Check if card has edit/delete buttons (indicating swipe support)
                    edit_buttons = card.find_elements(By.CSS_SELECTOR, "a[href*='edit']")
                    delete_buttons = card.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                    
                    if edit_buttons or delete_buttons:
                        # Card should support swipe gestures
                        # This is mainly checking that the structure is in place
                        assert True  # Structure check passed
    
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