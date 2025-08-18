"""
Functional tests for complete user workflows and end-to-end scenarios.
"""

import pytest
from datetime import date, time, timedelta
from app.models import User, Availability, Comment, AdminAction
from app import db


class TestUserWorkflows:
    """Test complete user workflows from login to task completion."""
    
    def test_new_user_complete_workflow(self, client, db_session, test_admin):
        """Test complete workflow for a new user from creation to usage."""
        # Step 1: Admin creates a new user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_admin.id)
            sess['_fresh'] = True
        
        response = client.post('/admin/users/create', data={
            'username': 'newuser',
            'password': 'newpass123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'User newuser created successfully' in response.data
        
        # Step 2: New user logs in
        client.get('/auth/logout')  # Logout admin
        
        response = client.post('/auth/login', data={
            'username': 'newuser',
            'password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome back, newuser' in response.data
        
        # Step 3: User views dashboard (should be empty initially)
        response = client.get('/')
        assert response.status_code == 200
        
        # Step 4: User adds their first availability
        future_date = date.today() + timedelta(days=1)
        response = client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
        
        # Step 5: User posts their first comment
        response = client.post('/comments/add', data={
            'content': 'Hello everyone! Looking forward to playing badminton.'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment posted successfully' in response.data
        
        # Step 6: User views their own availability
        response = client.get('/availability/my')
        assert response.status_code == 200
        assert b'newuser' in response.data
        
        # Verify data was created correctly
        new_user = User.query.filter_by(username='newuser').first()
        assert new_user is not None
        assert len(new_user.availability_entries) == 1
        assert len(new_user.comments) == 1
    
    def test_user_availability_management_workflow(self, authenticated_user, db_session, test_user):
        """Test complete availability management workflow."""
        # Step 1: User adds multiple availability entries
        dates_and_times = [
            (date.today() + timedelta(days=1), '09:00', '11:00'),
            (date.today() + timedelta(days=2), '14:00', '16:00'),
            (date.today() + timedelta(days=3), '18:00', '20:00')
        ]
        
        for availability_date, start_time, end_time in dates_and_times:
            response = authenticated_user.post('/availability/add', data={
                'date': availability_date.strftime('%Y-%m-%d'),
                'start_time': start_time,
                'end_time': end_time
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b'Availability added successfully' in response.data
        
        # Step 2: User views their availability
        response = authenticated_user.get('/availability/my')
        assert response.status_code == 200
        
        # Step 3: User edits one of their availability entries
        availability = Availability.query.filter_by(user_id=test_user.id).first()
        new_date = date.today() + timedelta(days=5)
        
        response = authenticated_user.post(f'/availability/edit/{availability.id}', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '15:00',
            'end_time': '17:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability updated successfully' in response.data
        
        # Step 4: User deletes one availability entry
        availability_to_delete = Availability.query.filter_by(user_id=test_user.id).first()
        response = authenticated_user.post(f'/availability/delete/{availability_to_delete.id}', 
                                         follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability deleted successfully' in response.data
        
        # Step 5: User views dashboard with different filters
        response = authenticated_user.get('/?view=week')
        assert response.status_code == 200
        
        response = authenticated_user.get('/?view=month')
        assert response.status_code == 200
        
        # Verify final state
        remaining_availability = Availability.query.filter_by(user_id=test_user.id).count()
        assert remaining_availability == 2  # Added 3, deleted 1
    
    def test_user_comment_management_workflow(self, authenticated_user, db_session, test_user):
        """Test complete comment management workflow."""
        # Step 1: User posts multiple comments
        comments_content = [
            "Looking for players for tomorrow morning!",
            "Great game today, thanks everyone!",
            "Anyone interested in doubles this weekend?"
        ]
        
        for content in comments_content:
            response = authenticated_user.post('/comments/add', data={
                'content': content
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b'Comment posted successfully' in response.data
        
        # Step 2: User views all comments
        response = authenticated_user.get('/comments')
        assert response.status_code == 200
        for content in comments_content:
            assert content.encode() in response.data
        
        # Step 3: User edits one of their comments
        comment = Comment.query.filter_by(user_id=test_user.id).first()
        new_content = "Updated: Looking for players for tomorrow afternoon!"
        
        response = authenticated_user.post(f'/comments/{comment.id}/edit', data={
            'content': new_content
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment updated successfully' in response.data
        
        # Step 4: User deletes one of their comments
        comment_to_delete = Comment.query.filter_by(user_id=test_user.id).first()
        response = authenticated_user.post(f'/comments/{comment_to_delete.id}/delete', 
                                         follow_redirects=True)
        assert response.status_code == 200
        assert b'Your comment has been deleted' in response.data
        
        # Verify final state
        remaining_comments = Comment.query.filter_by(user_id=test_user.id).count()
        assert remaining_comments == 2  # Added 3, deleted 1
    
    def test_user_interaction_workflow(self, client, db_session, test_factory):
        """Test workflow involving multiple users interacting."""
        # Create multiple users
        user1 = test_factory.create_user(username='player1', password='pass123')
        user2 = test_factory.create_user(username='player2', password='pass123')
        user3 = test_factory.create_user(username='player3', password='pass123')
        
        future_date = date.today() + timedelta(days=1)
        
        # User 1 logs in and adds availability and comments
        client.post('/auth/login', data={
            'username': 'player1',
            'password': 'pass123'
        })
        
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        })
        
        client.post('/comments/add', data={
            'content': 'Looking for doubles partners tomorrow morning!'
        })
        
        # User 1 logs out
        client.get('/auth/logout')
        
        # User 2 logs in and responds with their availability and comment
        client.post('/auth/login', data={
            'username': 'player2',
            'password': 'pass123'
        })
        
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:30',
            'end_time': '12:30'
        })
        
        client.post('/comments/add', data={
            'content': 'I can play tomorrow! Count me in.'
        })
        
        # User 2 logs out
        client.get('/auth/logout')
        
        # User 3 logs in and views the dashboard to see everyone's availability
        client.post('/auth/login', data={
            'username': 'player3',
            'password': 'pass123'
        })
        
        # Use week view to see tomorrow's availability
        response = client.get('/?view=week')
        assert response.status_code == 200
        assert b'player1' in response.data
        assert b'player2' in response.data
        
        # User 3 views comments to see the conversation
        response = client.get('/comments')
        assert response.status_code == 200
        assert b'Looking for doubles partners' in response.data
        assert b'Count me in' in response.data
        
        # User 3 adds their availability and joins the conversation
        client.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '11:00',
            'end_time': '13:00'
        })
        
        client.post('/comments/add', data={
            'content': 'Perfect timing! I\'ll be there too.'
        })
        
        # Verify all users have availability for the same day
        availability_count = Availability.query.filter_by(date=future_date).count()
        assert availability_count == 3
        
        # Verify all users have commented
        comment_count = Comment.query.count()
        assert comment_count == 3


class TestAdminWorkflows:
    """Test complete admin workflows and user management."""
    
    def test_admin_user_management_workflow(self, authenticated_admin, db_session, test_factory):
        """Test complete admin user management workflow."""
        # Step 1: Admin views user management dashboard
        response = authenticated_admin.get('/admin/')
        assert response.status_code == 200
        
        response = authenticated_admin.get('/admin/users')
        assert response.status_code == 200
        
        # Step 2: Admin creates a new user
        response = authenticated_admin.post('/admin/users/create', data={
            'username': 'manageduser',
            'password': 'managed123',
            'role': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'User manageduser created successfully' in response.data
        
        # Step 3: New user creates some content
        new_user = User.query.filter_by(username='manageduser').first()
        test_factory.create_availability(new_user)
        test_factory.create_comment(new_user, "Test comment from managed user")
        
        # Step 4: Admin blocks the user
        response = authenticated_admin.post(f'/admin/users/{new_user.id}/toggle', 
                                          follow_redirects=True)
        assert response.status_code == 200
        assert b'User manageduser has been blocked successfully' in response.data
        
        # Step 5: Admin views user details
        response = authenticated_admin.get(f'/admin/users/{new_user.id}')
        assert response.status_code == 200
        
        # Step 6: Admin unblocks the user
        response = authenticated_admin.post(f'/admin/users/{new_user.id}/toggle', 
                                          follow_redirects=True)
        assert response.status_code == 200
        assert b'User manageduser has been unblocked successfully' in response.data
        
        # Step 7: Admin views audit log
        response = authenticated_admin.get('/admin/audit')
        assert response.status_code == 200
        assert b'create_user' in response.data
        assert b'block_user' in response.data
        assert b'unblock_user' in response.data
    
    def test_admin_content_moderation_workflow(self, authenticated_admin, db_session, test_factory):
        """Test complete admin content moderation workflow."""
        # Create a user with content
        user = test_factory.create_user(username='contentuser', password='pass123')
        availability = test_factory.create_availability(user)
        comment = test_factory.create_comment(user, "Original comment content")
        
        # Step 1: Admin views availability management
        response = authenticated_admin.get('/admin/availability')
        assert response.status_code == 200
        
        # Step 2: Admin edits user's availability
        new_date = date.today() + timedelta(days=10)
        response = authenticated_admin.post(f'/admin/availability/{availability.id}/edit', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '16:00',
            'end_time': '18:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability for contentuser updated successfully' in response.data
        
        # Step 3: Admin views comment management
        response = authenticated_admin.get('/admin/comments')
        assert response.status_code == 200
        
        # Step 4: Admin edits user's comment
        response = authenticated_admin.post(f'/admin/comments/{comment.id}/edit', data={
            'content': 'Admin moderated comment content'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment by contentuser updated successfully' in response.data
        
        # Step 5: Admin views audit log to see all actions
        response = authenticated_admin.get('/admin/audit')
        assert response.status_code == 200
        assert b'edit_availability' in response.data
        assert b'edit_comment' in response.data
        
        # Verify changes were made
        db.session.refresh(availability)
        db.session.refresh(comment)
        assert availability.date == new_date
        assert comment.content == 'Admin moderated comment content'
    
    def test_admin_user_deletion_workflow(self, authenticated_admin, db_session, test_factory):
        """Test admin user deletion workflow with data cleanup."""
        # Create user with associated data
        user = test_factory.create_user(username='usertoDelete', password='pass123')
        availability = test_factory.create_availability(user)
        comment = test_factory.create_comment(user, "Comment to be deleted")
        
        user_id = user.id
        availability_id = availability.id
        comment_id = comment.id
        
        # Admin deletes the user
        response = authenticated_admin.post(f'/admin/users/{user_id}/delete', 
                                          follow_redirects=True)
        assert response.status_code == 200
        assert b'User usertoDelete and all associated data have been deleted successfully' in response.data
        
        # Verify user and all associated data are deleted
        assert User.query.get(user_id) is None
        assert Availability.query.get(availability_id) is None
        assert Comment.query.get(comment_id) is None
        
        # Verify admin action was logged
        admin_action = AdminAction.query.filter_by(action_type='delete_user').first()
        assert admin_action is not None
        assert 'usertoDelete' in admin_action.description


class TestErrorHandlingWorkflows:
    """Test error handling in complete workflows."""
    
    def test_user_workflow_with_validation_errors(self, authenticated_user, db_session):
        """Test user workflow handling validation errors gracefully."""
        # Try to add availability with past date
        past_date = date.today() - timedelta(days=1)
        response = authenticated_user.post('/availability/add', data={
            'date': past_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        })
        assert response.status_code == 200
        assert b'Date must be in the future' in response.data
        
        # Correct the error and try again
        future_date = date.today() + timedelta(days=1)
        response = authenticated_user.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
    
    def test_admin_workflow_with_constraints(self, authenticated_admin, db_session, test_factory):
        """Test admin workflow handling business rule constraints."""
        # Try to create user with duplicate username
        existing_user = test_factory.create_user(username='existing', password='pass123')
        
        response = authenticated_admin.post('/admin/users/create', data={
            'username': 'existing',
            'password': 'newpass123',
            'role': 'User'
        })
        assert response.status_code == 200
        assert b'Username already exists' in response.data
        
        # Try to block the last admin (should fail)
        # The test fixture creates one admin (authenticated_admin)
        # Let's verify there's only one admin and try to block them from another admin account
        
        # Create a second admin user
        second_admin = test_factory.create_user(username='secondadmin', password='pass123', role='Admin')
        
        # Logout current admin and login as second admin
        authenticated_admin.get('/auth/logout')
        authenticated_admin.post('/auth/login', data={
            'username': 'secondadmin',
            'password': 'pass123'
        })
        
        # Get the first admin user
        from app.models import User
        first_admin = User.query.filter_by(role='Admin').filter(User.username != 'secondadmin').first()
        
        # Block the first admin, leaving only the second admin active
        response = authenticated_admin.post(f'/admin/users/{first_admin.id}/toggle', 
                                          follow_redirects=True)
        assert response.status_code == 200
        
        # Now there should be only 1 active admin (secondadmin)
        active_admin_count = User.query.filter_by(role='Admin', is_active=True).count()
        assert active_admin_count == 1
        
        # Now try to block the second admin (themselves) - this should fail with "cannot block yourself"
        response = authenticated_admin.post(f'/admin/users/{second_admin.id}/toggle', 
                                          follow_redirects=True)
        assert response.status_code == 200
        assert b'You cannot block your own account' in response.data
    
    def test_concurrent_user_actions(self, app, db_session, test_factory):
        """Test handling of concurrent user actions."""
        user = test_factory.create_user(username='concurrent', password='pass123')
        availability = test_factory.create_availability(user)
        
        # Simulate two clients trying to edit the same availability
        client1 = app.test_client()
        client2 = app.test_client()
        
        # Both clients login
        for client in [client1, client2]:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
        
        # Client 1 edits the availability
        new_date1 = date.today() + timedelta(days=5)
        response1 = client1.post(f'/availability/edit/{availability.id}', data={
            'date': new_date1.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        assert response1.status_code == 200
        
        # Client 2 tries to edit the same availability
        new_date2 = date.today() + timedelta(days=6)
        response2 = client2.post(f'/availability/edit/{availability.id}', data={
            'date': new_date2.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00'
        }, follow_redirects=True)
        assert response2.status_code == 200
        
        # Verify the final state (last edit wins)
        db.session.refresh(availability)
        assert availability.date == new_date2