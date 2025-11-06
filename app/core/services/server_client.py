"""
Server client module for Custom Steam Dashboard.
Handles communication with the backend server API.
"""
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class ServerClient:
    """
    Client for communicating with Custom Steam Dashboard server.
    
    Features:
    - Fetch current player counts for watchlist games
    - Get game details and tags
    - Fetch deals and upcoming releases
    - Handle connection errors gracefully
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the server client.
        
        Args:
            base_url: Base URL of the server API
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    # ===== Game Data Endpoints =====
    
    async def get_current_players(self) -> List[Dict[str, Any]]:
        """
        Get current player counts for all watchlist games.
        
        Returns:
            List of games with player counts and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/current-players")
                response.raise_for_status()
                data = response.json()
                return data.get("games", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching current players: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching current players: {e}")
            return []
    
    async def get_game_details(self, appid: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific game.
        
        Args:
            appid: Steam application ID
            
        Returns:
            Game details dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/games/{appid}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Game {appid} not found")
                return None
            logger.error(f"Error fetching game details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching game details: {e}")
            return None
    
    async def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Get all games from the database.
        
        Returns:
            List of all games
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/games")
                response.raise_for_status()
                data = response.json()
                return data.get("games", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching all games: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching all games: {e}")
            return []
    
    # ===== Steam API Endpoints =====
    
    async def get_coming_soon_games(self) -> List[Dict[str, Any]]:
        """
        Get upcoming game releases from Steam.
        
        Returns:
            List of upcoming games
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/coming-soon")
                response.raise_for_status()
                data = response.json()
                return data.get("games", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching coming soon games: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching coming soon games: {e}")
            return []
    
    async def get_owned_games(self, steamid: str) -> List[Dict[str, Any]]:
        """
        Get owned games for a Steam user.
        
        Args:
            steamid: Steam ID64
            
        Returns:
            List of owned games
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/owned-games/{steamid}")
                response.raise_for_status()
                data = response.json()
                return data.get("games", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching owned games: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching owned games: {e}")
            return []
    
    async def get_recently_played(self, steamid: str) -> List[Dict[str, Any]]:
        """
        Get recently played games for a Steam user.
        
        Args:
            steamid: Steam ID64
            
        Returns:
            List of recently played games
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/recently-played/{steamid}")
                response.raise_for_status()
                data = response.json()
                return data.get("games", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching recently played games: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching recently played games: {e}")
            return []
    
    async def get_player_summary(self, steamid: str) -> Optional[Dict[str, Any]]:
        """
        Get Steam player summary.
        
        Args:
            steamid: Steam ID64
            
        Returns:
            Player summary dict or None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/player-summary/{steamid}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching player summary: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching player summary: {e}")
            return None
    
    async def resolve_vanity_url(self, vanity_url: str) -> Optional[str]:
        """
        Resolve a Steam vanity URL or custom name to a Steam ID64.

        Args:
            vanity_url: Vanity name, custom URL, or full profile URL
                       Examples: 'gaben', 'my_custom_name',
                                'https://steamcommunity.com/id/gaben'

        Returns:
            Steam ID64 string if found, None otherwise
        """
        try:
            # URL encode the vanity_url to handle special characters and slashes
            import urllib.parse
            encoded_vanity = urllib.parse.quote(vanity_url, safe='')

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/resolve-vanity/{encoded_vanity}")
                response.raise_for_status()
                data = response.json()
                return data.get('steamid')
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Could not resolve vanity URL: {vanity_url}")
                return None
            logger.error(f"Error resolving vanity URL: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Error resolving vanity URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error resolving vanity URL: {e}")
            return None

    # ===== Genre and Category Endpoints =====

    async def get_all_genres(self) -> List[str]:
        """
        Get all unique genres from the database.

        Returns:
            List of genre names
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/genres")
                response.raise_for_status()
                data = response.json()
                return data.get("genres", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching genres: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching genres: {e}")
            return []

    async def get_all_categories(self) -> List[str]:
        """
        Get all unique categories from the database.

        Returns:
            List of category names
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/categories")
                response.raise_for_status()
                data = response.json()
                return data.get("categories", [])
        except httpx.HTTPError as e:
            logger.error(f"Error fetching categories: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching categories: {e}")
            return []

    async def get_game_tags(self, appid: int) -> Dict[str, Any]:
        """
        Get genres and categories for a specific game.

        Args:
            appid: Steam application ID

        Returns:
            Dict with genres, categories, and combined tags
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/games/{appid}/tags")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching game tags: {e}")
            return {"appid": appid, "genres": [], "categories": [], "tags": []}
        except Exception as e:
            logger.error(f"Unexpected error fetching game tags: {e}")
            return {"appid": appid, "genres": [], "categories": [], "tags": []}

    async def get_game_details(self, appid: int) -> Optional[Dict[str, Any]]:
        """
        Get full game details from server database.

        Args:
            appid: Steam application ID

        Returns:
            Dict with game details (name, description, images, price, genres, categories) or None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/games/{appid}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Game {appid} not found in database")
                return None
            logger.error(f"Error fetching game details: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Error fetching game details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching game details: {e}")
            return None

    # ===== Health Check =====
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health status.
        
        Returns:
            Health status dict
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error checking server health: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error checking server health: {e}")
            return {"status": "error", "message": str(e)}

