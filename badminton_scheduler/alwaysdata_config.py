"""
Alwaysdata-specific configuration for Badminton Scheduler
This file contains optimizations and settings specific to alwaysdata hosting.
"""

import os
from pathlib import Path

class AlwaysdataConfig:
    """Configuration class optimized for alwaysdata hosting."""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///badminton_scheduler.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Production settings
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Session configuration
    SESSION_COOKIE_SECURE = True  # Use HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Security headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    # File upload settings (if needed)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application-specific settings
    ITEMS_PER_PAGE = 50
    MAX_SEARCH_RESULTS = 1000
    
    @staticmethod
    def init_app(app):
        """Initialize application with alwaysdata-specific settings."""
        
        # Ensure instance folder exists
        try:
            os.makedirs(app.instance_path, exist_ok=True)
        except OSError:
            pass
        
        # Configure logging for production
        if not app.debug and not app.testing:
            import logging
            from logging.handlers import RotatingFileHandler
            
            # Create logs directory
            logs_dir = os.path.join(app.instance_path, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            # Set up file handler
            file_handler = RotatingFileHandler(
                os.path.join(logs_dir, 'badminton_scheduler.log'),
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Badminton Scheduler startup')

class DevelopmentConfig(AlwaysdataConfig):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(AlwaysdataConfig):
    """Production configuration for alwaysdata."""
    
    @classmethod
    def init_app(cls, app):
        AlwaysdataConfig.init_app(app)
        
        # Production-specific initialization
        # Enable error reporting to logs
        import logging
        app.logger.setLevel(logging.INFO)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}