"""
Unit tests for server models.
"""
import pytest
from pydantic import ValidationError
from server.services.models import (
    SteamGameDetails,
    PlayerCountResponse,
    SteamPlayerGameOverview,
    SteamPlayerDetails,
    DealInfo,
    GamePrice
)


class TestSteamGameDetails:
    """Test cases for SteamGameDetails model."""

    def test_valid_game_details(self):
        """Test creating valid game details."""
        game_data = {
            "appid": 730,
            "name": "Counter-Strike 2",
            "is_free": True,
            "price": 0.0,
            "detailed_description": "A tactical FPS game",
            "header_image": "https://example.com/header.jpg",
            "background_image": "https://example.com/bg.jpg",
            "coming_soon": False,
            "release_date": "2023-09-27",
            "categories": ["Multi-player", "PvP"],
            "genres": ["Action", "FPS"]
        }
        
        game = SteamGameDetails(**game_data)
        assert game.appid == 730
        assert game.name == "Counter-Strike 2"
        assert game.is_free is True
        assert game.price == 0.0

    def test_game_details_with_none_release_date(self):
        """Test game details with None release date."""
        game_data = {
            "appid": 123,
            "name": "Test Game",
            "is_free": False,
            "price": 19.99,
            "detailed_description": "Test description",
            "header_image": "https://example.com/header.jpg",
            "background_image": "https://example.com/bg.jpg",
            "coming_soon": True,
            "release_date": None,
            "categories": [],
            "genres": []
        }
        
        game = SteamGameDetails(**game_data)
        assert game.release_date is None
        assert game.coming_soon is True

    def test_game_details_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        game_data = {
            "appid": 730,
            "name": "Counter-Strike 2",
            "is_free": True,
            "price": 0.0,
            "detailed_description": "A tactical FPS game",
            "header_image": "https://example.com/header.jpg",
            "background_image": "https://example.com/bg.jpg",
            "coming_soon": False,
            "release_date": "2023-09-27",
            "categories": ["Multi-player"],
            "genres": ["Action"],
            "extra_field": "should be ignored"
        }
        
        game = SteamGameDetails(**game_data)
        assert not hasattr(game, "extra_field")


class TestPlayerCountResponse:
    """Test cases for PlayerCountResponse model."""

    def test_valid_player_count(self):
        """Test creating valid player count response."""
        data = {"appid": 730, "player_count": 1000000}
        response = PlayerCountResponse(**data)
        
        assert response.appid == 730
        assert response.player_count == 1000000

    def test_zero_player_count(self):
        """Test player count with zero players."""
        data = {"appid": 123, "player_count": 0}
        response = PlayerCountResponse(**data)
        
        assert response.player_count == 0


class TestSteamPlayerGameOverview:
    """Test cases for SteamPlayerGameOverview model."""

    def test_valid_player_game_overview(self):
        """Test creating valid player game overview."""
        data = {
            "appid": 730,
            "name": "Counter-Strike 2",
            "playtime_forever": 5000,
            "playtime_2weeks": 120,
            "img_icon_url": "https://example.com/icon.jpg"
        }
        
        overview = SteamPlayerGameOverview(**data)
        assert overview.appid == 730
        assert overview.name == "Counter-Strike 2"
        assert overview.playtime_forever == 5000
        assert overview.playtime_2weeks == 120

    def test_player_game_zero_playtime(self):
        """Test player game with zero playtime."""
        data = {
            "appid": 456,
            "name": "New Game",
            "playtime_forever": 0,
            "playtime_2weeks": 0,
            "img_icon_url": "https://example.com/icon.jpg"
        }
        
        overview = SteamPlayerGameOverview(**data)
        assert overview.playtime_forever == 0
        assert overview.playtime_2weeks == 0


class TestSteamPlayerDetails:
    """Test cases for SteamPlayerDetails model."""

    def test_valid_player_details(self):
        """Test creating valid player details."""
        data = {
            "steamid": "76561198012345678",
            "personaname": "TestPlayer",
            "profileurl": "https://steamcommunity.com/id/testplayer",
            "avatar": "https://example.com/avatar.jpg",
            "avatarfull": "https://example.com/avatar_full.jpg"
        }
        
        player = SteamPlayerDetails(**data)
        assert player.steamid == "76561198012345678"
        assert player.personaname == "TestPlayer"


class TestDealInfo:
    """Test cases for DealInfo model."""

    def test_valid_deal_info(self):
        """Test creating valid deal info."""
        data = {
            "steam_appid": 730,
            "game_title": "Counter-Strike 2",
            "store_name": "Steam",
            "store_url": "https://store.steampowered.com/app/730",
            "current_price": 0.0,
            "regular_price": 0.0,
            "discount_percent": 0,
            "currency": "USD",
            "drm": "Steam"
        }
        
        deal = DealInfo(**data)
        assert deal.steam_appid == 730
        assert deal.game_title == "Counter-Strike 2"
        assert deal.discount_percent == 0

    def test_deal_info_with_discount(self):
        """Test deal info with discount."""
        data = {
            "steam_appid": 123,
            "game_title": "Test Game",
            "store_name": "Epic Games Store",
            "store_url": "https://example.com/game",
            "current_price": 19.99,
            "regular_price": 39.99,
            "discount_percent": 50,
            "currency": "USD",
            "drm": "Epic"
        }
        
        deal = DealInfo(**data)
        assert deal.current_price == 19.99
        assert deal.regular_price == 39.99
        assert deal.discount_percent == 50

    def test_deal_info_without_appid(self):
        """Test deal info without Steam App ID."""
        data = {
            "steam_appid": None,
            "game_title": "Non-Steam Game",
            "store_name": "GOG",
            "store_url": "https://gog.com/game",
            "current_price": 9.99,
            "regular_price": 19.99,
            "discount_percent": 50,
            "currency": "USD",
            "drm": "DRM-Free"
        }
        
        deal = DealInfo(**data)
        assert deal.steam_appid is None
        assert deal.drm == "DRM-Free"


class TestGamePrice:
    """Test cases for GamePrice model."""

    def test_valid_game_price(self):
        """Test creating valid game price."""
        data = {
            "steam_appid": 730,
            "game_title": "Counter-Strike 2",
            "store_name": "Steam",
            "store_url": "https://store.steampowered.com/app/730",
            "current_price": 0.0,
            "regular_price": 0.0,
            "discount_percent": 0,
            "currency": "USD",
            "drm": "Steam"
        }
        
        price = GamePrice(**data)
        assert price.steam_appid == 730
        assert price.game_title == "Counter-Strike 2"

    def test_game_price_different_currency(self):
        """Test game price with different currency."""
        data = {
            "steam_appid": 456,
            "game_title": "Test Game",
            "store_name": "Steam",
            "store_url": "https://store.steampowered.com/app/456",
            "current_price": 79.99,
            "regular_price": 99.99,
            "discount_percent": 20,
            "currency": "PLN",
            "drm": "Steam"
        }
        
        price = GamePrice(**data)
        assert price.currency == "PLN"
        assert price.current_price == 79.99
