"""
Unit tests for signing utilities.

Tests HMAC signature generation and request signing with mocked data.
"""
import pytest
from unittest.mock import patch
import time
import hmac
import hashlib
import base64


@pytest.mark.unit
@pytest.mark.app
class TestSignatureComputation:
    """Test compute_signature function."""

    def test_compute_signature_produces_consistent_result(self):
        """Test compute_signature produces same result for same inputs."""
        from app.helpers.signing import compute_signature

        # Compute signature twice with same inputs
        sig1 = compute_signature(
            client_secret="test-secret",
            method="GET",
            path="/api/games",
            body=b"",
            timestamp="1234567890",
            nonce="test-nonce"
        )

        sig2 = compute_signature(
            client_secret="test-secret",
            method="GET",
            path="/api/games",
            body=b"",
            timestamp="1234567890",
            nonce="test-nonce"
        )

        assert sig1 == sig2

    def test_compute_signature_different_for_different_inputs(self):
        """Test compute_signature produces different signatures for different inputs."""
        from app.helpers.signing import compute_signature

        base_params = {
            "client_secret": "test-secret",
            "method": "GET",
            "path": "/api/games",
            "body": b"",
            "timestamp": "1234567890",
            "nonce": "test-nonce"
        }

        sig_base = compute_signature(**base_params)

        # Different method
        sig_method = compute_signature(**{**base_params, "method": "POST"})
        assert sig_base != sig_method

        # Different path
        sig_path = compute_signature(**{**base_params, "path": "/api/other"})
        assert sig_base != sig_path

        # Different body
        sig_body = compute_signature(**{**base_params, "body": b"test"})
        assert sig_base != sig_body

        # Different timestamp
        sig_time = compute_signature(**{**base_params, "timestamp": "9999999999"})
        assert sig_base != sig_time

        # Different nonce
        sig_nonce = compute_signature(**{**base_params, "nonce": "other-nonce"})
        assert sig_base != sig_nonce

    def test_compute_signature_returns_base64_encoded_string(self):
        """Test compute_signature returns valid base64 string."""
        from app.helpers.signing import compute_signature

        signature = compute_signature(
            client_secret="secret",
            method="GET",
            path="/test",
            body=b"",
            timestamp="123",
            nonce="nonce"
        )

        # Should be able to decode as base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) == 32  # SHA256 produces 32 bytes
        except Exception:
            pytest.fail("Signature is not valid base64")

    def test_compute_signature_with_empty_body(self):
        """Test compute_signature handles empty body correctly."""
        from app.helpers.signing import compute_signature

        sig_empty = compute_signature(
            client_secret="secret",
            method="GET",
            path="/test",
            body=b"",
            timestamp="123",
            nonce="nonce"
        )

        # Verify it produces valid signature
        assert isinstance(sig_empty, str)
        assert len(sig_empty) > 0

    def test_compute_signature_with_json_body(self):
        """Test compute_signature with JSON body."""
        from app.helpers.signing import compute_signature

        json_body = b'{"key": "value", "number": 123}'

        signature = compute_signature(
            client_secret="secret",
            method="POST",
            path="/api/data",
            body=json_body,
            timestamp="123",
            nonce="nonce"
        )

        assert isinstance(signature, str)
        assert len(signature) > 0


@pytest.mark.unit
@pytest.mark.app
class TestGenerateNonce:
    """Test nonce generation."""

    def test_generate_nonce_produces_hex_string(self):
        """Test generate_nonce produces hex string."""
        from app.helpers.signing import generate_nonce

        nonce = generate_nonce()

        # Should be hex string
        try:
            int(nonce, 16)
        except ValueError:
            pytest.fail("Nonce is not valid hex string")

    def test_generate_nonce_default_length(self):
        """Test generate_nonce default length is 64 hex chars (32 bytes)."""
        from app.helpers.signing import generate_nonce

        nonce = generate_nonce()

        # 32 bytes = 64 hex characters
        assert len(nonce) == 64

    def test_generate_nonce_custom_length(self):
        """Test generate_nonce with custom length."""
        from app.helpers.signing import generate_nonce

        nonce = generate_nonce(length=16)

        # 16 bytes = 32 hex characters
        assert len(nonce) == 32

    def test_generate_nonce_produces_unique_values(self):
        """Test generate_nonce produces different values each time."""
        from app.helpers.signing import generate_nonce

        nonces = [generate_nonce() for _ in range(100)]

        # All should be unique
        assert len(set(nonces)) == 100


@pytest.mark.unit
@pytest.mark.app
class TestSignRequest:
    """Test sign_request function."""

    def test_sign_request_returns_required_headers(self):
        """Test sign_request returns all required signature headers."""
        from app.helpers.signing import sign_request

        with patch('app.helpers.signing.get_client_credentials', return_value=("client-id", "secret")):
            headers = sign_request(
                method="GET",
                path="/api/games",
                body=b""
            )

        # Verify all required headers are present
        assert "X-Client-Id" in headers
        assert "X-Timestamp" in headers
        assert "X-Nonce" in headers
        assert "X-Signature" in headers

    def test_sign_request_uses_provided_credentials(self):
        """Test sign_request uses provided client_id and secret."""
        from app.helpers.signing import sign_request

        headers = sign_request(
            method="GET",
            path="/test",
            body=b"",
            client_id="my-client",
            client_secret="my-secret"
        )

        assert headers["X-Client-Id"] == "my-client"

    def test_sign_request_uses_env_credentials_when_not_provided(self):
        """Test sign_request gets credentials from env when not provided."""
        from app.helpers.signing import sign_request

        with patch('app.helpers.signing.get_client_credentials', return_value=("env-client", "env-secret")):
            headers = sign_request(
                method="GET",
                path="/test",
                body=b""
            )

        assert headers["X-Client-Id"] == "env-client"

    def test_sign_request_timestamp_is_current(self):
        """Test sign_request generates current timestamp."""
        from app.helpers.signing import sign_request

        current_time = int(time.time())

        with patch('app.helpers.signing.get_client_credentials', return_value=("client", "secret")):
            headers = sign_request(
                method="GET",
                path="/test",
                body=b""
            )

        timestamp = int(headers["X-Timestamp"])

        # Should be within 2 seconds of current time
        assert abs(timestamp - current_time) <= 2

    def test_sign_request_with_none_body_treats_as_empty(self):
        """Test sign_request handles None body as empty bytes."""
        from app.helpers.signing import sign_request

        with patch('app.helpers.signing.get_client_credentials', return_value=("client", "secret")):
            headers = sign_request(
                method="GET",
                path="/test",
                body=None  # None body
            )

        # Should succeed and produce signature
        assert "X-Signature" in headers
        assert len(headers["X-Signature"]) > 0


@pytest.mark.unit
@pytest.mark.app
class TestGetClientCredentials:
    """Test get_client_credentials function."""

    def test_get_client_credentials_returns_tuple(self):
        """Test get_client_credentials returns (client_id, client_secret) tuple."""
        from app.helpers.signing import get_client_credentials

        with patch('app.helpers.signing.get_client_id', return_value="test-id"):
            with patch('app.helpers.signing.get_client_secret', return_value="test-secret"):
                client_id, client_secret = get_client_credentials()

        assert client_id == "test-id"
        assert client_secret == "test-secret"

    def test_get_client_credentials_calls_config_functions(self):
        """Test get_client_credentials calls config getter functions."""
        from app.helpers.signing import get_client_credentials

        with patch('app.helpers.signing.get_client_id', return_value="id") as mock_id:
            with patch('app.helpers.signing.get_client_secret', return_value="secret") as mock_secret:
                get_client_credentials()

        mock_id.assert_called_once()
        mock_secret.assert_called_once()


@pytest.mark.unit
@pytest.mark.app
class TestSigningEdgeCases:
    """Test edge cases in signing utilities."""

    def test_compute_signature_with_empty_secret(self):
        """Test compute_signature with empty secret string."""
        from app.helpers.signing import compute_signature

        # Should not raise error
        signature = compute_signature(
            client_secret="",
            method="GET",
            path="/test",
            body=b"",
            timestamp="123",
            nonce="nonce"
        )

        assert isinstance(signature, str)

    def test_compute_signature_with_special_characters_in_path(self):
        """Test compute_signature handles special characters in path."""
        from app.helpers.signing import compute_signature

        special_path = "/api/games?filter=FPS&limit=10"

        signature = compute_signature(
            client_secret="secret",
            method="GET",
            path=special_path,
            body=b"",
            timestamp="123",
            nonce="nonce"
        )

        assert isinstance(signature, str)

    def test_sign_request_with_very_large_body(self):
        """Test sign_request handles large request body."""
        from app.helpers.signing import sign_request

        large_body = b"x" * 1000000  # 1MB body

        with patch('app.helpers.signing.get_client_credentials', return_value=("client", "secret")):
            headers = sign_request(
                method="POST",
                path="/test",
                body=large_body
            )

        # Should handle large body without error
        assert "X-Signature" in headers

    def test_sign_request_generates_unique_nonce_each_time(self):
        """Test sign_request generates different nonce for each call."""
        from app.helpers.signing import sign_request

        with patch('app.helpers.signing.get_client_credentials', return_value=("client", "secret")):
            headers1 = sign_request(method="GET", path="/test", body=b"")
            headers2 = sign_request(method="GET", path="/test", body=b"")

        # Nonces should be different
        assert headers1["X-Nonce"] != headers2["X-Nonce"]

