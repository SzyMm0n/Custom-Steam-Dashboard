"""
Main window module for Custom Steam Dashboard.
Contains the primary application window with navigation and view management.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QToolBar, QSizePolicy
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize
from .ui.home_view_server import HomeView
from .ui.library_view_server import LibraryView
from .ui.comparison_view_server import ComparisonView
from .ui.deals_view_server import DealsView
from .ui.styles import apply_style, refresh_style
from .ui.theme_manager import ThemeManager
from .ui.theme_switcher import ThemeSwitcher


class MainWindow(QMainWindow):
    """
    Main application window with toolbar navigation and multiple views.

    Features:
    - Home view: Live game statistics and deals (from server)
    - Library view: User game library browser
    - Toolbar navigation between views
    - Refresh functionality
    """

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the main window.

        Args:
            server_url: URL of the backend server (defaults to SERVER_URL from environment)
        """
        super().__init__()
        self.setWindowTitle("Steam Dashboard")
        self.setMinimumSize(1000, 800)
        
        # Set window icon
        self._set_window_icon()

        if server_url is None:
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self._server_url = server_url

        # Initialize theme manager FIRST - this ensures singleton is created with default values
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

        # Setup central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Create stacked widget for view management
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Initialize views - they will all use the same ThemeManager singleton
        self.home_view = HomeView(server_url=self._server_url)
        self.stack.addWidget(self.home_view)

        self.library_view = LibraryView(server_url=self._server_url)
        self.stack.addWidget(self.library_view)

        self.comparison_view = ComparisonView(server_url=self._server_url)
        self.stack.addWidget(self.comparison_view)

        self.deals_view = DealsView(server_url=self._server_url)
        self.stack.addWidget(self.deals_view)

        # Initialize toolbar
        self._init_toolbar()

        # Apply initial theme to main window
        apply_style(self)

    # ===== UI Initialization =====

    def _set_window_icon(self):
        """
        Set the window icon for the application.
        Tries to find icon in multiple locations (dev and bundled executable).
        """
        # Possible icon paths (in order of preference)
        icon_paths = [
            # For bundled executable (PyInstaller)
            Path(sys._MEIPASS) / "icons" / "icon-128x128.png" if hasattr(sys, '_MEIPASS') else None,
            # For development - relative to this file
            Path(__file__).parent / "icons" / "icon-128x128.png",
            # Alternative sizes
            Path(__file__).parent / "icons" / "icon-32x32.png",
            Path(__file__).parent / "icons" / "icon-16x16.png",
        ]

        # Try each path until we find a valid icon
        for icon_path in icon_paths:
            if icon_path and icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    return

        # If no icon found, log a warning but continue
        print("Warning: Could not find application icon")

    def _init_toolbar(self):
        """
        Initialize the navigation toolbar.
        Creates actions for navigating between views and refreshing data.
        """
        toolbar = QToolBar("Menu")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Home view action
        home_action = QAction("Home", self)
        home_action.triggered.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        toolbar.addAction(home_action)

        # Library view action
        lib_action = QAction("Biblioteka gier", self)
        lib_action.triggered.connect(self.navigate_to_library)
        toolbar.addAction(lib_action)

        # Comparison view action
        comparison_action = QAction("Porównanie gier", self)
        comparison_action.triggered.connect(self.navigate_to_comparison)
        toolbar.addAction(comparison_action)

        # Deals view action
        deals_action = QAction("Promocje", self)
        deals_action.triggered.connect(self.navigate_to_deals)
        toolbar.addAction(deals_action)

        # Refresh action
        refresh_action = QAction("Odśwież", self)
        refresh_action.triggered.connect(self.refresh_current_view)
        toolbar.addAction(refresh_action)

        # Add separator and spacer to push theme switcher to the right
        toolbar.addSeparator()

        # Spacer widget to push theme switcher to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Theme switcher in the toolbar (right side)
        self._theme_switcher = ThemeSwitcher()
        toolbar.addWidget(self._theme_switcher)

    # ===== Navigation Methods =====

    def navigate_to_library(self):
        """Navigate to the library view."""
        self.stack.setCurrentWidget(self.library_view)

    def navigate_to_comparison(self):
        """Navigate to the comparison view."""
        self.stack.setCurrentWidget(self.comparison_view)

    def navigate_to_deals(self):
        """Navigate to the deals view."""
        self.stack.setCurrentWidget(self.deals_view)

    def refresh_current_view(self):
        """
        Refresh the currently displayed view.
        Calls refresh_data() method if available on the current widget.
        """
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            asyncio.create_task(current_widget.refresh_data())

    def _on_theme_changed(self, mode: str, palette: str):
        """Handle theme change event."""
        # Refresh main window style
        refresh_style(self)
    
    def _load_window_geometry(self):
        """Load saved window geometry."""
        try:
            from app.core.user_data_manager import UserDataManager
            data_manager = UserDataManager()
            geometry = data_manager.get_window_geometry()
            
            if geometry['size']:
                width, height = geometry['size']
                self.resize(width, height)
            
            if geometry['position']:
                x, y = geometry['position']
                self.move(x, y)
        except Exception as e:
            print(f"Could not load window geometry: {e}")
    
    def closeEvent(self, event):
        """Save window geometry on close."""
        try:
            from app.core.user_data_manager import UserDataManager
            data_manager = UserDataManager()
            
            # Save window size and position
            size = (self.width(), self.height())
            position = (self.x(), self.y())
            data_manager.save_window_geometry(size, position)
        except Exception as e:
            print(f"Could not save window geometry: {e}")
        
        event.accept()
