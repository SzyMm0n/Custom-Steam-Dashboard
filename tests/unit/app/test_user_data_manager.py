"""
Unit tests for UserDataManager.

Tests user data persistence with prepared data (no real file I/O).
"""
import pytest
from unittest.mock import patch, mock_open, Mock
import json
from pathlib import Path


@pytest.mark.unit
@pytest.mark.app
class TestUserDataManagerInitialization:
    """Test UserDataManager initialization and singleton pattern."""

    def test_user_data_manager_is_singleton(self):
        """Test UserDataManager implements singleton pattern."""
        from app.core.user_data_manager import UserDataManager

        instance1 = UserDataManager()
        instance2 = UserDataManager()

        assert instance1 is instance2

    def test_initialization_loads_data_from_file(self, prepared_json_data, tmp_path):
        """Test initialization loads existing data file."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"
        test_data = prepared_json_data['user_data']

        # Write test data to file
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        # Reset singleton
        UserDataManager._instance = None

        # Mock path to use tmp_path
        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Verify data was loaded
            assert manager._data['version'] == '1.0'
            assert 'custom_themes' in manager._data

    def test_initialization_creates_default_data_if_file_missing(self, tmp_path):
        """Test initialization creates default data when file doesn't exist."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "nonexistent.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Verify default data structure
            assert manager._data['version'] == '1.0'
            assert manager._data['custom_themes'] == []
            assert manager._data['last_library']['steam_id'] is None
            assert manager._data['preferences']['last_theme_mode'] == 'dark'


@pytest.mark.unit
@pytest.mark.app
class TestUserDataManagerSaveLoad:
    """Test save and load operations with prepared data."""

    def test_save_writes_data_to_file(self, prepared_json_data, tmp_path):
        """Test save() writes data to file."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()
            manager._data = prepared_json_data['user_data']

            # Save data
            result = manager.save()

            assert result is True
            assert test_file.exists()

            # Verify content
            with open(test_file) as f:
                saved_data = json.load(f)

            assert saved_data['version'] == '1.0'

    def test_save_creates_backup_of_existing_file(self, prepared_json_data, tmp_path):
        """Test save() creates backup before overwriting."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"
        backup_file = test_file.with_suffix('.json.bak')

        # Create existing file
        with open(test_file, 'w') as f:
            json.dump({'old': 'data'}, f)

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()
            manager._data = prepared_json_data['user_data']

            # Save data
            manager.save()

            # Verify backup was created
            assert backup_file.exists()

    def test_load_handles_corrupted_json(self, prepared_json_data, tmp_path):
        """Test loading corrupted JSON returns default data."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Write corrupted JSON
        with open(test_file, 'w') as f:
            f.write(prepared_json_data['corrupted_json'])

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Should have default data (not corrupted)
            assert manager._data['version'] == '1.0'
            assert isinstance(manager._data['custom_themes'], list)


@pytest.mark.unit
@pytest.mark.app
class TestUserDataManagerCustomThemes:
    """Test custom theme management."""

    def test_save_custom_theme_adds_new_theme(self, tmp_path):
        """Test save_custom_theme() adds new theme to list."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Save custom theme
            result = manager.save_custom_theme(
                name="My Theme",
                dark_colors={'primary': '#1e88e5'},
                light_colors={'primary': '#1976d2'},
                base_color="#1e88e5"
            )

            assert result is True
            themes = manager.get_custom_themes()
            assert len(themes) == 1
            assert themes[0]['name'] == "My Theme"

    def test_save_custom_theme_updates_existing(self, tmp_path):
        """Test save_custom_theme() updates existing theme with same name."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Save initial theme
            manager.save_custom_theme(
                name="My Theme",
                dark_colors={'primary': '#1e88e5'},
                light_colors={'primary': '#1976d2'},
                base_color="#1e88e5"
            )

            # Update with new colors
            manager.save_custom_theme(
                name="My Theme",  # Same name
                dark_colors={'primary': '#ff0000'},  # Different colors
                light_colors={'primary': '#ee0000'},
                base_color="#ff0000"
            )

            themes = manager.get_custom_themes()
            assert len(themes) == 1  # Should only have one theme
            assert themes[0]['dark_colors']['primary'] == '#ff0000'  # Updated

    def test_delete_custom_theme_removes_theme(self, tmp_path):
        """Test delete_custom_theme() removes theme from list."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Add theme
            manager.save_custom_theme(
                name="My Theme",
                dark_colors={'primary': '#1e88e5'},
                light_colors={'primary': '#1976d2'},
                base_color="#1e88e5"
            )

            # Delete theme
            result = manager.delete_custom_theme("My Theme")

            assert result is True
            themes = manager.get_custom_themes()
            assert len(themes) == 0

    def test_delete_nonexistent_theme_returns_false(self, tmp_path):
        """Test deleting non-existent theme returns False."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Try to delete non-existent theme
            result = manager.delete_custom_theme("Nonexistent")

            assert result is False


@pytest.mark.unit
@pytest.mark.app
class TestUserDataManagerEdgeCases:
    """Test edge cases in UserDataManager."""

    def test_get_data_file_path_creates_directory(self, tmp_path):
        """Test _get_data_file_path() creates parent directory."""
        from app.core.user_data_manager import UserDataManager

        # Reset singleton
        UserDataManager._instance = None

        # Create manager (should create directory)
        with patch('pathlib.Path.home', return_value=tmp_path):
            manager = UserDataManager()

            # Verify data file path includes created directory
            assert manager._data_file.parent.exists()

    def test_save_handles_write_permission_error(self, tmp_path):
        """Test save() returns False on write permission error."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "readonly.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("No write permission")):
                result = manager.save()

                assert result is False

    def test_custom_theme_with_special_characters_in_name(self, tmp_path):
        """Test custom theme name with special characters."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            special_name = "My Theme™ & 'Edition' (2024)"

            manager.save_custom_theme(
                name=special_name,
                dark_colors={'primary': '#1e88e5'},
                light_colors={'primary': '#1976d2'},
                base_color="#1e88e5"
            )

            themes = manager.get_custom_themes()
            assert themes[0]['name'] == special_name

    def test_empty_custom_themes_list(self, tmp_path):
        """Test get_custom_themes() with no themes saved."""
        from app.core.user_data_manager import UserDataManager

        test_file = tmp_path / "user_data.json"

        # Reset singleton
        UserDataManager._instance = None

        with patch.object(UserDataManager, '_get_data_file_path', return_value=test_file):
            manager = UserDataManager()

            themes = manager.get_custom_themes()

            assert themes == []
            assert isinstance(themes, list)

