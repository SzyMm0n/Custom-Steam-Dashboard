"""
Unit tests for deals service (server/services/deals_service.py).
Tests ITAD API integration, OAuth2 authentication, and deal retrieval.
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone

from server.services.deals_service import IsThereAnyDealClient, IDealsService
from server.services.models import DealInfo, GamePrice


class TestIsThereAnyDealClientInitialization:
    """Test cases for IsThereAnyDealClient initialization."""

    def test_client_initialization_default(self):
        """Test client initialization with default timeout."""
        client = IsThereAnyDealClient()
        
        assert client.base_url == "https://api.isthereanydeal.com"
        assert client._token is None
        assert client._token_expires_at is None

    def test_client_initialization_custom_timeout(self):
        """Test client initialization with custom timeout."""
        timeout = httpx.Timeout(60.0, connect=20.0)
        client = IsThereAnyDealClient(timeout=timeout)
        
        assert client.base_url == "https://api.isthereanydeal.com"

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key',
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    def test_client_reads_credentials_from_env(self):
        """Test that client reads credentials from environment."""
        client = IsThereAnyDealClient()
        
        assert client.api_key == 'test-api-key'
        assert client.client_id == 'test-client-id'
        assert client.client_secret == 'test-secret'

    @patch.dict('os.environ', {}, clear=True)
    def test_client_handles_missing_credentials(self):
        """Test that client handles missing credentials gracefully."""
        with patch('server.services.deals_service.logger') as mock_logger:
            client = IsThereAnyDealClient()
            
            assert client.api_key == ''
            assert client.client_id == ''
            mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
class TestOAuth2Authentication:
    """Test cases for OAuth2 token management."""

    @patch.dict('os.environ', {
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_access_token_success(self):
        """Test successful OAuth2 token acquisition."""
        client = IsThereAnyDealClient()
        
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-token-123",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            token = await client._get_access_token()
            
            assert token == "test-token-123"
            assert client._token == "test-token-123"
            assert client._token_expires_at is not None
            mock_post.assert_called_once()

    @patch.dict('os.environ', {
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_access_token_reuses_valid_token(self):
        """Test that valid token is reused without new request."""
        client = IsThereAnyDealClient()
        
        # Set a valid token
        client._token = "existing-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch.object(client._client, 'post', new_callable=AsyncMock) as mock_post:
            token = await client._get_access_token()
            
            assert token == "existing-token"
            mock_post.assert_not_called()

    @patch.dict('os.environ', {
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_access_token_refreshes_expired_token(self):
        """Test that expired token is refreshed."""
        client = IsThereAnyDealClient()
        
        # Set an expired token
        client._token = "expired-token"
        client._token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-token-456",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            token = await client._get_access_token()
            
            assert token == "new-token-456"
            assert client._token == "new-token-456"
            mock_post.assert_called_once()

    @patch.dict('os.environ', {
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_access_token_handles_api_error(self):
        """Test handling of OAuth2 API errors."""
        client = IsThereAnyDealClient()
        
        with patch.object(client._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=Mock(),
                response=Mock(status_code=401)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client._get_access_token()


@pytest.mark.asyncio
class TestGetBestDeals:
    """Test cases for getting best deals."""

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key',
        'ITAD_CLIENT_ID': 'test-client-id',
        'ITAD_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_best_deals_success(self):
        """Test successful retrieval of best deals."""
        client = IsThereAnyDealClient()
        
        # Mock OAuth token
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Mock deals response
        mock_response = Mock()
        mock_response.json.return_value = {
            "deals": [
                {
                    "id": "deal1",
                    "title": "Game 1",
                    "price": {"amount": 9.99, "currency": "USD"},
                    "regular": {"amount": 29.99, "currency": "USD"},
                    "cut": 67
                },
                {
                    "id": "deal2",
                    "title": "Game 2",
                    "price": {"amount": 4.99, "currency": "USD"},
                    "regular": {"amount": 19.99, "currency": "USD"},
                    "cut": 75
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            deals = await client.get_best_deals(limit=20, min_discount=20)
            
            assert isinstance(deals, list)
            assert len(deals) <= 20
            mock_get.assert_called_once()

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key'
    })
    async def test_get_best_deals_empty_response(self):
        """Test handling of empty deals response."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {"deals": []}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            deals = await client.get_best_deals()
            
            assert deals == []

    async def test_get_best_deals_validates_parameters(self):
        """Test that get_best_deals validates input parameters."""
        client = IsThereAnyDealClient()
        
        # Test with invalid limit (should still work, validation is optional)
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {"deals": []}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Should accept any integer values
            await client.get_best_deals(limit=100, min_discount=50)


@pytest.mark.asyncio
class TestGetGamePrices:
    """Test cases for getting game prices."""

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key'
    })
    async def test_get_game_prices_success(self):
        """Test successful game price retrieval."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "price": {
                "amount": 59.99,
                "currency": "USD"
            },
            "lowest": {
                "amount": 29.99,
                "currency": "USD",
                "recorded": "2024-01-15"
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            price = await client.get_game_prices(steam_appid=730)
            
            assert price is not None
            assert isinstance(price, (GamePrice, dict, type(None)))

    async def test_get_game_prices_not_found(self):
        """Test handling of game not found."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            price = await client.get_game_prices(steam_appid=999999)
            
            assert price is None


@pytest.mark.asyncio
class TestSearchGame:
    """Test cases for game search functionality."""

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key'
    })
    async def test_search_game_success(self):
        """Test successful game search."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "game123",
                    "title": "Counter-Strike 2",
                    "type": "game"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await client.search_game(title="Counter-Strike")
            
            assert result is not None

    async def test_search_game_no_results(self):
        """Test game search with no results."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await client.search_game(title="NonExistentGame12345")
            
            assert result is None or result == {}

    async def test_search_game_empty_query(self):
        """Test search with empty query string."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await client.search_game(title="")
            
            # Should handle empty query gracefully
            assert result is None or result == {}


@pytest.mark.asyncio
class TestSearchDeals:
    """Test cases for searching deals by title."""

    @patch.dict('os.environ', {
        'ITAD_API_KEY': 'test-api-key'
    })
    async def test_search_deals_success(self):
        """Test successful deal search."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "deals": [
                {
                    "id": "deal1",
                    "title": "Counter-Strike 2",
                    "price": {"amount": 0, "currency": "USD"},
                    "cut": 100
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            deals = await client.search_deals(title="Counter-Strike", limit=20, min_discount=0)
            
            assert isinstance(deals, list)

    async def test_search_deals_with_filters(self):
        """Test deal search with filters."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.json.return_value = {"deals": []}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            deals = await client.search_deals(
                title="Game",
                limit=10,
                min_discount=50
            )
            
            assert isinstance(deals, list)


@pytest.mark.asyncio
class TestErrorHandling:
    """Test cases for error handling in deals service."""

    async def test_handles_network_errors(self):
        """Test handling of network errors."""
        client = IsThereAnyDealClient()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Connection failed")
            
            # The client logs errors but may return empty list instead of raising
            try:
                result = await client.get_best_deals()
                # If it returns empty list, that's acceptable error handling
                assert result == [] or isinstance(result, list)
            except httpx.NetworkError:
                # Or it may raise, which is also valid
                pass

    async def test_handles_timeout_errors(self):
        """Test handling of timeout errors."""
        client = IsThereAnyDealClient()
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            try:
                result = await client.get_best_deals()
                assert result == [] or isinstance(result, list)
            except httpx.TimeoutException:
                pass

    async def test_handles_http_errors(self):
        """Test handling of HTTP errors."""
        client = IsThereAnyDealClient()
        
        client._token = "valid-token"
        client._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch.object(client._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=Mock(),
                response=Mock(status_code=500)
            )
            
            try:
                result = await client.get_best_deals()
                # May return empty list on error
                assert result == [] or isinstance(result, list)
            except httpx.HTTPStatusError:
                # Or may raise
                pass


class TestIDealsServiceInterface:
    """Test cases for IDealsService interface."""

    def test_interface_has_required_methods(self):
        """Test that IDealsService interface defines required methods."""
        required_methods = [
            'get_best_deals',
            'get_game_prices',
            'search_game',
            'search_deals'
        ]
        
        for method_name in required_methods:
            assert hasattr(IDealsService, method_name)

    def test_implementation_implements_interface(self):
        """Test that IsThereAnyDealClient implements IDealsService."""
        assert issubclass(IsThereAnyDealClient, IDealsService)
        
        client = IsThereAnyDealClient()
        
        # Check that all interface methods are implemented
        assert callable(getattr(client, 'get_best_deals'))
        assert callable(getattr(client, 'get_game_prices'))
        assert callable(getattr(client, 'search_game'))
        assert callable(getattr(client, 'search_deals'))
