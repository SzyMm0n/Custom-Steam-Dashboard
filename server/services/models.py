from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# === Pydantic models for Steam API responses ===
class SteamGameDetails(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    appid: int
    name: str
    is_free: bool
    price : float
    detailed_description: str
    header_image: str
    background_image: str
    coming_soon: bool
    release_date: str | None
    categories : list[str]
    genres : list[str]

class PlayerCountResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    appid : int
    player_count: int


class SteamPlayerGameOverview(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    appid: int
    name: str
    playtime_forever: int
    playtime_2weeks: int
    img_icon_url: str

class SteamPlayerDetails(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    steamid: str
    personaname: str
    profileurl: str
    avatar: str
    avatarfull: str


# === Pydantic models for Deals API responses ===
class DealInfo(BaseModel):
    """Information about a game deal"""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    steam_appid: int | None = None
    game_title: str
    store_name: str
    store_url: str
    current_price: float
    regular_price: float
    discount_percent: int
    currency: str = "USD"
    drm: str = "Unknown"


class GamePrice(BaseModel):
    """Price information for a specific game"""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    steam_appid: int
    game_title: str
    store_name: str
    store_url: str
    current_price: float
    regular_price: float
    discount_percent: int
    currency: str = "USD"
    drm: str = "Unknown"


