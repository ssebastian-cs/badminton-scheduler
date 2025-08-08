#!/usr/bin/env python3
"""
Quick test to verify the app works before starting the server.
"""

from run import app, db, User, Availability, Feedback

def test_app():
    """Test basic app functionality."""
    print("🧪 Testing Badminton Scheduler App...")
    print("=" * 50)
    
    with app.app_context():
        # Test database connection
        try:
            user_count = User.query.count()
            avail_count = Availability.query.count()
            feedback_count = Feedback.query.count()
            
            print(f"✅ Database connection: OK")
            print(f"   Users: {user_count}")
            print(f"   Availability entries: {avail_count}")
            print(f"   Feedback entries: {feedback_count}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
        
        # Test user authentication
        try:
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user and admin_user.check_password('admin123'):
                print(f"✅ Admin user authentication: OK")
            else:
                print(f"❌ Admin user authentication: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
        
        # Test frontend file exists
        try:
            with open('static_frontend.html', 'r') as f:
                content = f.read()
                if 'Badminton Scheduler' in content:
                    print(f"✅ Frontend file: OK ({len(content)} characters)")
                else:
                    print(f"❌ Frontend file: Invalid content")
                    return False
        except FileNotFoundError:
            print(f"❌ Frontend file: NOT FOUND")
            return False
        except Exception as e:
            print(f"❌ Frontend file error: {e}")
            return False
    
    print("\n🎉 All tests passed! App is ready to run.")
    print("\n🚀 To start the server, run:")
    print("   python run.py")
    print("\n🌐 Then visit:")
    print("   http://localhost:5000/static_frontend.html")
    print("\n👥 Demo credentials:")
    print("   Admin: admin / admin123")
    print("   User: john_smith / password123")
    
    return True

if __name__ == '__main__':
    test_app()