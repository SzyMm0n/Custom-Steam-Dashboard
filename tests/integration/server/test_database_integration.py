"""
Integration tests for DatabaseManager with real Neon database.

Tests actual CRUD operations with transaction rollback for isolation.
"""
import pytest
from datetime import datetime
import asyncpg


@pytest.mark.integration
@pytest.mark.server
@pytest.mark.database
class TestDatabaseIntegrationWatchlist:
    """Test watchlist CRUD operations with real database."""

    @pytest.mark.asyncio
    async def test_upsert_and_get_watchlist_happy_path(self, test_db_manager, test_db_connection):
        """Test adding game to watchlist and retrieving it."""
        # Add game to watchlist
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="Counter-Strike 2",
            last_count=50000
        )

        # Retrieve watchlist
        watchlist = await test_db_manager.get_watchlist()

        # Verify
        assert len(watchlist) == 1
        assert watchlist[0]['appid'] == 730
        assert watchlist[0]['name'] == "Counter-Strike 2"
        assert watchlist[0]['last_count'] == 50000

    @pytest.mark.asyncio
    async def test_upsert_watchlist_updates_existing(self, test_db_manager, test_db_connection):
        """Test upserting same game updates existing record."""
        # Insert initial record
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="CS:GO",
            last_count=30000
        )

        # Update with new values
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="Counter-Strike 2",
            last_count=50000
        )

        # Verify only one record exists with updated values
        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['name'] == "Counter-Strike 2"
        assert watchlist[0]['last_count'] == 50000

    @pytest.mark.asyncio
    async def test_remove_from_watchlist_happy_path(self, test_db_manager, test_db_connection):
        """Test removing game from watchlist."""
        # Add game
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="Counter-Strike 2",
            last_count=50000
        )

        # Remove game
        await test_db_manager.remove_from_watchlist(appid=730)

        # Verify removed
        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_game_does_not_error(self, test_db_manager, test_db_connection):
        """Test removing non-existent game doesn't raise error."""
        # Remove game that doesn't exist
        await test_db_manager.remove_from_watchlist(appid=99999)

        # Should not raise error
        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 0

    @pytest.mark.asyncio
    async def test_upsert_watchlist_with_special_characters(self, test_db_manager, test_db_connection):
        """Test upserting game with special characters in name."""
        special_name = "Game: The 'Awesome' Edition™ & \"Friends\""

        await test_db_manager.upsert_watchlist(
            appid=12345,
            name=special_name,
            last_count=1000
        )

        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['name'] == special_name

    @pytest.mark.asyncio
    async def test_get_watchlist_ordered_by_last_count(self, test_db_manager, test_db_connection):
        """Test watchlist is returned ordered by last_count DESC."""
        # Add multiple games
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)
        await test_db_manager.upsert_watchlist(appid=570, name="Dota 2", last_count=80000)
        await test_db_manager.upsert_watchlist(appid=440, name="TF2", last_count=30000)

        watchlist = await test_db_manager.get_watchlist()

        # Verify order (DESC by last_count)
        assert len(watchlist) == 3
        assert watchlist[0]['appid'] == 570  # Highest count
        assert watchlist[1]['appid'] == 730
        assert watchlist[2]['appid'] == 440  # Lowest count


@pytest.mark.integration
@pytest.mark.server
@pytest.mark.database
class TestDatabaseIntegrationPlayerCounts:
    """Test player count operations with real database."""

    @pytest.mark.asyncio
    async def test_insert_player_count_happy_path(self, test_db_manager, test_db_connection):
        """Test inserting player count record."""
        # First add game to watchlist (foreign key requirement)
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="Counter-Strike 2",
            last_count=50000
        )

        # Insert player count
        timestamp = int(datetime.now().timestamp())
        await test_db_connection.execute(
            f'INSERT INTO "{test_db_manager.schema}".players_raw_count (appid, time_stamp, count) '
            f'VALUES ($1, $2, $3)',
            730, timestamp, 50000
        )

        # Verify inserted
        result = await test_db_connection.fetch(
            f'SELECT * FROM "{test_db_manager.schema}".players_raw_count WHERE appid = $1',
            730
        )

        assert len(result) == 1
        assert result[0]['appid'] == 730
        assert result[0]['count'] == 50000

    @pytest.mark.asyncio
    async def test_insert_player_count_without_watchlist_fails(self, test_db_manager, test_db_connection):
        """Test inserting player count without watchlist entry fails (FK constraint)."""
        # Try to insert player count without watchlist entry
        timestamp = int(datetime.now().timestamp())

        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await test_db_connection.execute(
                f'INSERT INTO "{test_db_manager.schema}".players_raw_count (appid, time_stamp, count) '
                f'VALUES ($1, $2, $3)',
                99999, timestamp, 1000
            )

    @pytest.mark.asyncio
    async def test_insert_duplicate_player_count_fails(self, test_db_manager, test_db_connection):
        """Test inserting duplicate (appid, timestamp) fails (PK constraint)."""
        # Add game to watchlist
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Insert first record
        timestamp = 1234567890
        await test_db_connection.execute(
            f'INSERT INTO "{test_db_manager.schema}".players_raw_count (appid, time_stamp, count) '
            f'VALUES ($1, $2, $3)',
            730, timestamp, 50000
        )

        # Try to insert duplicate (same appid and timestamp)
        with pytest.raises(asyncpg.UniqueViolationError):
            await test_db_connection.execute(
                f'INSERT INTO "{test_db_manager.schema}".players_raw_count (appid, time_stamp, count) '
                f'VALUES ($1, $2, $3)',
                730, timestamp, 60000  # Different count, same key
            )


@pytest.mark.integration
@pytest.mark.server
@pytest.mark.database
class TestDatabaseIntegrationGameDetails:
    """Test game details operations with real database."""

    @pytest.mark.asyncio
    async def test_upsert_game_details_happy_path(self, test_db_manager, test_db_connection):
        """Test inserting game details."""
        # Add game to watchlist first
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Insert game details
        await test_db_connection.execute(
            f'INSERT INTO "{test_db_manager.schema}".games '
            f'(appid, name, detailed_description, header_image, is_free) '
            f'VALUES ($1, $2, $3, $4, $5)',
            730,
            "Counter-Strike 2",
            "A tactical FPS game",
            "https://example.com/cs2.jpg",
            True
        )

        # Verify inserted
        result = await test_db_connection.fetch(
            f'SELECT * FROM "{test_db_manager.schema}".games WHERE appid = $1',
            730
        )

        assert len(result) == 1
        assert result[0]['name'] == "Counter-Strike 2"
        assert result[0]['is_free'] == True

    @pytest.mark.asyncio
    async def test_delete_watchlist_cascades_to_games(self, test_db_manager, test_db_connection):
        """Test deleting watchlist entry cascades to games table."""
        # Add game to watchlist
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Insert game details
        await test_db_connection.execute(
            f'INSERT INTO "{test_db_manager.schema}".games '
            f'(appid, name, detailed_description) '
            f'VALUES ($1, $2, $3)',
            730, "Counter-Strike 2", "Description"
        )

        # Remove from watchlist
        await test_db_manager.remove_from_watchlist(appid=730)

        # Verify game details also removed (CASCADE)
        result = await test_db_connection.fetch(
            f'SELECT * FROM "{test_db_manager.schema}".games WHERE appid = $1',
            730
        )

        assert len(result) == 0


@pytest.mark.integration
@pytest.mark.server
@pytest.mark.database
class TestDatabaseIntegrationConcurrency:
    """Test concurrent database operations."""

    @pytest.mark.asyncio
    async def test_concurrent_inserts_to_watchlist(self, test_db_manager):
        """Test concurrent inserts to watchlist from multiple connections."""
        import asyncio

        # Define insert tasks
        async def insert_game(appid, name):
            await test_db_manager.upsert_watchlist(
                appid=appid,
                name=name,
                last_count=1000 * appid
            )

        # Execute concurrent inserts
        tasks = [
            insert_game(100, "Game 100"),
            insert_game(200, "Game 200"),
            insert_game(300, "Game 300"),
            insert_game(400, "Game 400"),
            insert_game(500, "Game 500"),
        ]

        await asyncio.gather(*tasks)

        # Verify all inserted
        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 5

    @pytest.mark.asyncio
    async def test_transaction_rollback_isolation(self, test_db_manager):
        """Test transaction rollback doesn't affect other connections."""
        # Add game in successful transaction
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Try to add game in failed transaction
        try:
            async with test_db_manager.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        f'INSERT INTO "{test_db_manager.schema}".watchlist '
                        f'(appid, name, last_count) VALUES ($1, $2, $3)',
                        999, "Test Game", 1000
                    )
                    # Force rollback by raising exception
                    raise Exception("Force rollback")
        except Exception:
            pass

        # Verify only first game exists
        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['appid'] == 730


@pytest.mark.integration
@pytest.mark.server
@pytest.mark.database
class TestDatabaseIntegrationEdgeCases:
    """Test edge cases with real database."""

    @pytest.mark.asyncio
    async def test_empty_watchlist(self, test_db_manager, test_db_connection):
        """Test getting empty watchlist."""
        watchlist = await test_db_manager.get_watchlist()
        assert watchlist == []

    @pytest.mark.asyncio
    async def test_very_long_game_name(self, test_db_manager, test_db_connection):
        """Test game name at VARCHAR(255) limit."""
        long_name = "A" * 255

        await test_db_manager.upsert_watchlist(
            appid=12345,
            name=long_name,
            last_count=1000
        )

        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['name'] == long_name

    @pytest.mark.asyncio
    async def test_game_name_exceeds_limit_truncates(self, test_db_manager, test_db_connection):
        """Test game name exceeding VARCHAR(255) is handled."""
        too_long_name = "A" * 300  # Exceeds 255 limit

        # This may raise error or truncate depending on DB settings
        try:
            await test_db_manager.upsert_watchlist(
                appid=12345,
                name=too_long_name,
                last_count=1000
            )

            # If no error, verify truncation
            watchlist = await test_db_manager.get_watchlist()
            assert len(watchlist[0]['name']) <= 255
        except asyncpg.StringDataRightTruncationError:
            # Expected error for exceeding limit
            pass

    @pytest.mark.asyncio
    async def test_zero_last_count(self, test_db_manager, test_db_connection):
        """Test game with zero last_count."""
        await test_db_manager.upsert_watchlist(
            appid=730,
            name="CS2",
            last_count=0
        )

        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['last_count'] == 0

    @pytest.mark.asyncio
    async def test_negative_appid_allowed_by_db(self, test_db_manager, test_db_connection):
        """Test database allows negative appid (no constraint in schema)."""
        # Database schema doesn't prevent negative appids
        await test_db_manager.upsert_watchlist(
            appid=-1,
            name="Invalid Game",
            last_count=0
        )

        watchlist = await test_db_manager.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['appid'] == -1

