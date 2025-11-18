"""Deals view module for Custom Steam Dashboard.
Displays best game deals and allows searching for specific games.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLineEdit,
    QFrame, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style, refresh_style
from app.ui.theme_manager import ThemeManager

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
        self._all_best_deals = []  # Store all deals for frontend filtering
        self._search_results = None
        
        # Pagination state for best deals
        self._page_size = 100
        self._current_page = 1
        self._total_pages = 1

        # Filters state
        self._filters = {
            'min_discount': 0,
            'min_price': 0.0,
            'shops': [61, 35, 88, 82],  # All shops by default
            'mature': False,
            'sort': '-cut'
        }

        # Store current search state for theme refresh
        self._current_search_result = None
        self._current_search_term = None
        self._current_search_min_discount = 0

        # Theme manager - connect BEFORE init_ui to ensure proper initial styling
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

        self._init_ui()
        
        # Auto-refresh timer (every 10 minutes for deals)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._refresh_timer.start(600000)  # 10 minutes
        
        # Initial data load
        asyncio.create_task(self._load_initial_data())

        # Force apply current theme state immediately after UI is built
        self._on_theme_changed(self._theme_manager.mode.value, self._theme_manager.palette.value)

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Promocje i okazje")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Main content area with two columns
        content_layout = QHBoxLayout()
        
        # Left column - Best deals with filters
        best_deals_group = self._create_best_deals_section()
        content_layout.addWidget(best_deals_group, stretch=1)
        
        # Right column - Search results
        search_results_group = self._create_search_results_section()
        content_layout.addWidget(search_results_group, stretch=1)
        
        layout.addLayout(content_layout)
        
        apply_style(self)
    
    def _create_best_deals_section(self) -> QWidget:
        """Create best deals list section."""
        group = QGroupBox("Najlepsze okazje")
        layout = QVBoxLayout()
        
        # Control buttons and filter info
        controls_layout = QHBoxLayout()
        
        self._refresh_best_btn = QPushButton("Odśwież")
        self._refresh_best_btn.clicked.connect(lambda: asyncio.create_task(self._load_best_deals()))
        controls_layout.addWidget(self._refresh_best_btn)
        
        # Filters button
        self._filters_btn = QPushButton("⚙ Filtry")
        self._filters_btn.clicked.connect(self._open_filters_dialog)
        controls_layout.addWidget(self._filters_btn)

        controls_layout.addStretch()
        
        # Filter status label
        self._filter_status_label = QLabel("Brak aktywnych filtrów")
        self._filter_status_label.setStyleSheet("color: gray; font-style: italic;")
        controls_layout.addWidget(self._filter_status_label)

        controls_layout.addSpacing(10)

        # Page size selector
        controls_layout.addWidget(QLabel("Na stronę:"))
        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(["50", "100", "150", "200"])
        self._page_size_combo.setCurrentText("100")
        self._page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        controls_layout.addWidget(self._page_size_combo)

        layout.addLayout(controls_layout)
        
        # Deals list
        self._best_deals_list = QListWidget()
        self._best_deals_list.setWordWrap(True)
        # Connect click event to open store URL
        self._best_deals_list.itemClicked.connect(self._on_deal_clicked)
        layout.addWidget(self._best_deals_list)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        self._first_page_btn = QPushButton("⏮ Pierwsza")
        self._prev_page_btn = QPushButton("◀ Poprzednia")
        self._next_page_btn = QPushButton("Następna ▶")
        self._last_page_btn = QPushButton("Ostatnia ⏭")

        self._first_page_btn.clicked.connect(lambda: self._go_to_page(1))
        self._prev_page_btn.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        self._next_page_btn.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        self._last_page_btn.clicked.connect(lambda: self._go_to_page(self._total_pages))

        pagination_layout.addWidget(self._first_page_btn)
        pagination_layout.addWidget(self._prev_page_btn)

        # Current page display and jump
        pagination_layout.addStretch()
        self._page_info_label = QLabel("Strona 1/1")
        pagination_layout.addWidget(self._page_info_label)

        pagination_layout.addStretch()
        self._jump_page_input = QLineEdit()
        self._jump_page_input.setPlaceholderText("Idź do strony...")
        self._jump_page_input.setFixedWidth(120)
        self._jump_page_input.returnPressed.connect(self._on_jump_to_page)
        pagination_layout.addWidget(self._jump_page_input)

        pagination_layout.addWidget(self._next_page_btn)
        pagination_layout.addWidget(self._last_page_btn)
        layout.addLayout(pagination_layout)

        # Status label
        self._best_deals_status = QLabel("Ładowanie...")
        self._best_deals_status.setStyleSheet("color: gray; font-style: italic;")
        self._best_deals_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._best_deals_status)
        
        group.setLayout(layout)
        return group
    
    def _create_search_results_section(self) -> QWidget:
        """Create search results section."""
        group = QGroupBox("Wyszukiwanie gry")
        layout = QVBoxLayout()

        # Search input and button
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Wpisz tytuł gry...")
        self._search_input.returnPressed.connect(lambda: asyncio.create_task(self._search_deals()))
        search_layout.addWidget(self._search_input)

        self._search_btn = QPushButton("Szukaj")
        self._search_btn.clicked.connect(lambda: asyncio.create_task(self._search_deals()))
        search_layout.addWidget(self._search_btn)

        layout.addLayout(search_layout)

        # Status label
        self._search_status_label = QLabel("Wpisz tytuł gry i kliknij 'Szukaj'")
        self._search_status_label.setStyleSheet("color: gray; font-style: italic;")
        self._search_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._search_status_label)

        # Results container (this will be cleared and refilled)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self._search_results_widget = QWidget()
        self._search_results_layout = QVBoxLayout(self._search_results_widget)
        self._search_results_layout.addStretch()  # Initial stretch

        scroll_area.setWidget(self._search_results_widget)
        layout.addWidget(scroll_area)

        group.setLayout(layout)
        return group

    def _on_page_size_changed(self, text: str):
        try:
            size = int(text)
        except ValueError:
            size = 100
        self._page_size = max(1, min(200, size))
        # Reset to first page on page size change
        self._current_page = 1
        # Re-apply filtering and pagination
        self._filter_and_display_best_deals()

    def _open_filters_dialog(self):
        """Open the advanced filters dialog."""
        from app.ui.deals_filter_dialog import DealsFilterDialog

        dialog = DealsFilterDialog(self._filters, self)
        dialog.filters_applied.connect(self._on_filters_applied)
        dialog.exec()

    def _on_filters_applied(self, filters: Dict[str, Any]):
        """Handle filters being applied from the dialog."""
        self._filters = filters
        self._update_filter_status()
        # Reload deals with new filters
        asyncio.create_task(self._load_best_deals())

    def _update_filter_status(self):
        """Update the filter status label."""
        from app.ui.deals_filter_dialog import DealsFilterDialog

        if DealsFilterDialog.is_default_filters(self._filters):
            self._filter_status_label.setText("Brak aktywnych filtrów")
            self._filter_status_label.setStyleSheet("color: gray; font-style: italic;")
            self._filters_btn.setStyleSheet("")  # Default style
        else:
            summary = DealsFilterDialog.get_filter_summary(self._filters)
            self._filter_status_label.setText(summary)
            self._filter_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self._filters_btn.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")

    def _on_best_discount_filter_changed(self):
        """Handle slider value change - filter locally without server request."""
        # Only filter if we have deals loaded
        if hasattr(self, '_all_best_deals') and self._all_best_deals:
            self._filter_and_display_best_deals()

    def _on_min_price_changed(self):
        """Handle min price change - filter locally without server request."""
        # Only filter if we have deals loaded
        if hasattr(self, '_all_best_deals') and self._all_best_deals:
            self._filter_and_display_best_deals()
        text = self._jump_page_input.text().strip()
        if not text:
            return
        try:
            page = int(text)
        except ValueError:
            return
        self._go_to_page(page)


    def _update_pagination_controls(self):
        # Update page info label and button states
        self._page_info_label.setText(f"Strona {self._current_page}/{self._total_pages}")
        self._first_page_btn.setEnabled(self._current_page > 1)
        self._prev_page_btn.setEnabled(self._current_page > 1)
        self._next_page_btn.setEnabled(self._current_page < self._total_pages)
        self._last_page_btn.setEnabled(self._current_page < self._total_pages)

    def _on_jump_to_page(self):
        """Handle jump to page from input field."""
        text = self._jump_page_input.text().strip()
        if not text:
            return
        try:
            page = int(text)
        except ValueError:
            return
        self._go_to_page(page)

    def _go_to_page(self, page: int):
        """Go to specified page."""
        if self._total_pages <= 0:
            return
        page = max(1, min(self._total_pages, page))
        if page == self._current_page:
            return
        self._current_page = page

        # Recalculate which deals to show for this page
        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size
        self._best_deals = self._all_best_deals[start:end]

        # Update UI
        self._update_best_deals_list()
        self._update_pagination_controls()

    async def _load_best_deals(self):
        """Load best deals from server."""
        try:
            self._best_deals_status.setText("Ładowanie...")
            self._refresh_best_btn.setEnabled(False)
            
            # Get filter values from stored filters
            min_discount = self._filters.get('min_discount', 0)
            min_price = self._filters.get('min_price', 0.0)
            shops = self._filters.get('shops', [61, 35, 88, 82])
            mature = self._filters.get('mature', False)
            sort_order = self._filters.get('sort', '-cut')

            # Fetch deals from backend with filters
            # Note: min_discount is NOT sent to backend - filtering by discount
            # should be done on frontend after receiving data from ITAD API
            deals = await self._server_client.get_best_deals(
                limit=1000,
                min_discount=0,  # Don't filter by discount on backend
                min_price=min_price,
                shops=shops,
                mature=mature,
                sort=sort_order
            )

            # Filter by minimum discount on frontend (if specified in filters)
            if min_discount > 0:
                deals = [d for d in deals if d.get('discount_percent', 0) >= min_discount]

            # Store all deals for pagination
            self._all_best_deals = deals

            # Reset to first page on fresh load
            self._current_page = 1

            # Apply pagination and update display
            self._filter_and_display_best_deals()

        except Exception as e:
            logger.error(f"DealsView: Error loading best deals: {e}")
            self._best_deals_status.setText("❌ Błąd ładowania promocji")
        finally:
            self._refresh_best_btn.setEnabled(True)

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

    def _filter_and_display_best_deals(self):
        """Apply pagination and update display."""
        # Get deals (already filtered by backend)
        filtered_deals = self._all_best_deals

        # Pagination math
        total_items = len(filtered_deals)
        self._total_pages = max(1, (total_items + self._page_size - 1) // self._page_size)
        # Clamp current page
        self._current_page = max(1, min(self._current_page, self._total_pages))
        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size

        # Update displayed deals (current page slice)
        self._best_deals = filtered_deals[start:end]
        self._update_best_deals_list()
        self._update_pagination_controls()

        # Update status message
        if total_items:
            self._best_deals_status.setText(
                f"Znaleziono {total_items} promocji"
            )
        else:
            self._best_deals_status.setText("Brak promocji spełniających kryteria filtrów")

    def _update_best_deals_list(self):
        """Update the best deals list widget for the current page."""
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
            
            # Use filters from dialog for minimum discount
            min_discount = self._filters.get('min_discount', 0)

            result = await self._server_client.search_game_deals(
                search_term,
                min_discount=min_discount,
                limit=20
            )

            if not result:
                self._search_status_label.setText("❌ Błąd wyszukiwania")
                return
            
            self._display_search_results(result, search_term, min_discount)

        except Exception as e:
            logger.error(f"DealsView: Error searching deals: {e}")
            self._search_status_label.setText("❌ Błąd wyszukiwania")
        finally:
            self._search_btn.setEnabled(True)
    
    def _display_search_results(self, result: Dict[str, Any], search_term: str, min_discount: int):
        """Display search results in the results panel."""
        # Store current search state for theme refresh
        self._current_search_result = result
        self._current_search_term = search_term
        self._current_search_min_discount = min_discount

        # Clear previous results (but not the status label which is separate)
        while self._search_results_layout.count():
            child = self._search_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not result.get("found"):
            # Update status label
            self._search_status_label.setText(f"❌ Brak wyników dla: '{search_term}'")
            self._search_status_label.setStyleSheet("color: orange; font-weight: bold;")

            # Add explanation in the results area
            if min_discount > 0:
                no_deals_msg = QLabel(f"(brak promocji z min. {min_discount}% zniżki)")
                no_deals_msg.setStyleSheet("color: gray; font-style: italic; text-align: center;")
                no_deals_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._search_results_layout.addWidget(no_deals_msg)

            self._search_results_layout.addStretch()
            return
        
        # Found deals - update status
        deals = result.get("deals", [])
        count = result.get("count", len(deals))

        if min_discount > 0:
            self._search_status_label.setText(f"✓ Znaleziono {count} promocji (min. {min_discount}%)")
        else:
            self._search_status_label.setText(f"✓ Znaleziono {count} promocji")
        self._search_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Display each deal in the results area
        for deal in deals:
            deal_widget = self._create_deal_widget(deal)
            self._search_results_layout.addWidget(deal_widget)

        self._search_results_layout.addStretch()
    
    def _create_deal_widget(self, deal: Dict[str, Any]) -> QWidget:
        """Create a widget displaying deal information."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Game title
        title = deal.get("game_title", "Unknown Game")
        title_label = QLabel(f"🎮 {title}")
        title_label.setStyleSheet("font-size: 13pt; font-weight: bold; margin-bottom: 5px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Deal header - using correct API field names
        discount = deal.get("discount_percent", 0)
        if discount > 0:
            header = QLabel(f"🎉 Promocja: -{discount}%")
            header.setStyleSheet("font-size: 12pt; font-weight: bold; color: #4CAF50;")
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
        
        # DRM info if available
        drm = deal.get("drm", "")
        if drm and drm != "Unknown":
            drm_label = QLabel(f"🔒 DRM: {drm}")
            drm_label.setStyleSheet("margin: 5px; color: #888;")
            layout.addWidget(drm_label)

        # URL if available - using correct API field name
        if deal.get("store_url"):
            url_label = QLabel(f"🔗 <a href='{deal['store_url']}' style='color: #2196F3;'>Przejdź do oferty</a>")
            url_label.setOpenExternalLinks(True)
            url_label.setStyleSheet("margin: 5px;")
            layout.addWidget(url_label)
        
        # Style based on discount using theme colors
        colors = self._theme_manager.get_colors()

        # Get base background color and adjust for discount level
        if discount >= 75:
            # Best deals - use accent color
            bg_color = colors['accent']
        elif discount >= 50:
            # Good deals - slightly dimmer
            bg_color = colors['accent_hover']
        elif discount >= 25:
            # Decent deals
            bg_color = colors['background_group']
        else:
            # Small discount
            bg_color = colors['background_light']

        widget.setStyleSheet(f"""
            background-color: {bg_color}; 
            border-radius: 5px; 
            margin: 5px; 
            padding: 5px;
            color: {colors['foreground']};
        """)

        return widget
    
    async def refresh_data(self):
        """Refresh all data (best deals)."""
        await self._load_best_deals()

    def _on_theme_changed(self, mode: str, palette: str):
        """Handle theme change event."""
        # Refresh widget style
        refresh_style(self)

        # Reload deal items to update their colors
        if self._best_deals:
            self._update_best_deals_list()

        # Refresh search results if they exist
        if self._current_search_result is not None:
            self._display_search_results(
                self._current_search_result,
                self._current_search_term,
                self._current_search_min_discount
            )
