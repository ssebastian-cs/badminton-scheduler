#!/usr/bin/env python3
"""
Comprehensive test runner for availability enhancements.
Runs all test suites and provides detailed reporting.

This script runs:
1. Unit tests for validation logic and time parsing
2. Integration tests for edit/delete workflows  
3. Integration tests for admin filtering functionality
4. Comprehensive API endpoint tests
5. Permission checking and error handling tests

Requirements covered:
- 2.6: User ownership validation for edit/delete operations
- 2.7: Past date protection for edit/delete operations
- 3.8: Admin filtering functionality with date ranges
- 5.4: Data integrity and validation
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test_suite(test_file, description):
    """Run a specific test suite and return results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            test_file, 
            '-v',  # Verbose output
            '--tb=short',  # Short traceback format
            '--no-header',  # No pytest header
            '--color=yes'  # Colored output
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Duration: {duration:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("\nSTDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        return {
            'file': test_file,
            'description': description,
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except Exception as e:
        print(f"Error running test suite: {e}")
        return {
            'file': test_file,
            'description': description,
            'success': False,
            'duration': 0,
            'error': str(e)
        }

def check_test_dependencies():
    """Check if required dependencies are available."""
    print("Checking test dependencies...")
    
    try:
        import pytest
        print(f"✓ pytest version: {pytest.__version__}")
    except ImportError:
        print("✗ pytest not found. Install with: pip install pytest")
        return False
    
    try:
        from run import app, db, User, Availability
        print("✓ Application modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import application modules: {e}")
        return False
    
    try:
        from api import parse_time_string, validate_time_logic
        print("✓ API validation functions imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import API functions: {e}")
        return False
    
    return True

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    total_duration = sum(r['duration'] for r in results)
    
    print(f"\nSUMMARY:")
    print(f"  Total test suites: {total_tests}")
    print(f"  Successful: {successful_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Total duration: {total_duration:.2f} seconds")
    print(f"  Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\nDETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"  {i}. {status} - {result['description']} ({result['duration']:.2f}s)")
        if not result['success'] and 'error' in result:
            print(f"     Error: {result['error']}")
    
    if failed_tests > 0:
        print(f"\nFAILED TEST DETAILS:")
        for result in results:
            if not result['success']:
                print(f"\n{'-'*40}")
                print(f"FAILED: {result['description']}")
                print(f"File: {result['file']}")
                if 'stderr' in result and result['stderr']:
                    print("Error output:")
                    print(result['stderr'])
    
    print(f"\n{'='*80}")
    
    return successful_tests == total_tests

def main():
    """Main test runner function."""
    print("Availability Enhancements - Comprehensive Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies first
    if not check_test_dependencies():
        print("\n❌ Dependency check failed. Please install required packages.")
        return 1
    
    # Define test suites to run
    test_suites = [
        {
            'file': 'test_validation_unit.py',
            'description': 'Unit Tests - Validation Logic and Time Parsing'
        },
        {
            'file': 'test_comprehensive_api.py', 
            'description': 'Integration Tests - API Endpoints and Workflows'
        },
        {
            'file': 'test_admin_filtering_integration.py',
            'description': 'Integration Tests - Admin Filtering Functionality'
        }
    ]
    
    # Check if test files exist
    missing_files = []
    for suite in test_suites:
        if not os.path.exists(suite['file']):
            missing_files.append(suite['file'])
    
    if missing_files:
        print(f"\n❌ Missing test files: {', '.join(missing_files)}")
        return 1
    
    # Run all test suites
    results = []
    
    for suite in test_suites:
        result = run_test_suite(suite['file'], suite['description'])
        results.append(result)
    
    # Generate comprehensive report
    all_passed = generate_test_report(results)
    
    if all_passed:
        print("\n🎉 All test suites passed successfully!")
        print("\nRequirements Coverage Verified:")
        print("  ✓ 2.6: User ownership validation for edit/delete operations")
        print("  ✓ 2.7: Past date protection for edit/delete operations")
        print("  ✓ 3.8: Admin filtering functionality with date ranges")
        print("  ✓ 5.4: Data integrity and validation")
        return 0
    else:
        print("\n❌ Some test suites failed. Please review the failures above.")
        return 1

if __name__ == '__main__':
    exit(main())