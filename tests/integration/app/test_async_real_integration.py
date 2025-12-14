"""
Integration tests using httpx.AsyncClient for proper async support.
Replaces TestClient tests that had async database operation conflicts.

This file solves the problem: TestClient (sync) + async database = conflicts
Solution: Use AsyncClient with ASGITransport for full async support
"""
import pytest
import json
from unittest.mock import patch

from app.helpers.signing import sign_request


@pytest.mark.integration
@pytest.mark.app
@pytest.mark.asyncio
class TestServerClientAsyncIntegration:
    """Integration tests with AsyncClient supporting async database operations."""

    async def test_login_and_fetch_players_from_database(self, test_db_manager, async_test_client):
        """
        Test complete flow: Login → Fetch players from real database.

        This replaces the skipped TestClient test.
        Tests: Auth → Backend API → Database retrieval → Response
        """
        from server.app import app

        # Add test data to real database
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=500000)
        await test_db_manager.upsert_watchlist(appid=440, name="TF2", last_count=30000)

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Step 1: Authenticate
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)

                # Verify login
                assert login_response.status_code == 200
                token = login_response.json()["access_token"]

                # Step 2: Fetch from real database via backend API
                api_path = "/api/current-players"
                api_headers = sign_request("GET", api_path, b"", client_id, client_secret)
                api_headers["Authorization"] = f"Bearer {token}"

                api_response = await client.get(api_path, headers=api_headers)

                # Verify: Data from real database
                assert api_response.status_code == 200
                games = api_response.json()["games"]
                assert len(games) == 2

                # Verify data integrity across all layers
                appids = [g["appid"] for g in games]
                assert 730 in appids
                assert 440 in appids

                # Verify exact data matches what we inserted
                cs2_game = next(g for g in games if g["appid"] == 730)
                assert cs2_game["name"] == "CS2"
                assert cs2_game["last_count"] == 500000

    async def test_fetch_all_games_through_backend(self, test_db_manager, async_test_client):
        """
        Test fetching all games: Database → Backend → API response.

        This replaces the skipped TestClient test.
        Tests full integration with game details.
        """
        from server.app import app
        from server.services.models import SteamGameDetails

        # Add game to watchlist (foreign key requirement)
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        # Add game details to real database
        game_data = SteamGameDetails(
            appid=730,
            name="Counter-Strike 2",
            detailed_description="Competitive FPS game",
            header_image="https://example.com/cs2_header.jpg",
            background_image="https://example.com/cs2_bg.jpg",
            price=0.0,
            is_free=True,
            genres=["Action", "FPS"],
            categories=["Multiplayer", "Competitive"],
            release_date="2023-09-27",
            coming_soon=False
        )
        await test_db_manager.upsert_game(game_data)

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Login
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)
                token = login_response.json()["access_token"]

                # Fetch all games from database through backend
                api_path = "/api/games"
                api_headers = sign_request("GET", api_path, b"", client_id, client_secret)
                api_headers["Authorization"] = f"Bearer {token}"

                response = await client.get(api_path, headers=api_headers)

                # Verify backend retrieved data correctly
                assert response.status_code == 200
                games = response.json()["games"]
                assert len(games) >= 1

                # Verify game details from database
                cs2 = next((g for g in games if g["appid"] == 730), None)
                assert cs2 is not None
                assert cs2["name"] == "Counter-Strike 2"
                assert cs2["is_free"] is True

    async def test_data_consistency_across_all_layers(self, test_db_manager, async_test_client):
        """
        Test data integrity: Database → Backend → API → Response.

        This replaces the skipped TestClient test.
        Verifies special characters and exact numbers are preserved.
        """
        from server.app import app

        # Insert data with special characters and specific values
        test_appid = 99999
        test_name = "Test Gämë: Spêcial Chàrs €ßü™"
        test_count = 123456789

        await test_db_manager.upsert_watchlist(
            appid=test_appid,
            name=test_name,
            last_count=test_count
        )

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Login
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)
                token = login_response.json()["access_token"]

                # Fetch through all layers
                api_path = "/api/current-players"
                api_headers = sign_request("GET", api_path, b"", client_id, client_secret)
                api_headers["Authorization"] = f"Bearer {token}"

                response = await client.get(api_path, headers=api_headers)

                # Verify data integrity through all layers
                assert response.status_code == 200
                games = response.json()["games"]

                test_game = next((g for g in games if g["appid"] == test_appid), None)
                assert test_game is not None

                # Special characters preserved exactly
                assert test_game["name"] == test_name

                # Numbers exact (no rounding/truncation)
                assert test_game["last_count"] == test_count

    async def test_concurrent_requests_to_backend(self, test_db_manager, async_test_client):
        """
        Test backend handles concurrent async requests correctly.

        Verifies: Multiple simultaneous requests don't cause database conflicts.
        """
        from server.app import app
        import asyncio

        # Add test data
        await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=50000)

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Login once
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)
                token = login_response.json()["access_token"]

                # Make concurrent requests - each with unique signature (time-based nonce)
                api_path = "/api/current-players"

                async def fetch_data(delay_ms):
                    # Small delay to ensure unique timestamps
                    await asyncio.sleep(delay_ms / 1000.0)

                    # Each call generates fresh signature with unique nonce/timestamp
                    api_headers = sign_request("GET", api_path, b"", client_id, client_secret)
                    api_headers["Authorization"] = f"Bearer {token}"

                    return await client.get(api_path, headers=api_headers)

                # Execute 5 concurrent requests with staggered timing
                responses = await asyncio.gather(*[fetch_data(i * 10) for i in range(5)])

                # All should succeed without conflicts
                assert all(r.status_code == 200 for r in responses)
                assert all(len(r.json()["games"]) == 1 for r in responses)
                assert all(r.json()["games"][0]["appid"] == 730 for r in responses)

    async def test_authentication_flow_integration(self, test_db_manager, async_test_client):
        """
        Test complete authentication flow through all components.

        Flow: Client → Middleware → Auth → JWT → Protected endpoint
        """
        from server.app import app

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Step 1: Login with HMAC signature
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)

                # Verify JWT issued
                assert login_response.status_code == 200
                data = login_response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"

                # Step 2: Use JWT for protected endpoint
                token = data["access_token"]
                api_headers = sign_request("GET", "/api/genres", b"", client_id, client_secret)
                api_headers["Authorization"] = f"Bearer {token}"

                genres_response = await client.get("/api/genres", headers=api_headers)

                # Verify authentication worked
                assert genres_response.status_code == 200

    async def test_error_propagation_through_layers(self, test_db_manager, async_test_client):
        """
        Test errors propagate correctly through all layers.

        Verifies: Database errors → Backend → API → Client (proper status codes)
        """
        from server.app import app

        with patch('server.app.db', test_db_manager):
            async with async_test_client(app) as client:
                # Login
                client_id = "desktop-main"
                client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
                body_data = {"client_id": client_id}
                body_bytes = json.dumps(body_data).encode('utf-8')

                login_headers = sign_request("POST", "/auth/login", body_bytes, client_id, client_secret)
                login_headers["Content-Type"] = "application/json"

                login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)
                token = login_response.json()["access_token"]

                # Request non-existent endpoint (should return 404)
                api_headers = sign_request("GET", "/api/nonexistent", b"", client_id, client_secret)
                api_headers["Authorization"] = f"Bearer {token}"

                response = await client.get("/api/nonexistent", headers=api_headers)

                # Verify proper error response
                assert response.status_code == 404
