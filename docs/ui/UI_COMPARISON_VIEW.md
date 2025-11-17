# Dokumentacja Comparison View

**Data aktualizacji:** 2025-11-17  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Klasa ComparisonView](#klasa-comparisonview)
3. [Struktura UI](#struktura-ui)
4. [Funkcjonalności](#funkcjonalności)
5. [Wizualizacja danych](#wizualizacja-danych)
6. [Przykład użycia](#przykład-użycia)

---

## Przegląd

**Plik:** `app/ui/comparison_view_server.py`

**ComparisonView** to widok umożliwiający porównanie liczby graczy między wieloma grami jednocześnie:
- 📊 Interaktywny wykres liczby graczy w czasie (matplotlib)
- 📈 Dane historyczne z ostatnich 7 dni (konfigurowalny zakres)
- 📋 Tabela statystyk podsumowujących (min, max, średnia, mediana, wahanie)
- 🎮 Wybór gier z listy watchlist
- 🔄 Automatyczne odświeżanie co 5 minut

Wszystkie dane są pobierane z serwera backend przez endpoint `/api/player-history/compare`.

---

## Klasa ComparisonView

**Klasa:** `ComparisonView(QWidget)`

### Inicjalizacja

```python
def __init__(self, server_url: Optional[str] = None, parent=None):
    """
    Inicjalizuje widok porównawczy.
    
    Args:
        server_url: URL serwera backend (domyślnie z SERVER_URL env)
        parent: Widget rodzica
    """
    super().__init__(parent)
    
    # Server client
    self._server_client = ServerClient(server_url)
    
    # Data storage
    self._all_games = []              # Lista wszystkich gier z watchlist
    self._selected_appids = []        # Wybrane appid do porównania
    self._history_data = {}           # Dane historyczne dla wybranych gier
    self._selected_time_range = "7d"  # Zakres czasu (1h, 3h, 6h, 12h, 1d, 3d, 7d)
    
    self._init_ui()
    
    # Auto-refresh timer (5 minut)
    self._refresh_timer = QTimer(self)
    self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
    self._refresh_timer.start(300000)  # 300000 ms = 5 minut
    
    # Initial data load
    asyncio.create_task(self._load_games())
```

### Zakresy czasu

```python
TIME_RANGES = {
    "1h": 0.04,   # 1 godzina w dniach
    "3h": 0.125,  # 3 godziny
    "6h": 0.25,   # 6 godzin
    "12h": 0.5,   # 12 godzin
    "1d": 1,      # 1 dzień
    "3d": 3,      # 3 dni
    "7d": 7       # 7 dni (domyślne)
}
```

---

## Struktura UI

### Layout Główny

```
┌──────────────────────────────────────────────────────────────────┐
│  Porównanie danych graczy                                        │
├────────────────────────────┬─────────────────────────────────────┤
│  LEFT PANEL                │  RIGHT PANEL (Controls)             │
│                            │                                     │
│  ┌──────────────────────┐  │  ┌───────────────────────────────┐  │
│  │  Wybierz gry do      │  │  │  Zakres czasu: [7d ▼]         │  │
│  │  porównania          │  │  │  [Porównaj wybrane]           │  │
│  ├──────────────────────┤  │  │  [Wybierz TOP 5]              │  │
│  │  ☑ Counter-Strike 2  │  │  │  [Wyczyść wybór]              │  │
│  │  ☑ Dota 2            │  │  │  [Odśwież dane]               │  │
│  │  ☐ Team Fortress 2   │  │  └───────────────────────────────┘  │
│  │  ☐ PUBG              │  │                                     │
│  │  ☐ Apex Legends      │  │                                     │
│  │  ...                 │  │                                     │
│  └──────────────────────┘  │                                     │
└────────────────────────────┴─────────────────────────────────────┘
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Wykres liczby graczy (7 dni)                              │  │
│  │                                                            │  │
│  │    [Interaktywny wykres matplotlib]                        │  │
│  │    - Linie dla każdej wybranej gry                         │  │
│  │    - Legenda z nazwami gier                                │  │
│  │    - Hover tooltip z dokładnymi wartościami                │  │
│  │    - Siatka i formatowanie osi                             │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Statystyki podsumowujące                                  │  │
│  ├──────────┬──────────┬──────────┬──────────┬─────────┬──────┤  │
│  │ Gra      │ Minimum  │ Maksimum │ Średnia  │ Mediana │ Wah. │  │
│  ├──────────┼──────────┼──────────┼──────────┼─────────┼──────┤  │
│  │ CS2      │ 800,000  │ 1,500,000│ 1,200,000│1,180,000│ 87%  │  │
│  │ Dota 2   │ 400,000  │ 600,000  │ 500,000  │ 495,000 │ 50%. │  │
│  └──────────┴──────────┴──────────┴──────────┴─────────┴──────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Funkcjonalności

### 1. **Wybór gier do porównania**

```python
def _on_selection_changed(self):
    """
    Obsługa zmiany wyboru gier.
    Automatycznie aktualizuje listę wybranych appid.
    """
    selected_items = self._game_list.selectedItems()
    self._selected_appids = []
    
    for item in selected_items:
        # Ekstrahuj appid z danych item
        appid = item.data(Qt.ItemDataRole.UserRole)
        if appid:
            self._selected_appids.append(appid)
    
    logger.info(f"Selected {len(self._selected_appids)} games for comparison")
```

**Funkcje pomocnicze:**

- **Wybierz TOP 5** - automatycznie zaznacza 5 najpopularniejszych gier
- **Wyczyść wybór** - odznacza wszystkie gry

### 2. **Wybór zakresu czasu**

```python
def _on_time_range_changed(self, time_range: str):
    """
    Obsługa zmiany zakresu czasu.
    
    Args:
        time_range: Wybrany zakres (1h, 3h, 6h, 12h, 1d, 3d, 7d)
    """
    self._selected_time_range = time_range
    logger.info(f"Time range changed to: {time_range}")
    
    # Automatycznie odśwież dane dla nowego zakresu
    if self._selected_appids:
        asyncio.create_task(self._load_comparison())
```

### 3. **Pobieranie danych historycznych**

```python
async def _load_comparison(self):
    """
    Pobiera dane historyczne dla wybranych gier z serwera.
    
    Endpoint: POST /api/player-history/compare
    Body: {"appids": [730, 570, ...]}
    Params: ?days=7&limit=1000
    """
    if not self._selected_appids:
        logger.warning("No games selected for comparison")
        return
    
    try:
        self._compare_btn.setEnabled(False)
        self._compare_btn.setText("Ładowanie...")
        
        # Konwersja zakresu czasu na dni
        time_range_days = {
            "1h": 0.04, "3h": 0.125, "6h": 0.25, "12h": 0.5,
            "1d": 1, "3d": 3, "7d": 7
        }
        days = time_range_days.get(self._selected_time_range, 7)
        
        # Pobierz dane z serwera
        response = await self._server_client.post(
            "/api/player-history/compare",
            json={"appids": self._selected_appids},
            params={"days": days, "limit": 1000}
        )
        
        self._history_data = response.get("games", {})
        
        # Aktualizuj wykres i tabelę
        self._update_chart()
        self._update_statistics()
        
    except Exception as e:
        logger.error(f"Error loading comparison data: {e}")
    finally:
        self._compare_btn.setEnabled(True)
        self._compare_btn.setText("Porównaj wybrane")
```

### 4. **Wizualizacja wykresu**

```python
def _update_chart(self):
    """
    Aktualizuje wykres matplotlib z danymi historycznymi.
    
    Features:
    - Różne kolory dla każdej gry
    - Legenda z nazwami gier
    - Formatowanie osi (daty, liczby graczy)
    - Siatka dla lepszej czytelności
    - Hover tooltip z dokładnymi wartościami
    """
    self._ax.clear()
    
    if not self._history_data:
        self._ax.text(0.5, 0.5, 'Brak danych', 
                     ha='center', va='center', transform=self._ax.transAxes)
        self._canvas.draw()
        return
    
    # Rysuj linię dla każdej gry
    for appid, game_data in self._history_data.items():
        name = game_data.get("name", f"Game {appid}")
        history = game_data.get("history", [])
        
        if not history:
            continue
        
        # Konwertuj timestamp na datetime
        timestamps = [datetime.fromtimestamp(h['time_stamp']) for h in history]
        player_counts = [h['player_count'] for h in history]
        
        # Rysuj linię
        self._ax.plot(timestamps, player_counts, marker='o', 
                     markersize=3, label=name, linewidth=2)
    
    # Formatowanie osi X (daty)
    self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m %H:%M'))
    self._ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    
    # Formatowanie osi Y (liczby graczy)
    self._ax.yaxis.set_major_formatter(
        lambda x, pos: f'{int(x):,}'.replace(',', ' ')
    )
    
    # Etykiety i siatka
    self._ax.set_xlabel('Data i godzina')
    self._ax.set_ylabel('Liczba graczy')
    self._ax.legend(loc='best')
    self._ax.grid(True, alpha=0.3)
    
    # Obróć etykiety osi X
    self._figure.autofmt_xdate()
    
    self._canvas.draw()
```

### 5. **Hover tooltip na wykresie**

```python
def _on_hover(self, event):
    """
    Wyświetla tooltip z dokładnymi wartościami przy najechaniu myszą.
    """
    if not event.inaxes:
        self._hover_annotation.set_visible(False)
        self._canvas.draw_idle()
        return
    
    # Znajdź najbliższy punkt na wykresie
    # ... implementacja szukania najbliższego punktu
    
    # Pokaż tooltip
    self._hover_annotation.xy = (x, y)
    self._hover_annotation.set_text(f"{game_name}\n{player_count:,} graczy\n{timestamp}")
    self._hover_annotation.set_visible(True)
    self._canvas.draw_idle()
```

### 6. **Tabela statystyk**

```python
def _update_statistics(self):
    """
    Aktualizuje tabelę statystyk podsumowujących.
    
    Obliczane wartości:
    - Minimum - najmniejsza liczba graczy w okresie
    - Maksimum - największa liczba graczy w okresie
    - Średnia - średnia arytmetyczna
    - Mediana - wartość środkowa
    - Wahanie % - (max - min) / min * 100
    """
    self._stats_table.setRowCount(0)
    
    if not self._history_data:
        return
    
    for row, (appid, game_data) in enumerate(self._history_data.items()):
        name = game_data.get("name", f"Game {appid}")
        history = game_data.get("history", [])
        
        if not history:
            continue
        
        # Ekstrahuj liczby graczy
        player_counts = [h['player_count'] for h in history]
        
        # Oblicz statystyki
        min_players = min(player_counts)
        max_players = max(player_counts)
        avg_players = sum(player_counts) / len(player_counts)
        median_players = sorted(player_counts)[len(player_counts) // 2]
        volatility = ((max_players - min_players) / min_players * 100) if min_players > 0 else 0
        
        # Dodaj wiersz do tabeli
        self._stats_table.insertRow(row)
        self._stats_table.setItem(row, 0, QTableWidgetItem(name))
        self._stats_table.setItem(row, 1, QTableWidgetItem(f"{min_players:,}"))
        self._stats_table.setItem(row, 2, QTableWidgetItem(f"{max_players:,}"))
        self._stats_table.setItem(row, 3, QTableWidgetItem(f"{int(avg_players):,}"))
        self._stats_table.setItem(row, 4, QTableWidgetItem(f"{int(median_players):,}"))
        self._stats_table.setItem(row, 5, QTableWidgetItem(f"{volatility:.1f}%"))
```

### 7. **Automatyczne odświeżanie**

```python
async def refresh_data(self):
    """
    Odświeża dane dla aktualnie wybranych gier.
    Wywoływane automatycznie co 5 minut lub ręcznie przyciskiem.
    """
    if self._selected_appids:
        await self._load_comparison()
    else:
        await self._load_games()
```

---

## Wizualizacja danych

### Format danych z serwera

**Endpoint:** `POST /api/player-history/compare`

**Request Body:**
```json
{
  "appids": [730, 570, 440]
}
```

**Query Parameters:**
- `days` (float) - liczba dni historii (0.04 = 1h, 7 = 7 dni)
- `limit` (int) - maksymalna liczba rekordów na grę (10-5000)

**Response:**
```json
{
  "games": {
    "730": {
      "name": "Counter-Strike 2",
      "history": [
        {
          "time_stamp": 1699876543,
          "player_count": 1234567
        },
        {
          "time_stamp": 1699880143,
          "player_count": 1240000
        }
      ]
    },
    "570": {
      "name": "Dota 2",
      "history": [...]
    }
  }
}
```

### Konfiguracja wykresu matplotlib

```python
# Kolory linii (automatyczne z color cycle)
self._ax.set_prop_cycle(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])

# Formatowanie osi
self._ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m %H:%M'))
self._ax.yaxis.set_major_formatter(lambda x, pos: f'{int(x):,}'.replace(',', ' '))

# Siatka
self._ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
```

---

## Przykład użycia

### 1. Podstawowe porównanie

```python
# W MainWindow
comparison_view = ComparisonView(server_url="http://localhost:8000")

# Użytkownik:
# 1. Zaznacza gry z listy (np. CS2, Dota 2)
# 2. Wybiera zakres czasu (np. 7d)
# 3. Klika "Porównaj wybrane"

# Aplikacja:
# - Pobiera dane z /api/player-history/compare
# - Rysuje wykres z 2 liniami
# - Wyświetla tabelę statystyk
```

### 2. Szybkie porównanie TOP 5

```python
# Użytkownik klika "Wybierz TOP 5"
# - Automatycznie zaznacza 5 najpopularniejszych gier
# - Można od razu kliknąć "Porównaj wybrane"
```

### 3. Analiza krótkoterminowa

```python
# Użytkownik:
# - Wybiera zakres "1h" lub "3h" z dropdown
# - Porównuje zmiany liczby graczy w ciągu ostatnich godzin

# Przydatne dla:
# - Analizy wzrostów podczas premier
# - Monitorowania spadków po aktualizacjach
# - Identyfikacji wzorców daily (np. peak hours)
```

---

## Integracja z ServerClient

```python
# ComparisonView używa ServerClient do komunikacji z backend

# 1. Uwierzytelnienie (automatyczne)
await self._server_client.authenticate()

# 2. Pobranie listy gier
games = await self._server_client.get_current_players()

# 3. Pobranie danych historycznych
response = await self._server_client.post(
    "/api/player-history/compare",
    json={"appids": [730, 570]},
    params={"days": 7, "limit": 1000}
)
```

---

## Error Handling

```python
try:
    await self._load_comparison()
except Exception as e:
    logger.error(f"Error loading comparison: {e}")
    # Wyświetl komunikat błędu na wykresie
    self._ax.clear()
    self._ax.text(0.5, 0.5, f'Błąd: {str(e)}',
                 ha='center', va='center',
                 transform=self._ax.transAxes)
    self._canvas.draw()
```

---

## Zależności

```python
# PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QGroupBox, QTableWidget, QComboBox
)

# Matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Custom
from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style
```

---

## Uwagi implementacyjne

1. **Wydajność** - wykres jest aktualizowany tylko gdy zmienią się dane lub wybór
2. **Memory management** - stare dane są czyszczone przy każdej aktualizacji
3. **Responsywność** - wszystkie operacje I/O są asynchroniczne
4. **Hover tooltip** - wymaga subskrypcji eventu motion_notify_event matplotlib
5. **Auto-refresh** - można wyłączyć przez ustawienie timera na 0

---

**Ostatnia aktualizacja:** 2025-11-17  
**Autor:** Custom Steam Dashboard Team
