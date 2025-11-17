from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from server.database.database import DatabaseManager, DatabaseRollupManager
from server.services.steam_service import SteamClient

logger = logging.getLogger(__name__)


class PlayerCountCollector:
    """
    Collects player count data for games in the watchlist.
    """

    def __init__(self, db: DatabaseManager, steam_client: SteamClient):
        """
        Initialize the player count collector.

        Args:
            db: Database manager instance
            steam_client: Steam API client instance
        """
        self.db = db
        self.steam_client = steam_client
        self.semaphore = asyncio.Semaphore(10)

    async def collect_player_counts(self) -> None:
        """
        Collect player counts for all games in the watchlist.
        This method is called by the scheduler every 5 minutes.
        """
        start_time = datetime.now(timezone.utc)
        try:
            logger.info("Starting player count collection...")
            
            # Get all games from watchlist with timeout
            try:
                watchlist = await asyncio.wait_for(
                    self.db.get_watchlist(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error("Timeout getting watchlist from database")
                return

            if not watchlist:
                logger.info("Watchlist is empty, skipping player count collection")
                return

            logger.info(f"Collecting player counts for {len(watchlist)} games")
            
            success_count = 0
            error_count = 0

            # Collect player counts concurrently with rate limiting
            async def fetch_and_store_count(game: dict) -> bool:
                async with self.semaphore:
                    try:
                        appid = game.get('appid')

                        # Fetch player count with timeout
                        player_count_data = await asyncio.wait_for(
                            self.steam_client.get_player_count(appid),
                            timeout=10.0
                        )

                        # Get current timestamp
                        timestamp = int(datetime.now(timezone.utc).timestamp())

                        # Store in database with timeout
                        await asyncio.wait_for(
                            self.db.insert_player_count(
                                appid=appid,
                                timestamp=timestamp,
                                count=player_count_data.player_count
                            ),
                            timeout=5.0
                        )
                        
                        # Update last_count in watchlist with timeout
                        await asyncio.wait_for(
                            self.db.upsert_watchlist(
                                appid=appid,
                                name=game.get('name'),
                                last_count=player_count_data.player_count
                            ),
                            timeout=5.0
                        )
                        
                        logger.debug(
                            f"Collected player count for {game.get('name')} (appid={appid}): "
                            f"{player_count_data.player_count} players"
                        )
                        return True
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Timeout collecting player count for {game.get('name')} (appid={game.get('appid')})"
                        )
                        return False
                    except Exception as e:
                        logger.error(
                            f"Error collecting player count for {game.get('name')} (appid={game.get('appid')}): {e}"
                        )
                        return False

            # Execute all tasks concurrently with overall timeout
            tasks = [fetch_and_store_count(game) for game in watchlist]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=240.0  # 4 minutes max for entire collection
                )
                success_count = sum(1 for r in results if r is True)
                error_count = len(results) - success_count
            except asyncio.TimeoutError:
                logger.error("Overall timeout reached for player count collection")
                return

            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Player count collection completed in {elapsed_time:.1f}s: "
                f"{success_count} successful, {error_count} failed"
            )

        except Exception as e:
            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(
                f"Error in player count collection job after {elapsed_time:.1f}s: {e}",
                exc_info=True
            )

class WatchlistRefresher:
    """
    Refreshes the watchlist periodically.
    """

    def __init__(self, db: DatabaseManager, steam_client: SteamClient):
        """
        Initialize the watchlist refresher.

        Args:
            db: Database manager instance
            steam_client: Steam API client instance
        """
        self.db = db
        self.steam_client = steam_client
        self.semaphore = asyncio.Semaphore(10)

    async def refresh_watchlist(self) -> None:
        """
        Refresh genres and categories for all games in the watchlist.
        This method can be scheduled to run periodically.
        """
        start_time = datetime.now(timezone.utc)
        try:
            logger.info("Starting watchlist refresh...")

            # Get current most played games with timeout
            try:
                most_played_games = await asyncio.wait_for(
                    self.steam_client.get_most_played_games(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error("Timeout getting most played games")
                return

            if not most_played_games:
                logger.info("No new games available, skipping watchlist refresh")
                return

            logger.info(f"Refreshing {len(most_played_games)} games in the watchlist")

            success_count = 0
            error_count = 0

            async def refresh_game(game) -> bool:
                async with self.semaphore:
                    try:
                        appid = game.appid

                        # Get player count with timeout
                        player_count = await asyncio.wait_for(
                            self.steam_client.get_player_count(appid),
                            timeout=10.0
                        )

                        # Update watchlist with timeout
                        await asyncio.wait_for(
                            self.db.upsert_watchlist(
                                appid=appid,
                                name=game.name,
                                last_count=player_count.player_count
                            ),
                            timeout=5.0
                        )
                        logger.debug(f"Refreshed or inserted for {game.name} (appid={appid})")
                        return True

                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout refreshing {game.name} (appid={game.appid})")
                        return False
                    except Exception as e:
                        logger.error(f"Error refreshing for {game.name} (appid={game.appid}): {e}")
                        return False

            # Execute all tasks concurrently with overall timeout
            tasks = [refresh_game(game) for game in most_played_games]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=300.0  # 5 minutes max
                )
                success_count = sum(1 for r in results if r is True)
                error_count = len(results) - success_count
            except asyncio.TimeoutError:
                logger.error("Overall timeout reached for watchlist refresh")
                return

            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Watchlist refresh completed in {elapsed_time:.1f}s: "
                f"{success_count} successful, {error_count} failed"
            )

        except Exception as e:
            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(
                f"Error in watchlist tags refresh job after {elapsed_time:.1f}s: {e}",
                exc_info=True
            )

class GameDataFiller:
    """
    Fills game data in the games, games_categories, game_genres.
    """

    def __init__(self, db: DatabaseManager, steam_client: SteamClient):
        """
        Initialize the game data filler.

        Args:
            db: Database manager instance
            steam_client: Steam API client instance
        """
        self.db = db
        self.steam_client = steam_client

    async def fill_game_data(self) -> None:
        """
        Fill game genres and categories for games.
        This method can be scheduled to run on finishing watchlist refresh.
        """
        try:
            logger.info("Starting game data fill...")

            # Get watchlist entries with game data
            watchlist = await self.db.get_watchlist()

            if not watchlist:
                logger.info("Watchlist is empty, skipping data fill")
                return

            logger.info(f"Filling game data for {len(watchlist)} games")

            for game in watchlist:
                try:
                    appid = game.get('appid')
                    details = await self.steam_client.get_game_details(appid)

                    if details:
                        await self.db.upsert_game(details)
                        logger.debug(f"Filled game data for {game.get('name')} (appid={appid})")

                except Exception as e:
                    logger.error(
                        f"Error filling game data for {game.get('name')} (appid={game.get('appid')}): {e}"
                    )

            logger.info(f"Game data fill completed for {len(watchlist)} games")

        except Exception as e:
            logger.error(f"Error in game data fill job: {e}", exc_info=True)

class DataCleaner:
    """
    Cleans old player count data from the database.
    """

    def __init__(self, db: DatabaseRollupManager):
        """
        Initialize the data cleaner.

        Args:
            db: Database manager instance
        """
        self.db = db

    async def rollup_hourly_data(self) -> None:
        """
        Rollup hourly data to reduce storage size.
        This method can be scheduled to run periodically.
        """
        try:
            logger.info("Starting hourly data rollup...")

            await self.db.rollup_hourly()

            logger.info("Hourly data rollup completed successfully")

        except Exception as e:
            logger.error(f"Error in hourly data rollup job: {e}", exc_info=True)

    async def rollup_daily_data(self) -> None:
        """
        Rollup daily data to reduce storage size.
        This method can be scheduled to run periodically.
        """
        try:
            logger.info("Starting daily data rollup...")

            await self.db.rollup_daily()

            logger.info("Daily data rollup completed successfully")

        except Exception as e:
            logger.error(f"Error in daily data rollup job: {e}", exc_info=True)

class DataDeleteOld:
    """
    Deletes old player count data from the database.
    """

    def __init__(self, db: DatabaseRollupManager):
        """
        Initialize the data deleter.

        Args:
            db: Database manager instance
        """
        self.db = db

    async def delete_old_hourly_data(self) -> None:
        """
        Delete old hourly data beyond retention period.
        This method can be scheduled to run periodically.
        """
        try:
            logger.info("Starting old hourly data deletion...")

            await self.db.delete_hourly_data()

            logger.info("Old hourly data deletion completed successfully")

        except Exception as e:
            logger.error(f"Error in old hourly data deletion job: {e}", exc_info=True)

    async def delete_old_daily_data(self) -> None:
        """
        Delete old daily data beyond retention period.
        This method can be scheduled to run periodically.
        """
        try:
            logger.info("Starting old daily data deletion...")

            await self.db.delete_daily_data()

            logger.info("Old daily data deletion completed successfully")

        except Exception as e:
            logger.error(f"Error in old daily data deletion job: {e}", exc_info=True)


class SchedulerManager:
    """
    Manages scheduled tasks for the application.
    """

    def __init__(self, db: DatabaseManager, steam_client: SteamClient):
        """
        Initialize the scheduler manager.

        Args:
            db: Database manager instance
            steam_client: Steam API client instance
        """
        self.db = db
        self.steam_client = steam_client
        self.scheduler = AsyncIOScheduler()

        # Create DatabaseRollupManager for data rollup and cleanup operations
        self.rollup_manager = DatabaseRollupManager(db)

        # Initialize job handlers
        self.player_count_collector = PlayerCountCollector(db, steam_client)
        self.watchlist_refresher = WatchlistRefresher(db, steam_client)
        self.game_data_filler = GameDataFiller(db, steam_client)
        self.data_cleaner = DataCleaner(self.rollup_manager)
        self.data_deleter = DataDeleteOld(self.rollup_manager)

    def start(self) -> None:
        """
        Start the scheduler and register all jobs.
        """
        logger.info("Starting scheduler...")
        
        # Add player count collection job - runs every 5 minutes
        self.scheduler.add_job(
            func=self.player_count_collector.collect_player_counts,
            trigger=IntervalTrigger(minutes=5),
            id='player_count_collection',
            name='Collect player counts for watchlist games',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.watchlist_refresher.refresh_watchlist,
            trigger=IntervalTrigger(hours=1),
            next_run_time=datetime.now(timezone.utc),  # Start immediately
            id='watchlist_refresh',
            name='Refresh watchlist',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.game_data_filler.fill_game_data,
            trigger=IntervalTrigger(hours=1),
            next_run_time=datetime.now(timezone.utc)+timedelta(minutes=2),  # Start shortly after watchlist refresh
            id='game_data_fill',
            name='Fill game data for watchlist games',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.data_cleaner.rollup_hourly_data,
            trigger=IntervalTrigger(hours=1),
            id='hourly_data_rollup',
            name='Rollup hourly player count data',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.data_cleaner.rollup_daily_data,
            trigger=IntervalTrigger(days=1),
            id='daily_data_rollup',
            name='Rollup daily player count data',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.data_deleter.delete_old_hourly_data,
            trigger=IntervalTrigger(days=1),
            id='old_hourly_data_deletion',
            name='Delete old hourly player count data',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        self.scheduler.add_job(
            func=self.data_deleter.delete_old_daily_data,
            trigger=IntervalTrigger(days=1),
            id='old_daily_data_deletion',
            name='Delete old daily player count data',
            replace_existing=True,
            max_instances=1,  # Ensure only one instance runs at a time
        ),

        # Start the scheduler
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        logger.info("Jobs scheduled:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")

    def shutdown(self) -> None:
        """
        Shutdown the scheduler gracefully.
        """
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")

    
    async def run_job_now(self, job_id: str) -> None:
        """
        Manually trigger a job to run immediately.

        Args:
            job_id: ID of the job to run
        """
        job = self.scheduler.get_job(job_id)
        if job:
            logger.info(f"Manually triggering job: {job.name}")
            await job.func()
        else:
            logger.warning(f"Job with ID '{job_id}' not found")

