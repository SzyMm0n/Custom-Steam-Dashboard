"""
Input validation models and utilities for API endpoints.
"""
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class SteamIDValidator(BaseModel):
    """Validator for Steam ID inputs"""
    steamid: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator('steamid')
    @classmethod
    def validate_steamid(cls, v: str) -> str:
        """
        Validate Steam ID format.
        Can be either:
        - Steam ID64 (17 digits starting with 7656119)
        - Vanity URL name (alphanumeric, underscore, hyphen, 2-32 chars)
        - Full Steam profile URL
        """
        # Strip whitespace
        v = v.strip()
        
        if not v:
            raise ValueError("Steam ID cannot be empty")
        
        # Check if it's a Steam ID64 (17 digits)
        if v.isdigit():
            if len(v) != 17:
                raise ValueError("Steam ID64 must be exactly 17 digits")
            if not v.startswith('7656119'):
                raise ValueError("Invalid Steam ID64 format")
            return v
        
        # Check if it's a full URL
        if v.startswith('https://'):
            # Extract vanity name from URL
            url_pattern = r'(?:https://)?(?:www\.)?steamcommunity\.com/(?:id|profiles)/([a-zA-Z0-9_-]+)/?'
            match = re.match(url_pattern, v)
            if not match:
                raise ValueError("Invalid Steam profile URL format")
            vanity_name = match.group(1)
            # If it's a profiles URL, it should be numeric
            if '/profiles/' in v:
                if not vanity_name.isdigit():
                    raise ValueError("Profile URL must contain numeric Steam ID")
                if len(vanity_name) != 17:
                    raise ValueError("Steam ID64 in URL must be exactly 17 digits")
            return v
        
        # Otherwise treat as vanity name
        if len(v) < 2 or len(v) > 32:
            raise ValueError("Vanity URL name must be between 2 and 32 characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Vanity URL name can only contain letters, numbers, underscores, and hyphens")
        
        return v


class AppIDValidator(BaseModel):
    """Validator for Steam App ID"""
    appid: int = Field(..., gt=0, lt=10000000)

    @field_validator('appid')
    @classmethod
    def validate_appid(cls, v: int) -> int:
        """Validate that appid is a positive integer in reasonable range"""
        if v <= 0:
            raise ValueError("App ID must be positive")
        if v >= 10000000:
            raise ValueError("App ID too large")
        return v


class AppIDListValidator(BaseModel):
    """Validator for list of Steam App IDs"""
    appids: List[int] = Field(..., min_length=1, max_length=100)

    @field_validator('appids')
    @classmethod
    def validate_appids(cls, v: List[int]) -> List[int]:
        """Validate list of app IDs"""
        if not v:
            raise ValueError("App ID list cannot be empty")
        
        if len(v) > 100:
            raise ValueError("Maximum 100 app IDs allowed per request")
        
        for appid in v:
            if not isinstance(appid, int):
                raise ValueError(f"App ID must be an integer, got {type(appid)}")
            if appid <= 0:
                raise ValueError(f"App ID must be positive, got {appid}")
            if appid >= 10000000:
                raise ValueError(f"App ID {appid} too large")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_appids = []
        for appid in v:
            if appid not in seen:
                seen.add(appid)
                unique_appids.append(appid)
        
        return unique_appids


class VanityURLValidator(BaseModel):
    """Validator for Steam vanity URL"""
    vanity_url: str = Field(..., min_length=1, max_length=200)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator('vanity_url')
    @classmethod
    def validate_vanity_url(cls, v: str) -> str:
        """Validate vanity URL format"""
        v = v.strip()
        
        if not v:
            raise ValueError("Vanity URL cannot be empty")
        
        if len(v) > 200:
            raise ValueError("Vanity URL too long")
        
        # If it's a full URL, validate format
        if v.startswith('https://'):
            url_pattern = r'(?:https://)?(?:www\.)?steamcommunity\.com/(?:id|profiles)/([a-zA-Z0-9_-]+)/?'
            if not re.match(url_pattern, v):
                raise ValueError("Invalid Steam community URL format")
        else:
            # Validate as vanity name
            if len(v) < 2 or len(v) > 32:
                raise ValueError("Vanity name must be between 2 and 32 characters")
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("Vanity name can only contain letters, numbers, underscores, and hyphens")
        
        return v


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing potential injection characters.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    
    # Truncate to max length
    value = value[:max_length]
    
    # Remove null bytes and control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    return value.strip()

