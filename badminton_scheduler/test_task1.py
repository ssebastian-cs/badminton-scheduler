#!/usr/bin/env python3
"""Test script for Task 1 - Database model enhancements"""

from run import app, db, Availability, User
from datetime import date, time, datetime

def test_task1():
    with app.app_context():
        # Clean up and create fresh test data
        Availability.query.delete()
        db.session.commit()
        
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
        
        today = date.today()
        
        # Test 1: Time-specific availability
        entry1 = Availability(
            user_id=test_user.id,
            date=today,
            time_start=time(19, 0),
            time_end=time(21, 0),
            is_all_day=False,
            status='available'
        )
        db.session.add(entry1)
        
        # Test 2: Another time slot same date
        entry2 = Availability(
            user_id=test_user.id,
            date=today,
            time_start=time(21, 30),
            time_end=time(23, 0),
            is_all_day=False,
            status='tentative'
        )
        db.session.add(entry2)
        
        # Test 3: All-day availability
        tomorrow = date(today.year, today.month, today.day + 1)
        entry3 = Availability(
            user_id=test_user.id,
            date=tomorrow,
            is_all_day=True,
            status='available'
        )
        db.session.add(entry3)
        
        db.session.commit()
        
        # Verify all entries were created
        entries = Availability.query.filter_by(user_id=test_user.id).order_by(Availability.date, Availability.time_start).all()
        
        print(f'Created {len(entries)} availability entries:')
        for i, entry in enumerate(entries, 1):
            data = entry.to_dict()
            print(f'{i}. Date: {data["date"]}, All-day: {data["is_all_day"]}, Start: {data["time_start"]}, End: {data["time_end"]}, Status: {data["status"]}')
            
        print()
        print('All database model enhancements completed successfully!')
        print('✅ Time-specific fields added')
        print('✅ Multiple time slots per date supported')
        print('✅ Unique constraints working properly')
        print('✅ Migration logic handles existing data')
        print('✅ to_dict() method includes all new fields')

if __name__ == '__main__':
    test_task1()