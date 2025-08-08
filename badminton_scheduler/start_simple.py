#!/usr/bin/env python3
"""
Simple server starter without import issues.
"""

import webbrowser
import time
import subprocess
import sys
from pathlib import Path

def main():
    print("🏸 Starting Badminton Scheduler...")
    print("=" * 50)
    
    # Check if sample data exists, create if not
    if not Path('badminton_scheduler.db').exists():
        print("📊 Creating sample data...")
        result = subprocess.run([sys.executable, 'scripts/create_sample_data_simple.py'])
        if result.returncode != 0:
            print("❌ Failed to create sample data")
            return
    
    print("🚀 Starting server...")
    print("📱 Frontend: http://localhost:5000/static/static_frontend.html")
    print("🔧 API: http://localhost:5000")
    print("\n👥 Demo Credentials:")
    print("   Admin: admin / admin123")
    print("   User: john_smith / password123")
    print("\n⚡ Opening browser in 3 seconds...")
    print("   Press Ctrl+C to stop")
    print("=" * 50)
    
    # Wait a bit then open browser
    time.sleep(3)
    try:
        webbrowser.open('http://localhost:5000/static/static_frontend.html')
    except:
        pass
    
    # Start the server by running run.py directly
    subprocess.run([sys.executable, 'run.py'])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped!")
    except Exception as e:
        print(f"\n❌ Error: {e}")