"""
Unit tests for DealsClient with mocked HTTP responses.
Tests client logic in isolation using respx to mock all HTTP communication.
"""
import pytest
import httpx
import respx

from app.core.services.deals_client import DealsClient


@pytest.mark.unit
@pytest.mark.app
class TestDealsClientMocked:
    """Test DealsClient logic with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_get_best_deals_response_parsing(self):
        """Test client correctly parses best deals response."""
        with respx.mock:
            # Mock deals endpoint
            deals_route = respx.get("http://localhost:8000/api/deals/best").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "deals": [
                            {
                                "game_title": "Grand Theft Auto V",
                                "steam_appid": 271590,
                                "current_price": 14.99,
                                "regular_price": 29.99,
                                "discount_percent": 50,
                                "currency": "USD",
                                "store_name": "Steam",
                                "store_url": "https://store.steampowered.com/app/271590"
                            },
                            {
                                "game_title": "The Witcher 3",
                                "steam_appid": 292030,
                                "current_price": 9.99,
                                "regular_price": 39.99,
                                "discount_percent": 75,
                                "currency": "USD",
                                "store_name": "GOG",
                                "store_url": "https://www.gog.com/game/the_witcher_3"
                            }
                        ]
                    }
                )
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            assert len(deals) == 2
            assert deals[0]["game_title"] == "Grand Theft Auto V"
            assert deals[0]["discount_percent"] == 50
            assert deals[1]["discount_percent"] == 75
            assert deals_route.called

    @pytest.mark.asyncio
    async def test_get_best_deals_with_query_parameters(self):
        """Test client correctly passes query parameters."""
        with respx.mock:
            # Mock deals endpoint with query parameters
            deals_route = respx.get(
                "http://localhost:8000/api/deals/best",
                params={"limit": 10, "min_discount": 30}
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "deals": [
                            {
                                "game_title": "Test Game",
                                "steam_appid": 12345,
                                "current_price": 19.99,
                                "regular_price": 49.99,
                                "discount_percent": 60,
                                "currency": "USD",
                                "store_name": "Steam",
                                "store_url": "https://example.com"
                            }
                        ]
                    }
                )
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals(limit=10, min_discount=30)

            assert len(deals) == 1
            assert deals[0]["discount_percent"] >= 30
            assert deals_route.called

    @pytest.mark.asyncio
    async def test_get_best_deals_empty_list_handling(self):
        """Test client handles empty deals list correctly."""
        with respx.mock:
            # Mock empty response
            respx.get("http://localhost:8000/api/deals/best").mock(
                return_value=httpx.Response(200, json={"deals": []})
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            assert len(deals) == 0
            assert isinstance(deals, list)

    @pytest.mark.asyncio
    async def test_get_game_deal_response_parsing(self):
        """Test client correctly parses single game deal response."""
        with respx.mock:
            # Mock game deal endpoint
            deal_route = respx.get("http://localhost:8000/api/deals/game/730").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "game_title": "Counter-Strike 2",
                        "steam_appid": 730,
                        "current_price": 0.0,
                        "regular_price": 0.0,
                        "discount_percent": 0,
                        "currency": "USD",
                        "store_name": "Steam",
                        "store_url": "https://store.steampowered.com/app/730"
                    }
                )
            )

            client = DealsClient(base_url="http://localhost:8000")
            deal = await client.get_game_deal(730)

            assert deal is not None
            assert deal["steam_appid"] == 730
            assert deal["game_title"] == "Counter-Strike 2"
            assert deal_route.called

    @pytest.mark.asyncio
    async def test_get_game_deal_404_handling(self):
        """Test client handles 404 not found responses correctly."""
        with respx.mock:
            # Mock 404 response
            respx.get("http://localhost:8000/api/deals/game/999999").mock(
                return_value=httpx.Response(404, json={"detail": "Game not found"})
            )

            client = DealsClient(base_url="http://localhost:8000")
            deal = await client.get_game_deal(999999)

            assert deal is None

    @pytest.mark.asyncio
    async def test_network_error_returns_empty_list(self):
        """Test client returns empty list on network errors."""
        with respx.mock:
            # Mock network error
            respx.get("http://localhost:8000/api/deals/best").mock(
                side_effect=httpx.NetworkError("Connection failed")
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            # Should return empty list on error
            assert deals == []

    @pytest.mark.asyncio
    async def test_timeout_error_returns_empty_list(self):
        """Test client returns empty list on timeout errors."""
        with respx.mock:
            # Mock timeout error
            respx.get("http://localhost:8000/api/deals/best").mock(
                side_effect=httpx.TimeoutException("Request timed out")
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            # Should return empty list on timeout
            assert deals == []

    @pytest.mark.asyncio
    async def test_server_error_500_returns_empty_list(self):
        """Test client returns empty list on server errors."""
        with respx.mock:
            # Mock server error
            respx.get("http://localhost:8000/api/deals/best").mock(
                return_value=httpx.Response(500, json={"detail": "Internal server error"})
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            # Should return empty list on error
            assert deals == []

    @pytest.mark.asyncio
    async def test_invalid_json_parsing_returns_empty_list(self):
        """Test client returns empty list when response JSON is invalid."""
        with respx.mock:
            # Mock response with invalid JSON
            respx.get("http://localhost:8000/api/deals/best").mock(
                return_value=httpx.Response(200, text="Not valid JSON")
            )

            client = DealsClient(base_url="http://localhost:8000")
            deals = await client.get_best_deals()

            # Should return empty list on parse error
            assert deals == []

