# Dokumentacja Stylów UI

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Przegląd

**Plik:** `app/ui/styles.py`

Moduł zawiera funkcję `apply_style()` do aplikowania ciemnego motywu Qt.

---

## apply_style()

```python
def apply_style(widget: QWidget) -> None:
    """
    Aplikuje ciemny motyw Qt do widgetu.
    
    Args:
        widget: Widget do wystylizowania
    """
    widget.setStyleSheet("""
        /* Base colors */
        QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555555;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        
        /* Input fields */
        QLineEdit, QTextEdit {
            background-color: #3a3a3a;
            border: 1px solid #555555;
            padding: 3px;
            border-radius: 3px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #0078d7;
        }
        
        /* Lists */
        QListWidget, QTableWidget {
            background-color: #2b2b2b;
            border: 1px solid #555555;
            alternate-background-color: #323232;
        }
        QListWidget::item:hover, QTableWidget::item:hover {
            background-color: #3a3a3a;
        }
        QListWidget::item:selected, QTableWidget::item:selected {
            background-color: #0078d7;
        }
        
        /* Headers */
        QHeaderView::section {
            background-color: #3a3a3a;
            border: none;
            padding: 5px;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background: #2b2b2b;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background: #555555;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #666666;
        }
        
        /* GroupBox */
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 3px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
```

---

## Przykład Użycia

```python
from app.ui.styles import apply_style
from PySide6.QtWidgets import QWidget

widget = QWidget()
apply_style(widget)  # Aplikuje ciemny motyw
```

---

## Kolory

| Element | Kolor | Hex |
|---------|-------|-----|
| Tło główne | Ciemny szary | `#2b2b2b` |
| Tło elementów | Średni szary | `#3a3a3a` |
| Tekst | Jasny szary | `#e0e0e0` |
| Obramowania | Szary | `#555555` |
| Akcent (hover) | Jaśniejszy szary | `#4a4a4a` |
| Zaznaczenie | Niebieski | `#0078d7` |

---

## Następne Kroki

- **Components**: [UI_COMPONENTS.md](UI_COMPONENTS.md)
- **Home View**: [UI_HOME_VIEW.md](UI_HOME_VIEW.md)
# Dokumentacja Library View

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Przegląd

**Plik:** `app/ui/library_view_server.py`

**LibraryView** wyświetla bibliotekę gier Steam użytkownika z czasem gry.

### Funkcjonalności

- ✅ Akceptuje SteamID64, vanity name lub profile URL
- ✅ Automatyczne rozwiązywanie vanity URL na SteamID
- ✅ Wyświetla avatar i nazwę użytkownika
- ✅ Tabela gier z czasem gry (total + 2 weeks)
- ✅ Sortowanie po kolumnach
- ✅ **Wszystkie dane z serwera backend** (nie wymaga API key)

---

## Klasa LibraryView

```python
class LibraryView(QWidget):
    """Widok biblioteki Steam."""
    
    def __init__(self, server_url: Optional[str] = None, parent=None):
        super().__init__(parent)
        if server_url is None:
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self._server_client = ServerClient(base_url=server_url)
        self._games_data = []
        self._init_ui()
```

---

## Struktura UI

```
┌──────────────────────────────────────────────┐
│  Biblioteka gier                             │
├──────────────────────────────────────────────┤
│  [Avatar] Nazwa Użytkownika                  │
├──────────────────────────────────────────────┤
│  SteamID / Vanity / URL:                     │
│  [_____________________________] [Pobierz]   │
├──────────────────────────────────────────────┤
│  Nazwa gry         │  Łącznie │  Ostatnie 2 tyg│
│  ──────────────────┼──────────┼────────────────│
│  Counter-Strike 2  │  123 h   │  10 h          │
│  Dota 2            │  567 h   │  5 h           │
│  ...               │  ...     │  ...           │
└──────────────────────────────────────────────┘
```

---

## Główne Metody

### 1. **Pobierz Bibliotekę**

```python
async def _fetch_library(self):
    """
    Pobiera bibliotekę użytkownika z serwera.
    
    Kroki:
        1. Resolve vanity URL → SteamID64 (jeśli potrzeba)
        2. GET /api/player-summary/{steamid}
        3. GET /api/owned-games/{steamid}
        4. Update UI (avatar, nazwa, tabela)
    """
    steamid_input = self.steamid_edit.text().strip()
    
    # 1. Resolve vanity URL
    if not steamid_input.startswith("7656"):  # Not SteamID64
        response = await self._server_client.get(
            f"/api/resolve-vanity/{steamid_input}"
        )
        steamid = response["steamid"]
    else:
        steamid = steamid_input
    
    # 2. Get player summary
    summary = await self._server_client.get(f"/api/player-summary/{steamid}")
    self.persona_lbl.setText(summary["personaname"])
    self._load_avatar(summary["avatarfull"])
    
    # 3. Get owned games
    games_response = await self._server_client.get(f"/api/owned-games/{steamid}")
    games = games_response["games"]
    
    # 4. Update table
    self._populate_table(games)
```

### 2. **Sortowanie Tabeli**

```python
def _on_header_clicked(self, logical_index: int):
    """
    Sortuje tabelę po klikniętej kolumnie.
    
    Toggle: Ascending ↔ Descending
    """
    current_order = self._sort_orders[logical_index]
    new_order = (Qt.SortOrder.Descending 
                 if current_order == Qt.SortOrder.AscendingOrder 
                 else Qt.SortOrder.AscendingOrder)
    
    self._sort_orders[logical_index] = new_order
    self._sort_table_by_column(logical_index, new_order)
```

### 3. **Formatowanie Czasu**

```python
def _minutes_to_hours(self, minutes: int) -> str:
    """
    Konwertuje minuty na godziny.
    
    Args:
        minutes: Czas w minutach
    
    Returns:
        "123 h" lub "0 h"
    """
    return f"{minutes // 60} h"
```

---

## Przykład Użycia

```python
from app.ui.library_view_server import LibraryView

# Utwórz widok
library_view = LibraryView(server_url="http://localhost:8000")

# Użytkownik wpisuje:
# - "76561198012345678" (SteamID64)
# - "gaben" (vanity name)
# - "https://steamcommunity.com/id/gaben" (profile URL)

# Kliknięcie "Pobierz" wywołuje:
asyncio.create_task(library_view._fetch_library())
```

---

## Następne Kroki

- **Home View**: [UI_HOME_VIEW.md](UI_HOME_VIEW.md)
- **Main Window**: [UI_MAIN_WINDOW.md](UI_MAIN_WINDOW.md)

