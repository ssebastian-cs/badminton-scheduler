#!/usr/bin/env python3
import os
from app import create_app, db
from app.models import User

# Create Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

with app.app_context():
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print('Admin user already exists!')
    else:
        # Create admin user
        admin_user = User(
            username='admin',
            password='admin123',
            role='Admin'
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully!')
        print('Username: admin')
        print('Password: admin123')