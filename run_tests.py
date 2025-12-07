#!/usr/bin/env python
"""
Script to run tests for Custom Steam Dashboard.
Usage: python run_tests.py [options]
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*60}")
    print(f"?? {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"? Error: {e}")
        return False


def main():
    """Main function to run tests."""
    project_root = Path(__file__).parent
    
    print("""
    ??????????????????????????????????????????????????????????????
    ?     Custom Steam Dashboard - Test Runner                  ?
    ??????????????????????????????????????????????????????????????
    """)
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"? pytest version: {pytest.__version__}")
    except ImportError:
        print("? pytest not installed!")
        print("Install with: pip install -r requirements-test.txt")
        return 1
    
    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Default: run all tests with coverage
    if not args:
        commands = [
            ("pytest tests/ -v --tb=short", "Running all tests"),
            ("pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing", 
             "Running tests with coverage"),
        ]
    elif "quick" in args:
        commands = [
            ("pytest tests/ -v --tb=short -x", "Running tests (stop on first failure)"),
        ]
    elif "unit" in args:
        commands = [
            ("pytest tests/ -v -m unit", "Running unit tests only"),
        ]
    elif "integration" in args:
        commands = [
            ("pytest tests/ -v -m integration", "Running integration tests only"),
        ]
    elif "coverage" in args:
        commands = [
            ("pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing", 
             "Running tests with coverage report"),
        ]
    else:
        # Custom pytest arguments
        commands = [
            (f"pytest {' '.join(args)}", "Running pytest with custom arguments"),
        ]
    
    # Run commands
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    # Print summary
    print(f"\n{'='*60}")
    if all_passed:
        print("? All tests passed!")
        print(f"{'='*60}\n")
        return 0
    else:
        print("? Some tests failed!")
        print(f"{'='*60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
