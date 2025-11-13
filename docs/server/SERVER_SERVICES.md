# Dokumentacja Serwisów

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [SteamClient](#steamclient)
3. [IsThereAnyDealClient](#isthereanydeaclient)
4. [BaseAsyncService](#baseasyncservice)
5. [Parse HTML](#parse-html)

---

## Przegląd

Serwisy to moduły odpowiedzialne za komunikację z zewnętrznymi API.

**Struktura:**
```
server/services/
├── _base_http.py          # Bazowa klasa HTTP
├── steam_service.py       # Steam API client
├── deals_service.py       # IsThereAnyDeal client
├── parse_html.py          # Parser HTML
└── models.py              # Modele Pydantic
```

---

## SteamClient

**Plik:** `server/services/steam_service.py`

### Klasa SteamClient

Klient do komunikacji z Steam API (Store API + Web API).

```python
class SteamClient(BaseAsyncService):
    """
    Klient Steam API z retry logic i rate limiting.
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://api.steampowered.com",
            timeout=30.0,
            rate_limit_calls=20,
            rate_limit_period=60.0
        )
        self.api_key = os.getenv("STEAM_API_KEY", "")
```

### Metody

#### 1. **get_player_counts_batch** - Liczby graczy (batch)

```python
async def get_player_counts_batch(self, appids: List[int]) -> Dict[int, int]:
    """
    Pobiera aktualną liczbę graczy dla wielu gier.
    
    Args:
        appids: Lista Steam Application IDs
        
    Returns:
        {appid: player_count, ...}
        
    Example:
        counts = await client.get_player_counts_batch([730, 570, 440])
        # {730: 1000000, 570: 500000, 440: 50000}
    """
    tasks = [self.get_current_players(appid) for appid in appids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    player_data = {}
    for appid, result in zip(appids, results):
        if isinstance(result, int):
            player_data[appid] = result
        else:
            logger.warning(f"Failed to get player count for {appid}: {result}")
    
    return player_data
```

#### 2. **get_current_players** - Liczba graczy (pojedyncza gra)

```python
async def get_current_players(self, appid: int) -> int:
    """
    Pobiera aktualną liczbę graczy dla gry.
    
    Endpoint: https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/
    """
    try:
        response = await self.get(
            "/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
            params={"appid": appid}
        )
        return response["response"]["player_count"]
    except Exception as e:
        logger.error(f"Error getting player count for {appid}: {e}")
        return 0
```

#### 3. **get_player_owned_games** - Posiadane gry użytkownika

```python
async def get_player_owned_games(self, steamid: str) -> List[OwnedGame]:
    """
    Pobiera listę posiadanych gier użytkownika.
    
    Endpoint: IPlayerService/GetOwnedGames/v1/
    Wymaga: STEAM_API_KEY
    
    Returns:
        Lista modeli OwnedGame
    """
    if not self.api_key:
        raise ValueError("STEAM_API_KEY not configured")
    
    response = await self.get(
        "/IPlayerService/GetOwnedGames/v1/",
        params={
            "steamid": steamid,
            "key": self.api_key,
            "include_appinfo": 1,
            "include_played_free_games": 1
        }
    )
    
    games = response.get("response", {}).get("games", [])
    return [OwnedGame(**game) for game in games]
```

#### 4. **get_recently_played_games** - Ostatnio grane

```python
async def get_recently_played_games(self, steamid: str) -> List[RecentGame]:
    """
    Pobiera ostatnio grane gry użytkownika (ostatnie 2 tygodnie).
    
    Endpoint: IPlayerService/GetRecentlyPlayedGames/v1/
    Wymaga: STEAM_API_KEY
    """
    if not self.api_key:
        raise ValueError("STEAM_API_KEY not configured")
    
    response = await self.get(
        "/IPlayerService/GetRecentlyPlayedGames/v1/",
        params={"steamid": steamid, "key": self.api_key}
    )
    
    games = response.get("response", {}).get("games", [])
    return [RecentGame(**game) for game in games]
```

#### 5. **get_player_summary** - Podsumowanie profilu

```python
async def get_player_summary(self, steamid: str) -> Dict:
    """
    Pobiera podsumowanie profilu Steam użytkownika.
    
    Endpoint: ISteamUser/GetPlayerSummaries/v2/
    Wymaga: STEAM_API_KEY
    """
    if not self.api_key:
        raise ValueError("STEAM_API_KEY not configured")
    
    response = await self.get(
        "/ISteamUser/GetPlayerSummaries/v2/",
        params={"steamids": steamid, "key": self.api_key}
    )
    
    players = response.get("response", {}).get("players", [])
    return players[0] if players else {}
```

#### 6. **resolve_vanity_url** - Rozwiązanie vanity URL

```python
async def resolve_vanity_url(self, vanity_url: str) -> Optional[str]:
    """
    Rozwiązuje vanity URL na Steam ID64.
    
    Args:
        vanity_url: 
            - "gaben"
            - "my_custom_name"
            - "https://steamcommunity.com/id/gaben"
    
    Returns:
        Steam ID64 lub None
    """
    # Wyodrębnij nazwę z URL
    vanity_name = vanity_url.split("/")[-1].strip()
    
    if not self.api_key:
        raise ValueError("STEAM_API_KEY not configured")
    
    response = await self.get(
        "/ISteamUser/ResolveVanityURL/v1/",
        params={"vanityurl": vanity_name, "key": self.api_key}
    )
    
    if response.get("response", {}).get("success") == 1:
        return response["response"]["steamid"]
    
    return None
```

#### 7. **get_coming_soon_games** - Nadchodzące premiery

```python
async def get_coming_soon_games(self, limit: int = 20) -> List[UpcomingGame]:
    """
    Pobiera nadchodzące premiery gier ze Steam Store.
    
    Używa HTML parsingu (steamcommunity.com/releases)
    
    Returns:
        Lista modeli UpcomingGame
    """
    url = "https://steamcommunity.com/games/upcoming"
    
    async with self.session.get(url) as response:
        html = await response.text()
    
    # Parse HTML
    games = parse_upcoming_games(html, limit=limit)
    return [UpcomingGame(**game) for game in games]
```

#### 8. **get_top_games_by_players** - Top gry (Steam Charts)

```python
async def get_top_games_by_players(self, limit: int = 100) -> List[Dict]:
    """
    Pobiera top gry według liczby graczy.
    
    Używa HTML parsingu (steamcharts.com)
    
    Returns:
        [
            {
                "appid": 730,
                "name": "Counter-Strike 2",
                "player_count": 1000000
            },
            ...
        ]
    """
    url = "https://steamcharts.com"
    
    async with self.session.get(url) as response:
        html = await response.text()
    
    games = parse_top_games(html, limit=limit)
    return games
```

---

## IsThereAnyDealClient

**Plik:** `server/services/deals_service.py`

### Klasa IsThereAnyDealClient

Klient do IsThereAnyDeal API (promocje gier).

```python
class IsThereAnyDealClient(BaseAsyncService):
    """
    Klient IsThereAnyDeal API.
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://api.isthereanydeal.com",
            timeout=30.0
        )
        self.client_id = os.getenv("ITAD_CLIENT_ID", "")
        self.client_secret = os.getenv("ITAD_CLIENT_SECRET", "")
```

### Metody

#### 1. **get_best_deals** - Najlepsze promocje

```python
async def get_best_deals(self, limit: int = 20) -> List[Dict]:
    """
    Pobiera najlepsze promocje na gry.
    
    Args:
        limit: Maksymalna liczba wyników
        
    Returns:
        [
            {
                "title": "Game Name",
                "normal_price": "$29.99",
                "sale_price": "$9.99",
                "savings": "67%",
                "store": "Steam",
                "url": "https://..."
            },
            ...
        ]
    """
    if not self.client_id:
        raise ValueError("ITAD_CLIENT_ID not configured")
    
    response = await self.get(
        "/v1/deals/list",
        params={
            "key": self.client_id,
            "limit": limit,
            "sort": "price:asc"
        }
    )
    
    deals = response.get("data", {}).get("list", [])
    return deals[:limit]
```

---

## BaseAsyncService

**Plik:** `server/services/_base_http.py`

### Klasa Bazowa

Bazowa klasa dla wszystkich klientów HTTP z retry logic i rate limiting.

```python
class BaseAsyncService:
    """
    Bazowa klasa dla asynchronicznych klientów HTTP.
    
    Features:
    - Connection pooling (httpx.AsyncClient)
    - Retry logic (tenacity)
    - Rate limiting
    - Timeout handling
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        rate_limit_calls: int = 20,
        rate_limit_period: float = 60.0
    ):
        self.base_url = base_url
        self.timeout = timeout
        
        # HTTP/2 client
        self.session = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            http2=True,
            limits=httpx.Limits(max_keepalive_connections=20)
        )
        
        # Rate limiting
        self._rate_limiter = AsyncLimiter(rate_limit_calls, rate_limit_period)
```

### Metody

#### GET Request z Retry

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
)
async def get(self, path: str, params: Dict = None) -> Dict:
    """
    Wykonuje GET request z retry logic.
    
    Retry strategy:
    - 3 próby
    - Exponential backoff (2s, 4s, 8s)
    - Tylko dla timeout/network errors
    """
    async with self._rate_limiter:
        response = await self.session.get(path, params=params)
        response.raise_for_status()
        return response.json()
```

---

## Parse HTML

**Plik:** `server/services/parse_html.py`

### Funkcje Parsowania

#### 1. **parse_upcoming_games** - Parser nadchodzących gier

```python
def parse_upcoming_games(html: str, limit: int = 20) -> List[Dict]:
    """
    Parsuje HTML z Steam /games/upcoming.
    
    Returns:
        [
            {
                "appid": 123456,
                "name": "Game Name",
                "release_date": "2025-12-01",
                "header_image": "https://...",
                "short_description": "..."
            }
        ]
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    games = []
    
    for item in soup.select('.upcoming_game_item')[:limit]:
        # Extract data...
        games.append({
            "appid": extract_appid(item),
            "name": item.select_one('.game_name').text,
            ...
        })
    
    return games
```

#### 2. **parse_top_games** - Parser top gier

```python
def parse_top_games(html: str, limit: int = 100) -> List[Dict]:
    """
    Parsuje HTML ze SteamCharts.
    
    Returns:
        [
            {
                "appid": 730,
                "name": "Counter-Strike 2",
                "player_count": 1000000
            }
        ]
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    games = []
    
    for row in soup.select('tr.game-row')[:limit]:
        # Extract data...
        games.append({
            "appid": extract_appid(row),
            "name": row.select_one('.game-name').text,
            "player_count": int(row.select_one('.current-players').text)
        })
    
    return games
```

---

## Modele Pydantic

**Plik:** `server/services/models.py`

### OwnedGame

```python
class OwnedGame(BaseModel):
    """Posiadana gra użytkownika."""
    appid: int
    name: Optional[str] = None
    playtime_forever: int = 0  # minuty
    playtime_2weeks: Optional[int] = None  # minuty
    img_icon_url: Optional[str] = None
    img_logo_url: Optional[str] = None
```

### RecentGame

```python
class RecentGame(BaseModel):
    """Ostatnio grana gra."""
    appid: int
    name: str
    playtime_2weeks: int  # minuty
    playtime_forever: int  # minuty
    img_icon_url: Optional[str] = None
    img_logo_url: Optional[str] = None
```

### UpcomingGame

```python
class UpcomingGame(BaseModel):
    """Nadchodząca premiera."""
    appid: int
    name: str
    release_date: str
    header_image: Optional[str] = None
    short_description: Optional[str] = None
```

---

## Podsumowanie

| Serwis | API | Funkcjonalności |
|--------|-----|-----------------|
| **SteamClient** | Steam Web API + Store | Liczby graczy, biblioteka, profile, premiery |
| **IsThereAnyDealClient** | ITAD API | Promocje gier |
| **BaseAsyncService** | - | Retry logic, rate limiting, HTTP/2 |

---

## Następne Kroki

- **Validation**: [SERVER_VALIDATION.md](SERVER_VALIDATION.md)
- **API Endpoints**: [SERVER_API_ENDPOINTS.md](SERVER_API_ENDPOINTS.md)

