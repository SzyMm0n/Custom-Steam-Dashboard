"""
Theme Manager for Custom Steam Dashboard.
Provides dark and light themes with multiple color palettes.
"""

from enum import Enum
from typing import Dict
from PySide6.QtCore import QObject, Signal


class ThemeMode(Enum):
    """Theme mode enumeration."""
    DARK = "dark"
    LIGHT = "light"


class ColorPalette(Enum):
    """Color palette enumeration."""
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    ORANGE = "orange"
    CUSTOM = "custom"


class ThemeManager(QObject):
    """
    Singleton theme manager for the application.
    Manages theme switching and color palettes.
    """
    
    theme_changed = Signal(str, str)  # mode, palette
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()

        # Load saved preferences
        from app.core.user_data_manager import UserDataManager
        data_manager = UserDataManager()
        saved_mode, saved_palette = data_manager.get_theme_preference()

        # Set initial mode from saved preferences
        try:
            self._mode = ThemeMode(saved_mode)
        except ValueError:
            self._mode = ThemeMode.DARK

        self._custom_dark_colors = None
        self._custom_light_colors = None

        # Check if saved palette is a custom theme
        if saved_palette and saved_palette.startswith("custom:"):
            theme_name = saved_palette[7:]  # Remove "custom:" prefix
            theme = data_manager.get_custom_theme(theme_name)
            if theme:
                self._custom_dark_colors = theme['dark_colors']
                self._custom_light_colors = theme['light_colors']
                self._palette = ColorPalette.CUSTOM
            else:
                # Theme not found, fallback to green
                self._palette = ColorPalette.GREEN
        else:
            # Standard palette
            try:
                self._palette = ColorPalette(saved_palette) if saved_palette else ColorPalette.GREEN
            except ValueError:
                self._palette = ColorPalette.GREEN

        self._initialized = True
    
    @property
    def mode(self) -> ThemeMode:
        """Get current theme mode."""
        return self._mode
    
    @property
    def palette(self) -> ColorPalette:
        """Get current color palette."""
        return self._palette
    
    def set_mode(self, mode: ThemeMode):
        """Set theme mode (dark/light)."""
        if self._mode != mode:
            self._mode = mode
            self._save_preference()
            self.theme_changed.emit(self._mode.value, self._palette.value)
    
    def set_palette(self, palette: ColorPalette):
        """Set color palette."""
        if self._palette != palette:
            self._palette = palette
            self._save_preference()
            self.theme_changed.emit(self._mode.value, self._palette.value)
    
    def _save_preference(self):
        """Save current theme preference to persistent storage."""
        from app.core.user_data_manager import UserDataManager
        data_manager = UserDataManager()
        # Don't save palette.value for CUSTOM, as it should be saved via _save_custom_theme_name
        if self._palette != ColorPalette.CUSTOM:
            data_manager.save_theme_preference(self._mode.value, self._palette.value)

    def toggle_mode(self):
        """Toggle between dark and light mode."""
        new_mode = ThemeMode.LIGHT if self._mode == ThemeMode.DARK else ThemeMode.DARK
        self.set_mode(new_mode)
    
    def set_custom_colors(self, dark_colors: dict, light_colors: dict):
        """
        Set custom color palettes for dark and light modes.

        Args:
            dark_colors: Dictionary of colors for dark mode
            light_colors: Dictionary of colors for light mode
        """
        self._custom_dark_colors = dark_colors
        self._custom_light_colors = light_colors

        # Always emit theme_changed signal, even if already on CUSTOM palette
        # This ensures UI updates when switching between different custom themes
        was_already_custom = (self._palette == ColorPalette.CUSTOM)
        self._palette = ColorPalette.CUSTOM

        if not was_already_custom:
            self._save_preference()

        # Always emit signal to update UI with new colors
        self.theme_changed.emit(self._mode.value, self._palette.value)

    def _save_custom_theme_name(self, theme_name: str):
        """Save the active custom theme name for restoration on restart."""
        from app.core.user_data_manager import UserDataManager
        data_manager = UserDataManager()
        # Save as special palette value
        data_manager.save_theme_preference(self._mode.value, f"custom:{theme_name}")

    def get_colors(self) -> Dict[str, str]:
        """Get current theme colors based on mode and palette."""
        # Use custom colors if CUSTOM palette is selected
        if self._palette == ColorPalette.CUSTOM:
            if self._mode == ThemeMode.DARK and self._custom_dark_colors:
                # Validate that custom colors have all required keys
                required_keys = {'background', 'background_light', 'background_panel', 'background_group',
                                'foreground', 'foreground_dim', 'border', 'border_group',
                                'accent', 'accent_hover', 'accent_pressed', 'accent_light',
                                'danger', 'danger_hover', 'danger_pressed',
                                'chart_bg', 'chart_plot', 'chart_grid', 'chart_text'}
                if all(key in self._custom_dark_colors for key in required_keys):
                    return self._custom_dark_colors
                else:
                    print(f"⚠ Custom dark colors incomplete, using fallback")
                    return DARK_COLORS[ColorPalette.GREEN]
            elif self._mode == ThemeMode.LIGHT and self._custom_light_colors:
                # Validate that custom colors have all required keys
                required_keys = {'background', 'background_light', 'background_panel', 'background_group',
                                'foreground', 'foreground_dim', 'border', 'border_group',
                                'accent', 'accent_hover', 'accent_pressed', 'accent_light',
                                'danger', 'danger_hover', 'danger_pressed',
                                'chart_bg', 'chart_plot', 'chart_grid', 'chart_text'}
                if all(key in self._custom_light_colors for key in required_keys):
                    return self._custom_light_colors
                else:
                    print(f"⚠ Custom light colors incomplete, using fallback")
                    return LIGHT_COLORS[ColorPalette.GREEN]
            # Fallback to GREEN if custom colors not set
            return DARK_COLORS[ColorPalette.GREEN] if self._mode == ThemeMode.DARK else LIGHT_COLORS[ColorPalette.GREEN]

        # Use predefined palettes
        if self._mode == ThemeMode.DARK:
            return DARK_COLORS[self._palette]
        else:
            return LIGHT_COLORS[self._palette]


# Dark Theme Color Palettes
DARK_COLORS = {
    ColorPalette.GREEN: {
        'background': '#0b0b0b',
        'background_light': '#1b1b1b',
        'background_panel': '#111111',
        'background_group': '#15331f',
        'foreground': '#FFFFFF',
        'foreground_dim': '#b0b0b0',
        'border': '#2a2a2a',
        'border_group': '#114d2b',
        'accent': '#16a34a',
        'accent_hover': '#15803d',
        'accent_pressed': '#166534',
        'accent_light': '#86efac',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#2b2b2b',
        'chart_plot': '#1e1e1e',
        'chart_grid': '#666666',
        'chart_text': '#FFFFFF',
    },
    ColorPalette.BLUE: {
        'background': '#0a0e1a',
        'background_light': '#1a1e2e',
        'background_panel': '#0f1420',
        'background_group': '#1e2a3f',
        'foreground': '#FFFFFF',
        'foreground_dim': '#b0b0b0',
        'border': '#2a3548',
        'border_group': '#1a4d8f',
        'accent': '#3b82f6',
        'accent_hover': '#2563eb',
        'accent_pressed': '#1d4ed8',
        'accent_light': '#93c5fd',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#1e2a3f',
        'chart_plot': '#141b2e',
        'chart_grid': '#4a5568',
        'chart_text': '#FFFFFF',
    },
    ColorPalette.PURPLE: {
        'background': '#0f0a1a',
        'background_light': '#1f1a2e',
        'background_panel': '#140f20',
        'background_group': '#2a1e3f',
        'foreground': '#FFFFFF',
        'foreground_dim': '#b0b0b0',
        'border': '#352a48',
        'border_group': '#4d1a8f',
        'accent': '#a855f7',
        'accent_hover': '#9333ea',
        'accent_pressed': '#7e22ce',
        'accent_light': '#d8b4fe',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#2a1e3f',
        'chart_plot': '#1e141b',
        'chart_grid': '#6b5578',
        'chart_text': '#FFFFFF',
    },
    ColorPalette.ORANGE: {
        'background': '#1a0f0a',
        'background_light': '#2e1f1a',
        'background_panel': '#200f14',
        'background_group': '#3f2a1e',
        'foreground': '#FFFFFF',
        'foreground_dim': '#b0b0b0',
        'border': '#483525',
        'border_group': '#8f4d1a',
        'accent': '#f97316',
        'accent_hover': '#ea580c',
        'accent_pressed': '#c2410c',
        'accent_light': '#fdba74',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#3f2a1e',
        'chart_plot': '#2e1e14',
        'chart_grid': '#78614a',
        'chart_text': '#FFFFFF',
    },
}

# Light Theme Color Palettes
LIGHT_COLORS = {
    ColorPalette.GREEN: {
        'background': '#ffffff',
        'background_light': '#f8f9fa',
        'background_panel': '#f1f3f5',
        'background_group': '#e8f5e9',
        'foreground': '#1a1a1a',
        'foreground_dim': '#666666',
        'border': '#dee2e6',
        'border_group': '#a5d6a7',
        'accent': '#16a34a',
        'accent_hover': '#15803d',
        'accent_pressed': '#166534',
        'accent_light': '#4ade80',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#f8f9fa',
        'chart_plot': '#ffffff',
        'chart_grid': '#999999',
        'chart_text': '#1a1a1a',
    },
    ColorPalette.BLUE: {
        'background': '#ffffff',
        'background_light': '#f8fafc',
        'background_panel': '#f1f5f9',
        'background_group': '#e0f2fe',
        'foreground': '#1a1a1a',
        'foreground_dim': '#666666',
        'border': '#cbd5e1',
        'border_group': '#7dd3fc',
        'accent': '#3b82f6',
        'accent_hover': '#2563eb',
        'accent_pressed': '#1d4ed8',
        'accent_light': '#60a5fa',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#f8fafc',
        'chart_plot': '#ffffff',
        'chart_grid': '#94a3b8',
        'chart_text': '#1a1a1a',
    },
    ColorPalette.PURPLE: {
        'background': '#ffffff',
        'background_light': '#faf8fc',
        'background_panel': '#f5f1f9',
        'background_group': '#f3e8ff',
        'foreground': '#1a1a1a',
        'foreground_dim': '#666666',
        'border': '#ddd6e1',
        'border_group': '#c084fc',
        'accent': '#a855f7',
        'accent_hover': '#9333ea',
        'accent_pressed': '#7e22ce',
        'accent_light': '#c084fc',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#faf8fc',
        'chart_plot': '#ffffff',
        'chart_grid': '#a78baf',
        'chart_text': '#1a1a1a',
    },
    ColorPalette.ORANGE: {
        'background': '#ffffff',
        'background_light': '#fffbf8',
        'background_panel': '#fff5f1',
        'background_group': '#ffedd5',
        'foreground': '#1a1a1a',
        'foreground_dim': '#666666',
        'border': '#e1d6dd',
        'border_group': '#fdba74',
        'accent': '#f97316',
        'accent_hover': '#ea580c',
        'accent_pressed': '#c2410c',
        'accent_light': '#fb923c',
        'danger': '#e11d48',
        'danger_hover': '#be123c',
        'danger_pressed': '#9f1239',
        'chart_bg': '#fffbf8',
        'chart_plot': '#ffffff',
        'chart_grid': '#c9a087',
        'chart_text': '#1a1a1a',
    },
}


def get_stylesheet(colors: Dict[str, str]) -> str:
    """
    Generate stylesheet based on color dictionary.
    
    Args:
        colors: Dictionary of color values
        
    Returns:
        str: Complete CSS stylesheet
    """
    return f"""
QWidget {{
  background-color: {colors['background']};
  color: {colors['foreground']};
  font-family: 'Segoe UI', 'Noto Sans', 'DejaVu Sans', 'Arial', Sans-Serif;
}}

QGroupBox {{
  background-color: {colors['background_group']};
  color: {colors['foreground']};
  border: 1px solid {colors['border_group']};
  border-radius: 8px;
  margin-top: 6px;
  padding: 6px;
  font-weight: bold;
}}

QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 3px;
  color: {colors['accent_light']};
}}

QLabel {{
  background-color: transparent;
  color: {colors['foreground']};
}}

QLabel[role=section] {{
  color: {colors['accent_light']};
  font-weight: bold;
  font-size: 16px;
}}

QLabel[role=title] {{
  color: {colors['accent_light']};
  font-weight: bold;
  font-size: 18px;
}}

QListWidget {{
  background-color: {colors['background_panel']};
  color: {colors['foreground']};
  border: 1px solid {colors['border']};
  border-radius: 4px;
  padding: 2px;
}}

QListWidget::item {{
  padding: 4px;
  border-radius: 2px;
}}

QListWidget::item:hover {{
  background-color: {colors['background_light']};
}}

QListWidget::item:selected {{
  background: {colors['accent']};
  color: #fff;
}}

QTableWidget {{
  background-color: {colors['background_panel']};
  color: {colors['foreground']};
  border: 1px solid {colors['border']};
  border-radius: 4px;
  gridline-color: {colors['border']};
}}

QTableWidget::item {{
  padding: 4px;
  color: {colors['foreground']};
}}

QTableWidget::item:selected {{
  background-color: {colors['accent']};
  color: #FFFFFF;
}}

QHeaderView::section {{
  background-color: {colors['background_group']};
  color: {colors['foreground']};
  border: none;
  padding: 6px;
  font-weight: 600;
  border-bottom: 1px solid {colors['border_group']};
}}

QHeaderView::section:hover {{
  background-color: {colors['accent']};
  color: #FFFFFF;
}}

QPushButton {{
  background-color: {colors['accent']};
  color: #FFFFFF;
  border-radius: 6px;
  padding: 6px 12px;
  font-weight: 500;
  border: none;
}}

QPushButton:hover {{
  background-color: {colors['accent_hover']};
}}

QPushButton:pressed {{
  background-color: {colors['accent_pressed']};
}}

QPushButton:disabled {{
  background-color: {colors['border']};
  color: {colors['foreground_dim']};
}}

QPushButton#clearButton {{
  background-color: {colors['danger']};
}}

QPushButton#clearButton:hover {{
  background-color: {colors['danger_hover']};
}}

QPushButton#clearButton:pressed {{
  background-color: {colors['danger_pressed']};
}}

QPushButton#themeToggleButton {{
  background-color: {colors['background_group']};
  color: {colors['foreground']};
  border: 1px solid {colors['border_group']};
  padding: 4px 8px;
  min-width: 60px;
}}

QPushButton#themeToggleButton:hover {{
  background-color: {colors['accent']};
  color: #FFFFFF;
}}

QComboBox {{
  background-color: {colors['background_panel']};
  color: {colors['foreground']};
  border: 1px solid {colors['border']};
  border-radius: 4px;
  padding: 4px 8px;
  min-width: 80px;
}}

QComboBox:hover {{
  border: 1px solid {colors['accent']};
}}

QComboBox::drop-down {{
  border: none;
  padding-right: 4px;
}}

QComboBox::down-arrow {{
  image: none;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 6px solid {colors['foreground']};
  margin-right: 4px;
}}

QComboBox QAbstractItemView {{
  background-color: {colors['background_panel']};
  color: {colors['foreground']};
  border: 1px solid {colors['border']};
  selection-background-color: {colors['accent']};
  selection-color: #FFFFFF;
}}

QLineEdit {{
  background-color: {colors['background_light']};
  color: {colors['foreground']};
  border: 1px solid {colors['border']};
  border-radius: 4px;
  padding: 4px 8px;
}}

QLineEdit:focus {{
  border: 1px solid {colors['accent']};
}}

QLineEdit:disabled {{
  background-color: {colors['background']};
  color: {colors['foreground_dim']};
}}

QSlider::groove:horizontal {{
  height: 8px;
  background: {colors['border']};
  border-radius: 4px;
}}

QSlider::handle:horizontal {{
  background: {colors['accent']};
  width: 16px;
  margin: -4px 0;
  border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
  background: {colors['accent_hover']};
}}

QSlider::handle:horizontal:pressed {{
  background: {colors['accent_pressed']};
}}

QScrollArea {{
  border: none;
  background-color: transparent;
}}

QScrollBar:vertical {{
  background-color: {colors['background_light']};
  width: 12px;
  border-radius: 6px;
}}

QScrollBar::handle:vertical {{
  background-color: {colors['border']};
  border-radius: 6px;
  min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
  background-color: {colors['accent']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
  height: 0px;
}}

QScrollBar:horizontal {{
  background-color: {colors['background_light']};
  height: 12px;
  border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
  background-color: {colors['border']};
  border-radius: 6px;
  min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
  background-color: {colors['accent']};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
  width: 0px;
}}

QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
  color: {colors['border']};
}}

QDialog {{
  background-color: {colors['background']};
  color: {colors['foreground']};
}}

QMessageBox {{
  background-color: {colors['background']};
  color: {colors['foreground']};
}}

QMessageBox QPushButton {{
  min-width: 80px;
}}

QToolBar {{
  background-color: {colors['background_group']};
  border: none;
  border-bottom: 1px solid {colors['border_group']};
  spacing: 4px;
  padding: 4px;
}}

QToolBar QToolButton {{
  background-color: transparent;
  color: {colors['foreground']};
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
}}

QToolBar QToolButton:hover {{
  background-color: {colors['accent']};
  color: #FFFFFF;
}}

QToolBar QToolButton:pressed {{
  background-color: {colors['accent_pressed']};
}}

QToolBar QToolButton:checked {{
  background-color: {colors['accent']};
  color: #FFFFFF;
}}
"""

