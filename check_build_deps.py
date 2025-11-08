#!/usr/bin/env python3
"""
Pre-build test script for Custom Steam Dashboard
Verifies that all required dependencies are available before building.
"""

import sys
import importlib
from typing import List, Tuple

def check_module(module_name: str, display_name: str = None) -> Tuple[bool, str]:
    """Check if a module can be imported."""
    display = display_name or module_name
    try:
        importlib.import_module(module_name)
        return True, f"✓ {display}"
    except ImportError as e:
        return False, f"✗ {display}: {str(e)}"

def main():
    """Run pre-build checks."""
    print("=" * 50)
    print("Custom Steam Dashboard - Pre-Build Check")
    print("=" * 50)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 10):
        print("✗ Python 3.10 or higher required!")
        return False
    print("✓ Python version OK")
    print()
    
    # Required modules for the desktop app
    required_modules = [
        ("PySide6.QtWidgets", "PySide6 (Qt)"),
        ("PySide6.QtCore", "PySide6.QtCore"),
        ("PySide6.QtGui", "PySide6.QtGui"),
        ("qasync", "qasync"),
        ("httpx", "httpx"),
        ("tenacity", "tenacity"),
        ("pydantic", "pydantic"),
        ("rapidfuzz", "rapidfuzz"),
        ("dotenv", "python-dotenv"),
        ("platformdirs", "platformdirs"),
        ("loguru", "loguru"),
    ]
    
    # Optional module for building
    build_modules = [
        ("PyInstaller", "PyInstaller"),
    ]
    
    print("Checking required dependencies:")
    print("-" * 50)
    
    all_ok = True
    for module, display in required_modules:
        ok, msg = check_module(module, display)
        print(msg)
        if not ok:
            all_ok = False
    
    print()
    print("Checking build tools:")
    print("-" * 50)
    
    build_ok = True
    for module, display in build_modules:
        ok, msg = check_module(module, display)
        print(msg)
        if not ok:
            build_ok = False
            print(f"  → Install with: pip install {module.lower()}")
    
    print()
    print("=" * 50)
    
    if not all_ok:
        print("✗ Some required dependencies are missing!")
        print("  Run: pip install -r requirements.txt")
        return False
    
    if not build_ok:
        print("⚠ Build tools not installed (PyInstaller)")
        print("  This is optional for running the app, but required for building")
        print("  Run: pip install pyinstaller>=6.9")
        print()
    
    print("✓ All required dependencies are available!")
    
    if all_ok and build_ok:
        print("✓ Ready to build executable!")
        print()
        print("Next steps:")
        print("  - Run: ./build_executable.sh (Linux/macOS)")
        print("  - Run: build_executable.bat (Windows)")
        return True
    elif all_ok:
        print("✓ Ready to run the application!")
        print()
        print("To run the app:")
        print("  python -m app.main_server")
        return True
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

