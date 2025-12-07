"""
Configuration file for pytest.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up test environment variables
os.environ.setdefault("STEAM_API_KEY", "test_api_key_12345")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_key")
os.environ.setdefault("JWT_TTL_SECONDS", "1200")
os.environ.setdefault("CLIENTS_JSON", '{"test-client": "test-secret"}')
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("SERVER_HOST", "127.0.0.1")
os.environ.setdefault("SERVER_PORT", "8000")

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
