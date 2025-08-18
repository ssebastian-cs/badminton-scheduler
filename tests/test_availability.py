#!/usr/bin/env python3
import os
from datetime import date, time, timedelta
from app import create_app, db
from app.models import User, Availability

# Create Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

with app.app_context():
    # Get admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print('Admin user not found!')
        exit(1)
    
    # Create a test user
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            password='test123',
            role='User'
        )
        db.session.add(test_user)
        db.session.commit()
        print('Test user created!')
    
    # Add some test availability entries
    tomorrow = date.today() + timedelta(days=1)
    day_after = date.today() + timedelta(days=2)
    
    # Admin availability
    admin_availability = Availability(
        user_id=admin_user.id,
        date=tomorrow,
        start_time=time(18, 0),  # 6:00 PM
        end_time=time(20, 0)     # 8:00 PM
    )
    
    # Test user availability
    test_availability = Availability(
        user_id=test_user.id,
        date=day_after,
        start_time=time(19, 0),  # 7:00 PM
        end_time=time(21, 0)     # 9:00 PM
    )
    
    db.session.add(admin_availability)
    db.session.add(test_availability)
    db.session.commit()
    
    print('Test availability entries created!')
    print(f'Admin availability: {tomorrow} from 6:00 PM to 8:00 PM')
    print(f'Test user availability: {day_after} from 7:00 PM to 9:00 PM')
    print('Test users:')
    print('- admin / admin123 (Admin)')
    print('- testuser / test123 (User)')