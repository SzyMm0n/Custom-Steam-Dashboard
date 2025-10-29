import asyncio
from typing import List, Dict, Any, Optional, Set

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame,
    QHBoxLayout, QCheckBox, QGroupBox, QSizePolicy,
    QSlider, QPushButton, QLineEdit, QDialog, QScrollArea
)
from PySide6.QtCore import QTimer, Qt, QLocale, QRegularExpression, QUrl
from PySide6.QtGui import QFont, QRegularExpressionValidator, QPixmap, QDesktopServices

import httpx
import urllib.parse

from app.core.services.steam_api import SteamStoreClient
from app.core.data.db import AsyncDatabase as Database
from app.ui.user_info_dialog import SteamUserInfoDialog  # UPDATED import (unused now but kept if needed)

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
        game_data can be a string title or a dict with keys: name, appid, players, tags, deal_url, deal_id, store_id, store_name
        """
        super().__init__(parent)
        self.setWindowTitle("Szczegóły gry")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        # Title and basic fields
        if isinstance(game_data, dict):
            title = game_data.get("name", "Nieznana gra")
            self._appid = game_data.get("appid")
            self._players = game_data.get("players")
            self._tags = game_data.get("tags") or set()
            self._deal_url = game_data.get("deal_url")
            self._deal_id = game_data.get("deal_id")
            self._store_id = game_data.get("store_id")
            self._store_name = game_data.get("store_name")
        else:
            title = str(game_data)
            self._appid = None
            self._players = None
            self._tags = set()
            self._deal_url = None
            self._deal_id = None
            self._store_id = None
            self._store_name = None

        self._title = title

        title_lbl = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        layout.addWidget(title_lbl)

        # Image + description area
        self.header_image_lbl = QLabel()
        self.header_image_lbl.setFixedHeight(120)
        self.header_image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_image_lbl)

        self.desc_lbl = QLabel("Ładowanie opisu...")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        # Details grid (additional metadata)
        details_layout = QVBoxLayout()

        if self._appid is not None:
            if self._players is not None:
                # format with thousands separator using Polish locale if possible
                try:
                    players_str = QLocale(QLocale.Language.Polish, QLocale.Country.Poland).toString(float(self._players), 'f', 0)
                except Exception:
                    players_str = str(self._players)
                details_layout.addWidget(QLabel(f"Obecni gracze: {players_str}"))

            if self._tags:
                tags_text = ", ".join(sorted(list(self._tags))) if isinstance(self._tags, (set, list, tuple)) else str(self._tags)
                tags_lbl = QLabel(f"Tagi: {tags_text}")
                tags_lbl.setWordWrap(True)
                details_layout.addWidget(tags_lbl)

        else:
            details_layout.addWidget(QLabel("Brak dodatkowych danych."))

        layout.addLayout(details_layout)

        # Close button + Go to store button
        btn_h = QHBoxLayout()
        
        self.store_btn = QPushButton("Przejdź do sklepu")
        # Aktywuj, jeżeli mamy appid, bezpośredni link do oferty lub przynajmniej tytuł (otworzymy stronę CheapShark)
        self.store_btn.setEnabled((self._appid is not None) or (self._deal_url is not None) or bool(self._title))
        self.store_btn.clicked.connect(self._open_store_page)
        btn_h.addWidget(self.store_btn)

        btn_h.addStretch(1)

        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        btn_h.addWidget(close_btn)
        layout.addLayout(btn_h)

        # Start background load of extra info (store API + local DB)
        try:
            if self._appid is not None:
                asyncio.create_task(self._load_store_and_activity(self._appid))
            else:
                # Fallback: resolve appid by searching Steam store by title
                if self._title and self._title != "Nieznana gra":
                    asyncio.create_task(self._resolve_and_load_by_name(self._title))
        except Exception:
            # best-effort background task
            pass

    def _make_cheapshark_search_url(self) -> Optional[QUrl]:
        try:
            if not self._title:
                return None
            q = urllib.parse.quote_plus(self._title)
            base = f"https://www.cheapshark.com/search#q={q}"
            # jeśli znamy store_id, dodaj jako filtr
            if self._store_id is not None:
                try:
                    sid = int(self._store_id)
                    base += f"&storeID={sid}"
                except Exception:
                    pass
            return QUrl(base)
        except Exception:
            return None

    def _open_store_page(self):
        try:
            # 1) Prefer Steam app page when appid is known
            if self._appid:
                url = QUrl(f"https://store.steampowered.com/app/{int(self._appid)}/")
                QDesktopServices.openUrl(url)
                return
            # 2) If we have any direct deal/store URL (including CheapShark redirect), open it
            if isinstance(self._deal_url, str) and self._deal_url.strip():
                QDesktopServices.openUrl(QUrl(self._deal_url))
                return
            # 3) If we only have a deal id, construct CheapShark redirect to the store
            if self._deal_id:
                redir = QUrl(f"https://www.cheapshark.com/redirect?dealID={urllib.parse.quote_plus(str(self._deal_id))}")
                QDesktopServices.openUrl(redir)
                return
            # 4) Fallback: Open CheapShark search page for this title (optionally with store filter)
            cs_url = self._make_cheapshark_search_url()
            if cs_url is not None:
                QDesktopServices.openUrl(cs_url)
                return
        except Exception:
            pass

    async def _resolve_and_load_by_name(self, title: str):
        """Resolve Steam appid by game title, then load details if found."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/storesearch",
                    params={"term": title, "cc": "pl", "l": "pl"},
                )
                data = resp.json() if resp.status_code == 200 else {}
                items = data.get("items") if isinstance(data, dict) else None
                if items and isinstance(items, list):
                    first = items[0] if items else None
                    if isinstance(first, dict):
                        appid = first.get("id") or first.get("appid")
                        if appid:
                            try:
                                self._appid = int(appid)
                                # enable store button now that we have id
                                self.store_btn.setEnabled(True)
                                await self._load_store_and_activity(self._appid)
                            except Exception:
                                pass
        except Exception:
            pass

    async def _load_store_and_activity(self, appid: int):
        # Fetch store details (header image, short description)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://store.steampowered.com/api/appdetails",
                    params={"appids": appid, "cc": "pl", "l": "pl"},
                )
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
                    if short_desc:
                        # update description on main thread
                        self.desc_lbl.setText(short_desc)
                    if header_image:
                        try:
                            img_resp = await client.get(header_image, timeout=10.0)
                            if img_resp.status_code == 200:
                                pix = QPixmap()
                                pix.loadFromData(img_resp.content)
                                # scale preserving aspect
                                scaled = pix.scaledToHeight(
                                    120, Qt.TransformationMode.SmoothTransformation
                                )
                                self.header_image_lbl.setPixmap(scaled)
                        except Exception:
                            pass
        except Exception:
            # ignore network errors, leave placeholders
            pass

        # Load activity from local DB (daily rollups or raw samples) and draw plot
        try:
            parent = self.parent()
            db = None
            if parent is not None and hasattr(parent, "_db"):
                db = parent._db
            elif hasattr(self, "_db"):
                db = getattr(self, "_db")

            if db is not None:
                # try to read daily rollups first
                def query_daily():
                    try:
                        sync = getattr(db, "_sync_db", None)
                        if sync is None:
                            return []
                        conn = getattr(sync, "_conn", None)
                        if conn is None:
                            return []
                        cur = conn.execute(
                            "SELECT date_ymd, avg_players, max_players FROM player_counts_daily WHERE appid=? ORDER BY date_ymd DESC LIMIT 7",
                            (appid,),
                        )
                        return cur.fetchall()
                    except Exception:
                        return []

                rows = await asyncio.to_thread(query_daily)
                if rows:
                    # format textual activity from daily rollups
                    lines = []
                    for date_ymd, avg_players, max_players in rows:
                        try:
                            avg_str = QLocale(
                                QLocale.Language.Polish, QLocale.Country.Poland
                            ).toString(float(avg_players), "f", 0)
                        except Exception:
                            avg_str = str(avg_players)
                        lines.append(f"{date_ymd}: średnio {avg_str}, max {max_players}")
                    # activity_text = "\n".join(lines)
        except Exception:
            # ignore DB errors
            pass


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
        self.top_live_title = QLabel("Live Games Count")
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
        # Reduce minimum height so the panel can adapt; scrolling will be handled by the panel scroll area
        self.tags_list_widget.setMinimumHeight(200)
        self.tags_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tags_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tags_list_widget.setFocusPolicy(Qt.StrongFocus)

        tags_v_layout.addWidget(self.tags_list_widget)
        right_column_layout.addWidget(self.tags_group_box)

        # Buttons
        buttons_h_layout = QHBoxLayout()
        self.clear_button = QPushButton("Wyczyść Filtry")
        # mark clear button so we can style it differently (red)
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_filters)
        self.apply_button = QPushButton("Zastosuj Filtry")
        self.apply_button.clicked.connect(self._on_apply_filters)
        buttons_h_layout.addWidget(self.clear_button)
        buttons_h_layout.addWidget(self.apply_button)
        right_column_layout.addLayout(buttons_h_layout)
        right_column_layout.addStretch(1)

        self.main_h_layout.addLayout(left_column, 1)
        # Wrap the right panel in a scroll area so that on small windows the user can scroll to see all categories
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel_widget)
        self.main_h_layout.addWidget(right_scroll, 0)

        # --- Styling: kolorystyka (czarny, biały, zielony, czerwony) ---
        STYLE = """
QWidget {
  background-color: #0b0b0b;
  color: #FFFFFF;
  font-family: Sans-Serif;
}

QGroupBox {
  background-color: #15331f; /* dark green card */
  color: #FFFFFF;
  border: 1px solid #114d2b;
  border-radius: 8px;
  margin-top: 6px;
  padding: 6px;
}

QLabel[role=section] {
  color: #86efac; /* light green */
  font-weight: bold;
  font-size: 16px;
}

QListWidget {
  background-color: #111111;
  color: #FFFFFF;
  border: 1px solid #2a2a2a;
}

QListWidget::item:selected {
  background: #16a34a; /* green accent */
  color: #fff;
}

QPushButton {
  background-color: #16a34a; /* green */
  color: #FFFFFF;
  border-radius: 6px;
  padding: 6px 8px;
}

QPushButton#clearButton {
  background-color: #e11d48; /* red */
}

QLineEdit {
  background-color: #1b1b1b;
  color: #fff;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  padding: 3px;
}
QSlider::groove:horizontal { height:8px; background:#2a2a2a; border-radius:4px;}
QSlider::handle:horizontal { background:#16a34a; width:16px; margin:-4px 0; border-radius:8px;}
"""
        # apply stylesheet to this widget (will affect children)
        self.setStyleSheet(STYLE)

        # mark section labels so stylesheet rules apply
        self.top_live_title.setProperty("role", "section")

        # separator between main panel and lower sections
        self.separator_1 = QFrame()
        self.separator_1.setFrameShape(QFrame.Shape.HLine)
        self.separator_1.setFrameShadow(QFrame.Shadow.Sunken)

        self.trending_title = QLabel("Best Deals")
        self.trending_title.setProperty("role", "section")
        self.trending_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.trending_list = QListWidget()
        # Nieco mniejsze, żeby suwaki nie były przysłonięte
        self.trending_list.setMinimumHeight(120)
        self.trending_list.setMaximumHeight(240)
        # NEW: open details when clicking deals items
        self.trending_list.itemClicked.connect(self._on_deal_item_clicked)

        self.separator_2 = QFrame()
        self.separator_2.setFrameShape(QFrame.Shape.HLine)
        self.separator_2.setFrameShadow(QFrame.Shadow.Sunken)
        self.upcoming_title = QLabel("Best Upcoming Releases")
        self.upcoming_title.setProperty("role", "section")
        self.upcoming_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.upcoming_list = QListWidget()
        # Nieco mniejsze, żeby suwaki nie były przysłonięte
        self.upcoming_list.setMinimumHeight(120)
        self.upcoming_list.setMaximumHeight(240)
        # NEW: open details when clicking upcoming items
        self.upcoming_list.itemClicked.connect(self._on_upcoming_item_clicked)

        self.layout.addLayout(self.main_h_layout)
        self.layout.addWidget(self.separator_1)
        self.layout.addWidget(self.trending_title)
        self.layout.addWidget(self.trending_list)
        self.layout.addWidget(self.separator_2)
        self.layout.addWidget(self.upcoming_title)
        self.layout.addWidget(self.upcoming_list)

    def _open_login_dialog(self):
        dlg = SteamUserInfoDialog(self)
        dlg.exec()

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

    # NEW: helpers to format deal prices using deals_api data (USD)
    def _format_deal_price(self, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        try:
            v = float(value)
        except Exception:
            return None
        # format with 2 decimals, US style
        return f"${v:,.2f}"

    def _format_deal_line(self, title: str, sale: Optional[float], normal: Optional[float]) -> str:
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
            self.top_live_list.addItem("Brak gier pasujących do filtrowania.")
        else:
            for item in filtered_results:
                players_formatted = self._format_players(item["players"])
                lw_item = QListWidgetItem(f"{players_formatted} - {item['name']}")
                lw_item.setData(Qt.UserRole, item)
                self.top_live_list.addItem(lw_item)

    async def refresh_data(self):
        self.top_live_title.setText("Live Games Count — Ładowanie...")
        self.trending_title.setText("Best Deals — Ładowanie...")
        self.upcoming_title.setText("Best Upcoming Releases — Ładowanie...")
        self.trending_list.clear()
        self.upcoming_list.clear()
        appids = await self._db.get_watchlist_appids()
        all_game_tags = await self._db.get_all_game_tags()
        if not appids:
            self.top_live_title.setText("Live Games Count")
            if self.tags_list_widget.count() == 0:
                await self._populate_tag_checkboxes()
            # Jeśli nie ma appidów, zresetuj tytuły sekcji promocji/nadchodzących
            self.trending_title.setText("Best Deals")
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
                    new_genres = [g for g in (details_result.genres or [])]
                    new_categories = [c for c in (details_result.categories or [])]
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
        self.top_live_title.setText("Live Games Count")
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
                    # Support both object attributes and dict keys, snake_case and camelCase
                    sale = None
                    normal = None
                    title = None
                    appid = None
                    deal_url = None
                    deal_id = None
                    store_id = None
                    store_name = None

                    if isinstance(d, dict):
                        sale = d.get('salePrice') or d.get('sale_price') or d.get('sale')
                        normal = d.get('normalPrice') or d.get('normal_price') or d.get('retailPrice') or d.get('retail_price')
                        title = d.get('title') or d.get('name') or d.get('gameName')
                        appid = d.get('steamAppID') or d.get('steam_app_id') or d.get('appID') or d.get('appid')
                        deal_id = d.get('dealID') or d.get('dealId') or d.get('deal_id')
                        store_id = d.get('storeID') or d.get('storeId') or d.get('store_id')
                        store_name = d.get('storeName') or d.get('store_name') or d.get('store')
                        # try to capture any useful url (deal page or steam link)
                        deal_url = (
                            d.get('steamLink') or d.get('steam_url') or d.get('steamUrl') or
                            d.get('storeURL') or d.get('storeUrl') or d.get('store_link') or
                            d.get('dealURL') or d.get('dealUrl') or d.get('url') or d.get('link') or d.get('store_url')
                        )
                    else:
                        sale = getattr(d, 'salePrice', None) or getattr(d, 'sale_price', None) or getattr(d, 'sale', None)
                        normal = getattr(d, 'normalPrice', None) or getattr(d, 'normal_price', None) or getattr(d, 'retailPrice', None) or getattr(d, 'retail_price', None)
                        title = getattr(d, 'title', None) or getattr(d, 'name', None) or getattr(d, 'gameName', None)
                        appid = getattr(d, 'steamAppID', None) or getattr(d, 'steam_app_id', None) or getattr(d, 'appID', None) or getattr(d, 'appid', None)
                        deal_id = getattr(d, 'dealID', None) or getattr(d, 'dealId', None) or getattr(d, 'deal_id', None)
                        store_id = getattr(d, 'storeID', None) or getattr(d, 'storeId', None) or getattr(d, 'store_id', None)
                        store_name = getattr(d, 'storeName', None) or getattr(d, 'store_name', None) or getattr(d, 'store', None)
                        deal_url = (
                            getattr(d, 'steamLink', None) or getattr(d, 'steam_url', None) or getattr(d, 'steamUrl', None) or
                            getattr(d, 'storeURL', None) or getattr(d, 'storeUrl', None) or getattr(d, 'store_link', None) or
                            getattr(d, 'dealURL', None) or getattr(d, 'dealUrl', None) or getattr(d, 'url', None) or getattr(d, 'link', None) or getattr(d, 'store_url', None)
                        )

                    # If it's not Steam and no direct URL was given but we have a deal id, use CheapShark redirect
                    if not deal_url and deal_id:
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
                    item.setData(Qt.UserRole, {
                        "name": title,
                        "appid": appid_int,
                        "deal_url": deal_url,
                        "deal_id": deal_id,
                        "store_id": store_id,
                        "store_name": store_name,
                    })
                    self.trending_list.addItem(item)
                except Exception:
                    self.trending_list.addItem(str(d))
        try:
            async with SteamStoreClient() as client2:
                upcoming = await client2.get_coming_soon(cc="pl", lang="pl", limit=10)
        except Exception as e:
            print(f"Błąd pobierania nadchodzących: {e}")
            upcoming = []

        # Pobierz szczegóły dla WSZYSTKICH pozycji 'upcoming' i użyj release_date.date z appdetails
        details_by_appid: Dict[int, Any] = {}
        if upcoming:
            try:
                async with SteamStoreClient() as client3:
                    tasks = []
                    appid_list: List[int] = []
                    for it in upcoming:
                        try:
                            aid = int(getattr(it, 'id', 0) or 0)
                            if aid > 0:
                                appid_list.append(aid)
                                tasks.append(client3.get_app_details(aid, cc="pl", lang="pl"))
                        except Exception:
                            continue
                    if tasks:
                        res = await asyncio.gather(*tasks, return_exceptions=True)
                        for aid, r in zip(appid_list, res):
                            if r and not isinstance(r, Exception):
                                details_by_appid[aid] = r
            except Exception:
                pass

        self.upcoming_list.clear()
        if not upcoming:
            self.upcoming_list.addItem("Brak nadchodzących premier.")
        else:
            for item in upcoming:
                name = getattr(item, 'name', 'Unknown')
                appid = getattr(item, 'id', None)
                try:
                    appid_int = int(appid) if appid is not None else None
                    if appid_int is not None and appid_int <= 0:
                        appid_int = None
                except Exception:
                    appid_int = None

                # Prefer date from appdetails
                release_text = ''
                if appid_int is not None:
                    d = details_by_appid.get(appid_int)
                    if d is not None:
                        rd = getattr(d, 'release_date', None)
                        release_text = getattr(rd, 'date', '') if rd else ''
                # Fallback to featured response string
                if not release_text:
                    release_text = getattr(item, 'release_date', None) or getattr(item, 'releaseDate', None) or ''

                price = getattr(item, 'final_price', None) or getattr(item, 'finalPrice', None) or ''
                discount = getattr(item, 'discount_percent', None) or getattr(item, 'discountPercent', None) or ''
                display = f"{name}"
                if release_text:
                    display += f" — premiera: {release_text}"
                if price:
                    display += f" — cena: {price}"
                if discount:
                    display += f" (-{discount}%)"
                lw = QListWidgetItem(display)
                lw.setData(Qt.UserRole, {"name": name, "appid": appid_int})
                self.upcoming_list.addItem(lw)

        # Ustaw tituły końcowe (reset po zakończeniu ładowania obu sekcji)
        self.trending_title.setText("Best Deals")
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

    # NEW: Handlers for Deals and Upcoming lists
    def _on_deal_item_clicked(self, item: 'QListWidgetItem'):
        if not item:
            return
        data = None
        try:
            data = item.data(Qt.UserRole)
        except Exception:
            pass
        if isinstance(data, dict):
            GameDetailDialog(data, self).exec()
        else:
            GameDetailDialog(item.text(), self).exec()

    def _on_upcoming_item_clicked(self, item: 'QListWidgetItem'):
        if not item:
            return
        data = None
        try:
            data = item.data(Qt.UserRole)
        except Exception:
            pass
        if isinstance(data, dict):
            GameDetailDialog(data, self).exec()
        else:
            GameDetailDialog(item.text(), self).exec()