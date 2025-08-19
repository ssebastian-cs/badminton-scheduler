import os
from datetime import timedelta


class Config:
    """Base configuration class with enhanced security settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration for enhanced security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)  # Reduced session time
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to cookies
    SESSION_COOKIE_SAMESITE = 'Strict'  # Enhanced CSRF protection
    SESSION_COOKIE_NAME = 'badminton_session'  # Custom session name
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on each request
    
    # CSRF configuration - Enhanced security
    WTF_CSRF_TIME_LIMIT = 1800  # CSRF token expires after 30 minutes (in seconds)
    WTF_CSRF_SSL_STRICT = False  # Set to True in production with HTTPS
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    
    # Security headers
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    
    # Rate limiting configuration - Enhanced limits
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Input validation limits - Stricter limits
    MAX_CONTENT_LENGTH = 512 * 1024  # 512KB max request size (reduced)
    
    # Security configuration
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'security-salt-change-in-production'
    
    # Rate limiting per endpoint
    LOGIN_RATE_LIMIT = "5 per minute"  # Stricter login rate limiting
    API_RATE_LIMIT = "30 per minute"   # API endpoint rate limiting
    FORM_RATE_LIMIT = "10 per minute"  # Form submission rate limiting
    
    # Security timeouts
    LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes lockout after failed attempts
    MAX_LOGIN_ATTEMPTS = 3       # Maximum login attempts before lockout
    
    # Database performance and security (SQLite compatible)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,  # Increased to 1 hour
        'echo': False,         # Disable SQL echo by default
        'connect_args': {
            'check_same_thread': False,
            'timeout': 20,
            'isolation_level': None  # Enable autocommit mode for SQLite
        }
    }
    
    # Content Security Policy
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
        'connect-src': "'self'",
        'frame-ancestors': "'none'",
        'form-action': "'self'",
        'base-uri': "'self'"
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///badminton_scheduler_dev.db'
    SQLALCHEMY_ECHO = True  # Log SQL queries in development
    
    # SQLite-compatible database options for development
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'echo': True,  # Enable SQL echo in development
        'connect_args': {
            'check_same_thread': False,
            'timeout': 20,
            'isolation_level': None
        }
    }


class ProductionConfig(Config):
    """Production configuration with maximum security."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///badminton_scheduler.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_SAMESITE = 'Strict'  # Strictest CSRF protection
    WTF_CSRF_SSL_STRICT = True  # Strict CSRF over HTTPS
    SECRET_KEY = os.environ.get('SECRET_KEY') or Config.SECRET_KEY
    
    # Stricter session settings for production
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Even shorter session in production
    WTF_CSRF_TIME_LIMIT = 900  # Shorter CSRF token lifetime (15 minutes in seconds)
    
    # Stricter rate limiting for production
    LOGIN_RATE_LIMIT = "3 per minute"  # Even stricter login rate limiting
    API_RATE_LIMIT = "20 per minute"   # Reduced API rate limiting
    FORM_RATE_LIMIT = "5 per minute"   # Reduced form submission rate limiting
    MAX_LOGIN_ATTEMPTS = 3             # Maximum login attempts
    LOGIN_ATTEMPT_TIMEOUT = 600        # 10 minutes lockout in production
    
    # Stricter content limits
    MAX_CONTENT_LENGTH = 256 * 1024  # 256KB max request size in production
    
    # Enhanced database performance and security for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,  # 1 hour recycle time
        'pool_size': 20,       # Larger pool for production
        'max_overflow': 30,    # More overflow connections
        'pool_timeout': 30,    # Connection timeout
        'echo': False,         # Never echo SQL in production
        'echo_pool': False,    # Disable pool logging
        'connect_args': {
            'check_same_thread': False,
            'timeout': 10,     # Shorter timeout in production
            'isolation_level': None  # Enable autocommit mode
        }
    }


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
    # Simplified database options for SQLite testing
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'echo': False,
        'connect_args': {
            'check_same_thread': False,
            'timeout': 20
        }
    }