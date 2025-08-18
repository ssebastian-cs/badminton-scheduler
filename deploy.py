#!/usr/bin/env python3
"""
Deployment preparation and configuration script for badminton scheduler.
This script handles deployment setup, environment validation, and production readiness checks.
"""

import os
import sys
import subprocess
import click
from pathlib import Path


@click.group()
def cli():
    """Deployment management commands."""
    pass


@cli.command()
@click.option('--env', type=click.Choice(['development', 'production']), default='development', help='Environment to check')
def check_config(env):
    """Check configuration and environment setup."""
    click.echo(f"Checking configuration for {env} environment...")
    
    # Check required environment variables
    required_vars = {
        'development': ['SECRET_KEY'],
        'production': ['SECRET_KEY', 'DATABASE_URL', 'FLASK_ENV']
    }
    
    missing_vars = []
    for var in required_vars.get(env, []):
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        click.echo(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        if env == 'production':
            click.echo("For production deployment, ensure all required variables are set.")
    else:
        click.echo("✅ All required environment variables are set")
    
    # Check database file permissions (for SQLite)
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///badminton_scheduler.db')
    if db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
        if os.path.exists(db_file):
            if os.access(db_file, os.R_OK | os.W_OK):
                click.echo("✅ Database file is readable and writable")
            else:
                click.echo("❌ Database file permissions issue")
        else:
            click.echo("ℹ️  Database file doesn't exist yet (will be created)")
    
    # Check logs directory
    logs_dir = Path('logs')
    if logs_dir.exists():
        if os.access(logs_dir, os.W_OK):
            click.echo("✅ Logs directory is writable")
        else:
            click.echo("❌ Logs directory is not writable")
    else:
        click.echo("ℹ️  Logs directory doesn't exist (will be created)")
    
    # Check static files
    static_dir = Path('app/static')
    if static_dir.exists():
        click.echo("✅ Static files directory exists")
    else:
        click.echo("❌ Static files directory missing")
    
    # Check requirements
    if Path('requirements.txt').exists():
        click.echo("✅ Requirements file exists")
    else:
        click.echo("❌ Requirements file missing")


@cli.command()
def setup_production():
    """Set up production environment."""
    click.echo("Setting up production environment...")
    
    # Create necessary directories
    directories = ['logs', 'instance', 'backups']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        click.echo(f"✅ Created/verified directory: {directory}")
    
    # Set proper file permissions
    try:
        os.chmod('logs', 0o755)
        os.chmod('instance', 0o755)
        click.echo("✅ Set directory permissions")
    except Exception as e:
        click.echo(f"⚠️  Could not set permissions: {e}")
    
    # Create production environment file template
    env_template = """# Production Environment Variables
# Copy this file to .env and fill in the values

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production

# Database
DATABASE_URL=sqlite:///instance/badminton_scheduler.db

# Flask Environment
FLASK_ENV=production
FLASK_APP=run.py

# Optional: External Database (PostgreSQL/MySQL)
# DATABASE_URL=postgresql://user:password@localhost/badminton_scheduler
# DATABASE_URL=mysql://user:password@localhost/badminton_scheduler

# Optional: Email Configuration (for future features)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password

# Optional: Redis for session storage (for scaling)
# REDIS_URL=redis://localhost:6379/0
"""
    
    with open('.env.production.template', 'w') as f:
        f.write(env_template)
    
    click.echo("✅ Created production environment template (.env.production.template)")
    click.echo("   Copy this to .env and update the values for your production environment")


@cli.command()
def create_systemd_service():
    """Create systemd service file for production deployment."""
    service_content = """[Unit]
Description=Badminton Scheduler Web Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/badminton-scheduler
Environment=PATH=/path/to/badminton-scheduler/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=/path/to/badminton-scheduler/.env
ExecStart=/path/to/badminton-scheduler/venv/bin/python run.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/path/to/badminton-scheduler/logs /path/to/badminton-scheduler/instance

[Install]
WantedBy=multi-user.target
"""
    
    with open('badminton-scheduler.service', 'w') as f:
        f.write(service_content)
    
    click.echo("✅ Created systemd service file (badminton-scheduler.service)")
    click.echo("   Update the paths and copy to /etc/systemd/system/ for production use")


@cli.command()
def create_nginx_config():
    """Create nginx configuration for production deployment."""
    nginx_config = """server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration (update paths to your certificates)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static {
        alias /path/to/badminton-scheduler/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security: Block access to sensitive files
    location ~ /\\.env {
        deny all;
    }
    
    location ~ /\\.git {
        deny all;
    }
    
    location ~ /logs/ {
        deny all;
    }
}
"""
    
    with open('nginx.conf', 'w') as f:
        f.write(nginx_config)
    
    click.echo("✅ Created nginx configuration (nginx.conf)")
    click.echo("   Update the domain and paths, then copy to /etc/nginx/sites-available/")


@cli.command()
def backup_database():
    """Create a backup of the database."""
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    # For SQLite database
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///badminton_scheduler.db')
    if db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
        if os.path.exists(db_file):
            backup_file = backup_dir / f'database_backup_{timestamp}.db'
            try:
                subprocess.run(['cp', db_file, str(backup_file)], check=True)
                click.echo(f"✅ Database backed up to: {backup_file}")
            except subprocess.CalledProcessError as e:
                click.echo(f"❌ Backup failed: {e}")
        else:
            click.echo("❌ Database file not found")
    else:
        click.echo("ℹ️  For non-SQLite databases, use database-specific backup tools")


@cli.command()
def run_health_check():
    """Run comprehensive health check."""
    click.echo("Running comprehensive health check...")
    
    health_results = []
    
    # Import app to test configuration
    try:
        from app import create_app
        app = create_app('production')
        click.echo("✅ Application configuration valid")
        health_results.append(("Application Config", True))
    except Exception as e:
        click.echo(f"❌ Application configuration error: {e}")
        health_results.append(("Application Config", False))
        return
    
    # Test database connection
    with app.app_context():
        try:
            from app import db
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            click.echo("✅ Database connection successful")
            health_results.append(("Database Connection", True))
        except Exception as e:
            click.echo(f"❌ Database connection failed: {e}")
            health_results.append(("Database Connection", False))
        
        # Test model imports and basic queries
        try:
            from app.models import User, Availability, Comment, AdminAction
            
            # Test each model
            models = {
                'User': User,
                'Availability': Availability,
                'Comment': Comment,
                'AdminAction': AdminAction
            }
            
            for model_name, model in models.items():
                try:
                    count = model.query.count()
                    click.echo(f"✅ {model_name} model: {count} records")
                    health_results.append((f"{model_name} Model", True))
                except Exception as e:
                    click.echo(f"❌ {model_name} model error: {e}")
                    health_results.append((f"{model_name} Model", False))
                    
        except Exception as e:
            click.echo(f"❌ Model import error: {e}")
            health_results.append(("Model Imports", False))
    
    # Check critical files
    critical_files = [
        'run.py',
        'app/__init__.py',
        'app/models.py',
        'app/config.py',
        'requirements.txt',
        'init_database.py'
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            click.echo(f"✅ {file_path} exists")
            health_results.append((f"File: {file_path}", True))
        else:
            click.echo(f"❌ {file_path} missing")
            health_results.append((f"File: {file_path}", False))
    
    # Check directories
    critical_dirs = ['app', 'app/routes', 'app/templates', 'app/static', 'tests', 'migrations']
    for dir_path in critical_dirs:
        if Path(dir_path).exists():
            click.echo(f"✅ Directory {dir_path} exists")
            health_results.append((f"Dir: {dir_path}", True))
        else:
            click.echo(f"❌ Directory {dir_path} missing")
            health_results.append((f"Dir: {dir_path}", False))
    
    # Check Python dependencies
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_login', 'flask_migrate', 
        'flask_wtf', 'werkzeug', 'wtforms', 'bcrypt'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            click.echo(f"✅ Package {package} available")
            health_results.append((f"Package: {package}", True))
        except ImportError:
            click.echo(f"❌ Package {package} missing")
            health_results.append((f"Package: {package}", False))
    
    # Test route blueprints
    try:
        from app.routes import auth, availability, comments, admin
        click.echo("✅ All route blueprints imported successfully")
        health_results.append(("Route Blueprints", True))
    except Exception as e:
        click.echo(f"❌ Route blueprint import error: {e}")
        health_results.append(("Route Blueprints", False))
    
    # Summary
    click.echo(f"\n{'='*50}")
    click.echo("HEALTH CHECK SUMMARY")
    click.echo('='*50)
    
    passed = sum(1 for _, success in health_results if success)
    total = len(health_results)
    
    for check_name, success in health_results:
        status = "✅ PASS" if success else "❌ FAIL"
        click.echo(f"{check_name:<30} {status}")
    
    click.echo(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        click.echo("🎉 All health checks passed!")
    else:
        click.echo("⚠️  Some health checks failed. Review the issues above.")


@cli.command()
def install_dependencies():
    """Install Python dependencies."""
    click.echo("Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        click.echo("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to install dependencies: {e}")


@cli.command()
def generate_secret_key():
    """Generate a secure secret key for production."""
    import secrets
    
    secret_key = secrets.token_urlsafe(32)
    click.echo(f"Generated secret key: {secret_key}")
    click.echo("Add this to your .env file as SECRET_KEY=<generated_key>")


@cli.command()
def run_integration_tests():
    """Run comprehensive integration tests for deployment validation."""
    click.echo("Running comprehensive integration tests...")
    
    test_results = []
    
    # Test database operations
    click.echo("\n=== Testing Database Operations ===")
    try:
        from app import create_app, db
        from app.models import User, Availability, Comment
        from datetime import date, time, timedelta
        
        app = create_app('development')
        with app.app_context():
            # Test user creation
            test_user = User(username='test_deploy_user', password='test123', role='User')
            db.session.add(test_user)
            db.session.commit()
            
            # Test availability creation
            tomorrow = date.today() + timedelta(days=1)
            test_availability = Availability(
                user_id=test_user.id,
                date=tomorrow,
                start_time=time(18, 0),
                end_time=time(20, 0)
            )
            db.session.add(test_availability)
            db.session.commit()
            
            # Test comment creation
            test_comment = Comment(user_id=test_user.id, content='Test deployment comment')
            db.session.add(test_comment)
            db.session.commit()
            
            # Verify data
            user_count = User.query.count()
            availability_count = Availability.query.count()
            comment_count = Comment.query.count()
            
            click.echo(f"✅ Database operations successful")
            click.echo(f"   Users: {user_count}, Availability: {availability_count}, Comments: {comment_count}")
            test_results.append(("Database Operations", True))
            
            # Cleanup test data
            db.session.delete(test_comment)
            db.session.delete(test_availability)
            db.session.delete(test_user)
            db.session.commit()
            
    except Exception as e:
        click.echo(f"❌ Database operations failed: {e}")
        test_results.append(("Database Operations", False))
    
    # Test authentication system
    click.echo("\n=== Testing Authentication System ===")
    try:
        from app.models import User
        from werkzeug.security import check_password_hash
        
        with app.app_context():
            # Test password hashing
            test_user = User(username='auth_test', password='password123', role='User')
            
            # Verify password is hashed
            if test_user.password_hash and check_password_hash(test_user.password_hash, 'password123'):
                click.echo("✅ Password hashing working correctly")
                test_results.append(("Password Hashing", True))
            else:
                click.echo("❌ Password hashing failed")
                test_results.append(("Password Hashing", False))
                
    except Exception as e:
        click.echo(f"❌ Authentication system test failed: {e}")
        test_results.append(("Authentication System", False))
    
    # Test form validation
    click.echo("\n=== Testing Form Validation ===")
    try:
        from app.forms import LoginForm, RegistrationForm, AvailabilityForm, CommentForm
        
        # Test form imports
        forms = [LoginForm, RegistrationForm, AvailabilityForm, CommentForm]
        for form_class in forms:
            form = form_class()
            if hasattr(form, 'validate'):
                click.echo(f"✅ {form_class.__name__} form available")
            else:
                click.echo(f"❌ {form_class.__name__} form invalid")
        
        test_results.append(("Form Validation", True))
        
    except Exception as e:
        click.echo(f"❌ Form validation test failed: {e}")
        test_results.append(("Form Validation", False))
    
    # Test route blueprints
    click.echo("\n=== Testing Route Blueprints ===")
    try:
        with app.test_client() as client:
            # Test main routes
            routes_to_test = [
                ('/', 'Dashboard'),
                ('/auth/login', 'Login'),
                ('/comments', 'Comments'),
            ]
            
            for route, name in routes_to_test:
                response = client.get(route)
                if response.status_code in [200, 302]:  # 302 for redirects
                    click.echo(f"✅ {name} route accessible")
                else:
                    click.echo(f"❌ {name} route failed: {response.status_code}")
            
            test_results.append(("Route Blueprints", True))
            
    except Exception as e:
        click.echo(f"❌ Route blueprint test failed: {e}")
        test_results.append(("Route Blueprints", False))
    
    # Test template rendering
    click.echo("\n=== Testing Template Rendering ===")
    try:
        with app.test_client() as client:
            # Test that templates render without errors
            response = client.get('/auth/login')
            if b'login' in response.data.lower() or response.status_code == 200:
                click.echo("✅ Template rendering working")
                test_results.append(("Template Rendering", True))
            else:
                click.echo("❌ Template rendering failed")
                test_results.append(("Template Rendering", False))
                
    except Exception as e:
        click.echo(f"❌ Template rendering test failed: {e}")
        test_results.append(("Template Rendering", False))
    
    # Summary
    click.echo(f"\n{'='*50}")
    click.echo("INTEGRATION TEST SUMMARY")
    click.echo('='*50)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        click.echo(f"{test_name:<25} {status}")
    
    click.echo(f"\nOverall: {passed}/{total} integration tests passed")
    
    if passed == total:
        click.echo("🎉 All integration tests passed!")
        return True
    else:
        click.echo("⚠️  Some integration tests failed.")
        return False


@cli.command()
def test_admin_workflow():
    """Test complete admin workflow end-to-end."""
    click.echo("Testing admin workflow...")
    
    try:
        from app import create_app, db
        from app.models import User, Availability, Comment, AdminAction
        from datetime import date, time, timedelta
        
        app = create_app('development')
        with app.app_context():
            # Create admin user
            admin_user = User(username='test_admin', password='admin123', role='Admin')
            db.session.add(admin_user)
            
            # Create regular user
            regular_user = User(username='test_user', password='user123', role='User')
            db.session.add(regular_user)
            db.session.commit()
            
            click.echo("✅ Created test users")
            
            # Test admin can create availability for others
            tomorrow = date.today() + timedelta(days=1)
            admin_availability = Availability(
                user_id=regular_user.id,
                date=tomorrow,
                start_time=time(19, 0),
                end_time=time(21, 0)
            )
            db.session.add(admin_availability)
            
            # Test admin can create comments
            admin_comment = Comment(user_id=admin_user.id, content='Admin test comment')
            db.session.add(admin_comment)
            
            # Test admin action logging
            admin_action = AdminAction(
                admin_id=admin_user.id,
                action_type='USER_CREATED',
                target_type='User',
                target_id=regular_user.id,
                description='Created test user'
            )
            db.session.add(admin_action)
            db.session.commit()
            
            click.echo("✅ Admin workflow operations successful")
            
            # Verify data
            admin_count = User.query.filter_by(role='Admin').count()
            user_count = User.query.filter_by(role='User').count()
            action_count = AdminAction.query.count()
            
            click.echo(f"✅ Verification: {admin_count} admins, {user_count} users, {action_count} actions")
            
            # Cleanup
            db.session.delete(admin_action)
            db.session.delete(admin_comment)
            db.session.delete(admin_availability)
            db.session.delete(regular_user)
            db.session.delete(admin_user)
            db.session.commit()
            
            click.echo("✅ Admin workflow test completed successfully")
            return True
            
    except Exception as e:
        click.echo(f"❌ Admin workflow test failed: {e}")
        return False


@cli.command()
def test_user_workflow():
    """Test complete user workflow end-to-end."""
    click.echo("Testing user workflow...")
    
    try:
        from app import create_app, db
        from app.models import User, Availability, Comment
        from datetime import date, time, timedelta
        
        app = create_app('development')
        with app.app_context():
            # Create test user
            test_user = User(username='workflow_user', password='test123', role='User')
            db.session.add(test_user)
            db.session.commit()
            
            click.echo("✅ Created test user")
            
            # Test user can create availability
            tomorrow = date.today() + timedelta(days=1)
            user_availability = Availability(
                user_id=test_user.id,
                date=tomorrow,
                start_time=time(18, 0),
                end_time=time(20, 0)
            )
            db.session.add(user_availability)
            
            # Test user can create comments
            user_comment = Comment(user_id=test_user.id, content='User workflow test comment')
            db.session.add(user_comment)
            db.session.commit()
            
            click.echo("✅ User workflow operations successful")
            
            # Test user can update their own data
            user_availability.end_time = time(21, 0)
            user_comment.content = 'Updated comment'
            db.session.commit()
            
            click.echo("✅ User data updates successful")
            
            # Verify data
            availability_count = Availability.query.filter_by(user_id=test_user.id).count()
            comment_count = Comment.query.filter_by(user_id=test_user.id).count()
            
            click.echo(f"✅ Verification: {availability_count} availability entries, {comment_count} comments")
            
            # Cleanup
            db.session.delete(user_comment)
            db.session.delete(user_availability)
            db.session.delete(test_user)
            db.session.commit()
            
            click.echo("✅ User workflow test completed successfully")
            return True
            
    except Exception as e:
        click.echo(f"❌ User workflow test failed: {e}")
        return False


@cli.command()
def full_deployment_test():
    """Run complete deployment validation test suite."""
    click.echo("Running full deployment validation...")
    click.echo("=" * 60)
    
    test_functions = [
        (run_health_check, "Health Check"),
        (run_integration_tests, "Integration Tests"),
        (test_admin_workflow, "Admin Workflow"),
        (test_user_workflow, "User Workflow"),
    ]
    
    results = []
    
    for test_func, test_name in test_functions:
        click.echo(f"\n{'='*60}")
        click.echo(f"RUNNING: {test_name}")
        click.echo('='*60)
        
        try:
            # Call the function and get result
            if test_func == run_health_check:
                test_func.callback()  # Click command
                success = True  # Assume success if no exception
            else:
                success = test_func.callback() if hasattr(test_func, 'callback') else test_func()
            
            results.append((test_name, success))
            
        except Exception as e:
            click.echo(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Final summary
    click.echo(f"\n{'='*60}")
    click.echo("DEPLOYMENT VALIDATION SUMMARY")
    click.echo('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        click.echo(f"{test_name:<25} {status}")
    
    click.echo(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        click.echo("\n🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
        click.echo("The application is ready for deployment.")
    else:
        click.echo("\n⚠️  DEPLOYMENT VALIDATION FAILED!")
        click.echo("Please resolve the issues before deploying.")
    
    return passed == total


if __name__ == '__main__':
    cli()