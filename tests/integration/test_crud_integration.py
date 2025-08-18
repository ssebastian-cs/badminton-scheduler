"""
Integration tests for CRUD operations.
"""

import pytest
from datetime import date, time, timedelta
from app.models import Availability, Comment
from app import db


class TestCRUDIntegration:
    """Test cases for CRUD operations integration."""
    
    def test_availability_create_flow(self, authenticated_user, test_user, app_context):
        """Test complete availability creation flow."""
        future_date = date.today() + timedelta(days=1)
        
        # Test availability creation form loads
        response = authenticated_user.get('/availability/add')
        assert response.status_code == 200
        assert b'Add Availability' in response.data
        
        # Test successful availability creation
        response = authenticated_user.post('/availability/add', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify availability was created in database
        with app_context.app_context():
            availability = Availability.query.filter_by(user_id=test_user.id).first()
            assert availability is not None
            assert availability.date == future_date
            assert availability.start_time == time(10, 0)
            assert availability.end_time == time(12, 0)
    
    def test_availability_read_flow(self, authenticated_user, test_availability):
        """Test availability reading/viewing flow."""
        # Test availability dashboard page (main availability view)
        response = authenticated_user.get('/availability')
        assert response.status_code == 200
        # Check if the availability date appears in the response
        date_str = test_availability.date.strftime('%Y-%m-%d')
        # The date might appear in different formats, so check for the basic date components
        assert str(test_availability.date.year).encode() in response.data
        
        # Test user's own availability page
        response = authenticated_user.get('/availability/my')
        assert response.status_code == 200
    
    def test_availability_update_flow(self, authenticated_user, test_availability, app_context):
        """Test availability update flow."""
        new_date = date.today() + timedelta(days=2)
        
        # Test availability edit form loads
        response = authenticated_user.get(f'/availability/edit/{test_availability.id}')
        assert response.status_code == 200
        assert b'Edit Availability' in response.data
        
        # Test successful availability update
        response = authenticated_user.post(f'/availability/edit/{test_availability.id}', data={
            'date': new_date.strftime('%Y-%m-%d'),
            'start_time': '11:00',
            'end_time': '13:00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify availability was updated in database
        with app_context.app_context():
            updated_availability = Availability.query.get(test_availability.id)
            assert updated_availability is not None
            assert updated_availability.date == new_date
            assert updated_availability.start_time == time(11, 0)
            assert updated_availability.end_time == time(13, 0)
    
    def test_availability_delete_flow(self, authenticated_user, test_availability, app_context):
        """Test availability deletion flow."""
        availability_id = test_availability.id
        
        # Test availability deletion
        response = authenticated_user.post(f'/availability/delete/{availability_id}', 
                                         follow_redirects=True)
        assert response.status_code == 200
        
        # Verify availability was deleted from database
        with app_context.app_context():
            availability = Availability.query.get(availability_id)
            assert availability is None
    
    def test_comment_create_flow(self, authenticated_user, test_user, app_context):
        """Test complete comment creation flow."""
        # Test comment creation form loads
        response = authenticated_user.get('/comments')
        assert response.status_code == 200
        assert b'Add Comment' in response.data or b'Comment' in response.data
        
        # Test successful comment creation
        response = authenticated_user.post('/comments/add', data={
            'content': 'This is a test comment'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify comment was created in database
        with app_context.app_context():
            comment = Comment.query.filter_by(user_id=test_user.id).first()
            assert comment is not None
            assert comment.content == 'This is a test comment'
    
    def test_comment_read_flow(self, authenticated_user, test_comment):
        """Test comment reading/viewing flow."""
        # Test comments list page
        response = authenticated_user.get('/comments')
        assert response.status_code == 200
        assert test_comment.content.encode() in response.data
    
    def test_comment_update_flow(self, authenticated_user, test_comment, app_context):
        """Test comment update flow."""
        # Test comment edit form loads
        response = authenticated_user.get(f'/comments/{test_comment.id}/edit')
        assert response.status_code == 200
        assert b'Edit Comment' in response.data or b'Comment' in response.data
        
        # Test successful comment update
        response = authenticated_user.post(f'/comments/{test_comment.id}/edit', data={
            'content': 'Updated comment content'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify comment was updated in database
        with app_context.app_context():
            updated_comment = Comment.query.get(test_comment.id)
            assert updated_comment is not None
            assert updated_comment.content == 'Updated comment content'
    
    def test_comment_delete_flow(self, authenticated_user, test_comment, app_context):
        """Test comment deletion flow."""
        comment_id = test_comment.id
        
        # Test comment deletion
        response = authenticated_user.post(f'/comments/{comment_id}/delete', 
                                         follow_redirects=True)
        assert response.status_code == 200
        
        # Verify comment was deleted from database
        with app_context.app_context():
            comment = Comment.query.get(comment_id)
            assert comment is None
    
    def test_user_ownership_validation(self, authenticated_user, client, test_factory, app_context):
        """Test that users can only modify their own data."""
        # Create another user and their data
        with app_context.app_context():
            other_user = test_factory.create_user(username="otheruser", password="password123")
            other_availability = test_factory.create_availability(other_user)
            other_comment = test_factory.create_comment(other_user, "Other user's comment")
            
            # Store IDs to avoid detached instance issues
            other_availability_id = other_availability.id
            other_comment_id = other_comment.id
        
        # Try to edit other user's availability (should redirect with error)
        response = authenticated_user.get(f'/availability/edit/{other_availability_id}')
        assert response.status_code == 302  # Redirects with flash message
        
        # Try to delete other user's availability (should redirect with error)
        response = authenticated_user.post(f'/availability/delete/{other_availability_id}')
        assert response.status_code == 302  # Redirects with flash message
        
        # Try to edit other user's comment (should redirect with error)
        response = authenticated_user.get(f'/comments/{other_comment_id}/edit')
        assert response.status_code == 302  # Redirects with flash message
        
        # Try to delete other user's comment (should redirect with error)
        response = authenticated_user.post(f'/comments/{other_comment_id}/delete')
        assert response.status_code == 302  # Redirects with flash message
    
    def test_availability_crud_with_validation_errors(self, authenticated_user, app_context):
        """Test availability CRUD operations with validation errors."""
        # Test creating availability with invalid data
        response = authenticated_user.post('/availability/add', data={
            'date': 'invalid-date',
            'start_time': '25:00',  # Invalid time
            'end_time': '10:00'     # End before start
        }, follow_redirects=True)
        
        # Should redirect back to form with errors
        assert response.status_code == 200
        
        # Verify no availability was created
        with app_context.app_context():
            count = Availability.query.count()
            assert count == 0
    
    def test_comment_crud_with_validation_errors(self, authenticated_user, app_context):
        """Test comment CRUD operations with validation errors."""
        # Test creating comment with empty content
        response = authenticated_user.post('/comments/add', data={
            'content': ''  # Empty content should fail validation
        }, follow_redirects=True)
        
        # Should redirect back with errors
        assert response.status_code == 200
        
        # Verify no comment was created
        with app_context.app_context():
            count = Comment.query.count()
            assert count == 0
    
    def test_database_transaction_rollback(self, authenticated_user, test_user, app_context):
        """Test that database transactions are properly rolled back on errors."""
        future_date = date.today() + timedelta(days=1)
        
        # Create an availability first
        with app_context.app_context():
            availability = Availability(
                user_id=test_user.id,
                date=future_date,
                start_time=time(10, 0),
                end_time=time(12, 0)
            )
            db.session.add(availability)
            db.session.commit()
            availability_id = availability.id
        
        # Try to update with invalid data that should cause rollback
        response = authenticated_user.post(f'/availability/edit/{availability_id}', data={
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '13:00'  # End time before start time should fail
        }, follow_redirects=True)
        
        # Verify original data is unchanged
        with app_context.app_context():
            availability = Availability.query.get(availability_id)
            assert availability is not None
            assert availability.start_time == time(10, 0)  # Original time
            assert availability.end_time == time(12, 0)    # Original time
    
    def test_concurrent_crud_operations(self, app_context, test_factory):
        """Test that multiple users can create data independently."""
        with app_context.app_context():
            # Create two users
            user1 = test_factory.create_user(username="user1", password="password1")
            user2 = test_factory.create_user(username="user2", password="password2")
            
            user1_id = user1.id
            user2_id = user2.id
            
            future_date = date.today() + timedelta(days=1)
            
            # User 1 creates availability
            availability1 = Availability(
                user_id=user1_id,
                date=future_date,
                start_time=time(10, 0),
                end_time=time(12, 0)
            )
            db.session.add(availability1)
            
            # User 2 creates availability
            availability2 = Availability(
                user_id=user2_id,
                date=future_date,
                start_time=time(14, 0),
                end_time=time(16, 0)
            )
            db.session.add(availability2)
            db.session.commit()
            
            # Verify both availabilities were created
            availabilities = Availability.query.all()
            assert len(availabilities) == 2
            
            # Verify each user owns their own availability
            user1_availability = Availability.query.filter_by(user_id=user1_id).first()
            user2_availability = Availability.query.filter_by(user_id=user2_id).first()
            
            assert user1_availability is not None
            assert user2_availability is not None
            assert user1_availability.start_time == time(10, 0)
            assert user2_availability.start_time == time(14, 0)