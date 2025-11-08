"""
Home view module for Custom Steam Dashboard.
Displays current player counts, game filters, deals, and upcoming releases.
Fetches data from the backend server.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame,
    QHBoxLayout, QGroupBox, QSizePolicy,
    QSlider, QPushButton, QLineEdit, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import QTimer, Qt, QLocale

from app.core.services.server_client import ServerClient
from app.ui.components_server import NumberValidator, GameDetailDialog
from app.ui.styles import apply_style

# DealsApiClient optional - import if available
try:
    from app.core.services.deals_api import DealsApiClient
except Exception:
    DealsApiClient = None

logger = logging.getLogger(__name__)


# ===== Main Home View Widget =====

class HomeView(QWidget):
    """
    Main home view displaying live game statistics and deals.
    Fetches data from the backend server.

    Shows:
    - Live player counts for watched games from server
    - Filtering by player count and game tags
    - Best deals from game stores
    - Upcoming game releases from server
    """

    MAX_PLAYERS_SLIDER = 2000000  # Maximum value for player count slider

    def __init__(self, server_url: str = "http://localhost:8000", parent=None):
        """
        Initialize the home view.

        Args:
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)

        # Server client for data fetching
        self._server_client = ServerClient(base_url=server_url)
        self._server_url = server_url  # Store for passing to dialogs

        # Data storage
        self._all_games_data: List[Dict[str, Any]] = []
        
        # Filter state
        self._selected_tags: Set[str] = set()
        self._min_players: int = 0
        self._max_players: int = self.MAX_PLAYERS_SLIDER

        # UI components
        self.layout = QVBoxLayout(self)
        self.main_h_layout = QHBoxLayout()
        self._locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)

        # Initialize UI
        self._init_ui()

        # Setup automatic refresh timer (5 minutes)
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._timer.start(300000)

        # Load initial data
        QTimer.singleShot(0, self._start_initial_load)

    def _start_initial_load(self):
        """Start the initial data load asynchronously."""
        asyncio.create_task(self.refresh_data())

    # ===== UI Initialization =====

    def _init_ui(self):
        """
        Initialize the user interface layout.
        Creates left panel with game list and right panel with filters.
        """
        # Left column - Live games list
        left_column = QVBoxLayout()
        self.top_live_title = QLabel("Live Games Count")
        self.top_live_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.top_live_list = QListWidget()
        self.top_live_list.setMinimumWidth(500)
        self.top_live_list.itemClicked.connect(self._on_live_item_clicked)
        left_column.addWidget(self.top_live_title)
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
        self.main_h_layout.addLayout(left_column, 1)

        # Wrap right panel in scroll area
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel_widget)
        self.main_h_layout.addWidget(right_scroll, 0)

        # Apply common dark theme styling
        apply_style(self)
        self.top_live_title.setProperty("role", "section")

        # Additional content sections
        self._create_additional_sections()

    def _create_additional_sections(self):
        """Create additional sections for deals and upcoming releases."""
        # Separator before deals
        self.separator_1 = QFrame()
        self.separator_1.setFrameShape(QFrame.Shape.HLine)
        self.separator_1.setFrameShadow(QFrame.Shadow.Sunken)

        # Best Deals section
        self.trending_title = QLabel("Best Deals")
        self.trending_title.setProperty("role", "section")
        self.trending_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.trending_list = QListWidget()
        self.trending_list.setMinimumHeight(120)
        self.trending_list.setMaximumHeight(240)
        self.trending_list.itemClicked.connect(self._on_deal_item_clicked)

        # Separator before upcoming
        self.separator_2 = QFrame()
        self.separator_2.setFrameShape(QFrame.Shape.HLine)
        self.separator_2.setFrameShadow(QFrame.Shadow.Sunken)

        # Upcoming Releases section
        self.upcoming_title = QLabel("Best Upcoming Releases")
        self.upcoming_title.setProperty("role", "section")
        self.upcoming_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.upcoming_list = QListWidget()
        self.upcoming_list.setMinimumHeight(120)
        self.upcoming_list.setMaximumHeight(240)
        self.upcoming_list.itemClicked.connect(self._on_upcoming_item_clicked)

        # Add all sections to main layout
        self.layout.addLayout(self.main_h_layout)
        self.layout.addWidget(self.separator_1)
        self.layout.addWidget(self.trending_title)
        self.layout.addWidget(self.trending_list)
        self.layout.addWidget(self.separator_2)
        self.layout.addWidget(self.upcoming_title)
        self.layout.addWidget(self.upcoming_list)

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
        self._update_list_view()

    # ===== Formatting Utilities =====

    def _format_players(self, value: int) -> str:
        """Format player count with Polish locale thousands separator."""
        return self._locale.toString(float(value), 'f', 0)

    def _format_deal_price(self, value: Optional[float]) -> Optional[str]:
        """Format deal price in USD."""
        if value is None:
            return None
        try:
            v = float(value)
        except Exception:
            return None
        return f"${v:,.2f}"

    def _format_deal_line(self, title: str, sale: Optional[float], normal: Optional[float]) -> str:
        """Format deal information line with price and discount."""
        sale_str = self._format_deal_price(sale)
        normal_str = self._format_deal_price(normal)
        if sale_str and normal_str and (normal or 0) > 0:
            try:
                disc = int(round(100 - (float(sale) / float(normal)) * 100))
                if disc < 0:
                    disc = 0
            except Exception:
                disc = None
            if disc is not None and disc > 0:
                return f"{title} — {sale_str} (z {normal_str}, -{disc}%)"
            else:
                return f"{title} — {sale_str} (z {normal_str})"
        if sale_str:
            return f"{title} — {sale_str}"
        return title

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
        """Update the game list view based on current filters."""
        self.top_live_list.clear()
        filtered_results = []
        required_tags = self._selected_tags
        
        for item in self._all_games_data:
            game_tags: Set[str] = item.get("tags", set())
            players: int = item.get("players", 0)
            
            if players < self._min_players:
                continue
            if players > self._max_players:
                continue
            if required_tags and not required_tags.issubset(game_tags):
                continue
            filtered_results.append(item)
        
        filtered_results.sort(key=lambda x: x["players"], reverse=True)
        
        if not filtered_results:
            self.top_live_list.addItem("Brak gier pasujących do filtrowania.")
        else:
            for item in filtered_results:
                players_formatted = self._format_players(item["players"])
                lw_item = QListWidgetItem(f"{players_formatted} - {item['name']}")
                lw_item.setData(Qt.ItemDataRole.UserRole, item)
                self.top_live_list.addItem(lw_item)

    async def refresh_data(self):
        """
        Refresh all data from the server.
        
        Fetches:
        - Current player counts for watchlist games
        - Game tags (genres, categories)
        - Best deals from game stores
        - Upcoming game releases
        """
        # Update titles to show loading state
        self.top_live_title.setText("Live Games Count — Ładowanie...")
        self.trending_title.setText("Best Deals — Ładowanie...")
        self.upcoming_title.setText("Best Upcoming Releases — Ładowanie...")
        self.trending_list.clear()
        self.upcoming_list.clear()
        
        # Fetch watchlist games from server
        games = await self._server_client.get_current_players()
        
        if not games:
            self.top_live_title.setText("Live Games Count")
            if self.tags_list_widget.count() == 0:
                await self._populate_tag_checkboxes()
            self.trending_title.setText("Best Deals")
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
            tags_batch = await self._server_client.get_game_tags_batch(appids_to_fetch[:100]) # Nie więcej niż 100 na raz, inaczej serwer zwróci błąd
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
        
        # Fetch deals (still from DealsAPI)
        await self._fetch_deals()
        
        # Fetch upcoming games from server
        await self._fetch_upcoming()
        
        # Reset titles
        self.trending_title.setText("Best Deals")
        self.upcoming_title.setText("Best Upcoming Releases")

    async def _fetch_deals(self):
        """Fetch and display best deals."""
        deals = []
        if DealsApiClient is not None:
            try:
                async with DealsApiClient() as deals_client:
                    deals = await deals_client.get_current_deals(limit=10, min_discount=20)
            except Exception as e:
                logger.error(f"Error fetching deals: {e}")
                deals = []
        
        self.trending_list.clear()
        if not deals:
            self.trending_list.addItem("Brak aktualnych promocji.")
            return
        
        for d in deals:
            try:
                # Extract deal data
                if isinstance(d, dict):
                    sale = d.get('salePrice') or d.get('sale_price') or d.get('sale')
                    normal = d.get('normalPrice') or d.get('normal_price') or d.get('retailPrice')
                    title = d.get('title') or d.get('name') or d.get('gameName')
                    appid = d.get('steamAppID') or d.get('steam_app_id') or d.get('appID')
                    deal_id = d.get('dealID') or d.get('deal_id')
                    store_id = d.get('storeID') or d.get('store_id')
                    store_name = d.get('storeName') or d.get('store_name')
                    deal_url = d.get('storeURL') or d.get('dealURL') or d.get('url')
                else:
                    sale = getattr(d, 'salePrice', None) or getattr(d, 'sale_price', None)
                    normal = getattr(d, 'normalPrice', None) or getattr(d, 'normal_price', None)
                    title = getattr(d, 'title', None) or getattr(d, 'name', None)
                    appid = getattr(d, 'steamAppID', None) or getattr(d, 'steam_app_id', None)
                    deal_id = getattr(d, 'dealID', None) or getattr(d, 'deal_id', None)
                    store_id = getattr(d, 'storeID', None) or getattr(d, 'store_id', None)
                    store_name = getattr(d, 'storeName', None) or getattr(d, 'store_name', None)
                    deal_url = getattr(d, 'storeURL', None) or getattr(d, 'dealURL', None)
                
                if not deal_url and deal_id:
                    import urllib.parse
                    deal_url = f"https://www.cheapshark.com/redirect?dealID={urllib.parse.quote_plus(str(deal_id))}"
                
                if title is None:
                    title = str(d)
                
                try:
                    appid_int = int(appid) if appid is not None else None
                    if appid_int is not None and appid_int <= 0:
                        appid_int = None
                except Exception:
                    appid_int = None
                
                text = self._format_deal_line(title, sale, normal)
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "name": title,
                    "appid": appid_int,
                    "deal_url": deal_url,
                    "deal_id": deal_id,
                    "store_id": store_id,
                    "store_name": store_name,
                })
                self.trending_list.addItem(item)
            except Exception as e:
                logger.error(f"Error processing deal: {e}")
                self.trending_list.addItem(str(d))

    async def _fetch_upcoming(self):
        """Fetch and display upcoming releases from server."""
        try:
            upcoming = await self._server_client.get_coming_soon_games()
        except Exception as e:
            logger.error(f"Error fetching upcoming games: {e}")
            upcoming = []
        
        self.upcoming_list.clear()
        if not upcoming:
            self.upcoming_list.addItem("Brak nadchodzących premier.")
            return
        
        for item in upcoming:
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

    # ===== Event Handlers - Item Clicks =====

    def _on_live_item_clicked(self, item: QListWidgetItem):
        """Handle click on live games list item."""
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            data = None

        if isinstance(data, dict):
            dialog = GameDetailDialog(data, server_url=self._server_url, parent=self)
        else:
            dialog = GameDetailDialog(
                item.text() if item is not None else "Nieznana gra",
                server_url=self._server_url,
                parent=self
            )
        dialog.exec()

    def _on_deal_item_clicked(self, item: QListWidgetItem):
        """Handle click on deals list item."""
        if not item:
            return
        data = None
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        if isinstance(data, dict):
            GameDetailDialog(data, server_url=self._server_url, parent=self).exec()
        else:
            GameDetailDialog(item.text(), server_url=self._server_url, parent=self).exec()

    def _on_upcoming_item_clicked(self, item: QListWidgetItem):
        """Handle click on upcoming list item."""
        if not item:
            return
        data = None
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        if isinstance(data, dict):
            GameDetailDialog(data, server_url=self._server_url, parent=self).exec()
        else:
            GameDetailDialog(item.text(), server_url=self._server_url, parent=self).exec()

