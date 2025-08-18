#!/usr/bin/env python3
"""
Test what happens when visiting the landing page without being logged in.
"""

from app import create_app

def test_landing_page():
    """Test the landing page behavior."""
    print("Testing landing page behavior...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n=== Testing Unauthenticated Access ===\n")
        
        # Test root URL without being logged in
        print("1. Testing root URL without login...")
        response = client.get('/', follow_redirects=False)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Location: {response.headers.get('Location', 'None')}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/auth/login' in location:
                print("   ✓ Correctly redirected to login page")
            else:
                print(f"   ❌ Redirected to wrong location: {location}")
        else:
            print(f"   ❌ Expected redirect (302), got {response.status_code}")
        
        # Test what happens when following redirects
        print("\n2. Testing root URL with redirects...")
        response = client.get('/', follow_redirects=True)
        
        print(f"   Final Status Code: {response.status_code}")
        
        if response.status_code == 200:
            if b'login' in response.data.lower() or b'username' in response.data.lower():
                print("   ✓ Landed on login page")
            else:
                print("   ❌ Did not land on login page")
                # Print first 200 chars to see what page we're on
                content = response.data.decode('utf-8')[:200]
                print(f"   Content preview: {content}")
        
        return True

if __name__ == "__main__":
    try:
        test_landing_page()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()