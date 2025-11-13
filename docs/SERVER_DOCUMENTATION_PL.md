# Dokumentacja Serwera - Custom Steam Dashboard

> **⚠️ UWAGA:** Ta dokumentacja jest przestarzała i została zastąpiona nowymi, szczegółowymi dokumentami.
>
> **Przejdź do nowej dokumentacji:** [server/SERVER_OVERVIEW.md](server/SERVER_OVERVIEW.md)

---

## 📚 Nowa Struktura Dokumentacji

Dokumentacja serwera została podzielona na tematyczne moduły dla lepszej organizacji:

### Główne Dokumenty

| Dokument | Opis | Link |
|----------|------|------|
| **📖 Przegląd Serwera** | Quick start, architektura, konfiguracja | [SERVER_OVERVIEW.md](server/SERVER_OVERVIEW.md) |
| **🔌 API Endpoints** | Wszystkie endpointy z przykładami | [SERVER_API_ENDPOINTS.md](server/SERVER_API_ENDPOINTS.md) |
| **🔐 Bezpieczeństwo** | JWT + HMAC, middleware, rate limiting | [SERVER_SECURITY.md](server/SERVER_SECURITY.md) |
| **🗄️ Baza Danych** | PostgreSQL, tabele, operacje | [SERVER_DATABASE.md](server/SERVER_DATABASE.md) |
| **⏰ Scheduler** | Zadania cykliczne, APScheduler | [SERVER_SCHEDULER.md](server/SERVER_SCHEDULER.md) |
| **🎮 Serwisy** | Steam API, ITAD, HTTP client | [SERVER_SERVICES.md](server/SERVER_SERVICES.md) |
| **✅ Walidacja** | Pydantic validators, obsługa błędów | [SERVER_VALIDATION.md](server/SERVER_VALIDATION.md) |

---

## 🚀 Quick Start

Zamiast czytać ten przestarzały dokument, zacznij od:

1. **[SERVER_OVERVIEW.md](server/SERVER_OVERVIEW.md)** - Przegląd i quick start
2. **[SERVER_API_ENDPOINTS.md](server/SERVER_API_ENDPOINTS.md)** - Poznaj dostępne endpointy
3. **[SERVER_SECURITY.md](server/SERVER_SECURITY.md)** - Zrozum system bezpieczeństwa

---

## 📋 Co się zmieniło od ostatniej aktualizacji?

### Dodano:
- ✅ **Uwierzytelnianie JWT + HMAC** - Dwuwarstwowe bezpieczeństwo
- ✅ **Rate Limiting** - Ochrona przed nadmiernym obciążeniem (slowapi)
- ✅ **Middleware weryfikacji** - Automatyczna weryfikacja podpisów
- ✅ **IsThereAnyDeal API** - Promocje gier (zamiast CheapShark)
- ✅ **Agregacja danych** - Godzinowa i dzienna archiwizacja
- ✅ **Timezone UTC** - Wszystkie operacje w UTC
- ✅ **Walidacja Pydantic** - Wszystkie endpointy z walidacją
- ✅ **Connection pooling** - asyncpg z pool management

### Zmieniono:
- 🔄 **Struktura bazy** - Dodano tabele `game_genres`, `game_categories`, `watchlist`
- 🔄 **Scheduler** - Dodano agregację godzinową/dzienną
- 🔄 **CORS** - Zaktualizowano konfigurację (nie tylko localhost)
- 🔄 **Endpointy** - Wszystkie `/api/*` wymagają JWT + HMAC

### Usunięto:
- ❌ **CheapShark API** - Zastąpione przez IsThereAnyDeal
- ❌ **Niezabezpieczone endpointy** - Wszystkie wymagają autoryzacji

---

## 🔗 Powiązana Dokumentacja

- **Autoryzacja**: [AUTH_AND_SIGNING_README.md](AUTH_AND_SIGNING_README.md)
- **JWT System**: [JWT_OVERVIEW.md](JWT_OVERVIEW.md)
- **Rate Limiting**: [RATE_LIMITING_VALIDATION.md](RATE_LIMITING_VALIDATION.md)
- **Bezpieczeństwo**: [PROPOZYCJE_ZABEZPIECZEN.md](PROPOZYCJE_ZABEZPIECZEN.md)

---

## 📝 Stara Dokumentacja (Archiwum)

<details>
<summary>Kliknij, aby zobaczyć przestarzałą treść (tylko do referencji)</summary>

### Przegląd Struktury

Serwer Custom Steam Dashboard to backend oparty na FastAPI, który zapewnia:
- REST API dla aplikacji klienckiej
- Automatyczne zbieranie danych o liczbie graczy ze Steam API
- Zarządzanie bazą danych PostgreSQL
- Scheduler do wykonywania zadań cyklicznych

### Struktura Katalogów

```
server/
├── __init__.py
├── app.py                      # Główna aplikacja FastAPI
├── scheduler.py                # Zarządzanie zadaniami cyklicznymi
├── README.md                   # Dokumentacja podstawowa
├── test_scheduler.py           # Testy schedulera
├── test_seed_watchlist.py      # Testy seedowania watchlist
├── database/
│   ├── __init__.py
│   └── database.py             # Zarządzanie bazą danych PostgreSQL
└── services/
    ├── __init__.py
    ├── models.py               # Modele danych Pydantic
    └── steam_service.py        # Klient Steam API

common/                          # Moduł współdzielony
├── __init__.py
├── _base_http.py               # Bazowy klient HTTP
└── parse_html.py               # Parsowanie HTML
```

---

## Środowisko i Konfiguracja

### Wymagania Systemowe

- **Python**: 3.11+
- **PostgreSQL**: 13+ (lub Neon.tech)
- **System operacyjny**: Linux, macOS, Windows

### Zależności

Pełna lista zależności znajduje się w `requirements.txt`:

#### Kluczowe Biblioteki:
- **FastAPI** (≥0.115) - Framework REST API
- **Uvicorn** (≥0.32) - Serwer ASGI
- **APScheduler** (≥3.10) - Scheduler zadań cyklicznych
- **asyncpg** (≥0.29) - Asynchroniczny driver PostgreSQL
- **httpx[http2]** (≥0.27) - Klient HTTP z obsługą HTTP/2
- **Pydantic** (≥2.7) - Walidacja i serializacja danych
- **tenacity** (≥9.0) - Retry logic dla zapytań HTTP
- **python-dotenv** (≥1.0) - Zarządzanie zmiennymi środowiskowymi

### Zmienne Środowiskowe

Konfiguracja w pliku `.env`:

```env
# PostgreSQL Configuration
PGHOST=localhost              # Host bazy danych
PGPORT=5432                   # Port bazy danych
PGUSER=postgres               # Użytkownik bazy danych
PGPASSWORD=your-password      # Hasło do bazy danych
PGDATABASE=postgres           # Nazwa bazy danych

# Steam API Configuration
STEAM_API_KEY=your-api-key    # Klucz API Steam (opcjonalny dla niektórych endpointów)
STEAM_ID=your-steam-id        # Steam ID użytkownika (do testów)
```

### Uruchomienie Serwera

```bash
# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie serwera
cd server
python app.py

# Lub za pomocą uvicorn bezpośrednio
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Serwer będzie dostępny pod adresem: `http://localhost:8000`
Dokumentacja API (Swagger): `http://localhost:8000/docs`

---

## Moduł Database

Plik: `server/database/database.py`

Moduł zarządzający wszystkimi operacjami na bazie danych PostgreSQL przy użyciu asyncpg.

### Klasa: `DatabaseManager`

Główna klasa zarządzająca połączeniami i operacjami na bazie danych.

#### Konstruktor

```python
def __init__(
    self,
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "password",
    database: str = "postgres",
    schema: str = "custom-steam-dashboard",
    min_pool_size: int = 10,
    max_pool_size: int = 20,
)
```

**Parametry:**
- `host` (str): Host PostgreSQL
- `port` (int): Port PostgreSQL
- `user` (str): Nazwa użytkownika
- `password` (str): Hasło do bazy
- `database` (str): Nazwa bazy danych
- `schema` (str): Nazwa schematu do użycia/stworzenia
- `min_pool_size` (int): Minimalna wielkość puli połączeń
- `max_pool_size` (int): Maksymalna wielkość puli połączeń

#### Metody Inicjalizacyjne

##### `async def initialize(self) -> None`

Inicjalizuje pulę połączeń, tworzy schemat i tabele.

**Funkcjonalność:**
- Tworzy pulę połączeń asyncpg
- Wywołuje `_create_schema()` i `_create_tables()`
- Loguje sukces lub błędy inicjalizacji

**Wyjątki:**
- Podnosi wyjątek przy błędzie połączenia lub tworzenia tabel

##### `async def close(self) -> None`

Zamyka pulę połączeń.

**Funkcjonalność:**
- Zamyka wszystkie aktywne połączenia w puli
- Loguje zamknięcie połączenia

##### `async def _create_schema(self) -> None`

Tworzy schemat jeśli nie istnieje (metoda prywatna).

**Funkcjonalność:**
- Wykonuje `CREATE SCHEMA IF NOT EXISTS`
- Ustawia `search_path` dla schematu

##### `async def _create_tables(self) -> None`

Tworzy wszystkie wymagane tabele (metoda prywatna).

**Funkcjonalność:**
Tworzy następujące tabele:
- `watchlist` - lista obserwowanych gier
- `players_raw_count` - surowe dane o liczbie graczy
- `player_counts_hourly` - agregacje godzinowe
- `player_counts_daily` - agregacje dzienne
- `games` - informacje o grach
- `game_categories` - kategorie gier (many-to-many)
- `game_genres` - gatunki gier (many-to-many)

#### Metody Watchlist

##### `async def upsert_watchlist(self, appid: int, name: str, last_count: int = 0) -> None`

Dodaje lub aktualizuje grę w watchlist.

**Parametry:**
- `appid` (int): Steam App ID
- `name` (str): Nazwa gry
- `last_count` (int): Ostatnia zapisana liczba graczy (domyślnie 0)

**Funkcjonalność:**
- Wstawia nowy rekord lub aktualizuje `last_count` jeśli gra już istnieje
- Używa `ON CONFLICT` dla upsert

##### `async def remove_from_watchlist(self, appid: int) -> None`

Usuwa grę z watchlist.

**Parametry:**
- `appid` (int): Steam App ID

**Funkcjonalność:**
- Wykonuje `DELETE FROM watchlist WHERE appid = $1`

##### `async def get_watchlist(self) -> List[Dict[str, Any]]`

Pobiera całą watchlist.

**Zwraca:**
- `List[Dict[str, Any]]`: Lista słowników zawierających wpisy watchlist, posortowane po `last_count` DESC

##### `async def seed_watchlist(self, steam_client: 'SteamClient') -> None`

Wypełnia watchlist top 100 najpopularniejszymi grami ze Steam.

**Parametry:**
- `steam_client` (SteamClient): Instancja klienta Steam API

**Funkcjonalność:**
- Sprawdza czy watchlist jest pusta
- Pobiera top 100 gier przez `steam_client.get_most_played_games()`
- Dodaje każdą grę do watchlist
- Loguje postęp i błędy
- Pomija jeśli watchlist już zawiera dane

#### Metody Game

##### `async def upsert_game(self, game_data: 'SteamGameDetails') -> None`

Wstawia lub aktualizuje informacje o grze.

**Parametry:**
- `game_data` (SteamGameDetails): Obiekt z danymi gry

**Funkcjonalność:**
- Wstawia dane gry do tabeli `games`
- Wywołuje `upsert_game_genres()` i `upsert_game_categories()`
- Używa `ON CONFLICT DO NOTHING` dla zapobiegania duplikatom

##### `async def upsert_game_genres(self, appid: int, genres: List[str]) -> None`

Wstawia lub aktualizuje gatunki gry.

**Parametry:**
- `appid` (int): Steam App ID
- `genres` (List[str]): Lista gatunków

**Funkcjonalność:**
- Używa `UNNEST()` dla bulk insert
- Ignoruje duplikaty przez `ON CONFLICT DO NOTHING`

##### `async def upsert_game_categories(self, appid: int, categories: List[str]) -> None`

Wstawia lub aktualizuje kategorie gry.

**Parametry:**
- `appid` (int): Steam App ID
- `categories` (List[str]): Lista kategorii

**Funkcjonalność:**
- Używa `UNNEST()` dla bulk insert
- Ignoruje duplikaty przez `ON CONFLICT DO NOTHING`

##### `async def get_game(self, appid: int) -> Optional[Dict[str, Any]]`

Pobiera szczegóły gry po App ID.

**Parametry:**
- `appid` (int): Steam App ID

**Zwraca:**
- `Optional[Dict[str, Any]]`: Słownik z informacjami o grze lub None

**Funkcjonalność:**
- Wykonuje JOIN z tabelami `game_genres` i `game_categories`
- Agreguje gatunki i kategorie w tablice

##### `async def get_all_games(self) -> List[Dict[str, Any]]`

Pobiera wszystkie gry z bazy.

**Zwraca:**
- `List[Dict[str, Any]]`: Lista słowników z informacjami o grach

##### `async def get_games_filtered_by_genre(self, genre: str) -> List[Dict[str, Any]]`

Pobiera gry filtrowane po gatunku.

**Parametry:**
- `genre` (str): Nazwa gatunku

**Zwraca:**
- `List[Dict[str, Any]]`: Lista gier należących do danego gatunku

##### `async def get_games_filtered_by_category(self, category: str) -> List[Dict[str, Any]]`

Pobiera gry filtrowane po kategorii.

**Parametry:**
- `category` (str): Nazwa kategorii

**Zwraca:**
- `List[Dict[str, Any]]`: Lista gier należących do danej kategorii

#### Metody Player Count

##### `async def insert_player_count(self, appid: int, timestamp: int, count: int) -> None`

Wstawia surowy rekord liczby graczy.

**Parametry:**
- `appid` (int): Steam App ID
- `timestamp` (int): Unix timestamp
- `count` (int): Liczba graczy

**Funkcjonalność:**
- Wstawia rekord do tabeli `players_raw_count`

##### `async def get_player_count_history(self, appid: int, limit: int = 100) -> List[Dict[str, Any]]`

Pobiera historię liczby graczy dla gry.

**Parametry:**
- `appid` (int): Steam App ID
- `limit` (int): Maksymalna liczba rekordów (domyślnie 100)

**Zwraca:**
- `List[Dict[str, Any]]`: Lista rekordów posortowana po timestamp DESC

#### Context Manager

##### `@asynccontextmanager async def acquire(self)`

Context manager do pozyskiwania połączenia z puli.

**Użycie:**
```python
async with db.acquire() as conn:
    await conn.execute(...)
```

**Funkcjonalność:**
- Automatycznie ustawia `search_path` dla schematu
- Zapewnia czysty zwrot połączenia do puli

---

### Klasa: `DatabaseRollupManager`

Zarządza agregacjami danych o liczbie graczy.

#### Konstruktor

```python
def __init__(self, db: DatabaseManager)
```

**Parametry:**
- `db` (DatabaseManager): Instancja DatabaseManager

#### Metody

##### `async def rollup_hourly(self) -> None`

Wykonuje agregację godzinową danych.

**Funkcjonalność:**
- Agreguje dane z `players_raw_count` do `player_counts_hourly`
- Oblicza: średnią, min, max, percentyl 95
- Grupuje po godzinach (Unix timestamp)
- Używa `ON CONFLICT DO NOTHING` dla unikania duplikatów

##### `async def rollup_daily(self) -> None`

Wykonuje agregację dzienną danych.

**Funkcjonalność:**
- Agreguje dane z `players_raw_count` do `player_counts_daily`
- Oblicza: średnią, min, max, percentyl 95
- Grupuje po dniach (format YYYY-MM-DD)
- Używa `ON CONFLICT DO NOTHING` dla unikania duplikatów

##### `async def delete_old_raw_data(self, days: int = 14) -> None`

Usuwa surowe dane starsze niż określona liczba dni.

**Parametry:**
- `days` (int): Liczba dni do zachowania (domyślnie 14)

**Funkcjonalność:**
- Oblicza cutoff timestamp
- Usuwa rekordy z `players_raw_count` starsze niż cutoff

##### `async def delete_hourly_data(self, days: int = 30) -> None`

Usuwa dane godzinowe starsze niż określona liczba dni.

**Parametry:**
- `days` (int): Liczba dni do zachowania (domyślnie 30)

##### `async def delete_daily_data(self, days: int = 90) -> None`

Usuwa dane dzienne starsze niż określona liczba dni.

**Parametry:**
- `days` (int): Liczba dni do zachowania (domyślnie 90)

---

### Funkcje Globalne

##### `async def init_db() -> DatabaseManager`

Inicjalizuje globalną instancję bazy danych.

**Zwraca:**
- `DatabaseManager`: Zainicjalizowana instancja DatabaseManager

**Funkcjonalność:**
- Tworzy instancję `DatabaseManager` z konfiguracją z env
- Wywołuje `initialize()`
- Ustawia globalną zmienną `db`

##### `async def close_db() -> None`

Zamyka globalną instancję bazy danych.

**Funkcjonalność:**
- Wywołuje `close()` na globalnej instancji `db`
- Ustawia `db` na `None`

---

## Moduł Services

### Plik: `server/services/models.py`

Definiuje modele danych używane w całej aplikacji.

#### Klasa: `SteamGameDetails`

Model Pydantic reprezentujący szczegóły gry Steam.

**Pola:**
- `appid` (int): Steam App ID
- `name` (str): Nazwa gry
- `is_free` (bool): Czy gra jest darmowa
- `price` (float): Cena gry (w PLN/USD)
- `detailed_description` (str): Szczegółowy opis gry
- `header_image` (str): URL obrazu nagłówka
- `background_image` (str): URL obrazu tła
- `coming_soon` (bool): Czy gra jest nadchodząca
- `release_date` (str | None): Data wydania
- `categories` (list[str]): Lista kategorii
- `genres` (list[str]): Lista gatunków

**Konfiguracja:**
- `extra="ignore"`: Ignoruje dodatkowe pola
- `populate_by_name=True`: Pozwala na populację przez nazwę pola

#### Klasa: `PlayerCountResponse`

Model odpowiedzi liczby graczy.

**Pola:**
- `appid` (int): Steam App ID
- `player_count` (int): Aktualna liczba graczy

#### Klasa: `SteamPlayerGameOverview`

Model przeglądu gry w bibliotece gracza.

**Pola:**
- `appid` (int): Steam App ID
- `name` (str): Nazwa gry
- `playtime_forever` (int): Całkowity czas gry (w minutach)
- `playtime_2weeks` (int): Czas gry z ostatnich 2 tygodni (w minutach)
- `img_icon_url` (str): URL ikony gry

#### Klasa: `SteamPlayerDetails`

Model szczegółów profilu gracza Steam.

**Pola:**
- `steamid` (str): Steam ID gracza
- `personaname` (str): Nazwa użytkownika
- `profileurl` (str): URL profilu
- `avatar` (str): URL małego avatara
- `avatarfull` (str): URL pełnego avatara

---

### Plik: `server/services/steam_service.py`

Klient API Steam do pobierania danych o grach i graczach.

#### Interfejs: `ISteamService`

Abstrakcyjna klasa bazowa definiująca kontrakt dla Steam Service.

**Metody abstrakcyjne:**
- `async def get_player_count(self, appid: int) -> PlayerCountResponse`
- `async def get_game_details(self, appid: int) -> SteamGameDetails`
- `async def get_coming_soon_games(self) -> list[SteamGameDetails]`
- `async def get_most_played_games(self) -> list[SteamGameDetails]`
- `async def get_player_owned_games(self, steam_id: str) -> list[SteamPlayerGameOverview]`
- `async def get_recently_played_games(self, steam_id: str) -> list[SteamPlayerGameOverview]`
- `async def get_badges(self, steam_id: str) -> dict`
- `async def get_player_summary(self, steam_id: str) -> dict`

#### Klasa: `SteamClient`

Implementacja klienta Steam API.

**Dziedziczenie:**
- `BaseAsyncService` - Zapewnia klient HTTP z retry logic
- `ISteamService` - Implementuje interfejs Steam Service

**Atrybuty:**
- `api_key` (str): Klucz API Steam z zmiennej środowiskowej

#### Konstruktor

```python
def __init__(self, *, timeout: httpx.Timeout | float | None = None)
```

**Parametry:**
- `timeout` (httpx.Timeout | float | None): Niestandardowy timeout dla requestów

#### Metody

##### `async def get_player_count(self, appid: int) -> PlayerCountResponse`

Pobiera aktualną liczbę graczy dla gry.

**Parametry:**
- `appid` (int): Steam App ID

**Zwraca:**
- `PlayerCountResponse`: Obiekt z liczbą graczy

**Endpoint:** `https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/`

**Funkcjonalność:**
- Wysyła request do Steam API
- Parsuje odpowiedź
- Zwraca 0 jeśli nie udało się pobrać danych

##### `async def get_game_details(self, appid: int) -> SteamGameDetails | None`

Pobiera szczegóły gry.

**Parametry:**
- `appid` (int): Steam App ID

**Zwraca:**
- `SteamGameDetails | None`: Obiekt ze szczegółami gry lub None

**Endpoint:** `https://store.steampowered.com/api/appdetails`

**Parametry zapytania:**
- `cc=pln`: Kod kraju (Polska)
- `l=en`: Język (angielski)

**Funkcjonalność:**
- Pobiera pełne dane gry
- Parsuje HTML w opisie przez `parse_html_tags()`
- Konwertuje cenę z groszy na złotówki
- Mapuje kategorie i gatunki

##### `async def get_coming_soon_games(self) -> list[SteamGameDetails]`

Pobiera listę nadchodzących gier.

**Zwraca:**
- `list[SteamGameDetails]`: Lista nadchodzących gier

**Endpoint:** `https://store.steampowered.com/api/featuredcategories/`

**Funkcjonalność:**
- Pobiera featured categories ze Steam
- Wyciąga sekcję `coming_soon`
- Mapuje na `SteamGameDetails`

##### `async def get_most_played_games(self) -> list[SteamGameDetails]`

Pobiera top 100 najpopularniejszych gier.

**Zwraca:**
- `list[SteamGameDetails]`: Lista najpopularniejszych gier

**Endpoint:** `https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/`

**Funkcjonalność:**
- Pobiera ranking gier
- Dla każdej gry wywołuje `get_game_details()` równolegle
- Używa semafora (max 10 równoczesnych requestów)
- Filtruje nieudane requesty

##### `async def get_player_owned_games(self, steam_id: str) -> list[SteamPlayerGameOverview]`

Pobiera bibliotekę gier gracza.

**Parametry:**
- `steam_id` (str): Steam ID gracza

**Zwraca:**
- `list[SteamPlayerGameOverview]`: Lista posiadanych gier

**Endpoint:** `https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/`

**Wymagania:**
- Wymaga `STEAM_API_KEY`

**Parametry zapytania:**
- `include_appinfo=True`: Dołącz informacje o grach
- `include_played_free_games=True`: Dołącz darmowe gry

##### `async def get_recently_played_games(self, steam_id: str) -> list[SteamPlayerGameOverview]`

Pobiera ostatnio grane gry gracza.

**Parametry:**
- `steam_id` (str): Steam ID gracza

**Zwraca:**
- `list[SteamPlayerGameOverview]`: Lista ostatnio granych gier

**Endpoint:** `https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/`

**Wymagania:**
- Wymaga `STEAM_API_KEY`

##### `async def get_badges(self, steam_id: str) -> dict`

Pobiera odznaki gracza.

**Parametry:**
- `steam_id` (str): Steam ID gracza

**Zwraca:**
- `dict`: Surowe dane odznak

**Endpoint:** `https://api.steampowered.com/IPlayerService/GetBadges/v1/`

**Wymagania:**
- Wymaga `STEAM_API_KEY`

**Uwaga:**
- TODO: Mapowanie badge ID na szczegóły odznak

##### `async def get_player_summary(self, steam_id: str) -> dict`

Pobiera podsumowanie profilu gracza.

**Parametry:**
- `steam_id` (str): Steam ID gracza

**Zwraca:**
- `dict`: Dane profilu gracza

**Endpoint:** `https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/`

**Wymagania:**
- Wymaga `STEAM_API_KEY`

---

## Moduł Scheduler

Plik: `server/scheduler.py`

Zarządza zadaniami cyklicznymi aplikacji używając APScheduler.

### Klasa: `PlayerCountCollector`

Zbiera dane o liczbie graczy dla gier w watchlist.

#### Konstruktor

```python
def __init__(self, db: DatabaseManager, steam_client: SteamClient)
```

**Parametry:**
- `db` (DatabaseManager): Instancja zarządcy bazy danych
- `steam_client` (SteamClient): Instancja klienta Steam API

**Atrybuty:**
- `semaphore` (asyncio.Semaphore): Semafor ograniczający do 1 równoczesnego zadania

#### Metody

##### `async def collect_player_counts(self) -> None`

Zbiera liczby graczy dla wszystkich gier w watchlist.

**Wywoływane przez:** Scheduler co 5 minut

**Funkcjonalność:**
- Pobiera watchlist z bazy
- Dla każdej gry:
  - Pobiera aktualną liczbę graczy przez Steam API
  - Zapisuje do `players_raw_count` z timestampem
  - Aktualizuje `last_count` w watchlist
- Wykonuje równolegle (kontrolowane przez semafor)
- Loguje błędy bez przerywania całego procesu

**Obsługa błędów:**
- Catch błędów dla pojedynczych gier
- Kontynuuje dla pozostałych gier

---

### Klasa: `WatchlistRefresher`

Odświeża watchlist periodycznie.

#### Konstruktor

```python
def __init__(self, db: DatabaseManager, steam_client: SteamClient)
```

#### Metody

##### `async def refresh_watchlist(self) -> None`

Odświeża watchlist na podstawie top gier.

**Wywoływane przez:** Scheduler co 1 godzinę

**Funkcjonalność:**
- Pobiera top gry przez `get_most_played_games()`
- Dla każdej gry:
  - Pobiera aktualną liczbę graczy
  - Upsertuje do watchlist
- Pozwala na automatyczne śledzenie popularnych gier

---

### Klasa: `GameDataFiller`

Wypełnia szczegółowe dane gier.

#### Konstruktor

```python
def __init__(self, db: DatabaseManager, steam_client: SteamClient)
```

#### Metody

##### `async def fill_game_data(self) -> None`

Wypełnia dane gier dla watchlist.

**Wywoływane przez:** Scheduler co 1 godzinę i 5 minut

**Funkcjonalność:**
- Pobiera watchlist
- Dla każdej gry:
  - Pobiera szczegóły przez `get_game_details()`
  - Zapisuje do tabeli `games`, `game_genres`, `game_categories`
- Uruchamia się 2 minuty po `refresh_watchlist`

---

### Klasa: `DataCleaner`

Wykonuje agregacje danych (rollup).

#### Konstruktor

```python
def __init__(self, db: DatabaseRollupManager)
```

**Parametry:**
- `db` (DatabaseRollupManager): Instancja zarządcy rollup

#### Metody

##### `async def rollup_hourly_data(self) -> None`

Agreguje dane do formatu godzinowego.

**Wywoływane przez:** Scheduler co 1 godzinę

**Funkcjonalność:**
- Wywołuje `db.rollup_hourly()`
- Redukuje rozmiar surowych danych

##### `async def rollup_daily_data(self) -> None`

Agreguje dane do formatu dziennego.

**Wywoływane przez:** Scheduler co 1 dzień

**Funkcjonalność:**
- Wywołuje `db.rollup_daily()`
- Tworzy statystyki dzienne

---

### Klasa: `DataDeleteOld`

Usuwa stare dane zgodnie z polityką retencji.

#### Konstruktor

```python
def __init__(self, db: DatabaseRollupManager)
```

#### Metody

##### `async def delete_old_hourly_data(self) -> None`

Usuwa stare dane godzinowe.

**Wywoływane przez:** Scheduler co 1 dzień

**Funkcjonalność:**
- Wywołuje `db.delete_hourly_data()`
- Domyślnie: 30 dni retencji

##### `async def delete_old_daily_data(self) -> None`

Usuwa stare dane dzienne.

**Wywoływane przez:** Scheduler co 1 dzień

**Funkcjonalność:**
- Wywołuje `db.delete_daily_data()`
- Domyślnie: 90 dni retencji

---

### Klasa: `SchedulerManager`

Zarządza wszystkimi zaplanowanymi zadaniami.

#### Konstruktor

```python
def __init__(self, db: DatabaseManager | DatabaseRollupManager, steam_client: SteamClient)
```

**Parametry:**
- `db` (DatabaseManager | DatabaseRollupManager): Instancja zarządcy bazy
- `steam_client` (SteamClient): Instancja klienta Steam

**Atrybuty:**
- `scheduler` (AsyncIOScheduler): Instancja schedulera APScheduler
- `player_count_collector` (PlayerCountCollector): Kolektor liczby graczy
- `watchlist_refresher` (WatchlistRefresher): Odświeżacz watchlist
- `game_data_filler` (GameDataFiller): Wypełniacz danych gier
- `data_cleaner` (DataCleaner): Cleaner do rollup
- `data_deleter` (DataDeleteOld): Deleter starych danych

#### Metody

##### `def start(self) -> None`

Uruchamia scheduler i rejestruje wszystkie zadania.

**Zarejestrowane zadania:**

1. **Player Count Collection**
   - ID: `player_count_collection`
   - Częstotliwość: Co 5 minut
   - Funkcja: `collect_player_counts()`
   - Max instances: 1

2. **Watchlist Refresh**
   - ID: `watchlist_refresh`
   - Częstotliwość: Co 1 godzinę
   - Next run: Natychmiast
   - Funkcja: `refresh_watchlist()`
   - Max instances: 1

3. **Game Data Fill**
   - ID: `game_data_fill`
   - Częstotliwość: Co 1 godzinę i 5 minut
   - Next run: Za 2 minuty
   - Funkcja: `fill_game_data()`
   - Max instances: 1

4. **Hourly Rollup**
   - ID: `hourly_data_rollup`
   - Częstotliwość: Co 1 godzinę
   - Funkcja: `rollup_hourly_data()`
   - Max instances: 1

5. **Daily Rollup**
   - ID: `daily_data_rollup`
   - Częstotliwość: Co 1 dzień
   - Funkcja: `rollup_daily_data()`
   - Max instances: 1

6. **Delete Old Hourly Data**
   - ID: `old_hourly_data_deletion`
   - Częstotliwość: Co 1 dzień
   - Funkcja: `delete_old_hourly_data()`
   - Max instances: 1

7. **Delete Old Daily Data**
   - ID: `old_daily_data_deletion`
   - Częstotliwość: Co 1 dzień
   - Funkcja: `delete_old_daily_data()`
   - Max instances: 1

**Funkcjonalność:**
- Konfiguruje wszystkie zadania z triggerami
- Zapobiega równoczesnym instancjom tego samego zadania
- Loguje zarejestrowane zadania i następne czasy uruchomienia

##### `def shutdown(self) -> None`

Wyłącza scheduler.

**Funkcjonalność:**
- Czeka na zakończenie bieżących zadań
- Zamyka scheduler
- Loguje shutdown

##### `async def run_job_now(self, job_id: str) -> None`

Manualnie uruchamia zadanie.

**Parametry:**
- `job_id` (str): ID zadania do uruchomienia

**Funkcjonalność:**
- Znajduje zadanie po ID
- Wywołuje funkcję zadania natychmiast
- Loguje ostrzeżenie jeśli zadanie nie istnieje

---

## Moduł App (FastAPI)

Plik: `server/app.py`

Główna aplikacja FastAPI zapewniająca REST API.

### Zmienne Globalne

- `db` (Optional[DatabaseManager]): Globalna instancja bazy danych
- `steam_client` (Optional[SteamClient]): Globalna instancja klienta Steam
- `scheduler_manager` (Optional[SchedulerManager]): Globalna instancja schedulera

### Funkcja: `lifespan(app: FastAPI)`

Context manager zarządzający lifecycle aplikacji.

**Typ:** `@asynccontextmanager`

**Funkcjonalność (Startup):**
1. Inicjalizuje bazę danych (`init_db()`)
2. Inicjalizuje klienta Steam
3. Seeduje watchlist jeśli pusta
4. Uruchamia scheduler
5. Loguje sukces startu

**Funkcjonalność (Shutdown):**
1. Zatrzymuje scheduler
2. Zamyka klienta Steam
3. Zamyka bazę danych
4. Loguje shutdown

### Instancja: `app`

Główna aplikacja FastAPI.

**Konfiguracja:**
- `title`: "Custom Steam Dashboard API"
- `description`: "REST API for Custom Steam Dashboard application"
- `version`: "1.0.0"
- `lifespan`: Funkcja lifespan

**Middleware:**
- `CORSMiddleware`: 
  - `allow_origins`: ["*"] (w produkcji: konkretne domeny)
  - `allow_credentials`: True
  - `allow_methods`: ["*"]
  - `allow_headers`: ["*"]

---

### Endpointy API

#### Podstawowe Endpointy

##### `GET /`

Root endpoint.

**Zwraca:**
```json
{
  "message": "Custom Steam Dashboard API",
  "version": "1.0.0",
  "status": "running"
}
```

##### `GET /health`

Health check endpoint.

**Zwraca:**
```json
{
  "status": "healthy",
  "database": "connected|disconnected",
  "scheduler": "running|stopped"
}
```

**Funkcjonalność:**
- Sprawdza status połączenia z bazą
- Sprawdza status schedulera

#### Watchlist Endpointy

##### `GET /api/watchlist`

Pobiera wszystkie gry w watchlist.

**Zwraca:**
```json
{
  "watchlist": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "last_count": 1000000
    }
  ]
}
```

**Obsługa błędów:**
- 500: Błąd serwera

#### Game Endpointy

##### `GET /api/games`

Pobiera wszystkie gry.

**Zwraca:**
```json
{
  "games": [...]
}
```

##### `GET /api/games/{appid}`

Pobiera szczegóły gry.

**Parametry ścieżki:**
- `appid` (int): Steam App ID

**Zwraca:**
- Obiekt gry ze wszystkimi szczegółami

**Obsługa błędów:**
- 404: Gra nie znaleziona
- 500: Błąd serwera

##### `GET /api/games/{appid}/current-players`

Pobiera aktualną liczbę graczy (live z Steam API).

**Parametry ścieżki:**
- `appid` (int): Steam App ID

**Zwraca:**
```json
{
  "appid": 730,
  "player_count": 1000000
}
```

**Obsługa błędów:**
- 500: Błąd Steam API

#### Steam API Endpointy

##### `GET /api/steam/most-played`

Pobiera najpopularniejsze gry.

**Zwraca:**
```json
{
  "games": [...]
}
```

##### `GET /api/steam/coming-soon`

Pobiera nadchodzące gry.

**Zwraca:**
```json
{
  "games": [...]
}
```

---

## Moduł Common

### Plik: `common/_base_http.py`

Bazowy asynchroniczny klient HTTP z retry logic.

#### Klasa: `BaseAsyncService`

Współdzielony klient HTTP z obsługą retry i context manager.

**Atrybuty:**
- `_client` (httpx.AsyncClient): Klient HTTP z HTTP/2

#### Konstruktor

```python
def __init__(self, *, timeout: httpx.Timeout | float = _DEFAULT_TIMEOUT)
```

**Parametry:**
- `timeout` (httpx.Timeout | float): Timeout dla requestów (domyślnie 10s)

**Konfiguracja:**
- HTTP/2 włączone
- Timeout: 10s (connect i read)

#### Metody

##### `async def aclose(self) -> None`

Zamyka klienta HTTP.

##### `async def __aenter__(self)`

Wejście do context managera.

**Zwraca:** `self`

##### `async def __aexit__(self, exc_type, exc, tb) -> None`

Wyjście z context managera.

**Funkcjonalność:**
- Automatycznie zamyka klienta

##### `async def _get_json(self, url: str, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any`

Wykonuje GET request i zwraca JSON.

**Parametry:**
- `url` (str): URL do zapytania
- `params` (Optional[Dict]): Parametry query string
- `headers` (Optional[Dict]): Nagłówki HTTP

**Zwraca:**
- `Any`: Sparsowany JSON

**Retry Configuration:**
- Maksymalnie 3 próby
- Exponential backoff: 0.5s min, 4s max
- Retry tylko dla `httpx.HTTPError`

**Funkcjonalność:**
- Unika podwójnego encodowania URL (unquote jeśli '%' w wartości)
- Automatyczne raise dla błędów HTTP
- Parsuje odpowiedź jako JSON

---

### Plik: `common/parse_html.py`

Utylity do parsowania HTML.

#### Funkcja: `parse_html_tags`

```python
async def parse_html_tags(html_string: str) -> str
```

Parsuje tagi HTML z ciągu znaków.

**Parametry:**
- `html_string` (str): Ciąg HTML do parsowania

**Zwraca:**
- `str`: Czysty tekst bez tagów HTML

**Funkcjonalność:**
- Usuwa wszystkie tagi HTML regex `<[^>]+>`
- Dekoduje HTML entities (`&nbsp;`, `&lt;`, etc.)
- Zwraca oczyszczony i przycięty tekst

**Uwaga:**
- Wymaga importu `re` (brakuje w kodzie - potencjalny bug)

---

## Podsumowanie Przepływu Danych

### Startup
1. FastAPI uruchamia `lifespan()`
2. Inicjalizacja bazy danych i tabel
3. Inicjalizacja Steam client
4. Auto-seed watchlist top 100 grami
5. Start schedulera z zadaniami

### Zbieranie Danych (co 5 minut)
1. `PlayerCountCollector.collect_player_counts()` uruchamia się
2. Pobiera watchlist z bazy
3. Dla każdej gry wywołuje Steam API
4. Zapisuje do `players_raw_count` i aktualizuje `watchlist`

### Odświeżanie Watchlist (co 1 godzinę)
1. `WatchlistRefresher.refresh_watchlist()` uruchamia się
2. Pobiera top gry ze Steam
3. Upsertuje do watchlist

### Wypełnianie Danych Gier (co 1h 5min)
1. `GameDataFiller.fill_game_data()` uruchamia się
2. Dla każdej gry w watchlist pobiera szczegóły
3. Zapisuje do `games`, `game_genres`, `game_categories`

### Agregacje (rollup)
1. **Godzinowo**: Agreguje surowe dane do `player_counts_hourly`
2. **Dziennie**: Agreguje surowe dane do `player_counts_daily`

### Czyszczenie
1. **Co dzień**: Usuwa surowe dane starsze niż 14 dni
2. **Co dzień**: Usuwa dane godzinowe starsze niż 30 dni
3. **Co dzień**: Usuwa dane dzienne starsze niż 90 dni

### Obsługa API Requestów
1. Client wysyła request do FastAPI endpoint
2. Endpoint wywołuje odpowiednie metody `DatabaseManager` lub `SteamClient`
3. Zwraca dane w formacie JSON

---

## Najlepsze Praktyki i Uwagi

### Bezpieczeństwo
- Zmienne środowiskowe dla credentials (`.env`)
- CORS skonfigurowany (w prod: konkretne origins)
- Walidacja danych przez Pydantic

### Performance
- Connection pooling (asyncpg)
- Asynchroniczne operacje (asyncio, asyncpg, httpx)
- Semafory dla rate limiting
- HTTP/2 dla szybszych requestów

### Niezawodność
- Retry logic (tenacity)
- Error handling w każdej metodzie
- Agregacje dla redukcji danych
- Max instances=1 dla zadań schedulera

### Monitoring
- Logging na każdym poziomie
- Health check endpoint
- Status schedulera w API

### Potencjalne Ulepszenia
1. Dodać endpoint dla manualne triggerowanie jobów
2. Dodać więcej metryk (Prometheus)
3. Dodać cache (Redis) dla często odpytywanych danych
4. Dodać user authentication
5. Poprawić `parse_html.py` (brakuje `import re`)
6. Dodać testy jednostkowe
7. Dodać dokumentację OpenAPI/Swagger customization

---

## Troubleshooting

### Baza danych nie łączy się
- Sprawdź zmienne środowiskowe w `.env`
- Zweryfikuj dostępność PostgreSQL
- Sprawdź firewall/security groups

### Scheduler nie zbiera danych
- Sprawdź logi: czy jest watchlist?
- Sprawdź Steam API: czy odpowiada?
- Sprawdź `/health` endpoint

### Steam API zwraca błędy
- Rate limiting: poczekaj kilka minut
- Sprawdź `STEAM_API_KEY` dla endpointów wymagających klucza
- Sprawdź dostępność Steam API

### Wysokie użycie pamięci
- Zmniejsz pool size w DatabaseManager
- Zmniejsz semaphore w `get_most_played_games()`
- Skonfiguruj częstsze czyszczenie danych

---

**Wersja dokumentacji:** 1.0  
**Data utworzenia:** 2025-11-03  
**Autor:** Auto-generated documentation

