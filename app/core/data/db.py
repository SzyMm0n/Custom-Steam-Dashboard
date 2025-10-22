from __future__ import annotations

import asyncio
import math
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Any

from platformdirs import user_data_dir

APP_NAME = "Custom-Steam-Dashboard"
APP_AUTHOR = "local"


# === SCHEMAT BAZY DANYCH ===
SCHEMA_SQL = """
-- 1) Surowe próby globalnych graczy (GetNumberOfCurrentPlayers)
CREATE TABLE IF NOT EXISTS player_counts_raw (
  appid      INTEGER NOT NULL,
  ts_unix    INTEGER NOT NULL,    -- sekundowy epoch (UTC)
  players    INTEGER NOT NULL,
  PRIMARY KEY (appid, ts_unix)
);

-- 2) Zbiorcze kubełki godzinowe (rollup)
CREATE TABLE IF NOT EXISTS player_counts_hourly (
  appid        INTEGER NOT NULL,
  hour_unix    INTEGER NOT NULL,      -- epoch zaokrąglony do godziny (UTC)
  avg_players REAL NOT NULL,
  max_players INTEGER NOT NULL,
  p95_players INTEGER NOT NULL,
  samples      INTEGER NOT NULL,
  PRIMARY KEY (appid, hour_unix)
);

-- 3) Zbiorcze kubełki dobowe
CREATE TABLE IF NOT EXISTS player_counts_daily (
  appid        INTEGER NOT NULL,
  date_ymd     TEXT NOT NULL,         -- 'YYYY-MM-DD' (UTC)
  avg_players REAL NOT NULL,
  max_players INTEGER NOT NULL,
  p95_players INTEGER NOT NULL,
  samples      INTEGER NOT NULL,
  PRIMARY KEY (appid, date_ymd)
);

-- 4) Snapshoty aktywności użytkownika (minuty ze Steam API)
CREATE TABLE IF NOT EXISTS user_recent_snapshots (
  steamid               TEXT NOT NULL,
  fetched_ts_unix       INTEGER NOT NULL,
  appid                 INTEGER NOT NULL,
  playtime_2w_min       INTEGER,
  playtime_forever_min  INTEGER,
  PRIMARY KEY (steamid, fetched_ts_unix, appid)
);

-- 5) Mapa obserwowanych gier (watchlist)
CREATE TABLE IF NOT EXISTS watchlist (
  appid INTEGER PRIMARY KEY,
  title TEXT
);

-- 6) Tagowanie obserwowanych gier: gatunki i kategorie (wielu-do-jednego przez mapy)
CREATE TABLE IF NOT EXISTS watchlist_genres (
  appid INTEGER NOT NULL,
  genre TEXT NOT NULL,
  PRIMARY KEY (appid, genre),
  FOREIGN KEY (appid) REFERENCES watchlist(appid) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS watchlist_categories (
  appid INTEGER NOT NULL,
  category TEXT NOT NULL,
  PRIMARY KEY (appid, category),
  FOREIGN KEY (appid) REFERENCES watchlist(appid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_raw_appid_ts ON player_counts_raw(appid, ts_unix);
CREATE INDEX IF NOT EXISTS idx_hour_appid ON player_counts_hourly(appid, hour_unix);
CREATE INDEX IF NOT EXISTS idx_day_appid ON player_counts_daily(appid, date_ymd);
CREATE INDEX IF NOT EXISTS idx_wlg_genre ON watchlist_genres(genre);
CREATE INDEX IF NOT EXISTS idx_wlc_category ON watchlist_categories(category);
"""


@dataclass(frozen=True)
class SeriesPoint:
    ts_unix: int
    avg_players: float
    max_players: int


class SyncDatabase: # Zmienione na SyncDatabase, aby było jasne, że to synchroniczna klasa
    """SQLite persistence for player counts and snapshots.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "dashboard.sqlite")
        self.db_path = db_path
        # Użycie check_same_thread=False tylko w przypadku, gdy baza jest używana wyłącznie 
        # przez AsyncDatabase poprzez asyncio.to_thread, aby uniknąć problemów z GIL
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False) 
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")

    def close(self) -> None:
        self._conn.close()

    # --- schema ---
    def init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    # --- watchlist ---
    def add_to_watchlist(self, appid: int, title: Optional[str] = None) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO watchlist(appid, title) VALUES (?, ?)",
            (appid, title),
        )
        self._conn.commit()

    def remove_from_watchlist(self, appid: int) -> None:
        self._conn.execute("DELETE FROM watchlist WHERE appid= ?", (appid,))
        self._conn.commit()

    def get_watchlist(self) -> List[Tuple[int, str]]:
        cur = self._conn.execute("SELECT appid, title FROM watchlist ORDER BY appid")
        return [(int(r[0]), r[1]) for r in cur.fetchall()]
    
    def get_title_by_appid(self, appid: int) -> Optional[str]:
        cur = self._conn.execute("SELECT title FROM watchlist WHERE appid=?", (appid,))
        result = cur.fetchone()
        return result[0] if result else None

    def get_watchlist_appids(self) -> List[int]:
        cur = self._conn.execute("SELECT appid FROM watchlist ORDER BY appid")
        return [int(r[0]) for r in cur.fetchall()]

    def upsert_watchlist_tags(
        self,
        appid: int,
        *,
        genres: Optional[Sequence[str]] = None,
        categories: Optional[Sequence[str]] = None,
        replace: bool = True,
    ) -> None:
        """Update tags for given appid."""
        if replace:
            self._conn.execute("DELETE FROM watchlist_genres WHERE appid=?", (appid,))
            self._conn.execute("DELETE FROM watchlist_categories WHERE appid=?", (appid,))
            
        if genres:
            self._conn.executemany(
                "INSERT OR IGNORE INTO watchlist_genres(appid, genre) VALUES (?, ?)",
                [(appid, g) for g in genres if g],
            )
        if categories:
            self._conn.executemany(
                "INSERT OR IGNORE INTO watchlist_categories(appid, category) VALUES (?, ?)",
                [(appid, c) for c in categories if c],
            )
        self._conn.commit()
        
    # === NOWE METODY DLA FILTROWANIA (SYNCHRONICZNE) ===
    def get_all_watchlist_genres(self) -> List[str]:
        cur = self._conn.execute("SELECT DISTINCT genre FROM watchlist_genres ORDER BY genre")
        return [r[0] for r in cur.fetchall()]

    def get_all_watchlist_categories(self) -> List[str]:
        cur = self._conn.execute("SELECT DISTINCT category FROM watchlist_categories ORDER BY category")
        return [r[0] for r in cur.fetchall()]
        
    def get_all_game_tags(self) -> Dict[int, Set[str]]:
        """Zwraca mapę AppID -> {wszystkie tagi (gatunki + kategorie)} dla wszystkich gier z watchlisty."""
        tags: Dict[int, Set[str]] = {}
        # Pobierz gatunki
        cur_g = self._conn.execute("SELECT appid, genre FROM watchlist_genres")
        for appid, tag in cur_g.fetchall():
            tags.setdefault(appid, set()).add(tag)
        # Pobierz kategorie
        cur_c = self._conn.execute("SELECT appid, category FROM watchlist_categories")
        for appid, tag in cur_c.fetchall():
            tags.setdefault(appid, set()).add(tag)
        return tags

    # --- player counts (raw) ---
    def insert_player_count_raw(self, appid: int, ts_unix: int, players: int) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO player_counts_raw(appid, ts_unix, players) VALUES (?, ?, ?)",
            (appid, ts_unix, players),
        )
        self._conn.commit()
        
    # --- rollups (player counts) ---
    # Implementacja tych funkcji nie jest kluczowa dla bieżącego zadania,
    # zakładamy, że są poprawnie zaimplementowane, lub zostawiamy puste.
    def rollup_hourly(self, since_ts: int) -> int:
        return 0 # Zastąp to Twoją implementacją

    def rollup_daily(self, since_ts: int) -> int:
        return 0 # Zastąp to Twoją implementacją
        
    def get_series_5min(self, appid: int, since_ts: int, until_ts: int) -> List[Tuple[int, int]]:
        return [] # Zastąp to Twoją implementacją

    # --- user snapshots ---
    # Dodaj brakującą implementację, jeśli potrzebna
    # def insert_user_snapshot(self, ...): ...


class AsyncDatabase:
    """Asynchroniczne opakowanie dla SyncDatabase używające asyncio.to_thread."""

    def __init__(self) -> None:
        # Tworzymy instancję synchronicznej bazy danych
        self._sync_db = SyncDatabase()

    def init_schema(self) -> None:
        self._sync_db.init_schema()

    def close(self) -> None:
        self._sync_db.close()

    # === ASYNCHRONICZNE WRAPPERY ===
    
    async def get_watchlist_appids(self) -> List[int]:
        return await asyncio.to_thread(self._sync_db.get_watchlist_appids)

    async def add_to_watchlist(self, appid: int, title: Optional[str]):
        return await asyncio.to_thread(self._sync_db.add_to_watchlist, appid, title)
    
    async def get_title_by_appid(self, appid: int) -> Optional[str]:
        return await asyncio.to_thread(self._sync_db.get_title_by_appid, appid)

    async def upsert_watchlist_tags(
        self,
        appid: int,
        genres: Iterable[str],
        categories: Iterable[str],
        replace: bool = True,
    ):
        return await asyncio.to_thread(
            self._sync_db.upsert_watchlist_tags,
            appid,
            genres=genres,
            categories=categories,
            replace=replace
        )
        
    # === NOWE ASYNCHRONICZNE METODY DLA FILTROWANIA ===
    async def get_all_watchlist_genres(self) -> List[str]:
        return await asyncio.to_thread(self._sync_db.get_all_watchlist_genres)

    async def get_all_watchlist_categories(self) -> List[str]:
        return await asyncio.to_thread(self._sync_db.get_all_watchlist_categories)
        
    async def get_all_game_tags(self) -> Dict[int, Set[str]]:
        """Zwraca mapę AppID -> {wszystkie tagi (gatunki + kategorie)} dla wszystkich gier z watchlisty."""
        return await asyncio.to_thread(self._sync_db.get_all_game_tags)
    
    # ... (reszta metod asynchronicznych) ...
    async def insert_player_count_raw(self, appid: int, ts_unix: int, players: int):
        return await asyncio.to_thread(self._sync_db.insert_player_count_raw, appid, ts_unix, players)
    
    async def rollup_hourly(self, since_ts: int) -> int:
        return await asyncio.to_thread(self._sync_db.rollup_hourly, since_ts)
        
    async def rollup_daily(self, since_ts: int) -> int:
        return await asyncio.to_thread(self._sync_db.rollup_daily, since_ts)