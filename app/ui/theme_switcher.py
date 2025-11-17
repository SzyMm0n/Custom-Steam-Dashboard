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

        # Connect to theme changes to update UI
        self._theme_manager.theme_changed.connect(self._on_theme_changed_external)

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
        self._populate_palette_combo()

        self._palette_combo.currentIndexChanged.connect(self._on_palette_changed)
        layout.addWidget(self._palette_combo)

    def _populate_palette_combo(self):
        """Populate the palette combo box with predefined and saved themes."""
        self._palette_combo.clear()

        # Add predefined palettes
        self._palette_combo.addItem("Zielona", ColorPalette.GREEN.value)
        self._palette_combo.addItem("Niebieska", ColorPalette.BLUE.value)
        self._palette_combo.addItem("Fioletowa", ColorPalette.PURPLE.value)
        self._palette_combo.addItem("Pomarańczowa", ColorPalette.ORANGE.value)

        # Add saved custom themes
        from app.core.user_data_manager import UserDataManager
        data_manager = UserDataManager()
        saved_themes = data_manager.get_custom_themes()

        if saved_themes:
            self._palette_combo.insertSeparator(self._palette_combo.count())
            for theme in saved_themes:
                theme_name = theme['name']
                # Use special format to identify custom themes: "custom:theme_name"
                self._palette_combo.addItem(f"⭐ {theme_name}", f"custom:{theme_name}")

        # Add "Create new" option
        self._palette_combo.insertSeparator(self._palette_combo.count())
        self._palette_combo.addItem("🎨 Stwórz nowy...", "custom:new")

        # Set current palette
        current_palette = self._theme_manager.palette
        if current_palette == ColorPalette.CUSTOM:
            # Try to find which custom theme is active
            # For now, just select first custom theme or "Create new"
            for i in range(self._palette_combo.count()):
                data = self._palette_combo.itemData(i)
                if data and data.startswith("custom:") and data != "custom:new":
                    self._palette_combo.setCurrentIndex(i)
                    return
        else:
            index = self._palette_combo.findData(current_palette.value)
            if index >= 0:
                self._palette_combo.setCurrentIndex(index)


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

        if not palette_value:
            return

        # Check if it's a custom theme
        if palette_value.startswith("custom:"):
            theme_name = palette_value[7:]  # Remove "custom:" prefix

            if theme_name == "new":
                # Open dialog to create new theme
                self._open_custom_theme_dialog()
            else:
                # Load existing custom theme
                self._load_custom_theme(theme_name)
        else:
            # Standard palette
            palette = ColorPalette(palette_value)
            self._theme_manager.set_palette(palette)

    def _open_custom_theme_dialog(self):
        """Open custom theme creator dialog."""
        from .custom_theme_dialog import CustomThemeDialog

        dialog = CustomThemeDialog(self)
        dialog.theme_created.connect(self._on_custom_theme_created)

        result = dialog.exec()

        # If user cancelled, revert combo box to previous palette
        if result == dialog.DialogCode.Rejected:
            # Find previous non-custom palette
            current_palette = self._theme_manager.palette
            if current_palette != ColorPalette.CUSTOM:
                index = self._palette_combo.findData(current_palette.value)
                if index >= 0:
                    self._palette_combo.blockSignals(True)
                    self._palette_combo.setCurrentIndex(index)
                    self._palette_combo.blockSignals(False)

    def _load_custom_theme(self, theme_name: str):
        """Load a saved custom theme by name."""
        from app.core.user_data_manager import UserDataManager

        data_manager = UserDataManager()
        theme = data_manager.get_custom_theme(theme_name)

        if theme:
            dark_colors = theme['dark_colors']
            light_colors = theme['light_colors']

            # Set custom colors in theme manager
            self._theme_manager.set_custom_colors(dark_colors, light_colors)

            # Save preference with theme name
            self._theme_manager._save_custom_theme_name(theme_name)

            print(f"✓ Loaded custom theme: {theme_name}")
        else:
            print(f"✗ Custom theme not found: {theme_name}")

    def _on_custom_theme_created(self, dark_colors: dict, light_colors: dict):
        """Handle custom theme creation."""
        # Set custom colors in theme manager
        self._theme_manager.set_custom_colors(dark_colors, light_colors)

        # Get the dialog to check if theme was saved
        dialog = self.sender()
        if hasattr(dialog, '_saved_theme_name'):
            theme_name = dialog._saved_theme_name
            self._theme_manager._save_custom_theme_name(theme_name)
            print(f"✓ Activated custom theme: {theme_name}")

        # Refresh the combo box to show newly saved theme
        self._populate_palette_combo()

        # Select the new theme in combo box if it was saved
        if hasattr(dialog, '_saved_theme_name'):
            theme_name = dialog._saved_theme_name
            search_data = f"custom:{theme_name}"
            for i in range(self._palette_combo.count()):
                if self._palette_combo.itemData(i) == search_data:
                    self._palette_combo.blockSignals(True)
                    self._palette_combo.setCurrentIndex(i)
                    self._palette_combo.blockSignals(False)
                    break

    def _on_theme_changed_external(self, mode: str, palette: str):
        """Handle external theme changes (from other ThemeSwitcher instances or code)."""
        # Update mode button text
        self._update_mode_button_text()

        # Update palette combo box selection
        current_palette = self._theme_manager.palette
        index = self._palette_combo.findData(current_palette.value)
        if index >= 0 and index != self._palette_combo.currentIndex():
            # Block signals to avoid triggering another change
            self._palette_combo.blockSignals(True)
            self._palette_combo.setCurrentIndex(index)
            self._palette_combo.blockSignals(False)

