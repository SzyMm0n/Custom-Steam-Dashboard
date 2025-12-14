"""
Unit tests for app/config.py module.

Tests configuration getters with mocked environment variables.
"""
import pytest
from unittest.mock import patch
import os


@pytest.mark.unit
@pytest.mark.app
class TestConfigGetters:
    """Test configuration getter functions."""

    def test_get_server_url_from_env(self):
        """Test get_server_url returns value from environment variable."""
        with patch.dict(os.environ, {'SERVER_URL': 'https://test.example.com'}):
            # Reload module to pick up new env var
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_server_url

            assert get_server_url() == 'https://test.example.com'

    def test_get_server_url_default_value(self):
        """Test get_server_url returns default when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_server_url

            url = get_server_url()
            assert url == "http://localhost:8000"

    def test_get_client_id_from_env(self):
        """Test get_client_id returns value from environment variable."""
        with patch.dict(os.environ, {'CLIENT_ID': 'test-client-123'}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_id

            assert get_client_id() == 'test-client-123'

    def test_get_client_id_default_value(self):
        """Test get_client_id returns default when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_id

            client_id = get_client_id()
            assert client_id == "desktop-main"

    def test_get_client_secret_from_env(self):
        """Test get_client_secret returns value from environment variable."""
        with patch.dict(os.environ, {'CLIENT_SECRET': 'super-secret-key-abc123'}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_secret

            assert get_client_secret() == 'super-secret-key-abc123'

    def test_get_client_secret_empty_default(self):
        """Test get_client_secret returns empty string when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_secret

            secret = get_client_secret()
            assert secret == ""


@pytest.mark.unit
@pytest.mark.app
class TestConfigEdgeCases:
    """Test configuration edge cases."""

    def test_get_server_url_with_trailing_slash(self):
        """Test get_server_url handles URLs with trailing slash."""
        with patch.dict(os.environ, {'SERVER_URL': 'https://api.example.com/'}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_server_url

            # Should return URL as-is (client will strip trailing slash if needed)
            assert get_server_url() == 'https://api.example.com/'

    def test_get_client_id_with_special_characters(self):
        """Test get_client_id handles client IDs with hyphens and underscores."""
        with patch.dict(os.environ, {'CLIENT_ID': 'my-test_client-123'}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_id

            assert get_client_id() == 'my-test_client-123'

    def test_get_client_secret_with_special_characters(self):
        """Test get_client_secret handles secrets with special characters."""
        special_secret = 'Abc123!@#$%^&*()_+-=[]{}|;:,.<>?'

        with patch.dict(os.environ, {'CLIENT_SECRET': special_secret}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_client_secret

            assert get_client_secret() == special_secret

    def test_config_loaded_only_once(self):
        """Test configuration is loaded at module import time."""
        with patch.dict(os.environ, {'SERVER_URL': 'https://initial.com'}):
            import importlib
            import app.config
            importlib.reload(app.config)

            from app.config import get_server_url

            initial_url = get_server_url()

            # Change env var
            os.environ['SERVER_URL'] = 'https://changed.com'

            # Should still return initial value (config loaded at import)
            assert get_server_url() == initial_url


@pytest.mark.unit
@pytest.mark.app
class TestConfigValidation:
    """Test configuration validation warnings."""

    def test_missing_client_secret_shows_warning(self):
        """Test warning is shown when CLIENT_SECRET is not set in development."""
        import warnings
        import sys

        # Ensure not frozen (development mode)
        with patch.object(sys, 'frozen', False, create=True):
            with patch.dict(os.environ, {}, clear=True):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")

                    import importlib
                    import app.config
                    importlib.reload(app.config)

                    # Should have warning about missing CLIENT_SECRET
                    assert len(w) > 0
                    assert any("CLIENT_SECRET not set" in str(warning.message) for warning in w)

    def test_no_warning_when_client_secret_set(self):
        """Test no warning when CLIENT_SECRET is properly set."""
        import warnings

        with patch.dict(os.environ, {'CLIENT_SECRET': 'my-secret-key'}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                import importlib
                import app.config
                importlib.reload(app.config)

                # Should not have warning about CLIENT_SECRET
                client_secret_warnings = [
                    warning for warning in w
                    if "CLIENT_SECRET not set" in str(warning.message)
                ]
                assert len(client_secret_warnings) == 0

