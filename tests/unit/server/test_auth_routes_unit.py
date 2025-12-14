"""
Unit tests for authentication routes.

Tests login endpoint logic, validation, and error handling with mocked dependencies.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import HTTPException
import json
import time


@pytest.mark.unit
@pytest.mark.server
class TestAuthLoginHappyPath:
    """Test successful login scenarios."""

    @pytest.mark.asyncio
    async def test_login_with_valid_signature_returns_jwt(self):
        """Test login with valid HMAC signature returns JWT token."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        # Mock request with valid signature headers
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "test_nonce_123456",
            "X-Signature": "valid_signature_base64"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        # Mock verify_request_signature to return client_id
        with patch('server.auth_routes.verify_request_signature', return_value="test-client"):
            # Patch CLIENTS_MAP in auth_routes module
            with patch.dict('server.auth_routes.CLIENTS_MAP', {"test-client": "test-secret"}, clear=True):
                # Mock create_jwt to return token data
                with patch('server.auth_routes.create_jwt', return_value={
                    "access_token": "test_jwt_token_123",
                    "token_type": "bearer",
                    "expires_in": 1200
                }):
                    # Call login
                    login_data = LoginRequest(client_id="test-client")
                    response = await login(login_data, mock_request)

                    # Verify response
                    assert response.access_token == "test_jwt_token_123"
                    assert response.token_type == "bearer"
                    assert response.expires_in == 1200

    @pytest.mark.asyncio
    async def test_login_verifies_signature_with_correct_params(self):
        """Test login calls verify_request_signature with correct parameters."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"

        test_timestamp = str(int(time.time()))
        test_nonce = "test_nonce_abc"
        test_signature = "test_sig"

        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": test_timestamp,
            "X-Nonce": test_nonce,
            "X-Signature": test_signature
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        with patch('server.auth_routes.verify_request_signature', return_value="test-client") as mock_verify:
            # Patch CLIENTS_MAP in auth_routes
            with patch.dict('server.auth_routes.CLIENTS_MAP', {"test-client": "secret"}, clear=True):
                with patch('server.auth_routes.create_jwt', return_value={
                    "access_token": "token",
                    "token_type": "bearer",
                    "expires_in": 1200
                }):
                    login_data = LoginRequest(client_id="test-client")
                    await login(login_data, mock_request)

                    # Verify verify_request_signature was called with correct params
                    mock_verify.assert_called_once_with(
                        method="POST",
                        path="/auth/login",
                        body=b'{"client_id":"test-client"}',
                        x_client_id="test-client",
                        x_timestamp=test_timestamp,
                        x_nonce=test_nonce,
                        x_signature=test_signature
                    )


@pytest.mark.unit
@pytest.mark.server
class TestAuthLoginBadPath:
    """Test login error scenarios."""

    @pytest.mark.asyncio
    async def test_login_with_invalid_signature_raises_403(self):
        """Test login with invalid signature raises HTTPException 403."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "nonce",
            "X-Signature": "invalid_signature"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        # Mock verify_request_signature to raise HTTPException
        with patch('server.auth_routes.verify_request_signature',
                   side_effect=HTTPException(status_code=403, detail="Invalid signature")):

            login_data = LoginRequest(client_id="test-client")

            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_request)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_login_with_expired_timestamp_raises_401(self):
        """Test login with expired timestamp raises HTTPException 401."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"

        # Timestamp from 2 minutes ago (expired)
        old_timestamp = str(int(time.time()) - 120)

        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": old_timestamp,
            "X-Nonce": "nonce",
            "X-Signature": "signature"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        with patch('server.auth_routes.verify_request_signature',
                   side_effect=HTTPException(status_code=401, detail="Timestamp expired")):

            login_data = LoginRequest(client_id="test-client")

            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_unknown_client_raises_403(self):
        """Test login with unknown client_id raises HTTPException 403."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "unknown-client",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "nonce",
            "X-Signature": "signature"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"unknown-client"}')

        # Mock verify_request_signature returns unknown client
        with patch('server.auth_routes.verify_request_signature', return_value="unknown-client"):
            # Mock CLIENTS_MAP in security module (where it's actually defined)
            with patch('server.security.CLIENTS_MAP', {"test-client": "secret"}):

                login_data = LoginRequest(client_id="unknown-client")

                with pytest.raises(HTTPException) as exc_info:
                    await login(login_data, mock_request)

                assert exc_info.value.status_code == 403
                assert "Invalid client credentials" in str(exc_info.value.detail)


@pytest.mark.unit
@pytest.mark.server
class TestAuthLoginEdgeCases:
    """Test edge cases in login endpoint."""

    @pytest.mark.asyncio
    async def test_login_with_client_id_mismatch_raises_400(self):
        """Test login with mismatched client_id between body and header raises 400."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "client-in-header",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "nonce",
            "X-Signature": "signature"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"client-in-body"}')

        # verify_request_signature returns client from header
        with patch('server.auth_routes.verify_request_signature', return_value="client-in-header"):

            # But login_data has different client_id
            login_data = LoginRequest(client_id="client-in-body")

            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_request)

            assert exc_info.value.status_code == 400
            assert "Client ID in body must match" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_with_missing_headers_raises_error(self):
        """Test login with missing signature headers raises error."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"

        # Missing X-Signature header
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "nonce"
            # X-Signature is None
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        with patch('server.auth_routes.verify_request_signature',
                   side_effect=HTTPException(status_code=400, detail="Missing X-Signature header")):

            login_data = LoginRequest(client_id="test-client")

            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_request)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_login_with_verification_exception_raises_500(self):
        """Test login handles unexpected exceptions during verification."""
        from server.auth_routes import login, LoginRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/auth/login"
        mock_request.headers.get = Mock(side_effect=lambda key: {
            "X-Client-Id": "test-client",
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "nonce",
            "X-Signature": "signature"
        }.get(key))
        mock_request.body = AsyncMock(return_value=b'{"client_id":"test-client"}')

        # Mock unexpected exception during verification
        with patch('server.auth_routes.verify_request_signature',
                   side_effect=Exception("Unexpected error")):

            login_data = LoginRequest(client_id="test-client")

            with pytest.raises(HTTPException) as exc_info:
                await login(login_data, mock_request)

            assert exc_info.value.status_code == 500


@pytest.mark.unit
@pytest.mark.server
class TestAuthVerifyToken:
    """Test verify token endpoint."""

    @pytest.mark.asyncio
    async def test_verify_token_with_valid_jwt_returns_info(self):
        """Test verify endpoint with valid JWT returns token info."""
        from server.auth_routes import verify_token

        # Mock JWT payload from require_auth dependency
        mock_payload = {
            "client_id": "test-client",
            "exp": int(time.time()) + 1200
        }

        result = await verify_token(payload=mock_payload)

        assert result["valid"] == True
        assert result["client_id"] == "test-client"
        assert result["expires_at"] == mock_payload["exp"]

    @pytest.mark.asyncio
    async def test_verify_token_returns_expiry_time(self):
        """Test verify endpoint includes expiry time in response."""
        from server.auth_routes import verify_token

        expiry = int(time.time()) + 600
        mock_payload = {
            "client_id": "test-client",
            "exp": expiry
        }

        result = await verify_token(payload=mock_payload)

        assert "expires_at" in result
        assert result["expires_at"] == expiry

