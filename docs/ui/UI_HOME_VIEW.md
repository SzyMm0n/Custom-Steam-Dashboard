# Dokumentacja Home View

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Klasa HomeView](#klasa-homeview)
3. [Struktura UI](#struktura-ui)
4. [Funkcjonalności](#funkcjonalności)
5. [Filtrowanie](#filtrowanie)
6. [Odświeżanie Danych](#odświeżanie-danych)

---

## Przegląd

**Plik:** `app/ui/home_view_server.py`

**HomeView** to główny widok aplikacji wyświetlający:
- 📊 Aktualną liczbę graczy dla obserwowanych gier
- 🔍 Filtrowanie po liczbie graczy i tagach
- 💰 Najlepsze promocje na gry
- 🎮 Nadchodzące premiery

Wszystkie dane są pobierane z serwera backend.

---

## Klasa HomeView

**Klasa:** `HomeView(QWidget)`

### Inicjalizacja

```python
def __init__(self, server_url: Optional[str] = None, parent=None):
    """
    Inicjalizuje widok główny.
    
    Args:
        server_url: URL serwera backend (domyślnie z SERVER_URL env)
        parent: Widget rodzica
    """
    super().__init__(parent)
    
    # Server client
    if server_url is None:
        server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    self._server_client = ServerClient(base_url=server_url)
    
    # Data storage
    self._all_games_data: List[Dict[str, Any]] = []
    self._filtered_games_data: List[Dict[str, Any]] = []
    
    # Filter state
    self._selected_tags: Set[str] = set()
    self._min_players: int = 0
    self._max_players: int = 2000000  # MAX_PLAYERS_SLIDER
    self._search_term: str = ""
    
    # UI setup
    self._init_ui()
    
    # Auto-refresh timer (5 minut)
    self._timer = QTimer(self)
    self._timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
    self._timer.start(300000)  # 300000 ms = 5 minut
    
    # Initial load
    QTimer.singleShot(0, self._start_initial_load)
```

### Stałe

```python
MAX_PLAYERS_SLIDER = 2000000  # Maksymalna wartość slidera liczby graczy
```

---

## Struktura UI

### Layout Główny

```
┌──────────────────────────────────────────────────────────────────┐
│  Home View                                                       │
├────────────────────────────────┬─────────────────────────────────┤
│  LEFT COLUMN (60%)             │  RIGHT COLUMN (40%)             │
│                                │                                 │
│  ┌──────────────────────────┐  │  ┌───────────────────────────┐  │
│  │  Live Games Count        │  │  │  Filtry                   │  │
│  ├──────────────────────────┤  │  ├───────────────────────────┤  │
│  │  [Search: _________]     │  │  │  Zakres graczy:           │  │
│  │  [Odśwież]               │  │  │  Min: [______] Max: [___] │  │
│  ├──────────────────────────┤  │  │  ▓▓▓▓▓▓▓░░░░░ (slider)    │  │
│  │  • CS2: 1,234,567        │  │  │                           │  │
│  │  • Dota 2: 567,890       │  │  │  Tagi:                    │  │
│  │  • PUBG: 234,567         │  │  │  ☑ Action                │  │
│  │  • ...                   │  │  │  ☐ Adventure              │  │
│  └──────────────────────────┘  │  │  ☑ Free to Play          │  │
│                                │  │  ...                      │  │
│  ┌──────────────────────────┐  │  └───────────────────────────┘  │
│  │  Best Deals              │  │                                 │
│  ├──────────────────────────┤  │                                 │
│  │  • Game 1: -75%          │  │                                 │
│  │  • Game 2: -60%          │  │                                 │
│  └──────────────────────────┘  │                                 │
│                                │                                 │
│  ┌──────────────────────────┐  │                                 │
│  │  Upcoming Releases       │  │                                 │
│  ├──────────────────────────┤  │                                 │
│  │  • Game A: 2025-12-01    │  │                                 │
│  │  • Game B: 2025-12-15    │  │                                 │
│  └──────────────────────────┘  │                                 │
└────────────────────────────────┴─────────────────────────────────┘
```

### Komponenty UI

#### 1. **Left Column** (Lewa kolumna - 60%)

##### Live Games Count

```python
def _init_top_live_section(self, layout: QVBoxLayout):
    """
    Tworzy sekcję z listą gier i ich liczbą graczy.
    
    Zawiera:
        - Tytuł "Live Games Count"
        - Pole wyszukiwania (search bar)
        - Przycisk "Odśwież"
        - Lista gier (QListWidget)
    """
    # Tytuł
    self.top_live_title = QLabel("Live Games Count")
    self.top_live_title.setStyleSheet("font-size: 18px; font-weight: bold;")
    
    # Search bar
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Szukaj gry...")
    self.search_input.textChanged.connect(self._on_search_changed)
    
    # Przycisk odśwież
    refresh_btn = QPushButton("Odśwież")
    refresh_btn.clicked.connect(lambda: asyncio.create_task(self.refresh_data()))
    
    # Lista gier
    self.top_live_list = QListWidget()
    self.top_live_list.setAlternatingRowColors(True)
    self.top_live_list.itemDoubleClicked.connect(self._on_game_double_clicked)
```

**Format elementu listy:**
```
Counter-Strike 2 — 1,234,567 graczy
```

##### Best Deals

```python
def _init_deals_section(self, layout: QVBoxLayout):
    """
    Tworzy sekcję z promocjami.
    
    Pokazuje:
        - Tytuł "Best Deals"
        - Lista promocji (QListWidget)
    """
    self.trending_title = QLabel("Best Deals")
    self.trending_title.setStyleSheet("font-size: 16px; font-weight: bold;")
    
    self.trending_list = QListWidget()
    self.trending_list.itemDoubleClicked.connect(self._on_deal_double_clicked)
```

**Format elementu:**
```
Game Name — -75% ($9.99 z $39.99)
```

##### Upcoming Releases

```python
def _init_upcoming_section(self, layout: QVBoxLayout):
    """
    Tworzy sekcję z nadchodzącymi premierami.
    
    Pokazuje:
        - Tytuł "Best Upcoming Releases"
        - Lista premier (QListWidget)
    """
    self.upcoming_title = QLabel("Best Upcoming Releases")
    self.upcoming_title.setStyleSheet("font-size: 16px; font-weight: bold;")
    
    self.upcoming_list = QListWidget()
    self.upcoming_list.itemDoubleClicked.connect(self._on_upcoming_double_clicked)
```

**Format elementu:**
```
Game Name — Premiera: 2025-12-01
```

#### 2. **Right Column** (Prawa kolumna - 40%)

##### Player Count Filters

```python
def _init_player_filter_section(self, layout: QVBoxLayout):
    """
    Tworzy sekcję filtrów liczby graczy.
    
    Zawiera:
        - Pola tekstowe (min/max)
        - Slider z zakresem
        - Przycisk "Zastosuj"
    """
    # Min players
    self.min_input = QLineEdit()
    self.min_input.setValidator(NumberValidator())
    self.min_input.setPlaceholderText("0")
    self.min_input.textChanged.connect(self._on_min_player_changed)
    
    # Max players
    self.max_input = QLineEdit()
    self.max_input.setValidator(NumberValidator())
    self.max_input.setPlaceholderText("2 000 000")
    self.max_input.textChanged.connect(self._on_max_player_changed)
    
    # Slider
    self.player_slider = QSlider(Qt.Orientation.Horizontal)
    self.player_slider.setRange(0, self.MAX_PLAYERS_SLIDER)
    self.player_slider.setValue(self.MAX_PLAYERS_SLIDER)
    self.player_slider.valueChanged.connect(self._on_slider_changed)
    
    # Apply button
    apply_btn = QPushButton("Zastosuj filtry")
    apply_btn.clicked.connect(self._apply_filters)
```

##### Tag Filters

```python
def _init_tag_filter_section(self, layout: QVBoxLayout):
    """
    Tworzy sekcję filtrów tagów.
    
    Zawiera:
        - Scroll area z checkboxami
        - Lista gatunków i kategorii
        - Auto-update po zmianie
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setMaximumHeight(300)
    
    container = QWidget()
    self.tags_layout = QVBoxLayout(container)
    
    # Checkboxy będą dodawane dynamicznie po pobraniu tagów z serwera
    scroll.setWidget(container)
```

---

## Funkcjonalności

### 1. **Wyszukiwanie Gier**

```python
def _on_search_changed(self, text: str):
    """
    Obsługuje zmianę tekstu w polu wyszukiwania.
    
    Filtruje listę gier po nazwie (case-insensitive).
    
    Args:
        text: Tekst wyszukiwania
    """
    self._search_term = text.lower()
    self._apply_filters()
```

**Działanie:**
- Użytkownik wpisuje "counter"
- Lista pokazuje tylko gry zawierające "counter" w nazwie
- Filtr działa real-time (po każdej zmianie tekstu)

### 2. **Filtrowanie po Liczbie Graczy**

```python
def _on_min_player_changed(self, text: str):
    """Aktualizuje minimalną liczbę graczy."""
    try:
        # Usuń spacje (separator tysięcy)
        cleaned = text.replace(" ", "")
        self._min_players = int(cleaned) if cleaned else 0
    except ValueError:
        self._min_players = 0

def _on_max_player_changed(self, text: str):
    """Aktualizuje maksymalną liczbę graczy."""
    try:
        cleaned = text.replace(" ", "")
        self._max_players = int(cleaned) if cleaned else self.MAX_PLAYERS_SLIDER
    except ValueError:
        self._max_players = self.MAX_PLAYERS_SLIDER
```

**Działanie:**
1. Użytkownik wpisuje "100 000" w Min
2. System czyści tekst → "100000"
3. Konwertuje na int → 100000
4. Filtruje gry: `game['current_players'] >= 100000`

### 3. **Filtrowanie po Tagach**

```python
def _on_tag_checkbox_changed(self, tag: str, checked: bool):
    """
    Obsługuje zmianę stanu checkboxa tagu.
    
    Args:
        tag: Nazwa tagu (np. "Action")
        checked: Czy checkbox jest zaznaczony
    """
    if checked:
        self._selected_tags.add(tag)
    else:
        self._selected_tags.discard(tag)
    
    self._apply_filters()
```

**Działanie:**
1. Użytkownik zaznacza "Action" i "Free to Play"
2. `_selected_tags` = {"Action", "Free to Play"}
3. Filtrowane są tylko gry mające **wszystkie** zaznaczone tagi

### 4. **Aplikowanie Filtrów**

```python
def _apply_filters(self):
    """
    Aplikuje wszystkie aktywne filtry do listy gier.
    
    Kolejność filtrowania:
        1. Wyszukiwanie (nazwa gry)
        2. Zakres liczby graczy (min/max)
        3. Tagi (gatunki/kategorie)
    """
    filtered = self._all_games_data.copy()
    
    # 1. Filter by search term
    if self._search_term:
        filtered = [
            g for g in filtered
            if self._search_term in g.get('name', '').lower()
        ]
    
    # 2. Filter by player count
    filtered = [
        g for g in filtered
        if self._min_players <= g.get('current_players', 0) <= self._max_players
    ]
    
    # 3. Filter by tags
    if self._selected_tags:
        filtered = [
            g for g in filtered
            if self._game_has_all_tags(g, self._selected_tags)
        ]
    
    # Update UI
    self._filtered_games_data = filtered
    self._populate_live_games_list(filtered)
```

---

## Odświeżanie Danych

### Automatyczne Odświeżanie (Timer)

```python
# W __init__:
self._timer = QTimer(self)
self._timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
self._timer.start(300000)  # 5 minut
```

### Manualne Odświeżanie (Przycisk)

```python
refresh_btn = QPushButton("Odśwież")
refresh_btn.clicked.connect(lambda: asyncio.create_task(self.refresh_data()))
```

### Główna Metoda Odświeżania

```python
async def refresh_data(self):
    """
    Asynchronicznie odświeża wszystkie dane z serwera.
    
    Pobiera:
        1. Listę gier z watchlisty + liczba graczy
        2. Promocje (best deals)
        3. Nadchodzące premiery
        4. Tagi (gatunki/kategorie) dla wszystkich gier
    
    Kolejność:
        1. Fetch /api/current-players
        2. Fetch /api/games/tags/batch (dla wszystkich appids)
        3. Fetch /api/deals
        4. Fetch /api/coming-soon
        5. Update UI
    """
    try:
        # 1. Get current players from watchlist
        response = await self._server_client.get("/api/current-players")
        games = response.get("games", [])
        
        # 2. Get tags for all games
        appids = [g['appid'] for g in games]
        tags_response = await self._server_client.post(
            "/api/games/tags/batch",
            json={"appids": appids}
        )
        tags_data = tags_response.get("tags", {})
        
        # Merge tags into games
        for game in games:
            appid = game['appid']
            game['tags'] = tags_data.get(str(appid), {})
        
        # 3. Get deals
        deals_response = await self._server_client.get("/api/deals")
        deals = deals_response.get("deals", [])
        
        # 4. Get upcoming
        upcoming_response = await self._server_client.get("/api/coming-soon")
        upcoming = upcoming_response.get("games", [])
        
        # Update data
        self._all_games_data = games
        self._apply_filters()  # Re-apply filters
        
        # Update UI
        self._populate_deals_list(deals)
        self._populate_upcoming_list(upcoming)
        self._populate_tag_checkboxes()  # Update available tags
        
        logger.info(f"Refreshed data: {len(games)} games, {len(deals)} deals, {len(upcoming)} upcoming")
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}", exc_info=True)
```

---

## Interakcje Użytkownika

### 1. **Double Click na Grze**

```python
def _on_game_double_clicked(self, item: QListWidgetItem):
    """
    Otwiera dialog z szczegółami gry.
    
    Args:
        item: Kliknięty element listy
    """
    # Pobierz dane gry z item.data()
    game_data = item.data(Qt.ItemDataRole.UserRole)
    
    # Otwórz dialog
    dialog = GameDetailDialog(game_data, self._server_url, self)
    dialog.exec()
```

### 2. **Double Click na Promocji**

```python
def _on_deal_double_clicked(self, item: QListWidgetItem):
    """
    Otwiera dialog z szczegółami promocji.
    """
    deal_data = item.data(Qt.ItemDataRole.UserRole)
    dialog = GameDetailDialog(deal_data, self._server_url, self)
    dialog.exec()
```

### 3. **Double Click na Premierze**

```python
def _on_upcoming_double_clicked(self, item: QListWidgetItem):
    """
    Otwiera dialog z szczegółami nadchodzącej gry.
    """
    upcoming_data = item.data(Qt.ItemDataRole.UserRole)
    dialog = GameDetailDialog(upcoming_data, self._server_url, self)
    dialog.exec()
```

---

## Formatowanie Danych

### Liczba Graczy

```python
from PySide6.QtCore import QLocale

locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)

# Formatuj liczbę
players = 1234567
formatted = locale.toString(players)  # "1 234 567"

# Wyświetl
text = f"{game_name} — {formatted} graczy"
```

### Ceny (Promocje)

```python
# Deal format:
deal = {
    "title": "Game Name",
    "normal_price": "$39.99",
    "sale_price": "$9.99",
    "savings": "75%"
}

# Display:
text = f"{deal['title']} — -{deal['savings']} ({deal['sale_price']} z {deal['normal_price']})"
```

### Daty (Premiery)

```python
# Upcoming format:
upcoming = {
    "name": "Game Name",
    "release_date": "2025-12-01"
}

# Display:
text = f"{upcoming['name']} — Premiera: {upcoming['release_date']}"
```

---

## Best Practices

### 1. **Asynchroniczne Operacje**

```python
# ✅ Dobre - używaj asyncio
refresh_btn.clicked.connect(lambda: asyncio.create_task(self.refresh_data()))

# ❌ Złe - blokuje UI
refresh_btn.clicked.connect(self.refresh_data_sync)
```

### 2. **Error Handling**

```python
# ✅ Dobre - obsługuj błędy
try:
    await self.refresh_data()
except Exception as e:
    logger.error(f"Error: {e}")
    QMessageBox.warning(self, "Błąd", "Nie można pobrać danych")

# ❌ Złe - ignoruj błędy
await self.refresh_data()  # Może rzucić wyjątek
```

### 3. **Filtrowanie Wydajne**

```python
# ✅ Dobre - filtruj tylko gdy potrzeba
def _on_search_changed(self, text: str):
    self._search_term = text
    self._apply_filters()  # Aplikuj raz na końcu

# ❌ Złe - wielokrotne filtrowanie
def _on_search_changed(self, text: str):
    self._search_term = text
    self._filter_by_search()
    self._filter_by_players()
    self._filter_by_tags()  # 3 razy!
```

---

## Podsumowanie

| Funkcja | Opis |
|---------|------|
| **refresh_data()** | Pobiera dane z serwera (gry, promocje, premiery) |
| **_apply_filters()** | Filtruje listę gier (search, players, tags) |
| **_on_game_double_clicked()** | Otwiera szczegóły gry |
| **Auto-refresh** | Co 5 minut automatycznie |

---

## Następne Kroki

- **Library View**: [UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md)
- **Components**: [UI_COMPONENTS.md](UI_COMPONENTS.md)
- **Main Window**: [UI_MAIN_WINDOW.md](UI_MAIN_WINDOW.md)

