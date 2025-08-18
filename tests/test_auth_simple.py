#!/usr/bin/env python3
"""
Simple test to check auth functionality.
"""

from app import create_app

def test_basic_auth():
    """Test basic authentication flow."""
    print("Testing basic authentication...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n1. Testing login page access...")
        response = client.get('/auth/login')
        print(f"   Login page: {response.status_code} (should be 200)")
        
        if response.status_code == 200:
            print("   ✓ Login page accessible")
            
            print("\n2. Testing admin login...")
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=False)
            
            print(f"   Admin login: {login_response.status_code} (should be 302)")
            
            if login_response.status_code == 302:
                print("   ✓ Admin login successful")
                
                print("\n3. Testing dashboard access...")
                dashboard_response = client.get('/', follow_redirects=False)
                print(f"   Dashboard: {dashboard_response.status_code} (should be 302 to admin)")
                
                print("\n4. Testing logout...")
                logout_response = client.get('/auth/logout', follow_redirects=False)
                print(f"   Logout: {logout_response.status_code} (should be 302)")
                
                if logout_response.status_code == 302:
                    print("   ✓ Logout successful")
                    
                    print("\n5. Testing access after logout...")
                    after_logout = client.get('/', follow_redirects=False)
                    print(f"   Dashboard after logout: {after_logout.status_code} (should be 302 to login)")
                    
                    if after_logout.status_code == 302:
                        print("   ✓ Properly redirected to login after logout")
                        return True
        
        return False

if __name__ == "__main__":
    try:
        success = test_basic_auth()
        if success:
            print("\n✅ Basic authentication is working")
        else:
            print("\n❌ Authentication has issues")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()