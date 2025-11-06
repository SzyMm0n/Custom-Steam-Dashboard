"""
User information dialog module for Custom Steam Dashboard (Server-Based).
Displays Steam user profile and game library information using server API.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QPixmap, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style

logger = logging.getLogger(__name__)
class SteamUserInfoDialog(QDialog):
    """
    Dialog for displaying Steam user information and game library.
    Fetches data from the backend server.
    Features:
    - Accepts SteamID64, vanity name, or full profile URL
    - Server handles API authentication
    - Displays user profile with avatar
    - Shows game library with playtime statistics
    - Polish locale support
    """
    def __init__(self, server_url: str = "http://localhost:8000", parent=None):
        """
        Initialize the Steam user info dialog.
        Args:
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)
        self._server_client = ServerClient(base_url=server_url)
        self.setWindowTitle("Informacje o użytkowniku Steam")
        self.setMinimumSize(800, 560)
        try:
            self.setLocale(QLocale(QLocale.Language.Polish, QLocale.Country.Poland))
        except Exception:
            pass
        self._init_ui()
    def _choose_polish_font(self) -> QFont:
        """Select a font that supports Polish characters."""
        candidates = ["Segoe UI", "Noto Sans", "DejaVu Sans", "Arial Unicode MS", "Arial"]
        available = set(QFontDatabase.families())
        for fam in candidates:
            if fam in available:
                return QFont(fam)
        return QFont()
    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        layout = QVBoxLayout(self)
        base_font = self._choose_polish_font()
        self.setFont(base_font)
        # Profile header
        prof = QHBoxLayout()
        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(64, 64)
        self.avatar_lbl.setScaledContents(True)
        prof.addWidget(self.avatar_lbl)
        self.persona_lbl = QLabel("Nieznany użytkownik")
        f = QFont(base_font)
        f.setPointSize(f.pointSize() + 2)
        f.setBold(True)
        self.persona_lbl.setFont(f)
        prof.addWidget(self.persona_lbl, 1)
        layout.addLayout(prof)
        # Input field
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("SteamID / URL / vanity:"))
        self.steamid_input = QLineEdit()
        self.steamid_input.setPlaceholderText("Wpisz SteamID64, vanity name lub URL profilu")
        row1.addWidget(self.steamid_input, 1)
        layout.addLayout(row1)
        # Buttons
        btns = QHBoxLayout()
        self.fetch_btn = QPushButton("Pobierz dane")
        self.fetch_btn.clicked.connect(lambda: asyncio.create_task(self._on_fetch_clicked()))
        btns.addWidget(self.fetch_btn)
        btns.addStretch(1)
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.reject)
        btns.addWidget(close_btn)
        layout.addLayout(btns)
        # Status
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)
        # Table
        self.table = QTableWidget(0, 3)
        self.table.setFont(base_font)
        header = self.table.horizontalHeader()
        header_font = QFont(base_font)
        header_font.setBold(True)
        header.setFont(header_font)
        self.table.setHorizontalHeaderLabels(["Nazwa gry", "Łączna liczba godzin", "Ostatnie 2 tygodnie (h)"])
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Apply common dark theme styling
        apply_style(self)

    async def _on_fetch_clicked(self) -> None:
        """Fetch user data from server API."""
        raw_input = self.steamid_input.text().strip()
        if not raw_input:
            QMessageBox.warning(self, "Brak SteamID", "Podaj SteamID64, vanity lub URL profilu.")
            return
        self.fetch_btn.setEnabled(False)
        self.status_lbl.setText("Rozwiązywanie identyfikatora...")
        self.persona_lbl.setText("Ładowanie...")
        self.avatar_lbl.clear()
        self.table.setRowCount(0)

        # Resolve Steam ID (handles SteamID64, vanity URLs, or full profile URLs)
        steamid = await self._resolve_steam_id(raw_input)

        if not steamid:
            self.status_lbl.setText("Nie udało się rozwiązać identyfikatora Steam. Sprawdź poprawność danych.")
            self.fetch_btn.setEnabled(True)
            return

        try:
            self.status_lbl.setText("Pobieranie profilu...")
            summary = await self._server_client.get_player_summary(steamid)
            self.status_lbl.setText("Pobieranie biblioteki...")
            owned_games = await self._server_client.get_owned_games(steamid)
            recently_played = await self._server_client.get_recently_played(steamid)
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            self.status_lbl.setText(f"Błąd: {e}\\n\\nUpewnij się, że serwer działa na {self._server_client.base_url}")
            self.fetch_btn.setEnabled(True)
            return
        # Update profile
        if summary:
            self.persona_lbl.setText(summary.get('personaname', steamid))
            avatar_url = summary.get('avatarfull') or summary.get('avatarmedium') or summary.get('avatar')
            if avatar_url:
                await self._load_avatar(avatar_url)
        else:
            self.persona_lbl.setText("(brak danych profilu)")
        # Process data
        recent_map = {g.get('appid'): g.get('playtime_2weeks', 0) for g in recently_played if g.get('appid')}
        owned_sorted = sorted(owned_games, key=lambda g: g.get('playtime_forever', 0), reverse=True)
        # Populate table
        self.table.setRowCount(len(owned_sorted))
        for row, game in enumerate(owned_sorted):
            name = game.get('name', f"AppID {game.get('appid', 'Unknown')}")
            name_item = QTableWidgetItem(name)
            name_item.setFont(self.font())
            total_min = game.get('playtime_forever', 0)
            last2w_min = recent_map.get(game.get('appid'), game.get('playtime_2weeks', 0)) or 0
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
        self.table.resizeColumnsToContents()
        self.status_lbl.setText(f"Załadowano gier: {len(owned_sorted)}")
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
        """Load and display user avatar image."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    pix = QPixmap()
                    pix.loadFromData(r.content)
                    self.avatar_lbl.setPixmap(pix)
        except Exception as e:
            logger.error(f"Error loading avatar: {e}")
