"""
Library view module for Custom Steam Dashboard (Server-Based).
Displays user's Steam game library with playtime statistics using server API.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtGui import QPixmap

import httpx
from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style

logger = logging.getLogger(__name__)


class LibraryView(QWidget):
    """
    Library view widget for displaying Steam user's game collection.
    Fetches data from the backend server.
    
    Features:
    - Accepts SteamID64, vanity name, or profile URL
    - Displays game library with playtime statistics via server
    - Shows total hours and recent (2 weeks) playtime
    - No API key required (server handles authentication)
    """

    def __init__(self, server_url: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the library view.

        Args:
            server_url: URL of the backend server (defaults to SERVER_URL from environment)
            parent: Parent widget
        """
        super().__init__(parent)
        if server_url is None:
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self._server_client = ServerClient(base_url=server_url)
        
        # Store games data for sorting
        self._games_data = []
        
        # Track current sort order for each column
        self._sort_orders = {
            0: Qt.SortOrder.AscendingOrder,   # Name column
            1: Qt.SortOrder.DescendingOrder,  # Total hours
            2: Qt.SortOrder.DescendingOrder   # Last 2 weeks
        }
        
        self._init_ui()

    # ===== UI Initialization =====

    def _init_ui(self) -> None:
        """
        Initialize the user interface layout.
        Creates profile header, input fields, and game library table.
        """
        layout = QVBoxLayout(self)

        # Title section
        title = QLabel("Biblioteka gier")
        f = title.font()
        f.setPointSize(f.pointSize() + 2)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        # Profile header with avatar and username
        profile_row = QHBoxLayout()
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(64, 64)
        self.avatar_lbl.setScaledContents(True)
        profile_row.addWidget(self.avatar_lbl)
        self.persona_lbl = QLabel("Nieznany użytkownik")
        pf = self.persona_lbl.font()
        pf.setPointSize(pf.pointSize() + 1)
        pf.setBold(True)
        self.persona_lbl.setFont(pf)
        profile_row.addWidget(self.persona_lbl, 1)
        layout.addLayout(profile_row)

        # Input row for SteamID/URL
        row = QHBoxLayout()
        row.addWidget(QLabel("SteamID / URL / vanity:"))
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("np. 7656119..., lub https://steamcommunity.com/id/TwojaNazwa")
        row.addWidget(self.id_input, 1)
        self.fetch_btn = QPushButton("Pobierz")
        self.fetch_btn.clicked.connect(lambda: asyncio.create_task(self._on_fetch()))
        row.addWidget(self.fetch_btn)
        layout.addLayout(row)

        # Status label
        self.status = QLabel("")
        layout.addWidget(self.status)

        # Game library table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Nazwa gry",
            "Łączna liczba godzin",
            "Ostatnie 2 tygodnie (h)"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting by clicking headers
        self.table.setSortingEnabled(False)  # We'll handle sorting manually for better control
        header.sectionClicked.connect(self._on_header_clicked)
        header.setCursor(Qt.CursorShape.PointingHandCursor)  # Show clickable cursor
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Apply common dark theme styling
        apply_style(self)
        title.setProperty("role", "title")

    # ===== Event Handlers =====

    def _on_header_clicked(self, logical_index: int) -> None:
        """
        Handle header click to sort the table by that column.
        
        Args:
            logical_index: Column index that was clicked
                0 - Game name
                1 - Total hours
                2 - Last 2 weeks hours
        """
        if not self._games_data:
            return
        
        # Toggle sort order for this column
        current_order = self._sort_orders.get(logical_index, Qt.SortOrder.AscendingOrder)
        new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        self._sort_orders[logical_index] = new_order
        
        # Sort based on clicked column
        if logical_index == 0:  # Name column
            sorted_games = sorted(
                self._games_data,
                key=lambda g: g.get('name', '').lower(),
                reverse=(new_order == Qt.SortOrder.DescendingOrder)
            )
        elif logical_index == 1:  # Total hours
            sorted_games = sorted(
                self._games_data,
                key=lambda g: g.get('playtime_forever', 0),
                reverse=(new_order == Qt.SortOrder.DescendingOrder)
            )
        else:  # logical_index == 2, Last 2 weeks
            sorted_games = sorted(
                self._games_data,
                key=lambda g: g.get('playtime_2weeks', 0),
                reverse=(new_order == Qt.SortOrder.DescendingOrder)
            )
        
        # Update table with sorted data
        self._populate_table(sorted_games)
        
        # Update header to show sort indicator
        header = self.table.horizontalHeader()
        header.setSortIndicator(logical_index, new_order)

    async def _on_fetch(self) -> None:
        """
        Fetch and display user's game library from server.
        Handles SteamID resolution and data retrieval via server API.
        """
        raw = self.id_input.text().strip()
        if not raw:
            self.status.setText("Podaj identyfikator użytkownika.")
            return

        # Disable fetch button during loading
        self.fetch_btn.setEnabled(False)
        self.status.setText("Rozwiązywanie profilu...")
        self.table.setRowCount(0)
        self.persona_lbl.setText("Ładowanie...")
        self.avatar_lbl.clear()

        try:
            # Resolve Steam ID (handles SteamID64, vanity URLs, or full profile URLs)
            steamid = await self._resolve_steam_id(raw)

            if not steamid:
                self.status.setText("Nie udało się rozwiązać identyfikatora Steam. Sprawdź poprawność danych.")
                self.fetch_btn.setEnabled(True)
                return

            # Fetch player summary from server
            self.status.setText("Pobieranie profilu...")
            summary = await self._server_client.get_player_summary(steamid)
            
            # Fetch owned games from server
            self.status.setText("Pobieranie biblioteki...")
            owned_games = await self._server_client.get_owned_games(steamid)
            
            # Fetch recently played games from server
            recently_played = await self._server_client.get_recently_played(steamid)
            
        except Exception as e:
            logger.error(f"Error fetching library data: {e}")
            self.status.setText(f"Błąd: {e}")
            self.fetch_btn.setEnabled(True)
            return

        # Update profile header with user information
        if summary:
            self.persona_lbl.setText(summary.get('personaname', steamid))
            avatar_url = (
                summary.get('avatarfull') or 
                summary.get('avatarmedium') or 
                summary.get('avatar')
            )
            if avatar_url:
                await self._load_avatar(avatar_url)
        else:
            self.persona_lbl.setText("(brak danych profilu)")

        # Process playtime data
        recent_map = {}
        for game in recently_played:
            appid = game.get('appid')
            playtime_2weeks = game.get('playtime_2weeks', 0)
            if appid:
                recent_map[appid] = playtime_2weeks

        # Merge playtime data and store for sorting
        self._games_data = []
        for game in owned_games:
            appid = game.get('appid')
            total_min = game.get('playtime_forever', 0)
            last2w_min = recent_map.get(appid, game.get('playtime_2weeks', 0)) or 0
            
            # Fix inconsistency (last2w > total)
            if total_min < last2w_min:
                total_min = last2w_min
            
            self._games_data.append({
                'appid': appid,
                'name': game.get('name', f"AppID {appid or 'Unknown'}"),
                'playtime_forever': total_min,
                'playtime_2weeks': last2w_min
            })

        # Sort by total playtime (descending) by default
        sorted_games = sorted(
            self._games_data,
            key=lambda g: g.get('playtime_forever', 0),
            reverse=True
        )

        # Populate table with sorted data
        self._populate_table(sorted_games)
        
        # Set initial sort indicator on total hours column
        header = self.table.horizontalHeader()
        header.setSortIndicator(1, Qt.SortOrder.DescendingOrder)

        self.status.setText(f"Załadowano gier: {len(self._games_data)}")
        self.fetch_btn.setEnabled(True)

    def _populate_table(self, games_list: list) -> None:
        """
        Populate the table with game data.
        
        Args:
            games_list: List of game dictionaries with name, playtime_forever, playtime_2weeks
        """
        self.table.setRowCount(len(games_list))
        for row, game in enumerate(games_list):
            # Game name
            name = game.get('name', f"AppID {game.get('appid', 'Unknown')}")
            name_item = QTableWidgetItem(name)
            
            # Total playtime
            total_min = game.get('playtime_forever', 0)
            last2w_min = game.get('playtime_2weeks', 0)
            
            total_h = total_min / 60.0
            last2w_h = last2w_min / 60.0
            
            total_item = QTableWidgetItem(f"{total_h:.1f}")
            last_item = QTableWidgetItem(f"{last2w_h:.1f}")
            
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            last_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, total_item)
            self.table.setItem(row, 2, last_item)

    async def _resolve_steam_id(self, raw_input: str) -> Optional[str]:
        """
        Resolve various Steam ID formats to Steam ID64.

        Args:
            raw_input: Can be SteamID64, vanity name, or full profile URL

        Returns:
            Steam ID64 string if successful, None otherwise
        """
        # Check if it's already a valid Steam ID64 (17-digit number)
        if raw_input.isdigit() and len(raw_input) == 17:
            return raw_input

        # Try to resolve as vanity URL using server
        try:
            steamid = await self._server_client.resolve_vanity_url(raw_input)
            return steamid
        except Exception as e:
            logger.error(f"Error resolving Steam ID: {e}")
            return None

    async def _load_avatar(self, url: str) -> None:
        """
        Load and display user avatar image.
        
        Args:
            url: URL of the avatar image
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    pix = QPixmap()
                    pix.loadFromData(r.content)
                    self.avatar_lbl.setPixmap(pix)
        except Exception as e:
            logger.error(f"Error loading avatar: {e}")

