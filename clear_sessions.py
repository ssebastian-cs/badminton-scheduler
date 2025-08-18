#!/usr/bin/env python3
"""
Script to clear all sessions and test logout functionality.
"""

import os
import glob
from app import create_app, db
from app.models import User

def clear_sessions():
    """Clear all session files and cookies."""
    print("Clearing session files...")
    
    # Remove any flask session files
    session_files = glob.glob("flask_session_*")
    for file in session_files:
        try:
            os.remove(file)
            print(f"Removed session file: {file}")
        except OSError:
            pass
    
    # Clear any temporary session directories
    session_dirs = glob.glob("flask-session*")
    for dir_path in session_dirs:
        try:
            import shutil
            shutil.rmtree(dir_path)
            print(f"Removed session directory: {dir_path}")
        except OSError:
            pass
    
    print("Session cleanup complete.")

def check_users():
    """Check current users in database."""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        print(f"\nCurrent users in database:")
        for user in users:
            print(f"- ID: {user.id}, Username: {user.username}, Role: {user.role}, Active: {user.is_active}")

if __name__ == "__main__":
    clear_sessions()
    check_users()
    print("\nTo test logout:")
    print("1. Start the app: python run.py")
    print("2. Login to the app")
    print("3. Try to logout using /auth/logout")
    print("4. Check if you're redirected to login page")