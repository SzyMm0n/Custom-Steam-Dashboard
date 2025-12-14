"""
Unit tests for AuthenticatedAPIClient.

Tests JWT authentication, token management, and request signing.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
import httpx
import time


@pytest.mark.unit
@pytest.mark.app
class TestAuthenticatedAPIClientInitialization:
    """Test API client initialization."""

    def test_init_with_default_base_url(self):
        """Test initialization with default base URL from config."""
        with patch('app.helpers.api_client.get_server_url', return_value="https://api.example.com"):
            from app.helpers.api_client import AuthenticatedAPIClient

            client = AuthenticatedAPIClient()

            assert client.base_url == "https://api.example.com"
            assert client._access_token is None

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://custom.com")

        assert client.base_url == "https://custom.com"

    def test_init_strips_trailing_slash(self):
        """Test initialization strips trailing slash from base URL."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://api.com/")

        assert client.base_url == "https://api.com"


@pytest.mark.unit
@pytest.mark.app
class TestLogin:
    """Test login functionality."""

    @pytest.mark.asyncio
    async def test_login_success_stores_token(self):
        """Test successful login stores access token."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://api.com")

        # Mock httpx.AsyncClient
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_abc123",
            "expires_in": 1200
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Mock signing
            with patch('app.helpers.api_client.sign_request', return_value={"X-Signature": "sig"}):
                with patch('app.helpers.api_client.get_client_credentials', return_value=("client", "secret")):
                    result = await client.login()

        assert result is True
        assert client._access_token == "test_token_abc123"
        assert client._token_expires_at is not None

    @pytest.mark.asyncio
    async def test_login_failure_returns_false(self):
        """Test login failure returns False."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://api.com")

        # Mock HTTP error
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Forbidden", request=Mock(), response=Mock(status_code=403, text="Invalid")
            ))
            mock_client_class.return_value = mock_client

            with patch('app.helpers.api_client.sign_request', return_value={}):
                with patch('app.helpers.api_client.get_client_credentials', return_value=("c", "s")):
                    result = await client.login()

        assert result is False
        assert client._access_token is None

    @pytest.mark.asyncio
    async def test_login_timeout_returns_false(self):
        """Test login timeout returns False."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://api.com")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value = mock_client

            with patch('app.helpers.api_client.sign_request', return_value={}):
                with patch('app.helpers.api_client.get_client_credentials', return_value=("c", "s")):
                    result = await client.login()

        assert result is False


@pytest.mark.unit
@pytest.mark.app
class TestTokenManagement:
    """Test token management and refresh."""

    def test_token_expiry_calculation(self):
        """Test token expiry time is calculated with buffer."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient()
        client._access_token = "token"

        current_time = int(time.time())
        client._token_expires_at = current_time + 1200

        # Token should expire in future
        assert client._token_expires_at > current_time

    def test_token_cleared_on_init(self):
        """Test token is None on initialization."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient()

        assert client._access_token is None
        assert client._token_expires_at is None


@pytest.mark.unit
@pytest.mark.app
class TestEdgeCases:
    """Test edge cases in API client."""

    @pytest.mark.asyncio
    async def test_login_with_empty_response(self):
        """Test login handles empty JSON response."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient()

        mock_response = Mock()
        mock_response.json.side_effect = Exception("Empty response")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with patch('app.helpers.api_client.sign_request', return_value={}):
                with patch('app.helpers.api_client.get_client_credentials', return_value=("c", "s")):
                    result = await client.login()

        assert result is False

    def test_base_url_with_path(self):
        """Test initialization with base URL containing path."""
        from app.helpers.api_client import AuthenticatedAPIClient

        client = AuthenticatedAPIClient(base_url="https://api.com/v1")

        assert client.base_url == "https://api.com/v1"

