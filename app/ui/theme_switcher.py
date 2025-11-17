"""
Theme switcher widget for Custom Steam Dashboard.
Provides UI controls for switching themes and color palettes.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel
from .theme_manager import ThemeManager, ThemeMode, ColorPalette


class ThemeSwitcher(QWidget):
    """
    Widget providing theme switching controls.

    Features:
    - Dark/Light mode toggle button
    - Color palette selector
    """

    def __init__(self, parent=None):
        """Initialize the theme switcher widget."""
        super().__init__(parent)
        self._theme_manager = ThemeManager()
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Theme mode toggle button
        self._mode_button = QPushButton()
        self._mode_button.setObjectName("themeToggleButton")
        self._mode_button.clicked.connect(self._toggle_mode)
        self._update_mode_button_text()
        layout.addWidget(self._mode_button)

        # Palette label
        palette_label = QLabel("Paleta:")
        layout.addWidget(palette_label)

        # Palette selector
        self._palette_combo = QComboBox()
        self._palette_combo.addItem("Zielona", ColorPalette.GREEN.value)
        self._palette_combo.addItem("Niebieska", ColorPalette.BLUE.value)
        self._palette_combo.addItem("Fioletowa", ColorPalette.PURPLE.value)
        self._palette_combo.addItem("Pomarańczowa", ColorPalette.ORANGE.value)

        # Set current palette
        current_palette = self._theme_manager.palette
        index = self._palette_combo.findData(current_palette.value)
        if index >= 0:
            self._palette_combo.setCurrentIndex(index)

        self._palette_combo.currentIndexChanged.connect(self._on_palette_changed)
        layout.addWidget(self._palette_combo)

    def _update_mode_button_text(self):
        """Update the mode button text based on current theme."""
        if self._theme_manager.mode == ThemeMode.DARK:
            self._mode_button.setText("🌙 Ciemny")
        else:
            self._mode_button.setText("☀️ Jasny")

    def _toggle_mode(self):
        """Toggle between dark and light mode."""
        self._theme_manager.toggle_mode()
        self._update_mode_button_text()

    def _on_palette_changed(self, index):
        """Handle palette selection change."""
        palette_value = self._palette_combo.itemData(index)
        palette = ColorPalette(palette_value)
        self._theme_manager.set_palette(palette)

