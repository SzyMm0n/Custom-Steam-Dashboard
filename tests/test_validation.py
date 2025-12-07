"""
Unit tests for server validation module.
"""
import pytest
from pydantic import ValidationError
from server.validation import SteamIDValidator, AppIDValidator


class TestSteamIDValidator:
    """Test cases for Steam ID validation."""

    def test_valid_steam_id64(self):
        """Test valid Steam ID64 format."""
        valid_id = "76561198012345678"
        validator = SteamIDValidator(steamid=valid_id)
        assert validator.steamid == valid_id

    def test_invalid_steam_id64_length(self):
        """Test Steam ID64 with invalid length."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="123456789")
        assert "exactly 17 digits" in str(exc_info.value)

    def test_invalid_steam_id64_prefix(self):
        """Test Steam ID64 with invalid prefix."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="12345678901234567")
        assert "Invalid Steam ID64 format" in str(exc_info.value)

    def test_valid_vanity_name(self):
        """Test valid vanity URL name."""
        valid_vanity = "testuser123"
        validator = SteamIDValidator(steamid=valid_vanity)
        assert validator.steamid == valid_vanity

    def test_vanity_name_too_short(self):
        """Test vanity name that is too short."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="a")
        assert "between 2 and 32 characters" in str(exc_info.value)

    def test_vanity_name_too_long(self):
        """Test vanity name that is too long."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="a" * 33)
        assert "between 2 and 32 characters" in str(exc_info.value)

    def test_vanity_name_invalid_characters(self):
        """Test vanity name with invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="user@name")
        assert "letters, numbers, underscores, and hyphens" in str(exc_info.value)

    def test_valid_profile_url(self):
        """Test valid Steam profile URL."""
        valid_url = "https://steamcommunity.com/id/testuser"
        validator = SteamIDValidator(steamid=valid_url)
        assert validator.steamid == valid_url

    def test_valid_profiles_url_with_id64(self):
        """Test valid Steam profiles URL with ID64."""
        valid_url = "https://steamcommunity.com/profiles/76561198012345678"
        validator = SteamIDValidator(steamid=valid_url)
        assert validator.steamid == valid_url

    def test_empty_steamid(self):
        """Test empty Steam ID."""
        with pytest.raises(ValidationError) as exc_info:
            SteamIDValidator(steamid="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from Steam ID."""
        validator = SteamIDValidator(steamid="  testuser  ")
        # Whitespace is stripped by Pydantic's str_strip_whitespace config
        assert validator.steamid == "testuser"


class TestAppIDValidator:
    """Test cases for App ID validation."""

    def test_valid_appid(self):
        """Test valid App ID."""
        valid_appid = 730
        validator = AppIDValidator(appid=valid_appid)
        assert validator.appid == valid_appid

    def test_appid_zero(self):
        """Test App ID of zero."""
        with pytest.raises(ValidationError) as exc_info:
            AppIDValidator(appid=0)
        assert "greater than 0" in str(exc_info.value)

    def test_appid_negative(self):
        """Test negative App ID."""
        with pytest.raises(ValidationError) as exc_info:
            AppIDValidator(appid=-1)
        assert "greater than 0" in str(exc_info.value)

    def test_appid_too_large(self):
        """Test App ID that is too large."""
        with pytest.raises(ValidationError) as exc_info:
            AppIDValidator(appid=10000000)
        assert "less than 10000000" in str(exc_info.value)

    def test_appid_boundary_max(self):
        """Test App ID at maximum boundary."""
        valid_appid = 9999999
        validator = AppIDValidator(appid=valid_appid)
        assert validator.appid == valid_appid

    def test_appid_boundary_min(self):
        """Test App ID at minimum boundary."""
        valid_appid = 1
        validator = AppIDValidator(appid=valid_appid)
        assert validator.appid == valid_appid
