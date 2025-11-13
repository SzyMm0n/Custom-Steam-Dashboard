# Dokumentacja Bazy Danych

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Struktura Bazy](#struktura-bazy)
3. [Klasa DatabaseManager](#klasa-databasemanager)
4. [Operacje na Danych](#operacje-na-danych)
5. [Migracje](#migracje)

---

## Przegląd

**Custom Steam Dashboard** wykorzystuje **PostgreSQL** jako główną bazę danych z **asyncpg** jako asynchronicznym driverem.

**Plik:** `server/database/database.py`

### Funkcjonalności

- ✅ Connection pooling (asyncpg)
- ✅ Automatyczne tworzenie tabel przy starcie
- ✅ Seedowanie watchlisty (top 100 gier)
- ✅ Batch operacje (wydajność)
- ✅ Archiwizacja historycznych danych

---

## Struktura Bazy

### Tabele

#### 1. **games** - Informacje o grach

```sql
CREATE TABLE IF NOT EXISTS games (
    appid INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    header_image TEXT,
    short_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_games_name ON games(name);
```

**Kolumny:**
- `appid` - Steam Application ID (PK)
- `name` - Nazwa gry
- `header_image` - URL obrazu nagłówka
- `short_description` - Krótki opis gry
- `created_at` - Data dodania

---

#### 2. **game_genres** - Gatunki gier

```sql
CREATE TABLE IF NOT EXISTS game_genres (
    appid INTEGER REFERENCES games(appid) ON DELETE CASCADE,
    genre TEXT NOT NULL,
    PRIMARY KEY (appid, genre)
);

CREATE INDEX IF NOT EXISTS idx_game_genres_appid ON game_genres(appid);
CREATE INDEX IF NOT EXISTS idx_game_genres_genre ON game_genres(genre);
```

---

#### 3. **game_categories** - Kategorie gier

```sql
CREATE TABLE IF NOT EXISTS game_categories (
    appid INTEGER REFERENCES games(appid) ON DELETE CASCADE,
    category TEXT NOT NULL,
    PRIMARY KEY (appid, category)
);

CREATE INDEX IF NOT EXISTS idx_game_categories_appid ON game_categories(appid);
CREATE INDEX IF NOT EXISTS idx_game_categories_category ON game_categories(category);
```

---

#### 4. **player_counts_raw** - Surowe dane liczby graczy

```sql
CREATE TABLE IF NOT EXISTS player_counts_raw (
    id SERIAL PRIMARY KEY,
    appid INTEGER REFERENCES games(appid) ON DELETE CASCADE,
    player_count INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_counts_appid ON player_counts_raw(appid);
CREATE INDEX IF NOT EXISTS idx_player_counts_timestamp ON player_counts_raw(timestamp);
```

**Używane przez:** Scheduler (co 5 minut)

---

#### 5. **player_counts_hourly** - Agregacja godzinowa

```sql
CREATE TABLE IF NOT EXISTS player_counts_hourly (
    id SERIAL PRIMARY KEY,
    appid INTEGER REFERENCES games(appid) ON DELETE CASCADE,
    avg_player_count INTEGER NOT NULL,
    max_player_count INTEGER NOT NULL,
    min_player_count INTEGER NOT NULL,
    hour_start TIMESTAMP NOT NULL,
    UNIQUE(appid, hour_start)
);

CREATE INDEX IF NOT EXISTS idx_player_counts_hourly_appid ON player_counts_hourly(appid);
CREATE INDEX IF NOT EXISTS idx_player_counts_hourly_hour ON player_counts_hourly(hour_start);
```

**Używane przez:** Archiwizacja (co godzinę)

---

#### 6. **player_counts_daily** - Agregacja dzienna

```sql
CREATE TABLE IF NOT EXISTS player_counts_daily (
    id SERIAL PRIMARY KEY,
    appid INTEGER REFERENCES games(appid) ON DELETE CASCADE,
    avg_player_count INTEGER NOT NULL,
    max_player_count INTEGER NOT NULL,
    min_player_count INTEGER NOT NULL,
    date DATE NOT NULL,
    UNIQUE(appid, date)
);

CREATE INDEX IF NOT EXISTS idx_player_counts_daily_appid ON player_counts_daily(appid);
CREATE INDEX IF NOT EXISTS idx_player_counts_daily_date ON player_counts_daily(date);
```

**Używane przez:** Archiwizacja (codziennie)

---

#### 7. **watchlist** - Lista obserwowanych gier

```sql
CREATE TABLE IF NOT EXISTS watchlist (
    appid INTEGER PRIMARY KEY REFERENCES games(appid) ON DELETE CASCADE,
    current_players INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_watchlist_current_players ON watchlist(current_players DESC);
```

**Opis:**
- Lista gier do monitorowania (top 100 najpopularniejszych)
- Scheduler aktualizuje `current_players` co 5 minut
- UI pobiera dane z tej tabeli

---

## Klasa DatabaseManager

**Plik:** `server/database/database.py`

### Inicjalizacja

```python
class DatabaseManager:
    """
    Zarządza połączeniem z PostgreSQL i operacjami na bazie.
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Tworzy connection pool."""
        self.pool = await asyncpg.create_pool(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", ""),
            database=os.getenv("PGDATABASE", "postgres"),
            min_size=5,
            max_size=20
        )
    
    async def disconnect(self):
        """Zamyka connection pool."""
        if self.pool:
            await self.pool.close()
```

### Tworzenie Tabel

```python
async def create_tables(self):
    """Tworzy wszystkie wymagane tabele."""
    async with self.pool.acquire() as conn:
        # Tabela games
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS games (...)
        """)
        
        # Pozostałe tabele...
        # (zobacz pełny kod w database.py)
```

---

## Operacje na Danych

### Gry

```python
# Pobierz wszystkie gry
async def get_all_games(self) -> List[Dict]:
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM games")
        return [dict(row) for row in rows]

# Pobierz pojedynczą grę
async def get_game(self, appid: int) -> Optional[Dict]:
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM games WHERE appid = $1", appid
        )
        return dict(row) if row else None

# Upsert gry (insert or update)
async def upsert_game(self, appid: int, name: str, 
                     header_image: str = None,
                     short_description: str = None):
    async with self.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO games (appid, name, header_image, short_description)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (appid) DO UPDATE SET
                name = EXCLUDED.name,
                header_image = EXCLUDED.header_image,
                short_description = EXCLUDED.short_description
        """, appid, name, header_image, short_description)
```

### Gatunki i Kategorie

```python
# Pobierz tagi (gatunki + kategorie) dla wielu gier
async def get_game_tags(self, appids: List[int]) -> Dict[int, Dict]:
    """
    Returns:
        {
            730: {
                "genres": ["Action", "Free to Play"],
                "categories": ["Multi-player", "Steam Achievements"]
            }
        }
    """
    async with self.pool.acquire() as conn:
        # Pobierz gatunki
        genres = await conn.fetch("""
            SELECT appid, array_agg(genre) as genres
            FROM game_genres
            WHERE appid = ANY($1::int[])
            GROUP BY appid
        """, appids)
        
        # Pobierz kategorie
        categories = await conn.fetch("""
            SELECT appid, array_agg(category) as categories
            FROM game_categories
            WHERE appid = ANY($1::int[])
            GROUP BY appid
        """, appids)
        
        # Połącz wyniki
        result = {}
        for row in genres:
            result[row['appid']] = {"genres": row['genres'], "categories": []}
        for row in categories:
            if row['appid'] in result:
                result[row['appid']]['categories'] = row['categories']
        
        return result

# Upsert tagów
async def upsert_game_tags(self, appid: int, 
                          genres: List[str], 
                          categories: List[str]):
    async with self.pool.acquire() as conn:
        # Usuń stare tagi
        await conn.execute("DELETE FROM game_genres WHERE appid = $1", appid)
        await conn.execute("DELETE FROM game_categories WHERE appid = $1", appid)
        
        # Wstaw nowe gatunki
        if genres:
            await conn.executemany(
                "INSERT INTO game_genres (appid, genre) VALUES ($1, $2)",
                [(appid, g) for g in genres]
            )
        
        # Wstaw nowe kategorie
        if categories:
            await conn.executemany(
                "INSERT INTO game_categories (appid, category) VALUES ($1, $2)",
                [(appid, c) for c in categories]
            )
```

### Watchlist

```python
# Pobierz watchlist (dla UI)
async def get_watchlist(self) -> List[Dict]:
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                w.appid,
                g.name,
                w.current_players,
                w.last_updated
            FROM watchlist w
            JOIN games g ON w.appid = g.appid
            ORDER BY w.current_players DESC
        """)
        return [dict(row) for row in rows]

# Aktualizuj liczby graczy (scheduler)
async def update_watchlist_players(self, player_data: Dict[int, int]):
    """
    Args:
        player_data: {appid: player_count, ...}
    """
    async with self.pool.acquire() as conn:
        await conn.executemany("""
            UPDATE watchlist
            SET current_players = $2, last_updated = NOW()
            WHERE appid = $1
        """, [(appid, count) for appid, count in player_data.items()])

# Seedowanie watchlisty (top 100 gier)
async def seed_watchlist(self, steam_client: SteamClient):
    """Wypełnia watchlist top 100 najpopularniejszymi grami."""
    # Sprawdź czy watchlist jest pusta
    count = await self.pool.fetchval("SELECT COUNT(*) FROM watchlist")
    if count > 0:
        return  # Już wypełniona
    
    # Pobierz top 100 z Steam Charts
    top_games = await steam_client.get_top_games_by_players(limit=100)
    
    async with self.pool.acquire() as conn:
        for game in top_games:
            # Upsert gry
            await conn.execute("""
                INSERT INTO games (appid, name)
                VALUES ($1, $2)
                ON CONFLICT (appid) DO NOTHING
            """, game['appid'], game['name'])
            
            # Dodaj do watchlist
            await conn.execute("""
                INSERT INTO watchlist (appid, current_players)
                VALUES ($1, $2)
                ON CONFLICT (appid) DO NOTHING
            """, game['appid'], game['player_count'])
```

### Player Counts (Archiwizacja)

```python
# Zapisz surowe dane (co 5 minut)
async def save_player_counts(self, player_data: Dict[int, int]):
    async with self.pool.acquire() as conn:
        await conn.executemany("""
            INSERT INTO player_counts_raw (appid, player_count)
            VALUES ($1, $2)
        """, [(appid, count) for appid, count in player_data.items()])

# Agregacja godzinowa
async def aggregate_hourly(self):
    """Agreguje dane z player_counts_raw do player_counts_hourly."""
    async with self.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO player_counts_hourly 
                (appid, avg_player_count, max_player_count, min_player_count, hour_start)
            SELECT 
                appid,
                AVG(player_count)::int as avg_player_count,
                MAX(player_count) as max_player_count,
                MIN(player_count) as min_player_count,
                date_trunc('hour', timestamp) as hour_start
            FROM player_counts_raw
            WHERE timestamp < date_trunc('hour', NOW())
            GROUP BY appid, hour_start
            ON CONFLICT (appid, hour_start) DO NOTHING
        """)
        
        # Usuń stare surowe dane (starsze niż 24h)
        await conn.execute("""
            DELETE FROM player_counts_raw
            WHERE timestamp < NOW() - INTERVAL '24 hours'
        """)

# Agregacja dzienna
async def aggregate_daily(self):
    """Agreguje dane z player_counts_hourly do player_counts_daily."""
    async with self.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO player_counts_daily 
                (appid, avg_player_count, max_player_count, min_player_count, date)
            SELECT 
                appid,
                AVG(avg_player_count)::int as avg_player_count,
                MAX(max_player_count) as max_player_count,
                MIN(min_player_count) as min_player_count,
                date_trunc('day', hour_start)::date as date
            FROM player_counts_hourly
            WHERE hour_start < date_trunc('day', NOW())
            GROUP BY appid, date
            ON CONFLICT (appid, date) DO NOTHING
        """)
        
        # Usuń stare dane godzinowe (starsze niż 7 dni)
        await conn.execute("""
            DELETE FROM player_counts_hourly
            WHERE hour_start < NOW() - INTERVAL '7 days'
        """)
```

---

## Migracje

Przy każdym starcie serwera automatycznie:

1. ✅ Tworzenie brakujących tabel
2. ✅ Tworzenie indeksów
3. ✅ Seedowanie watchlisty (jeśli pusta)

**Kod:**

```python
async def init_db() -> DatabaseManager:
    """Inicjalizuje bazę danych przy starcie aplikacji."""
    db = DatabaseManager()
    await db.connect()
    await db.create_tables()
    logger.info("Database initialized successfully")
    return db
```

---

## Podsumowanie

| Tabela | Rozmiar | Retencja | Aktualizacja |
|--------|---------|----------|--------------|
| `games` | ~100-1000 | Permanentne | Na żądanie |
| `game_genres` | ~500-5000 | Permanentne | Na żądanie |
| `game_categories` | ~500-5000 | Permanentne | Na żądanie |
| `watchlist` | ~100 | Permanentne | Co 5 minut |
| `player_counts_raw` | Rosnąca | 24 godziny | Co 5 minut |
| `player_counts_hourly` | Rosnąca | 7 dni | Co godzinę |
| `player_counts_daily` | Rosnąca | Permanentne | Codziennie |

---

## Następne Kroki

- **Scheduler**: [SERVER_SCHEDULER.md](SERVER_SCHEDULER.md)
- **Services**: [SERVER_SERVICES.md](SERVER_SERVICES.md)

