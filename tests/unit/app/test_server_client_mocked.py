"""
Unit tests for ServerClient with mocked HTTP responses.
Tests client logic in isolation using respx to mock all HTTP communication.
"""
import pytest
import httpx
import respx

from app.core.services.server_client import ServerClient


@pytest.mark.unit
@pytest.mark.app
class TestServerClientMocked:
    """Test ServerClient logic with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_authenticate_success_with_mocked_response(self):
        """Test successful authentication with mocked login endpoint."""
        with respx.mock:
            # Mock login endpoint
            login_route = respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_jwt_token_12345",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            client = ServerClient(base_url="http://localhost:8000")
            result = await client.authenticate()

            assert result is True
            assert login_route.called

    @pytest.mark.asyncio
    async def test_authenticate_failure_with_invalid_credentials(self):
        """Test authentication failure handling with 401 response."""
        with respx.mock:
            # Mock login endpoint to return 401
            login_route = respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(401, json={"detail": "Invalid signature"})
            )

            client = ServerClient(base_url="http://localhost:8000")
            result = await client.authenticate()

            assert result is False
            assert login_route.called

    @pytest.mark.asyncio
    async def test_get_current_players_parsing_logic(self):
        """Test client correctly parses current players response."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock current-players endpoint
            players_route = respx.get("http://localhost:8000/api/current-players").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "games": [
                            {
                                "appid": 730,
                                "name": "Counter-Strike 2",
                                "last_count": 500000
                            },
                            {
                                "appid": 440,
                                "name": "Team Fortress 2",
                                "last_count": 30000
                            }
                        ]
                    }
                )
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            games = await client.get_current_players()

            # Verify client correctly parsed the response
            assert len(games) == 2
            assert games[0]["appid"] == 730
            assert games[0]["name"] == "Counter-Strike 2"
            assert players_route.called

    @pytest.mark.asyncio
    async def test_get_current_players_empty_list_handling(self):
        """Test client handles empty games list correctly."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock empty response
            respx.get("http://localhost:8000/api/current-players").mock(
                return_value=httpx.Response(200, json={"games": []})
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            games = await client.get_current_players()

            assert len(games) == 0
            assert isinstance(games, list)

    @pytest.mark.asyncio
    async def test_get_all_games_response_parsing(self):
        """Test client correctly parses games list response."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock games endpoint
            games_route = respx.get("http://localhost:8000/api/games").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "games": [
                            {
                                "appid": 730,
                                "name": "Counter-Strike 2",
                                "price": 0.0,
                                "is_free": True
                            }
                        ]
                    }
                )
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            games = await client.get_all_games()

            assert len(games) == 1
            assert games[0]["appid"] == 730
            assert games_route.called

    @pytest.mark.asyncio
    async def test_get_coming_soon_games_response_parsing(self):
        """Test client correctly parses upcoming games response."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock coming-soon endpoint
            coming_soon_route = respx.get("http://localhost:8000/api/coming-soon").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "games": [
                            {
                                "appid": 123456,
                                "name": "Upcoming Game",
                                "release_date": "2025-12-31"
                            }
                        ]
                    }
                )
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            games = await client.get_coming_soon_games()

            assert len(games) == 1
            assert games[0]["name"] == "Upcoming Game"
            assert coming_soon_route.called

    @pytest.mark.asyncio
    async def test_network_error_handling_returns_empty_list(self):
        """Test client gracefully handles network errors."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock network error
            respx.get("http://localhost:8000/api/current-players").mock(
                side_effect=httpx.NetworkError("Connection failed")
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            # Should return empty list on error
            games = await client.get_current_players()

            assert games == []

    @pytest.mark.asyncio
    async def test_server_error_500_handling(self):
        """Test client handles server errors gracefully."""
        with respx.mock:
            # Mock login
            respx.post("http://localhost:8000/auth/login").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token",
                        "token_type": "bearer",
                        "expires_in": 1200
                    }
                )
            )

            # Mock server error
            respx.get("http://localhost:8000/api/current-players").mock(
                return_value=httpx.Response(500, json={"detail": "Internal server error"})
            )

            client = ServerClient(base_url="http://localhost:8000")
            await client.authenticate()

            # Should return empty list on error
            games = await client.get_current_players()

            assert games == []

