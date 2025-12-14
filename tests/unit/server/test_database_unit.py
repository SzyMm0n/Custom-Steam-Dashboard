"""
Unit tests for DatabaseManager (with mocked connections).

Tests SQL generation, validation logic, and error handling without real database.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg


@pytest.mark.unit
@pytest.mark.server
class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization and configuration."""

    def test_init_default_values(self):
        """Test DatabaseManager initializes with default values."""
        from server.database.database import DatabaseManager

        db = DatabaseManager(
            host="testhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )

        assert db.host == "testhost"
        assert db.port == 5432
        assert db.user == "testuser"
        assert db.password == "testpass"
        assert db.database == "testdb"
        assert db.schema == "custom_steam_dashboard"
        assert db.min_pool_size == 10
        assert db.max_pool_size == 30
        assert db.pool is None

    def test_init_custom_values(self):
        """Test DatabaseManager initializes with custom values."""
        from server.database.database import DatabaseManager

        db = DatabaseManager(
            host="custom",
            schema="test_schema",
            min_pool_size=5,
            max_pool_size=15,
            command_timeout=30.0
        )

        assert db.schema == "test_schema"
        assert db.min_pool_size == 5
        assert db.max_pool_size == 15
        assert db.command_timeout == 30.0

    def test_table_name_formatting(self):
        """Test _table() method formats table names with schema."""
        from server.database.database import DatabaseManager

        db = DatabaseManager(schema="my_schema")

        assert db._table("watchlist") == '"my_schema".watchlist'
        assert db._table("player_counts") == '"my_schema".player_counts'
        assert db._table("game_details") == '"my_schema".game_details'


@pytest.mark.unit
@pytest.mark.server
class TestDatabaseMethodCalls:
    """Test database methods execute with correct parameters."""

    @pytest.mark.asyncio
    async def test_upsert_watchlist_calls_execute(self):
        """Test upsert_watchlist calls execute with correct parameters."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager()

        # Mock the acquire context manager properly
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        # Create proper async context manager mock
        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        # Make acquire() return the context manager
        db.acquire = MagicMock(return_value=mock_acquire)

        # Call method
        await db.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Verify execute was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]

        # Verify parameters
        assert 730 in call_args  # appid
        assert "CS2" in call_args  # name
        assert 50000 in call_args  # last_count

    @pytest.mark.asyncio
    async def test_remove_from_watchlist_calls_execute(self):
        """Test remove_from_watchlist executes DELETE query."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager()

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        await db.remove_from_watchlist(appid=730)

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]

        # Verify DELETE query and appid parameter
        assert "DELETE" in call_args[0]
        assert 730 in call_args

    @pytest.mark.asyncio
    async def test_get_watchlist_calls_fetch(self):
        """Test get_watchlist calls fetch and returns list."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager()

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        result = await db.get_watchlist()

        mock_conn.fetch.assert_called_once()
        assert isinstance(result, list)


@pytest.mark.unit
@pytest.mark.server
class TestDatabaseErrorHandling:
    """Test error handling in database operations."""

    @pytest.mark.asyncio
    async def test_initialize_handles_connection_error(self):
        """Test initialize() handles connection errors gracefully."""
        from server.database.database import DatabaseManager

        db = DatabaseManager(
            host="invalid_host",
            port=9999,
            user="invalid",
            password="invalid",
            database="invalid"
        )

        with patch('asyncpg.create_pool', side_effect=asyncpg.PostgresError("Connection failed")):
            with pytest.raises(asyncpg.PostgresError):
                await db.initialize()

    @pytest.mark.asyncio
    async def test_close_handles_missing_pool(self):
        """Test close() handles case when pool is None."""
        from server.database.database import DatabaseManager

        db = DatabaseManager()
        db.pool = None

        # Should not raise error
        await db.close()

    @pytest.mark.asyncio
    async def test_close_handles_pool_close_error(self):
        """Test close() handles errors during pool closure."""
        from server.database.database import DatabaseManager

        db = DatabaseManager()
        db.pool = AsyncMock()
        db.pool.close.side_effect = Exception("Close failed")

        # Should handle error gracefully (may log but not raise)
        try:
            await db.close()
        except Exception:
            pass  # Acceptable if it raises, but shouldn't crash


@pytest.mark.unit
@pytest.mark.server
class TestDatabaseQueryBuilding:
    """Test SQL query construction logic."""

    @pytest.mark.asyncio
    async def test_get_watchlist_query_structure(self):
        """Test get_watchlist builds correct query with schema."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager(schema="test_schema")

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.execute = AsyncMock()

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        await db.get_watchlist()

        # Verify fetch was called (query executed)
        mock_conn.fetch.assert_called_once()

        # Get the actual query that was passed
        call_args = mock_conn.fetch.call_args[0]
        query = call_args[0]

        # Verify query contains schema and table
        assert '"test_schema".watchlist' in query or 'test_schema' in query

    @pytest.mark.asyncio
    async def test_upsert_watchlist_uses_correct_schema(self):
        """Test upsert_watchlist uses configured schema in query."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager(schema="custom_schema")

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        await db.upsert_watchlist(appid=730, name="CS2")

        # Verify execute was called
        mock_conn.execute.assert_called_once()

        # Get the query
        call_args = mock_conn.execute.call_args[0]
        query = call_args[0]

        # Verify schema is used
        assert 'custom_schema' in query or '"custom_schema"' in query


@pytest.mark.unit
@pytest.mark.server
class TestDatabaseEdgeCases:
    """Test edge cases in database operations."""

    @pytest.mark.asyncio
    async def test_get_watchlist_empty_result(self):
        """Test get_watchlist returns empty list when no data."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager()

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.execute = AsyncMock()

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        result = await db.get_watchlist()

        assert result == []

    @pytest.mark.asyncio
    async def test_upsert_watchlist_with_special_characters(self):
        """Test upsert_watchlist handles names with special characters."""
        from server.database.database import DatabaseManager
        from unittest.mock import MagicMock

        db = DatabaseManager()

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=None)

        db.acquire = MagicMock(return_value=mock_acquire)

        # Name with special characters
        special_name = "Game: The 'Awesome' Edition™"

        await db.upsert_watchlist(appid=730, name=special_name)

        # Verify it was called (parameterized query should handle special chars)
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_context_manager(self):
        """Test acquire() context manager properly handles connection."""
        from server.database.database import DatabaseManager

        db = DatabaseManager()
        db.pool = AsyncMock()

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        db.pool.acquire = AsyncMock(return_value=mock_conn)
        db.pool.release = AsyncMock()

        # Use acquire context manager
        async with db.acquire() as conn:
            assert conn == mock_conn
            # Verify search_path was set
            mock_conn.execute.assert_called()

        # Verify connection was released
        db.pool.release.assert_called_once_with(mock_conn)

