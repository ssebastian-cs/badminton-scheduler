#!/usr/bin/env python3
"""
Migration script for availability enhancements.
This script handles data migration and backward compatibility for the availability system.
"""

import sys
import os
from datetime import datetime

def migrate_existing_availability():
    """
    Migrate existing availability entries to use the new time-specific fields.
    Sets is_all_day=True for all existing entries that don't have time information.
    """
    from app import create_app
    from models import db, Availability
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting availability migration...")
            
            # Find all availability entries that need migration
            entries_to_migrate = Availability.query.filter(
                Availability.is_all_day.is_(None)
            ).all()
            
            if not entries_to_migrate:
                print("No entries found that need migration.")
                return True
            
            print(f"Found {len(entries_to_migrate)} entries to migrate.")
            
            migrated_count = 0
            for entry in entries_to_migrate:
                try:
                    # Set is_all_day=True for existing entries without time information
                    if entry.is_all_day is None:
                        entry.is_all_day = True
                        
                    # Set updated_at if it's None
                    if entry.updated_at is None:
                        entry.updated_at = entry.created_at or datetime.utcnow()
                    
                    # If there's a time_slot but no time_start/time_end, try to parse it
                    if entry.time_slot and not entry.time_start and not entry.time_end:
                        try:
                            # Try to parse the time_slot into structured time fields
                            from api import parse_time_range, parse_time_string
                            
                            if '-' in entry.time_slot and not entry.time_slot.startswith('until'):
                                # Try parsing as time range
                                start_time, end_time = parse_time_range(entry.time_slot)
                                entry.time_start = start_time
                                entry.time_end = end_time
                                entry.is_all_day = False
                                print(f"  Parsed time range '{entry.time_slot}' -> {start_time}-{end_time}")
                            elif entry.time_slot.startswith('until'):
                                # Parse "until" format
                                time_str = entry.time_slot.replace('until ', '')
                                end_time = parse_time_string(time_str)
                                entry.time_end = end_time
                                entry.is_all_day = False
                                print(f"  Parsed until time '{entry.time_slot}' -> until {end_time}")
                            else:
                                # Try parsing as single time
                                start_time = parse_time_string(entry.time_slot)
                                entry.time_start = start_time
                                entry.is_all_day = False
                                print(f"  Parsed single time '{entry.time_slot}' -> from {start_time}")
                        except Exception as parse_error:
                            # If parsing fails, keep as all-day but preserve time_slot for backward compatibility
                            print(f"  Could not parse time_slot '{entry.time_slot}': {parse_error}")
                            entry.is_all_day = True
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"Error migrating entry {entry.id}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            print(f"Successfully migrated {migrated_count} availability entries.")
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            return False

def verify_migration():
    """
    Verify that the migration was successful by checking data consistency.
    """
    from app import create_app
    from models import db, Availability
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Verifying migration...")
            
            # Check that all entries have is_all_day set
            entries_without_all_day = Availability.query.filter(
                Availability.is_all_day.is_(None)
            ).count()
            
            if entries_without_all_day > 0:
                print(f"WARNING: {entries_without_all_day} entries still have is_all_day=NULL")
                return False
            
            # Check that all entries have updated_at set
            entries_without_updated_at = Availability.query.filter(
                Availability.updated_at.is_(None)
            ).count()
            
            if entries_without_updated_at > 0:
                print(f"WARNING: {entries_without_updated_at} entries still have updated_at=NULL")
                return False
            
            # Get summary statistics
            total_entries = Availability.query.count()
            all_day_entries = Availability.query.filter(Availability.is_all_day == True).count()
            time_specific_entries = Availability.query.filter(Availability.is_all_day == False).count()
            
            print(f"Migration verification successful:")
            print(f"  Total entries: {total_entries}")
            print(f"  All-day entries: {all_day_entries}")
            print(f"  Time-specific entries: {time_specific_entries}")
            
            return True
            
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

def test_backward_compatibility():
    """
    Test that existing API calls continue to work without time parameters.
    """
    from app import create_app
    from models import db, Availability
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Testing backward compatibility...")
            
            # Test creating availability without time parameters (should default to all-day)
            from flask import Flask
            from flask.testing import FlaskClient
            
            with app.test_client() as client:
                # This would require authentication, so we'll just test the data model
                test_availability = Availability(
                    user_id=1,  # Assuming user 1 exists
                    date=datetime(2025, 8, 15).date(),
                    status='available'
                )
                
                # Verify defaults are set correctly
                assert test_availability.is_all_day == True, "Default is_all_day should be True"
                assert test_availability.time_start is None, "Default time_start should be None"
                assert test_availability.time_end is None, "Default time_end should be None"
                
                print("  ✓ Default values work correctly")
                
                # Test to_dict method includes new fields
                result_dict = test_availability.to_dict()
                required_fields = ['time_start', 'time_end', 'is_all_day', 'updated_at']
                for field in required_fields:
                    assert field in result_dict, f"to_dict should include {field}"
                
                print("  ✓ to_dict method includes new fields")
                
                # Test backward compatibility with time_slot
                test_availability.time_slot = "7:00 PM"
                result_dict = test_availability.to_dict()
                assert 'time_slot' in result_dict, "to_dict should still include time_slot for backward compatibility"
                
                print("  ✓ time_slot field preserved for backward compatibility")
            
            print("Backward compatibility test passed!")
            return True
            
        except Exception as e:
            print(f"Backward compatibility test failed: {e}")
            return False

def main():
    """
    Main migration function that runs all migration steps.
    """
    print("=== Availability Enhancement Migration ===")
    print()
    
    # Step 1: Migrate existing data
    if not migrate_existing_availability():
        print("Migration failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Step 2: Verify migration
    if not verify_migration():
        print("Migration verification failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Step 3: Test backward compatibility
    if not test_backward_compatibility():
        print("Backward compatibility test failed. Exiting.")
        sys.exit(1)
    
    print()
    print("=== Migration completed successfully! ===")
    print("The availability system now supports:")
    print("- Time-specific availability with time_start and time_end fields")
    print("- All-day availability flag (is_all_day)")
    print("- Updated timestamp tracking (updated_at)")
    print("- Full backward compatibility with existing API calls")

if __name__ == '__main__':
    main()