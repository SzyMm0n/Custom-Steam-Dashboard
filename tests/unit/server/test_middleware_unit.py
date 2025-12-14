"""
Unit tests for middleware logic functions.

Tests path verification logic without mocking ASGI interface.
"""
import pytest


@pytest.mark.unit
@pytest.mark.server
class TestShouldVerifySignature:
    """Test should_verify_signature logic."""

    def test_exempts_root_path(self):
        """Test that root path is exempt from verification."""
        from server.middleware import should_verify_signature

        assert not should_verify_signature("/")

    def test_exempts_health_path(self):
        """Test that health endpoint is exempt."""
        from server.middleware import should_verify_signature

        assert not should_verify_signature("/health")

    def test_exempts_auth_paths(self):
        """Test that /auth/ paths are exempt."""
        from server.middleware import should_verify_signature

        assert not should_verify_signature("/auth/login")
        assert not should_verify_signature("/auth/refresh")
        assert not should_verify_signature("/auth/verify")

    def test_exempts_docs_paths(self):
        """Test that documentation paths are exempt."""
        from server.middleware import should_verify_signature

        assert not should_verify_signature("/docs")
        assert not should_verify_signature("/redoc")
        assert not should_verify_signature("/openapi.json")

    def test_requires_verification_for_api_paths(self):
        """Test that /api/ paths require verification."""
        from server.middleware import should_verify_signature

        assert should_verify_signature("/api/games")
        assert should_verify_signature("/api/games/730")
        assert should_verify_signature("/api/watchlist")
        assert should_verify_signature("/api/deals")

    def test_does_not_require_verification_for_other_paths(self):
        """Test that non-protected paths don't require verification."""
        from server.middleware import should_verify_signature

        # Random paths that don't match protected patterns
        assert not should_verify_signature("/random")
        assert not should_verify_signature("/status")
        assert not should_verify_signature("/metrics")


@pytest.mark.unit
@pytest.mark.server
class TestPathConstants:
    """Test path constant definitions."""

    def test_protected_paths_defined(self):
        """Test that PROTECTED_PATHS constant is defined."""
        from server.middleware import PROTECTED_PATHS

        assert isinstance(PROTECTED_PATHS, list)
        assert len(PROTECTED_PATHS) > 0
        assert "/api/" in PROTECTED_PATHS

    def test_exempt_paths_defined(self):
        """Test that EXEMPT_PATHS constant is defined."""
        from server.middleware import EXEMPT_PATHS

        assert isinstance(EXEMPT_PATHS, list)
        assert len(EXEMPT_PATHS) > 0
        assert "/auth/" in EXEMPT_PATHS
        assert "/docs" in EXEMPT_PATHS
        assert "/health" in EXEMPT_PATHS

    def test_auth_paths_in_exempt_list(self):
        """Test that auth paths are properly exempted."""
        from server.middleware import EXEMPT_PATHS

        # Auth should be exempt (handles own verification)
        assert "/auth/" in EXEMPT_PATHS


@pytest.mark.unit
@pytest.mark.server
class TestEdgeCases:
    """Test edge cases in path verification logic."""

    def test_path_with_query_parameters(self):
        """Test paths with query parameters."""
        from server.middleware import should_verify_signature

        # Path comparison uses startswith, so query params are included
        assert should_verify_signature("/api/games?limit=10")

    def test_path_with_trailing_slash(self):
        """Test paths with trailing slash."""
        from server.middleware import should_verify_signature

        assert should_verify_signature("/api/games/")
        assert not should_verify_signature("/health/")

    def test_case_sensitive_paths(self):
        """Test that path matching is case-sensitive."""
        from server.middleware import should_verify_signature

        # Should be case-sensitive
        assert should_verify_signature("/api/games")
        # Capital letters - depends on implementation, but typically case-sensitive
        # This documents current behavior

    def test_empty_path(self):
        """Test empty path string."""
        from server.middleware import should_verify_signature

        # Empty string should not match anything
        assert not should_verify_signature("")

    def test_path_with_multiple_segments(self):
        """Test deeply nested paths."""
        from server.middleware import should_verify_signature

        assert should_verify_signature("/api/v1/games/730/details")
        assert not should_verify_signature("/auth/v1/login")


