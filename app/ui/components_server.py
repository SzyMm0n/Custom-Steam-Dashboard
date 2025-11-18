"""
UI components and helper widgets for Custom Steam Dashboard (Server-Based).
Contains reusable validators, dialogs, and UI utilities that fetch data from server.
"""
from typing import Optional, Any, Set
import asyncio
import logging
import urllib.parse

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QLocale, QRegularExpression, QUrl
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QLocale, QRegularExpression, QUrl, Signal
from PySide6.QtGui import QFont, QRegularExpressionValidator, QPixmap, QDesktopServices
import httpx

from app.config import get_server_url
from app.ui.styles import apply_style
from app.core.services.server_client import ServerClient
from app.ui.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


# ===== Input Validators =====

class NumberValidator(QRegularExpressionValidator):
    """
    Validator for numeric input fields with thousands separators.
    Allows digits and spaces, maximum 15 characters.
    """

    def __init__(self, parent=None):
        """
        Initialize the number validator.

        Args:
            parent: Parent widget
        """
        super().__init__(QRegularExpression(r"^[0-9 ]{0,15}$"), parent)


# ===== Game Detail Dialog (Server-Based) =====

class GameDetailDialog(QDialog):
    """
    Dialog displaying detailed information about a game.
    Fetches data from the backend server instead of direct API calls.
    
    Shows:
    - Game title and header image
    - Description from Steam
    - Player counts and tags from server
    - Store links
    """

    def __init__(
        self, 
        game_data: Any, 
        server_url: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the game detail dialog.

        Args:
            game_data: Either a string (game title) or dict with game information
                      (name, appid, players, tags, deal_url, deal_id, store_id, store_name)
            server_url: URL of the backend server (defaults to configured SERVER_URL)
            parent: Parent widget
        """
        super().__init__(parent)
        if server_url is None:
            server_url = get_server_url()
        self._server_client = ServerClient(base_url=server_url)
        self.setWindowTitle("Szczegóły gry")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        # Parse game data from dict or string
        self._parse_game_data(game_data)

        # Create UI elements
        self._create_title_section(layout)
        self._create_image_section(layout)
        self._create_details_section(layout)
        self._create_buttons_section(layout)

        # Apply common dark theme styling
        apply_style(self)

        # Load additional information asynchronously from server
        self._load_async_data()

    def _parse_game_data(self, game_data: Any) -> None:
        """
        Parse game data from various formats.

        Args:
            game_data: Game data as dict or string
        """
        if isinstance(game_data, dict):
            self._title = game_data.get("name", "Nieznana gra")
            self._appid = game_data.get("appid")
            self._players = game_data.get("players")
            self._tags = game_data.get("tags") or set()
            self._deal_url = game_data.get("deal_url")
            self._deal_id = game_data.get("deal_id")
            self._store_id = game_data.get("store_id")
            self._store_name = game_data.get("store_name")
        else:
            self._title = str(game_data)
            self._appid = None
            self._players = None
            self._tags = set()
            self._deal_url = None
            self._deal_id = None
            self._store_id = None
            self._store_name = None

    def _create_title_section(self, layout: QVBoxLayout) -> None:
        """
        Create the title section of the dialog.

        Args:
            layout: Parent layout
        """
        title_lbl = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        layout.addWidget(title_lbl)

    def _create_image_section(self, layout: QVBoxLayout) -> None:
        """
        Create the header image section.
        Create the header image and description section.

        Args:
            layout: Parent layout
        """
        # Create horizontal layout for image and description side by side
        content_layout = QHBoxLayout()
        
        # Left side - header image
        self.header_image_lbl = QLabel()
        self.header_image_lbl.setFixedHeight(120)
        self.header_image_lbl.setFixedSize(300, 140)  # Fixed size for consistent layout
        self.header_image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_image_lbl)
        self.header_image_lbl.setStyleSheet("border: 1px solid #555; background-color: #2b2b2b;")
        content_layout.addWidget(self.header_image_lbl)
        
        # Right side - description
        self.desc_lbl = QLabel("Ładowanie opisu...")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.desc_lbl.setMinimumWidth(300)
        content_layout.addWidget(self.desc_lbl, 1)  # Stretch factor 1 to take remaining space
        
        layout.addLayout(content_layout)

    def _create_details_section(self, layout: QVBoxLayout) -> None:
        """
        Create the details section showing player counts and tags.

        Args:
            layout: Parent layout
        """
        details_layout = QVBoxLayout()

        if self._appid is not None:
            # Display player count
            if self._players is not None:
                players_str = self._format_player_count(self._players)
                details_layout.addWidget(QLabel(f"Obecni gracze: {players_str}"))

            # Display tags
            if self._tags:
                tags_text = self._format_tags(self._tags)
                tags_lbl = QLabel(f"Tagi: {tags_text}")
                tags_lbl.setWordWrap(True)
                details_layout.addWidget(tags_lbl)
        else:
            details_layout.addWidget(QLabel("Brak dodatkowych danych."))

        layout.addLayout(details_layout)

    def _create_buttons_section(self, layout: QVBoxLayout) -> None:
        """
        Create the button section with store link and close buttons.

        Args:
            layout: Parent layout
        """
        btn_h = QHBoxLayout()

        # Store button
        self.store_btn = QPushButton("Przejdź do sklepu")
        self.store_btn.setEnabled(
            (self._appid is not None) or (self._deal_url is not None) or bool(self._title)
        )
        self.store_btn.clicked.connect(self._open_store_page)
        btn_h.addWidget(self.store_btn)

        btn_h.addStretch(1)

        # Close button
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        btn_h.addWidget(close_btn)

        layout.addLayout(btn_h)

    def _format_player_count(self, count: int) -> str:
        """
        Format player count with Polish locale thousands separator.

        Args:
            count: Player count

        Returns:
            Formatted string
        """
        try:
            return QLocale(QLocale.Language.Polish, QLocale.Country.Poland).toString(
                float(count), 'f', 0
            )
        except Exception:
            return str(count)

    def _format_tags(self, tags: Set[str]) -> str:
        """
        Format tags as comma-separated string.

        Args:
            tags: Set of tag strings

        Returns:
            Formatted string
        """
        if isinstance(tags, (set, list, tuple)):
            return ", ".join(sorted(list(tags)))
        return str(tags)

    def _load_async_data(self) -> None:
        """
        Load additional game data asynchronously from server.
        Attempts to fetch store details and tags from server.
        """
        try:
            if self._appid is not None:
                asyncio.create_task(self._load_from_server(self._appid))
            elif self._title and self._title != "Nieznana gra":
                asyncio.create_task(self._resolve_and_load_by_name(self._title))
        except Exception as e:
            logger.error(f"Error loading async data: {e}")

    def _make_cheapshark_search_url(self) -> Optional[QUrl]:
        """
        Construct CheapShark search URL for the game.

        Returns:
            QUrl for CheapShark search or None
        """
        try:
            if not self._title:
                return None
            q = urllib.parse.quote_plus(self._title)
            base = f"https://www.cheapshark.com/search#q={q}"
            
            # Add store filter if available
            if self._store_id is not None:
                try:
                    sid = int(self._store_id)
                    base += f"&storeID={sid}"
                except Exception:
                    pass
            return QUrl(base)
        except Exception:
            return None

    def _open_store_page(self) -> None:
        """
        Open the appropriate store page for the game.
        Priority: Best deal URL > Steam page > Fallback search
        """
        try:
            # 1) Prefer the best deal URL from IsThereAnyDeal (could be any store)
            if isinstance(self._deal_url, str) and self._deal_url.strip():
                QDesktopServices.openUrl(QUrl(self._deal_url))
                return

            # 2) Fallback to Steam app page when appid is known
            if self._appid:
                url = QUrl(f"https://store.steampowered.com/app/{int(self._appid)}/")
                QDesktopServices.openUrl(url)
                return

            # 3) If we have a deal id (legacy CheapShark), construct redirect
            if self._deal_id:
                redir = QUrl(
                    f"https://www.cheapshark.com/redirect?dealID={urllib.parse.quote_plus(str(self._deal_id))}"
                )
                QDesktopServices.openUrl(redir)
                return

            # 4) Fallback: Try Steam search by title
            if self._title and self._title != "Nieznana gra":
                search_url = QUrl(
                    f"https://store.steampowered.com/search/?term={urllib.parse.quote_plus(self._title)}"
                )
                QDesktopServices.openUrl(search_url)
        except Exception as e:
            logger.error(f"Error opening store page: {e}")

    async def _resolve_and_load_by_name(self, title: str) -> None:
        """
        Resolve Steam appid by searching for game title via Steam API.
        Still uses direct Steam API call as this is a simple search endpoint.

        Args:
            title: Game title to search for
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/storesearch",
                    params={"term": title, "cc": "pl", "l": "pl"},
                )
                data = resp.json() if resp.status_code == 200 else {}
                items = data.get("items") if isinstance(data, dict) else None
                
                if items and isinstance(items, list) and items:
                    first = items[0]
                    if isinstance(first, dict):
                        appid = first.get("id") or first.get("appid")
                        if appid:
                            try:
                                self._appid = int(appid)
                                self.store_btn.setEnabled(True)
                                await self._load_from_server(self._appid)
                            except Exception as e:
                                logger.error(f"Error resolving appid: {e}")
        except Exception as e:
            logger.error(f"Error searching for game: {e}")

    async def _load_from_server(self, appid: int) -> None:
        """
        Load game details and tags from server database.

        Args:
            appid: Steam application ID
        """
        try:
            # Fetch full game details from server database
            game_details = await self._server_client.get_game_details(appid)

            if game_details:
                # Update tags from database
                genres = game_details.get('genres', [])
                categories = game_details.get('categories', [])

                # Filter out None values that might come from SQL
                genres = [g for g in genres if g is not None]
                categories = [c for c in categories if c is not None]

                all_tags = genres + categories
                if all_tags:
                    self._tags = set(all_tags)
                    # Update tags display
                    tags_text = self._format_tags(self._tags)
                    self._update_tags_label(f"Tagi: {tags_text}")

                # Update description from database
                description = game_details.get('detailed_description')
                if description:
                    self.desc_lbl.setText(description)
                else:
                    # Fallback to Steam API if no description in database
                    await self._load_steam_store_details(appid)

                # Load header image from database
                header_image_url = game_details.get('header_image')
                if header_image_url:
                    await self._load_image_from_url(header_image_url)
                else:
                    # Fallback to Steam API if no image in database
                    await self._load_steam_store_details(appid)

                # Display additional info if available
                price = game_details.get('price')
                is_free = game_details.get('is_free')
                release_date = game_details.get('release_date')

                # Add price info to details section if available
                if is_free:
                    self._add_detail_label("Cena: Darmowa")
                elif price is not None:
                    self._add_detail_label(f"Cena: {price} PLN")

                if release_date:
                    self._add_detail_label(f"Data wydania: {release_date}")
            else:
                # Game not in database, fallback to Steam API
                logger.info(f"Game {appid} not in database, fetching from Steam API")
                await self._load_steam_store_details(appid)

                # Still try to get tags from server
                tags_data = await self._server_client.get_game_tags(appid)
                if tags_data:
                    server_tags = tags_data.get('tags', [])
                    if server_tags:
                        self._tags = set(server_tags)
                        tags_text = self._format_tags(self._tags)
                        self._update_tags_label(f"Tagi: {tags_text}")

        except Exception as e:
            logger.error(f"Error fetching from server: {e}")
            # Fallback to Steam API on error
            await self._load_steam_store_details(appid)

    def _update_tags_label(self, text: str) -> None:
        """
        Update the tags label in the dialog.

        Args:
            text: New text for tags label
        """
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QLabel) and widget.text().startswith("Tagi:"):
                        widget.setText(text)
                        return

    def _add_detail_label(self, text: str) -> None:
        """
        Add a detail label to the details section.

        Args:
            text: Label text to add
        """
        # Find the details layout and add label
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.layout():
                # Check if this is the details layout (contains "Obecni gracze" or "Tagi")
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QLabel) and (
                        widget.text().startswith("Obecni gracze:") or
                        widget.text().startswith("Tagi:")
                    ):
                        # Found the details layout, add new label
                        item.layout().addWidget(QLabel(text))
                        return

    async def _load_image_from_url(self, image_url: str) -> None:
        """
        Load and display image from URL.

        Args:
            image_url: URL of the image to load
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                img_resp = await client.get(image_url, timeout=10.0)
                if img_resp.status_code == 200:
                    pix = QPixmap()
                    pix.loadFromData(img_resp.content)
                    scaled = pix.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
                    # Scale to fit the fixed size while maintaining aspect ratio
                    scaled = pix.scaled(
                        300, 140,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.header_image_lbl.setPixmap(scaled)
        except Exception as e:
            logger.error(f"Error loading image from URL: {e}")

    async def _load_steam_store_details(self, appid: int) -> None:
        """
        Load store details from Steam API (fallback method).
        Used when game details are not available in server database.

        Args:
            appid: Steam application ID
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/appdetails",
                    params={"appids": appid, "cc": "pl", "l": "pl"},
                )

                if resp.status_code != 200:
                    self.desc_lbl.setText("Nie udało się załadować opisu gry.")
                    return

                data = resp.json()
                node = data.get(str(appid)) if isinstance(data, dict) else None
                
                if node and node.get("success"):
                    d = node.get("data", {}) or {}
                    header_image = (
                        d.get("header_image")
                        or d.get("capsule_image")
                        or d.get("capsule_image_full")
                    )
                    short_desc = d.get("short_description") or d.get("about_the_game") or ""
                    
                    # Update description
                    if short_desc:
                        self.desc_lbl.setText(short_desc)
                    else:
                        self.desc_lbl.setText("Brak opisu gry.")

                    # Load and display header image
                    if header_image:
                        await self._load_header_image(client, header_image)
                else:
                    self.desc_lbl.setText("Nie udało się pobrać informacji o grze ze Steam.")
        except Exception as e:
            logger.error(f"Error loading Steam store details: {e}")
            self.desc_lbl.setText("Błąd podczas ładowania opisu gry.")

    async def _load_header_image(self, client: httpx.AsyncClient, image_url: str) -> None:
        """
        Load and display the game's header image.

        Args:
            client: HTTP client instance
            image_url: URL of the header image
        """
        try:
            img_resp = await client.get(image_url, timeout=10.0)
            if img_resp.status_code == 200:
                pix = QPixmap()
                pix.loadFromData(img_resp.content)
                # Scale to fit the fixed size while maintaining aspect ratio
                scaled = pix.scaled(
                    300, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.header_image_lbl.setPixmap(scaled)
        except Exception as e:
            logger.error(f"Error loading header image: {e}")


# ===== Game Detail Panel (Inline Display) =====

class GameDetailPanel(QFrame):
    """
    Panel displaying detailed information about a game (inline, not dialog).
    Can be embedded in the main view as a temporary section.
    
    Shows:
    - Game title and header image
    - Description from Steam
    - Player counts and tags from server
    - Store links
    
    Signals:
    - closed: Emitted when user closes the panel
    """
    
    closed = Signal()  # Signal emitted when panel is closed
    
    def __init__(
        self,
        game_data: Any,
        server_url: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the game detail panel.
        
        Args:
            game_data: Either a string (game title) or dict with game information
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)
        if server_url is None:
            server_url = get_server_url()
        self._server_client = ServerClient(base_url=server_url)
        
        # Theme manager
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

        # Parse game data
        self._parse_game_data(game_data)
        
        # Setup frame style (theme-aware)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        # We'll apply theme below after building key widgets

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create UI elements
        self._create_header_section(layout)
        self._create_content_section(layout)
        self._create_details_section(layout)
        self._create_buttons_section(layout)
        
        # Apply theme-aware styling now that widgets exist
        self._apply_theme()

        # Load async data
        self._load_async_data()
    
    def _is_valid(self) -> bool:
        """Check if the panel and its widgets are still valid (not deleted)."""
        try:
            # Try to access a basic property to verify object is alive
            _ = self.isVisible()
            # Also check key widgets
            if hasattr(self, 'desc_lbl'):
                _ = self.desc_lbl.text()
            if hasattr(self, 'details_layout'):
                _ = self.details_layout.count()
            return True
        except RuntimeError:
            # C++ object has been deleted
            return False

    def _parse_game_data(self, game_data: Any) -> None:
        """Parse game data from various formats."""
        if isinstance(game_data, dict):
            self._title = game_data.get("name", "Nieznana gra")
            self._appid = game_data.get("appid")
            self._players = game_data.get("players")
            self._tags = game_data.get("tags") or set()
            self._deal_url = game_data.get("deal_url")
            self._deal_id = game_data.get("deal_id")
            self._store_id = game_data.get("store_id")
            self._store_name = game_data.get("store_name")
        else:
            self._title = str(game_data)
            self._appid = None
            self._players = None
            self._tags = set()
            self._deal_url = None
            self._deal_id = None
            self._store_id = None
            self._store_name = None
    
    def _create_header_section(self, layout: QVBoxLayout) -> None:
        """Create the header with title and close button."""
        header_layout = QHBoxLayout()
        
        # Title
        title_lbl = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        header_layout.addWidget(title_lbl, 1)
        
        # Close button
        self._close_btn = QPushButton("✕")
        self._close_btn.setMaximumSize(32, 32)
        self._close_btn.setMinimumSize(32, 32)
        self._close_btn.setToolTip("Zamknij panel")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(self._close_btn)

        layout.addLayout(header_layout)
        
        # Separator
        self._separator = QFrame()
        self._separator.setFrameShape(QFrame.Shape.HLine)
        self._separator.setFixedHeight(2)
        layout.addWidget(self._separator)

    def _create_content_section(self, layout: QVBoxLayout) -> None:
        """Create the content section with image and description."""
        content_layout = QHBoxLayout()
        
        # Left side - header image
        self.header_image_lbl = QLabel()
        self.header_image_lbl.setFixedSize(300, 140)
        self.header_image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.header_image_lbl)
        
        # Right side - description (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.desc_lbl = QLabel("Ładowanie opisu...")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.desc_lbl)
        
        content_layout.addWidget(scroll, 1)
        
        layout.addLayout(content_layout)
    
    def _create_details_section(self, layout: QVBoxLayout) -> None:
        """Create the details section."""
        self.details_layout = QVBoxLayout()
        
        if self._appid is not None:
            if self._players is not None:
                players_str = self._format_player_count(self._players)
                self.details_layout.addWidget(QLabel(f"🎮 Obecni gracze: {players_str}"))
            
            if self._tags:
                tags_text = self._format_tags(self._tags)
                tags_lbl = QLabel(f"🏷️ Tagi: {tags_text}")
                tags_lbl.setWordWrap(True)
                self.details_layout.addWidget(tags_lbl)
        else:
            self.details_layout.addWidget(QLabel("Brak dodatkowych danych."))
        
        layout.addLayout(self.details_layout)
    
    def _create_buttons_section(self, layout: QVBoxLayout) -> None:
        """Create the buttons section."""
        btn_layout = QHBoxLayout()
        
        # Store button
        self.store_btn = QPushButton("🛒 Przejdź do sklepu")
        self.store_btn.setEnabled(
            (self._appid is not None) or (self._deal_url is not None) or bool(self._title)
        )
        self.store_btn.clicked.connect(self._open_store_page)
        btn_layout.addWidget(self.store_btn)
        
        btn_layout.addStretch(1)
        
        layout.addLayout(btn_layout)
    
    def _format_player_count(self, count: int) -> str:
        """Format player count with Polish locale."""
        try:
            return QLocale(QLocale.Language.Polish, QLocale.Country.Poland).toString(
                float(count), 'f', 0
            )
        except Exception:
            return str(count)
    
    def _format_tags(self, tags: Set[str]) -> str:
        """Format tags as comma-separated string."""
        if isinstance(tags, (set, list, tuple)):
            return ", ".join(sorted(list(tags)))
        return str(tags)
    
    def _on_close(self) -> None:
        """Handle close button click."""
        self.closed.emit()
        self.setVisible(False)
        self.deleteLater()
    
    def _load_async_data(self) -> None:
        """Load additional game data asynchronously."""
        try:
            if self._appid is not None:
                asyncio.create_task(self._load_from_server(self._appid))
            elif self._title and self._title != "Nieznana gra":
                asyncio.create_task(self._resolve_and_load_by_name(self._title))
        except Exception as e:
            logger.error(f"Error loading async data: {e}")
    
    async def _resolve_and_load_by_name(self, title: str) -> None:
        """Resolve Steam appid by title."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/storesearch",
                    params={"term": title, "cc": "pl", "l": "pl"},
                )
                data = resp.json() if resp.status_code == 200 else {}
                items = data.get("items") if isinstance(data, dict) else None
                
                if items and isinstance(items, list) and items:
                    first = items[0]
                    if isinstance(first, dict):
                        appid = first.get("id") or first.get("appid")
                        if appid:
                            try:
                                self._appid = int(appid)
                                self.store_btn.setEnabled(True)
                                await self._load_from_server(self._appid)
                            except Exception as e:
                                logger.error(f"Error resolving appid: {e}")
        except Exception as e:
            logger.error(f"Error searching for game: {e}")
    
    async def _load_from_server(self, appid: int) -> None:
        """Load game details from server."""
        try:
            # Check if panel is still valid before proceeding
            if not self._is_valid():
                return

            game_details = await self._server_client.get_game_details(appid)
            
            if not self._is_valid():
                return

            if game_details:
                # Update tags
                genres = [g for g in game_details.get('genres', []) if g is not None]
                categories = [c for c in game_details.get('categories', []) if c is not None]
                all_tags = genres + categories
                
                if all_tags and self._is_valid():
                    self._tags = set(all_tags)
                    tags_text = self._format_tags(self._tags)
                    self._update_tags_label(f"🏷️ Tagi: {tags_text}")
                
                # Update description
                if not self._is_valid():
                    return

                description = game_details.get('detailed_description')
                if description:
                    if self._is_valid():
                        self.desc_lbl.setText(description)
                else:
                    await self._load_steam_store_details(appid)
                
                # Load image
                if not self._is_valid():
                    return

                header_image_url = game_details.get('header_image')
                if header_image_url:
                    await self._load_image_from_url(header_image_url)
                else:
                    await self._load_steam_store_details(appid)
                
                # Add price info
                if not self._is_valid():
                    return

                price = game_details.get('price')
                is_free = game_details.get('is_free')
                release_date = game_details.get('release_date')
                
                if is_free:
                    self._add_detail_label("💰 Cena: Darmowa")
                elif price is not None:
                    self._add_detail_label(f"💰 Cena: {price} PLN")
                
                if release_date:
                    self._add_detail_label(f"📅 Data wydania: {release_date}")
            else:
                await self._load_steam_store_details(appid)
                
                if not self._is_valid():
                    return

                tags_data = await self._server_client.get_game_tags(appid)
                if tags_data and self._is_valid():
                    server_tags = tags_data.get('tags', [])
                    if server_tags:
                        self._tags = set(server_tags)
                        tags_text = self._format_tags(self._tags)
                        self._update_tags_label(f"🏷️ Tagi: {tags_text}")
        except RuntimeError as e:
            # Qt object already deleted
            logger.debug(f"Panel closed during async operation: {e}")
        except Exception as e:
            logger.error(f"Error fetching from server: {e}")
            if self._is_valid():
                await self._load_steam_store_details(appid)

    def _update_tags_label(self, text: str) -> None:
        """Update tags label."""
        if not self._is_valid():
            return

        try:
            for i in range(self.details_layout.count()):
                widget = self.details_layout.itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text().startswith("🏷️ Tagi:"):
                    widget.setText(text)
                    return
        except RuntimeError:
            # Layout or widget already deleted
            pass

    def _add_detail_label(self, text: str) -> None:
        """Add a detail label."""
        if not self._is_valid():
            return
        try:
            self.details_layout.addWidget(QLabel(text))
        except RuntimeError:
            pass

    async def _load_image_from_url(self, image_url: str) -> None:
        """Load image from URL."""
        try:
            if not self._is_valid():
                return

            async with httpx.AsyncClient(timeout=10.0) as client:
                img_resp = await client.get(image_url, timeout=10.0)

                if not self._is_valid():
                    return

                if img_resp.status_code == 200:
                    pix = QPixmap()
                    pix.loadFromData(img_resp.content)
                    scaled = pix.scaled(
                        300, 140,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    if self._is_valid():
                        self.header_image_lbl.setPixmap(scaled)
        except RuntimeError:
            # Qt object already deleted
            pass
        except Exception as e:
            logger.error(f"Error loading image from URL: {e}")
    
    async def _load_steam_store_details(self, appid: int) -> None:
        """Load details from Steam API (fallback)."""
        try:
            if not self._is_valid():
                return

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/appdetails",
                    params={"appids": appid, "cc": "pl", "l": "pl"},
                )
                
                if not self._is_valid():
                    return

                if resp.status_code != 200:
                    if self._is_valid():
                        self.desc_lbl.setText("Nie udało się załadować opisu gry.")
                    return
                
                data = resp.json()
                node = data.get(str(appid)) if isinstance(data, dict) else None
                
                if not self._is_valid():
                    return

                if node and node.get("success"):
                    d = node.get("data", {}) or {}
                    header_image = (
                        d.get("header_image")
                        or d.get("capsule_image")
                        or d.get("capsule_image_full")
                    )
                    short_desc = d.get("short_description") or d.get("about_the_game") or ""
                    
                    if self._is_valid():
                        if short_desc:
                            self.desc_lbl.setText(short_desc)
                        else:
                            self.desc_lbl.setText("Brak opisu gry.")

                    if header_image and self._is_valid():
                        await self._load_header_image(client, header_image)
                else:
                    if self._is_valid():
                        self.desc_lbl.setText("Nie udało się pobrać informacji o grze ze Steam.")
        except RuntimeError:
            # Qt object already deleted
            pass
        except Exception as e:
            logger.error(f"Error loading Steam store details: {e}")
            if self._is_valid():
                self.desc_lbl.setText("Błąd podczas ładowania opisu gry.")

    async def _load_header_image(self, client: httpx.AsyncClient, image_url: str) -> None:
        """Load header image."""
        try:
            img_resp = await client.get(image_url, timeout=10.0)
            if img_resp.status_code == 200:
                pix = QPixmap()
                pix.loadFromData(img_resp.content)
                scaled = pix.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
                scaled = pix.scaled(
                    300, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.header_image_lbl.setPixmap(scaled)
        except Exception as e:
            logger.error(f"Error loading header image: {e}")
    
    def _open_store_page(self) -> None:
        """Open store page."""
        try:
            if isinstance(self._deal_url, str) and self._deal_url.strip():
                QDesktopServices.openUrl(QUrl(self._deal_url))
                return
            
            if self._appid:
                url = QUrl(f"https://store.steampowered.com/app/{int(self._appid)}/")
                QDesktopServices.openUrl(url)
                return
            
            if self._deal_id:
                redir = QUrl(
                    f"https://www.cheapshark.com/redirect?dealID={urllib.parse.quote_plus(str(self._deal_id))}"
                )
                QDesktopServices.openUrl(redir)
                return
            
            if self._title and self._title != "Nieznana gra":
                search_url = QUrl(
                    f"https://store.steampowered.com/search/?term={urllib.parse.quote_plus(self._title)}"
                )
                QDesktopServices.openUrl(search_url)
        except Exception as e:
            logger.error(f"Error opening store page: {e}")

    def _apply_theme(self) -> None:
        """Apply theme-aware styles to the panel and its key widgets."""
        colors = self._theme_manager.get_colors()
        # Panel background and border using group colors
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['background_group']};
                border: 2px solid {colors['border_group']};
                border-radius: 8px;
            }}
            """
        )
        # Separator and header image border/background
        self._separator.setStyleSheet(f"background-color: {colors['border_group']};")
        self.header_image_lbl.setStyleSheet(
            f"border: 1px solid {colors['border']}; background-color: {colors['background_panel']};"
        )
        # Close button uses danger palette
        self._close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['danger_pressed']};
            }}
            """
        )

    def _on_theme_changed(self, mode: str, palette: str) -> None:
        """Reapply theme styles when the app theme changes."""
        self._apply_theme()
