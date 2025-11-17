"""
Common styling module for Custom Steam Dashboard.
Provides consistent theme styling across all UI components.
This module is kept for backward compatibility and delegates to theme_manager.
"""

from .theme_manager import (
    ThemeManager,
    get_stylesheet,
)

# Lazy initialization to avoid circular imports
_theme_manager = None


def _get_theme_manager():
    """Get or create theme manager singleton."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


# Backward compatibility - expose current colors
def _get_current_colors():
    """Get current theme colors."""
    return _get_theme_manager().get_colors()


def get_colors():
    """Get current theme colors (public API)."""
    return _get_current_colors()



def get_common_style() -> str:
    """
    Get the common stylesheet string for current theme.

    Returns:
        str: CSS stylesheet for current theme
    """
    colors = _get_theme_manager().get_colors()
    return get_stylesheet(colors)



def apply_style(widget):
    """
    Apply the current theme style to a widget.

    Args:
        widget: QWidget to apply styling to
    """
    colors = _get_theme_manager().get_colors()
    stylesheet = get_stylesheet(colors)
    widget.setStyleSheet(stylesheet)


def get_style():
    """
    Get the common stylesheet string.

    Returns:
        str: CSS stylesheet for current theme
    """
    return get_common_style()


def get_color(color_name: str) -> str:
    """
    Get a color value from the current theme palette.

    Args:
        color_name: Name of the color (e.g., 'accent', 'background')

    Returns:
        str: Hex color code
    """
    colors = _get_theme_manager().get_colors()
    return colors.get(color_name, '#FFFFFF')


def refresh_style(widget):
    """
    Refresh the style of a widget with current theme.
    Useful after theme changes.

    Args:
        widget: QWidget to refresh styling on
    """
    apply_style(widget)

