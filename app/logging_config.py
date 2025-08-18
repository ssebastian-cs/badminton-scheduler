"""
Comprehensive logging configuration for the Badminton Scheduler application.
Provides structured logging for debugging, monitoring, and security events.
"""

import logging
import logging.handlers
import os
from datetime import datetime, timezone
from flask import request
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter that creates structured log entries with context."""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        try:
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'endpoint': request.endpoint,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                }
                
                # Skip user context to avoid circular dependency with database queries
                pass
        except RuntimeError:
            # Outside request context
            pass
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class SecurityEventLogger:
    """Specialized logger for security events with enhanced context."""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security logging for the Flask app."""
        self.app = app
        
        # Create security logger
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate logs
        if not self.logger.handlers:
            # Create security log file handler
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            security_handler = logging.handlers.RotatingFileHandler(
                'logs/security.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=10
            )
            security_handler.setLevel(logging.INFO)
            security_handler.setFormatter(StructuredFormatter())
            
            self.logger.addHandler(security_handler)
    
    def log_event(self, event_type, message, level='INFO', **kwargs):
        """
        Log a security event with structured data.
        
        Args:
            event_type: Type of security event (e.g., 'LOGIN_ATTEMPT', 'PERMISSION_DENIED')
            message: Human-readable message
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional context data
        """
        if not self.logger:
            return
        
        # Create structured security event
        event_data = {
            'event_type': event_type,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        # Add request context
        try:
            if request:
                event_data['request_context'] = {
                    'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                    'method': request.method,
                    'url': request.url,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'referer': request.headers.get('Referer', 'None')
                }
                
                # Skip user context to avoid circular dependency with database queries
                pass
        except RuntimeError:
            pass
        
        # Log with appropriate level
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(event_data, default=str))


class ApplicationLogger:
    """Main application logger with multiple handlers for different log types."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize comprehensive logging for the Flask app."""
        self.app = app
        
        # Don't configure logging in testing
        if app.testing:
            return
        
        # Create logs directory
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Console handler for development
        if app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Main application log file
        app_handler = logging.handlers.RotatingFileHandler(
            'logs/application.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(app_handler)
        
        # Error log file (errors and above only)
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
        
        # Database operations log
        db_logger = logging.getLogger('sqlalchemy.engine')
        if app.debug:
            db_logger.setLevel(logging.INFO)
            db_handler = logging.handlers.RotatingFileHandler(
                'logs/database.log',
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            db_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            db_logger.addHandler(db_handler)
        
        # Set up Flask app logger
        app.logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)
        
        # Log application startup
        app.logger.info(f'Badminton Scheduler starting up - Debug: {app.debug}')


def setup_logging(app):
    """
    Set up comprehensive logging for the application.
    
    Args:
        app: Flask application instance
    
    Returns:
        tuple: (app_logger, security_logger)
    """
    # Initialize application logging
    app_logger = ApplicationLogger(app)
    
    # Initialize security logging
    security_logger = SecurityEventLogger(app)
    
    return app_logger, security_logger


def log_user_action(action, details=None, level='INFO'):
    """
    Log user actions for audit trail.
    
    Args:
        action: Description of the action performed
        details: Additional details about the action
        level: Log level
    """
    logger = logging.getLogger('user_actions')
    
    log_data = {
        'action': action,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': details or {}
    }
    
    # Skip user context to avoid circular dependency with database queries
    pass
    
    # Add request context
    try:
        if request:
            log_data['request'] = {
                'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                'method': request.method,
                'endpoint': request.endpoint
            }
    except RuntimeError:
        pass
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, json.dumps(log_data, default=str))


def log_database_operation(operation, table, record_id=None, success=True, error=None):
    """
    Log database operations for audit and debugging.
    
    Args:
        operation: Type of operation (CREATE, READ, UPDATE, DELETE)
        table: Database table name
        record_id: ID of the record (if applicable)
        success: Whether the operation was successful
        error: Error message if operation failed
    """
    logger = logging.getLogger('database_operations')
    
    log_data = {
        'operation': operation,
        'table': table,
        'record_id': record_id,
        'success': success,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if error:
        log_data['error'] = str(error)
    
    # Skip user context to avoid circular dependency with database queries
    pass
    
    level = logging.INFO if success else logging.ERROR
    logger.log(level, json.dumps(log_data, default=str))


# Global security logger instance
security_logger = SecurityEventLogger()