# Dokumentacja Deals View

**Data aktualizacji:** 2025-11-17  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Klasa DealsView](#klasa-dealsview)
3. [Struktura UI](#struktura-ui)
4. [Funkcjonalności](#funkcjonalności)
5. [Integracja z API](#integracja-z-api)
6. [Przykład użycia](#przykład-użycia)

---

## Przegląd

**Plik:** `app/ui/deals_view_server.py`

**DealsView** to widok do przeglądania i wyszukiwania promocji na gry:
- 💰 Lista najlepszych aktualnych promocji (z IsThereAnyDeal API)
- 🔍 Wyszukiwanie promocji po tytule gry
- 🏷️ Wyświetlanie zniżek i cen
- 🛒 Bezpośrednie linki do sklepów
- 🔄 Automatyczne odświeżanie co 10 minut

Dane są pobierane z serwera backend przez endpointy `/api/deals/*`.

---

## Klasa DealsView

**Klasa:** `DealsView(QWidget)`

### Inicjalizacja

```python
def __init__(self, server_url: Optional[str] = None, parent=None):
    """
    Inicjalizuje widok promocji.
    
    Args:
        server_url: URL serwera backend (domyślnie z SERVER_URL env)
        parent: Widget rodzica
    """
    super().__init__(parent)
    
    # Server client
    self._server_client = ServerClient(server_url)
    
    # Data storage
    self._best_deals = []          # Lista najlepszych promocji
    self._search_results = None    # Wyniki wyszukiwania
    
    self._init_ui()
    
    # Auto-refresh timer (10 minut dla promocji)
    self._refresh_timer = QTimer(self)
    self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
    self._refresh_timer.start(600000)  # 600000 ms = 10 minut
    
    # Initial data load
    asyncio.create_task(self._load_initial_data())
```

### Stałe

```python
DEFAULT_MIN_DISCOUNT = 20  # Minimalna zniżka do wyświetlenia (%)
DEFAULT_LIMIT = 30         # Domyślna liczba wyświetlanych promocji
```

---

## Struktura UI

### Layout Główny

```
┌──────────────────────────────────────────────────────────────────┐
│  Promocje i okazje                                               │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Wyszukaj promocje                                         │  │
│  │  [Wpisz tytuł gry...________________] [Szukaj]             │  │
│  └────────────────────────────────────────────────────────────┘  │
├────────────────────────────┬─────────────────────────────────────┤
│  LEFT COLUMN (50%)         │  RIGHT COLUMN (50%)                 │
│                            │                                     │
│  ┌──────────────────────┐  │  ┌───────────────────────────────┐  │
│  │  Najlepsze okazje    │  │  │  Wyniki wyszukiwania          │  │
│  │  [Odśwież] Min:20%   │  │  │                               │  │
│  ├──────────────────────┤  │  ├───────────────────────────────┤  │
│  │ 🎮 Game Title 1      │  │  │  Wpisz tytuł gry i kliknij    │  │
│  │ 💵 -80% | $9.99      │  │  │  'Szukaj'                     │  │
│  │ 🏪 Steam             │  │  │                               │  │
│  │ ──────────────────   │  │  │                               │  │
│  │ 🎮 Game Title 2      │  │  │                               │  │
│  │ 💵 -75% | $12.49     │  │  │  (lub wyniki wyszukiwania)    │  │
│  │ 🏪 GOG               │  │  │                               │  │
│  │ ──────────────────   │  │  │                               │  │
│  │ 🎮 Game Title 3      │  │  │                               │  │
│  │ 💵 -70% | $14.99     │  │  │                               │  │
│  │ 🏪 Epic Games        │  │  │                               │  │
│  │ ...                  │  │  │                               │  │
│  └──────────────────────┘  │  └───────────────────────────────┘  │
│  Znaleziono 30 promocji    │                                     │
└────────────────────────────┴─────────────────────────────────────┘
```

---

## Funkcjonalności

### 1. **Pobieranie najlepszych promocji**

```python
async def _load_best_deals(self):
    """
    Pobiera najlepsze promocje z serwera.
    
    Endpoint: GET /api/deals/best?limit=30&min_discount=20
    
    Server sprawdza promocje dla gier z watchlist i zwraca
    najlepsze okazje posortowane według zniżki.
    """
    try:
        self._best_deals_status.setText("Ładowanie...")
        self._refresh_best_btn.setEnabled(False)
        
        # Pobierz dane z serwera
        deals = await self._server_client.get_best_deals(
            limit=30,
            min_discount=20
        )
        
        self._best_deals = deals
        self._update_best_deals_list()
        
        if deals:
            self._best_deals_status.setText(f"Znaleziono {len(deals)} promocji")
        else:
            self._best_deals_status.setText("Brak aktywnych promocji")
            
    except Exception as e:
        logger.error(f"Error loading best deals: {e}")
        self._best_deals_status.setText("❌ Błąd ładowania promocji")
    finally:
        self._refresh_best_btn.setEnabled(True)
```

### 2. **Wyświetlanie listy promocji**

```python
def _update_best_deals_list(self):
    """
    Aktualizuje listę najlepszych promocji.
    
    Format elementu:
    🎮 Game Name
    💵 -XX% | $YY.YY (było $ZZ.ZZ)
    🏪 Store Name
    """
    self._best_deals_list.clear()
    
    if not self._best_deals:
        item = QListWidgetItem("Brak promocji")
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self._best_deals_list.addItem(item)
        return
    
    for deal in self._best_deals:
        # Tworzenie sformatowanego tekstu
        game_name = deal.get('game_name', 'Unknown Game')
        discount = deal.get('discount_percent', 0)
        current_price = deal.get('price_new', 0)
        old_price = deal.get('price_old', 0)
        store_name = deal.get('shop_name', 'Unknown Store')
        store_url = deal.get('url', '')
        
        # Format: nazwa + emoji
        text = f"🎮 {game_name}\n"
        text += f"💵 -{discount}% | ${current_price:.2f}"
        
        if old_price > 0:
            text += f" (było ${old_price:.2f})"
        
        text += f"\n🏪 {store_name}"
        
        # Tworzenie itemu
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, store_url)
        
        # Kolorowanie według wysokości zniżki
        if discount >= 75:
            item.setForeground(QColor("#4CAF50"))  # Zielony dla wysokich zniżek
        elif discount >= 50:
            item.setForeground(QColor("#FFC107"))  # Żółty dla średnich
        
        self._best_deals_list.addItem(item)
```

### 3. **Wyszukiwanie gry**

```python
async def _search_deals(self):
    """
    Wyszukuje promocje dla konkretnej gry.
    
    Endpoint: GET /api/deals/search?title={game_title}
    
    Zwraca:
    - Informacje o grze (title, steam_appid)
    - Aktualną cenę i najlepszą ofertę
    - Listę sklepów z cenami
    """
    search_term = self._search_input.text().strip()
    
    if not search_term or len(search_term) < 2:
        self._search_status_label.setText("Wpisz co najmniej 2 znaki")
        return
    
    try:
        self._search_btn.setEnabled(False)
        self._search_btn.setText("Szukam...")
        self._search_status_label.setText("Wyszukiwanie...")
        
        # Szukaj w ITAD API przez serwer
        result = await self._server_client.search_game_deals(search_term)
        
        if not result.get('found', False):
            self._search_status_label.setText(
                f"❌ Nie znaleziono gry '{search_term}'"
            )
            return
        
        # Wyświetl wyniki
        game = result.get('game', {})
        deal = result.get('deal')
        
        self._display_search_results(game, deal)
        
    except Exception as e:
        logger.error(f"Error searching deals: {e}")
        self._search_status_label.setText("❌ Błąd wyszukiwania")
    finally:
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Szukaj")
```

### 4. **Wyświetlanie wyników wyszukiwania**

```python
def _display_search_results(self, game: Dict, deal: Optional[Dict]):
    """
    Wyświetla wyniki wyszukiwania dla konkretnej gry.
    
    Args:
        game: Informacje o grze (title, steam_appid)
        deal: Informacje o promocji (może być None)
    """
    # Wyczyść poprzednie wyniki
    while self._search_results_layout.count():
        item = self._search_results_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    
    # Tytuł gry
    title_label = QLabel(f"🎮 {game.get('title', 'Unknown')}")
    title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
    self._search_results_layout.addWidget(title_label)
    
    # Steam AppID (jeśli dostępny)
    steam_appid = game.get('steam_appid')
    if steam_appid:
        appid_label = QLabel(f"Steam AppID: {steam_appid}")
        appid_label.setStyleSheet("color: gray;")
        self._search_results_layout.addWidget(appid_label)
    
    # Separator
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    self._search_results_layout.addWidget(separator)
    
    # Informacje o promocji
    if deal:
        self._display_deal_info(deal)
    else:
        no_deal_label = QLabel("❌ Brak aktywnych promocji dla tej gry")
        no_deal_label.setStyleSheet("color: gray; font-style: italic;")
        self._search_results_layout.addWidget(no_deal_label)
    
    self._search_results_layout.addStretch()
```

### 5. **Otwieranie linków do sklepów**

```python
def _on_deal_clicked(self, item: QListWidgetItem):
    """
    Obsługa kliknięcia na element promocji.
    Otwiera link do sklepu w przeglądarce.
    """
    store_url = item.data(Qt.ItemDataRole.UserRole)
    
    if store_url:
        try:
            QDesktopServices.openUrl(QUrl(store_url))
            logger.info(f"Opening store URL: {store_url}")
        except Exception as e:
            logger.error(f"Error opening URL: {e}")
```

### 6. **Automatyczne odświeżanie**

```python
async def refresh_data(self):
    """
    Odświeża listę najlepszych promocji.
    Wywoływane automatycznie co 10 minut lub ręcznie przyciskiem.
    
    Nie odświeża wyników wyszukiwania - użytkownik musi
    wyszukać ponownie ręcznie.
    """
    await self._load_best_deals()
```

---

## Integracja z API

### Endpointy używane przez DealsView

#### 1. GET /api/deals/best

Pobiera najlepsze promocje z watchlist.

**Query Parameters:**
- `limit` (int) - liczba promocji (domyślnie 20, max 50)
- `min_discount` (int) - minimalna zniżka w % (domyślnie 20)

**Response:**
```json
{
  "deals": [
    {
      "game_name": "Counter-Strike 2",
      "appid": 730,
      "discount_percent": 80,
      "price_new": 9.99,
      "price_old": 49.99,
      "shop_name": "Steam",
      "url": "https://store.steampowered.com/app/730"
    }
  ],
  "count": 1
}
```

#### 2. GET /api/deals/search

Wyszukuje promocje dla konkretnej gry po tytule.

**Query Parameters:**
- `title` (str) - tytuł gry do wyszukania (min. 2 znaki)

**Response:**
```json
{
  "found": true,
  "game": {
    "title": "Counter-Strike 2",
    "id": "counterstrike2",
    "steam_appid": 730
  },
  "deal": {
    "game_name": "Counter-Strike 2",
    "discount_percent": 0,
    "price_new": 0,
    "price_old": 0,
    "shop_name": "Steam",
    "url": "https://store.steampowered.com/app/730"
  }
}
```

#### 3. GET /api/deals/game/{appid}

Pobiera informacje o promocjach dla konkretnej gry po Steam AppID.

**Path Parameters:**
- `appid` (int) - Steam Application ID

**Response:**
```json
{
  "game": {
    "appid": 730,
    "name": "Counter-Strike 2",
    "current_players": 1234567
  },
  "deal": {
    "game_name": "Counter-Strike 2",
    "discount_percent": 0,
    "price_new": 0,
    "shop_name": "Steam",
    "url": "https://store.steampowered.com/app/730"
  },
  "message": "No active deals found for this game"
}
```

---

## Obsługa błędów

### 1. Brak wyników wyszukiwania

```python
if not result.get('found', False):
    self._search_status_label.setText(
        f"❌ Nie znaleziono gry '{search_term}'"
    )
    # Wyświetl propozycje alternatywne (opcjonalnie)
    return
```

### 2. Błąd sieciowy

```python
try:
    deals = await self._server_client.get_best_deals(...)
except httpx.RequestError as e:
    logger.error(f"Network error: {e}")
    self._best_deals_status.setText("❌ Błąd połączenia z serwerem")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    self._best_deals_status.setText("❌ Wystąpił nieoczekiwany błąd")
```

### 3. Brak aktywnych promocji

```python
if not deals:
    self._best_deals_status.setText("Brak aktywnych promocji")
    # Wyświetl informację w liście
    item = QListWidgetItem("ℹ️ Brak promocji spełniających kryteria")
    item.setFlags(Qt.ItemFlag.NoItemFlags)
    self._best_deals_list.addItem(item)
```

---

## Przykład użycia

### 1. Przeglądanie najlepszych promocji

```python
# W MainWindow
deals_view = DealsView(server_url="http://localhost:8000")

# Użytkownik:
# 1. Otwiera zakładkę "Promocje"
# 2. Widzi listę 30 najlepszych promocji
# 3. Klika na wybraną promocję
# 4. Otwiera się przeglądarka ze stroną sklepu
```

### 2. Wyszukiwanie konkretnej gry

```python
# Użytkownik:
# 1. Wpisuje "cyberpunk" w pole wyszukiwania
# 2. Klika "Szukaj" (lub Enter)
# 3. Widzi wyniki z aktualną ceną
# 4. Może otworzyć link do sklepu

# Aplikacja:
# - Wysyła zapytanie do /api/deals/search?title=cyberpunk
# - Wyświetla informacje o grze i promocji
# - Pokazuje link do najlepszej oferty
```

### 3. Odświeżanie danych

```python
# Automatyczne:
# - Co 10 minut timer wywołuje refresh_data()
# - Aktualizuje listę najlepszych promocji

# Ręczne:
# - Użytkownik klika "Odśwież"
# - Natychmiastowa aktualizacja listy
```

---

## Integracja z ServerClient

```python
# DealsView używa ServerClient do komunikacji z backend

# 1. Uwierzytelnienie (automatyczne)
await self._server_client.authenticate()

# 2. Pobranie najlepszych promocji
deals = await self._server_client.get_best_deals(
    limit=30,
    min_discount=20
)

# 3. Wyszukiwanie gry
result = await self._server_client.search_game_deals("cyberpunk")

# 4. Pobranie promocji dla konkretnej gry
deal_info = await self._server_client.get(f"/api/deals/game/{appid}")
```

---

## Zależności

```python
# PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLineEdit, QFrame
)
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

# Custom
from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style
```

---

## Uwagi implementacyjne

1. **Rate Limiting** - endpoint `/api/deals/best` ma limit 20 żądań/minutę
2. **Caching** - serwer cachuje wyniki z ITAD API, więc częste odświeżanie jest bezpieczne
3. **Watchlist** - promocje są sprawdzane tylko dla gier z watchlist (efektywność)
4. **Link safety** - linki są walidowane przed otwarciem w przeglądarce
5. **Min discount** - można dostosować minimalną zniżkę (aktualnie 20%)
6. **External API** - używa IsThereAnyDeal.com API przez serwer backend

---

## Rozszerzenia (TODO)

- [ ] Filtrowanie po sklepach (Steam, GOG, Epic, etc.)
- [ ] Sortowanie (zniżka, cena, nazwa)
- [ ] Historia cen (wykres zmian ceny w czasie)
- [ ] Wishlist - zapisywanie ulubionych promocji
- [ ] Powiadomienia o nowych promocjach
- [ ] Eksport listy promocji do CSV/JSON

---

**Ostatnia aktualizacja:** 2025-11-17  
**Autor:** Custom Steam Dashboard Team
