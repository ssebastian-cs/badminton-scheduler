#!/usr/bin/env python3
"""
Test script to verify logout functionality.
"""

from app import create_app
import sys

def test_logout():
    """Test the logout functionality."""
    print("Testing logout functionality...")
    
    # Create app for testing with CSRF disabled
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n1. Testing login...")
        
        # First, try to access dashboard (should redirect to login)
        response = client.get('/')
        print(f"   Dashboard access without login: {response.status_code} (should be 302 redirect)")
        
        # Login with admin credentials
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        print(f"   Login response: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print("   ✓ Login successful (redirected)")
            
            # Now try to access dashboard (should work)
            dashboard_response = client.get('/', follow_redirects=True)
            print(f"   Dashboard access after login: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("   ✓ Dashboard accessible after login")
                
                print("\n2. Testing logout...")
                
                # Now logout
                logout_response = client.get('/auth/logout', follow_redirects=False)
                print(f"   Logout response: {logout_response.status_code}")
                
                if logout_response.status_code == 302:
                    print("   ✓ Logout successful (redirected)")
                    
                    # Try to access dashboard again (should redirect to login)
                    dashboard_after_logout = client.get('/', follow_redirects=False)
                    print(f"   Dashboard access after logout: {dashboard_after_logout.status_code}")
                    
                    if dashboard_after_logout.status_code == 302:
                        print("   ✓ Dashboard properly protected after logout")
                        print("\n✅ LOGOUT FUNCTIONALITY WORKING CORRECTLY")
                        return True
                    else:
                        print("   ❌ Dashboard still accessible after logout")
                        return False
                else:
                    print("   ❌ Logout failed")
                    return False
            else:
                print("   ❌ Dashboard not accessible after login")
                return False
        else:
            print("   ❌ Login failed")
            return False

if __name__ == "__main__":
    success = test_logout()
    sys.exit(0 if success else 1)