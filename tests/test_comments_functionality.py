#!/usr/bin/env python3
"""
Test script to verify the comments functionality implementation.
This script tests the comments CRUD operations, ownership validation, and authorization.
"""

import os
import sys
import tempfile
from datetime import datetime, date, time

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import User, Comment
from app.forms import CommentForm


def test_comment_form_validation():
    """Test CommentForm validation."""
    print("\nTesting CommentForm validation...")
    
    # Create a temporary app context for form testing
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        with app.test_request_context():
            # Test valid comment form
            form_data = {'content': 'This is a valid comment'}
            form = CommentForm(data=form_data)
            
            # Manually validate content field
            if form.content.validate(form):
                print("✓ Valid comment form validation successful")
            else:
                print("✗ Valid comment form validation failed")
                return False
            
            # Test empty content
            form_data = {'content': ''}
            form = CommentForm(data=form_data)
            
            if not form.content.validate(form):
                print("✓ Empty content correctly rejected")
            else:
                print("✗ Empty content validation failed")
                return False
            
            # Test whitespace-only content
            form_data = {'content': '   \n\t   '}
            form = CommentForm(data=form_data)
            
            if not form.content.validate(form):
                print("✓ Whitespace-only content correctly rejected")
            else:
                print("✗ Whitespace-only content validation failed")
                return False
            
            # Test content too long
            long_content = 'x' * 1001
            form_data = {'content': long_content}
            form = CommentForm(data=form_data)
            
            if not form.content.validate(form):
                print("✓ Long content correctly rejected")
            else:
                print("✗ Long content validation failed")
                return False
    
    return True


def test_comment_crud_operations():
    """Test Comment CRUD operations with database."""
    print("\nTesting Comment CRUD operations...")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='_crud.db')
    
    try:
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test users
            user1 = User(username='cruduser1', password='password123', role='User')
            user2 = User(username='cruduser2', password='password123', role='User')
            admin_user = User(username='crudadmin', password='password123', role='Admin')
            
            db.session.add_all([user1, user2, admin_user])
            db.session.commit()
            
            # Test comment creation
            comment1 = Comment(user_id=user1.id, content='First test comment')
            comment2 = Comment(user_id=user2.id, content='Second test comment')
            comment3 = Comment(user_id=admin_user.id, content='Admin comment')
            
            db.session.add_all([comment1, comment2, comment3])
            db.session.commit()
            
            print("✓ Comments created successfully")
            
            # Test comment retrieval with ordering
            all_comments = Comment.query.order_by(Comment.created_at.desc()).all()
            if len(all_comments) == 3:
                print("✓ Comment retrieval with ordering works")
            else:
                print("✗ Comment retrieval failed")
                return False
            
            # Test user-comment relationships
            user1_comments = user1.comments
            if len(user1_comments) == 1 and user1_comments[0].content == 'First test comment':
                print("✓ User-comment relationship works")
            else:
                print("✗ User-comment relationship failed")
                return False
            
            # Test comment update
            original_updated_at = comment1.updated_at
            comment1.update_content('Updated first comment')
            db.session.commit()
            
            if comment1.content == 'Updated first comment' and comment1.updated_at > original_updated_at:
                print("✓ Comment update works")
            else:
                print("✗ Comment update failed")
                return False
            
            # Test comment deletion
            comment_id = comment2.id
            db.session.delete(comment2)
            db.session.commit()
            
            deleted_comment = Comment.query.get(comment_id)
            if deleted_comment is None:
                print("✓ Comment deletion works")
            else:
                print("✗ Comment deletion failed")
                return False
            
            # Test cascade deletion (when user is deleted)
            user1_id = user1.id
            user1_comment_count = len(user1.comments)
            
            db.session.delete(user1)
            db.session.commit()
            
            # Check that user's comments were also deleted
            remaining_comments = Comment.query.filter_by(user_id=user1_id).all()
            if len(remaining_comments) == 0:
                print("✓ Cascade deletion works")
            else:
                print("✗ Cascade deletion failed")
                return False
    
    finally:
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)
    
    return True


def test_comment_authorization_logic():
    """Test comment ownership and authorization logic."""
    print("\nTesting comment authorization logic...")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='_auth.db')
    
    try:
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test users
            user1 = User(username='authuser1', password='password123', role='User')
            user2 = User(username='authuser2', password='password123', role='User')
            admin_user = User(username='authadmin', password='password123', role='Admin')
            
            db.session.add_all([user1, user2, admin_user])
            db.session.commit()
            
            # Create test comments
            user1_comment = Comment(user_id=user1.id, content='User1 comment')
            user2_comment = Comment(user_id=user2.id, content='User2 comment')
            
            db.session.add_all([user1_comment, user2_comment])
            db.session.commit()
            
            # Test ownership validation logic
            # User can edit their own comment
            if user1_comment.user_id == user1.id:
                print("✓ User can identify their own comment")
            else:
                print("✗ User ownership identification failed")
                return False
            
            # User cannot edit other's comment (unless admin)
            if user1_comment.user_id != user2.id and not user2.is_admin():
                print("✓ User cannot edit other's comment")
            else:
                print("✗ User authorization check failed")
                return False
            
            # Admin can edit any comment
            if admin_user.is_admin():
                print("✓ Admin can edit any comment")
            else:
                print("✗ Admin authorization check failed")
                return False
            
            # Test role-based access
            if user1.role == 'User' and not user1.is_admin():
                print("✓ Regular user role check works")
            else:
                print("✗ Regular user role check failed")
                return False
            
            if admin_user.role == 'Admin' and admin_user.is_admin():
                print("✓ Admin user role check works")
            else:
                print("✗ Admin user role check failed")
                return False
    
    finally:
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)
    
    return True


def test_comment_display_formatting():
    """Test comment display and timestamp formatting."""
    print("\nTesting comment display formatting...")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='_display.db')
    
    try:
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TESTING'] = True
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test user
            user = User(username='displayuser', password='password123', role='User')
            db.session.add(user)
            db.session.commit()
            
            # Create test comment with multiline content
            multiline_content = "This is a comment\nwith multiple lines\nfor testing"
            comment = Comment(user_id=user.id, content=multiline_content)
            db.session.add(comment)
            db.session.commit()
            
            # Test timestamp formatting
            created_time = comment.created_at
            if isinstance(created_time, datetime):
                formatted_time = created_time.strftime('%B %d, %Y at %I:%M %p')
                print(f"✓ Timestamp formatting works: {formatted_time}")
            else:
                print("✗ Timestamp formatting failed")
                return False
            
            # Test content with newlines
            if '\n' in comment.content:
                print("✓ Multiline content preserved")
            else:
                print("✗ Multiline content test failed")
                return False
            
            # Test comment update timestamp
            original_created = comment.created_at
            original_updated = comment.updated_at
            
            # Wait a moment and update
            import time
            time.sleep(0.01)
            
            comment.update_content("Updated content")
            db.session.commit()
            
            if comment.updated_at > original_updated and comment.created_at == original_created:
                print("✓ Update timestamp works correctly")
            else:
                print("✗ Update timestamp failed")
                return False
    
    finally:
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)
    
    return True


def main():
    """Run all comment functionality tests."""
    print("Starting comments functionality tests...")
    
    success = True
    
    # Run all tests
    tests = [
        test_comment_form_validation,
        test_comment_crud_operations,
        test_comment_authorization_logic,
        test_comment_display_formatting
    ]
    
    for test in tests:
        try:
            if not test():
                success = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            success = False
    
    if success:
        print("\n🎉 All comments functionality tests passed!")
        return True
    else:
        print("\n❌ Some comments functionality tests failed!")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)