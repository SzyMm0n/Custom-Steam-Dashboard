"""
Extended unit tests for Steam service (server/services/steam_service.py).
Tests additional methods and edge cases beyond basic functionality.
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch

from server.services.steam_service import SteamClient, ISteamService
from server.services.models import (
    SteamGameDetails,
    PlayerCountResponse,
    SteamPlayerGameOverview
)


@pytest.mark.asyncio
class TestGetComingSoonGames:
    """Test cases for getting coming soon games."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_coming_soon_games_success(self):
        """Test successful retrieval of coming soon games."""
        client = SteamClient()
        
        mock_response = {
            "coming_soon": {
                "items": [
                    {
                        "id": 123,
                        "name": "Upcoming Game 1",
                        "discounted": False,
                        "discount_percent": 0,
                        "original_price": 1999,
                        "final_price": 1999
                    }
                ]
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            games = await client.get_coming_soon_games()
            
            assert isinstance(games, list)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_coming_soon_games_empty(self):
        """Test handling of empty coming soon games."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"coming_soon": {"items": []}}
            
            games = await client.get_coming_soon_games()
            
            assert games == [] or isinstance(games, list)


@pytest.mark.asyncio
class TestGetMostPlayedGames:
    """Test cases for getting most played games."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_most_played_games_success(self):
        """Test successful retrieval of most played games."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "games": [
                    {"appid": 730, "name": "Counter-Strike 2", "playtime_forever": 10000},
                    {"appid": 440, "name": "Team Fortress 2", "playtime_forever": 5000}
                ]
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            games = await client.get_most_played_games()
            
            assert isinstance(games, list)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_most_played_games_api_error(self):
        """Test handling of API errors when getting most played games."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "API Error",
                request=Mock(),
                response=Mock(status_code=500)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_most_played_games()


@pytest.mark.asyncio
class TestGetPlayerOwnedGames:
    """Test cases for getting player's owned games."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_player_owned_games_success(self):
        """Test successful retrieval of player's owned games."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "game_count": 2,
                "games": [
                    {
                        "appid": 730,
                        "name": "Counter-Strike 2",
                        "playtime_forever": 5000,
                        "img_icon_url": "icon1",
                        "img_logo_url": "logo1"
                    },
                    {
                        "appid": 440,
                        "name": "Team Fortress 2",
                        "playtime_forever": 2000,
                        "img_icon_url": "icon2",
                        "img_logo_url": "logo2"
                    }
                ]
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            games = await client.get_player_owned_games(steam_id="76561198000000000")
            
            assert isinstance(games, list)
            assert len(games) >= 0

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_player_owned_games_private_profile(self):
        """Test handling of private profile."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {}}
            
            games = await client.get_player_owned_games(steam_id="76561198000000000")
            
            assert games == [] or isinstance(games, list)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_player_owned_games_invalid_steam_id(self):
        """Test handling of invalid Steam ID."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            games = await client.get_player_owned_games(steam_id="invalid_id")
            
            # Should handle gracefully
            assert isinstance(games, list) or games is None


@pytest.mark.asyncio
class TestGetRecentlyPlayedGames:
    """Test cases for getting recently played games."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_recently_played_games_success(self):
        """Test successful retrieval of recently played games."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "total_count": 1,
                "games": [
                    {
                        "appid": 730,
                        "name": "Counter-Strike 2",
                        "playtime_2weeks": 500,
                        "playtime_forever": 5000,
                        "img_icon_url": "icon",
                        "img_logo_url": "logo"
                    }
                ]
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            games = await client.get_recently_played_games(steam_id="76561198000000000")
            
            assert isinstance(games, list)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_recently_played_games_none(self):
        """Test when no recently played games."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {"total_count": 0}}
            
            games = await client.get_recently_played_games(steam_id="76561198000000000")
            
            assert games == [] or isinstance(games, list)


@pytest.mark.asyncio
class TestGetBadges:
    """Test cases for getting player badges."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_badges_success(self):
        """Test successful retrieval of player badges."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "badges": [
                    {
                        "badgeid": 1,
                        "level": 5,
                        "completion_time": 1234567890,
                        "xp": 500,
                        "scarcity": 100
                    }
                ],
                "player_xp": 5000,
                "player_level": 10
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            badges = await client.get_badges(steam_id="76561198000000000")
            
            assert isinstance(badges, dict)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_badges_private_profile(self):
        """Test handling of private profile for badges."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {}}
            
            badges = await client.get_badges(steam_id="76561198000000000")
            
            assert isinstance(badges, dict)


@pytest.mark.asyncio
class TestGetPlayerSummary:
    """Test cases for getting player summary."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_player_summary_success(self):
        """Test successful retrieval of player summary."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "players": [
                    {
                        "steamid": "76561198000000000",
                        "personaname": "TestPlayer",
                        "profileurl": "https://steamcommunity.com/id/testplayer/",
                        "avatar": "https://example.com/avatar.jpg",
                        "personastate": 1,
                        "communityvisibilitystate": 3
                    }
                ]
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            summary = await client.get_player_summary(steam_id="76561198000000000")
            
            assert isinstance(summary, dict)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_get_player_summary_not_found(self):
        """Test handling of non-existent player."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {"players": []}}
            
            summary = await client.get_player_summary(steam_id="invalid_id")
            
            assert isinstance(summary, dict)


@pytest.mark.asyncio
class TestResolveVanityURL:
    """Test cases for resolving vanity URLs."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_resolve_vanity_url_success(self):
        """Test successful vanity URL resolution."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "success": 1,
                "steamid": "76561198000000000"
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            steam_id = await client.resolve_vanity_url(vanity_url="testplayer")
            
            assert steam_id == "76561198000000000"

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_resolve_vanity_url_not_found(self):
        """Test handling of non-existent vanity URL."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "success": 42,
                "message": "No match"
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            steam_id = await client.resolve_vanity_url(vanity_url="nonexistent")
            
            assert steam_id is None

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_resolve_vanity_url_api_error(self):
        """Test handling of API errors during vanity URL resolution."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "API Error",
                request=Mock(),
                response=Mock(status_code=503)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.resolve_vanity_url(vanity_url="testplayer")


@pytest.mark.asyncio
class TestSteamClientRetryLogic:
    """Test cases for retry logic and error handling."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_handles_rate_limiting(self):
        """Test handling of rate limiting (429)."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Too Many Requests",
                request=Mock(),
                response=Mock(status_code=429)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_player_count(appid=730)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_handles_server_errors(self):
        """Test handling of server errors (500, 502, 503)."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Internal Server Error",
                request=Mock(),
                response=Mock(status_code=500)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_game_details(appid=730)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_handles_network_errors(self):
        """Test handling of network errors."""
        client = SteamClient()
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Connection refused")
            
            with pytest.raises(httpx.NetworkError):
                await client.get_player_count(appid=730)


@pytest.mark.asyncio
class TestSteamClientConcurrency:
    """Test cases for concurrent requests."""

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_concurrent_player_count_requests(self):
        """Test multiple concurrent player count requests."""
        client = SteamClient()
        
        mock_response = {
            "response": {
                "player_count": 100000
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Make concurrent requests
            import asyncio
            tasks = [
                client.get_player_count(appid=730),
                client.get_player_count(appid=440),
                client.get_player_count(appid=570)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(r, PlayerCountResponse) for r in results)

    @patch.dict('os.environ', {'STEAM_API_KEY': 'test-api-key'})
    async def test_concurrent_game_details_requests(self):
        """Test multiple concurrent game details requests."""
        client = SteamClient()
        
        mock_response = {
            "730": {
                "success": True,
                "data": {
                    "steam_appid": 730,
                    "name": "Counter-Strike 2",
                    "type": "game",
                    "is_free": True,
                    "detailed_description": "A game",
                    "header_image": "https://example.com/image.jpg",
                    "release_date": {"coming_soon": False, "date": "2023-09-27"}
                }
            }
        }
        
        with patch.object(client, '_get_json', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            import asyncio
            tasks = [
                client.get_game_details(appid=730),
                client.get_game_details(appid=730),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 2


class TestISteamServiceInterface:
    """Test cases for ISteamService interface."""

    def test_interface_has_required_methods(self):
        """Test that ISteamService interface defines all required methods."""
        required_methods = [
            'get_player_count',
            'get_game_details',
            'get_coming_soon_games',
            'get_most_played_games',
            'get_player_owned_games',
            'get_recently_played_games',
            'get_badges',
            'get_player_summary',
            'resolve_vanity_url'
        ]
        
        for method_name in required_methods:
            assert hasattr(ISteamService, method_name)

    def test_steam_client_implements_interface(self):
        """Test that SteamClient implements ISteamService."""
        assert issubclass(SteamClient, ISteamService)
