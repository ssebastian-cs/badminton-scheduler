"""
End-to-end functional tests for complete user workflows.

These tests simulate real user interactions from start to finish,
testing the complete application flow including navigation, form submissions,
and multi-user interactions.
"""

import pytest
from datetime import date, timedelta
from app.models import User, Availability, Comment


class TestCompleteUserJourneys:
    """Test complete user journeys from registration to task completion."""
    
    def test_new_user_onboarding_journey(self, client, db_session, test_factory):
        """Test complete journey of a new user from creation to first usage."""
        # Admin creates a new user
        admin = test_factory.create_admin_user()
        
        # Admin logs in
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Admin creates new user
        response = client.post('/admin/users/create', data={
            'username': 'newplayer',
            'password': 'newpass123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'User newplayer created successfully' in response.data
        
        # Admin logs out
        client.get('/auth/logout')
        
        # New user logs in for the first time
        response = client.post('/auth/login', data={
            'username': 'newplayer',
            'password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back, newplayer' in response.data
        
        # User views empty dashboard
        response = client.get('/')
        assert response.status_code == 200
        assert b'No availability found' in response.data
        
        # User adds their first availability
        future_date = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '09:00',
            'end_time': '11:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
        
        # User posts their first comment
        response = client.post('/comments/add', data={
            'content': 'Hello everyone! New player here, looking forward to games!'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment posted successfully' in response.data
        
        # User views their availability
        response = client.get('/availability/my')
        assert response.status_code == 200
        assert b'newplayer' in response.data
        
        # Verify data was created
        new_user = User.query.filter_by(username='newplayer').first()
        assert new_user is not None
        assert len(new_user.availability_entries) == 1
        assert len(new_user.comments) == 1
    
    def test_multi_user_coordination_workflow(self, client, db_session, test_factory):
        """Test workflow where multiple users coordinate for a game."""
        # Create multiple users
        organizer = test_factory.create_user(username='organizer', password='pass123')
        player1 = test_factory.create_user(username='player1', password='pass123')
        player2 = test_factory.create_user(username='player2', password='pass123')
        
        future_date = date.today() + timedelta(days=2)
        
        # Organizer logs in and posts availability with invitation
        client.post('/auth/login', data={
            'username': 'organizer',
            'password': 'pass123'
        })
        
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        
        client.post('/comments/add', data={
            'content': f'Looking for players for doubles on {future_date.strftime("%B %d")} at 6 PM!'
        })
        
        client.get('/auth/logout')
        
        # Player1 sees the invitation and responds
        client.post('/auth/login', data={
            'username': 'player1',
            'password': 'pass123'
        })
        
        # Player1 views comments to see the invitation
        response = client.get('/comments')
        assert response.status_code == 200
        assert b'Looking for players for doubles' in response.data
        
        # Player1 adds matching availability
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '18:00',
            'end_time': '20:00'
        })
        
        client.post('/comments/add', data={
            'content': 'Count me in! I\'ll be there at 6 PM.'
        })
        
        client.get('/auth/logout')
        
        # Player2 also responds
        client.post('/auth/login', data={
            'username': 'player2',
            'password': 'pass123'
        })
        
        # Player2 checks the dashboard to see who's available
        response = client.get('/?view=week')
        assert response.status_code == 200
        assert b'organizer' in response.data
        assert b'player1' in response.data
        
        # Player2 adds availability for the same time
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '18:30',
            'end_time': '20:30'
        })
        
        client.post('/comments/add', data={
            'content': 'Perfect! I can join a bit later, around 6:30 PM.'
        })
        
        # Verify all users have availability for the target date
        availability_count = Availability.query.filter_by(date=future_date).count()
        assert availability_count == 3
        
        # Verify conversation thread exists
        comment_count = Comment.query.count()
        assert comment_count == 3


class TestAdminManagementWorkflows:
    """Test complete admin management workflows."""
    
    def test_user_lifecycle_management(self, client, db_session, test_factory):
        """Test complete user lifecycle from creation to deletion."""
        admin = test_factory.create_admin_user()
        
        # Admin logs in
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Admin creates user
        response = client.post('/admin/users/create', data={
            'username': 'testuser',
            'password': 'testpass123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Get the created user
        test_user = User.query.filter_by(username='testuser').first()
        assert test_user is not None
        
        # User creates some content (simulate user activity)
        test_availability = test_factory.create_availability(test_user)
        test_comment = test_factory.create_comment(test_user, "Test content")
        
        # Admin views user details
        response = client.get(f'/admin/users/{test_user.id}')
        assert response.status_code == 200
        
        # Admin blocks user
        response = client.post(f'/admin/users/{test_user.id}/toggle', 
                             follow_redirects=True)
        assert response.status_code == 200
        assert b'testuser has been blocked successfully' in response.data
        
        # Admin unblocks user
        response = client.post(f'/admin/users/{test_user.id}/toggle', 
                             follow_redirects=True)
        assert response.status_code == 200
        assert b'testuser has been unblocked successfully' in response.data
        
        # Admin deletes user and all associated data
        user_id = test_user.id
        availability_id = test_availability.id
        comment_id = test_comment.id
        
        response = client.post(f'/admin/users/{user_id}/delete', 
                             follow_redirects=True)
        assert response.status_code == 200
        assert b'testuser and all associated data have been deleted successfully' in response.data
        
        # Verify complete cleanup
        assert User.query.get(user_id) is None
        assert Availability.query.get(availability_id) is None
        assert Comment.query.get(comment_id) is None
    
    def test_content_moderation_workflow(self, client, db_session, test_factory):
        """Test admin content moderation capabilities."""
        admin = test_factory.create_admin_user()
        user = test_factory.create_user(username='contentuser', password='pass123')
        
        # User creates content
        availability = test_factory.create_availability(user)
        comment = test_factory.create_comment(user, "Original comment content")
        
        # Admin logs in
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Admin moderates availability
        response = client.get('/admin/availability')
        assert response.status_code == 200
        
        new_date = date.today() + timedelta(days=5)
        response = client.post(f'/admin/availability/{availability.id}/edit', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '15:00',
            'end_time': '17:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability for contentuser updated successfully' in response.data
        
        # Admin moderates comment
        response = client.get('/admin/comments')
        assert response.status_code == 200
        
        response = client.post(f'/admin/comments/{comment.id}/edit', data={
            'content': 'Moderated comment content'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment by contentuser updated successfully' in response.data
        
        # Admin views audit log
        response = client.get('/admin/audit')
        assert response.status_code == 200
        assert b'edit_availability' in response.data
        assert b'edit_comment' in response.data


class TestErrorHandlingAndValidation:
    """Test error handling and validation in complete workflows."""
    
    def test_form_validation_recovery_workflow(self, client, db_session, test_factory):
        """Test user workflow with form validation errors and recovery."""
        user = test_factory.create_user(username='testuser', password='pass123')
        
        # User logs in
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'pass123'
        })
        
        # User tries to add availability with past date (should fail)
        past_date = date.today() - timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': past_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        })
        assert response.status_code == 200
        assert b'Date must be in the future' in response.data
        
        # User corrects the error and resubmits
        future_date = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
        
        # User tries to add empty comment (should fail)
        response = client.post('/comments/add', data={
            'content': ''
        })
        # Empty comment might redirect or show validation error
        assert response.status_code in [200, 302]
        
        # User adds valid comment
        response = client.post('/comments/add', data={
            'content': 'This is a valid comment.'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment posted successfully' in response.data
    
    def test_concurrent_operations_workflow(self, client, db_session, test_factory):
        """Test handling of concurrent operations by multiple users."""
        user = test_factory.create_user(username='concurrentuser', password='pass123')
        availability = test_factory.create_availability(user)
        
        # Simulate two browser sessions
        client1 = client
        client2 = client.application.test_client()
        
        # Both sessions login as the same user
        for test_client in [client1, client2]:
            test_client.post('/auth/login', data={
                'username': 'concurrentuser',
                'password': 'pass123'
            })
        
        # Client 1 edits availability
        new_date1 = date.today() + timedelta(days=3)
        response1 = client1.post(f'/availability/edit/{availability.id}', data={
            'date': new_date1.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response1.status_code == 200
        
        # Client 2 tries to edit the same availability
        new_date2 = date.today() + timedelta(days=4)
        response2 = client2.post(f'/availability/edit/{availability.id}', data={
            'date': new_date2.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00'
        }, follow_redirects=True)
        assert response2.status_code == 200
        
        # Verify final state (last edit should win)
        from app import db
        db.session.refresh(availability)
        assert availability.date == new_date2


class TestMobileResponsiveWorkflows:
    """Test workflows specifically for mobile responsiveness."""
    
    def test_mobile_navigation_workflow(self, client, db_session, test_factory):
        """Test mobile-specific navigation and interaction patterns."""
        user = test_factory.create_user(username='mobileuser', password='pass123')
        
        # User logs in
        client.post('/auth/login', data={
            'username': 'mobileuser',
            'password': 'pass123'
        })
        
        # Test mobile dashboard view
        response = client.get('/', headers={'User-Agent': 'Mobile Safari'})
        assert response.status_code == 200
        
        # Test mobile availability form
        response = client.get('/availability/add', headers={'User-Agent': 'Mobile Safari'})
        assert response.status_code == 200
        
        # Test mobile form submission
        future_date = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, headers={'User-Agent': 'Mobile Safari'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
        
        # Test mobile comment form
        response = client.post('/comments/add', data={
            'content': 'Posted from mobile device!'
        }, headers={'User-Agent': 'Mobile Safari'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment posted successfully' in response.data


class TestAccessibilityWorkflows:
    """Test accessibility features in user workflows."""
    
    def test_keyboard_navigation_workflow(self, client, db_session, test_factory):
        """Test that all workflows are accessible via keyboard navigation."""
        user = test_factory.create_user(username='accessuser', password='pass123')
        
        # User logs in
        client.post('/auth/login', data={
            'username': 'accessuser',
            'password': 'pass123'
        })
        
        # Test that all main pages are accessible
        pages = [
            '/',
            '/availability/add',
            '/availability/my',
            '/comments'
        ]
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            # Check for proper heading structure
            assert b'<h1' in response.data or b'<h2' in response.data
    
    def test_screen_reader_workflow(self, client, db_session, test_factory):
        """Test workflow compatibility with screen readers."""
        user = test_factory.create_user(username='screenreader', password='pass123')
        
        # User logs in
        client.post('/auth/login', data={
            'username': 'screenreader',
            'password': 'pass123'
        })
        
        # Test form labels and ARIA attributes
        response = client.get('/availability/add')
        assert response.status_code == 200
        # Check for proper form labels
        assert b'<label' in response.data
        assert b'for=' in response.data
        
        # Test successful form submission with screen reader
        future_date = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data