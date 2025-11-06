"""
Common styling module for Custom Steam Dashboard.
Provides consistent dark theme styling across all UI components.
"""

# Dark theme color palette
COLORS = {
    'background': '#0b0b0b',
    'background_light': '#1b1b1b',
    'background_panel': '#111111',
    'background_group': '#15331f',
    'foreground': '#FFFFFF',
    'border': '#2a2a2a',
    'border_group': '#114d2b',
    'accent_green': '#16a34a',
    'accent_green_light': '#86efac',
    'accent_red': '#e11d48',
    'slider_groove': '#2a2a2a',
}

# Common stylesheet that can be used across all components
COMMON_STYLE = """
QWidget {
  background-color: #0b0b0b;
  color: #FFFFFF;
  font-family: 'Segoe UI', 'Noto Sans', 'DejaVu Sans', 'Arial', Sans-Serif;
}

QGroupBox {
  background-color: #15331f;
  color: #FFFFFF;
  border: 1px solid #114d2b;
  border-radius: 8px;
  margin-top: 6px;
  padding: 6px;
  font-weight: bold;
}

QGroupBox::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 3px;
  color: #86efac;
}

QLabel {
  background-color: transparent;
  color: #FFFFFF;
}

QLabel[role=section] {
  color: #86efac;
  font-weight: bold;
  font-size: 16px;
}

QLabel[role=title] {
  color: #86efac;
  font-weight: bold;
  font-size: 18px;
}

QListWidget {
  background-color: #111111;
  color: #FFFFFF;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  padding: 2px;
}

QListWidget::item {
  padding: 4px;
  border-radius: 2px;
}

QListWidget::item:hover {
  background-color: #1b1b1b;
}

QListWidget::item:selected {
  background: #16a34a;
  color: #fff;
}

QTableWidget {
  background-color: #111111;
  color: #FFFFFF;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  gridline-color: #2a2a2a;
}

QTableWidget::item {
  padding: 4px;
}

QTableWidget::item:selected {
  background-color: #16a34a;
  color: #FFFFFF;
}

QHeaderView::section {
  background-color: #15331f;
  color: #FFFFFF;
  border: none;
  padding: 6px;
  font-weight: 600;
  border-bottom: 1px solid #114d2b;
}

QHeaderView::section:hover {
  background-color: #1a4028;
}

QPushButton {
  background-color: #16a34a;
  color: #FFFFFF;
  border-radius: 6px;
  padding: 6px 12px;
  font-weight: 500;
  border: none;
}

QPushButton:hover {
  background-color: #15803d;
}

QPushButton:pressed {
  background-color: #166534;
}

QPushButton:disabled {
  background-color: #2a2a2a;
  color: #666666;
}

QPushButton#clearButton {
  background-color: #e11d48;
}

QPushButton#clearButton:hover {
  background-color: #be123c;
}

QPushButton#clearButton:pressed {
  background-color: #9f1239;
}

QLineEdit {
  background-color: #1b1b1b;
  color: #FFFFFF;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  padding: 4px 8px;
}

QLineEdit:focus {
  border: 1px solid #16a34a;
}

QLineEdit:disabled {
  background-color: #0b0b0b;
  color: #666666;
}

QSlider::groove:horizontal {
  height: 8px;
  background: #2a2a2a;
  border-radius: 4px;
}

QSlider::handle:horizontal {
  background: #16a34a;
  width: 16px;
  margin: -4px 0;
  border-radius: 8px;
}

QSlider::handle:horizontal:hover {
  background: #15803d;
}

QSlider::handle:horizontal:pressed {
  background: #166534;
}

QScrollArea {
  border: none;
  background-color: transparent;
}

QScrollBar:vertical {
  background-color: #1b1b1b;
  width: 12px;
  border-radius: 6px;
}

QScrollBar::handle:vertical {
  background-color: #2a2a2a;
  border-radius: 6px;
  min-height: 20px;
}

QScrollBar::handle:vertical:hover {
  background-color: #16a34a;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
  height: 0px;
}

QScrollBar:horizontal {
  background-color: #1b1b1b;
  height: 12px;
  border-radius: 6px;
}

QScrollBar::handle:horizontal {
  background-color: #2a2a2a;
  border-radius: 6px;
  min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
  background-color: #16a34a;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
  width: 0px;
}

QFrame[frameShape="4"],
QFrame[frameShape="5"] {
  color: #2a2a2a;
}

QDialog {
  background-color: #0b0b0b;
  color: #FFFFFF;
}

QMessageBox {
  background-color: #0b0b0b;
  color: #FFFFFF;
}

QMessageBox QPushButton {
  min-width: 80px;
}
"""


def apply_style(widget):
    """
    Apply the common dark theme style to a widget.
    
    Args:
        widget: QWidget to apply styling to
    """
    widget.setStyleSheet(COMMON_STYLE)


def get_style():
    """
    Get the common stylesheet string.
    
    Returns:
        str: CSS stylesheet for dark theme
    """
    return COMMON_STYLE


def get_color(color_name: str) -> str:
    """
    Get a color value from the theme palette.
    
    Args:
        color_name: Name of the color (e.g., 'accent_green', 'background')
        
    Returns:
        str: Hex color code
    """
    return COLORS.get(color_name, '#FFFFFF')

