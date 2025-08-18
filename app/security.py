"""Security utilities for input validation, sanitization, and protection."""

import re
import html
import bleach
from flask import request, abort, current_app
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import secrets


class SecurityValidator:
    """Comprehensive security validation and sanitization utilities."""
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'union\s+select', r'drop\s+table', r'delete\s+from', r'insert\s+into',
        r'update\s+set', r'create\s+table', r'alter\s+table', r'exec\s*\(',
        r'execute\s*\(', r'sp_executesql', r'xp_cmdshell', r'--', r'/\*', r'\*/',
        r';\s*drop', r';\s*delete', r';\s*insert', r';\s*update', r';\s*create',
        r"'\s*;\s*drop", r"'\s*or\s*'1'\s*=\s*'1", r"'\s*or\s*1\s*=\s*1"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>', r'</script>', r'javascript:', r'vbscript:', r'data:',
        r'onload\s*=', r'onerror\s*=', r'onclick\s*=', r'onmouseover\s*=',
        r'onfocus\s*=', r'onblur\s*=', r'onchange\s*=', r'onsubmit\s*=',
        r'onkeydown\s*=', r'onkeyup\s*=', r'onkeypress\s*=', r'eval\s*\(',
        r'expression\s*\(', r'url\s*\(', r'@import'
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./', r'\.\.\\', r'%2e%2e%2f', r'%2e%2e%5c', r'..%2f', r'..%5c'
    ]
    
    @staticmethod
    def sanitize_string(input_string, max_length=None, allow_html=False):
        """
        Sanitize string input to prevent XSS and injection attacks.
        
        Args:
            input_string (str): The input string to sanitize
            max_length (int): Maximum allowed length
            allow_html (bool): Whether to allow safe HTML tags
            
        Returns:
            str: Sanitized string
        """
        if not input_string:
            return input_string
        
        # Convert to string if not already
        input_string = str(input_string)
        
        # Strip whitespace
        sanitized = input_string.strip()
        
        # Check length limit
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove null bytes and control characters (but keep tab, newline, carriage return)
        sanitized = ''.join(char for char in sanitized 
                          if ord(char) >= 32 or char in ['\t', '\n', '\r'])
        
        if allow_html:
            # Allow only safe HTML tags and strip dangerous content
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
            allowed_attributes = {}
            sanitized = bleach.clean(sanitized, tags=allowed_tags, 
                                   attributes=allowed_attributes, strip=True)
        else:
            # HTML escape all content
            sanitized = html.escape(sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_against_injection(input_string, check_sql=True, check_xss=True, check_path=True):
        """
        Validate input against common injection patterns.
        
        Args:
            input_string (str): Input to validate
            check_sql (bool): Check for SQL injection patterns
            check_xss (bool): Check for XSS patterns
            check_path (bool): Check for path traversal patterns
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not input_string:
            return True, None
        
        input_lower = input_string.lower()
        
        if check_sql:
            for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    return False, "Input contains potentially malicious SQL content"
        
        if check_xss:
            for pattern in SecurityValidator.XSS_PATTERNS:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    return False, "Input contains potentially malicious script content"
        
        if check_path:
            for pattern in SecurityValidator.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    return False, "Input contains potentially malicious path content"
        
        return True, None
    
    @staticmethod
    def validate_username(username):
        """
        Validate username format and security.
        
        Args:
            username (str): Username to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        # Length check
        if len(username) < 3 or len(username) > 20:
            return False, "Username must be between 3 and 20 characters"
        
        # Format check
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Security check
        is_valid, error_msg = SecurityValidator.validate_against_injection(username)
        if not is_valid:
            return False, "Username contains invalid content"
        
        return True, None
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength and security.
        
        Args:
            password (str): Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        # Length check
        if len(password) < 6 or len(password) > 128:
            return False, "Password must be between 6 and 128 characters"
        
        # Check for null bytes and control characters
        if '\x00' in password or any(ord(char) < 32 for char in password 
                                   if char not in ['\t', '\n', '\r']):
            return False, "Password contains invalid characters"
        
        # Basic strength check
        has_letter = re.search(r'[a-zA-Z]', password)
        has_number = re.search(r'[0-9]', password)
        
        if not has_letter or not has_number:
            return False, "Password must contain at least one letter and one number"
        
        return True, None
    
    @staticmethod
    def generate_csrf_token():
        """Generate a secure CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_sensitive_data(data):
        """Hash sensitive data for logging or comparison."""
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]


class RateLimiter:
    """Enhanced in-memory rate limiter with authentication-specific features."""
    
    def __init__(self):
        self.requests = {}
        self.blocked_ips = {}
        self.login_attempts = {}  # Track failed login attempts
        self.locked_accounts = {}  # Track locked user accounts
    
    def is_rate_limited(self, identifier, max_requests=100, window_minutes=60):
        """
        Check if an identifier (IP, user) is rate limited.
        
        Args:
            identifier (str): Unique identifier (IP address, user ID)
            max_requests (int): Maximum requests allowed
            window_minutes (int): Time window in minutes
            
        Returns:
            bool: True if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        
        # Check current request count before adding
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        current_requests = len(self.requests[identifier])
        
        # Check if adding this request would exceed the limit
        if current_requests >= max_requests:
            # Block IP for extended period if severely over limit
            if current_requests >= max_requests * 2:
                self.blocked_ips[identifier] = now + timedelta(hours=1)
            return True
        
        # Add current request after checking
        self.requests[identifier].append(now)
        return False
    
    def is_blocked(self, identifier):
        """Check if an identifier is temporarily blocked."""
        if identifier in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[identifier]:
                return True
            else:
                del self.blocked_ips[identifier]
        return False
    
    def record_login_attempt(self, identifier, success=False):
        """
        Record a login attempt for rate limiting authentication.
        
        Args:
            identifier (str): IP address or username
            success (bool): Whether the login was successful
        """
        now = datetime.utcnow()
        
        if success:
            # Clear failed attempts on successful login
            if identifier in self.login_attempts:
                del self.login_attempts[identifier]
            return
        
        # Record failed attempt
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        self.login_attempts[identifier].append(now)
        
        # Clean old attempts (older than 15 minutes)
        cutoff = now - timedelta(minutes=15)
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt > cutoff
        ]
    
    def is_login_rate_limited(self, identifier, max_attempts=3, window_minutes=15):
        """
        Check if login attempts are rate limited.
        
        Args:
            identifier (str): IP address or username
            max_attempts (int): Maximum failed attempts allowed
            window_minutes (int): Time window in minutes
            
        Returns:
            tuple: (is_limited, remaining_attempts, lockout_time)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self.login_attempts:
            return False, max_attempts, None
        
        # Clean old attempts
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt > window_start
        ]
        
        current_attempts = len(self.login_attempts[identifier])
        remaining = max_attempts - current_attempts
        
        if current_attempts >= max_attempts:
            # Calculate lockout time (exponential backoff)
            lockout_minutes = min(window_minutes * (2 ** (current_attempts - max_attempts)), 60)
            lockout_time = now + timedelta(minutes=lockout_minutes)
            return True, 0, lockout_time
        
        return False, remaining, None
    
    def lock_account(self, username, duration_minutes=30):
        """
        Temporarily lock a user account.
        
        Args:
            username (str): Username to lock
            duration_minutes (int): Lock duration in minutes
        """
        now = datetime.utcnow()
        self.locked_accounts[username] = now + timedelta(minutes=duration_minutes)
    
    def is_account_locked(self, username):
        """
        Check if a user account is locked.
        
        Args:
            username (str): Username to check
            
        Returns:
            tuple: (is_locked, unlock_time)
        """
        if username not in self.locked_accounts:
            return False, None
        
        unlock_time = self.locked_accounts[username]
        if datetime.utcnow() >= unlock_time:
            del self.locked_accounts[username]
            return False, None
        
        return True, unlock_time


# Global rate limiter instance
rate_limiter = RateLimiter()


def validate_request_security():
    """Decorator to validate request security."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Check if IP is blocked
            if rate_limiter.is_blocked(client_ip):
                abort(429)  # Too Many Requests
            
            # Basic rate limiting
            if rate_limiter.is_rate_limited(client_ip, max_requests=100, window_minutes=60):
                abort(429)
            
            # Validate request size
            if request.content_length and request.content_length > current_app.config.get('MAX_CONTENT_LENGTH', 512*1024):
                abort(413)  # Request Entity Too Large
            
            # Check for suspicious headers
            suspicious_headers = ['x-forwarded-host', 'x-original-url', 'x-rewrite-url']
            for header in suspicious_headers:
                if header in request.headers:
                    log_security_event('SUSPICIOUS_HEADER', f'Header {header} from {client_ip}', 'WARNING')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_endpoint(max_requests=10, window_minutes=10, per_user=False):
    """
    Decorator for endpoint-specific rate limiting.
    
    Args:
        max_requests (int): Maximum requests allowed
        window_minutes (int): Time window in minutes
        per_user (bool): Apply rate limiting per user instead of per IP
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier for rate limiting
            if per_user and hasattr(current_user, 'id') and current_user.is_authenticated:
                identifier = f"user_{current_user.id}_{f.__name__}"
            else:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if client_ip:
                    client_ip = client_ip.split(',')[0].strip()
                identifier = f"ip_{client_ip}_{f.__name__}"
            
            # Check rate limit
            if rate_limiter.is_rate_limited(identifier, max_requests, window_minutes):
                log_security_event('ENDPOINT_RATE_LIMITED', 
                                 f'Rate limit exceeded for {f.__name__}: {identifier}', 'WARNING')
                abort(429)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def csrf_protect_ajax():
    """Decorator to protect AJAX endpoints with CSRF validation."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for CSRF token in headers or form data
            csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
            
            if not csrf_token:
                log_security_event('MISSING_CSRF_TOKEN', 
                                 f'AJAX request without CSRF token to {f.__name__}', 'WARNING')
                abort(400)
            
            # Validate CSRF token
            if not validate_csrf_token_manually(csrf_token):
                abort(400)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_form_data(form_data):
    """
    Sanitize all form data fields with comprehensive validation.
    
    Args:
        form_data (dict): Form data dictionary
        
    Returns:
        dict: Sanitized form data
    """
    sanitized = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            # Validate against injection attacks
            is_valid, error_msg = SecurityValidator.validate_against_injection(value)
            if not is_valid:
                log_security_event('MALICIOUS_INPUT_DETECTED', 
                                 f'Field {key}: {error_msg}', 'ERROR')
                # Don't process the form if malicious content is detected
                abort(400)
            
            # Sanitize the value based on field type
            max_length = 1000
            if key in ['username']:
                max_length = 20
            elif key in ['password']:
                max_length = 128
            elif key in ['content', 'comment']:
                max_length = 1000
            elif key in ['role']:
                max_length = 10
            
            sanitized[key] = SecurityValidator.sanitize_string(value, max_length=max_length)
        else:
            sanitized[key] = value
    
    return sanitized


def validate_csrf_token_manually(token):
    """
    Manually validate CSRF token for AJAX requests.
    
    Args:
        token (str): CSRF token to validate
        
    Returns:
        bool: True if token is valid
    """
    try:
        from flask_wtf.csrf import validate_csrf
        validate_csrf(token)
        return True
    except Exception as e:
        log_security_event('CSRF_VALIDATION_FAILED', 
                         f'Invalid CSRF token: {str(e)}', 'WARNING')
        return False


def secure_headers_middleware():
    """
    Add security headers to all responses.
    
    Returns:
        dict: Security headers to add
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


def log_security_event(event_type, details, severity='INFO'):
    """
    Log security-related events.
    
    Args:
        event_type (str): Type of security event
        details (str): Event details
        severity (str): Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    log_message = f"SECURITY [{severity}] {event_type}: {details} | IP: {client_ip} | User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    
    if severity == 'CRITICAL':
        current_app.logger.critical(log_message)
    elif severity == 'ERROR':
        current_app.logger.error(log_message)
    elif severity == 'WARNING':
        current_app.logger.warning(log_message)
    else:
        current_app.logger.info(log_message)


def secure_filename(filename):
    """
    Secure a filename by removing dangerous characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Secured filename
    """
    if not filename:
        return filename
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename