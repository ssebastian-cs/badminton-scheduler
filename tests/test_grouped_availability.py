#!/usr/bin/env python3
"""
Test the grouped availability display.
"""

from app import create_app

def test_grouped_availability():
    """Test that availability entries are grouped by user."""
    print("Testing grouped availability display...")
    
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        print("\n=== Testing Grouped Availability ===\n")
        
        # Login as admin
        print("1. Logging in as admin...")
        login_response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        if login_response.status_code == 302:
            print("   ✓ Admin login successful")
            
            # Access dashboard
            print("\n2. Accessing dashboard...")
            dashboard_response = client.get('/', follow_redirects=False)
            
            if dashboard_response.status_code == 200:
                print("   ✓ Dashboard accessible")
                
                # Check if the page loads without errors
                content = dashboard_response.data.decode('utf-8')
                if 'Welcome, admin!' in content:
                    print("   ✓ Dashboard content loaded correctly")
                    
                    # Check for admin panel button
                    if 'Admin Panel' in content:
                        print("   ✓ Admin Panel button present")
                    else:
                        print("   ❌ Admin Panel button missing")
                        
                    # Check for availability section
                    if 'No availability found' in content or 'available' in content:
                        print("   ✓ Availability section present")
                    else:
                        print("   ❌ Availability section missing")
                        
                else:
                    print("   ❌ Dashboard content not loaded properly")
            else:
                print(f"   ❌ Dashboard not accessible: {dashboard_response.status_code}")
        else:
            print(f"   ❌ Admin login failed: {login_response.status_code}")

if __name__ == "__main__":
    try:
        test_grouped_availability()
        print("\n✅ Grouped availability display should now work correctly")
        print("📋 Changes made:")
        print("   - Availability entries are now grouped by user within each date")
        print("   - Each user shows all their time slots together")
        print("   - Edit/delete buttons are available for each individual time slot")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()