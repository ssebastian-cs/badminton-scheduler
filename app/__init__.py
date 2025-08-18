from flask import Flask, request, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
talisman = Talisman()


def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'production':
        from .config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from .config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from .config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize Talisman for security headers (only in production)
    if config_name == 'production':
        talisman.init_app(app, 
            force_https=True,
            strict_transport_security=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline'",
                'style-src': "'self' 'unsafe-inline'",
                'img-src': "'self' data:",
                'font-src': "'self'",
                'connect-src': "'self'",
                'frame-ancestors': "'none'"
            }
        )
    
    # Configure comprehensive logging
    from .logging_config import setup_logging
    app_logger, security_logger = setup_logging(app)
    
    # Initialize error tracking
    from .error_tracking import error_tracker
    error_tracker.init_app(app)
    
    # Comprehensive security middleware
    @app.before_request
    def security_checks():
        """Perform comprehensive security checks on each request."""
        from .security import rate_limiter, log_security_event, secure_headers_middleware
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Store client IP in g for use in routes
        g.client_ip = client_ip
        
        # Check if IP is blocked
        if rate_limiter.is_blocked(client_ip):
            log_security_event('RATE_LIMIT_BLOCK', f'Blocked IP attempted access: {client_ip}', 'WARNING')
            from flask import abort
            abort(429)
        
        # Enhanced rate limiting based on endpoint type
        if request.endpoint:
            if request.endpoint.endswith('login'):
                # Stricter rate limiting for login endpoint
                if rate_limiter.is_rate_limited(f"login_{client_ip}", max_requests=10, window_minutes=15):
                    log_security_event('LOGIN_RATE_LIMIT_EXCEEDED', f'Login rate limit exceeded for IP: {client_ip}', 'WARNING')
                    from flask import abort
                    abort(429)
            elif request.method == 'POST' and not request.endpoint.startswith('static'):
                # Rate limiting for form submissions
                if rate_limiter.is_rate_limited(f"form_{client_ip}", max_requests=20, window_minutes=10):
                    log_security_event('FORM_RATE_LIMIT_EXCEEDED', f'Form submission rate limit exceeded for IP: {client_ip}', 'WARNING')
                    from flask import abort
                    abort(429)
            elif not request.endpoint.startswith('static'):
                # General rate limiting for non-static requests
                if rate_limiter.is_rate_limited(client_ip, max_requests=100, window_minutes=60):
                    log_security_event('RATE_LIMIT_EXCEEDED', f'Rate limit exceeded for IP: {client_ip}', 'WARNING')
                    from flask import abort
                    abort(429)
        
        # Check request size
        max_size = app.config.get('MAX_CONTENT_LENGTH', 512*1024)
        if request.content_length and request.content_length > max_size:
            log_security_event('REQUEST_TOO_LARGE', f'Request size {request.content_length} exceeds limit', 'WARNING')
            from flask import abort
            abort(413)
        
        # Validate request method
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
        if request.method not in allowed_methods:
            log_security_event('INVALID_METHOD', f'Invalid HTTP method {request.method} from {client_ip}', 'WARNING')
            from flask import abort
            abort(405)
        
        # Check for suspicious headers
        suspicious_headers = ['x-forwarded-host', 'x-original-url', 'x-rewrite-url']
        for header in suspicious_headers:
            if header in request.headers:
                log_security_event('SUSPICIOUS_HEADER', f'Header {header} detected from {client_ip}', 'WARNING')
        
        # Validate User-Agent (block empty or suspicious user agents)
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            log_security_event('SUSPICIOUS_USER_AGENT', f'Empty or short User-Agent from {client_ip}', 'WARNING')
        
        # Check for common attack patterns in URL
        suspicious_patterns = ['../', '..\\', '<script', 'javascript:', 'vbscript:', 'data:']
        request_url = request.url.lower()
        for pattern in suspicious_patterns:
            if pattern in request_url:
                log_security_event('SUSPICIOUS_URL', f'Suspicious URL pattern {pattern} from {client_ip}', 'ERROR')
                from flask import abort
                abort(400)
    
    @app.after_request
    def add_security_headers(response):
        """Add comprehensive security headers to all responses."""
        from .security import secure_headers_middleware
        
        # Add security headers
        headers = secure_headers_middleware()
        for header, value in headers.items():
            response.headers[header] = value
        
        # Add CSP header if not in development
        if not app.debug:
            csp_policy = app.config.get('CSP_POLICY', {})
            if csp_policy:
                csp_string = '; '.join([f"{key} {value}" for key, value in csp_policy.items()])
                response.headers['Content-Security-Policy'] = csp_string
        
        return response
    
    # Register comprehensive error handlers
    from .error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Register template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        if text is None:
            return ''
        return text.replace('\n', '<br>\n')
    
    # Import models so Flask-Migrate can detect them
    from . import models
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.availability import availability_bp
    from .routes.comments import comments_bp
    from .routes.admin import admin_bp
    from .routes.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(availability_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(health_bp)
    
    return app