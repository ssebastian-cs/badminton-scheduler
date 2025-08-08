#!/usr/bin/env python3
"""
Deployment script for Badminton Scheduler on Alwaysdata
Run this script after uploading files to set up the application.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def setup_virtual_environment():
    """Set up Python virtual environment."""
    if not os.path.exists('venv'):
        if not run_command('python3 -m venv venv', 'Creating virtual environment'):
            return False
    
    # Install requirements
    return run_command('venv/bin/pip install -r requirements.txt', 'Installing Python packages')

def setup_database():
    """Initialize the database."""
    print("🔄 Setting up database...")
    
    try:
        # Import after ensuring packages are installed
        sys.path.insert(0, os.getcwd())
        
        # Try to import and initialize the database
        from run import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if we need to create sample data
            from models import User
            if User.query.count() == 0:
                print("🔄 Creating sample admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Sample admin user created (username: admin, password: admin123)")
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

def set_file_permissions():
    """Set appropriate file permissions."""
    print("🔄 Setting file permissions...")
    
    try:
        # Set permissions for database file if it exists
        if os.path.exists('badminton_scheduler.db'):
            os.chmod('badminton_scheduler.db', 0o664)
        
        # Set permissions for instance directory
        if os.path.exists('instance'):
            os.chmod('instance', 0o775)
        
        # Set permissions for static files
        if os.path.exists('static'):
            os.chmod('static', 0o755)
            for root, dirs, files in os.walk('static'):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)
        
        # Secure environment file
        if os.path.exists('.env'):
            os.chmod('.env', 0o600)
        
        print("✅ File permissions set successfully")
        return True
        
    except Exception as e:
        print(f"❌ Setting file permissions failed: {str(e)}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.production'):
            print("🔄 Creating .env file from template...")
            with open('.env.production', 'r') as template:
                content = template.read()
            
            # Generate a random secret key
            import secrets
            secret_key = secrets.token_urlsafe(32)
            content = content.replace('your-super-secret-production-key-change-this-immediately', secret_key)
            
            with open('.env', 'w') as env_file:
                env_file.write(content)
            
            print("✅ .env file created with random secret key")
            print("⚠️  Please review and update the .env file with your specific configuration")
            return True
        else:
            print("❌ No .env.production template found")
            return False
    else:
        print("✅ .env file already exists")
        return True

def test_application():
    """Test if the application can start properly."""
    print("🔄 Testing application startup...")
    
    try:
        # Test import
        sys.path.insert(0, os.getcwd())
        from wsgi import application
        
        # Test basic configuration
        with application.app_context():
            print("✅ Application imports and configures successfully")
            return True
            
    except Exception as e:
        print(f"❌ Application test failed: {str(e)}")
        return False

def main():
    """Main deployment function."""
    print("🚀 Starting Badminton Scheduler deployment on Alwaysdata...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('run.py'):
        print("❌ Error: run.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    steps = [
        ("Create environment file", create_env_file),
        ("Set up virtual environment", setup_virtual_environment),
        ("Set up database", setup_database),
        ("Set file permissions", set_file_permissions),
        ("Test application", test_application),
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        print(f"\n📋 Step: {step_name}")
        if not step_function():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 60)
    
    if failed_steps:
        print("❌ Deployment completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n🔧 Please check the errors above and fix them manually.")
        sys.exit(1)
    else:
        print("🎉 Deployment completed successfully!")
        print("\n📝 Next steps:")
        print("1. Configure your alwaysdata web site to point to wsgi.py")
        print("2. Set up static files serving for /static/ directory")
        print("3. Test your application at your domain")
        print("4. Review and update the .env file with your specific settings")
        print("\n🌐 Your application should be accessible at:")
        print("   https://yourdomain.com/static/static_frontend.html")

if __name__ == "__main__":
    main()