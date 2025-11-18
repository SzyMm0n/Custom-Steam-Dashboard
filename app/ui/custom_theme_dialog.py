"""
Custom Theme Creator Dialog for Custom Steam Dashboard.
Allows users to create custom color palettes based on a base color.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QColorDialog, QWidget, QRadioButton, QButtonGroup,
    QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Dict


class CustomThemeDialog(QDialog):
    """
    Dialog for creating custom color themes.
    
    Features:
    - Color picker for base color selection
    - Live preview of theme elements
    - Dark/Light mode toggle
    - Automatic palette generation
    - Preview of buttons, text, and accent colors
    """
    
    theme_created = Signal(dict, dict)  # Signal(dark_colors, light_colors)
    
    def __init__(self, parent=None):
        """Initialize the custom theme creator dialog."""
        super().__init__(parent)
        self.setWindowTitle("Kreator własnego motywu")
        self.setMinimumSize(700, 600)
        
        # Current state
        self._base_color = QColor("#16a34a")  # Default green
        self._preview_mode = "dark"  # "dark" or "light"
        
        self._init_ui()
        self._update_preview()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Kreator własnego motywu")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Wybierz kolor bazowy, a system automatycznie wygeneruje kompletną paletę kolorów.\n"
            "Możesz podejrzeć jak będzie wyglądać w trybie ciemnym i jasnym."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin: 5px 10px; color: #888;")
        layout.addWidget(instructions)
        
        # Color picker section
        picker_group = self._create_color_picker_section()
        layout.addWidget(picker_group)

        # Theme name section
        name_group = self._create_name_section()
        layout.addWidget(name_group)

        # Mode selector
        mode_group = self._create_mode_selector()
        layout.addWidget(mode_group)
        
        # Live preview section
        preview_group = self._create_preview_section()
        layout.addWidget(preview_group, 1)
        
        # Buttons
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)
    
    def _create_color_picker_section(self) -> QWidget:
        """Create color picker section."""
        group = QGroupBox("Wybór koloru bazowego")
        layout = QHBoxLayout(group)
        
        # Color preview
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(80, 80)
        self._color_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._color_preview)
        
        # Color info
        info_layout = QVBoxLayout()
        self._color_label = QLabel(f"Wybrany kolor: {self._base_color.name()}")
        self._color_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        info_layout.addWidget(self._color_label)
        
        desc = QLabel("Kliknij 'Wybierz kolor' aby otworzyć paletę kolorów")
        desc.setStyleSheet("color: #888;")
        info_layout.addWidget(desc)
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)
        
        # Pick button
        pick_btn = QPushButton("Wybierz kolor")
        pick_btn.setMinimumHeight(40)
        pick_btn.clicked.connect(self._pick_color)
        layout.addWidget(pick_btn)
        
        # Now update the preview after widgets are created
        self._update_color_preview()

        return group
    
    def _create_name_section(self) -> QWidget:
        """Create theme name input section."""
        group = QGroupBox("Nazwa motywu (opcjonalnie)")
        layout = QVBoxLayout(group)

        # Name input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Nazwa:"))

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("np. Mój Niebieski Motyw")
        self._name_input.setMaxLength(50)
        input_layout.addWidget(self._name_input, 1)

        layout.addLayout(input_layout)

        # Save checkbox
        self._save_checkbox = QCheckBox("Zapisz motyw do listy moich motywów")
        self._save_checkbox.setChecked(False)
        self._save_checkbox.toggled.connect(self._on_save_checkbox_toggled)
        layout.addWidget(self._save_checkbox)

        # Info label
        self._save_info = QLabel("💡 Zapisane motywy będą dostępne w menu palet")
        self._save_info.setStyleSheet("color: #888; font-size: 10pt;")
        self._save_info.setVisible(False)
        layout.addWidget(self._save_info)

        return group

    def _on_save_checkbox_toggled(self, checked: bool):
        """Handle save checkbox toggle."""
        self._save_info.setVisible(checked)
        if checked and not self._name_input.text().strip():
            # Auto-generate name based on color
            color_name = self._base_color.name().upper()
            self._name_input.setText(f"Własny {color_name}")

    def _create_mode_selector(self) -> QWidget:
        """Create mode selector (dark/light)."""
        group = QGroupBox("Podgląd trybu")
        layout = QHBoxLayout(group)
        
        self._mode_button_group = QButtonGroup(self)
        
        # Dark mode radio
        dark_radio = QRadioButton("🌙 Tryb ciemny")
        dark_radio.setChecked(True)
        self._mode_button_group.addButton(dark_radio, 0)
        layout.addWidget(dark_radio)
        
        # Light mode radio
        light_radio = QRadioButton("☀️ Tryb jasny")
        self._mode_button_group.addButton(light_radio, 1)
        layout.addWidget(light_radio)
        
        layout.addStretch()
        
        # Connect signal
        self._mode_button_group.buttonClicked.connect(self._on_mode_changed)
        
        return group
    
    def _create_preview_section(self) -> QWidget:
        """Create live preview section."""
        group = QGroupBox("Podgląd na żywo")
        layout = QVBoxLayout(group)
        
        # Preview container
        self._preview_container = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_container)
        self._preview_layout.setContentsMargins(20, 20, 20, 20)
        self._preview_layout.setSpacing(15)
        
        # Title in preview
        self._preview_title = QLabel("Przykładowy tytuł")
        self._preview_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self._preview_layout.addWidget(self._preview_title)
        
        # Description text
        self._preview_text = QLabel("To jest przykładowy tekst, który pokazuje jak będzie wyglądać treść w twoim motywie.")
        self._preview_text.setWordWrap(True)
        self._preview_layout.addWidget(self._preview_text)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        self._preview_button_normal = QPushButton("Przycisk akcji")
        self._preview_button_normal.setMinimumHeight(35)
        buttons_layout.addWidget(self._preview_button_normal)
        
        self._preview_button_danger = QPushButton("Przycisk anuluj")
        self._preview_button_danger.setObjectName("dangerButton")
        self._preview_button_danger.setMinimumHeight(35)
        buttons_layout.addWidget(self._preview_button_danger)
        
        buttons_layout.addStretch()
        self._preview_layout.addLayout(buttons_layout)
        
        # Group box example
        self._preview_group = QGroupBox("Przykładowa grupa")
        preview_group_layout = QVBoxLayout(self._preview_group)
        preview_group_layout.addWidget(QLabel("Zawartość grupy z akcentowym kolorem"))
        self._preview_layout.addWidget(self._preview_group)
        
        self._preview_layout.addStretch()
        
        layout.addWidget(self._preview_container)
        
        return group
    
    def _create_button_section(self) -> QHBoxLayout:
        """Create dialog buttons."""
        layout = QHBoxLayout()
        
        # Reset button
        reset_btn = QPushButton("Resetuj")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self._reset_to_default)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("Zastosuj motyw")
        apply_btn.setMinimumHeight(40)
        apply_btn.setStyleSheet("font-weight: bold;")
        apply_btn.clicked.connect(self._apply_theme)
        layout.addWidget(apply_btn)
        
        return layout
    
    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(
            self._base_color, 
            self, 
            "Wybierz kolor bazowy",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        
        if color.isValid():
            self._base_color = color
            self._update_color_preview()
            self._update_preview()
    
    def _on_mode_changed(self, button):
        """Handle mode change (dark/light)."""
        button_id = self._mode_button_group.id(button)
        self._preview_mode = "dark" if button_id == 0 else "light"
        self._update_preview()
    
    def _reset_to_default(self):
        """Reset to default green color."""
        self._base_color = QColor("#16a34a")
        self._update_color_preview()
        self._update_preview()
    
    def _update_color_preview(self):
        """Update the color preview box."""
        self._color_preview.setStyleSheet(
            f"background-color: {self._base_color.name()}; "
            f"border: 2px solid #333; border-radius: 8px;"
        )
        self._color_label.setText(f"Wybrany kolor: {self._base_color.name().upper()}")
    
    def _update_preview(self):
        """Update the live preview with current colors."""
        # Generate palette
        colors = self._generate_palette(self._base_color, self._preview_mode)
        
        # Apply to preview container
        self._preview_container.setStyleSheet(
            f"QWidget {{ background-color: {colors['background']}; color: {colors['foreground']}; }}"
        )
        
        # Title
        self._preview_title.setStyleSheet(
            f"font-size: 16pt; font-weight: bold; color: {colors['accent_light']};"
        )
        
        # Text
        self._preview_text.setStyleSheet(f"color: {colors['foreground']};")
        
        # Normal button
        self._preview_button_normal.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent_pressed']};
            }}
            """
        )
        
        # Danger button
        self._preview_button_danger.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['danger_pressed']};
            }}
            """
        )
        
        # Group box
        self._preview_group.setStyleSheet(
            f"""
            QGroupBox {{
                background-color: {colors['background_group']};
                border: 1px solid {colors['border_group']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                color: {colors['accent_light']};
            }}
            QLabel {{
                color: {colors['foreground']};
            }}
            """
        )
    
    def _generate_palette(self, base_color: QColor, mode: str) -> Dict[str, str]:
        """
        Generate a complete color palette from a base color.
        
        Args:
            base_color: Base color to generate palette from
            mode: "dark" or "light"
            
        Returns:
            Dictionary with all theme colors
        """
        # Convert to HSV for manipulation
        h, s, v, _ = base_color.getHsvF()
        
        if mode == "dark":
            return {
                'background': self._adjust_color(h, max(0.05, s * 0.3), 0.04).name(),
                'background_light': self._adjust_color(h, max(0.05, s * 0.3), 0.10).name(),
                'background_panel': self._adjust_color(h, max(0.05, s * 0.3), 0.07).name(),
                'background_group': self._adjust_color(h, s * 0.6, 0.15).name(),
                'foreground': '#FFFFFF',
                'foreground_dim': '#b0b0b0',
                'border': self._adjust_color(h, max(0.1, s * 0.4), 0.16).name(),
                'border_group': self._adjust_color(h, s * 0.8, 0.35).name(),
                'accent': base_color.name(),
                'accent_hover': self._adjust_color(h, s, max(0.1, v - 0.15)).name(),
                'accent_pressed': self._adjust_color(h, s, max(0.05, v - 0.25)).name(),
                'accent_light': self._adjust_color(h, max(0.5, s * 0.8), min(1.0, v + 0.3)).name(),
                'danger': '#e11d48',
                'danger_hover': '#be123c',
                'danger_pressed': '#9f1239',
                'chart_bg': self._adjust_color(h, max(0.05, s * 0.3), 0.17).name(),
                'chart_plot': self._adjust_color(h, max(0.05, s * 0.3), 0.12).name(),
                'chart_grid': '#666666',
                'chart_text': '#FFFFFF',
            }
        else:  # light mode
            return {
                'background': '#ffffff',
                'background_light': self._adjust_color(h, max(0.05, s * 0.2), 0.97).name(),
                'background_panel': self._adjust_color(h, max(0.05, s * 0.2), 0.94).name(),
                'background_group': self._adjust_color(h, s * 0.4, 0.92).name(),
                'foreground': '#1a1a1a',
                'foreground_dim': '#666666',
                'border': self._adjust_color(h, max(0.1, s * 0.3), 0.87).name(),
                'border_group': self._adjust_color(h, s * 0.6, 0.75).name(),
                'accent': base_color.name(),
                'accent_hover': self._adjust_color(h, s, max(0.1, v - 0.15)).name(),
                'accent_pressed': self._adjust_color(h, s, max(0.05, v - 0.25)).name(),
                'accent_light': self._adjust_color(h, max(0.5, s * 0.8), min(1.0, v + 0.1)).name(),
                'danger': '#e11d48',
                'danger_hover': '#be123c',
                'danger_pressed': '#9f1239',
                'chart_bg': self._adjust_color(h, max(0.05, s * 0.2), 0.97).name(),
                'chart_plot': '#ffffff',
                'chart_grid': '#999999',
                'chart_text': '#1a1a1a',
            }
    
    def _adjust_color(self, h: float, s: float, v: float) -> QColor:
        """
        Create a color from HSV values.
        
        Args:
            h: Hue (0.0 - 1.0)
            s: Saturation (0.0 - 1.0)
            v: Value/Brightness (0.0 - 1.0)
            
        Returns:
            QColor object
        """
        color = QColor()
        color.setHsvF(h, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)), 1.0)
        return color
    
    def _apply_theme(self):
        """Apply the custom theme and emit signal."""
        # Generate both dark and light palettes
        dark_colors = self._generate_palette(self._base_color, "dark")
        light_colors = self._generate_palette(self._base_color, "light")
        
        theme_name = None

        # Save theme if checkbox is checked
        if self._save_checkbox.isChecked():
            name = self._name_input.text().strip()
            if not name:
                name = f"Własny {self._base_color.name().upper()}"
            
            # Check for duplicate names
            from app.core.user_data_manager import UserDataManager
            from PySide6.QtWidgets import QMessageBox

            data_manager = UserDataManager()
            existing_theme = data_manager.get_custom_theme(name)

            if existing_theme:
                # Ask user if they want to overwrite
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Motyw już istnieje")
                msg.setText(f"Motyw o nazwie '{name}' już istnieje.")
                msg.setInformativeText("Czy chcesz go zastąpić?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg.setDefaultButton(QMessageBox.StandardButton.No)

                if msg.exec() != QMessageBox.StandardButton.Yes:
                    # User cancelled, don't save
                    return

            theme_name = name

            success = data_manager.save_custom_theme(
                name=name,
                dark_colors=dark_colors,
                light_colors=light_colors,
                base_color=self._base_color.name()
            )
            
            if success:
                print(f"✓ Saved custom theme: {name}")
        
        # Emit signal with both palettes and theme name
        self.theme_created.emit(dark_colors, light_colors)
        
        # If theme was saved, store the name in a property for ThemeSwitcher
        if theme_name:
            self._saved_theme_name = theme_name

        # Close dialog
        self.accept()

