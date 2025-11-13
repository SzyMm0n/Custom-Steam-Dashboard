# Dokumentacja Library View
**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0
## Spis Treści
1. [Przegląd](#przegląd)
2. [Klasa LibraryView](#klasa-libraryview)
3. [Struktura UI](#struktura-ui)
4. [Funkcjonalności](#funkcjonalności)
5. [Przykład Użycia](#przykład-użycia)
---
## Przegląd
**Plik:** `app/ui/library_view_server.py`
**LibraryView** to widok wyświetlający bibliotekę gier Steam użytkownika z czasem gry.
### Funkcjonalności
- ✅ Akceptuje SteamID64, vanity name lub profile URL
- ✅ Automatyczne rozwiązywanie vanity URL na SteamID
- ✅ Wyświetla avatar i nazwę użytkownika
- ✅ Tabela gier z czasem gry (total + ostatnie 2 tygodnie)
- ✅ Sortowanie po kolumnach (nazwa, czas gry)
- ✅ **Wszystkie dane z serwera backend** (nie wymaga API key)
---
## Klasa LibraryView
**Klasa:** `LibraryView(QWidget)`
### Inicjalizacja
```python
def __init__(self, server_url: Optional[str] = None, parent: Optional[QWidget] = None):
    """
    Inicjalizuje widok biblioteki.
    Args:
        server_url: URL serwera backend (domyślnie z SERVER_URL env)
        parent: Widget rodzica
    """
    super().__init__(parent)
    if server_url is None:
        server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    self._server_client = ServerClient(base_url=server_url)
    self._games_data = []  # Przechowuje dane gier dla sortowania
    # Track current sort order dla każdej kolumny
    self._sort_orders = {
        0: Qt.SortOrder.AscendingOrder,   # Nazwa (A-Z)
        1: Qt.SortOrder.DescendingOrder,  # Łączny czas (najwięcej)
        2: Qt.SortOrder.DescendingOrder   # Ostatnie 2 tyg (najwięcej)
    }
    self._init_ui()
```
---
## Struktura UI
### Layout Główny
```
┌──────────────────────────────────────────────────────┐
│  Biblioteka gier                                     │
├──────────────────────────────────────────────────────┤
│  [Avatar] Nazwa Użytkownika                          │
├──────────────────────────────────────────────────────┤
│  SteamID / Vanity / URL:                             │
│  [_____________________________________] [Pobierz]   │
├──────────────────────────────────────────────────────┤
│  Nazwa gry           │  Łącznie │  Ostatnie 2 tyg.   │
│  ────────────────────┼──────────┼─────────────────── │
│  Counter-Strike 2    │  123 h   │  10 h              │
│  Dota 2              │  567 h   │  5 h               │
│  Team Fortress 2     │  89 h    │  0 h               │
│  ...                 │  ...     │  ...               │
└──────────────────────────────────────────────────────┘
```
---
## Funkcjonalności
### 1. **Pobieranie Biblioteki**
```python
async def _fetch_library(self):
    """
    Pobiera bibliotekę użytkownika z serwera.
    Kroki:
        1. Pobierz input (SteamID / vanity / URL)
        2. Resolve vanity URL → SteamID64 (jeśli potrzeba)
        3. GET /api/player-summary/{steamid}
        4. GET /api/owned-games/{steamid}
        5. Update UI (avatar, nazwa, tabela)
    """
    steamid_input = self.steamid_edit.text().strip()
    if not steamid_input:
        QMessageBox.warning(self, "Brak SteamID", "Podaj SteamID, vanity name lub URL profilu")
        return
    try:
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Pobieranie...")
        # 1. Resolve vanity URL (jeśli nie jest SteamID64)
        if not steamid_input.startswith("7656"):
            response = await self._server_client.get(
                f"/api/resolve-vanity/{urllib.parse.quote(steamid_input)}"
            )
            steamid = response["steamid"]
        else:
            steamid = steamid_input
        # 2. Get player summary
        summary = await self._server_client.get(f"/api/player-summary/{steamid}")
        self.persona_lbl.setText(summary.get("personaname", "Nieznany użytkownik"))
        # 3. Get owned games
        games_response = await self._server_client.get(f"/api/owned-games/{steamid}")
        games = games_response.get("games", [])
        # 4. Update table
        self._games_data = games
        self._populate_table(games)
    except Exception as e:
        QMessageBox.critical(self, "Błąd", f"Nie można pobrać biblioteki:\n{str(e)}")
    finally:
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Pobierz")
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
    Returns:
        Sformatowany string (np. "123 h")
    """
    hours = minutes // 60
    return f"{hours} h"
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
- **Components**: [UI_COMPONENTS.md](UI_COMPONENTS.md)
