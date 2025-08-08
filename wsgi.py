"""
WSGI config for Badminton Scheduler - Alwaysdata Deployment

It exposes the WSGI callable as a module-level variable named ``application``.
Optimized for alwaysdata hosting platform.
"""
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Activate virtual environment if it exists
venv_activate = os.path.join(project_dir, 'venv', 'bin', 'activate_this.py')
if os.path.exists(venv_activate):
    exec(open(venv_activate).read(), {'__file__': venv_activate})

# Import the Flask application
try:
    from run import app as application
except ImportError:
    # Fallback to direct app import
    from app import app as application

# Ensure the application is properly configured for production
if hasattr(application, 'config'):
    # Set production defaults
    application.config.setdefault('ENV', 'production')
    application.config.setdefault('DEBUG', False)
    
    # Ensure database directory exists
    db_url = application.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

if __name__ == "__main__":
    application.run()
