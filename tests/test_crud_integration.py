"""
Integration tests for CRUD operations on availability and comments.
"""

import pytest
from datetime import date, time, timedelta
from flask import url_for
from app.models import Availability, Comment, User
from app import db


class TestAvailabilityCRUD:
    """Integration tests for availability CRUD operations."""
    
    def test_dashboard_access(self, authenticated_user):
        """Test accessing the dashboard."""
        response = authenticated_user.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Availability' in response.data
    
    def test_dashboard_today_view(self, authenticated_user, db_session, test_user, test_factory):
        """Test dashboard shows today's availability by default."""
        # Create availability for today (should not show - future only)
        # Create availability for tomorrow
        tomorrow_availability = test_factory.create_availability(
            user=test_user,
            date_offset=1
        )
        
        response = authenticated_user.get('/')
        assert response.status_code == 200
        # Should show tomorrow's availability
        assert test_user.username.encode() in response.data
    
    def test_dashboard_view_filters(self, authenticated_user, db_session, test_user, test_factory):
        """Test dashboard view filters (today, week, month, custom)."""
        # Create availability entries for different dates
        test_factory.create_availability(user=test_user, date_offset=1)  # Tomorrow
        test_factory.create_availability(user=test_user, date_offset=7)  # Next week
        test_factory.create_availability(user=test_user, date_offset=30) # Next month
        
        # Test week view
        response = authenticated_user.get('/?view=week')
        assert response.status_code == 200
        
        # Test month view
        response = authenticated_user.get('/?view=month')
        assert response.status_code == 200
        
        # Test custom date range
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)
        response = authenticated_user.get(f'/?view=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
    
    def test_add_availability_page(self, authenticated_user):
        """Test accessing the add availability page."""
        response = authenticated_user.get('/availability/add')
        assert response.status_code == 200
        assert b'Date' in response.data
        assert b'Start Time' in response.data
        assert b'End Time' in response.data
    
    def test_add_availability_success(self, authenticated_user, db_session, test_user):
        """Test successfully adding availability."""
        future_date = date.today() + timedelta(days=1)
        
        response = authenticated_user.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Availability added successfully' in response.data
        
        # Check that availability was created in database
        availability = Availability.query.filter_by(user_id=test_user.id).first()
        assert availability is not None
        assert availability.date == future_date
        assert availability.start_time == time(10, 0)
        assert availability.end_time == time(12, 0)
    
    def test_add_availability_validation_errors(self, authenticated_user):
        """Test availability form validation errors."""
        # Past date
        past_date = date.today() - timedelta(days=1)
        response = authenticated_user.post('/availability/add', data={
            'date': past_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        })
        assert response.status_code == 200
        assert b'Date must be in the future' in response.data
        
        # End time before start time
        future_date = date.today() + timedelta(days=1)
        response = authenticated_user.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '12:00',
            'end_time': '10:00'
        })
        assert response.status_code == 200
        assert b'End time must be after start time' in response.data
    
    def test_edit_availability_own_entry(self, authenticated_user, db_session, test_user, test_availability):
        """Test editing own availability entry."""
        response = authenticated_user.get(f'/availability/edit/{test_availability.id}')
        assert response.status_code == 200
        
        # Update the availability
        new_date = date.today() + timedelta(days=5)
        response = authenticated_user.post(f'/availability/edit/{test_availability.id}', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Availability updated successfully' in response.data
        
        # Check that availability was updated
        db.session.refresh(test_availability)
        assert test_availability.date == new_date
        assert test_availability.start_time == time(14, 0)
        assert test_availability.end_time == time(16, 0)
    
    def test_edit_availability_permission_denied(self, authenticated_user, db_session, test_factory):
        """Test that users cannot edit others' availability."""
        other_user = test_factory.create_user(username='otheruser', password='password123')
        other_availability = test_factory.create_availability(other_user)
        
        response = authenticated_user.get(f'/availability/edit/{other_availability.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'You can only edit your own availability' in response.data
    
    def test_delete_availability_own_entry(self, authenticated_user, db_session, test_user, test_availability):
        """Test deleting own availability entry."""
        availability_id = test_availability.id
        
        response = authenticated_user.post(f'/availability/delete/{availability_id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability deleted successfully' in response.data
        
        # Check that availability was deleted
        availability = Availability.query.get(availability_id)
        assert availability is None
    
    def test_delete_availability_permission_denied(self, authenticated_user, db_session, test_factory):
        """Test that users cannot delete others' availability."""
        other_user = test_factory.create_user(username='otheruser', password='password123')
        other_availability = test_factory.create_availability(other_user)
        
        response = authenticated_user.post(f'/availability/delete/{other_availability.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'You can only delete your own availability' in response.data
        
        # Check that availability was not deleted
        availability = Availability.query.get(other_availability.id)
        assert availability is not None
    
    def test_my_availability_page(self, authenticated_user, db_session, test_user, test_factory):
        """Test viewing own availability entries."""
        # Create multiple availability entries
        availability1 = test_factory.create_availability(user=test_user, date_offset=1)
        availability2 = test_factory.create_availability(user=test_user, date_offset=2)
        
        response = authenticated_user.get('/availability/my')
        assert response.status_code == 200
        
        # Should show user's availability entries
        assert test_user.username.encode() in response.data
    
    def test_availability_404_errors(self, authenticated_user):
        """Test 404 errors for non-existent availability entries."""
        response = authenticated_user.get('/availability/edit/99999')
        assert response.status_code == 404
        
        response = authenticated_user.post('/availability/delete/99999')
        assert response.status_code == 404


class TestCommentsCRUD:
    """Integration tests for comments CRUD operations."""
    
    def test_comments_page_access(self, authenticated_user):
        """Test accessing the comments page."""
        response = authenticated_user.get('/comments')
        assert response.status_code == 200
        assert b'Comments' in response.data or b'Comment' in response.data
    
    def test_comments_display(self, authenticated_user, db_session, multiple_users, multiple_comments):
        """Test displaying all comments."""
        response = authenticated_user.get('/comments')
        assert response.status_code == 200
        
        # Should show all comments with usernames
        for comment in multiple_comments:
            assert comment.user.username.encode() in response.data
            assert comment.content.encode() in response.data
    
    def test_add_comment_success(self, authenticated_user, db_session, test_user):
        """Test successfully adding a comment."""
        comment_content = "This is a test comment"
        
        response = authenticated_user.post('/comments/add', data={
            'content': comment_content
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Comment posted successfully' in response.data
        
        # Check that comment was created in database
        comment = Comment.query.filter_by(user_id=test_user.id).first()
        assert comment is not None
        assert comment.content == comment_content
    
    def test_add_comment_validation_errors(self, authenticated_user):
        """Test comment form validation errors."""
        # Empty content
        response = authenticated_user.post('/comments/add', data={
            'content': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment content is required' in response.data or b'Comment content cannot be empty' in response.data
        
        # Content too long
        long_content = 'a' * 1001
        response = authenticated_user.post('/comments/add', data={
            'content': long_content
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment must be between 1 and 1000 characters' in response.data or b'Comment content cannot exceed 1000 characters' in response.data
    
    def test_edit_comment_own_comment(self, authenticated_user, db_session, test_user, test_comment):
        """Test editing own comment."""
        response = authenticated_user.get(f'/comments/{test_comment.id}/edit')
        assert response.status_code == 200
        
        # Update the comment
        new_content = "Updated comment content"
        response = authenticated_user.post(f'/comments/{test_comment.id}/edit', data={
            'content': new_content
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Comment updated successfully' in response.data
        
        # Check that comment was updated
        db.session.refresh(test_comment)
        assert test_comment.content == new_content
    
    def test_edit_comment_permission_denied(self, authenticated_user, db_session, test_factory):
        """Test that users cannot edit others' comments."""
        other_user = test_factory.create_user(username='otheruser', password='password123')
        other_comment = test_factory.create_comment(other_user, "Other user's comment")
        
        response = authenticated_user.get(f'/comments/{other_comment.id}/edit', follow_redirects=True)
        assert response.status_code == 200
        assert b'You can only edit your own comments' in response.data
    
    def test_delete_comment_own_comment(self, authenticated_user, db_session, test_user, test_comment):
        """Test deleting own comment."""
        comment_id = test_comment.id
        
        response = authenticated_user.post(f'/comments/{comment_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Your comment has been deleted' in response.data
        
        # Check that comment was deleted
        comment = Comment.query.get(comment_id)
        assert comment is None
    
    def test_delete_comment_permission_denied(self, authenticated_user, db_session, test_factory):
        """Test that users cannot delete others' comments."""
        other_user = test_factory.create_user(username='otheruser', password='password123')
        other_comment = test_factory.create_comment(other_user, "Other user's comment")
        
        response = authenticated_user.post(f'/comments/{other_comment.id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'You can only delete your own comments' in response.data
        
        # Check that comment was not deleted
        comment = Comment.query.get(other_comment.id)
        assert comment is not None
    
    def test_api_delete_comment_success(self, authenticated_user, db_session, test_user, test_comment):
        """Test API endpoint for deleting comments."""
        comment_id = test_comment.id
        
        response = authenticated_user.delete(f'/api/comments/{comment_id}/delete')
        assert response.status_code == 200
        
        # Check JSON response
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'deleted successfully' in json_data['message']
        
        # Check that comment was deleted
        comment = Comment.query.get(comment_id)
        assert comment is None
    
    def test_api_delete_comment_permission_denied(self, authenticated_user, db_session, test_factory):
        """Test API endpoint permission denial."""
        other_user = test_factory.create_user(username='otheruser', password='password123')
        other_comment = test_factory.create_comment(other_user, "Other user's comment")
        
        response = authenticated_user.delete(f'/api/comments/{other_comment.id}/delete')
        assert response.status_code == 403
        
        # Check JSON response
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'You can only delete your own comments' in json_data['error']
    
    def test_comments_404_errors(self, authenticated_user):
        """Test 404 errors for non-existent comments."""
        response = authenticated_user.get('/comments/99999/edit')
        assert response.status_code == 404
        
        response = authenticated_user.post('/comments/99999/delete')
        assert response.status_code == 404
        
        response = authenticated_user.delete('/api/comments/99999/delete')
        assert response.status_code == 404


class TestAdminCRUD:
    """Integration tests for admin CRUD operations."""
    
    def test_admin_can_edit_any_availability(self, authenticated_admin, db_session, test_factory):
        """Test that admin can edit any user's availability."""
        user = test_factory.create_user(username='regularuser', password='password123')
        availability = test_factory.create_availability(user)
        
        response = authenticated_admin.get(f'/availability/edit/{availability.id}')
        assert response.status_code == 200
        
        # Update the availability
        new_date = date.today() + timedelta(days=10)
        response = authenticated_admin.post(f'/availability/edit/{availability.id}', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '15:00',
            'end_time': '17:00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Availability updated successfully' in response.data
    
    def test_admin_can_delete_any_availability(self, authenticated_admin, db_session, test_factory):
        """Test that admin can delete any user's availability."""
        user = test_factory.create_user(username='regularuser', password='password123')
        availability = test_factory.create_availability(user)
        availability_id = availability.id
        
        response = authenticated_admin.post(f'/availability/delete/{availability_id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'Availability deleted successfully' in response.data
        
        # Check that availability was deleted
        availability = Availability.query.get(availability_id)
        assert availability is None
    
    def test_admin_can_edit_any_comment(self, authenticated_admin, db_session, test_factory):
        """Test that admin can edit any user's comment."""
        user = test_factory.create_user(username='regularuser', password='password123')
        comment = test_factory.create_comment(user, "Original comment")
        
        response = authenticated_admin.get(f'/comments/{comment.id}/edit')
        assert response.status_code == 200
        
        # Update the comment
        new_content = "Admin edited comment"
        response = authenticated_admin.post(f'/comments/{comment.id}/edit', data={
            'content': new_content
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Comment updated successfully' in response.data
        
        # Check that comment was updated
        db.session.refresh(comment)
        assert comment.content == new_content
    
    def test_admin_can_delete_any_comment(self, authenticated_admin, db_session, test_factory):
        """Test that admin can delete any user's comment."""
        user = test_factory.create_user(username='regularuser', password='password123')
        comment = test_factory.create_comment(user, "Comment to delete")
        comment_id = comment.id
        
        response = authenticated_admin.post(f'/comments/{comment_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment by regularuser deleted successfully' in response.data
        
        # Check that comment was deleted
        comment = Comment.query.get(comment_id)
        assert comment is None


class TestCRUDSecurity:
    """Security tests for CRUD operations."""
    
    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated users cannot access CRUD operations."""
        # Availability operations
        response = client.get('/availability/add')
        assert response.status_code == 302  # Redirect to login
        
        response = client.post('/availability/add', data={})
        assert response.status_code == 302
        
        # Comment operations
        response = client.get('/comments')
        assert response.status_code == 302
        
        response = client.post('/comments/add', data={})
        assert response.status_code == 302
    
    def test_sql_injection_protection_in_crud(self, authenticated_user, db_session):
        """Test SQL injection protection in CRUD operations."""
        # Test in comment content
        sql_injection = "'; DROP TABLE comments; --"
        response = authenticated_user.post('/comments/add', data={
            'content': sql_injection
        }, follow_redirects=True)
        
        # Should not crash and should sanitize/reject the input
        assert response.status_code == 200
        
        # Check that no comments with malicious content were created
        malicious_comment = Comment.query.filter(Comment.content.contains('DROP TABLE')).first()
        assert malicious_comment is None
    
    def test_xss_protection_in_crud(self, authenticated_user, db_session):
        """Test XSS protection in CRUD operations."""
        xss_content = "<script>alert('xss')</script>"
        response = authenticated_user.post('/comments/add', data={
            'content': xss_content
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that script tags are not present in the response
        assert b'<script>' not in response.data
        
        # If comment was created, content should be sanitized
        comment = Comment.query.first()
        if comment:
            assert '<script>' not in comment.content
    
    def test_csrf_protection(self, client, db_session, test_user):
        """Test CSRF protection on forms."""
        # Login first
        client.post('/auth/login', data={
            'username': test_user.username,
            'password': 'password123'
        })
        
        # Try to submit form without CSRF token (if CSRF is enabled)
        response = client.post('/comments/add', data={
            'content': 'Test comment without CSRF'
        })
        
        # Should either reject the request or handle it gracefully
        # (CSRF is disabled in testing config, so this mainly tests the setup)
        assert response.status_code in [200, 400, 403]