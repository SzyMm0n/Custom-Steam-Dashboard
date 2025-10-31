from __future__ import annotations

from pydantic.dataclasses import dataclass
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

