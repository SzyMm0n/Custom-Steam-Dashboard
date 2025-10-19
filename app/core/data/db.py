from __future__ import annotations

import math
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from platformdirs import user_data_dir

APP_NAME = "Custom-Steam-Dashboard"
APP_AUTHOR = "local"


SCHEMA_SQL = """
-- 1) Surowe próby globalnych graczy (GetNumberOfCurrentPlayers)
CREATE TABLE IF NOT EXISTS player_counts_raw (
  appid     INTEGER NOT NULL,
  ts_unix   INTEGER NOT NULL,   -- sekundowy epoch (UTC)
  players   INTEGER NOT NULL,
  PRIMARY KEY (appid, ts_unix)
);

-- 2) Zbiorcze kubełki godzinowe (rollup)
CREATE TABLE IF NOT EXISTS player_counts_hourly (
  appid       INTEGER NOT NULL,
  hour_unix   INTEGER NOT NULL,     -- epoch zaokrąglony do godziny (UTC)
  avg_players REAL NOT NULL,
  max_players INTEGER NOT NULL,
  p95_players INTEGER NOT NULL,
  samples     INTEGER NOT NULL,
  PRIMARY KEY (appid, hour_unix)
);

-- 3) Zbiorcze kubełki dobowe
CREATE TABLE IF NOT EXISTS player_counts_daily (
  appid       INTEGER NOT NULL,
  date_ymd    TEXT NOT NULL,         -- 'YYYY-MM-DD' (UTC)
  avg_players REAL NOT NULL,
  max_players INTEGER NOT NULL,
  p95_players INTEGER NOT NULL,
  samples     INTEGER NOT NULL,
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


class Database:
    """SQLite persistence for player counts and snapshots.

    Notes:
    - All timestamps are handled in UTC seconds since epoch.
    - Rollups compute p95 using sorted raw samples within each bucket.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "dashboard.sqlite")
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")

    def close(self) -> None:
        self._conn.close()

    # --- schema ---
    def init_schema(self) -> None:
        # Create base schema (no-op if exists)
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

    def upsert_watchlist_tags(
        self,
        appid: int,
        *,
        genres: Optional[Sequence[str]] = None,
        categories: Optional[Sequence[str]] = None,
        replace: bool = True,
    ) -> None:
        """Update tags for given appid. If replace=True (default) existing tags are replaced.
        Empty lists are treated as "clear" when replace=True.
        """
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

    def get_all_watchlist_genres(self) -> List[str]:
        cur = self._conn.execute("SELECT DISTINCT genre FROM watchlist_genres ORDER BY genre")
        return [r[0] for r in cur.fetchall()]

    def get_all_watchlist_categories(self) -> List[str]:
        cur = self._conn.execute("SELECT DISTINCT category FROM watchlist_categories ORDER BY category")
        return [r[0] for r in cur.fetchall()]

    def get_watchlist_filtered(
        self,
        *,
        genres_any: Optional[Sequence[str]] = None,
        genres_all: Optional[Sequence[str]] = None,
        categories_any: Optional[Sequence[str]] = None,
        categories_all: Optional[Sequence[str]] = None,
    ) -> List[Tuple[int, str, List[str], List[str]]]:
        """Return watchlist filtered by genres/categories.
        - *_any: at least one of provided values must match.
        - *_all: all provided values must match.
        If both *_any and *_all are provided for the same dimension, both constraints apply.
        """
        clauses: List[str] = []
        params: List[object] = []

        def _count_subq(table: str, column: str, values: Sequence[str]) -> tuple[str, List[object]]:
            placeholders = ",".join(["?"] * len(values))
            sql = (
                f"(SELECT COUNT(DISTINCT {column}) FROM {table} t "
                f"WHERE t.appid = wl.appid AND {column} IN ({placeholders}))"
            )
            return sql, list(values)

        if genres_any:
            subq, p = _count_subq("watchlist_genres", "genre", list(genres_any))
            clauses.append(f"{subq} >= 1")
            params.extend(p)
        if genres_all:
            subq, p = _count_subq("watchlist_genres", "genre", list(genres_all))
            clauses.append(f"{subq} = {len(genres_all)}")
            params.extend(p)
        if categories_any:
            subq, p = _count_subq("watchlist_categories", "category", list(categories_any))
            clauses.append(f"{subq} >= 1")
            params.extend(p)
        if categories_all:
            subq, p = _count_subq("watchlist_categories", "category", list(categories_all))
            clauses.append(f"{subq} = {len(categories_all)}")
            params.extend(p)

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self._conn.execute(
            f"SELECT wl.appid, wl.title, wg.genre, wc.category FROM watchlist wl INNER JOIN main.watchlist_genres wg on wl.appid = wg.appid INNER JOIN main.watchlist_categories wc on wl.appid = wc.appid {where_sql} ORDER BY wl.appid",
            params,
        )
        return [(int(r[0]), r[1], r[2], r[3] ) for r in cur.fetchall()]

    # --- inserts ---
    def insert_player_count_raw(self, appid: int, ts_unix: int, players: int) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO player_counts_raw(appid, ts_unix, players) VALUES (?, ?, ?)",
            (appid, int(ts_unix), int(players)),
        )
        self._conn.commit()

    def insert_user_snapshot(
        self,
        steamid: str,
        fetched_ts_unix: int,
        appid: int,
        playtime_2w_min: Optional[int],
        playtime_forever_min: Optional[int],
    ) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO user_recent_snapshots
            (steamid, fetched_ts_unix, appid, playtime_2w_min, playtime_forever_min)
            VALUES (?, ?, ?, ?, ?)
            """,
            (steamid, fetched_ts_unix, appid, playtime_2w_min, playtime_forever_min),
        )
        self._conn.commit()

    # --- rollups ---
    @staticmethod
    def _p95(values: Sequence[int]) -> int:
        if not values:
            return 0
        arr = sorted(values)
        k = max(0, int(math.ceil(0.95 * len(arr))) - 1)
        return int(arr[k])

    def rollup_hourly(self, *, since_ts: Optional[int] = None, until_ts: Optional[int] = None, appids: Optional[Iterable[int]] = None) -> int:
        """Compute hourly buckets from raw and upsert rows.

        Returns number of upserted buckets.
        """
        where = []
        params: List[object] = []
        if since_ts is not None:
            where.append("ts_unix >= ?")
            params.append(int(since_ts))
        if until_ts is not None:
            where.append("ts_unix <= ?")
            params.append(int(until_ts))
        if appids is not None:
            appids_list = list(appids)
            if appids_list:
                where.append(f"appid IN ({','.join('?' for _ in appids_list)})")
                params.extend(int(a) for a in appids_list)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        # Fetch raw samples grouped by hour in Python to compute p95 accurately
        cur = self._conn.execute(
            f"""
            SELECT appid,
                   (ts_unix / 3600) * 3600 AS hour_unix,
                   players
            FROM player_counts_raw
            {where_sql}
            ORDER BY appid, hour_unix
            """,
            params,
        )
        buckets: dict[tuple[int, int], List[int]] = {}
        for appid, hour_unix, players in cur.fetchall():
            buckets.setdefault((int(appid), int(hour_unix)), []).append(int(players))

        upserts = 0
        for (appid, hour_unix), values in buckets.items():
            samples = len(values)
            avg_players = sum(values) / samples if samples else 0.0
            max_players = max(values) if values else 0
            p95_players = self._p95(values)
            self._conn.execute(
                """
                INSERT INTO player_counts_hourly(appid, hour_unix, avg_players, max_players, p95_players, samples)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(appid, hour_unix) DO UPDATE SET
                  avg_players=excluded.avg_players,
                  max_players=excluded.max_players,
                  p95_players=excluded.p95_players,
                  samples=excluded.samples
                """,
                (appid, hour_unix, avg_players, max_players, p95_players, samples),
            )
            upserts += 1
        self._conn.commit()
        return upserts

    def rollup_daily(self, *, since_ts: Optional[int] = None, until_ts: Optional[int] = None, appids: Optional[Iterable[int]] = None) -> int:
        """Compute daily buckets from raw and upsert rows.

        Returns number of upserted buckets.
        """
        where = []
        params: List[object] = []
        if since_ts is not None:
            where.append("ts_unix >= ?")
            params.append(int(since_ts))
        if until_ts is not None:
            where.append("ts_unix <= ?")
            params.append(int(until_ts))
        if appids is not None:
            appids_list = list(appids)
            if appids_list:
                where.append(f"appid IN ({','.join('?' for _ in appids_list)})")
                params.extend(int(a) for a in appids_list)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        # Use UTC date from epoch seconds
        cur = self._conn.execute(
            f"""
            SELECT appid,
                   strftime('%Y-%m-%d', ts_unix, 'unixepoch') AS ymd,
                   players
            FROM player_counts_raw
            {where_sql}
            ORDER BY appid, ymd
            """,
            params,
        )
        buckets: dict[tuple[int, str], List[int]] = {}
        for appid, ymd, players in cur.fetchall():
            buckets.setdefault((int(appid), str(ymd)), []).append(int(players))

        upserts = 0
        for (appid, ymd), values in buckets.items():
            samples = len(values)
            avg_players = sum(values) / samples if samples else 0.0
            max_players = max(values) if values else 0
            p95_players = self._p95(values)
            self._conn.execute(
                """
                INSERT INTO player_counts_daily(appid, date_ymd, avg_players, max_players, p95_players, samples)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(appid, date_ymd) DO UPDATE SET
                  avg_players=excluded.avg_players,
                  max_players=excluded.max_players,
                  p95_players=excluded.p95_players,
                  samples=excluded.samples
                """,
                (appid, ymd, avg_players, max_players, p95_players, samples),
            )
            upserts += 1
        self._conn.commit()
        return upserts

    # --- retention ---
    def purge_retention(self, *, now_ts: Optional[int] = None) -> None:
        now = int(now_ts or time.time())
        raw_keep_since = now - 14 * 24 * 3600
        hourly_keep_since = now - 30 * 24 * 3600
        daily_keep_since = now - 90 * 24 * 3600

        # raw
        self._conn.execute("DELETE FROM player_counts_raw WHERE ts_unix < ?", (raw_keep_since,))
        # hourly (compare hour_unix)
        self._conn.execute("DELETE FROM player_counts_hourly WHERE hour_unix < ?", (hourly_keep_since,))
        # daily (compare by date string)
        cutoff_ymd = time.strftime("%Y-%m-%d", time.gmtime(daily_keep_since))
        self._conn.execute("DELETE FROM player_counts_daily WHERE date_ymd < ?", (cutoff_ymd,))
        self._conn.commit()

    # --- queries for graphs ---
    def get_series_5min(self, appid: int, *, since_ts: int, until_ts: int) -> List[SeriesPoint]:
        """Aggregate raw into 5-minute buckets on the fly for charting last ~14d."""
        cur = self._conn.execute(
            """
            SELECT ((ts_unix/300)*300) AS bucket_ts, AVG(players) AS avg_p, MAX(players) AS max_p
            FROM player_counts_raw
            WHERE appid=? AND ts_unix BETWEEN ? AND ?
            GROUP BY bucket_ts
            ORDER BY bucket_ts
            """,
            (appid, int(since_ts), int(until_ts)),
        )
        return [SeriesPoint(int(ts), float(avg), int(mx)) for ts, avg, mx in cur.fetchall()]

    def get_series_hourly(self, appid: int, *, since_ts: int, until_ts: int) -> List[SeriesPoint]:
        cur = self._conn.execute(
            """
            SELECT hour_unix, avg_players, max_players
            FROM player_counts_hourly
            WHERE appid=? AND hour_unix BETWEEN ? AND ?
            ORDER BY hour_unix
            """,
            (appid, int(since_ts), int(until_ts)),
        )
        return [SeriesPoint(int(ts), float(avg), int(mx)) for ts, avg, mx in cur.fetchall()]

    def get_series_daily(self, appid: int, *, since_ymd: str, until_ymd: str) -> List[tuple[str, float, int]]:
        cur = self._conn.execute(
            """
            SELECT date_ymd, avg_players, max_players
            FROM player_counts_daily
            WHERE appid=? AND date_ymd BETWEEN ? AND ?
            ORDER BY date_ymd
            """,
            (appid, since_ymd, until_ymd),
        )
        return [(str(d), float(avg), int(mx)) for d, avg, mx in cur.fetchall()]


# --- tiny demo ---
if __name__ == "__main__":
    db = Database()
    db.init_schema()
    now = int(time.time())
    print(db.db_path)
    # seed few samples for a demo appid
    appid = 2807960
    for i in range(12):
        db.insert_player_count_raw(appid, now - i * 300, 1000 + i * 10)

    up_h = db.rollup_hourly(since_ts=now - 3600 * 2)
    up_d = db.rollup_daily(since_ts=now - 3600 * 24)
    print("hourly upserts:", up_h, "daily upserts:", up_d)

    five = db.get_series_5min(appid, since_ts=now - 3600, until_ts=now)
    print("5-min points:", five[:2], "...", len(five))

    db.add_to_watchlist(2807960, "Battlefield 6")
    db.add_to_watchlist(570, "Dota 2")
    db.upsert_watchlist_tags(570, genres=["Action", "Strategy"], categories=["Multi-player"])
    watch = db.get_watchlist()
    print("watchlist (first 2):", watch[:2])
    print("genres:", db.get_all_watchlist_genres()[:5])
    print("categories:", db.get_all_watchlist_categories()[:5])
    filtered = db.get_watchlist_filtered(genres_all=["Action"], categories_any=["Multi-player"])
    print("filtered:", filtered)
    db.purge_retention(now_ts=now)
    db.close()
