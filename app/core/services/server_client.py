"""
Server client module for Custom Steam Dashboard.
Handles communication with the backend server API.
"""
import logging
import os
from typing import List, Dict, Any, Optional
import httpx

from app.helpers.api_client import AuthenticatedAPIClient

logger = logging.getLogger(__name__)


class ServerClient:
    """
    Client for communicating with Custom Steam Dashboard server.
    
    Features:
    - Authenticated requests with JWT and HMAC signatures
    - Fetch current player counts for watchlist games
    - Get game details and tags
    - Fetch deals and upcoming releases
    - Handle connection errors gracefully
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the server client.
        
        Args:
            base_url: Base URL of the server API (defaults to SERVER_URL from environment)
        """
        if base_url is None:
            base_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)

        # Create a new authenticated API client instance for this ServerClient
        # (not using singleton - each ServerClient gets its own authenticated session)
        self._api_client = AuthenticatedAPIClient(base_url)

    async def authenticate(self) -> bool:
        """
        Authenticate with the server.
        Must be called before making any API requests.

        Returns:
            True if authentication successful, False otherwise
        """
        return await self._api_client.login()

    # ===== Game Data Endpoints =====
    
    async def get_current_players(self) -> List[Dict[str, Any]]:
        """
        Get current player counts for all watchlist games.
        
        Returns:
            List of games with player counts and metadata
        """
        try:
            data = await self._api_client.get("/api/current-players")
            if data:
                return data.get("games", [])
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching current players: {e}")
            return []
    
    async def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Get all games from the database.
        
        Returns:
            List of all games
        """
        try:
            data = await self._api_client.get("/api/games")
            if data:
                return data.get("games", [])
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
            data = await self._api_client.get("/api/coming-soon")
            if data:
                return data.get("games", [])
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
            data = await self._api_client.get(f"/api/owned-games/{steamid}")
            if data:
                return data.get("games", [])
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
            data = await self._api_client.get(f"/api/recently-played/{steamid}")
            if data:
                return data.get("games", [])
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
            return await self._api_client.get(f"/api/player-summary/{steamid}")
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

            data = await self._api_client.get(f"/api/resolve-vanity/{encoded_vanity}")
            if data:
                return data.get('steamid')
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
            data = await self._api_client.get("/api/genres")
            if data:
                return data.get("genres", [])
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
            data = await self._api_client.get("/api/categories")
            if data:
                return data.get("categories", [])
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching categories: {e}")
            return []

    async def get_game_tags_batch(self, appids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get genres and categories for multiple games in one batch request.

        Args:
            appids: List of Steam application IDs

        Returns:
            Dict mapping appid to dict with genres, categories, and combined tags
            Example: {123: {"genres": ["Action"], "categories": ["Multiplayer"], "tags": ["Action", "Multiplayer"]}}
        """
        if not appids:
            return {}

        try:
            data = await self._api_client.post("/api/games/tags/batch", {"appids": appids})
            if data:
                tags_batch_raw = data.get("tags", {})

                # Convert string keys back to int and add combined "tags" field
                tags_batch = {}
                for appid_str, tags_data in tags_batch_raw.items():
                    appid = int(appid_str)
                    genres = tags_data.get("genres", [])
                    categories = tags_data.get("categories", [])
                    tags_batch[appid] = {
                        "genres": genres,
                        "categories": categories,
                        "tags": list(set(genres + categories))
                    }

                return tags_batch
            return {appid: {"genres": [], "categories": [], "tags": []} for appid in appids}
        except Exception as e:
            logger.error(f"Unexpected error fetching game tags batch: {e}")
            return {appid: {"genres": [], "categories": [], "tags": []} for appid in appids}

    async def get_game_tags(self, appid: int) -> Dict[str, Any]:
        """
        Get genres and categories for a single game (convenience method).

        Args:
            appid: Steam application ID

        Returns:
            Dict with genres, categories, and combined tags
            Example: {"genres": ["Action"], "categories": ["Multiplayer"], "tags": ["Action", "Multiplayer"]}
        """
        batch_result = await self.get_game_tags_batch([appid])
        return batch_result.get(appid, {"genres": [], "categories": [], "tags": []})

    async def get_game_details(self, appid: int) -> Optional[Dict[str, Any]]:
        """
        Get full game details from server database.

        Args:
            appid: Steam application ID

        Returns:
            Dict with game details (name, description, images, price, genres, categories) or None
        """
        try:
            return await self._api_client.get(f"/api/games/{appid}")
        except Exception as e:
            logger.error(f"Unexpected error fetching game details: {e}")
            return None

    # ===== Deals Endpoints =====

    async def get_best_deals(
        self,
        limit: int = 20,
        min_discount: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get the best current game deals from the server.

        Args:
            limit: Maximum number of deals to return (1-50, default: 20)
            min_discount: Minimum discount percentage (0-100, default: 20)

        Returns:
            List of deal dictionaries
        """
        try:
            data = await self._api_client.get(
                f"/api/deals/best?limit={limit}&min_discount={min_discount}"
            )
            if data:
                return data.get("deals", [])
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching deals: {e}")
            return []

    async def get_game_deal(self, appid: int) -> Optional[Dict[str, Any]]:
        """
        Get deal and price information for a specific game.

        Args:
            appid: Steam application ID

        Returns:
            Dictionary containing game and deal information
        """
        try:
            return await self._api_client.get(f"/api/deals/game/{appid}")
        except Exception as e:
            logger.error(f"Unexpected error fetching game deal: {e}")
            return None

    async def search_game_deals(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for game deals by title.

        Args:
            title: Game title to search for

        Returns:
            Dictionary with game info and deal information, or None on error
        """
        try:
            import urllib.parse
            encoded_title = urllib.parse.quote(title)
            return await self._api_client.get(f"/api/deals/search?title={encoded_title}")
        except Exception as e:
            logger.error(f"Unexpected error searching game deals: {e}")
            return None

    async def get_player_history_comparison(self, appids: List[int], days: float = 7) -> Dict[int, Dict[str, Any]]:
        """
        Get player count history for multiple games for comparison.

        Args:
            appids: List of Steam application IDs
            days: Number of days of history to retrieve (default: 7, supports fractional for hours)

        Returns:
            Dictionary mapping appid to game data with history
        """
        if not appids:
            return {}

        try:
            logger.info(f"Fetching player history comparison for {len(appids)} games, {days} days")
            data = await self._api_client.post(
                f"/api/player-history/compare?days={days}",
                {"appids": appids}
            )
            if data:
                games_data = data.get("games", {})
                logger.info(f"Received history data for {len(games_data)} games")
                # Convert string keys to int
                return {int(k): v for k, v in games_data.items()}
            logger.warning("No data returned from player history comparison endpoint")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching player history comparison: {e}", exc_info=True)
            return {}

    # ===== Health Check =====
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health status.
        
        Returns:
            Health status dict
        """
        try:
            # Health check doesn't require authentication
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
