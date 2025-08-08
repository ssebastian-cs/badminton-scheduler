#!/usr/bin/env python3
"""
Database backup script for Badminton Scheduler on Alwaysdata
Creates backups of the SQLite database with timestamp.
"""

import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def backup_sqlite_database(db_path, backup_dir='backups'):
    """Create a backup of the SQLite database."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"badminton_scheduler_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Verify the backup
        if os.path.exists(backup_path):
            original_size = os.path.getsize(db_path)
            backup_size = os.path.getsize(backup_path)
            
            if original_size == backup_size:
                print(f"✅ Database backup created successfully: {backup_path}")
                print(f"   Size: {backup_size} bytes")
                return backup_path
            else:
                print(f"❌ Backup verification failed: size mismatch")
                return False
        else:
            print(f"❌ Backup file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return False

def export_data_to_json(db_path, export_dir='exports'):
    """Export database data to JSON format."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate export filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_filename = f"badminton_scheduler_export_{timestamp}.json"
    export_path = os.path.join(export_dir, export_filename)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue  # Skip system tables
            
            print(f"🔄 Exporting table: {table_name}")
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            table_data = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    value = row[key]
                    # Handle datetime objects
                    if isinstance(value, str) and ('T' in value or ' ' in value):
                        # Assume it's a datetime string
                        row_dict[key] = value
                    else:
                        row_dict[key] = value
                table_data.append(row_dict)
            
            export_data['tables'][table_name] = table_data
            print(f"   Exported {len(table_data)} rows")
        
        conn.close()
        
        # Write to JSON file
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Data export completed: {export_path}")
        return export_path
        
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        return False

def cleanup_old_backups(backup_dir='backups', keep_days=30):
    """Remove backup files older than specified days."""
    if not os.path.exists(backup_dir):
        return
    
    cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    removed_count = 0
    
    for filename in os.listdir(backup_dir):
        if filename.startswith('badminton_scheduler_backup_'):
            file_path = os.path.join(backup_dir, filename)
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    print(f"🗑️  Removed old backup: {filename}")
                except Exception as e:
                    print(f"❌ Failed to remove {filename}: {str(e)}")
    
    if removed_count > 0:
        print(f"✅ Cleaned up {removed_count} old backup files")
    else:
        print("ℹ️  No old backup files to clean up")

def main():
    """Main backup function."""
    print("🔄 Starting database backup process...")
    
    # Determine database path
    db_path = 'badminton_scheduler.db'
    if not os.path.exists(db_path):
        # Try instance directory
        instance_db_path = os.path.join('instance', 'badminton_scheduler.db')
        if os.path.exists(instance_db_path):
            db_path = instance_db_path
        else:
            print("❌ No database file found")
            return
    
    print(f"📁 Database path: {db_path}")
    
    # Create backup
    backup_path = backup_sqlite_database(db_path)
    
    # Export to JSON
    export_path = export_data_to_json(db_path)
    
    # Cleanup old backups
    cleanup_old_backups()
    
    if backup_path and export_path:
        print("\n🎉 Backup process completed successfully!")
        print(f"   Database backup: {backup_path}")
        print(f"   JSON export: {export_path}")
    else:
        print("\n❌ Backup process completed with errors")

if __name__ == "__main__":
    main()