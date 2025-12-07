"""
Unit tests for server security module.
"""
import pytest
import jwt
import time
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from server.security import (
    create_jwt,
    verify_jwt,
    compute_signature,
    verify_request_signature,
    _check_and_store_nonce,
    _cleanup_expired_nonces,
    JWT_SECRET,
    JWT_ALGORITHM
)


class TestJWTToken:
    """Test cases for JWT token generation and verification."""

    def test_create_jwt_token(self):
        """Test JWT token generation."""
        client_id = "test-client"
        result = create_jwt(client_id)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        
        # Verify token can be decoded
        token = result["access_token"]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == client_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_jwt_token_with_extra_claims(self):
        """Test JWT token generation with extra claims."""
        client_id = "test-client"
        extra_claims = {"custom_field": "custom_value"}
        result = create_jwt(client_id, extra_claims=extra_claims)
        
        token = result["access_token"]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        assert payload["sub"] == client_id
        assert payload["custom_field"] == "custom_value"

    def test_verify_jwt_token_valid(self):
        """Test verification of valid JWT token."""
        client_id = "test-client"
        result = create_jwt(client_id)
        token = result["access_token"]
        
        payload = verify_jwt(token)
        assert payload["sub"] == client_id

    def test_verify_jwt_token_invalid(self):
        """Test verification of invalid JWT token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt("invalid.token.here")
        assert exc_info.value.status_code == 401


class TestSignatureVerification:
    """Test cases for HMAC signature verification."""

    def test_compute_signature(self):
        """Test signature computation."""
        client_secret = "test-secret"
        method = "POST"
        path = "/api/test"
        body_hash = "d41d8cd98f00b204e9800998ecf8427e"
        timestamp = str(int(time.time()))
        nonce = "test-nonce-123"
        
        signature = compute_signature(
            client_secret=client_secret,
            method=method,
            path=path,
            body_hash=body_hash,
            timestamp=timestamp,
            nonce=nonce
        )
        
        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_compute_signature_consistent(self):
        """Test that signature computation is consistent."""
        client_secret = "test-secret"
        method = "POST"
        path = "/api/test"
        body_hash = "abc123"
        timestamp = "1234567890"
        nonce = "test-nonce"
        
        sig1 = compute_signature(client_secret, method, path, body_hash, timestamp, nonce)
        sig2 = compute_signature(client_secret, method, path, body_hash, timestamp, nonce)
        
        assert sig1 == sig2

    def test_verify_request_signature_missing_headers(self):
        """Test signature verification with missing headers."""
        with pytest.raises(HTTPException) as exc_info:
            verify_request_signature(
                method="POST",
                path="/api/test",
                body=b"",
                x_client_id=None,
                x_timestamp=None,
                x_nonce=None,
                x_signature=None
            )
        assert exc_info.value.status_code == 401
        assert "Missing signature headers" in exc_info.value.detail

    def test_verify_request_signature_unknown_client(self):
        """Test signature verification with unknown client."""
        with pytest.raises(HTTPException) as exc_info:
            verify_request_signature(
                method="POST",
                path="/api/test",
                body=b"",
                x_client_id="unknown-client",
                x_timestamp=str(int(time.time())),
                x_nonce="test-nonce",
                x_signature="dummy-signature"
            )
        assert exc_info.value.status_code == 403
        assert "Unknown client_id" in exc_info.value.detail

    def test_verify_request_signature_old_timestamp(self):
        """Test signature verification with old timestamp."""
        with pytest.raises(HTTPException) as exc_info:
            verify_request_signature(
                method="POST",
                path="/api/test",
                body=b"",
                x_client_id="test-client",
                x_timestamp=str(int(time.time()) - 120),  # 2 minutes ago
                x_nonce="test-nonce",
                x_signature="dummy-signature"
            )
        assert exc_info.value.status_code == 401


class TestNonceManagement:
    """Test cases for nonce management."""

    def test_check_and_store_nonce_new(self):
        """Test adding a new nonce."""
        nonce = "unique-nonce-" + str(time.time())
        
        result = _check_and_store_nonce(nonce)
        assert result is True

    def test_check_and_store_nonce_duplicate(self):
        """Test rejecting duplicate nonce."""
        nonce = "duplicate-nonce-" + str(time.time())
        
        # First use should succeed
        result1 = _check_and_store_nonce(nonce)
        assert result1 is True
        
        # Second use should fail
        result2 = _check_and_store_nonce(nonce)
        assert result2 is False

    def test_cleanup_expired_nonces(self):
        """Test cleanup of expired nonces."""
        # This test verifies the cleanup function runs without error
        _cleanup_expired_nonces()
        # No assertion needed - just verify it doesn't crash
