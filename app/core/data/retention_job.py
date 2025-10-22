from __future__ import annotations

import argparse
import asyncio
import time
from typing import Optional

# ZMIANA: Poprawka importu na AsyncDatabase (jak wcześniej zrobiliśmy)
from app.core.data.db import AsyncDatabase as Database 
from app.core.services.steam_api import SteamStoreClient


async def seed_watchlist_top(db: Database, limit: int = 150) -> int:
    """Fetch most played games and seed watchlist.
    For each app, also fetch AppDetails and upsert genres/categories.
    Returns number of items inserted/updated.
    """
    inserted = 0
    async with SteamStoreClient() as steam:
        try:
            most = await steam.get_most_played(limit=limit)
        except Exception as e:
            print(f"Failed to fetch most played list: {e}")
            return 0
        for g in most:
            title = g.name
            genres = g.genres or []
            categories = g.categories or []
            try:
                # ZMIANA 1: DODANIE `await`
                await db.add_to_watchlist(g.appid, title or None)
                # ZMIANA 2: DODANIE `await`
                await db.upsert_watchlist_tags(
                    g.appid,
                    genres=(genres or []),
                    categories=(categories or []),
                    replace=True,
                )
                inserted += 1
            except Exception as e:
                print(f"Failed to insert appid={g.appid} into watchlist: {e}")
    return inserted

async def refresh_watchlist_tags(db: Database) -> int:
    """Fetch AppDetails for all watchlisted appids and upsert genres/categories.
    Returns number of apps updated.
    """
    updated = 0
    rows = db.get_watchlist()
    if not rows:
        return 0
    async with SteamStoreClient() as store:
        for appid, title in rows:
            try:
                d = await store.get_app_details(appid)
                if not d:
                    continue
                db.upsert_watchlist_tags(appid, genres=(d.genres or []), categories=(d.categories or []), replace=True)
                updated += 1
            except Exception as e:
                print(f"Failed to refresh tags for appid={appid}: {e}")
    return updated


async def collect_once(db: Database, *, now_ts: Optional[int] = None) -> None:
    now = int(now_ts or time.time())
    watch = db.get_watchlist()
    if not watch:
        print("Watchlist empty. Add some appids first.")
        return
    async with SteamStoreClient() as store:
        for appid, title in watch:
            try:
                pc = await store.get_number_of_current_players(appid)
                db.insert_player_count_raw(appid=appid, ts_unix=now, players=pc.player_count)
                print(f"Inserted raw count for appid={appid} ({title or ''}): {pc.player_count}")
            except Exception as e:
                print(f"Failed to fetch players for appid={appid}: {e}")

    # Rollups around recent windows (safe overlap)
    db.rollup_hourly(since_ts=now - 3 * 3600)
    db.rollup_daily(since_ts=now - 3 * 24 * 3600)

    # Retention purge
    db.purge_retention(now_ts=now)


def main() -> None:
    parser = argparse.ArgumentParser(description="Player count retention job")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Initialize schema; seed watchlist if empty")

    p_seed = sub.add_parser("watch-seed-top", help="Seed watchlist with top most played (default 150)")
    p_seed.add_argument("--limit", type=int, default=150)

    p_add = sub.add_parser("watch-add", help="Add appid to watchlist")
    p_add.add_argument("appid", type=int)
    p_add.add_argument("--title", type=str, default=None)

    p_rm = sub.add_parser("watch-rm", help="Remove appid from watchlist")
    p_rm.add_argument("appid", type=int)

    sub.add_parser("watch-list", help="List watchlist")

    sub.add_parser("watch-refresh-tags", help="Fetch AppDetails for watchlist and update genres/categories")

    sub.add_parser("collect-once", help="Collect one sample for all watched appids, rollup and purge")

    p = parser.parse_args()

    db = Database()
    try:
        if p.cmd == "init":
            db.init_schema()
            print("Schema initialized at:", db.db_path)
            items = db.get_watchlist()
            if not items:
                try:
                    n = asyncio.run(seed_watchlist_top(db, limit=150))
                    print(f"Seeded {n} most played apps into watchlist.")
                except Exception as e:
                    print(f"Seed skipped due to error: {e}")
        elif p.cmd == "watch-seed-top":
            db.init_schema()
            n = asyncio.run(seed_watchlist_top(db, limit=max(1, p.limit)))
            print(f"Seeded {n} apps.")
        elif p.cmd == "watch-add":
            db.init_schema()
            db.add_to_watchlist(p.appid, p.title)
            print("Added to watchlist:", p.appid, p.title or "")
        elif p.cmd == "watch-rm":
            db.init_schema()
            db.remove_from_watchlist(p.appid)
            print("Removed from watchlist:", p.appid)
        elif p.cmd == "watch-list":
            db.init_schema()
            items = db.get_watchlist()
            if not items:
                print("(empty)")
            else:
                for a, t in items:
                    print(a, "-", (t or "(no title)"))
        elif p.cmd == "watch-refresh-tags":
            db.init_schema()
            n = asyncio.run(refresh_watchlist_tags(db))
            print(f"Updated tags for {n} apps.")
        elif p.cmd == "collect-once":
            db.init_schema()
            asyncio.run(collect_once(db))
        else:
            parser.error("Unknown command")
    finally:
        db.close()


if __name__ == "__main__":
    main()
