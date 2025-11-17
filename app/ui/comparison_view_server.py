"""
Comparison view module for Custom Steam Dashboard.
Displays player count comparison charts and statistics for multiple games.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style

logger = logging.getLogger(__name__)


class ComparisonView(QWidget):
    """
    Comparison view for analyzing player counts across multiple games.
    
    Features:
    - Interactive chart showing player counts over time
    - Game selection from watchlist
    - Summary statistics table (min, max, average)
    - 7-day historical data
    """
    
    def __init__(self, server_url: Optional[str] = None, parent=None):
        """
        Initialize the comparison view.
        
        Args:
            server_url: URL of the backend server
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._server_client = ServerClient(server_url)
        self._all_games = []
        self._selected_appids = []
        self._history_data = {}
        self._selected_time_range = "7d"  # Default time range

        self._init_ui()
        
        # Auto-refresh timer (every 5 minutes)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._refresh_timer.start(300000)  # 5 minutes
        
        # Initial data load
        asyncio.create_task(self._load_games())
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Porównanie danych graczy")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Chart area
        self._chart_group = QGroupBox("Wykres liczby graczy (7 dni)")
        chart_layout = QVBoxLayout()
        
        self._figure = Figure(figsize=(10, 6))
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._ax = self._figure.add_subplot(111)
        # --- Hover annotation setup ---
        self._hover_annotation = self._ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", alpha=0.85, edgecolor="#444"),
            arrowprops=dict(arrowstyle="->", color="#333")
        )
        self._hover_annotation.set_visible(False)
        self._cid_motion = None  # Matplotlib connection id for motion event

        chart_layout.addWidget(self._canvas)
        self._chart_group.setLayout(chart_layout)
        layout.addWidget(self._chart_group, stretch=2)

        # Statistics table
        stats_group = QGroupBox("Statystyki podsumowujące")
        stats_layout = QVBoxLayout()
        
        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(6)
        self._stats_table.setHorizontalHeaderLabels(["Gra", "Minimum", "Maksimum", "Średnia", "Mediana", "Wahanie %"])
        self._stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._stats_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        stats_layout.addWidget(self._stats_table)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group, stretch=1)
        
        apply_style(self)
    
    def _create_control_panel(self) -> QWidget:
        """Create control panel with game selection."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Game selection list
        game_selection_group = QGroupBox("Wybierz gry do porównania")
        game_layout = QVBoxLayout()
        
        self._game_list = QListWidget()
        self._game_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._game_list.itemSelectionChanged.connect(self._on_selection_changed)
        game_layout.addWidget(self._game_list)
        
        game_selection_group.setLayout(game_layout)
        layout.addWidget(game_selection_group)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        # Time range selector
        time_range_layout = QHBoxLayout()
        time_range_label = QLabel("Zakres czasu:")
        self._time_range_combo = QComboBox()
        self._time_range_combo.addItems(["1h", "3h", "6h", "12h", "1d", "3d", "7d"])
        self._time_range_combo.setCurrentText("7d")
        self._time_range_combo.currentTextChanged.connect(self._on_time_range_changed)
        time_range_layout.addWidget(time_range_label)
        time_range_layout.addWidget(self._time_range_combo)
        button_layout.addLayout(time_range_layout)

        self._compare_btn = QPushButton("Porównaj wybrane")
        self._compare_btn.clicked.connect(lambda: asyncio.create_task(self._load_comparison()))
        button_layout.addWidget(self._compare_btn)
        
        self._select_top_btn = QPushButton("Wybierz TOP 5")
        self._select_top_btn.clicked.connect(self._select_top_5)
        button_layout.addWidget(self._select_top_btn)
        
        self._clear_btn = QPushButton("Wyczyść wybór")
        self._clear_btn.clicked.connect(self._clear_selection)
        button_layout.addWidget(self._clear_btn)
        
        self._refresh_btn = QPushButton("Odśwież dane")
        self._refresh_btn.clicked.connect(lambda: asyncio.create_task(self.refresh_data()))
        button_layout.addWidget(self._refresh_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return panel
    
    async def _load_games(self):
        """Load list of games from server."""
        try:
            # Authenticate if not already authenticated
            if not hasattr(self, '_authenticated') or not self._authenticated:
                logger.info("ComparisonView: Authenticating with server...")
                auth_success = await self._server_client.authenticate()
                if not auth_success:
                    logger.error("ComparisonView: Failed to authenticate with server")
                    return
                self._authenticated = True
                logger.info("ComparisonView: Authentication successful")

            logger.info("ComparisonView: Fetching current players...")
            games = await self._server_client.get_current_players()

            if not games:
                logger.warning("ComparisonView: No games returned from server")
                return

            self._all_games = sorted(games, key=lambda x: x.get('current_players', 0), reverse=True)
            
            self._game_list.clear()
            for game in self._all_games:
                name = game.get('name', 'Unknown')
                appid = game.get('appid')
                
                item = self._game_list.addItem(name)
                # Store appid in item data
                self._game_list.item(self._game_list.count() - 1).setData(Qt.ItemDataRole.UserRole, appid)

            logger.info(f"Loaded {len(self._all_games)} games for comparison")
        except Exception as e:
            logger.error(f"Error loading games: {e}")
    
    def _on_selection_changed(self):
        """Handle game selection change."""
        selected_items = self._game_list.selectedItems()
        self._selected_appids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        # Enable compare button only if at least one game is selected
        self._compare_btn.setEnabled(len(self._selected_appids) > 0)
    
    def _on_time_range_changed(self, time_range: str):
        """Handle time range selection change."""
        self._selected_time_range = time_range
        # Update chart group title
        self._chart_group.setTitle(f"Wykres liczby graczy ({time_range})")
        # Reload comparison if games are already selected
        if self._selected_appids and self._history_data:
            asyncio.create_task(self._load_comparison())

    def _time_range_to_days(self, time_range: str) -> float:
        """Convert time range string to days (fractional for hours)."""
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return hours / 24.0
        elif time_range.endswith('d'):
            return int(time_range[:-1])
        return 7  # Default

    def _select_top_5(self):
        """Select top 5 games by current player count."""
        self._game_list.clearSelection()
        for i in range(min(5, self._game_list.count())):
            self._game_list.item(i).setSelected(True)
    
    def _clear_selection(self):
        """Clear all selections."""
        self._game_list.clearSelection()
        self._selected_appids = []
        self._history_data = {}
        self._update_chart()
        self._update_stats_table()
    
    async def _load_comparison(self):
        """Load comparison data for selected games."""
        if not self._selected_appids:
            return
        
        try:
            self._compare_btn.setEnabled(False)
            self._compare_btn.setText("Ładowanie...")
            
            # Convert time range to days
            days = self._time_range_to_days(self._selected_time_range)

            logger.info(f"ComparisonView: Loading comparison for {len(self._selected_appids)} games: {self._selected_appids}")
            logger.info(f"ComparisonView: Time range: {self._selected_time_range} ({days} days)")

            # Fetch player history for selected games
            self._history_data = await self._server_client.get_player_history_comparison(
                self._selected_appids, 
                days=days
            )
            
            if not self._history_data:
                logger.warning("ComparisonView: No history data returned from server")
            else:
                logger.info(f"ComparisonView: Received history data for {len(self._history_data)} games")

            # Update UI
            self._update_chart()
            self._update_stats_table()
            
        except Exception as e:
            logger.error(f"ComparisonView: Error loading comparison data: {e}", exc_info=True)
        finally:
            self._compare_btn.setEnabled(True)
            self._compare_btn.setText("Porównaj wybrane")
    
    def _update_chart(self):
        """Update the comparison chart."""
        self._ax.clear()
        
        if not self._history_data:
            self._ax.text(0.5, 0.5, 'Wybierz gry i kliknij "Porównaj wybrane"',
                         ha='center', va='center', transform=self._ax.transAxes,
                         fontsize=12, color='white')
            # Set dark background
            self._figure.patch.set_facecolor('#2b2b2b')
            self._ax.set_facecolor('#1e1e1e')
            self._canvas.draw()
            return
        
        # Set dark theme
        self._figure.patch.set_facecolor('#2b2b2b')
        self._ax.set_facecolor('#1e1e1e')

        # Plot data for each game with brighter colors
        colors = ['#5dade2', '#f39c12', '#2ecc71', '#e74c3c', '#9b59b6',
                  '#1abc9c', '#e67e22', '#3498db', '#f1c40f', '#16a085']

        for idx, (appid, game_data) in enumerate(self._history_data.items()):
            history = game_data.get('history', [])
            if not history:
                continue
            
            # Sort by timestamp
            history = sorted(history, key=lambda x: x.get('time_stamp', 0))
            
            # Extract timestamps and player counts
            timestamps = [datetime.fromtimestamp(record.get('time_stamp', 0)) for record in history]
            counts = [record.get('count', 0) for record in history]
            
            # Plot line with brighter color
            color = colors[idx % len(colors)]
            name = game_data.get('name', f'Game {appid}')
            self._ax.plot(timestamps, counts, label=name, color=color, linewidth=2.5, marker='o', markersize=4)

        # Format chart with light colors for dark theme
        self._ax.set_xlabel('Data', fontsize=10, color='white')
        self._ax.set_ylabel('Liczba graczy', fontsize=10, color='white')

        # Dynamic title based on time range
        time_range_label = self._selected_time_range
        self._ax.set_title(f'Porównanie liczby graczy ({time_range_label})',
                          fontsize=12, fontweight='bold', color='white')

        # Legend with dark theme
        legend = self._ax.legend(loc='best', fontsize=9, facecolor='#2b2b2b', edgecolor='#444')
        for text in legend.get_texts():
            text.set_color('white')

        # Grid with lighter color for visibility
        self._ax.grid(True, alpha=0.2, color='#666')

        # Format x-axis based on time range
        days = self._time_range_to_days(self._selected_time_range)
        if days <= 1:  # For 1 day or less, show hours
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self._ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, int(days * 24 / 6))))
        elif days <= 3:  # For 1-3 days, show day and hour
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m %H:%M'))
            self._ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        else:  # For longer periods, show only dates
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            self._ax.xaxis.set_major_locator(mdates.DayLocator())
        self._figure.autofmt_xdate()
        
        # Tick colors
        self._ax.tick_params(colors='white', which='both')

        # Spine colors
        for spine in self._ax.spines.values():
            spine.set_edgecolor('#444')

        # Format y-axis with thousand separators
        self._ax.yaxis.set_major_formatter(lambda x, p: f'{int(x):,}')
        
        self._figure.tight_layout()
        self._canvas.draw()
        # Setup hover after drawing if not already
        if self._cid_motion is None:
            self._cid_motion = self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _on_motion(self, event):
        """Handle mouse movement over the canvas to display nearest point info."""
        if event.inaxes != self._ax:
            if self._hover_annotation.get_visible():
                self._hover_annotation.set_visible(False)
                self._canvas.draw_idle()
            return
        nearest_line = None
        nearest_x = None
        nearest_y = None
        nearest_dist = math.inf
        # Iterate over lines to find nearest data point to cursor x position
        for line in self._ax.get_lines():
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            if not len(xdata):
                continue
            # Convert event.xdata (float) compare to xdata (datetime -> float via mdates)
            x_numeric = [mdates.date2num(x) for x in xdata]
            # Find index of closest x
            try:
                cursor_x = event.xdata
                diffs = [abs(cursor_x - xv) for xv in x_numeric]
            except Exception:
                continue
            min_idx = diffs.index(min(diffs))
            dist = diffs[min_idx]
            # Threshold: ignore if too far (adjustable)
            if dist < nearest_dist and dist < 0.15:  # ~0.15 day (~3.6h) resolution threshold
                nearest_dist = dist
                nearest_line = line
                nearest_x = xdata[min_idx]
                nearest_y = ydata[min_idx]
        if nearest_line is None:
            if self._hover_annotation.get_visible():
                self._hover_annotation.set_visible(False)
                self._canvas.draw_idle()
            return
        # Update annotation
        self._hover_annotation.xy = (nearest_x, nearest_y)
        # Format timestamp and count
        ts_str = nearest_x.strftime('%d.%m %H:%M') if isinstance(nearest_x, datetime) else str(nearest_x)
        count_str = f"{int(nearest_y):,}".replace(',', ' ')  # Use space as thousands sep for PL locale feel
        label = nearest_line.get_label()
        self._hover_annotation.set_text(f"{label}\n{ts_str}\nGraczy: {count_str}")
        self._hover_annotation.set_visible(True)
        self._canvas.draw_idle()

    def _update_stats_table(self):
        """Update the statistics table."""
        self._stats_table.setRowCount(0)
        
        if not self._history_data:
            return
        
        for appid, game_data in self._history_data.items():
            history = game_data.get('history', [])
            if not history:
                continue
            
            # Calculate statistics
            counts = [record.get('count', 0) for record in history]
            if not counts:
                continue
            
            min_count = min(counts)
            max_count = max(counts)
            avg_count = sum(counts) / len(counts)
            
            # Calculate median
            sorted_counts = sorted(counts)
            n = len(sorted_counts)
            if n % 2 == 0:
                median_count = (sorted_counts[n//2 - 1] + sorted_counts[n//2]) / 2
            else:
                median_count = sorted_counts[n//2]

            # Calculate volatility (percentage difference between max and min relative to average)
            volatility = ((max_count - min_count) / avg_count * 100) if avg_count > 0 else 0

            # Add row to table
            row = self._stats_table.rowCount()
            self._stats_table.insertRow(row)
            
            name = game_data.get('name', f'Game {appid}')
            self._stats_table.setItem(row, 0, QTableWidgetItem(name))
            self._stats_table.setItem(row, 1, QTableWidgetItem(f"{min_count:,}"))
            self._stats_table.setItem(row, 2, QTableWidgetItem(f"{max_count:,}"))
            self._stats_table.setItem(row, 3, QTableWidgetItem(f"{int(avg_count):,}"))
            self._stats_table.setItem(row, 4, QTableWidgetItem(f"{int(median_count):,}"))
            self._stats_table.setItem(row, 5, QTableWidgetItem(f"{volatility:.1f}%"))

            # Center align numeric columns
            for col in range(1, 6):
                self._stats_table.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    async def refresh_data(self):
        """Refresh all data."""
        await self._load_games()
        if self._selected_appids:
            await self._load_comparison()
