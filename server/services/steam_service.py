from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from abc import ABC, abstractmethod

from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from server.services.models import SteamGameDetails, PlayerCountResponse, SteamPlayerGameOverview
import httpx

from server.services._base_http import BaseAsyncService
from server.services.parse_html import parse_html_tags

logger = logging.getLogger(__name__)

class ISteamService(ABC):

    @abstractmethod
    async def get_player_count(self, appid: int) -> PlayerCountResponse: ...

    @abstractmethod
    async def get_game_details(self, appid: int) -> SteamGameDetails: ...

    @abstractmethod
    async def get_coming_soon_games(self) -> list[SteamGameDetails]: ...

    @abstractmethod
    async def get_most_played_games(self) -> list[SteamGameDetails]: ...

    @abstractmethod
    async def get_player_owned_games(self, steam_id: str) -> list[SteamPlayerGameOverview]: ...

    @abstractmethod
    async def get_recently_played_games(self, steam_id: str) -> list[SteamPlayerGameOverview]: ...

    @abstractmethod
    async def get_badges(self, steam_id: str) -> dict: ...

    @abstractmethod
    async def get_player_summary(self, steam_id: str) -> dict: ...

    @abstractmethod
    async def resolve_vanity_url(self, vanity_url: str) -> str | None: ...

class SteamClient(BaseAsyncService, ISteamService):

    api_key: str = os.getenv('STEAM_API_KEY', '')

    def __init__(self, *, timeout: httpx.Timeout | float | None = None):
        if timeout is not None:
            super().__init__(timeout=timeout)
        else:
            super().__init__()

    async def get_player_count(self, appid: int) -> PlayerCountResponse:
        """
        Get the current player count for a given appid.

        Args:
            appid (int): The Steam appid of the game
        Returns:
            PlayerCountResponse: The player count response
        """
        logger.info(f"Getting player count for appid: {appid}")

        player_count_endpoint = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        params = {
            "appid": appid,
        }

        data = await self._get_json(player_count_endpoint, params=params)

        if data and 'response' in data:

            logger.debug(f"Player count data retrieved successfully for appid: {appid}")
            response = data.get('response')
            return PlayerCountResponse(appid=appid, player_count=response.get('player_count', 0))

        logger.warning(f"Failed to retrieve player count data for appid: {appid}")
        return PlayerCountResponse(appid=appid, player_count=0)

    async def get_game_details(self, appid: int) -> SteamGameDetails | None:
        """
        Get game details for a given appid.

        Args:
            appid (int): The Steam appid of the game
        Returns:
            SteamGameDetails | None: The game details or None if not found
        """

        logger.info(f"Getting game details for appid: {appid}")

        game_details_endpoint = "https://store.steampowered.com/api/appdetails"
        params = {
            "appids": appid,
            "cc" : "pln",
            "l" : "en",
        }
        data = await self._get_json(game_details_endpoint, params=params)
        if data and str(appid) in data and data[str(appid)].get('success', False):
            logger.debug(f"Game details data retrieved successfully for appid: {appid}")
            data = data[str(appid)].get('data', {})
            return SteamGameDetails(
                appid=data.get('steam_appid', -1),
                name=data.get('name', ''),
                is_free=data.get('is_free', False),
                price=data.get('price_overview', {}).get('final', 0) / 100 if 'price_overview' in data else 0.0,
                detailed_description= await parse_html_tags(data.get('detailed_description', '')),
                header_image=data.get('header_image', ''),
                background_image=data.get('background', ''),
                coming_soon=data.get('release_date', {}).get('coming_soon', False),
                release_date=data.get('release_date', {}).get('date', None),
                categories=[category.get('description') for category in data.get('categories', [])],
                genres=[genre.get('description') for genre in data.get('genres', [])],
            )
        logger.warning(f"Failed to retrieve game details data for appid: {appid}")
        return None

    async def get_coming_soon_games(self) -> list[SteamGameDetails]:
        """
        Get a list of games coming soon on Steam.

        Args:
            None
        Returns:
            list[SteamGameDetails]: A list of games coming soon on Steam
        """
        logger.info(f"Getting coming soon games from Steam")

        coming_soon_endpoint = "https://store.steampowered.com/api/featuredcategories/"
        params = {
            "cc": "pln",
            "l": "en",
        }
        data = await self._get_json(coming_soon_endpoint, params=params)
        coming_soon_games = []
        if data:
            logger.info("Coming soon games data retrieved successfully")
            items = data.get('coming_soon', {}).get('items', [])
            for game in items:
                coming_soon_games.append(
                SteamGameDetails(
                    appid=game.get('id', -1),
                    name=game.get('name', ''),
                    is_free=False if game.get('final_price', -1) > 0 else True,
                    price=game.get('final_price', 0) / 100 if 'final_price' in game else 0.0,
                    detailed_description='',
                    header_image=game.get('header_image', ''),
                    background_image=game.get('large_capsule_image', ''),
                    coming_soon=True,
                    release_date=game.get('release_date', None),
                    categories=[],
                    genres=[],
                )
                )
            return coming_soon_games

        logger.warning("Failed to retrieve coming soon games data")
        return coming_soon_games

    async def get_most_played_games(self) -> list[SteamGameDetails]:
        """
        Get the most played games on Steam.

        Args:
            None
        Returns:
            list[SteamGameDetails]: A list of the most played games on Steam
        """

        logger.info(f"Getting most played games from Steam")
        most_played_endpoint = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
        semaphore = asyncio.Semaphore(10)

        data = await self._get_json(most_played_endpoint)
        most_played_games = []

        if data:
            logger.info("Most played games data retrieved successfully")
            items = data.get('response', {}).get('ranks', [])

            async def fetch_game_details(appid: int):
                async with semaphore:
                    return await self.get_game_details(appid)

            tasks = [fetch_game_details(game.get('appid', -1)) for game in items]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            most_played_games = [game for game in results if isinstance(game, SteamGameDetails)]

        return most_played_games

    async def get_player_owned_games(self, steam_id: str) -> list[SteamPlayerGameOverview]:
        """
        Get owned games for a given player library using Steam ID.

        Args:
            steam_id (str): The Steam ID of the player
        Returns:
            list[SteamPlayerGameOverview]: A list of owned games, including free titles
        """

        logger.info(f"Getting owned games for steam_id: {steam_id}")

        player_games_endpoint = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": True,
            "include_played_free_games": True
        }
        data = await self._get_json(player_games_endpoint, params=params)
        owned_games = []
        if data and 'response' in data:
            logger.debug(f"Owned games data retrieved successfully for steam_id: {steam_id}")
            games = data.get('response', {}).get('games', [])
            for game in games:
                owned_games.append(
                    SteamPlayerGameOverview(
                        appid=game.get('appid', -1),
                        name=game.get('name', ''),
                        playtime_forever=game.get('playtime_forever', 0),
                        playtime_2weeks=game.get('playtime_2weeks', 0),
                        img_icon_url=game.get('img_icon_url', ''),
                    )
                )
            return owned_games

        logger.warning(f"Failed to retrieve owned games data for steam_id: {steam_id}")
        return owned_games

    async def get_recently_played_games(self, steam_id: str) -> list[SteamPlayerGameOverview]:
        """
        Get recently played games for a given player using Steam ID.

        Args:
            steam_id (str): The Steam ID of the player
        Returns:
            list[SteamPlayerGameOverview]: A list of recently played games
        """

        logger.info(f"Getting recently played games for steam_id: {steam_id}")

        recent_games_endpoint = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": True,
        }
        data = await self._get_json(recent_games_endpoint, params=params)

        recent_games = []
        if data and 'response' in data:
            logger.debug(f"Recently played games data retrieved successfully for steam_id: {steam_id}")
            games = data.get('response', {}).get('games', [])
            for game in games:
                recent_games.append(
                    SteamPlayerGameOverview(
                        appid=game.get('appid', -1),
                        name=game.get('name', ''),
                        playtime_forever=game.get('playtime_forever', 0),
                        playtime_2weeks=game.get('playtime_2weeks', 0),
                        img_icon_url=game.get('img_icon_url', ''),
                    )
                )
            return recent_games

        logger.warning(f"Failed to retrieve recently played games data for steam_id: {steam_id}")
        return recent_games

    # TODO: Check if badge id can be mapped to badge details
    async def get_badges(self, steam_id: str) -> dict:
        """
        Get badges for a given Steam ID, currently returns raw badge data.

        Args:
            steam_id (str): The Steam ID of the player
        Returns:
            dict: A dictionary containing badge information
        """

        logger.info(f"Getting badges for steam_id: {steam_id}")
        badges_endpoint = "https://api.steampowered.com/IPlayerService/GetBadges/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
        }
        data = await self._get_json(badges_endpoint, params=params)
        if data and 'response' in data:
            logger.debug(f"Badges data retrieved successfully for steam_id: {steam_id}")
            return data.get('response', {})

        logger.warning(f"Failed to retrieve badges data for steam_id: {steam_id}")
        return {}

    async def get_player_summary(self, steam_id: str) -> dict:
        """
        Get player summary information for a given Steam ID

        Args:
            steam_id (str): The Steam ID of the player
        Returns:
            dict: A dictionary containing player summary information
        """
        logger.info(f"Getting player summary for steam_id: {steam_id}")
        player_summary_endpoint = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {
            "key": self.api_key,
            "steamids": steam_id,
        }
        data = await self._get_json(player_summary_endpoint, params=params)
        if data and 'response' in data:
            logger.debug(f"Player summary data retrieved successfully for steam_id: {steam_id}")
            players = data.get('response', {}).get('players', [])
            if players:
                return players[0]

        logger.warning(f"Failed to retrieve player summary data for steam_id: {steam_id}")
        return {}

    async def resolve_vanity_url(self, vanity_url: str) -> str | None:
        """
        Resolve a Steam vanity URL (custom URL) to a Steam ID64.

        Args:
            vanity_url (str): The vanity URL or custom name (e.g., 'gaben' or 'my_custom_name')

        Returns:
            str | None: The Steam ID64 if found, None otherwise
        """
        logger.info(f"Resolving vanity URL: {vanity_url}")

        # Extract vanity name from full URL if provided
        vanity_name = vanity_url
        if '/' in vanity_url:
            # Handle formats like:
            # - https://steamcommunity.com/id/gaben
            # - steamcommunity.com/id/customname
            # - /id/username
            parts = vanity_url.rstrip('/').split('/')
            if 'id' in parts:
                idx = parts.index('id')
                if idx + 1 < len(parts):
                    vanity_name = parts[idx + 1]
            else:
                # Take last non-empty part
                vanity_name = parts[-1] if parts[-1] else vanity_url

        vanity_name = vanity_name.strip()

        if not vanity_name:
            logger.warning("Empty vanity name provided")
            return None

        # Check if it's already a Steam ID64 (17-digit number)
        if vanity_name.isdigit() and len(vanity_name) == 17:
            logger.debug(f"Input is already a Steam ID64: {vanity_name}")
            return vanity_name

        # Use Steam API to resolve vanity URL
        resolve_endpoint = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {
            "key": self.api_key,
            "vanityurl": vanity_name,
        }

        data = await self._get_json(resolve_endpoint, params=params)

        if data and 'response' in data:
            response = data.get('response', {})
            success = response.get('success')

            # success == 1 means the vanity URL was resolved successfully
            if success == 1:
                steam_id = response.get('steamid')
                logger.info(f"Successfully resolved vanity URL '{vanity_name}' to Steam ID: {steam_id}")
                return steam_id
            else:
                logger.warning(f"Failed to resolve vanity URL '{vanity_name}': {response.get('message', 'Unknown error')}")
                return None

        logger.warning(f"No response from Steam API for vanity URL: {vanity_name}")
        return None

if __name__ == "__main__":
    import asyncio

    load_dotenv()
    async def test():
        client = SteamClient()
        owned_games = await client.get_player_owned_games(os.getenv('STEAM_ID'))
        for game in owned_games:
            print(game)

        badges = await client.get_badges(os.getenv('STEAM_ID'))
        print(badges)

    asyncio.run(test())