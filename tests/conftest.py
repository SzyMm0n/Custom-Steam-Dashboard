"""
Configuration file for pytest.
"""
import os
import sys
from pathlib import Path
import uuid
import asyncio
from typing import Generator, AsyncGenerator
from contextlib import asynccontextmanager

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file for test configuration
from dotenv import load_dotenv
load_dotenv()

# Set up test environment variables (fallbacks if not in .env)
os.environ.setdefault("STEAM_API_KEY", os.getenv("STEAM_API_KEY", "test_api_key_12345"))
os.environ.setdefault("JWT_SECRET", os.getenv("JWT_SECRET", "test_jwt_secret_key"))
os.environ.setdefault("JWT_TTL_SECONDS", os.getenv("JWT_TTL_SECONDS", "1200"))
os.environ.setdefault("CLIENTS_JSON", os.getenv("CLIENTS_JSON", '{"test-client": "test-secret"}'))
os.environ.setdefault("SERVER_HOST", "127.0.0.1")
os.environ.setdefault("SERVER_PORT", "8000")

import pytest
import asyncpg



@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures a single event loop is used throughout the test session,
    preventing conflicts with pytest-qt and async fixtures.
    """
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_test_client():
    """
    Create an async HTTP client for testing FastAPI app.

    Uses httpx.AsyncClient with ASGITransport for proper async support.
    This avoids TestClient issues with async database operations.

    Usage:
        async with async_test_client(app) as client:
            response = await client.get("/api/endpoint")

    Returns:
        Function that creates AsyncClient with given app
    """
    from httpx import ASGITransport, AsyncClient
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _create_client(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver"
        ) as client:
            yield client

    return _create_client


@pytest.fixture(scope="function")
async def test_db_manager():
    """
    Create a test database manager with unique schema.

    This fixture:
    1. Creates a unique test schema: test_custom_steam_dashboard_<uuid>
    2. Creates all necessary tables in that schema
    3. Returns a DatabaseManager instance
    4. Cleans up (drops schema) after test completes

    Note: Scope is explicitly set to 'function' to avoid conflicts
    with pytest-qt plugin when running all tests together.

    Yields:
        DatabaseManager: Initialized database manager with test schema
    """
    from server.database.database import DatabaseManager

    # Generate unique schema name for this test
    test_schema = f"test_custom_steam_dashboard_{uuid.uuid4().hex[:8]}"

    # Get database credentials from environment
    db_manager = DatabaseManager(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", 5432)),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "password"),
        database=os.getenv("PGDATABASE", "postgres"),
        schema=test_schema,
        min_pool_size=2,
        max_pool_size=5
    )

    # Initialize database (creates schema and tables)
    await db_manager.initialize()

    try:
        yield db_manager
    finally:
        # Cleanup: drop test schema
        if db_manager.pool:
            try:
                async with db_manager.pool.acquire() as conn:
                    await conn.execute(f'DROP SCHEMA IF EXISTS "{test_schema}" CASCADE')
            except Exception:
                pass  # Ignore cleanup errors
        await db_manager.close()


@pytest.fixture(scope="function")
async def test_db_connection(test_db_manager):
    """
    Provide a database connection with transaction rollback.

    This fixture provides a connection within a transaction that is
    rolled back after the test, ensuring test isolation.

    Args:
        test_db_manager: The test database manager fixture

    Yields:
        asyncpg.Connection: Database connection within a transaction
    """
    async with test_db_manager.pool.acquire() as conn:
        # Set search path to test schema
        await conn.execute(f'SET search_path TO "{test_db_manager.schema}", public')

        # Start transaction
        async with conn.transaction():
            yield conn
            # Transaction is automatically rolled back after yield


@pytest.fixture
def prepared_json_data():
    """
    Provide prepared test data for file I/O operations.

    Returns dict with common test data structures instead of reading from files.

    Returns:
        dict: Test data for user preferences, themes, etc.
    """
    return {
        'user_data': {
            'version': '1.0',
            'custom_themes': [
                {
                    'name': 'Test Theme',
                    'dark_colors': {
                        'primary': '#1e88e5',
                        'secondary': '#424242',
                        'background': '#121212',
                        'surface': '#1e1e1e',
                        'text': '#ffffff'
                    },
                    'light_colors': {
                        'primary': '#1976d2',
                        'secondary': '#f5f5f5',
                        'background': '#ffffff',
                        'surface': '#f5f5f5',
                        'text': '#000000'
                    }
                }
            ],
            'last_library': {
                'steam_id': '76561198012345678',
                'persona_name': 'TestUser',
                'last_loaded': '2025-12-11T10:00:00'
            },
            'preferences': {
                'theme_mode': 'dark',
                'color_palette': 'green',
                'auto_refresh': True,
                'refresh_interval': 300
            }
        },
        'corrupted_json': '{"invalid": json data',
        'empty_json': '{}',
        'theme_preference': {
            'mode': 'dark',
            'palette': 'blue'
        }
    }


@pytest.fixture
def mock_steam_api(respx_mock):
    """
    Mock Steam API responses for testing.

    Uses respx to mock HTTP requests to Steam API endpoints.

    Args:
        respx_mock: respx fixture for mocking HTTP requests

    Returns:
        respx.MockRouter: Configured mock router for Steam API
    """
    import respx
    import httpx

    # Mock player count endpoint
    respx_mock.get(
        url__regex=r"https://api\.steampowered\.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/.*"
    ).mock(return_value=httpx.Response(200, json={
        "response": {
            "player_count": 50000,
            "result": 1
        }
    }))

    # Mock game details endpoint
    respx_mock.get(
        url__regex=r"https://store\.steampowered\.com/api/appdetails.*"
    ).mock(return_value=httpx.Response(200, json={
        "730": {
            "success": True,
            "data": {
                "type": "game",
                "name": "Counter-Strike 2",
                "steam_appid": 730,
                "is_free": True,
                "short_description": "Test game description",
                "header_image": "https://example.com/image.jpg",
                "categories": [{"description": "Multi-player"}],
                "genres": [{"description": "Action"}],
                "release_date": {"date": "Aug 21, 2012"}
            }
        }
    }))

    return respx_mock


@pytest.fixture
def mock_itad_api(respx_mock):
    """
    Mock IsThereAnyDeal API responses for testing.

    Args:
        respx_mock: respx fixture for mocking HTTP requests

    Returns:
        respx.MockRouter: Configured mock router for ITAD API
    """
    import respx
    import httpx

    # Mock OAuth token endpoint
    respx_mock.post(
        url__regex=r"https://api\.isthereanydeal\.com/oauth/token.*"
    ).mock(return_value=httpx.Response(200, json={
        "access_token": "test_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600
    }))

    # Mock deals endpoint
    respx_mock.get(
        url__regex=r"https://api\.isthereanydeal\.com/deals/v2.*"
    ).mock(return_value=httpx.Response(200, json={
        "list": [
            {
                "id": "deal123",
                "title": "Test Game",
                "price": {"amount": 9.99, "currency": "USD"},
                "regular": {"amount": 29.99, "currency": "USD"},
                "cut": 67,
                "shop": {"name": "Steam"},
                "urls": {"buy": "https://store.steampowered.com/app/730"}
            }
        ]
    }))

    return respx_mock

