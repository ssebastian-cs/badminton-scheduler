import os
import sys
from app import create_app, db
from flask.cli import with_appcontext
import click

# Create Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo('Initialized the database.')


@app.cli.command()
@with_appcontext
def create_admin():
    """Create an admin user."""
    from app.models import User
    
    username = click.prompt('Admin username')
    password = click.prompt('Admin password', hide_input=True, confirmation_prompt=True)
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        click.echo('User already exists!')
        return
    
    try:
        admin_user = User(
            username=username,
            password=password,
            role='Admin'
        )
        
        db.session.add(admin_user)
        db.session.commit()
        click.echo(f'Admin user "{username}" created successfully!')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {e}')


@app.cli.command()
@with_appcontext
def reset_db():
    """Reset database (drop all tables and recreate)."""
    if click.confirm('This will delete all data. Are you sure?'):
        db.drop_all()
        db.create_all()
        click.echo('Database reset complete!')


@app.cli.command()
@with_appcontext
def seed_db():
    """Seed database with sample data."""
    from app.models import User, Availability, Comment
    from datetime import date, time, timedelta
    
    try:
        # Create sample users
        users_data = [
            ('admin', 'admin123', 'Admin'),
            ('alice', 'password123', 'User'),
            ('bob', 'password123', 'User'),
            ('charlie', 'password123', 'User')
        ]
        
        users = []
        for username, password, role in users_data:
            if not User.query.filter_by(username=username).first():
                user = User(username=username, password=password, role=role)
                db.session.add(user)
                users.append(user)
        
        db.session.commit()
        
        # Create sample availability entries
        today = date.today()
        for i, user in enumerate(users[1:]):  # Skip admin
            for day_offset in range(1, 8):  # Next 7 days
                availability_date = today + timedelta(days=day_offset)
                start_hour = 18 + (i % 3)  # 6 PM, 7 PM, or 8 PM
                
                availability = Availability(
                    user_id=user.id,
                    date=availability_date,
                    start_time=time(start_hour, 0),
                    end_time=time(start_hour + 2, 0)
                )
                db.session.add(availability)
        
        # Create sample comments
        sample_comments = [
            "Looking forward to playing this week!",
            "Anyone up for doubles on Friday?",
            "Great games last week, thanks everyone!"
        ]
        
        for i, user in enumerate(users[1:]):  # Skip admin
            if i < len(sample_comments):
                comment = Comment(user_id=user.id, content=sample_comments[i])
                db.session.add(comment)
        
        db.session.commit()
        click.echo('Database seeded with sample data!')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error seeding database: {e}')


@app.cli.command()
def run_tests():
    """Run the complete test suite."""
    import subprocess
    
    click.echo("Running complete test suite...")
    
    try:
        # Run the comprehensive test runner
        result = subprocess.run([sys.executable, 'run_tests.py'], 
                              capture_output=True, text=True)
        
        click.echo(result.stdout)
        if result.stderr:
            click.echo("STDERR:", result.stderr)
        
        if result.returncode == 0:
            click.echo("✅ All tests completed!")
        else:
            click.echo("⚠️  Some tests failed. Check output above.")
            
    except Exception as e:
        click.echo(f"Error running tests: {e}")


@app.cli.command()
def health_check():
    """Run application health check."""
    click.echo("Running health check...")
    
    try:
        # Test database connection
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            click.echo("✅ Database connection successful")
        
        # Test critical imports
        from app.models import User, Availability, Comment, AdminAction
        click.echo("✅ All models imported successfully")
        
        from app.routes import auth, availability, comments, admin
        click.echo("✅ All route blueprints imported successfully")
        
        click.echo("✅ Health check passed!")
        
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")


if __name__ == '__main__':
    # Check if running in production
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, use a proper WSGI server
        click.echo("Production mode detected. Use a WSGI server like Gunicorn:")
        click.echo("gunicorn -w 4 -b 0.0.0.0:5000 run:app")
    else:
        # Development mode
        app.run(debug=True, host='0.0.0.0', port=5000)