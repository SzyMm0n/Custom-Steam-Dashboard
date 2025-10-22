import asyncio
from typing import List, Dict, Any, Optional, Set

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame,
    QHBoxLayout, QCheckBox, QGroupBox, QSizePolicy,
    QSlider, QPushButton, QLineEdit, QDialog
)
from PySide6.QtCore import QTimer, Qt, QLocale, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator

from app.core.services.steam_api import SteamStoreClient
from app.core.data.db import AsyncDatabase as Database

# DealsApiClient optional
try:
    from app.core.services.deals_api import DealsApiClient
except Exception:
    DealsApiClient = None


class NumberValidator(QRegularExpressionValidator):
    def __init__(self, parent=None):
        # Pozwalamy na cyfry i spacje (separator tysięcy), maksymalnie 15 znaków
        super().__init__(QRegularExpression(r"^[0-9 ]{0,15}$"), parent)


class GameDetailDialog(QDialog):
    def __init__(self, game_data: Any, parent: Optional[QWidget] = None):
        """Show expanded details for a game.
        game_data can be a string title or a dict with keys: name, appid, players, tags
        """
        super().__init__(parent)
        self.setWindowTitle("Szczegóły gry")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        # Title
        if isinstance(game_data, dict):
            title = game_data.get("name", "Nieznana gra")
        else:
            title = str(game_data)

        title_lbl = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        layout.addWidget(title_lbl)

        # Details grid
        details_layout = QVBoxLayout()

        if isinstance(game_data, dict):
            appid = game_data.get("appid")
            players = game_data.get("players")
            tags = game_data.get("tags") or set()

            if appid is not None:
                details_layout.addWidget(QLabel(f"AppID: {appid}"))

            if players is not None:
                # format with thousands separator using Polish locale if possible
                try:
                    players_str = QLocale(QLocale.Language.Polish, QLocale.Country.Poland).toString(float(players), 'f', 0)
                except Exception:
                    players_str = str(players)
                details_layout.addWidget(QLabel(f"Obecni gracze: {players_str}"))

            if tags:
                tags_text = ", ".join(sorted(list(tags))) if isinstance(tags, (set, list, tuple)) else str(tags)
                tags_lbl = QLabel(f"Tagi: {tags_text}")
                tags_lbl.setWordWrap(True)
                details_layout.addWidget(tags_lbl)

        else:
            details_layout.addWidget(QLabel("Brak dodatkowych danych."))

        layout.addLayout(details_layout)

        # Close button
        btn_h = QHBoxLayout()
        btn_h.addStretch(1)
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        btn_h.addWidget(close_btn)
        layout.addLayout(btn_h)


class HomeView(QWidget):
    MAX_PLAYERS_SLIDER = 2000000

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._tag_checkboxes: List[QCheckBox] = []
        self._all_games_data: List[Dict[str, Any]] = []

        self._selected_tags: Set[str] = set()
        self._min_players: int = 0
        self._max_players: int = self.MAX_PLAYERS_SLIDER

        self.layout = QVBoxLayout(self)
        self.main_h_layout = QHBoxLayout()
        self._locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)

        self._init_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self._timer.start(300000)

        QTimer.singleShot(0, self._start_initial_load)

    def _start_initial_load(self):
        asyncio.create_task(self.refresh_data())

    def _init_ui(self):
        # Left column
        left_column = QVBoxLayout()
        self.top_live_title = QLabel("Live Games Count (Watchlista)")
        self.top_live_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.top_live_list = QListWidget()
        self.top_live_list.setMinimumWidth(500)
        self.top_live_list.itemClicked.connect(self._on_live_item_clicked)
        left_column.addWidget(self.top_live_title)
        left_column.addWidget(self.top_live_list)

        # Right column
        right_panel_widget = QWidget()
        right_panel_widget.setMinimumWidth(280)
        right_column_layout = QVBoxLayout(right_panel_widget)

        players_group = QGroupBox("Gracze online (Min. / Max.)")
        players_v_layout = QVBoxLayout(players_group)
        validator = NumberValidator(self)

        # Min
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

        # Max
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

        # Tags
        self.tags_group_box = QGroupBox("Filtruj wg kategorii/gatunków")
        tags_v_layout = QVBoxLayout(self.tags_group_box)

        # Use a single QListWidget for tags (checkable items) for reliable scrolling
        self.tags_list_widget = QListWidget()
        self.tags_list_widget.setSelectionMode(QListWidget.NoSelection)
        self.tags_list_widget.setAlternatingRowColors(False)
        self.tags_list_widget.setMinimumHeight(350)
        self.tags_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tags_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tags_list_widget.setFocusPolicy(Qt.StrongFocus)

        tags_v_layout.addWidget(self.tags_list_widget)
        right_column_layout.addWidget(self.tags_group_box)

        # Buttons
        buttons_h_layout = QHBoxLayout()
        self.clear_button = QPushButton("Wyczyść Filtry")
        self.clear_button.clicked.connect(self._on_clear_filters)
        self.apply_button = QPushButton("Zastosuj Filtry")
        self.apply_button.clicked.connect(self._on_apply_filters)
        buttons_h_layout.addWidget(self.clear_button)
        buttons_h_layout.addWidget(self.apply_button)
        right_column_layout.addLayout(buttons_h_layout)
        right_column_layout.addStretch(1)

        self.main_h_layout.addLayout(left_column, 1)
        self.main_h_layout.addWidget(right_panel_widget, 0)

        # Sections below
        self.separator_1 = QFrame()
        self.separator_1.setFrameShape(QFrame.Shape.HLine)
        self.separator_1.setFrameShadow(QFrame.Shadow.Sunken)
        self.trending_title = QLabel("Best Deals (Promocje)")
        self.trending_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.trending_list = QListWidget()
        # Nieco mniejsze, żeby suwaki nie były przysłonięte
        self.trending_list.setMinimumHeight(120)
        self.trending_list.setMaximumHeight(240)

        self.separator_2 = QFrame()
        self.separator_2.setFrameShape(QFrame.Shape.HLine)
        self.separator_2.setFrameShadow(QFrame.Shadow.Sunken)
        self.upcoming_title = QLabel("Best Upcoming Releases")
        self.upcoming_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.upcoming_list = QListWidget()
        # Nieco mniejsze, żeby suwaki nie były przysłonięte
        self.upcoming_list.setMinimumHeight(120)
        self.upcoming_list.setMaximumHeight(240)

        self.layout.addLayout(self.main_h_layout)
        self.layout.addWidget(self.separator_1)
        self.layout.addWidget(self.trending_title)
        self.layout.addWidget(self.trending_list)
        self.layout.addWidget(self.separator_2)
        self.layout.addWidget(self.upcoming_title)
        self.layout.addWidget(self.upcoming_list)

    # Slider/input handlers
    def _on_min_slider_moved(self, value: int):
        if value > self._max_players:
            # sync max
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

    def _on_apply_filters(self):
        # Collect selected tags from tags_list_widget
        self._selected_tags.clear()
        for i in range(self.tags_list_widget.count()):
            it = self.tags_list_widget.item(i)
            if it.checkState() == Qt.Checked:
                self._selected_tags.add(it.text())
        # parse inputs
        min_val_text = self.min_players_input.text().replace(' ', '')
        min_val = int(min_val_text) if min_val_text.isdigit() else 0
        max_val_text = self.max_players_input.text().replace(' ', '')
        max_val = int(max_val_text) if max_val_text.isdigit() else self.MAX_PLAYERS_SLIDER
        self._min_players = max(0, min(min_val, self.MAX_PLAYERS_SLIDER))
        self._max_players = max(0, min(max_val, self.MAX_PLAYERS_SLIDER))
        if self._min_players > self._max_players:
            self._min_players = self._max_players
        # sync sliders
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
        # Odznacz wszystkie pozycje w tags_list_widget
        for i in range(self.tags_list_widget.count()):
            it = self.tags_list_widget.item(i)
            if it.checkState() == Qt.Checked:
                it.setCheckState(Qt.Unchecked)
        # 4. Reset stanu filtrowania tagów
        self._selected_tags.clear()
        self._update_list_view()

    def _format_players(self, value: int) -> str:
        return self._locale.toString(float(value), 'f', 0)

    async def _populate_tag_checkboxes(self):
        """Pobiera wszystkie unikalne tagi i tworzy dla nich pola wyboru."""
        if self._tag_checkboxes:
            return

        try:
            genres = await self._db.get_all_watchlist_genres()
            categories = await self._db.get_all_watchlist_categories()
            all_tags = sorted(list(set(genres + categories)))
        except Exception as e:
            print(f"Błąd pobierania tagów z DB: {e}")
            all_tags = []

        if not all_tags:
            self.tags_list_widget.addItem("Brak tagów do filtrowania.")
            return

        # Clear existing items then add checkable items
        self.tags_list_widget.clear()
        for tag in all_tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.tags_list_widget.addItem(item)

        # Ensure scrollbar is available and content is laid out
        self.tags_list_widget.updateGeometry()
        sb = self.tags_list_widget.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_list_view(self):
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
            self.top_live_list.addItem("Brak gier pasujących do filtrów.")
        else:
            for item in filtered_results:
                players_formatted = self._format_players(item["players"])
                lw_item = QListWidgetItem(f"{players_formatted} - {item['name']}")
                lw_item.setData(Qt.UserRole, item)
                self.top_live_list.addItem(lw_item)

    async def refresh_data(self):
        self.top_live_title.setText("Live Games Count (Ładowanie...)")
        self.trending_title.setText("Best Deals (Ładowanie...)")
        self.upcoming_title.setText("Best Upcoming Releases (Ładowanie...)")
        self.trending_list.clear()
        self.upcoming_list.clear()
        appids = await self._db.get_watchlist_appids()
        all_game_tags = await self._db.get_all_game_tags()
        if not appids:
            self.top_live_title.setText("Live Games Count (Watchlista - pusta)")
            if self.tags_list_widget.count() == 0:
                await self._populate_tag_checkboxes()
            # Jeśli nie ma appidów, zresetuj tytuły sekcji promocji/nadchodzących
            self.trending_title.setText("Best Deals (Promocje)")
            self.upcoming_title.setText("Best Upcoming Releases")
            return
        async with SteamStoreClient() as client:
            player_tasks = [client.get_number_of_current_players(appid) for appid in appids]
            appids_to_detail = [appid for appid in appids if appid not in all_game_tags]
            detail_tasks = [client.get_app_details(appid, cc="pl", lang="pl") for appid in appids_to_detail]
            player_counts = await asyncio.gather(*player_tasks, return_exceptions=True)
            game_details_results = await asyncio.gather(*detail_tasks, return_exceptions=True)
            game_details_map = {appids_to_detail[i]: result for i, result in enumerate(game_details_results)}
        results = []
        for i, appid in enumerate(appids):
            count_result = player_counts[i]
            if isinstance(count_result, Exception) or count_result.player_count <= 0:
                continue
            name = f"AppID {appid}"
            current_game_tags: Set[str] = all_game_tags.get(appid, set())
            if appid in game_details_map:
                details_result = game_details_map[appid]
                if not isinstance(details_result, Exception) and details_result is not None:
                    name = details_result.name
                    new_genres = [g.description for g in details_result.genres or []]
                    new_categories = [c.description for c in details_result.categories or []]
                    await self._db.upsert_watchlist_tags(appid, genres=new_genres, categories=new_categories, replace=True)
                    await self._db.add_to_watchlist(appid, name)
                    current_game_tags = set(new_genres + new_categories)
            if name.startswith("AppID"):
                title_from_db = await self._db.get_title_by_appid(appid)
                if title_from_db:
                    name = title_from_db
            results.append({
                "name": name,
                "players": count_result.player_count,
                "appid": appid,
                "tags": current_game_tags,
            })
        self._all_games_data = results
        if self.tags_list_widget.count() == 0:
            await self._populate_tag_checkboxes()
        self._update_list_view()
        self.top_live_title.setText(f"Live Games Count (Watchlista - {len(results)} gier)")
        deals = []
        if DealsApiClient is not None:
            try:
                async with DealsApiClient() as deals_client:
                    deals = await deals_client.get_current_deals(limit=10, min_discount=20)
            except Exception as e:
                print(f"Błąd pobierania promocji: {e}")
                deals = []
        self.trending_list.clear()
        if not deals:
            self.trending_list.addItem("Brak aktualnych promocji.")
        else:
            for d in deals:
                try:
                    sale = getattr(d, 'salePrice', None)
                    normal = getattr(d, 'normalPrice', None)
                    title = getattr(d, 'title', str(d))
                    self.trending_list.addItem(f"{title} — {sale} (z {normal})")
                except Exception:
                    self.trending_list.addItem(str(d))
        try:
            async with SteamStoreClient() as client2:
                upcoming = await client2.get_coming_soon(cc="pl", lang="pl", limit=10)
        except Exception as e:
            print(f"Błąd pobierania nadchodzących: {e}")
            upcoming = []
        self.upcoming_list.clear()
        if not upcoming:
            self.upcoming_list.addItem("Brak nadchodzących premier.")
        else:
            for item in upcoming:
                name = getattr(item, 'name', 'Unknown')
                release = getattr(item, 'release_date', None) or getattr(item, 'releaseDate', None) or ''
                price = getattr(item, 'final_price', None) or getattr(item, 'finalPrice', None) or ''
                discount = getattr(item, 'discount_percent', None) or getattr(item, 'discountPercent', None) or ''
                display = f"{name} — premiera: {release}"
                if price:
                    display += f" — cena: {price}"
                if discount:
                    display += f" (-{discount}%)"
                self.upcoming_list.addItem(display)

        # Ustaw tytuły końcowe (reset po zakończeniu ładowania obu sekcji)
        self.trending_title.setText("Best Deals (Promocje)")
        self.upcoming_title.setText("Best Upcoming Releases")

    def _on_live_item_clicked(self, item: 'QListWidgetItem'):
        try:
            data = item.data(Qt.UserRole)
        except Exception:
            data = None

        # Open dialog with full data (dict) when available
        if isinstance(data, dict):
            dialog = GameDetailDialog(data, self)
        else:
            dialog = GameDetailDialog(item.text() if item is not None else "Nieznana gra", self)
        dialog.exec()

    def _on_live_clicked(self, item: 'QListWidgetItem'):
        return self._on_live_item_clicked(item)