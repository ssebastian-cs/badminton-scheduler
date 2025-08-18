#!/usr/bin/env python3
"""
Test to isolate the logout bug.
"""

from app import create_app

def test_logout_bug():
    """Test the logout functionality specifically."""
    print("Testing logout bug...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n=== Step-by-step logout test ===\n")
        
        # Step 1: Login
        print("1. Logging in as admin...")
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        print(f"   Login status: {login_response.status_code}")
        
        # Step 2: Verify we're logged in
        print("\n2. Checking if logged in...")
        dashboard_response = client.get('/', follow_redirects=False)
        print(f"   Dashboard status: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            print("   ✓ User is logged in")
        else:
            print("   ❌ User not logged in")
            return
        
        # Step 3: Logout
        print("\n3. Attempting logout...")
        logout_response = client.get('/auth/logout', follow_redirects=False)
        print(f"   Logout status: {logout_response.status_code}")
        print(f"   Logout redirect: {logout_response.headers.get('Location', 'None')}")
        
        # Step 4: Check if actually logged out
        print("\n4. Checking if actually logged out...")
        after_logout = client.get('/', follow_redirects=False)
        print(f"   After logout status: {after_logout.status_code}")
        print(f"   After logout redirect: {after_logout.headers.get('Location', 'None')}")
        
        if after_logout.status_code == 302:
            location = after_logout.headers.get('Location', '')
            if 'login' in location:
                print("   ✓ Properly logged out - redirected to login")
            else:
                print(f"   ❌ Wrong redirect after logout: {location}")
        elif after_logout.status_code == 200:
            print("   ❌ LOGOUT BUG: Still logged in after logout!")
            # Check what page we're on
            if b'Welcome' in after_logout.data:
                print("   ❌ Still on dashboard - logout failed completely")
        
        # Step 5: Try accessing protected page
        print("\n5. Testing protected page access...")
        protected_response = client.get('/availability/add', follow_redirects=False)
        print(f"   Protected page status: {protected_response.status_code}")
        if protected_response.status_code == 302:
            print("   ✓ Protected page redirects (user logged out)")
        else:
            print("   ❌ Protected page accessible (user still logged in)")

if __name__ == "__main__":
    try:
        test_logout_bug()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()