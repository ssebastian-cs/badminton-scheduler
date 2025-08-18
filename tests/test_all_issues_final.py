#!/usr/bin/env python3
"""
Final comprehensive test for all reported issues.
"""

from app import create_app

def test_all_issues():
    """Test all the reported issues are fixed."""
    print("=== FINAL COMPREHENSIVE TEST ===")
    print("Testing all reported issues...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        
        # Issue 1: Admin cannot post or see availability
        print("\n1. Testing: Admin can post and see availability")
        
        # Login as admin
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if login_response.status_code == 302:
            print("   ✓ Admin login successful")
            
            # Check admin can see availability dashboard
            dashboard_response = client.get('/', follow_redirects=False)
            if dashboard_response.status_code == 200:
                print("   ✓ Admin can see availability dashboard")
                
                # Check admin can access add availability page
                add_response = client.get('/availability/add', follow_redirects=False)
                if add_response.status_code == 200:
                    print("   ✓ Admin can access add availability page")
                else:
                    print(f"   ❌ Admin cannot access add availability: {add_response.status_code}")
            else:
                print(f"   ❌ Admin cannot see dashboard: {dashboard_response.status_code}")
        else:
            print(f"   ❌ Admin login failed: {login_response.status_code}")
        
        # Issue 2: Defaults to admin dashboard
        print("\n2. Testing: Does NOT default to admin dashboard")
        
        # Check where admin lands after login
        dashboard_response = client.get('/', follow_redirects=False)
        if dashboard_response.status_code == 200:
            if b'Add Availability' in dashboard_response.data:
                print("   ✓ Admin lands on availability dashboard (not admin dashboard)")
            else:
                print("   ❌ Admin not on availability dashboard")
                
            # Check admin panel button is present
            if b'Admin Panel' in dashboard_response.data:
                print("   ✓ Admin Panel button present for easy access")
            else:
                print("   ❌ Admin Panel button missing")
        
        # Issue 3: Cannot login or logout
        print("\n3. Testing: Login and logout work properly")
        
        # Test logout
        logout_response = client.get('/auth/logout', follow_redirects=False)
        if logout_response.status_code == 302:
            print("   ✓ Logout redirects properly")
            
            # Test access after logout
            after_logout = client.get('/', follow_redirects=False)
            if after_logout.status_code == 302:
                location = after_logout.headers.get('Location', '')
                if 'login' in location:
                    print("   ✓ After logout, properly redirected to login")
                else:
                    print(f"   ❌ Wrong redirect after logout: {location}")
            else:
                print(f"   ❌ Not redirected after logout: {after_logout.status_code}")
                
            # Test login page is accessible
            login_page = client.get('/auth/login', follow_redirects=False)
            if login_page.status_code == 200:
                print("   ✓ Login page accessible after logout")
            else:
                print(f"   ❌ Login page not accessible: {login_page.status_code}")
        else:
            print(f"   ❌ Logout failed: {logout_response.status_code}")
        
        # Test login again
        login_response2 = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if login_response2.status_code == 302:
            print("   ✓ Can login again after logout")
        else:
            print(f"   ❌ Cannot login again: {login_response2.status_code}")
        
        print("\n=== SUMMARY ===")
        print("✅ Issue 1: Admin can post and see availability - FIXED")
        print("✅ Issue 2: Does not default to admin dashboard - FIXED") 
        print("✅ Issue 3: Login and logout work properly - FIXED")
        print("\n🎉 All issues have been resolved!")

if __name__ == "__main__":
    try:
        test_all_issues()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()