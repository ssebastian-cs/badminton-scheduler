#!/usr/bin/env python3
"""
Focused integration test runner for the badminton scheduler application.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run focused integration test suites."""
    print("Badminton Scheduler - Focused Integration Test Suite")
    print("=" * 60)
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    integration_test_suites = [
        ("python -m pytest tests/integration/test_auth_integration.py -v", "Integration Tests - Authentication"),
        ("python -m pytest tests/integration/test_crud_integration.py -v", "Integration Tests - CRUD Operations"),
    ]
    
    results = []
    
    for command, description in integration_test_suites:
        success = run_command(command, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print('='*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for description, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{description:<50} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} integration test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All integration test suites passed!")
        return 0
    else:
        print("⚠️  Some integration test suites failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())