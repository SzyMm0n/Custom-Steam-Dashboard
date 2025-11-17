"""
Main window module for Custom Steam Dashboard.
Contains the primary application window with navigation and view management.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QToolBar
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize
from .ui.home_view_server import HomeView
from .ui.library_view_server import LibraryView
from .ui.comparison_view_server import ComparisonView


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

        # Setup central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Create stacked widget for view management
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Initialize views
        self.home_view = HomeView(server_url=self._server_url)
        self.stack.addWidget(self.home_view)

        self.library_view = LibraryView(server_url=self._server_url)
        self.stack.addWidget(self.library_view)

        self.comparison_view = ComparisonView(server_url=self._server_url)
        self.stack.addWidget(self.comparison_view)

        # Initialize toolbar
        self._init_toolbar()

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

        # Refresh action
        refresh_action = QAction("Odśwież", self)
        refresh_action.triggered.connect(self.refresh_current_view)
        toolbar.addAction(refresh_action)

    # ===== Navigation Methods =====

    def navigate_to_library(self):
        """Navigate to the library view."""
        self.stack.setCurrentWidget(self.library_view)

    def navigate_to_comparison(self):
        """Navigate to the comparison view."""
        self.stack.setCurrentWidget(self.comparison_view)

    def refresh_current_view(self):
        """
        Refresh the currently displayed view.
        Calls refresh_data() method if available on the current widget.
        """
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            asyncio.create_task(current_widget.refresh_data())