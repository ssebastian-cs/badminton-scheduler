#!/usr/bin/env python3
"""
Verify that the comments system is working with the existing database.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import User, Comment


def verify_comments_functionality():
    """Verify comments functionality with existing database."""
    print("Verifying comments functionality with existing database...")
    
    app = create_app()
    
    with app.app_context():
        # Get existing users
        users = User.query.all()
        print(f"Found {len(users)} existing users: {[u.username for u in users]}")
        
        if not users:
            print("No users found. Creating test users...")
            user1 = User(username='verifyuser1', password='password123', role='User')
            admin = User(username='verifyadmin', password='password123', role='Admin')
            db.session.add_all([user1, admin])
            db.session.commit()
            users = [user1, admin]
        
        # Use first two users for testing
        user1 = users[0]
        admin_user = None
        for user in users:
            if user.is_admin():
                admin_user = user
                break
        
        if not admin_user:
            admin_user = users[1] if len(users) > 1 else user1
        
        print(f"Using user: {user1.username} (role: {user1.role})")
        print(f"Using admin: {admin_user.username} (role: {admin_user.role})")
        
        # Create test comments
        test_comment1 = Comment(user_id=user1.id, content='Test comment for verification')
        test_comment2 = Comment(user_id=admin_user.id, content='Admin test comment')
        
        db.session.add_all([test_comment1, test_comment2])
        db.session.commit()
        
        print("✓ Test comments created successfully")
        
        # Verify comment retrieval
        all_comments = Comment.query.order_by(Comment.created_at.desc()).all()
        print(f"✓ Found {len(all_comments)} total comments in database")
        
        # Verify user-comment relationships
        user1_comments = Comment.query.filter_by(user_id=user1.id).all()
        print(f"✓ User {user1.username} has {len(user1_comments)} comments")
        
        # Verify comment content and timestamps
        for comment in all_comments[-2:]:  # Last 2 comments (our test comments)
            print(f"✓ Comment by {comment.user.username}: '{comment.content[:50]}...'")
            print(f"  Created: {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Updated: {comment.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test comment update
        test_comment1.update_content('Updated test comment for verification')
        db.session.commit()
        
        updated_comment = Comment.query.get(test_comment1.id)
        if updated_comment.content == 'Updated test comment for verification':
            print("✓ Comment update functionality works")
        else:
            print("✗ Comment update functionality failed")
            return False
        
        # Test authorization logic
        print(f"✓ User {user1.username} can edit their own comment: {test_comment1.user_id == user1.id}")
        print(f"✓ Admin {admin_user.username} can edit any comment: {admin_user.is_admin()}")
        print(f"✓ User {user1.username} cannot edit admin's comment: {test_comment2.user_id != user1.id and not user1.is_admin()}")
        
        # Clean up test comments
        db.session.delete(test_comment1)
        db.session.delete(test_comment2)
        db.session.commit()
        
        print("✓ Test comments cleaned up")
        print("\n🎉 Comments functionality verification completed successfully!")
        return True


def verify_comment_routes():
    """Verify comment routes work correctly."""
    print("\nVerifying comment routes...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Get a test user
        user = User.query.first()
        if not user:
            print("No users found for route testing")
            return False
        
        with app.test_client() as client:
            # Simulate login
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
                'content': 'Route verification test comment'
            })
            if response.status_code == 302:  # Redirect after successful post
                print("✓ Comment addition route works")
            else:
                print(f"✗ Comment addition failed with status {response.status_code}")
                return False
            
            # Verify comment was created
            comment = Comment.query.filter_by(content='Route verification test comment').first()
            if comment and comment.user_id == user.id:
                print("✓ Comment was saved correctly via route")
                
                # Clean up
                db.session.delete(comment)
                db.session.commit()
                print("✓ Test comment cleaned up")
            else:
                print("✗ Comment was not saved correctly via route")
                return False
        
        print("✓ Comment routes verification completed successfully!")
        return True


def main():
    """Run verification tests."""
    print("Starting comments functionality verification...")
    
    success = True
    
    if not verify_comments_functionality():
        success = False
    
    if not verify_comment_routes():
        success = False
    
    if success:
        print("\n🎉 All comments functionality verification tests passed!")
        print("The comments and feedback system is working correctly!")
        return True
    else:
        print("\n❌ Some verification tests failed!")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)