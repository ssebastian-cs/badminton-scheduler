#!/usr/bin/env python3
"""
Script to create sample data for the badminton scheduler app using the simplified structure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run import app, db, User, Availability, Feedback
from datetime import datetime, date, timedelta

def create_sample_data():
    """Create sample users, availability, and feedback data."""
    
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create sample users
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@badminton.com',
                'password': 'admin123',
                'is_admin': True
            },
            {
                'username': 'john_smith',
                'email': 'john.smith@email.com',
                'password': 'password123',
                'is_admin': False
            },
            {
                'username': 'sarah_johnson',
                'email': 'sarah.johnson@email.com',
                'password': 'password123',
                'is_admin': False
            },
            {
                'username': 'mike_chen',
                'email': 'mike.chen@email.com',
                'password': 'password123',
                'is_admin': False
            },
            {
                'username': 'lisa_wong',
                'email': 'lisa.wong@email.com',
                'password': 'password123',
                'is_admin': False
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                is_admin=user_data['is_admin']
            )
            user.set_password(user_data['password'])
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"Created {len(users)} users")
        
        # Create sample availability data for the next 30 days
        today = date.today()
        availability_data = []
        
        for i in range(30):
            current_date = today + timedelta(days=i)
            
            # Skip some days to make it more realistic
            if current_date.weekday() in [0, 2, 4]:  # Monday, Wednesday, Friday
                for user in users[1:]:  # Skip admin user
                    if i % 3 == 0:  # Not everyone available every day
                        continue
                        
                    status_options = ['available', 'tentative', 'not_available']
                    preference_options = ['drop_in', 'book_court', 'either']
                    
                    availability = Availability(
                        user_id=user.id,
                        date=current_date,
                        status=status_options[i % 3],
                        play_preference=preference_options[i % 3],
                        notes=f"Sample availability for {current_date}" if i % 5 == 0 else None
                    )
                    availability_data.append(availability)
                    db.session.add(availability)
        
        db.session.commit()
        print(f"Created {len(availability_data)} availability entries")
        
        # Create sample feedback
        feedback_data = [
            {
                'user_id': users[1].id,
                'content': 'Great session last week! Really enjoyed the competitive games.',
                'rating': 5,
                'is_public': True
            },
            {
                'user_id': users[2].id,
                'content': 'The court booking system worked well. Thanks for organizing!',
                'rating': 4,
                'is_public': True
            },
            {
                'user_id': users[3].id,
                'content': 'Would love to see more beginner-friendly sessions.',
                'rating': 4,
                'is_public': True
            },
            {
                'user_id': users[4].id,
                'content': 'Private feedback about scheduling conflicts.',
                'rating': 3,
                'is_public': False
            }
        ]
        
        feedback_entries = []
        for fb_data in feedback_data:
            feedback = Feedback(
                user_id=fb_data['user_id'],
                content=fb_data['content'],
                rating=fb_data['rating'],
                is_public=fb_data['is_public']
            )
            feedback_entries.append(feedback)
            db.session.add(feedback)
        
        db.session.commit()
        print(f"Created {len(feedback_entries)} feedback entries")
        
        print("\n=== Sample Data Created Successfully! ===")
        print("\nDemo Credentials:")
        print("Admin Account:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nUser Accounts:")
        for user_data in users_data[1:]:
            print(f"  Username: {user_data['username']}")
            print(f"  Password: {user_data['password']}")
        print("\n" + "="*50)

if __name__ == '__main__':
    create_sample_data()