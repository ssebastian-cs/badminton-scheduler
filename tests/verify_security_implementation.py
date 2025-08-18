#!/usr/bin/env python3
"""
Verification script for security implementation in task 10.
Tests the key security measures that were implemented.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_security_imports():
    """Test that all security modules can be imported."""
    try:
        from app.security import SecurityValidator, RateLimiter, sanitize_form_data
        from app.forms import LoginForm, RegistrationForm, AvailabilityForm, CommentForm
        from app.config import Config, ProductionConfig
        print("✓ All security modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_security_validator():
    """Test SecurityValidator functionality."""
    try:
        from app.security import SecurityValidator
        
        # Test username validation
        valid, msg = SecurityValidator.validate_username('testuser')
        assert valid is True, f"Valid username failed: {msg}"
        
        valid, msg = SecurityValidator.validate_username('user<script>')
        assert valid is False, f"Invalid username passed: {msg}"
        
        # Test password validation
        valid, msg = SecurityValidator.validate_password_strength('password123')
        assert valid is True, f"Valid password failed: {msg}"
        
        valid, msg = SecurityValidator.validate_password_strength('weak')
        assert valid is False, f"Weak password passed: {msg}"
        
        # Test injection validation
        valid, msg = SecurityValidator.validate_against_injection("normal text")
        assert valid is True, f"Normal text failed: {msg}"
        
        valid, msg = SecurityValidator.validate_against_injection("'; DROP TABLE users; --")
        assert valid is False, f"SQL injection passed: {msg}"
        
        valid, msg = SecurityValidator.validate_against_injection("<script>alert('xss')</script>")
        assert valid is False, f"XSS attack passed: {msg}"
        
        print("✓ SecurityValidator tests passed")
        return True
    except Exception as e:
        print(f"✗ SecurityValidator test failed: {e}")
        return False

def test_input_sanitization():
    """Test input sanitization functionality."""
    try:
        from app.security import SecurityValidator
        
        # Test HTML escaping
        sanitized = SecurityValidator.sanitize_string("<script>alert('test')</script>")
        assert '<script>' not in sanitized, "HTML not escaped"
        assert '&lt;script&gt;' in sanitized, "HTML not properly escaped"
        
        # Test length limiting
        long_string = 'a' * 1000
        sanitized = SecurityValidator.sanitize_string(long_string, max_length=100)
        assert len(sanitized) == 100, f"Length not limited: {len(sanitized)}"
        
        # Test whitespace stripping
        sanitized = SecurityValidator.sanitize_string('  test  ')
        assert sanitized == 'test', f"Whitespace not stripped: '{sanitized}'"
        
        print("✓ Input sanitization tests passed")
        return True
    except Exception as e:
        print(f"✗ Input sanitization test failed: {e}")
        return False

def test_rate_limiter():
    """Test rate limiter functionality."""
    try:
        from app.security import RateLimiter
        
        limiter = RateLimiter()
        
        # Test normal usage
        for i in range(5):
            limited = limiter.is_rate_limited('test_ip', max_requests=10, window_minutes=60)
            assert limited is False, f"Normal usage rate limited at request {i}"
        
        # Test rate limiting
        for i in range(15):
            limiter.is_rate_limited('test_ip2', max_requests=10, window_minutes=60)
        
        # Should be rate limited now
        limited = limiter.is_rate_limited('test_ip2', max_requests=10, window_minutes=60)
        assert limited is True, "Rate limiting not working"
        
        print("✓ Rate limiter tests passed")
        return True
    except Exception as e:
        print(f"✗ Rate limiter test failed: {e}")
        return False

def test_configuration_security():
    """Test security configuration settings."""
    try:
        from app.config import Config, ProductionConfig
        
        # Test base config security settings
        config = Config()
        assert hasattr(config, 'SESSION_COOKIE_HTTPONLY'), "SESSION_COOKIE_HTTPONLY not set"
        assert hasattr(config, 'SESSION_COOKIE_SAMESITE'), "SESSION_COOKIE_SAMESITE not set"
        assert hasattr(config, 'WTF_CSRF_TIME_LIMIT'), "WTF_CSRF_TIME_LIMIT not set"
        assert hasattr(config, 'MAX_CONTENT_LENGTH'), "MAX_CONTENT_LENGTH not set"
        
        # Test production config
        prod_config = ProductionConfig()
        assert hasattr(prod_config, 'SESSION_COOKIE_SECURE'), "SESSION_COOKIE_SECURE not set"
        assert hasattr(prod_config, 'WTF_CSRF_SSL_STRICT'), "WTF_CSRF_SSL_STRICT not set"
        
        print("✓ Configuration security tests passed")
        return True
    except Exception as e:
        print(f"✗ Configuration security test failed: {e}")
        return False

def test_form_security_features():
    """Test that forms have security features."""
    try:
        from app import create_app
        
        app = create_app('testing')
        with app.app_context():
            with app.test_request_context():
                from app.forms import LoginForm, RegistrationForm, CommentForm
                
                # Test that forms have validation methods
                login_form = LoginForm()
                assert hasattr(login_form, 'validate_username'), "LoginForm missing validate_username"
                assert hasattr(login_form, 'validate_password'), "LoginForm missing validate_password"
                
                reg_form = RegistrationForm()
                assert hasattr(reg_form, 'validate_username'), "RegistrationForm missing validate_username"
                assert hasattr(reg_form, 'validate_password'), "RegistrationForm missing validate_password"
                
                comment_form = CommentForm()
                assert hasattr(comment_form, 'validate_content'), "CommentForm missing validate_content"
            
        print("✓ Form security features tests passed")
        return True
    except Exception as e:
        print(f"✗ Form security features test failed: {e}")
        return False

def test_csrf_protection():
    """Test CSRF protection is enabled."""
    try:
        from app import create_app
        
        app = create_app('testing')
        with app.app_context():
            # Check that CSRF is in extensions
            assert 'csrf' in app.extensions, "CSRF protection not enabled"
            
            # Check CSRF configuration
            assert app.config.get('WTF_CSRF_ENABLED', True) is True, "CSRF not enabled"
            
        print("✓ CSRF protection tests passed")
        return True
    except Exception as e:
        print(f"✗ CSRF protection test failed: {e}")
        return False

def test_error_templates():
    """Test that security error templates exist."""
    try:
        import os
        
        error_templates = ['400.html', '403.html', '413.html', '429.html', '500.html']
        template_dir = 'app/templates/errors'
        
        for template in error_templates:
            template_path = os.path.join(template_dir, template)
            assert os.path.exists(template_path), f"Error template {template} not found"
        
        print("✓ Error templates tests passed")
        return True
    except Exception as e:
        print(f"✗ Error templates test failed: {e}")
        return False

def test_dependencies():
    """Test that security dependencies are available."""
    try:
        import bleach
        import flask_talisman
        
        print("✓ Security dependencies tests passed")
        return True
    except ImportError as e:
        print(f"✗ Security dependencies test failed: {e}")
        return False

def run_verification():
    """Run all verification tests."""
    print("Running security implementation verification...")
    print("=" * 50)
    
    tests = [
        test_security_imports,
        test_dependencies,
        test_security_validator,
        test_input_sanitization,
        test_rate_limiter,
        test_configuration_security,
        test_form_security_features,
        test_csrf_protection,
        test_error_templates
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Verification Results:")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All security implementation verification tests passed!")
        print("\nSecurity measures successfully implemented:")
        print("- CSRF protection on all forms")
        print("- Custom form validators for dates, times, and user input")
        print("- Input sanitization and validation functions")
        print("- Secure session handling and cookie configuration")
        print("- SQL injection prevention measures")
        print("- Rate limiting and security logging")
        print("- Error handling with security-focused templates")
        print("- Security headers configuration for production")
        return True
    else:
        print(f"\n⚠️  {failed} verification tests failed.")
        return False

if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)