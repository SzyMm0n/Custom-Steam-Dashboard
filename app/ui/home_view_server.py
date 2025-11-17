# -*- coding: utf-8 -*-
"""
Home view module for Custom Steam Dashboard.
Displays current player counts, game filters, and upcoming releases.
Fetches data from the backend server.
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Set

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame,
    QHBoxLayout, QGroupBox, QSizePolicy,
    QSlider, QPushButton, QLineEdit, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import QTimer, Qt, QLocale

from app.core.services.server_client import ServerClient
from app.ui.components_server import NumberValidator, GameDetailDialog, GameDetailPanel
from app.ui.styles import apply_style, refresh_style
from app.ui.theme_manager import ThemeManager


logger = logging.getLogger(__name__)


# ===== Main Home View Widget =====

class HomeView(QWidget):
    """
    Main home view displaying live game statistics and upcoming releases.
    Fetches data from the backend server.

    Shows:
    - Live player counts for watched games from server
    - Filtering by player count and game tags
    - Upcoming game releases from server
    """

    MAX_PLAYERS_SLIDER = 2000000  # Maximum value for player count slider

    def __init__(self, server_url: Optional[str] = None, parent=None):
        """
        Initialize the home view.

        Args:
            server_url: URL of the backend server (defaults to SERVER_URL from environment)
            parent: Parent widget
        """
        super().__init__(parent)

        # Server client for data fetching
        if server_url is None:
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
            server_url = os.getenv("SERVER_URL", "https://custom-steam-dashboard.pl.eu.org")
        self._server_client = ServerClient(base_url=server_url)
        self._server_url = server_url  # Store for passing to dialogs

        # Data storage
        self._all_games_data: List[Dict[str, Any]] = []
        self._filtered_games_data: List[Dict[str, Any]] = []  # For search filtering
        
        # Filter state
        self._selected_tags: Set[str] = set()
        self._min_players: int = 0
        self._max_players: int = self.MAX_PLAYERS_SLIDER
        self._search_term: str = ""  # Current search term
        
        # Game detail panel (temporary section)
        self._detail_panel: Optional[GameDetailPanel] = None

        # Theme manager - connect BEFORE init_ui to ensure proper initial styling
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

        # UI components
        self.layout = QVBoxLayout(self)
        self.main_h_layout = QHBoxLayout()
        self._locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)

        # Initialize UI
        self._init_ui()

        # Force apply current theme state immediately after UI is built
        colors = self._theme_manager.get_colors()
        self._on_theme_changed(self._theme_manager.mode.value, self._theme_manager.palette.value)

        # Setup automatic refresh timer (5 minutes)
        # Use QTimer.singleShot() to avoid asyncio event loop conflicts
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._timer.start(300000)
        self._timer.timeout.connect(self._schedule_refresh)
        self._timer.start(300000)  # 5 minutes

        # Load initial data
        QTimer.singleShot(0, self._start_initial_load)

    def _start_initial_load(self):
        """Start the initial data load asynchronously."""
        # Use QTimer.singleShot to defer task creation
        asyncio.create_task(self.refresh_data())
    
    def _schedule_refresh(self):
        """Schedule data refresh using QTimer to avoid event loop conflicts."""
        # Use QTimer.singleShot(0, ...) to schedule task in next event loop iteration
        # This prevents "Cannot enter into task while another task is being executed" error
        QTimer.singleShot(0, lambda: asyncio.create_task(self.refresh_data()))

    # ===== UI Initialization =====

    def _init_ui(self):
        """
        Initialize the user interface layout.
        Creates left panel with game list and right panel with filters.
        """
        # Title
        title_layout = QHBoxLayout()
        self.top_live_title = QLabel("Live Games Count")
        self.top_live_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        title_layout.addWidget(self.top_live_title)
        title_layout.addStretch()

        # Left column - Live games list
        left_column = QVBoxLayout()

        # Search bar for filtering games
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Szukaj gry po nazwie lub App ID...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setMinimumHeight(35)
        
        self.clear_search_btn = QPushButton("×")
        self.clear_search_btn.setMaximumWidth(35)
        self.clear_search_btn.setMaximumHeight(35)
        self.clear_search_btn.setToolTip("Wyczyść wyszukiwanie")
        self.clear_search_btn.clicked.connect(self._on_clear_search)
        self.clear_search_btn.setVisible(False)  # Hidden by default
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)
        
        # Search results info label
        self.search_info_label = QLabel("")
        self.search_info_label.setVisible(False)
        
        # Game list
        self.top_live_list = QListWidget()
        self.top_live_list.setMinimumWidth(500)
        self.top_live_list.itemClicked.connect(self._on_live_item_clicked)
        
        left_column.addLayout(search_layout)
        left_column.addWidget(self.search_info_label)
        left_column.addWidget(self.top_live_list)

        # Right column - Filters panel
        right_panel_widget = QWidget()
        right_panel_widget.setMinimumWidth(280)
        right_column_layout = QVBoxLayout(right_panel_widget)

        # Player count filter group
        players_group = QGroupBox("Gracze online (Min. / Max.)")
        players_v_layout = QVBoxLayout(players_group)
        validator = NumberValidator(self)

        # Min player count controls
        min_v_layout = QVBoxLayout()
        min_top_h = QHBoxLayout()
        min_top_h.addWidget(QLabel("Min. graczy:"))
        self.min_players_input = QLineEdit("0")
        self.min_players_input.setValidator(validator)
        self.min_players_input.setMaximumWidth(100)
        min_top_h.addWidget(self.min_players_input)
        self.min_players_input.editingFinished.connect(self._on_min_input_changed)
        min_top_h.addStretch(1)
        min_v_layout.addLayout(min_top_h)

        self.min_players_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_players_slider.setRange(0, self.MAX_PLAYERS_SLIDER)
        self.min_players_slider.setValue(0)
        self.min_players_slider.setTracking(True)
        self.min_players_slider.valueChanged.connect(self._on_min_slider_moved)
        min_v_layout.addWidget(self.min_players_slider)
        self.min_players_label = QLabel(f"Aktualnie Min.: {self._format_players(0)}")
        min_v_layout.addWidget(self.min_players_label)

        # Max player count controls
        max_v_layout = QVBoxLayout()
        max_top_h = QHBoxLayout()
        max_top_h.addWidget(QLabel("Max. graczy:"))
        self.max_players_input = QLineEdit(self._format_players(self.MAX_PLAYERS_SLIDER))
        self.max_players_input.setValidator(validator)
        self.max_players_input.setMaximumWidth(100)
        max_top_h.addWidget(self.max_players_input)
        self.max_players_input.editingFinished.connect(self._on_max_input_changed)
        max_top_h.addStretch(1)
        max_v_layout.addLayout(max_top_h)

        self.max_players_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_players_slider.setRange(0, self.MAX_PLAYERS_SLIDER)
        self.max_players_slider.setValue(self.MAX_PLAYERS_SLIDER)
        self.max_players_slider.setTracking(True)
        self.max_players_slider.valueChanged.connect(self._on_max_slider_moved)
        max_v_layout.addWidget(self.max_players_slider)
        self.max_players_label = QLabel(f"Aktualnie Max.: {self._format_players(self.MAX_PLAYERS_SLIDER)}")
        max_v_layout.addWidget(self.max_players_label)

        players_v_layout.addLayout(min_v_layout)
        players_v_layout.addLayout(max_v_layout)
        right_column_layout.addWidget(players_group)

        # Tags/Categories filter group
        self.tags_group_box = QGroupBox("Filtruj wg kategorii/gatunków")
        tags_v_layout = QVBoxLayout(self.tags_group_box)

        # Use a single QListWidget for tags (checkable items)
        self.tags_list_widget = QListWidget()
        self.tags_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tags_list_widget.setAlternatingRowColors(False)
        self.tags_list_widget.setMinimumHeight(200)
        self.tags_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tags_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tags_list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        tags_v_layout.addWidget(self.tags_list_widget)
        right_column_layout.addWidget(self.tags_group_box)

        # Filter action buttons
        buttons_h_layout = QHBoxLayout()
        self.clear_button = QPushButton("Wyczyść Filtry")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_filters)
        self.apply_button = QPushButton("Zastosuj Filtry")
        self.apply_button.clicked.connect(self._on_apply_filters)
        buttons_h_layout.addWidget(self.clear_button)
        buttons_h_layout.addWidget(self.apply_button)
        right_column_layout.addLayout(buttons_h_layout)
        right_column_layout.addStretch(1)

        # Add panels to main layout
        self.layout.addLayout(title_layout)
        self.main_h_layout.addLayout(left_column, 1)

        # Wrap right panel in scroll area
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel_widget)
        self.main_h_layout.addWidget(right_scroll, 0)

        # Apply common dark theme styling
        apply_style(self)
        self.top_live_title.setProperty("role", "section")

        # Additional content sections (detail panel and upcoming releases)
        # Game detail panel container (initially hidden)
        self.detail_panel_container = QFrame()
        self.detail_panel_layout = QVBoxLayout(self.detail_panel_container)
        self.detail_panel_layout.setContentsMargins(0, 10, 0, 10)
        self.detail_panel_container.setVisible(False)  # Hidden by default

        # Separator before upcoming
        self.separator_upcoming = QFrame()
        self.separator_upcoming.setFrameShape(QFrame.Shape.HLine)
        self.separator_upcoming.setFrameShadow(QFrame.Shadow.Sunken)

        # Upcoming Releases section
        self.upcoming_title = QLabel("Best Upcoming Releases")
        self.upcoming_title.setProperty("role", "section")
        self.upcoming_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.upcoming_list = QListWidget()
        self.upcoming_list.setMinimumHeight(120)
        self.upcoming_list.setMaximumHeight(240)
        self.upcoming_list.itemClicked.connect(self._on_upcoming_item_clicked)

        # Add sections to main layout
        self.layout.addLayout(self.main_h_layout)
        self.layout.addWidget(self.detail_panel_container)  # Panel szczegółów
        self.layout.addWidget(self.separator_upcoming)
        self.layout.addWidget(self.upcoming_title)
        self.layout.addWidget(self.upcoming_list)

    # ===== Event Handlers - Search Bar =====

    def _on_search_changed(self, text: str):
        """Handle search input change - filter games by name or App ID."""
        self._search_term = text.strip().lower()
        
        # Show/hide clear button
        self.clear_search_btn.setVisible(len(self._search_term) > 0)
        
        # Update the view
        self._update_list_view()

    def _on_clear_search(self):
        """Clear the search box and reset filtering."""
        self.search_input.clear()
        self._search_term = ""
        self.clear_search_btn.setVisible(False)
        self._update_list_view()

    # ===== Event Handlers - Slider and Input =====

    def _on_min_slider_moved(self, value: int):
        """Handle minimum player count slider movement."""
        if value > self._max_players:
            self.max_players_slider.blockSignals(True)
            self.max_players_slider.setValue(value)
            self.max_players_slider.blockSignals(False)
            self._max_players = value
            self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(value)}")
            self.max_players_input.setText(self._format_players(value))

        self._min_players = value
        self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(value)}")
        self.min_players_input.setText(self._format_players(value))
        self._update_list_view()

    def _on_max_slider_moved(self, value: int):
        """Handle maximum player count slider movement."""
        if value < self._min_players:
            self.min_players_slider.blockSignals(True)
            self.min_players_slider.setValue(value)
            self.min_players_slider.blockSignals(False)
            self._min_players = value
            self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(value)}")
            self.min_players_input.setText(self._format_players(value))

        self._max_players = value
        self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(value)}")
        self.max_players_input.setText(self._format_players(value))
        self._update_list_view()

    def _on_min_input_changed(self):
        """Handle manual input change for minimum player count."""
        text = self.min_players_input.text().replace(' ', '')
        try:
            val = int(text) if text != '' else 0
        except Exception:
            val = 0
        val = max(0, min(val, self.MAX_PLAYERS_SLIDER))
        self.min_players_slider.blockSignals(True)
        self.min_players_slider.setValue(val)
        self.min_players_slider.blockSignals(False)
        self._min_players = val
        self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(val)}")
        self.min_players_input.setText(self._format_players(val))
        if self._min_players > self._max_players:
            self._max_players = self._min_players
            self.max_players_slider.blockSignals(True)
            self.max_players_slider.setValue(self._max_players)
            self.max_players_slider.blockSignals(False)
            self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(self._max_players)}")
            self.max_players_input.setText(self._format_players(self._max_players))
        self._update_list_view()

    def _on_max_input_changed(self):
        """Handle manual input change for maximum player count."""
        text = self.max_players_input.text().replace(' ', '')
        try:
            val = int(text) if text != '' else self.MAX_PLAYERS_SLIDER
        except Exception:
            val = self.MAX_PLAYERS_SLIDER
        val = max(0, min(val, self.MAX_PLAYERS_SLIDER))
        self.max_players_slider.blockSignals(True)
        self.max_players_slider.setValue(val)
        self.max_players_slider.blockSignals(False)
        self._max_players = val
        self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(val)}")
        self.max_players_input.setText(self._format_players(val))
        if self._max_players < self._min_players:
            self._min_players = self._max_players
            self.min_players_slider.blockSignals(True)
            self.min_players_slider.setValue(self._min_players)
            self.min_players_slider.blockSignals(False)
            self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(self._min_players)}")
            self.min_players_input.setText(self._format_players(self._min_players))
        self._update_list_view()

    # ===== Event Handlers - Filter Actions =====

    def _on_apply_filters(self):
        """Apply selected tag and player count filters."""
        self._selected_tags.clear()
        for i in range(self.tags_list_widget.count()):
            it = self.tags_list_widget.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                self._selected_tags.add(it.text())
        
        # Parse inputs
        min_val_text = self.min_players_input.text().replace(' ', '')
        min_val = int(min_val_text) if min_val_text.isdigit() else 0
        max_val_text = self.max_players_input.text().replace(' ', '')
        max_val = int(max_val_text) if max_val_text.isdigit() else self.MAX_PLAYERS_SLIDER
        self._min_players = max(0, min(min_val, self.MAX_PLAYERS_SLIDER))
        self._max_players = max(0, min(max_val, self.MAX_PLAYERS_SLIDER))
        if self._min_players > self._max_players:
            self._min_players = self._max_players
        
        # Sync sliders
        self.min_players_slider.blockSignals(True)
        self.min_players_slider.setValue(self._min_players)
        self.min_players_slider.blockSignals(False)
        self.max_players_slider.blockSignals(True)
        self.max_players_slider.setValue(self._max_players)
        self.max_players_slider.blockSignals(False)
        self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(self._min_players)}")
        self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(self._max_players)}")
        self._update_list_view()

    def _on_clear_filters(self):
        """Reset all filters to default values."""
        # Reset sliders
        self.min_players_slider.blockSignals(True)
        self.min_players_slider.setValue(0)
        self.min_players_slider.blockSignals(False)
        self.max_players_slider.blockSignals(True)
        self.max_players_slider.setValue(self.MAX_PLAYERS_SLIDER)
        self.max_players_slider.blockSignals(False)
        self._min_players = 0
        self._max_players = self.MAX_PLAYERS_SLIDER
        self.min_players_label.setText(f"Aktualnie Min.: {self._format_players(0)}")
        self.max_players_label.setText(f"Aktualnie Max.: {self._format_players(self.MAX_PLAYERS_SLIDER)}")
        self.min_players_input.setText("0")
        self.max_players_input.setText(self._format_players(self.MAX_PLAYERS_SLIDER))
        
        # Uncheck all tags
        for i in range(self.tags_list_widget.count()):
            it = self.tags_list_widget.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                it.setCheckState(Qt.CheckState.Unchecked)

        self._selected_tags.clear()
        
        # Clear search
        self.search_input.clear()
        self._search_term = ""
        self.clear_search_btn.setVisible(False)
        
        self._update_list_view()

    # ===== Formatting Utilities =====

    def _format_players(self, value: int) -> str:
        """Format player count with Polish locale thousands separator."""
        return self._locale.toString(float(value), 'f', 0)

    # ===== Data Management =====

    async def _populate_tag_checkboxes(self):
        """Populate tag checkboxes from server."""
        if self.tags_list_widget.count() > 0:
            return

        try:
            # Fetch genres and categories from server
            genres = await self._server_client.get_all_genres()
            categories = await self._server_client.get_all_categories()
            all_tags = sorted(list(set(genres + categories)))
        except Exception as e:
            logger.error(f"Error fetching tags from server: {e}")
            all_tags = []

        if not all_tags:
            self.tags_list_widget.addItem("Brak tagów do filtrowania.")
            return

        # Clear and add checkable items
        self.tags_list_widget.clear()
        for tag in all_tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.tags_list_widget.addItem(item)

        self.tags_list_widget.updateGeometry()

    def _update_list_view(self):
        """Update the game list view based on current filters and search."""
        self.top_live_list.clear()
        
        # First apply tag and player count filters
        filtered_results = []
        required_tags = self._selected_tags
        
        for item in self._all_games_data:
            game_tags: Set[str] = item.get("tags", set())
            players: int = item.get("players", 0)
            
            # Player count filters
            if players < self._min_players:
                continue
            if players > self._max_players:
                continue
            
            # Tag filters
            if required_tags and not required_tags.issubset(game_tags):
                continue
            
            filtered_results.append(item)
        
        # Then apply search filter
        if self._search_term:
            search_filtered = []
            for item in filtered_results:
                name = item.get("name", "").lower()
                appid = str(item.get("appid", ""))
                
                # Match by name or appid
                if self._search_term in name or self._search_term in appid:
                    search_filtered.append(item)
            
            # Update search info label
            total_count = len(self._all_games_data)
            found_count = len(search_filtered)
            self.search_info_label.setText(
                f"🔍 Znaleziono <b>{found_count}</b> gier pasujących do \"{self._search_term}\" "
                f"(z {total_count} wszystkich)"
            )
            # Apply theme colors to search info label
            colors = self._theme_manager.get_colors()
            self.search_info_label.setStyleSheet(f"""
                padding: 8px;
                background-color: {colors['background_group']};
                border-left: 4px solid {colors['accent']};
                border-radius: 3px;
                color: {colors['foreground']};
            """)
            self.search_info_label.setVisible(True)
            
            filtered_results = search_filtered
        else:
            self.search_info_label.setVisible(False)
        
        # Sort by player count (descending)
        filtered_results.sort(key=lambda x: x["players"], reverse=True)
        
        # Display results
        if not filtered_results:
            if self._search_term:
                self.top_live_list.addItem(
                    f"Brak gier pasujących do wyszukiwania \"{self._search_term}\""
                )
            else:
                self.top_live_list.addItem("Brak gier pasujących do filtrowania.")
        else:
            for item in filtered_results:
                players_formatted = self._format_players(item["players"])
                name = item['name']
                
                lw_item = QListWidgetItem(f"{players_formatted} - {name}")
                lw_item.setData(Qt.ItemDataRole.UserRole, item)
                self.top_live_list.addItem(lw_item)

    async def refresh_data(self):
        """
        Refresh all data from the server.
        
        Fetches:
        - Current player counts for watchlist games
        - Game tags (genres, categories)
        - Upcoming game releases
        """
        # Update titles to show loading state
        self.top_live_title.setText("Live Games Count — Ładowanie...")
        self.upcoming_title.setText("Best Upcoming Releases — Ładowanie...")
        self.upcoming_list.clear()
        
        # Fetch watchlist games from server
        games = await self._server_client.get_current_players()
        
        if not games:
            self.top_live_title.setText("Live Games Count")
            if self.tags_list_widget.count() == 0:
                await self._populate_tag_checkboxes()
            self.upcoming_title.setText("Best Upcoming Releases")
            self.top_live_list.addItem("Brak danych z serwera. Upewnij się, że serwer działa.")
            return
        
        # Filter games with valid player counts and collect appids
        valid_games = []
        appids_to_fetch = []

        for game in games:
            appid = game.get('appid')
            name = game.get('name', f"AppID {appid}")
            last_count = game.get('last_count', 0)
            
            if last_count <= 0:
                continue
            
            valid_games.append({
                "name": name,
                "players": last_count,
                "appid": appid,
            })
            appids_to_fetch.append(appid)

        # Fetch tags for ALL games in ONE batch request
        try:
            tags_batch = await self._server_client.get_game_tags_batch(appids_to_fetch[:100])
        except Exception as e:
            logger.error(f"Error fetching tags batch: {e}")
            tags_batch = {}

        # Combine game data with tags
        results = []
        for game in valid_games:
            appid = game['appid']
            tags_data = tags_batch.get(appid, {})
            tags = set(tags_data.get('tags', []))

            results.append({
                "name": game['name'],
                "players": game['players'],
                "appid": appid,
                "tags": tags,
            })
        
        self._all_games_data = results
        
        # Populate tags if needed
        if self.tags_list_widget.count() == 0:
            await self._populate_tag_checkboxes()
        
        self._update_list_view()
        self.top_live_title.setText("Live Games Count")
        
        # Fetch upcoming releases
        await self._fetch_upcoming()

    async def _fetch_upcoming(self):
        """Fetch and display upcoming releases from server with content filtering."""
        try:
            upcoming = await self._server_client.get_coming_soon_games()
        except Exception as e:
            logger.error(f"Error fetching upcoming games: {e}")
            upcoming = []
        
        self.upcoming_list.clear()
        self.upcoming_title.setText("Best Upcoming Releases")
        
        if not upcoming:
            self.upcoming_list.addItem("Brak nadchodzących premier.")
            return
        
        # Content filter - słowa kluczowe do wykluczenia (case-insensitive)
        blocked_keywords = [
            'adult', 'sex', 'hentai', 'nsfw', 'porn', 'erotic', 'xxx',
            'sexual', 'nude', 'nudity', 'ecchi', '18+', 'mature content',
            'adult only', 'adults only', 'sexual content'
        ]
        
        # Filter out inappropriate content
        filtered_upcoming = []
        for item in upcoming:
            name = item.get('name', 'Unknown').lower()
            
            # Check if game name contains blocked keywords
            is_blocked = False
            for keyword in blocked_keywords:
                if keyword in name:
                    is_blocked = True
                    logger.debug(f"Filtered out game: {item.get('name')} (matched keyword: {keyword})")
                    break
            
            if not is_blocked:
                filtered_upcoming.append(item)
        
        # Display filtered results
        for item in filtered_upcoming:
            name = item.get('name', 'Unknown')
            appid = item.get('appid') or item.get('id')
            
            try:
                appid_int = int(appid) if appid is not None else None
                if appid_int is not None and appid_int <= 0:
                    appid_int = None
            except Exception:
                appid_int = None
            
            # Get release date
            release_date = item.get('release_date', {})
            if isinstance(release_date, dict):
                release_text = release_date.get('date', '')
            else:
                release_text = str(release_date) if release_date else ''
            
            price = item.get('price', '') or item.get('final_price', '')
            discount = item.get('discount', '') or item.get('discount_percent', '')
            
            display = f"{name}"
            if release_text:
                display += f" — premiera: {release_text}"
            if price:
                display += f" — cena: {price}"
            if discount:
                display += f" (-{discount}%)"
            
            lw = QListWidgetItem(display)
            lw.setData(Qt.ItemDataRole.UserRole, {"name": name, "appid": appid_int})
            self.upcoming_list.addItem(lw)
        
        # Log filtering statistics
        filtered_count = len(upcoming) - len(filtered_upcoming)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} inappropriate game(s) from upcoming releases")

    # ===== Event Handlers - Item Clicks =====

    def _on_live_item_clicked(self, item: QListWidgetItem):
        """Handle click on live games list item - show detail panel."""
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            data = None

        if not data:
            data = item.text() if item is not None else "Nieznana gra"
        
        self._show_game_detail_panel(data)
        # Use QTimer.singleShot to avoid event loop conflicts
        QTimer.singleShot(0, lambda: self._show_game_detail_panel(data))

    def _on_upcoming_item_clicked(self, item: QListWidgetItem):
        """Handle click on upcoming list item - show detail panel."""
        if not item:
            return
        data = None
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        
        if not data:
            data = item.text()
        
        self._show_game_detail_panel(data)
        # Use QTimer.singleShot to avoid event loop conflicts
        QTimer.singleShot(0, lambda: self._show_game_detail_panel(data))
    
    def _show_game_detail_panel(self, game_data: Any) -> None:
        """
        Show game detail panel in the temporary section.
        
        Args:
            game_data: Game data (dict or string)
        """
        # Close existing panel if any
        if self._detail_panel is not None:
            self._detail_panel.setVisible(False)
            self._detail_panel.deleteLater()
            self._detail_panel = None
        
        # Create new panel
        self._detail_panel = GameDetailPanel(game_data, server_url=self._server_url, parent=self)
        self._detail_panel.closed.connect(self._on_detail_panel_closed)
        
        # Add to container
        self.detail_panel_layout.addWidget(self._detail_panel)
        self.detail_panel_container.setVisible(True)
    
    def _on_detail_panel_closed(self) -> None:
        """Handle detail panel close event."""
        self._detail_panel = None
        self.detail_panel_container.setVisible(False)
    
    def _on_deal_item_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle click on deal item (placeholder method).
        Note: Deals functionality is handled in separate deals_view module.
        
        Args:
            item: Clicked list widget item
        """
        logger.debug("Deal item clicked (placeholder method - use deals_view for full functionality)")
        pass

    def _on_theme_changed(self, mode: str, palette: str):
        """Handle theme change event."""
        # Refresh widget style
        refresh_style(self)

        # Update search info label style for current theme
        colors = self._theme_manager.get_colors()
        if self._search_term:
            self.search_info_label.setStyleSheet(f"""
                padding: 8px;
                background-color: {colors['background_group']};
                border-left: 4px solid {colors['accent']};
                border-radius: 3px;
                color: {colors['foreground']};
            """)
