#!/usr/bin/env python3
"""
Test what happens when we visit the login page directly.
"""

from app import create_app

def test_login_page():
    """Test the login page behavior."""
    print("Testing login page behavior...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n=== Testing Login Page Direct Access ===\n")
        
        # Test 1: Visit login page without being logged in
        print("1. Testing login page without authentication...")
        response = client.get('/auth/login', follow_redirects=False)
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Login page accessible")
            if b'username' in response.data.lower() or b'login' in response.data.lower():
                print("   ✓ Login form present")
            else:
                print("   ❌ Login form not found")
        elif response.status_code == 302:
            print(f"   ❌ Login page redirects: {response.headers.get('Location')}")
        
        # Test 2: Login first, then visit login page
        print("\n2. Testing login page after authentication...")
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if login_response.status_code == 302:
            print("   ✓ Login successful")
            
            # Now try to visit login page while logged in
            login_page_response = client.get('/auth/login', follow_redirects=False)
            print(f"   Login page status while logged in: {login_page_response.status_code}")
            
            if login_page_response.status_code == 302:
                location = login_page_response.headers.get('Location', '')
                print(f"   Redirected to: {location}")
                if 'availability' in location or location.endswith('/'):
                    print("   ✓ Correctly redirected away from login page")
                else:
                    print("   ❌ Unexpected redirect location")
            else:
                print("   ❌ Should redirect when already logged in")
        
        # Test 3: Test root URL behavior
        print("\n3. Testing root URL behavior...")
        root_response = client.get('/', follow_redirects=False)
        print(f"   Root URL status: {root_response.status_code}")
        
        if root_response.status_code == 200:
            print("   ✓ Root URL accessible (user logged in)")
        elif root_response.status_code == 302:
            print(f"   Root URL redirects to: {root_response.headers.get('Location')}")

if __name__ == "__main__":
    try:
        test_login_page()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()