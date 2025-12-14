"""
Unit tests for ThemeManager.

Tests theme mode/palette management and signal emission.
"""
import pytest
from unittest.mock import patch, Mock
from PySide6.QtCore import Qt


@pytest.mark.unit
@pytest.mark.app
class TestThemeManagerSingleton:
    """Test ThemeManager singleton pattern."""

    def test_theme_manager_is_singleton(self):
        """Test ThemeManager implements singleton pattern."""
        from app.ui.theme_manager import ThemeManager

        # Reset singleton for test
        ThemeManager._instance = None

        instance1 = ThemeManager()
        instance2 = ThemeManager()

        assert instance1 is instance2

    def test_singleton_initializes_only_once(self):
        """Test singleton initialization happens only once."""
        from app.ui.theme_manager import ThemeManager

        # Reset singleton
        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")

            instance1 = ThemeManager()
            instance2 = ThemeManager()

            # Should only call UserDataManager once
            assert mock_udm.call_count == 1


@pytest.mark.unit
@pytest.mark.app
class TestThemeMode:
    """Test theme mode getter and setter."""

    def test_get_mode_returns_current_mode(self):
        """Test mode property returns current theme mode."""
        from app.ui.theme_manager import ThemeManager, ThemeMode

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")

            manager = ThemeManager()

            assert manager.mode == ThemeMode.DARK

    def test_set_mode_changes_mode(self, qtbot):
        """Test set_mode changes the theme mode."""
        from app.ui.theme_manager import ThemeManager, ThemeMode

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")
            mock_udm.return_value.save_theme_preference = Mock()

            manager = ThemeManager()

            manager.set_mode(ThemeMode.LIGHT)

            assert manager.mode == ThemeMode.LIGHT

    def test_set_mode_emits_signal(self, qtbot):
        """Test set_mode emits theme_changed signal."""
        from app.ui.theme_manager import ThemeManager, ThemeMode

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")
            mock_udm.return_value.save_theme_preference = Mock()

            manager = ThemeManager()

            with qtbot.waitSignal(manager.theme_changed, timeout=1000) as blocker:
                manager.set_mode(ThemeMode.LIGHT)

            # Signal should have been emitted
            assert blocker.signal_triggered

    def test_set_mode_same_mode_does_not_emit(self, qtbot):
        """Test setting same mode doesn't emit signal."""
        from app.ui.theme_manager import ThemeManager, ThemeMode

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")
            mock_udm.return_value.save_theme_preference = Mock()

            manager = ThemeManager()

            # Set to same mode (DARK)
            manager.set_mode(ThemeMode.DARK)

            # Signal should not be emitted (no change)
            # Can't easily test negative with qtbot, but we can check mode didn't call save
            assert mock_udm.return_value.save_theme_preference.call_count == 0


@pytest.mark.unit
@pytest.mark.app
class TestColorPalette:
    """Test color palette management."""

    def test_get_palette_returns_current_palette(self):
        """Test palette property returns current color palette."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "blue")

            manager = ThemeManager()

            assert manager.palette == ColorPalette.BLUE

    def test_set_palette_changes_palette(self, qtbot):
        """Test set_palette changes the color palette."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")
            mock_udm.return_value.save_theme_preference = Mock()

            manager = ThemeManager()

            manager.set_palette(ColorPalette.PURPLE)

            assert manager.palette == ColorPalette.PURPLE

    def test_set_palette_emits_signal(self, qtbot):
        """Test set_palette emits theme_changed signal."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "green")
            mock_udm.return_value.save_theme_preference = Mock()

            manager = ThemeManager()

            with qtbot.waitSignal(manager.theme_changed, timeout=1000) as blocker:
                manager.set_palette(ColorPalette.ORANGE)

            assert blocker.signal_triggered


@pytest.mark.unit
@pytest.mark.app
class TestCustomTheme:
    """Test custom theme loading."""

    def test_load_custom_theme_from_preferences(self):
        """Test loading custom theme from saved preferences."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        custom_theme = {
            'name': 'My Theme',
            'dark_colors': {'primary': '#ff0000'},
            'light_colors': {'primary': '#ee0000'}
        }

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "custom:My Theme")
            mock_udm.return_value.get_custom_theme.return_value = custom_theme

            manager = ThemeManager()

            assert manager.palette == ColorPalette.CUSTOM
            assert manager._custom_dark_colors == custom_theme['dark_colors']

    def test_fallback_to_green_if_custom_theme_not_found(self):
        """Test fallback to green palette if custom theme not found."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "custom:Missing")
            mock_udm.return_value.get_custom_theme.return_value = None  # Theme not found

            manager = ThemeManager()

            # Should fallback to GREEN
            assert manager.palette == ColorPalette.GREEN


@pytest.mark.unit
@pytest.mark.app
class TestEdgeCases:
    """Test edge cases in ThemeManager."""

    def test_invalid_mode_in_preferences(self):
        """Test handles invalid mode value in preferences."""
        from app.ui.theme_manager import ThemeManager, ThemeMode

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("invalid_mode", "green")

            manager = ThemeManager()

            # Should fallback to DARK
            assert manager.mode == ThemeMode.DARK

    def test_invalid_palette_in_preferences(self):
        """Test handles invalid palette value in preferences."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", "invalid_palette")

            manager = ThemeManager()

            # Should fallback to GREEN
            assert manager.palette == ColorPalette.GREEN

    def test_none_palette_in_preferences(self):
        """Test handles None palette value."""
        from app.ui.theme_manager import ThemeManager, ColorPalette

        ThemeManager._instance = None

        with patch('app.core.user_data_manager.UserDataManager') as mock_udm:
            mock_udm.return_value.get_theme_preference.return_value = ("dark", None)

            manager = ThemeManager()

            assert manager.palette == ColorPalette.GREEN

