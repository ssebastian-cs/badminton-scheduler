#!/usr/bin/env python3
"""
Startup script for the Badminton Scheduler application.
This script will:
1. Check if sample data exists
2. Create sample data if needed
3. Start the Flask server
4. Provide instructions for accessing the app
"""

import os
import sys
import webbrowser
import time
from pathlib import Path

def check_database():
    """Check if database exists and has data."""
    db_path = Path('badminton_scheduler.db')
    return db_path.exists()

def create_sample_data():
    """Create sample data if needed."""
    print("Creating sample data...")
    try:
        from create_sample_data_simple import create_sample_data
        create_sample_data()
        return True
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return False

def start_server():
    """Start the Flask server."""
    print("\n" + "="*60)
    print("🏸 BADMINTON SCHEDULER - STARTING UP")
    print("="*60)
    
    # Check if database exists
    if not check_database():
        print("📊 Database not found. Creating sample data...")
        if not create_sample_data():
            print("❌ Failed to create sample data. Exiting.")
            return
    else:
        print("📊 Database found!")
    
    print("\n🚀 Starting Flask server...")
    print("📱 Frontend available at: http://localhost:5000/static_frontend.html")
    print("🔧 API available at: http://localhost:5000")
    print("❤️  Health check: http://localhost:5000/health")
    
    print("\n👥 Demo Credentials:")
    print("   Admin: admin / admin123")
    print("   User:  john_smith / password123")
    
    print("\n⚡ Server starting in 3 seconds...")
    print("   Press Ctrl+C to stop the server")
    print("="*60)
    
    time.sleep(3)
    
    # Open browser automatically
    try:
        webbrowser.open('http://localhost:5000/static_frontend.html')
    except:
        pass
    
    # Start the server
    try:
        from run import app
        app.run(debug=True, port=5000, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thanks for using Badminton Scheduler!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    start_server()