# services/deals_api.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Import bazowej klasy za pomocą względnej ścieżki (POPRAWNY DLA TEJ STRUKTURY)
from common._base_http import BaseAsyncService


class Deal(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    title: str = Field(default='', description="The title of the game or product on sale")
    steamAppID: Optional[int] = Field(default=-1, description="Unique identifier for the game or product")
    salePrice: float = Field(default=0.0, description="The current sale price of the game or product")
    normalPrice: Optional[float] = Field(default=None, description="The original price before the discount")
    dealID: Optional[str] = Field(default=None, description="Unique identifier for the deal")


class IDealsApi(ABC):
    @abstractmethod
    async def get_current_deals(self, limit: int = 50, min_discount: int = 30) -> List[Deal]: ...

    @abstractmethod
    async def get_deals_for_title(self, title: str, limit: int = 50) -> List[Deal]: ...

    @abstractmethod
    async def get_deal_by_id(self, deal_id: str) -> Optional[Deal]: ...


class DealsApiClient(BaseAsyncService, IDealsApi):
    BASE_URL = "https://www.cheapshark.com/api/1.0"

    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout) if timeout is not None else super().__init__()

    async def get_current_deals(self, limit: int = 50, min_discount: int = 30) -> List[Deal]:
        url = f"{self.BASE_URL}/deals"
        params = {
            "onSale": 1,
            "pageSize": max(1, min(500, int(limit))),
            "sortBy": "Savings",
        }
        data = await self._get_json(url, params=params)
        deals: List[Deal] = []
        for d in data or []:
            savings = float(d.get("savings") or 0.0)
            if savings < float(min_discount):
                continue
            steam_app_id = d.get("steamAppID")
            try:
                steam_app_id_int = int(steam_app_id) if steam_app_id is not None else -1
            except ValueError:
                steam_app_id_int = -1
            deals.append(
                Deal(
                    title=d.get("title", ""),
                    steamAppID=steam_app_id_int,
                    salePrice=float(d.get("salePrice") or 0.0),
                    normalPrice=float(d.get("normalPrice")) if d.get("normalPrice") is not None else None,
                    dealID=d.get("dealID"),
                )
            )
        return deals

    async def get_deals_for_title(self, title: str, limit: int = 50) -> List[Deal]:
        url = f"{self.BASE_URL}/deals"
        params = {
            "title": title,
            "pageSize": max(1, min(500, int(limit))),
        }
        data = await self._get_json(url, params=params)
        deals: List[Deal] = []
        for d in data or []:
            steam_app_id = d.get("steamAppID")
            try:
                steam_app_id_int = int(steam_app_id) if steam_app_id is not None else -1
            except ValueError:
                steam_app_id_int = -1
            deals.append(
                Deal(
                    title=d.get("title", ""),
                    steamAppID=steam_app_id_int,
                    salePrice=float(d.get("salePrice") or 0.0),
                    normalPrice=float(d.get("normalPrice")) if d.get("normalPrice") is not None else None,
                    dealID=d.get("dealID"),
                )
            )
        return deals

    async def get_deal_by_id(self, deal_id: str) -> Optional[Deal]:
        url = f"{self.BASE_URL}/deals"
        data = await self._get_json(url, params={"id": deal_id})
        if not data:
            return None
        game_info = data.get("gameInfo", {})
        if not game_info:
            return None
        try:
            steam_app_id_int = int(game_info.get("steamAppID")) if game_info.get("steamAppID") is not None else -1
        except ValueError:
            steam_app_id_int = -1
        normal_price = game_info.get("retailPrice")
        sale_price = data.get("cheapestPrice", {}).get("price") or game_info.get("salePrice")
        return Deal(
            title=game_info.get("name", ""),
            steamAppID=steam_app_id_int,
            salePrice=float(sale_price) if sale_price is not None else 0.0,
            normalPrice=float(normal_price) if normal_price is not None else None,
            dealID=deal_id,
        )


if __name__ == "__main__":
    import asyncio

    async def demo() -> None:
        async with DealsApiClient() as client:
            top = await client.get_current_deals(limit=10, min_discount=30)
            print(f"Current deals ({len(top)}) sample:", [d.title for d in top[:3]])

            title_deals = await client.get_deals_for_title("Elden Ring", limit=5)
            print(f"Deals for title ({len(title_deals)}) sample:", [d.title for d in title_deals[:3]])

            if title_deals and title_deals[0].dealID:
                d = await client.get_deal_by_id(title_deals[0].dealID or "")
                print("Deal by id sample:", d)

    asyncio.run(demo())
