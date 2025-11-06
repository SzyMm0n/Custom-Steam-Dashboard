"""
Library view module for Custom Steam Dashboard (Server-Based).
Displays user's Steam game library with playtime statistics using server API.
"""
from __future__ import annotations

import asyncio
import logging
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

    def __init__(self, server_url: str = "http://localhost:8000", parent: Optional[QWidget] = None) -> None:
        """
        Initialize the library view.

        Args:
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)
        self._server_client = ServerClient(base_url=server_url)
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
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Apply common dark theme styling
        apply_style(self)
        title.setProperty("role", "title")

    # ===== Event Handlers =====

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

        # Sort games by total playtime
        owned_sorted = sorted(
            owned_games,
            key=lambda g: g.get('playtime_forever', 0),
            reverse=True
        )

        # Populate table with game data
        self.table.setRowCount(len(owned_sorted))
        for row, game in enumerate(owned_sorted):
            # Game name
            name = game.get('name', f"AppID {game.get('appid', 'Unknown')}")
            name_item = QTableWidgetItem(name)
            
            # Total playtime
            total_min = game.get('playtime_forever', 0)
            last2w_min = recent_map.get(game.get('appid'), game.get('playtime_2weeks', 0)) or 0
            
            # Fix inconsistency (last2w > total)
            if total_min < last2w_min:
                total_min = last2w_min
            
            total_h = total_min / 60.0
            last2w_h = last2w_min / 60.0
            
            total_item = QTableWidgetItem(f"{total_h:.1f}")
            last_item = QTableWidgetItem(f"{last2w_h:.1f}")
            
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            last_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, total_item)
            self.table.setItem(row, 2, last_item)

        self.status.setText(f"Załadowano gier: {len(owned_sorted)}")
        self.fetch_btn.setEnabled(True)

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

