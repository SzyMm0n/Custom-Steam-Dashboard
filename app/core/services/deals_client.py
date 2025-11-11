"""
Deals client module for Custom Steam Dashboard.
Handles communication with the backend server for deals and pricing information.
"""
import logging
import os
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class DealsClient:
    """
    Client for fetching game deals and pricing information from the server.
    
    The backend server uses IsThereAnyDeal API to provide:
    - Best current deals based on watchlist
    - Price information for specific games
    - Historical pricing data
    
    This client provides a clean interface for the GUI to request deals data.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the deals client.
        
        Args:
            base_url: Base URL of the backend server API (defaults to SERVER_URL from environment)
        """
        if base_url is None:
            base_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    async def get_best_deals(
        self,
        limit: int = 20,
        min_discount: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get the best current game deals from the server.
        
        The server checks prices for games in the watchlist and returns
        the best available deals based on the specified criteria.
        
        Args:
            limit: Maximum number of deals to return (1-50, default: 20)
            min_discount: Minimum discount percentage (0-100, default: 20)
        
        Returns:
            List of deal dictionaries containing:
                - game_title: Name of the game
                - steam_appid: Steam application ID
                - current_price: Current sale price
                - regular_price: Original/regular price
                - discount_percent: Discount percentage
                - currency: Currency code (e.g., 'USD')
                - store_name: Name of the store offering the deal
                - store_url: URL to purchase the game
                - updated_at: Last price update timestamp
        
        Example:
            >>> deals = await client.get_best_deals(limit=10, min_discount=30)
            >>> for deal in deals:
            ...     print(f"{deal['game_title']}: ${deal['current_price']} (-{deal['discount_percent']}%)")
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/deals/best",
                    params={
                        "limit": limit,
                        "min_discount": min_discount
                    }
                )
                response.raise_for_status()
                data = response.json()
                deals = data.get("deals", [])
                
                logger.info(f"Fetched {len(deals)} deals from server")
                return deals
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching deals: {e.response.status_code} - {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching deals: {e}")
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
            Dictionary containing game and deal information:
                - game: Game details (name, appid, etc.)
                - deal: Current best deal if available, or None
                  Contains same fields as get_best_deals results
            Returns None if game is not found or request fails.
        
        Example:
            >>> game_info = await client.get_game_deal(730)  # CS2
            >>> if game_info and game_info.get('deal'):
            ...     deal = game_info['deal']
            ...     print(f"Best price: ${deal['current_price']} at {deal['store_name']}")
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/deals/game/{appid}")
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"Fetched deal information for game {appid}")
                return data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"No deal information found for game {appid}")
                return None
            logger.error(f"HTTP error fetching game deal: {e.response.status_code} - {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching game deal: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching game deal: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if the deals service is available on the server.
        
        Returns:
            True if the service is available, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Deals service health check failed: {e}")
            return False


# Context manager support for resource cleanup
class DealsClientContext:
    """
    Context manager wrapper for DealsClient.
    
    Allows usage with async context managers for automatic resource cleanup,
    though the current implementation doesn't require it (httpx clients
    are created per request).
    
    Example:
        >>> async with DealsClientContext(server_url) as client:
        ...     deals = await client.get_best_deals()
    """
    
    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            import os
            base_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self.base_url = base_url
        self._client = None
    
    async def __aenter__(self) -> DealsClient:
        self._client = DealsClient(self.base_url)
        return self._client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Nothing to cleanup in current implementation
        pass


# Convenience function for one-off requests
async def get_current_deals(
    limit: int = 20,
    min_discount: int = 20,
    server_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch deals without creating a client instance.
    
    Args:
        limit: Maximum number of deals to return
        min_discount: Minimum discount percentage
        server_url: Backend server URL (defaults to SERVER_URL from environment)

    Returns:
        List of deal dictionaries
    """
    if server_url is None:
        import os
        server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    client = DealsClient(server_url)
    return await client.get_best_deals(limit, min_discount)


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        """Test the deals client functionality."""
        client = DealsClient()
        
        print("=== Testing Deals Client ===\n")
        
        # Test health check
        print("1. Health Check")
        is_healthy = await client.health_check()
        print(f"   Service available: {is_healthy}\n")
        
        if not is_healthy:
            print("Server not available. Make sure the server is running.")
            return
        
        # Test getting best deals
        print("2. Best Deals (limit=5, min_discount=20%)")
        deals = await client.get_best_deals(limit=5, min_discount=20)
        if deals:
            for i, deal in enumerate(deals, 1):
                print(f"   {i}. {deal.get('game_title', 'Unknown')}")
                print(f"      Price: ${deal.get('current_price', 0):.2f} "
                      f"(was ${deal.get('regular_price', 0):.2f}, "
                      f"-{deal.get('discount_percent', 0)}%)")
                print(f"      Store: {deal.get('store_name', 'Unknown')}")
        else:
            print("   No deals found")
        
        print("\n3. Specific Game Deal (Counter-Strike 2, AppID 730)")
        game_deal = await client.get_game_deal(730)
        if game_deal:
            game = game_deal.get('game', {})
            deal = game_deal.get('deal')
            print(f"   Game: {game.get('name', 'Counter-Strike 2')}")
            if deal:
                print(f"   Best Deal: ${deal.get('current_price', 0):.2f} "
                      f"(-{deal.get('discount_percent', 0)}%) "
                      f"at {deal.get('store_name', 'N/A')}")
            else:
                print("   No active deals")
        else:
            print("   Game not found")
        
        print("\n=== Test Complete ===")
    
    asyncio.run(test())

