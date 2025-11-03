"""
PostgreSQL database module using asyncpg for Custom Steam Dashboard.
Handles schema creation, table management, and database operations.
"""
import os

import asyncio
import asyncpg
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from server.services.models import SteamGameDetails

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations using asyncpg.
    """

    def __init__(
        self,
        host: str = os.getenv("PGHOST") or"localhost",
        port: int = os.getenv("PGPORT") or 5432,
        user: str = os.getenv("PGUSER") or "postgres",
        password: str = os.getenv("PGPASSWORD") or "password",
        database: str = os.getenv("PGDATABASE") or "postgres",
        schema: str = "custom-steam-dashboard",
        min_pool_size: int = 10,
        max_pool_size: int = 20,
    ):
        """
        Initialize the database manager.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            user: Database user
            password: Database password
            database: Database name
            schema: Schema name to use/create
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.schema = schema
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """
        Initialize database connection pool, create schema and tables.
        """
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
            )
            logger.info(f"Database connection pool created successfully")

            # Create schema and tables
            await self._create_schema()
            await self._create_tables()
            logger.info("Database initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def close(self):
        """
        Close database connection pool.
        """
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def _create_schema(self):
        """
        Create the custom schema if it doesn't exist.
        """
        async with self.pool.acquire() as conn:
            # Create schema
            await conn.execute(
                f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'
            )
            # Set search path to include the schema
            await conn.execute(
                f'SET search_path TO "{self.schema}", public'
            )
            logger.info(f"Schema '{self.schema}' created/verified")

    async def _create_tables(self):
        """
        Create all necessary tables for the Steam Dashboard.
        """
        async with self.pool.acquire() as conn:
            # Set search path for this connection
            await conn.execute(
                f'SET search_path TO "{self.schema}", public'
            )

            # Watchlist table - stores identifiers for games being tracked
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist
                (
                appid INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                last_count INTEGER NOT NULL
                )
            """)
            # Players count table - stores raw player count for each game
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS players_raw_count(
                appid INTEGER REFERENCES watchlist(appid) NOT NULL ,
                time_stamp INTEGER NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (appid, time_stamp)
                )
            """)
            #  Players count hourly - stores hourly aggregated player counts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS player_counts_hourly (
                appid INTEGER NOT NULL,
                hour_unix INTEGER NOT NULL,
                avg_players INTEGER NOT NULL,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                p95_players INTEGER NOT NULL,
                PRIMARY KEY (appid, hour_unix)
                )
            """)
            # Players count daily - stores daily aggregated player counts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS player_counts_daily (
                appid INTEGER NOT NULL,
                date_dmy TEXT NOT NULL,
                avg_players INTEGER NOT NULL,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                p95_players INTEGER NOT NULL,
                PRIMARY KEY (appid, date_dmy)
                )
            """)
            # Games table - stores game information
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    appid INTEGER REFERENCES watchlist (appid) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    detailed_description TEXT,
                    header_image VARCHAR(512),
                    background_image VARCHAR(512),
                    release_date VARCHAR(100),
                    price DECIMAL(10, 2),
                    is_free BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (appid)
                )
            """)
            # Game categories - relacja many-to-many między grami a kategoriami
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_categories
                (
                appid  INTEGER REFERENCES games (appid) ON DELETE CASCADE,
                category VARCHAR(50) NOT NULL,
                PRIMARY KEY (appid, category)
                )
            """)
            # Game genres - relacja many-to-many między grami a gatunkami
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_genres
                (
                appid INTEGER REFERENCES games (appid) ON DELETE CASCADE,
                genre VARCHAR(50) NOT NULL,
                PRIMARY KEY (appid, genre)
                ) 
            """)
            #TODO: Additional tables for user management, reviews, and wishlists can be added here

            # User wishlists
            # await conn.execute("""
            #     CREATE TABLE IF NOT EXISTS user_wishlist (
            #         id SERIAL PRIMARY KEY,
            #         steam_id BIGINT REFERENCES users(steam_id) ON DELETE CASCADE,
            #         app_id BIGINT REFERENCES games(app_id) ON DELETE CASCADE,
            #         priority INTEGER DEFAULT 0,
            #         added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         UNIQUE(steam_id, app_id)
            #     )
            # """)

            logger.info("All tables created successfully")

    async def seed_watchlist(self, steam_client: 'SteamClient') -> None:
        """
        Seed the watchlist table with top 100 most played games from Steam.

        Args:
            steam_client: SteamClient instance for fetching game data
        """
        logger.info("Seeding watchlist table with top 100 most played games...")

        # Check if watchlist already has data
        existing_watchlist = await self.get_watchlist()
        if existing_watchlist:
            logger.info(f"Watchlist already contains {len(existing_watchlist)} games, skipping seed")
            return

        try:
            # Get top 100 most played games
            most_played_games = await steam_client.get_most_played_games()

            if not most_played_games:
                logger.warning("No games returned from Steam API")
                return

            logger.info(f"Fetched {len(most_played_games)} games from Steam API")

            # Add each game to watchlist
            for game in most_played_games:
                try:
                    await self.upsert_watchlist(game.appid, game.name, 0)
                    logger.debug(f"   ✓ Added {game.name} (appid={game.appid})")
                except Exception as e:
                    logger.error(f"Error adding {game.name} to watchlist: {e}")

            # Verify the seed
            final_watchlist = await self.get_watchlist()
            logger.info(f"Watchlist seeded successfully with {len(final_watchlist)} games")

        except Exception as e:
            logger.error(f"Error seeding watchlist: {e}", exc_info=True)

    @asynccontextmanager
    async def acquire(self):
        """
        Context manager for acquiring a database connection from the pool.
        
        Usage:
            async with db.acquire() as conn:
                await conn.execute(...)
        """
        async with self.pool.acquire() as connection:
            await connection.execute(f'SET search_path TO "{self.schema}", public')
            yield connection

    # Watchlist operations
    async def upsert_watchlist(self, appid: int, name: str, last_count: int = 0) -> None:
        """
        Add a game to the watchlist.

        Args:
            appid: Steam app ID
            name: Game name
            last_count: Last recorded player count
        """
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO watchlist (appid, name, last_count)
                VALUES ($1, $2, $3)
                ON CONFLICT (appid) DO UPDATE 
                SET last_count = EXCLUDED.last_count
            """, appid, name, last_count)

    async def remove_from_watchlist(self, appid: int) -> None:
        """
        Remove a game from the watchlist.

        Args:
            appid: Steam app ID
        """
        async with self.acquire() as conn:
            await conn.execute(" DELETE FROM watchlist WHERE appid = $1", appid)

    async def get_watchlist(self) -> List[Dict[str, Any]]:
        """
        Retrieve the entire watchlist.

        Returns:
            List of dictionaries containing watchlist entries
        """
        async with self.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM watchlist ORDER BY last_count DESC")
            return [dict(row) for row in rows]

    # Game operations
    async def upsert_game_genres(self, appid: int, genres: List[str]) -> None:
        """
        Insert or update game genres.

        Args:
            appid: Steam app ID
            genres: List of genres
        """
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_genres (appid, genre) VALUES ($1, UNNEST($2::VARCHAR[]))
                ON CONFLICT (appid, genre) DO NOTHING 
            """, appid, genres)
    async def upsert_game_categories(self, appid: int, categories: List[str]) -> None:
        """
        Insert or update game categories.

        Args:
            appid: Steam app ID
            categories: List of categories
        """
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_categories (appid, category) VALUES ($1, UNNEST($2::VARCHAR[]))
                ON CONFLICT (appid, category) DO NOTHING 
            """, appid, categories)

    async def upsert_game(self, game_data: 'SteamGameDetails') -> None:
        """
        Insert or update game information.
        
        Args:
            game_data: Dictionary containing game information
        """
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO games (
                    appid, name, detailed_description, header_image,
                    background_image, release_date, price, is_free
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (appid) DO NOTHING 
            """,
                game_data.appid,
                game_data.name,
                game_data.detailed_description,
                game_data.header_image,
                game_data.background_image,
                game_data.release_date,
                game_data.price,
                game_data.is_free
            )
            # Upsert genres and categories
            await self.upsert_game_genres(game_data.appid, game_data.genres)
            await self.upsert_game_categories(game_data.appid, game_data.categories)

    async def get_game(self, appid: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve game information by app ID.
        
        Args:
            appid: Steam app ID
            
        Returns:
            Dictionary containing game information or None
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT
                     g.*,
                     ARRAY_AGG(DISTINCT gg.genre) AS genres,
                     ARRAY_AGG(DISTINCT gc.category) AS categories
                   FROM games g
                   LEFT JOIN game_genres gg ON g.appid = gg.appid
                   LEFT JOIN game_categories gc ON g.appid = gc.appid
                   WHERE g.appid = $1
                   GROUP BY g.appid
                """,
                appid
            )
            return dict(row) if row else None

    async def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Retrieve all games from the database.
        
        Returns:
            List of dictionaries containing game information
        """
        async with self.acquire() as conn:
            rows = await conn.fetch("""SELECT
                     g.*,
                     ARRAY_AGG(DISTINCT gg.genre) AS genres,
                     ARRAY_AGG(DISTINCT gc.category) AS categories
                   FROM games g
                   LEFT JOIN game_genres gg ON g.appid = gg.appid
                   LEFT JOIN game_categories gc ON g.appid = gc.appid
                   GROUP BY g.appid
                """)
            return [dict(row) for row in rows]

    async def get_games_filtered_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """
        Retrieve games filtered by a specific genre.

        Args:
            genre: Genre to filter by

        Returns:
            List of dictionaries containing game information
        """
        async with self.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    g.*,
                    ARRAY_AGG(DISTINCT gg.genre) AS genres,
                    ARRAY_AGG(DISTINCT gc.category) AS categories
                FROM games g
                JOIN game_genres gg ON g.appid = gg.appid
                LEFT JOIN game_categories gc ON g.appid = gc.appid
                WHERE gg.genre = $1
                GROUP BY g.appid
            """, genre)
            return [dict(row) for row in rows]

    async def get_games_filtered_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Retrieve games filtered by a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of dictionaries containing game information
        """
        async with self.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    g.*,
                    ARRAY_AGG(DISTINCT gg.genre) AS genres,
                    ARRAY_AGG(DISTINCT gc.category) AS categories
                FROM games g
                JOIN game_categories gc ON g.appid = gc.appid
                LEFT JOIN game_genres gg ON g.appid = gg.appid
                WHERE gc.category = $1
                GROUP BY g.appid
            """, category)
            return [dict(row) for row in rows]

    # Player count operations
    async def insert_player_count(self, appid: int, timestamp: int, count: int) -> None:
        """
        Insert a raw player count record.

        Args:
            appid: Steam app ID
            timestamp: Unix timestamp
            count: Player count
        """
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO players_raw_count (appid, time_stamp, count)
                VALUES ($1, $2, $3)
            """, appid, timestamp, count)

    async def get_player_count_history(self, appid: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve player count history for a game.

        Args:
            appid: Steam app ID
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing player count records
        """
        async with self.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM players_raw_count
                WHERE appid = $1
                ORDER BY time_stamp DESC
                LIMIT $2
            """, appid, limit)
            return [dict(row) for row in rows]
class DatabaseRollupManager:
    """
    Manages rollup operations for player count data.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the rollup manager.

        Args:
            db: DatabaseManager instance
        """
        self.db = db

    async def rollup_hourly(self) -> None:
        """
        Perform hourly rollup of player count data.
        """
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO player_counts_hourly (appid, hour_unix, avg_players, min_players, max_players, p95_players)
                SELECT
                    appid,
                    date_trunc('hour', to_timestamp(time_stamp))::int AS hour_unix,
                    AVG(count) AS avg_players,
                    MIN(count) AS min_players,
                    MAX(count) AS max_players,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY count) AS p95_players
                FROM players_raw_count
                GROUP BY appid, hour_unix
                ON CONFLICT (appid, hour_unix) DO NOTHING 
            """)
            logger.info("Hourly rollup completed")

    async def rollup_daily(self) -> None:
        """
        Perform daily rollup of player count data.
        """
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO player_counts_daily (appid, date_dmy, avg_players, min_players, max_players, p95_players)
                SELECT
                    appid,
                    to_char(to_timestamp(time_stamp), 'YYYY-MM-DD') AS date_dmy,
                    AVG(count) AS avg_players,
                    MIN(count) AS min_players,
                    MAX(count) AS max_players,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY count) AS p95_players
                FROM players_raw_count
                GROUP BY appid, date_dmy
                ON CONFLICT (appid, date_dmy) DO NOTHING
            """)
            logger.info("Daily rollup completed")

    async def delete_old_raw_data(self, days: int = 14) -> None:
        """
        Delete raw player count data older than a specified number of days.

        Args:
            days: Number of days to retain data
        """
        cutoff_timestamp = int((asyncio.get_event_loop().time() - days * 86400))
        async with self.db.acquire() as conn:
            await conn.execute("""
                DELETE FROM players_raw_count
                WHERE time_stamp < $1
            """, cutoff_timestamp)
            logger.info(f"Old raw data older than {days} days deleted")

    async def delete_daily_data(self, days: int = 90) -> None:
        """
        Delete daily aggregated player count data older than a specified number of days.

        Args:
            days: Number of days to retain data
        """
        cutoff_date = (asyncio.get_event_loop().time() - days * 86400)
        async with self.db.acquire() as conn:
            await conn.execute("""
                DELETE FROM player_counts_daily
                WHERE to_date(date_dmy, 'YYYY-MM-DD') < to_timestamp($1)
            """, cutoff_date)
            logger.info(f"Old daily data older than {days} days deleted")

    async def delete_hourly_data(self, days: int = 30) -> None:
        """
        Delete hourly aggregated player count data older than a specified number of days.

        Args:
            days: Number of days to retain data
        """
        cutoff_timestamp = int((asyncio.get_event_loop().time() - days * 86400))
        async with self.db.acquire() as conn:
            await conn.execute("""
                DELETE FROM player_counts_hourly
                WHERE hour_unix < $1
            """, cutoff_timestamp)
            logger.info(f"Old hourly data older than {days} days deleted")

# Global database instance
db: Optional[DatabaseManager] = None


async def init_db() -> DatabaseManager:
    """
    Initialize the global database instance.

    Returns:
        Initialized DatabaseManager instance
    """
    global db
    db = DatabaseManager(
        host=os.getenv("PGHOST") or "localhost",
        port=os.getenv("PGPORT") or 5432,
        user=os.getenv("PGUSER") or "postgres",
        password=os.getenv("PGPASSWORD") or "",
        database=os.getenv("PGDATABASE") or "postgres",
        schema="custom_steam_dashboard",
    )
    await db.initialize()
    return db


async def close_db():
    """
    Close the global database instance.
    """
    global db
    if db:
        await db.close()
        db = None


if __name__ == '__main__':
    import asyncio
    load_dotenv(dotenv_path="../../.env")

    async def main():
        database = await init_db()
        print('Database initialized successfully.')

        await close_db()

    asyncio.run(main())



