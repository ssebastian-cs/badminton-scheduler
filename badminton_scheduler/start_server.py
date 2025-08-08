#!/usr/bin/env python3
"""
Non-blocking server starter for testing.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def start_server():
    """Start the server in a non-blocking way."""
    print("🏸 Starting Badminton Scheduler...")
    print("=" * 50)
    
    # Check if everything is ready
    if not Path('static_frontend.html').exists():
        print("❌ Frontend file not found!")
        return
    
    if not Path('badminton_scheduler.db').exists():
        print("📊 Creating sample data...")
        subprocess.run([sys.executable, 'create_sample_data_simple.py'])
    
    print("🚀 Starting server...")
    print("📱 Frontend: http://localhost:5000/static_frontend.html")
    print("🔧 API: http://localhost:5000")
    print("❤️  Health: http://localhost:5000/health")
    print("\n👥 Demo Credentials:")
    print("   Admin: admin / admin123")
    print("   User: john_smith / password123")
    print("\n⚡ Opening browser in 3 seconds...")
    print("   Press Ctrl+C to stop")
    print("=" * 50)
    
    # Wait a bit then open browser
    time.sleep(3)
    try:
        webbrowser.open('http://localhost:5000/static_frontend.html')
    except:
        pass
    
    # Start the server
    from run import app
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped!")
    except Exception as e:
        print(f"\n❌ Error: {e}")