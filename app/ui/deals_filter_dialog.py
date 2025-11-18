"""Dialog for filtering deals with advanced options."""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QComboBox,
    QSlider, QWidget
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import apply_style
from app.ui.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class DealsFilterDialog(QDialog):
    """
    Dialog for advanced filtering of game deals.
    
    Features:
    - Minimum discount percentage
    - Minimum price
    - Shop selection (Steam, GOG, Epic, Humble)
    - Mature content filter
    - Sort options
    """
    
    # Signal emitted when filters are applied
    filters_applied = Signal(dict)
    
    def __init__(self, current_filters: Optional[Dict[str, Any]] = None, parent=None):
        """
        Initialize the filter dialog.
        
        Args:
            current_filters: Current filter values to initialize with
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Filtry promocji")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize with current filters or defaults
        self._filters = current_filters or self._get_default_filters()
        
        self._init_ui()
        self._load_filter_values()
        
        apply_style(self)
    
    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filter values."""
        return {
            'min_discount': 0,
            'min_price': 0.0,
            'shops': [61, 35, 88, 82],  # All shops by default
            'mature': False,
            'sort': '-cut'  # Sort by discount (highest first)
        }
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Zaawansowane filtry promocji")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Discount filter
        discount_group = self._create_discount_section()
        layout.addWidget(discount_group)
        
        # Price filter
        price_group = self._create_price_section()
        layout.addWidget(price_group)
        
        # Shops filter
        shops_group = self._create_shops_section()
        layout.addWidget(shops_group)
        
        # Sorting options
        sort_group = self._create_sort_section()
        layout.addWidget(sort_group)
        
        # Other options
        other_group = self._create_other_section()
        layout.addWidget(other_group)
        
        # Buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
    
    def _create_discount_section(self) -> QWidget:
        """Create discount filter section."""
        group = QGroupBox("Minimalna zniżka")
        layout = QVBoxLayout()
        
        # Slider + Spinbox combo
        controls_layout = QHBoxLayout()
        
        self._discount_slider = QSlider(Qt.Orientation.Horizontal)
        self._discount_slider.setMinimum(0)
        self._discount_slider.setMaximum(100)
        self._discount_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._discount_slider.setTickInterval(10)
        
        self._discount_spinbox = QSpinBox()
        self._discount_spinbox.setMinimum(0)
        self._discount_spinbox.setMaximum(100)
        self._discount_spinbox.setSuffix("%")
        
        # Connect slider and spinbox
        self._discount_slider.valueChanged.connect(self._discount_spinbox.setValue)
        self._discount_spinbox.valueChanged.connect(self._discount_slider.setValue)
        
        controls_layout.addWidget(self._discount_slider, stretch=3)
        controls_layout.addWidget(self._discount_spinbox, stretch=1)
        
        layout.addLayout(controls_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_price_section(self) -> QWidget:
        """Create price filter section."""
        group = QGroupBox("Minimalna cena")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Od:"))
        
        self._min_price_spinbox = QDoubleSpinBox()
        self._min_price_spinbox.setMinimum(0.0)
        self._min_price_spinbox.setMaximum(999.99)
        self._min_price_spinbox.setDecimals(2)
        self._min_price_spinbox.setSingleStep(1.0)
        self._min_price_spinbox.setSuffix(" €")
        
        layout.addWidget(self._min_price_spinbox)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_shops_section(self) -> QWidget:
        """Create shops filter section."""
        group = QGroupBox("Sklepy")
        layout = QVBoxLayout()
        
        info_label = QLabel("Wybierz sklepy, które chcesz uwzględnić:")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
        
        # Checkboxes for each shop
        self._shop_checkboxes = {}
        
        shops = [
            (61, "Steam"),
            (35, "GOG"),
            (88, "Epic Games Store"),
            (82, "Humble Bundle")
        ]
        
        for shop_id, shop_name in shops:
            checkbox = QCheckBox(shop_name)
            checkbox.setChecked(True)  # All shops by default
            self._shop_checkboxes[shop_id] = checkbox
            layout.addWidget(checkbox)
        
        # Select/Deselect all buttons
        buttons_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Zaznacz wszystkie")
        select_all_btn.clicked.connect(self._select_all_shops)
        buttons_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Odznacz wszystkie")
        deselect_all_btn.clicked.connect(self._deselect_all_shops)
        buttons_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_sort_section(self) -> QWidget:
        """Create sorting options section."""
        group = QGroupBox("Sortowanie")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Sortuj według:"))
        
        self._sort_combo = QComboBox()
        self._sort_combo.addItem("Największa zniżka", "-cut")
        self._sort_combo.addItem("Najniższa cena", "price")
        self._sort_combo.addItem("Najwyższa cena", "-price")
        self._sort_combo.addItem("Nazwa (A-Z)", "title")
        self._sort_combo.addItem("Nazwa (Z-A)", "-title")
        
        layout.addWidget(self._sort_combo)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_other_section(self) -> QWidget:
        """Create other options section."""
        group = QGroupBox("Inne opcje")
        layout = QVBoxLayout()
        
        self._mature_checkbox = QCheckBox("Pokaż gry dla dorosłych (mature content)")
        layout.addWidget(self._mature_checkbox)
        
        group.setLayout(layout)
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        # Reset button
        reset_btn = QPushButton("Resetuj filtry")
        reset_btn.clicked.connect(self._reset_filters)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("Zastosuj")
        apply_btn.clicked.connect(self._apply_filters)
        apply_btn.setDefault(True)
        layout.addWidget(apply_btn)
        
        return layout
    
    def _select_all_shops(self):
        """Select all shop checkboxes."""
        for checkbox in self._shop_checkboxes.values():
            checkbox.setChecked(True)
    
    def _deselect_all_shops(self):
        """Deselect all shop checkboxes."""
        for checkbox in self._shop_checkboxes.values():
            checkbox.setChecked(False)
    
    def _load_filter_values(self):
        """Load current filter values into UI controls."""
        self._discount_spinbox.setValue(self._filters.get('min_discount', 0))
        self._min_price_spinbox.setValue(self._filters.get('min_price', 0.0))
        self._mature_checkbox.setChecked(self._filters.get('mature', False))
        
        # Set shop checkboxes
        selected_shops = self._filters.get('shops', [61, 35, 88, 82])
        for shop_id, checkbox in self._shop_checkboxes.items():
            checkbox.setChecked(shop_id in selected_shops)
        
        # Set sort combo
        sort_value = self._filters.get('sort', '-cut')
        index = self._sort_combo.findData(sort_value)
        if index >= 0:
            self._sort_combo.setCurrentIndex(index)
    
    def _reset_filters(self):
        """Reset all filters to defaults."""
        self._filters = self._get_default_filters()
        self._load_filter_values()
    
    def _apply_filters(self):
        """Apply filters and close dialog."""
        # Collect filter values
        self._filters = {
            'min_discount': self._discount_spinbox.value(),
            'min_price': self._min_price_spinbox.value(),
            'shops': [
                shop_id for shop_id, checkbox in self._shop_checkboxes.items()
                if checkbox.isChecked()
            ],
            'mature': self._mature_checkbox.isChecked(),
            'sort': self._sort_combo.currentData()
        }
        
        # Emit signal with filters
        self.filters_applied.emit(self._filters)
        
        # Accept dialog
        self.accept()
    
    def get_filters(self) -> Dict[str, Any]:
        """Get current filter values."""
        return self._filters.copy()
    
    @staticmethod
    def is_default_filters(filters: Dict[str, Any]) -> bool:
        """Check if filters are at default values."""
        defaults = DealsFilterDialog._get_default_filters_static()
        
        return (
            filters.get('min_discount', 0) == 0 and
            filters.get('min_price', 0.0) == 0.0 and
            set(filters.get('shops', [])) == set(defaults['shops']) and
            filters.get('mature', False) == False and
            filters.get('sort', '-cut') == '-cut'
        )
    
    @staticmethod
    def _get_default_filters_static() -> Dict[str, Any]:
        """Get default filter values (static method)."""
        return {
            'min_discount': 0,
            'min_price': 0.0,
            'shops': [61, 35, 88, 82],
            'mature': False,
            'sort': '-cut'
        }
    
    @staticmethod
    def get_filter_summary(filters: Dict[str, Any]) -> str:
        """Get human-readable summary of active filters."""
        parts = []
        
        min_discount = filters.get('min_discount', 0)
        if min_discount > 0:
            parts.append(f"zniżka ≥{min_discount}%")
        
        min_price = filters.get('min_price', 0.0)
        if min_price > 0:
            parts.append(f"cena ≥{min_price:.2f}€")
        
        shops = filters.get('shops', [61, 35, 88, 82])
        all_shops = [61, 35, 88, 82]
        if set(shops) != set(all_shops):
            shop_names = {61: "Steam", 35: "GOG", 88: "Epic", 82: "Humble"}
            selected_names = [shop_names.get(s, str(s)) for s in shops]
            parts.append(f"sklepy: {', '.join(selected_names)}")
        
        if filters.get('mature', False):
            parts.append("mature content")
        
        sort_names = {
            '-cut': "największa zniżka",
            'price': "najniższa cena",
            '-price': "najwyższa cena",
            'title': "nazwa A-Z",
            '-title': "nazwa Z-A"
        }
        sort_value = filters.get('sort', '-cut')
        if sort_value != '-cut':
            parts.append(f"sortuj: {sort_names.get(sort_value, sort_value)}")
        
        if not parts:
            return "Brak aktywnych filtrów"
        
        return "Filtry: " + ", ".join(parts)

