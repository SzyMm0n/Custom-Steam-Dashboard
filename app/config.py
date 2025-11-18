"""
Configuration module for Custom Steam Dashboard client application.

This module reads configuration from environment variables at import time.
The values are then baked into the executable during PyInstaller build.

SAFE TO COMMIT TO REPOSITORY - No secrets are stored here!

HOW IT WORKS:
1. During development: This file reads from .env using python-dotenv
2. During build: generate_config.py replaces this file with hardcoded values
3. After build: restore_config.py restores this file
4. In executable: The hardcoded values are used (no .env needed!)

Usage for building:
    1. Set values in .env file
    2. Run: ./build_executable.sh
    3. Script automatically generates hardcoded config, builds, then restores this file
"""

import os
import sys

# Try to load .env file if python-dotenv is available (for development)
try:
    from dotenv import load_dotenv
    # Only load .env in development (not in frozen executable)
    if not getattr(sys, 'frozen', False):
        load_dotenv()
except ImportError:
    # dotenv not available, that's fine - we'll use environment variables
    pass


# ===== Server Configuration =====
# IMPORTANT: These values are read from environment variables.
# During build, generate_config.py will replace this entire file with hardcoded values.

_SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
_CLIENT_ID = os.getenv("CLIENT_ID", "desktop-main")
_CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")

# Validate configuration
if not _CLIENT_SECRET and not getattr(sys, 'frozen', False):
    import warnings
    warnings.warn(
        "CLIENT_SECRET not set! Please set environment variables.\n"
        "Example: export CLIENT_SECRET='your-secret-here'",
        RuntimeWarning
    )


def get_server_url() -> str:
    """
    Get the server URL.
    
    In development: Returns value from environment/.env
    In executable: Returns hardcoded value embedded during build

    Returns:
        Server URL string
    """
    return _SERVER_URL


def get_client_id() -> str:
    """
    Get the client ID.
    
    In development: Returns value from environment/.env
    In executable: Returns hardcoded value embedded during build

    Returns:
        Client ID string
    """
    return _CLIENT_ID


def get_client_secret() -> str:
    """
    Get the client secret.
    
    In development: Returns value from environment/.env
    In executable: Returns hardcoded value embedded during build

    Returns:
        Client secret string
    """
    return _CLIENT_SECRET


# Debug output (only in development)
if not getattr(sys, 'frozen', False) and os.getenv('DEBUG_CONFIG'):
    print(f"[CONFIG] Server URL: {_SERVER_URL}")
    print(f"[CONFIG] Client ID: {_CLIENT_ID}")
    print(f"[CONFIG] Client Secret: {'*' * 10 if _CLIENT_SECRET else 'NOT SET'}")

