#!/usr/bin/env python3
"""
Database initialization and migration script for badminton scheduler.
This script handles database setup, migrations, and initial data seeding.
"""

import os
import sys
import click
from flask import Flask
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


def create_app_for_init():
    """Create Flask app instance for database initialization."""
    from app import create_app
    return create_app(os.environ.get('FLASK_ENV', 'development'))


@click.group()
def cli():
    """Database management commands."""
    pass


@cli.command()
@click.option('--drop', is_flag=True, help='Drop existing tables before creating new ones')
@click.option('--seed', is_flag=True, help='Seed database with initial data')
def init_db(drop, seed):
    """Initialize the database with tables and optional seed data."""
    app = create_app_for_init()
    
    with app.app_context():
        from app import db
        from app.models import User, Availability, Comment, AdminAction
        
        if drop:
            click.echo('Dropping existing tables...')
            db.drop_all()
        
        click.echo('Creating database tables...')
        db.create_all()
        
        if seed:
            click.echo('Seeding database with initial data...')
            seed_database()
        
        click.echo('Database initialization complete!')


@cli.command()
def create_admin():
    """Create an admin user interactively."""
    app = create_app_for_init()
    
    with app.app_context():
        from app import db
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


@cli.command()
@click.option('--username', prompt=True, help='Username for the new user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the new user')
@click.option('--role', type=click.Choice(['User', 'Admin']), default='User', help='Role for the new user')
def create_user(username, password, role):
    """Create a new user."""
    app = create_app_for_init()
    
    with app.app_context():
        from app import db
        from app.models import User
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            click.echo('User already exists!')
            return
        
        try:
            user = User(
                username=username,
                password=password,
                role=role
            )
            
            db.session.add(user)
            db.session.commit()
            click.echo(f'{role} user "{username}" created successfully!')
            
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error creating user: {e}')


@cli.command()
def migrate_db():
    """Run database migrations."""
    app = create_app_for_init()
    
    with app.app_context():
        try:
            # Import Flask-Migrate commands
            from flask_migrate import upgrade, migrate, init
            
            # Check if migrations directory exists
            if not os.path.exists('migrations'):
                click.echo('Initializing migrations...')
                init()
            
            # Generate migration if needed
            click.echo('Generating migration...')
            migrate(message='Auto migration')
            
            # Apply migrations
            click.echo('Applying migrations...')
            upgrade()
            
            click.echo('Database migration complete!')
            
        except Exception as e:
            click.echo(f'Migration error: {e}')


@cli.command()
def reset_db():
    """Reset database (drop all tables and recreate)."""
    if not click.confirm('This will delete all data. Are you sure?'):
        return
    
    app = create_app_for_init()
    
    with app.app_context():
        from app import db
        
        click.echo('Dropping all tables...')
        db.drop_all()
        
        click.echo('Creating tables...')
        db.create_all()
        
        click.echo('Database reset complete!')


@cli.command()
def check_db():
    """Check database connection and table status."""
    app = create_app_for_init()
    
    with app.app_context():
        from app import db
        from app.models import User, Availability, Comment, AdminAction
        
        try:
            # Test database connection
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            click.echo('✓ Database connection successful')
            
            # Check tables
            tables = {
                'Users': User,
                'Availability': Availability,
                'Comments': Comment,
                'Admin Actions': AdminAction
            }
            
            for table_name, model in tables.items():
                try:
                    count = model.query.count()
                    click.echo(f'✓ {table_name}: {count} records')
                except Exception as e:
                    click.echo(f'✗ {table_name}: Error - {e}')
            
        except Exception as e:
            click.echo(f'✗ Database connection failed: {e}')


def seed_database():
    """Seed database with initial test data."""
    from app import db
    from app.models import User, Availability, Comment
    from datetime import date, time, timedelta
    
    try:
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password='admin123', role='Admin')
            db.session.add(admin)
        
        # Create test users if not exist
        test_users = [
            ('alice', 'password123', 'User'),
            ('bob', 'password123', 'User'),
            ('charlie', 'password123', 'User')
        ]
        
        users = []
        for username, password, role in test_users:
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username, password=password, role=role)
                db.session.add(user)
            users.append(user)
        
        db.session.commit()
        
        # Create sample availability entries
        today = date.today()
        for i, user in enumerate(users):
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
            (users[0].id, "Looking forward to playing this week!"),
            (users[1].id, "Anyone up for doubles on Friday?"),
            (users[2].id, "Great games last week, thanks everyone!")
        ]
        
        for user_id, content in sample_comments:
            comment = Comment(user_id=user_id, content=content)
            db.session.add(comment)
        
        db.session.commit()
        click.echo('Sample data seeded successfully!')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error seeding database: {e}')


if __name__ == '__main__':
    cli()