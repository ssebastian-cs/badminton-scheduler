#!/usr/bin/env python3
"""
Create test data for the badminton scheduler application.
"""

from run import app, db, User, Availability
from datetime import datetime, date, timedelta

def create_test_data():
    """Create test users and availability data."""
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(username='admin', email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print("Created admin user")
        
        # Check if regular user already exists
        user = User.query.filter_by(username='john_smith').first()
        if not user:
            # Create regular user
            user = User(username='john_smith', email='john@test.com', is_admin=False)
            user.set_password('password123')
            db.session.add(user)
            print("Created regular user")
        
        # Create another regular user
        user2 = User.query.filter_by(username='jane_doe').first()
        if not user2:
            user2 = User(username='jane_doe', email='jane@test.com', is_admin=False)
            user2.set_password('password123')
            db.session.add(user2)
            print("Created second regular user")
        
        db.session.commit()
        
        # Create availability data for different dates
        today = date.today()
        
        # Clear existing availability data
        Availability.query.delete()
        
        availabilities = [
            # Today's entries
            Availability(user_id=admin.id, date=today, status='available', 
                        time_start=datetime.strptime('19:00', '%H:%M').time(),
                        time_end=datetime.strptime('21:00', '%H:%M').time(),
                        is_all_day=False, time_slot='19:00-21:00'),
            Availability(user_id=user.id, date=today, status='tentative', 
                        is_all_day=True, time_slot=None),
            Availability(user_id=user2.id, date=today, status='available',
                        time_start=datetime.strptime('18:00', '%H:%M').time(),
                        time_end=datetime.strptime('20:00', '%H:%M').time(),
                        is_all_day=False, time_slot='18:00-20:00'),
            
            # Yesterday's entries
            Availability(user_id=admin.id, date=today - timedelta(days=1), 
                        status='not_available', 
                        time_start=datetime.strptime('18:00', '%H:%M').time(),
                        time_end=datetime.strptime('20:00', '%H:%M').time(),
                        is_all_day=False, time_slot='18:00-20:00'),
            Availability(user_id=user.id, date=today - timedelta(days=1), 
                        status='available', is_all_day=True, time_slot=None),
            
            # Tomorrow's entries
            Availability(user_id=admin.id, date=today + timedelta(days=1), 
                        status='available', is_all_day=True, time_slot=None),
            Availability(user_id=user.id, date=today + timedelta(days=1), 
                        status='tentative',
                        time_start=datetime.strptime('17:00', '%H:%M').time(),
                        time_end=datetime.strptime('19:00', '%H:%M').time(),
                        is_all_day=False, time_slot='17:00-19:00'),
            Availability(user_id=user2.id, date=today + timedelta(days=1), 
                        status='available',
                        time_start=datetime.strptime('20:00', '%H:%M').time(),
                        time_end=datetime.strptime('22:00', '%H:%M').time(),
                        is_all_day=False, time_slot='20:00-22:00'),
            
            # Next week's entries
            Availability(user_id=admin.id, date=today + timedelta(days=7), 
                        status='available',
                        time_start=datetime.strptime('19:00', '%H:%M').time(),
                        time_end=datetime.strptime('22:00', '%H:%M').time(),
                        is_all_day=False, time_slot='19:00-22:00'),
            Availability(user_id=user.id, date=today + timedelta(days=7), 
                        status='not_available', is_all_day=True, time_slot=None),
            Availability(user_id=user2.id, date=today + timedelta(days=7), 
                        status='available', is_all_day=True, time_slot=None),
        ]
        
        for avail in availabilities:
            db.session.add(avail)
        
        db.session.commit()
        
        print(f"Created {len(availabilities)} availability entries")
        print("\nTest users created:")
        print("- Admin: admin / admin123")
        print("- User 1: john_smith / password123")
        print("- User 2: jane_doe / password123")
        print("\nAvailability data created for:")
        print(f"- Yesterday: {(today - timedelta(days=1)).isoformat()}")
        print(f"- Today: {today.isoformat()}")
        print(f"- Tomorrow: {(today + timedelta(days=1)).isoformat()}")
        print(f"- Next week: {(today + timedelta(days=7)).isoformat()}")

if __name__ == '__main__':
    create_test_data()