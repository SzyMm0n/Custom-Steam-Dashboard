from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

import httpx

from server.services._base_http import BaseAsyncService
from server.services.models import DealInfo, GamePrice

logger = logging.getLogger(__name__)


class IDealsService(ABC):
    """Interface for deals service"""

    @abstractmethod
    async def get_best_deals(self, limit: int = 20, min_discount: int = 20) -> List[DealInfo]:
        """Get best current deals"""
        ...

    @abstractmethod
    async def get_game_prices(self, steam_appid: int) -> Optional[GamePrice]:
        """Get price information for a specific game"""
        ...

    @abstractmethod
    async def search_game(self, title: str) -> Optional[Dict[str, Any]]:
        """Search for a game by title"""
        ...


class IsThereAnyDealClient(BaseAsyncService, IDealsService):
    """
    Client for IsThereAnyDeal API v2.
    
    API Documentation: https://docs.isthereanydeal.com/
    """

    def __init__(self, *, timeout: httpx.Timeout | float | None = None):
        if timeout is not None:
            super().__init__(timeout=timeout)
        else:
            super().__init__(timeout=httpx.Timeout(30.0, connect=10.0))

        # Load credentials from environment
        self.api_key = os.getenv('ITAD_API_KEY', '')
        self.client_id = os.getenv('ITAD_CLIENT_ID', '')
        self.client_secret = os.getenv('ITAD_CLIENT_SECRET', '')

        if not self.api_key or not self.client_id:
            logger.warning(
                "IsThereAnyDeal credentials not found in environment variables. "
                "Set ITAD_API_KEY and ITAD_CLIENT_ID for full functionality."
            )

        self.base_url = "https://api.isthereanydeal.com"
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None


    async def _get_access_token(self) -> str:
        """
        Get or refresh OAuth2 access token.
        
        Returns:
            Access token string
        """
        # Check if we have a valid token
        if self._token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at:
                return self._token

        # Request new token
        token_url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self._client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()

            self._token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)

            logger.info("Successfully obtained IsThereAnyDeal access token")
            return self._token

        except Exception as e:
            logger.error(f"Error obtaining IsThereAnyDeal access token: {e}")
            raise


    async def _get_json_with_auth(
        self, 
        url: str, 
        *, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make authenticated GET request to IsThereAnyDeal API.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response data
        """
        # Get access token
        token = await self._get_access_token()

        # Add authorization header
        headers = {
            "Authorization": f"Bearer {token}",
        }

        return await self._get_json(url, params=params, headers=headers)

    async def search_game(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for a game by title in IsThereAnyDeal database.
        
        Args:
            title: Game title to search for
            
        Returns:
            Game information including ITAD ID, or None if not found
        """
        logger.info(f"Searching for game: {title}")

        # Use search endpoint instead of lookup
        search_url = f"{self.base_url}/games/search/v1"
        params = {
            "key": self.api_key,
            "title": title,
            "results": 1  # Only get the best match
        }

        try:
            data = await self._get_json(search_url, params=params)
            
            # Search returns an array of results
            if data and isinstance(data, list) and len(data) > 0:
                game = data[0]  # Get first result (best match)
                logger.debug(f"Found game: {game.get('title')} (ID: {game.get('id')})")
                return game
            
            logger.warning(f"Game not found: {title}")
            return None

        except Exception as e:
            logger.error(f"Error searching for game {title}: {e}")
            return None

    async def get_game_info_by_steam_id(self, steam_appid: int) -> Optional[Dict[str, Any]]:
        """
        Get game information from IsThereAnyDeal using Steam AppID.
        
        Args:
            steam_appid: Steam application ID
            
        Returns:
            Game information or None if not found
        """
        logger.info(f"Getting game info for Steam AppID: {steam_appid}")

        info_url = f"{self.base_url}/games/info/v2"
        params = {
            "key": self.api_key,
            "id": f"app/{steam_appid}",  # Use Steam ID format
        }

        try:
            data = await self._get_json(info_url, params=params)
            
            if data:
                logger.debug(f"Retrieved info for Steam AppID {steam_appid}")
                return data
            
            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Game not found for Steam AppID {steam_appid}")
                return None
            logger.error(f"HTTP error getting game info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting game info for Steam AppID {steam_appid}: {e}")
            return None

    async def get_game_prices(self, steam_appid: int) -> Optional[GamePrice]:
        """
        Get current price information for a game from multiple stores.
        
        Args:
            steam_appid: Steam application ID
            
        Returns:
            GamePrice object with best deal information, or None if not found
        """
        logger.info(f"Getting prices for Steam AppID: {steam_appid}")

        # Step 1: Lookup ITAD ID using Steam AppID
        lookup_url = f"{self.base_url}/games/lookup/v1"
        params = {
            "key": self.api_key,
            "appid": steam_appid
        }

        try:
            # Lookup game
            lookup_data = await self._get_json(lookup_url, params=params)

            if not lookup_data or "game" not in lookup_data:
                logger.warning(f"Game not found for Steam AppID {steam_appid}")
                return None

            game_info = lookup_data["game"]
            itad_id = game_info.get("id")

            if not itad_id:
                logger.warning(f"No ITAD ID found for Steam AppID {steam_appid}")
                return None

            # Step 2: Get prices using ITAD ID - POST /games/prices/v3
            prices_url = f"{self.base_url}/games/prices/v3"

            response = await self._client.post(
                prices_url,
                json=[itad_id],  # Array with single game ID
                params={
                    "key": self.api_key,
                    "country": "PL",  # Poland - for PLN currency
                    "shops": "61,35,88,82"  # Steam, GOG, Epic, Humble Bundle (comma-separated)
                    # Don't use deals=true filter, we'll filter on client side
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                logger.info(f"No price data for Steam AppID {steam_appid}")
                return None

            game_data = data[0]
            deals = game_data.get("deals", [])

            if not deals:
                logger.info(f"No prices available for Steam AppID {steam_appid}")
                return None

            # Filter deals to only those with actual discounts (cut > 0)
            discounted_deals = [d for d in deals if d.get("cut", 0) > 0]

            if not discounted_deals:
                logger.info(f"No active discounts for Steam AppID {steam_appid}")
                return None

            # Find the best deal (highest discount, then lowest price)
            best_deal = max(discounted_deals, key=lambda d: (
                d.get("cut", 0),
                -d.get("price", {}).get("amount", float('inf'))
            ))

            price_info = best_deal.get("price", {})
            regular_info = best_deal.get("regular", {})
            discount = best_deal.get("cut", 0)

            return GamePrice(
                steam_appid=steam_appid,
                game_title=game_info.get("title", "Unknown"),
                store_name=best_deal.get("shop", {}).get("name", "Unknown Store"),
                store_url=best_deal.get("url", ""),
                current_price=price_info.get("amount", 0.0),
                regular_price=regular_info.get("amount", 0.0),
                discount_percent=discount,
                currency=price_info.get("currency", "USD"),
                drm=best_deal.get("drm", [{}])[0].get("name", "Unknown") if best_deal.get("drm") else "Unknown",
            )

        except Exception as e:
            logger.error(f"Error getting prices for Steam AppID {steam_appid}: {e}")
            return None

    async def lookup_steam_appids(self, steam_appids: List[int]) -> Dict[int, str]:
        """
        Convert Steam AppIDs to IsThereAnyDeal game IDs (UUIDs).

        Args:
            steam_appids: List of Steam application IDs

        Returns:
            Dictionary mapping Steam AppID to ITAD game ID (UUID)
        """
        logger.info(f"Looking up ITAD IDs for {len(steam_appids)} Steam AppIDs")

        if not steam_appids:
            return {}

        # Use batch lookup endpoint - POST /lookup/id/shop/{shopId}/v1
        # Steam shop ID is 61
        lookup_url = f"{self.base_url}/lookup/id/shop/61/v1"

        # Convert AppIDs to shop format (app/123)
        shop_ids = [f"app/{appid}" for appid in steam_appids]

        result = {}

        try:
            # Make POST request with shop IDs in body
            response = await self._client.post(
                lookup_url,
                json=shop_ids[:500],  # Max 500 at a time (no explicit limit in docs, being safe)
                params={"key": self.api_key} if self.api_key else {}
            )
            response.raise_for_status()
            data = response.json()

            # Response format: {"app/123": "uuid-here", "app/456": "uuid-here"}
            for shop_id, itad_id in data.items():
                if itad_id and shop_id.startswith("app/"):
                    try:
                        appid = int(shop_id.replace("app/", ""))
                        result[appid] = itad_id
                    except ValueError:
                        continue

            logger.info(f"Successfully looked up {len(result)} games")
            return result

        except Exception as e:
            logger.error(f"Error looking up Steam AppIDs: {e}")
            return {}

    async def get_game_prices_batch(
        self,
        steam_appids: List[int],
        game_names: Optional[Dict[int, str]] = None
    ) -> Dict[int, Optional[GamePrice]]:
        """
        Get current price information for multiple games at once.

        Args:
            steam_appids: List of Steam application IDs
            game_names: Optional dictionary mapping appid to game name (for populating titles)

        Returns:
            Dictionary mapping appid to GamePrice (or None if no deal found)
        """
        logger.info(f"Getting prices for {len(steam_appids)} games")

        if not steam_appids:
            return {}

        # Step 1: Convert Steam AppIDs to ITAD IDs
        appid_to_itad = await self.lookup_steam_appids(steam_appids)

        if not appid_to_itad:
            logger.warning("No games found in ITAD database")
            return {}

        # Step 2: Get prices using ITAD IDs - POST /games/prices/v3
        prices_url = f"{self.base_url}/games/prices/v3"

        # Prepare ITAD IDs list
        itad_ids = list(appid_to_itad.values())

        # Create reverse mapping (ITAD ID -> AppID)
        itad_to_appid = {v: k for k, v in appid_to_itad.items()}

        result = {}

        try:
            # Make POST request with ITAD IDs in body
            response = await self._client.post(
                prices_url,
                json=itad_ids[:200],  # Max 200 games per request
                params={
                    "key": self.api_key,
                    "country": "PL",
                    "shops": "61,35,88,82"  # Steam, GOG, Epic, Humble Bundle (comma-separated string)
                    # Don't use deals=true, we'll filter on client side
                }
            )
            response.raise_for_status()
            data = response.json()

            # Response is array of game data
            for game_data in data:
                itad_id = game_data.get("id")
                if not itad_id or itad_id not in itad_to_appid:
                    continue

                appid = itad_to_appid[itad_id]

                # Get list of deals
                deals = game_data.get("deals", [])
                if not deals:
                    result[appid] = None
                    continue

                # Filter to only deals with actual discounts (cut > 0)
                discounted_deals = [d for d in deals if d.get("cut", 0) > 0]

                if not discounted_deals:
                    result[appid] = None
                    continue

                # Find the best deal (highest discount, then lowest price)
                best_deal = max(discounted_deals, key=lambda d: (
                    d.get("cut", 0),  # Discount percentage
                    -d.get("price", {}).get("amount", float('inf'))  # Negative price for sorting
                ))

                price_info = best_deal.get("price", {})
                regular_info = best_deal.get("regular", {})

                current_price = price_info.get("amount", 0.0)
                regular_price = regular_info.get("amount", 0.0)
                discount = best_deal.get("cut", 0)  # Already calculated by API

                # Double-check discount is significant (should be caught by filter above)
                if discount < 1:  # Less than 1% discount
                    result[appid] = None
                    continue

                # Get game title from provided mapping, fallback to API data, then "Unknown"
                game_title = "Unknown"
                if game_names and appid in game_names:
                    game_title = game_names[appid]
                elif "title" in game_data:
                    game_title = game_data["title"]

                price = GamePrice(
                    steam_appid=appid,
                    game_title=game_title,
                    store_name=best_deal.get("shop", {}).get("name", "Unknown Store"),
                    store_url=best_deal.get("url", ""),
                    current_price=current_price,
                    regular_price=regular_price,
                    discount_percent=discount,
                    currency=price_info.get("currency", "USD"),
                    drm=best_deal.get("drm", [{}])[0].get("name", "Unknown") if best_deal.get("drm") else "Unknown",
                )

                # Store the price directly (no conversion)
                result[appid] = price

        except Exception as e:
            logger.error(f"Error getting prices batch: {e}")

        return result

    async def get_best_deals(
        self,
        limit: int = 20,
        min_discount: int = 20,
        game_appids: Optional[List[int]] = None,
        game_names: Optional[Dict[int, str]] = None
    ) -> List[DealInfo]:
        """
        Get best current deals from IsThereAnyDeal.

        Note: IsThereAnyDeal API v2 requires game IDs to check prices.
        This method needs a list of game AppIDs to check (typically from database watchlist).

        Args:
            limit: Maximum number of deals to return (default: 20)
            min_discount: Minimum discount percentage (default: 20)
            game_appids: List of Steam AppIDs to check for deals (required)
            game_names: Optional dictionary mapping appid to game name (for display)

        Returns:
            List of DealInfo objects with best current deals
        """
        if not game_appids:
            logger.warning("No game AppIDs provided, cannot fetch deals")
            return []

        logger.info(f"Fetching best deals for {len(game_appids)} games (limit={limit}, min_discount={min_discount}%)")

        try:

            # Get prices for all games in batch
            prices = await self.get_game_prices_batch(game_appids, game_names)

            # Filter to only include games with deals meeting minimum discount
            deal_objects = []
            for appid, price in prices.items():
                if price and price.discount_percent >= min_discount:
                    deal_info = DealInfo(
                        steam_appid=price.steam_appid,
                        game_title=price.game_title,
                        store_name=price.store_name,
                        store_url=price.store_url,
                        current_price=price.current_price,
                        regular_price=price.regular_price,
                        discount_percent=price.discount_percent,
                        currency=price.currency,
                        drm=price.drm,
                    )
                    deal_objects.append(deal_info)

            # Sort by discount percentage (highest first)
            deal_objects.sort(key=lambda d: d.discount_percent, reverse=True)

            # Limit results
            result = deal_objects[:limit]

            logger.info(f"Found {len(result)} deals meeting criteria")
            return result

        except Exception as e:
            logger.error(f"Error fetching best deals: {e}")
            return []


# For testing
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def test():
        async with IsThereAnyDealClient() as client:
            # Test getting best deals
            print("=== Testing Best Deals ===")
            deals = await client.get_best_deals(limit=10, min_discount=30)
            for deal in deals:
                print(f"{deal.game_title}: ${deal.current_price} "
                      f"(was ${deal.regular_price}, -{deal.discount_percent}%) "
                      f"at {deal.store_name}")

            # Test getting game prices
            print("\n=== Testing Game Prices (Counter-Strike 2) ===")
            cs2_appid = 730
            prices = await client.get_game_prices(cs2_appid)
            if prices:
                print(f"Best deal: {prices.store_name} - ${prices.current_price} "
                      f"(-{prices.discount_percent}%)")
            else:
                print("No prices found")

    asyncio.run(test())
