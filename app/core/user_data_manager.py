"""
User preferences and data persistence manager for Custom Steam Dashboard.
Handles saving/loading of custom themes, last library, and user settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class UserDataManager:
    """
    Manages user data persistence including:
    - Custom themes
    - Last loaded library (Steam ID)
    - Application preferences
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(UserDataManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the user data manager."""
        if self._initialized:
            return
        
        self._initialized = True
        self._data_file = self._get_data_file_path()
        self._data = self._load_data()
    
    def _get_data_file_path(self) -> Path:
        """
        Get the path to the user data file.
        Works in both development and executable modes.
        
        Returns:
            Path to user_data.json
        """
        import sys
        
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # Store in user's home directory for persistent storage
            if sys.platform == 'win32':
                data_dir = Path.home() / 'AppData' / 'Local' / 'CustomSteamDashboard'
            elif sys.platform == 'darwin':
                data_dir = Path.home() / 'Library' / 'Application Support' / 'CustomSteamDashboard'
            else:  # Linux and others
                data_dir = Path.home() / '.config' / 'CustomSteamDashboard'
        else:
            # Running as script - store in project directory
            data_dir = Path(__file__).parent.parent.parent
        
        # Ensure directory exists
        data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir / 'user_data.json'
    
    def _load_data(self) -> dict:
        """
        Load user data from file.
        
        Returns:
            Dictionary with user data, or default structure if file doesn't exist
        """
        if not self._data_file.exists():
            logger.info("No user data file found, creating default structure")
            return self._get_default_data()
        
        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded user data from {self._data_file}")
                return data
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            return self._get_default_data()
    
    def _get_default_data(self) -> dict:
        """
        Get default data structure.
        
        Returns:
            Default user data dictionary
        """
        return {
            'version': '1.0',
            'custom_themes': [],
            'last_library': {
                'steam_id': None,
                'persona_name': None,
                'avatar_url': None,
                'last_loaded': None
            },
            'preferences': {
                'last_theme_mode': 'dark',
                'last_theme_palette': 'green',
                'window_size': None,
                'window_position': None
            }
        }
    
    def save(self) -> bool:
        """
        Save user data to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup of existing file
            if self._data_file.exists():
                backup_file = self._data_file.with_suffix('.json.bak')
                self._data_file.rename(backup_file)
            
            # Write new data
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved user data to {self._data_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False
    
    # ===== Custom Themes =====
    
    def save_custom_theme(self, name: str, dark_colors: dict, light_colors: dict, base_color: str) -> bool:
        """
        Save a custom theme.
        
        Args:
            name: Name of the theme
            dark_colors: Colors for dark mode
            light_colors: Colors for light mode
            base_color: Base color used (hex)
            
        Returns:
            True if successful
        """
        theme = {
            'name': name,
            'base_color': base_color,
            'dark_colors': dark_colors,
            'light_colors': light_colors,
            'created_at': datetime.now().isoformat()
        }
        
        # Check if theme with this name already exists
        existing_index = None
        for i, t in enumerate(self._data['custom_themes']):
            if t['name'] == name:
                existing_index = i
                break
        
        if existing_index is not None:
            # Update existing theme
            self._data['custom_themes'][existing_index] = theme
            logger.info(f"Updated custom theme: {name}")
        else:
            # Add new theme
            self._data['custom_themes'].append(theme)
            logger.info(f"Saved new custom theme: {name}")
        
        return self.save()
    
    def get_custom_themes(self) -> List[dict]:
        """
        Get all saved custom themes.
        
        Returns:
            List of theme dictionaries
        """
        return self._data.get('custom_themes', [])
    
    def delete_custom_theme(self, name: str) -> bool:
        """
        Delete a custom theme by name.
        
        Args:
            name: Name of the theme to delete
            
        Returns:
            True if deleted, False if not found
        """
        original_count = len(self._data['custom_themes'])
        self._data['custom_themes'] = [
            t for t in self._data['custom_themes'] if t['name'] != name
        ]
        
        if len(self._data['custom_themes']) < original_count:
            logger.info(f"Deleted custom theme: {name}")
            self.save()
            return True
        
        logger.warning(f"Custom theme not found: {name}")
        return False
    
    def get_custom_theme(self, name: str) -> Optional[dict]:
        """
        Get a specific custom theme by name.
        
        Args:
            name: Name of the theme
            
        Returns:
            Theme dictionary or None if not found
        """
        for theme in self._data['custom_themes']:
            if theme['name'] == name:
                return theme
        return None
    
    # ===== Last Library =====
    
    def save_last_library(self, steam_id: str, persona_name: str = None, avatar_url: str = None):
        """
        Save the last loaded library information.
        
        Args:
            steam_id: Steam ID64
            persona_name: User's persona name (optional)
            avatar_url: User's avatar URL (optional)
        """
        self._data['last_library'] = {
            'steam_id': steam_id,
            'persona_name': persona_name,
            'avatar_url': avatar_url,
            'last_loaded': datetime.now().isoformat()
        }
        self.save()
        logger.info(f"Saved last library: {steam_id}")
    
    def get_last_library(self) -> Optional[dict]:
        """
        Get the last loaded library information.
        
        Returns:
            Dictionary with steam_id, persona_name, avatar_url, last_loaded or None
        """
        last_lib = self._data.get('last_library', {})
        if last_lib.get('steam_id'):
            return last_lib
        return None
    
    def clear_last_library(self):
        """Clear the last library information."""
        self._data['last_library'] = {
            'steam_id': None,
            'persona_name': None,
            'avatar_url': None,
            'last_loaded': None
        }
        self.save()
        logger.info("Cleared last library")
    
    # ===== Preferences =====
    
    def save_theme_preference(self, mode: str, palette: str):
        """
        Save the last used theme preference.
        
        Args:
            mode: Theme mode ("dark" or "light")
            palette: Palette name ("green", "blue", etc.)
        """
        self._data['preferences']['last_theme_mode'] = mode
        self._data['preferences']['last_theme_palette'] = palette
        self.save()
    
    def get_theme_preference(self) -> tuple:
        """
        Get the last used theme preference.
        
        Returns:
            Tuple of (mode, palette)
        """
        prefs = self._data.get('preferences', {})
        mode = prefs.get('last_theme_mode', 'dark')
        palette = prefs.get('last_theme_palette', 'green')
        return (mode, palette)
    
    def save_window_geometry(self, size: tuple = None, position: tuple = None):
        """
        Save window geometry.
        
        Args:
            size: (width, height) tuple
            position: (x, y) tuple
        """
        if size:
            self._data['preferences']['window_size'] = list(size)
        if position:
            self._data['preferences']['window_position'] = list(position)
        self.save()
    
    def get_window_geometry(self) -> dict:
        """
        Get saved window geometry.
        
        Returns:
            Dictionary with 'size' and 'position' keys (or None values)
        """
        prefs = self._data.get('preferences', {})
        return {
            'size': tuple(prefs.get('window_size')) if prefs.get('window_size') else None,
            'position': tuple(prefs.get('window_position')) if prefs.get('window_position') else None
        }

