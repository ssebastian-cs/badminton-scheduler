#!/usr/bin/env python3
"""
Simple server health check.
"""

import requests
import time

def test_server_health():
    """Test if server is responding."""
    print("Testing server health...")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is healthy!")
            print(f"Response: {data}")
            return True
        else:
            print(f"✗ Server responded but with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server at http://localhost:5000")
        print("Make sure the server is running with: python run.py")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_frontend_access():
    """Test if frontend is accessible."""
    print("\nTesting frontend access...")
    
    try:
        response = requests.get("http://localhost:5000/static_frontend.html", timeout=5)
        print(f"Frontend access status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Frontend is accessible!")
            print("You can open http://localhost:5000/static_frontend.html in your browser")
            return True
        else:
            print(f"✗ Frontend responded but with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error accessing frontend: {e}")
        return False

if __name__ == "__main__":
    print("Checking server status...\n")
    
    health_ok = test_server_health()
    frontend_ok = test_frontend_access()
    
    print("\n" + "="*50)
    if health_ok and frontend_ok:
        print("✓ Server is running and accessible!")
        print("\nTo test admin login:")
        print("1. Open http://localhost:5000/static_frontend.html in your browser")
        print("2. Use credentials: admin / admin123")
        print("3. You should see admin features after login")
    else:
        print("✗ Server issues detected. Check the server terminal for errors.")