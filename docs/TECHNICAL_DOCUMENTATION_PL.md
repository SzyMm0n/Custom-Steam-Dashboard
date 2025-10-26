# Custom-Steam-Dashboard — Dokumentacja techniczna

Poniżej znajdziesz kompletny opis struktury projektu, użytych technologii oraz szczegółową dokumentację każdej ważnej klasy, funkcji i metody. Opisy zawierają: co robi dana funkcja, dlaczego powstała, argumenty i ich znaczenie oraz krótkie przykłady użycia.


## 1) Struktura projektu

- `app/`
  - `main.py` — uruchamianie aplikacji desktopowej (PySide6 + asyncio via qasync), bootstrap danych.
  - `main_window.py` — główne okno aplikacji (QMainWindow), nawigacja i odświeżanie widoków.
  - `ui/`
    - `home_view.py` — ekran domowy z trzema sekcjami: Live Games Count (gracze online), Best Deals, Best Upcoming Releases.
- `app/core/`
  - `services/`
    - `_base_http.py` — wspólna baza dla asynchronicznych klientów HTTP z retry (httpx + tenacity).
    - `steam_api.py` — klient Steam Store/Web API + modele Pydantic, interfejsy i implementacje.
    - `deals_api.py` — klient API CheapShark (promocje gier) + modele, interfejs i implementacja.
  - `data/`
    - `db.py` — warstwa trwałości (SQLite), schemat, rollupy, watchlista, zapytania do wykresów.
    - `retention_job.py` — skrypty asynchronicznego zbierania danych, seeding watchlisty, CLI narzędziowe.
- `README.md` — skrót repo (do rozbudowy).
- `requirements.txt` / `pyproject.toml` — zależności i konfiguracja pakietu/build.


## 2) Technologie i biblioteki

- UI: PySide6 (Qt for Python) — aplikacja desktopowa, widżety, sygnały/sloty.
- Integracja z asyncio: qasync — mostek między pętlą zdarzeń Qt i asyncio (await w UI bez blokowania).
- HTTP: httpx[http2] — asynchroniczny klient HTTP/2; tenacity — retry z wykładniczym backoffem.
- Modele danych: pydantic v2 — walidacja i niezmienność obiektów (frozen), mapowanie odpowiedzi API.
- Trwałość: sqlite3 (standard lib) + platformdirs — plik bazy w katalogu użytkownika (WAL, foreign keys).
- Konfiguracja: python-dotenv (opcjonalnie) — wczytywanie kluczy (np. STEAM_API_KEY) z pliku `.env`.
- Dodatkowo w zależnościach: rapidfuzz (dopasowanie tytułów — obecnie niewykorzystywane w kodzie), loguru (logowanie — obecnie niewykorzystywane w kodzie), pyinstaller (build binariów).

Wymagana wersja Pythona: >= 3.11, rekomendowana 3.12 (patrz `pyproject.toml`).


## 3) Szybki start (opcjonalnie)

- Zainstaluj zależności:
  - `pip install -r requirements.txt` lub `pip install .` (z `pyproject.toml`).
- (Opcjonalnie do Steam Web API) ustaw zmienne środowiskowe: `STEAM_API_KEY`, `STEAM_ID` (np. przez `.env`).
- Uruchom aplikację: `python -m app.main`.
- Uruchom CLI retencji/seedingu: `python -m app.core.data.retention_job --help`.


## 4) Warstwa UI

### 4.1 `app/main_window.py`

Klasa: `MainWindow(QMainWindow)`

- Cel: Główne okno aplikacji; trzyma stos widoków (QStackedWidget), toolbar do nawigacji i odświeżania.

Metody:
- `__init__(self)`
  - Co robi: Konfiguruje okno, tworzy centralny layout z `QStackedWidget`, dodaje `HomeView` i toolbar.
  - Dlaczego: Uporządkowanie nawigacji i możliwość rozbudowy o kolejne widoki.
  - Argumenty: brak.

- `_init_toolbar(self)`
  - Co robi: Tworzy pasek narzędzi z akcjami „Home” i „Odśwież”.
  - Dlaczego: Szybki dostęp do nawigacji i ręcznego odświeżenia danych.
  - Argumenty: brak (metoda pomocnicza).

- `refresh_current_view(self)`
  - Co robi: Wywołuje `refresh()` na obecnym widżecie, jeśli istnieje.
  - Dlaczego: Umożliwia odświeżanie danych bez przeładowywania aplikacji.
  - Argumenty: brak.

Przykład użycia (programistyczny):
- Po utworzeniu `MainWindow`, kliknięcie „Odśwież” wywoła `HomeView.refresh()`.


### 4.2 `app/ui/home_view.py`

Stała: `TOP_GAME_APP_IDS: list[int]` — lista popularnych AppID, dla których pobieramy liczbę graczy.

Klasa: `HomeView(QWidget)`

- Cel: Widok główny z sekcjami: Live Games Count, Best Deals, Best Upcoming Releases.

Metody:
- `__init__(self)`
  - Co robi: Buduje układ i widżety, planuje pierwsze odświeżenie po 100 ms.
  - Dlaczego: Inicjalne renderowanie i automatyczne pobranie danych po starcie UI.
  - Argumenty: brak.

- `refresh(self)`
  - Co robi: Czyści listy, wyświetla placeholder „Ładowanie danych…”, startuje task `_load_data_async()`.
  - Dlaczego: Oddziela synchronizację UI (szybkie) od faktycznego pobierania (async).
  - Argumenty: brak.

- `async _load_data_async(self)`
  - Co robi: Asynchronicznie pobiera dane przez `SteamStoreClient`:
    - wywołuje `_load_top_live_games`,
    - pobiera „Best Deals” przez wewnętrzne `_get_featured_category_items("specials", ...)`,
    - pobiera „Best Upcoming Releases” przez `get_coming_soon(...)`.
  - Dlaczego: Batchowe pobranie danych bez blokowania wątku UI.
  - Argumenty: brak.

- `async _load_top_live_games(self, client: SteamStoreClient)`
  - Co robi: Równolegle pobiera liczbę graczy i szczegóły aplikacji (nazwy) dla `TOP_GAME_APP_IDS`; sortuje malejąco po liczbie graczy i prezentuje top 15.
  - Dlaczego: Prezentacja „na żywo” jakie gry mają najwięcej graczy.
  - Argumenty:
    - `client`: instancja `SteamStoreClient`, współdzielona w obrębie jednego cyklu odświeżenia.

Przykład (logika wewnętrzna):
- `refresh()` -> `asyncio.create_task(self._load_data_async())` -> `async with SteamStoreClient(): ...` -> aktualizacja list.


## 5) Warstwa usług HTTP

### 5.1 `app/core/services/_base_http.py`

Klasa: `BaseAsyncService`

- Cel: Bazowy asynchroniczny klient HTTP z automatycznym zamykaniem sesji, retry i pomocniczą metodą `_get_json`.

Metody:
- `__init__(self, *, timeout: httpx.Timeout | float = _DEFAULT_TIMEOUT)`
  - Co robi: Tworzy `httpx.AsyncClient(http2=True)` z domyślnym timeoutem.
  - Dlaczego: Wspólna konfiguracja dla wszystkich klientów (spójność, HTTP/2, timeouty).
  - Argumenty: `timeout` — `httpx.Timeout` lub liczba sekund.

- `async aclose(self) -> None`, `async __aenter__`, `async __aexit__`
  - Co robi: Obsługa context managera async, poprawne zamykanie klienta.
  - Dlaczego: Unikanie wycieków połączeń.

- `async _get_json(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> Any`
  - Co robi: GET z retry (tenacity), odkodowanie procentów w wartościach parametrów (ochrona przed podwójnym kodowaniem), zwraca `resp.json()` lub rzuca wyjątek HTTP.
  - Dlaczego: Odporne pobieranie JSON z API, spójne zachowanie błędów.
  - Argumenty: `url`, `params`, `headers` — standardowe dla zapytań HTTP.

Przykład:
```python
async with SteamStoreClient(timeout=15) as cli:
    data = await cli._get_json("https://httpbin.org/get", params={"q": "steam"})
```


### 5.2 `app/core/services/steam_api.py`

Modele (Pydantic, `frozen=True`, `extra="ignore"`):
- `PlayerCount(appid: int, player_count: int=0)` — wynik liczby aktywnych graczy.
- `NewsItem(...)` — pozycja z newsów (tytuł, URL, autor, data, flaga czy „update-like”).
- `ReleaseInfo(coming_soon: bool, date: str|None)` — blok daty wydania.
- `PriceOverview(currency, initial, final, discount_percent)` — informacje cenowe.
- `AppDetails(...)` — wybrane pola z `store.steampowered.com/api/appdetails` (nazwa, gatunki, kategorie, cena, itp.).
- `FeaturedItem(id, name, release_date, final_price, discount_percent, ...)` — element z sekcji „featured categories”.
- `SteamGame(appid, name, playtime_forever, playtime_2weeks)` — gra użytkownika z Web API.
- `TopGame(appid, name, categories, genres, rank)` — pozycja z Most Played (SteamChartsService) wraz z uzupełnionymi metadanymi.

Interfejsy (ABC):
- `ISteamStore` — kontrakt metod dla publicznego Store API.
- `ISteamWebApi` — kontrakt metod dla klucza deweloperskiego Web API.

Klasa: `SteamStoreClient(BaseAsyncService, ISteamStore)`

Metody publiczne:
- `async get_number_of_current_players(appid: int) -> PlayerCount`
  - Co: Liczba graczy online dla gry.
  - Dlaczego: Sekcja „Live Games Count” w UI.
  - Argumenty: `appid` — identyfikator aplikacji.
  - Zwraca: `PlayerCount`.
  - Przykład:
    ```python
    pc = await client.get_number_of_current_players(570)
    print(pc.player_count)
    ```

- `async get_recent_news(appid: int, count: int = 5, updates_only: bool = True) -> list[NewsItem]`
  - Co: Najnowsze newsy dla gry; domyślnie filtruje do „update-like”.
  - Dlaczego: Możliwe rozszerzenie UI o changelogi/patche.
  - Argumenty: `appid`, `count`, `updates_only`.

- `async get_app_details(appid: int, cc: str = "pln", lang: str = "en") -> AppDetails | None`
  - Co: Szczegóły gry (nazwa, gatunki, kategorie, cena, itp.).
  - Dlaczego: Uzupełnianie metadanych (np. nazwy w Live Games, tagi w watchliście).
  - Argumenty: `appid`, `cc` — kraj (ceny), `lang` — język opisów.

- `async get_coming_soon(cc="pln", lang="en", limit=30) -> list[FeaturedItem]`
- `async get_new_releases(cc="pln", lang="en", limit=30) -> list[FeaturedItem]`
- `async get_top_sellers(cc="pln", lang="en", limit=30) -> list[FeaturedItem]`
  - Co: Wybrane kategorie „featured” ze sklepu.
  - Dlaczego: Sekcje „Best Upcoming Releases” i potencjalne inne listy.
  - Argumenty: `cc`, `lang`, `limit`.

- `async get_most_played(limit: int = 150) -> list[TopGame]`
  - Co: Lista najczęściej granych gier (rankingi) + uzupełnione metadane z `get_app_details` (równolegle, z semaforem).
  - Dlaczego: Seed watchlisty i źródło popularnych tytułów do obserwacji.
  - Argumenty: `limit` — maksymalna liczba pozycji.

Metody wewnętrzne:
- `async _get_featured_category_items(key: str, *, cc: str, lang: str, limit: int) -> list[FeaturedItem]`
  - Co: Uniwersalny pobieracz kategorii z `featuredcategories`; toleruje warianty kluczy (np. `topsellers`).
  - Dlaczego: Reużywalność dla „coming_soon”, „new_releases”, „top_sellers”, „specials”.

Helper:
- `_looks_like_update(title: str|None, feedlabel: str|None) -> bool` — heurystyka rozpoznawania newsów typu „update/patch”.

Klasa: `SteamWebApiClient(BaseAsyncService, ISteamWebApi)`

- Wymaga `STEAM_API_KEY` w środowisku lub przekazania `api_key` w konstruktorze.

Metody:
- `async get_owned_games(steamid: str) -> list[SteamGame]`
- `async get_recently_played(steamid: str) -> list[SteamGame]`
- `async get_badges(steamid: str) -> dict`
  - Co: Wybrane endpointy IPlayerService (własne biblioteki gier, ostatnio grane, odznaki).
  - Dlaczego: Ewentualna rozbudowa UI o profil użytkownika/aktywność.

Przykład:
```python
from os import getenv
async with SteamWebApiClient() as api:
    games = await api.get_owned_games(getenv("STEAM_ID"))
    print(len(games))
```


### 5.3 `app/core/services/deals_api.py`

Model: `Deal`
- Pola: `title`, `steamAppID`, `salePrice`, `normalPrice`, `dealID` (frozen, walidowane pydantic).

Interfejs: `IDealsApi`
- `get_current_deals(limit=50, min_discount=30) -> list[Deal]`
- `get_deals_for_title(title, limit=50) -> list[Deal]`
- `get_deal_by_id(deal_id) -> Deal|None`

Klasa: `DealsApiClient(BaseAsyncService, IDealsApi)`
- `BASE_URL = https://www.cheapshark.com/api/1.0`

Metody:
- `async get_current_deals(limit=50, min_discount=30) -> list[Deal]`
  - Co: Największe oszczędności (sortBy=Savings), filtruje poniżej `min_discount`.
  - Dlaczego: Sekcja „Best Deals” w UI.
  - Argumenty: `limit` (1..500), `min_discount` (w %).

- `async get_deals_for_title(title: str, limit=50) -> list[Deal]`
  - Co: Promocje ograniczone do frazy tytułu.
  - Dlaczego: Szukanie promocji konkretnej gry.

- `async get_deal_by_id(deal_id: str) -> Deal|None`
  - Co: Szczegóły konkretnej oferty (łączy `gameInfo` i `cheapestPrice`).
  - Dlaczego: Drill-down po kliknięciu oferty (rozszerzalne).

Przykład:
```python
async with DealsApiClient() as deals:
    top = await deals.get_current_deals(limit=10, min_discount=40)
    print([d.title for d in top])
```


## 6) Warstwa danych i trwałości (SQLite)

Plik: `app/core/data/db.py`

Stałe i typy:
- `SCHEMA_SQL` — kompletny schemat bazy (tabele surowe, rollupy godzinowe/dobowe, snapshoty użytkownika, watchlista + tagi, indeksy).
- `SeriesPoint(ts_unix: int, avg_players: float, max_players: int)` — punkt seryjny do wykresów.

Klasa: `Database`
- Cel: Enkapsulacja połączenia SQLite, operacje CRUD i agregacje.
- Konstruktor: `__init__(db_path: str|None = None)`
  - Co: Tworzy/otwiera bazę `dashboard.sqlite` w katalogu użytkownika (`platformdirs`), ustawia WAL, foreign keys, synchronous=NORMAL.
  - Dlaczego: Stabilna lokalizacja i parametry dla aplikacji desktopowej.

Metody ogólne:
- `close()` — zamyka połączenie.
- `init_schema()` — wykonuje `SCHEMA_SQL`, bezpieczne przy wielokrotnym wywołaniu.

Watchlista i tagi:
- `add_to_watchlist(appid: int, title: str|None)` — INSERT OR REPLACE do `watchlist`.
- `remove_from_watchlist(appid: int)` — usuwa z `watchlist`.
- `get_watchlist() -> list[tuple[int, str]]` — zwraca `(appid, title)`.
- `upsert_watchlist_tags(appid, *, genres: seq[str]|None, categories: seq[str]|None, replace: bool=True)`
  - Co: Czyści stare tagi (jeśli `replace=True`) i wstawia nowe (IGNORE duplikaty).
  - Dlaczego: Synchronizacja tagów z metadanymi ze Store API.
- `get_all_watchlist_genres() -> list[str]` — wszystkie unikalne gatunki.
- `get_all_watchlist_categories() -> list[str]` — wszystkie unikalne kategorie.
- `get_watchlist_filtered(*, genres_any=None, genres_all=None, categories_any=None, categories_all=None) -> list[tuple[int, str, str, str]]`
  - Co: Zwraca wiersze `appid, title, genre, category` spełniające warunki ANY/ALL (przez podzapytania COUNT DISTINCT).
  - Dlaczego: Filtrowanie listy obserwowanych po tagach.

Wstawki danych:
- `insert_player_count_raw(appid: int, ts_unix: int, players: int)` — wstawia próbkę graczy do `player_counts_raw` (INSERT OR IGNORE po PK).
- `insert_user_snapshot(steamid, fetched_ts_unix, appid, playtime_2w_min, playtime_forever_min)` — snapshot aktywności użytkownika.

Agregacje (rollupy):
- `@staticmethod _p95(values: seq[int]) -> int` — percentyl 95 (indeksowany po zaokrągleniu w górę; zabezpieczenie na puste listy).
- `rollup_hourly(*, since_ts: int|None=None, until_ts: int|None=None, appids: Iterable[int]|None=None) -> int`
  - Co: Grupuje surowe próbki w kubełki godzinowe (liczy avg, max, p95), UPSERT do `player_counts_hourly`.
  - Argumenty: zakres czasowy i opcjonalny filtr appid.
  - Zwraca: liczba upsertowanych kubełków.
- `rollup_daily(*, since_ts: int|None=None, until_ts: int|None=None, appids: Iterable[int]|None=None) -> int`
  - Co: Jak wyżej, na poziomie „dni” (ymd via `strftime`).

Zapytania do wykresów:
- `get_series_5min(appid: int, *, since_ts: int, until_ts: int) -> list[SeriesPoint]`
- `get_series_hourly(appid: int, *, since_ts: int, until_ts: int) -> list[SeriesPoint]`
- `get_series_daily(appid: int, *, since_ymd: str, until_ymd: str) -> list[tuple[str, float, int]]`
  - Co: Zwracają punkty agregacji w zadanych oknach czasowych, rosnąco po czasie.

Przykład:
```python
db = Database(); db.init_schema()
now = int(__import__('time').time())
db.insert_player_count_raw(570, now, 500000)
db.rollup_hourly(since_ts=now-3600)
pts = db.get_series_hourly(570, since_ts=now-3600*24, until_ts=now)
```


## 7) Zadania okresowe i CLI

Plik: `app/core/data/retention_job.py`

Funkcje:
- `async seed_watchlist_top(db: Database, limit: int = 150) -> int`
  - Co: Pobiera Most Played z `SteamStoreClient.get_most_played`, dla każdego dodaje do watchlisty i uzupełnia tagi.
  - Dlaczego: Szybki „bootstrap” listy obserwowanych gier.
  - Argumenty: `db`, `limit` — ile gier wstawić.
  - Zwraca: liczba pozycji dodanych/zaktualizowanych.

- `async refresh_watchlist_tags(db: Database) -> int`
  - Co: Dla wszystkich z watchlisty pobiera `get_app_details` i odświeża gatunki/kategorie.
  - Dlaczego: Utrzymanie aktualnych tagów po czasie.

- `async collect_once(db: Database, *, now_ts: int|None = None) -> None`
  - Co: Dla każdego `appid` w watchliście pobiera bieżących graczy, wstawia do `player_counts_raw`, wykonuje rollupy (godzinowy/dobowy) i purge retencji.
  - Dlaczego: Jednorazowy „tick” kolekcjonera; może być wywołany z CRON.
  - Argumenty: `now_ts` — wstrzyknięcie czasu (testy/repro); domyślnie `time.time()`.

- `main()` (CLI)
  - Subkomendy:
    - `init` — inicjalizacja schematu, opcjonalny seeding topki.
    - `watch-seed-top --limit N` — seed najpopularniejszych.
    - `watch-add APPID [--title T]` — dodaj do watchlisty.
    - `watch-rm APPID` — usuń z watchlisty.
    - `watch-list` — wypisz watchlistę.
    - `watch-refresh-tags` — odśwież tagi dla watchlisty.
    - `collect-once` — jednorazowy zbiór danych i porządki.

Przykład CLI:
```bash
python -m app.core.data.retention_job init
python -m app.core.data.retention_job watch-seed-top --limit 150
python -m app.core.data.retention_job collect-once
```


## 8) Uruchamianie i pętla zdarzeń

Plik: `app/main.py`

Funkcje:
- `async bootstrap(app) -> None`
  - Co: Tworzy `Database`, inicjuje schemat i uruchamia `seed_watchlist_top` (limit=150). Obsługuje wyjątki bez wyłączania aplikacji.
  - Dlaczego: Przygotowanie danych przed startem głównego okna.
  - Argumenty: `app` — instancja `QApplication` (nieużywana wewnętrznie, przekazywana dla spójności sygnatury).

- `async main_coro(app, window) -> None`
  - Co: Pokazuje okno (`window.show()`), czeka aż aplikacja wyśle `aboutToQuit` (Future), utrzymując pętlę.
  - Dlaczego: Integracja cyklu życia Qt z asyncio, kontrolowane zamykanie.
  - Argumenty: `app: QApplication`, `window: MainWindow`.

- `main()`
  - Co: Tworzy `QApplication`, uruchamia `bootstrap` przez `asyncio.run`, spina pętlę `QEventLoop` (qasync), tworzy `MainWindow` i uruchamia `qasync.run(main_coro(app, window))`.
  - Dlaczego: Poprawna integracja Qt i asyncio z przewidywalnym shutdownem.

Przykład: Punkt wejścia aplikacji — `python -m app.main`.


## 9) Dodatkowe uwagi projektowe i edge-case’y

- Wyjątki HTTP i problemy sieci: `_get_json` ma retry dla `httpx.HTTPError` (3 próby, backoff wykładniczy), ale nie łapie błędów parsowania JSON — to celowe; klienci mogą to obsłużyć.
- W `HomeView` „Best Deals” korzysta z metody `_get_featured_category_items("specials", ...)` klasy SteamStoreClient — to metoda „prywatna” (nazwa z podkreśleniem), ale świadomie użyta jako wewnętrzne API w obrębie modułu. Można ją wygładzić do metody publicznej w przyszłości.
- Baza SQLite w katalogu użytkownika z WAL — bezpieczniejsza równoległość odczytów, lepsza odporność na crash.
- Rollupy: p95 liczone na posortowanych próbkach; przy małej liczbie próbek p95 może równać się max.
- `get_watchlist_filtered`: zwraca złączenie watchlist + tagi; wynik zawiera powtarzające się `appid` (dla różnych kombinacji gatunek/kategoria) — to intencjonalne dla płaskiego wyświetlania/filtrowania; można dodać wariant zagregowany na potrzeby UI.
- Steam Web API: aby używać `SteamWebApiClient`, wymagany jest klucz deweloperski (env `STEAM_API_KEY`) i identyfikator użytkownika `STEAM_ID` przy przykładach.


## 10) Szybkie mini-przykłady użycia (zebrane)

Pobranie najpopularniejszych gier i seed watchlisty:
```python
import asyncio
from app.core.data.db import Database
from app.core.data.retention_job import seed_watchlist_top

async def run():
    db = Database(); db.init_schema()
    n = await seed_watchlist_top(db, limit=50)
    print("Seeded:", n)

asyncio.run(run())
```

Top żywo online (wycinek logiki `HomeView`):
```python
import asyncio
from app.core.services.steam_api import SteamStoreClient

APPIDS = [570, 730]

async def live_counts():
    async with SteamStoreClient() as client:
        pcs = await asyncio.gather(*(client.get_number_of_current_players(a) for a in APPIDS))
        for pc in pcs:
            print(pc.appid, pc.player_count)

asyncio.run(live_counts())
```

Promocje CheapShark:
```python
import asyncio
from app.core.services.deals_api import DealsApiClient

async def deals():
    async with DealsApiClient() as api:
        top = await api.get_current_deals(limit=5, min_discount=30)
        for d in top:
            print(d.title, d.salePrice)

asyncio.run(deals())
```

Wstawka i agregacja w SQLite:
```python
from app.core.data.db import Database
import time

db = Database(); db.init_schema()
now = int(time.time())
db.insert_player_count_raw(570, now, 500000)
db.rollup_hourly(since_ts=now-3600)
print(db.get_series_hourly(570, since_ts=now-3600*24, until_ts=now)[:2])
```

---

Ta dokumentacja obejmuje wszystkie kluczowe elementy projektu aktualne na moment ostatniej analizy. W przypadku rozbudowy UI lub nowych usług API warto dodać analogiczne sekcje i zaktualizować przykłady.

