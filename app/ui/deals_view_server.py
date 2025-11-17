"""Deals view module for Custom Steam Dashboard.
Displays best game deals and allows searching for specific games.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLineEdit,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style

logger = logging.getLogger(__name__)


class DealsView(QWidget):
    """
    Deals view for browsing game promotions and deals.
    
    Features:
    - List of best current deals from multiple stores
    - Search for deals by game title
    - Display discount percentages and prices
    - Filter by minimum discount
    """
    
    def __init__(self, server_url: Optional[str] = None, parent=None):
        """
        Initialize the deals view.
        
        Args:
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._server_client = ServerClient(server_url)
        self._best_deals = []
        self._search_results = None
        
        self._init_ui()
        
        # Auto-refresh timer (every 10 minutes for deals)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._refresh_timer.start(600000)  # 10 minutes
        
        # Initial data load
        asyncio.create_task(self._load_initial_data())
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Promocje i okazje")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Search section
        search_group = self._create_search_section()
        layout.addWidget(search_group)
        
        # Main content area with two columns
        content_layout = QHBoxLayout()
        
        # Left column - Best deals
        best_deals_group = self._create_best_deals_section()
        content_layout.addWidget(best_deals_group, stretch=1)
        
        # Right column - Search results
        search_results_group = self._create_search_results_section()
        content_layout.addWidget(search_results_group, stretch=1)
        
        layout.addLayout(content_layout)
        
        apply_style(self)
    
    def _create_search_section(self) -> QWidget:
        """Create search bar section."""
        search_group = QGroupBox("Wyszukaj promocje")
        search_layout = QVBoxLayout()
        
        # Search input and button
        input_layout = QHBoxLayout()
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Wpisz tytuł gry...")
        self._search_input.returnPressed.connect(lambda: asyncio.create_task(self._search_deals()))
        input_layout.addWidget(self._search_input)
        
        self._search_btn = QPushButton("Szukaj")
        self._search_btn.clicked.connect(lambda: asyncio.create_task(self._search_deals()))
        input_layout.addWidget(self._search_btn)
        
        search_layout.addLayout(input_layout)
        search_group.setLayout(search_layout)
        
        return search_group
    
    def _create_best_deals_section(self) -> QWidget:
        """Create best deals list section."""
        group = QGroupBox("Najlepsze okazje")
        layout = QVBoxLayout()
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self._refresh_best_btn = QPushButton("Odśwież")
        self._refresh_best_btn.clicked.connect(lambda: asyncio.create_task(self._load_best_deals()))
        controls_layout.addWidget(self._refresh_best_btn)
        
        controls_layout.addStretch()
        
        self._min_discount_label = QLabel("Min. zniżka: 20%")
        controls_layout.addWidget(self._min_discount_label)
        
        layout.addLayout(controls_layout)
        
        # Deals list
        self._best_deals_list = QListWidget()
        self._best_deals_list.setWordWrap(True)
        # Connect click event to open store URL
        self._best_deals_list.itemClicked.connect(self._on_deal_clicked)
        layout.addWidget(self._best_deals_list)
        
        # Status label
        self._best_deals_status = QLabel("Ładowanie...")
        self._best_deals_status.setStyleSheet("color: gray; font-style: italic;")
        self._best_deals_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._best_deals_status)
        
        group.setLayout(layout)
        return group
    
    def _create_search_results_section(self) -> QWidget:
        """Create search results section."""
        group = QGroupBox("Wyniki wyszukiwania")
        layout = QVBoxLayout()
        
        # Results display
        self._search_results_widget = QWidget()
        self._search_results_layout = QVBoxLayout(self._search_results_widget)
        
        # Initial message
        self._search_status_label = QLabel("Wpisz tytuł gry i kliknij 'Szukaj'")
        self._search_status_label.setStyleSheet("color: gray; font-style: italic;")
        self._search_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._search_results_layout.addWidget(self._search_status_label)
        
        layout.addWidget(self._search_results_widget)
        
        group.setLayout(layout)
        return group
    
    async def _load_initial_data(self):
        """Load initial data (best deals)."""
        try:
            # Authenticate first
            auth_success = await self._server_client.authenticate()
            if not auth_success:
                logger.error("DealsView: Failed to authenticate with server")
                self._best_deals_status.setText("❌ Błąd uwierzytelniania")
                return
            
            await self._load_best_deals()
        except Exception as e:
            logger.error(f"DealsView: Error loading initial data: {e}")
            self._best_deals_status.setText("❌ Błąd ładowania danych")
    
    async def _load_best_deals(self):
        """Load best deals from server."""
        try:
            self._best_deals_status.setText("Ładowanie...")
            self._refresh_best_btn.setEnabled(False)
            
            deals = await self._server_client.get_best_deals(limit=30, min_discount=20)
            self._best_deals = deals
            
            self._update_best_deals_list()
            
            if deals:
                self._best_deals_status.setText(f"Znaleziono {len(deals)} promocji")
            else:
                self._best_deals_status.setText("Brak aktywnych promocji")
            
        except Exception as e:
            logger.error(f"DealsView: Error loading best deals: {e}")
            self._best_deals_status.setText("❌ Błąd ładowania promocji")
        finally:
            self._refresh_best_btn.setEnabled(True)
    
    def _update_best_deals_list(self):
        """Update the best deals list widget."""
        self._best_deals_list.clear()
        
        for deal in self._best_deals:
            # Create deal item text - using correct API field names
            game_name = deal.get("game_title", "Unknown Game")
            discount = deal.get("discount_percent", 0)
            price_new = deal.get("current_price", 0)
            price_old = deal.get("regular_price", 0)
            store = deal.get("store_name", "Unknown Store")
            currency = deal.get("currency", "USD")
            store_url = deal.get("store_url", "")
            
            # Format item text
            item_text = f"🎮 {game_name}\n"
            item_text += f"💰 -{discount}% | "
            
            if price_new and price_old:
                item_text += f"{price_new:.2f} {currency} (było: {price_old:.2f} {currency})\n"
            elif price_new:
                item_text += f"{price_new:.2f} {currency}\n"
            else:
                item_text += "Cena niedostępna\n"
            
            item_text += f"🏪 {store}"
            
            if store_url:
                item_text += " 🔗 (kliknij aby otworzyć)"
            
            item = QListWidgetItem(item_text)
            
            # Store the URL in the item's data for later retrieval
            item.setData(Qt.ItemDataRole.UserRole, store_url)
            
            # Make item look clickable
            if store_url:
                item.setToolTip(f"Kliknij aby otworzyć ofertę w sklepie: {store}")
            
            # Color based on discount
            if discount >= 75:
                item.setBackground(Qt.GlobalColor.darkGreen)
            elif discount >= 50:
                item.setBackground(Qt.GlobalColor.darkBlue)
            elif discount >= 25:
                item.setBackground(Qt.GlobalColor.darkCyan)
            
            self._best_deals_list.addItem(item)
    
    def _on_deal_clicked(self, item: QListWidgetItem):
        """Handle clicking on a deal item to open store URL."""
        # Retrieve the store URL from item data
        store_url = item.data(Qt.ItemDataRole.UserRole)
        
        if store_url:
            # Open URL in default browser
            QDesktopServices.openUrl(QUrl(store_url))
            logger.info(f"Opening deal URL: {store_url}")
        else:
            logger.warning("No store URL available for this deal")
    
    async def _search_deals(self):
        """Search for deals by game title."""
        search_term = self._search_input.text().strip()
        
        if not search_term or len(search_term) < 2:
            self._search_status_label.setText("⚠️ Wpisz przynajmniej 2 znaki")
            return
        
        try:
            self._search_status_label.setText(f"Szukam: {search_term}...")
            self._search_btn.setEnabled(False)
            
            result = await self._server_client.search_game_deals(search_term)
            
            if not result:
                self._search_status_label.setText("❌ Błąd wyszukiwania")
                return
            
            self._display_search_result(result)
            
        except Exception as e:
            logger.error(f"DealsView: Error searching deals: {e}")
            self._search_status_label.setText("❌ Błąd wyszukiwania")
        finally:
            self._search_btn.setEnabled(True)
    
    def _display_search_result(self, result: Dict[str, Any]):
        """Display search result in the results panel."""
        # Clear previous results
        while self._search_results_layout.count():
            child = self._search_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not result.get("found"):
            # Not found
            self._search_status_label = QLabel("❌ Nie znaleziono gry")
            self._search_status_label.setStyleSheet("color: orange; font-weight: bold;")
            self._search_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._search_results_layout.addWidget(self._search_status_label)
            return
        
        # Found - display game and deal info
        game = result.get("game", {})
        deal = result.get("deal")
        
        # Game title
        title_label = QLabel(f"🎮 {game.get('title', 'Unknown')}")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 5px;")
        title_label.setWordWrap(True)
        self._search_results_layout.addWidget(title_label)
        
        # Steam AppID if available
        if game.get("steam_appid"):
            appid_label = QLabel(f"Steam AppID: {game['steam_appid']}")
            appid_label.setStyleSheet("color: gray; margin-left: 10px;")
            self._search_results_layout.addWidget(appid_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._search_results_layout.addWidget(line)
        
        # Deal information
        if deal:
            deal_widget = self._create_deal_widget(deal)
            self._search_results_layout.addWidget(deal_widget)
        else:
            no_deal_label = QLabel("ℹ️ Brak aktywnych promocji dla tej gry")
            no_deal_label.setStyleSheet("color: gray; font-style: italic; margin: 10px;")
            self._search_results_layout.addWidget(no_deal_label)
        
        self._search_results_layout.addStretch()
    
    def _create_deal_widget(self, deal: Dict[str, Any]) -> QWidget:
        """Create a widget displaying deal information."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Deal header - using correct API field names
        if deal.get("discount_percent", 0) > 0:
            discount = deal["discount_percent"]
            header = QLabel(f"🎉 Promocja: -{discount}%")
            header.setStyleSheet("font-size: 12pt; font-weight: bold; color: green;")
        else:
            header = QLabel("💵 Aktualna cena")
            header.setStyleSheet("font-size: 12pt; font-weight: bold;")
        
        layout.addWidget(header)
        
        # Price information - using correct API field names
        price_new = deal.get("current_price")
        price_old = deal.get("regular_price")
        currency = deal.get("currency", "USD")
        
        if price_new is not None:
            if price_old and price_old > price_new:
                price_text = f"Cena: {price_new:.2f} {currency} (było: {price_old:.2f} {currency})"
            else:
                price_text = f"Cena: {price_new:.2f} {currency}"
            
            price_label = QLabel(price_text)
            price_label.setStyleSheet("font-size: 11pt; margin: 5px;")
            layout.addWidget(price_label)
        
        # Store information - using correct API field name
        store = deal.get("store_name", "Unknown")
        store_label = QLabel(f"🏪 Sklep: {store}")
        store_label.setStyleSheet("margin: 5px;")
        layout.addWidget(store_label)
        
        # URL if available - using correct API field name
        if deal.get("store_url"):
            url_label = QLabel(f"🔗 <a href='{deal['store_url']}'>Przejdź do oferty</a>")
            url_label.setOpenExternalLinks(True)
            url_label.setStyleSheet("margin: 5px;")
            layout.addWidget(url_label)
        
        widget.setStyleSheet("background-color: #2a2a2a; border-radius: 5px; margin: 5px;")
        
        return widget
    
    async def refresh_data(self):
        """Refresh all data (best deals)."""
        await self._load_best_deals()

