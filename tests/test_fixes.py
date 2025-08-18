#!/usr/bin/env python3
"""
Test the fixes for the reported issues.
"""

from app import create_app

def test_all_fixes():
    """Test all the fixes."""
    print("Testing all fixes...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n=== Testing Login/Logout ===\n")
        
        # Test login
        print("1. Testing admin login...")
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if login_response.status_code == 302:
            print("   ✓ Admin login successful")
            
            # Test dashboard access
            print("\n2. Testing dashboard access...")
            dashboard_response = client.get('/', follow_redirects=True)
            
            if dashboard_response.status_code == 200:
                print("   ✓ Dashboard accessible")
                
                # Check if admin lands on availability dashboard (not admin dashboard)
                if b'Add Availability' in dashboard_response.data:
                    print("   ✓ Admin lands on availability dashboard")
                else:
                    print("   ❌ Admin not on availability dashboard")
                
                # Check if admin panel button is present
                if b'Admin Panel' in dashboard_response.data:
                    print("   ✓ Admin Panel button present")
                else:
                    print("   ❌ Admin Panel button missing")
                
                # Test availability dashboard specifically
                print("\n3. Testing availability dashboard...")
                avail_response = client.get('/availability', follow_redirects=True)
                
                if avail_response.status_code == 200:
                    print("   ✓ Availability dashboard accessible")
                else:
                    print(f"   ❌ Availability dashboard failed: {avail_response.status_code}")
                
                # Test logout
                print("\n4. Testing logout...")
                logout_response = client.get('/auth/logout', follow_redirects=False)
                
                if logout_response.status_code == 302:
                    print("   ✓ Logout successful")
                    
                    # Test access after logout
                    print("\n5. Testing access after logout...")
                    after_logout = client.get('/', follow_redirects=False)
                    
                    if after_logout.status_code == 302:
                        print("   ✓ Properly redirected after logout")
                        return True
                    else:
                        print(f"   ❌ Not redirected after logout: {after_logout.status_code}")
                else:
                    print(f"   ❌ Logout failed: {logout_response.status_code}")
            else:
                print(f"   ❌ Dashboard not accessible: {dashboard_response.status_code}")
        else:
            print(f"   ❌ Admin login failed: {login_response.status_code}")
        
        return False

if __name__ == "__main__":
    try:
        success = test_all_fixes()
        if success:
            print("\n✅ All fixes are working correctly")
        else:
            print("\n❌ Some issues remain")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.pri