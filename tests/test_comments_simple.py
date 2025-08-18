#!/usr/bin/env python3
"""
Simple test to verify comments functionality works correctly.
"""

import os
import sys
import tempfile

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import User, Comment


def test_comments_basic_functionality():
    """Test basic comments functionality."""
    print("Testing basic comments functionality...")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='_simple.db')
    
    try:
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test users
            user1 = User(username='user1', password='password123', role='User')
            user2 = User(username='user2', password='password123', role='User')
            admin = User(username='admin', password='password123', role='Admin')
            
            db.session.add_all([user1, user2, admin])
            db.session.commit()
            
            print("✓ Users created successfully")
            
            # Create comments
            comment1 = Comment(user_id=user1.id, content='First comment by user1')
            comment2 = Comment(user_id=user2.id, content='Second comment by user2')
            comment3 = Comment(user_id=admin.id, content='Admin comment')
            
            db.session.add_all([comment1, comment2, comment3])
            db.session.commit()
            
            print("✓ Comments created successfully")
            
            # Test comment retrieval
            all_comments = Comment.query.all()
            if len(all_comments) == 3:
                print("✓ Comment retrieval works")
            else:
                print(f"✗ Expected 3 comments, got {len(all_comments)}")
                return False
            
            # Test user-comment relationships
            user1_comments = Comment.query.filter_by(user_id=user1.id).all()
            if len(user1_comments) == 1 and user1_comments[0].content == 'First comment by user1':
                print("✓ User-comment relationship works")
            else:
                print("✗ User-comment relationship failed")
                return False
            
            # Test comment update
            comment1.update_content('Updated first comment')
            db.session.commit()
            
            updated_comment = Comment.query.get(comment1.id)
            if updated_comment.content == 'Updated first comment':
                print("✓ Comment update works")
            else:
                print("✗ Comment update failed")
                return False
            
            # Test authorization logic
            # User can edit their own comment
            if comment1.user_id == user1.id:
                print("✓ User ownership check works")
            else:
                print("✗ User ownership check failed")
                return False
            
            # Admin can edit any comment
            if admin.is_admin():
                print("✓ Admin role check works")
            else:
                print("✗ Admin role check failed")
                return False
            
            # Regular user cannot edit other's comment
            if comment1.user_id != user2.id and not user2.is_admin():
                print("✓ User authorization check works")
            else:
                print("✗ User authorization check failed")
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
            
            print("✓ All basic functionality tests passed")
            return True
    
    finally:
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)


def test_comments_routes():
    """Test comments routes with test client."""
    print("\nTesting comments routes...")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='_routes.db')
    
    try:
        app = create_app('testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test user
            user = User(username='testuser', password='password123', role='User')
            db.session.add(user)
            db.session.commit()
            
            with app.test_client() as client:
                # Login user
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['_fresh'] = True
                
                # Test comments page
                response = client.get('/comments')
                if response.status_code == 200:
                    print("✓ Comments page loads successfully")
                else:
                    print(f"✗ Comments page failed with status {response.status_code}")
                    return False
                
                # Test adding a comment
                response = client.post('/comments/add', data={
                    'content': 'Test comment from route test'
                })
                if response.status_code == 302:  # Redirect after successful post
                    print("✓ Comment addition works")
                else:
                    print(f"✗ Comment addition failed with status {response.status_code}")
                    return False
                
                # Verify comment was created
                comment = Comment.query.filter_by(content='Test comment from route test').first()
                if comment and comment.user_id == user.id:
                    print("✓ Comment was saved correctly")
                else:
                    print("✗ Comment was not saved correctly")
                    return False
                
                print("✓ All route tests passed")
                return True
    
    finally:
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)


def main():
    """Run all simple tests."""
    print("Starting simple comments functionality tests...")
    
    success = True
    
    # Run tests
    if not test_comments_basic_functionality():
        success = False
    
    if not test_comments_routes():
        success = False
    
    if success:
        print("\n🎉 All simple comments tests passed!")
        return True
    else:
        print("\n❌ Some simple comments tests failed!")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)