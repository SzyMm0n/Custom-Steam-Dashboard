# Dokumentacja User Info Dialog

**Data aktualizacji:** 2025-11-17  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Klasa SteamUserInfoDialog](#klasa-steamuserinfodialog)
3. [Struktura UI](#struktura-ui)
4. [Funkcjonalności](#funkcjonalności)
5. [Rozwiązywanie Steam ID](#rozwiązywanie-steam-id)
6. [Przykład użycia](#przykład-użycia)

---

## Przegląd

**Plik:** `app/ui/user_info_dialog_server.py`

**SteamUserInfoDialog** to okno dialogowe do wyświetlania profilu użytkownika Steam:
- 👤 Profil użytkownika z avatarem i nazwą
- 🎮 Biblioteka gier z czasem gry
- 📊 Statystyki (łączny czas, ostatnie 2 tygodnie)
- 🔍 Rozwiązywanie różnych formatów Steam ID
- 🇵🇱 Pełne wsparcie dla polskich znaków

Dialog jest używany zarówno przez LibraryView jak i może być wywoływany jako standalone.

---

## Klasa SteamUserInfoDialog

**Klasa:** `SteamUserInfoDialog(QDialog)`

### Inicjalizacja

```python
def __init__(self, server_url: Optional[str] = None, parent=None):
    """
    Inicjalizuje dialog informacji użytkownika Steam.
    
    Args:
        server_url: URL serwera backend (domyślnie z SERVER_URL env)
        parent: Widget rodzica
    """
    super().__init__(parent)
    
    if server_url is None:
        server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    
    self._server_client = ServerClient(base_url=server_url)
    
    self.setWindowTitle("Informacje o użytkowniku Steam")
    self.setMinimumSize(800, 560)
    
    # Ustawienie polskiego locale
    try:
        self.setLocale(QLocale(QLocale.Language.Polish, QLocale.Country.Poland))
    except Exception:
        pass
    
    self._init_ui()
```

### Wybór czcionki z polskimi znakami

```python
def _choose_polish_font(self) -> QFont:
    """
    Wybiera czcionkę obsługującą polskie znaki.
    
    Kolejność priorytetu:
    1. Segoe UI (Windows)
    2. Noto Sans (Cross-platform)
    3. DejaVu Sans (Linux)
    4. Arial Unicode MS
    5. Arial (fallback)
    """
    candidates = [
        "Segoe UI",
        "Noto Sans",
        "DejaVu Sans",
        "Arial Unicode MS",
        "Arial"
    ]
    
    available = set(QFontDatabase.families())
    
    for font_name in candidates:
        if font_name in available:
            return QFont(font_name)
    
    return QFont()  # System default
```

---

## Struktura UI

### Layout dialogu

```
┌──────────────────────────────────────────────────────────────────┐
│  Informacje o użytkowniku Steam                            [X]   │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────┐                                                      │
│  │ Avatar │  Nazwa Użytkownika                                   │
│  │ 64x64  │  (pogrubiona czcionka)                               │
│  └────────┘                                                      │
├──────────────────────────────────────────────────────────────────┤
│  SteamID / URL / vanity:                                         │
│  [Wpisz SteamID64, vanity name lub URL profilu_____________]     │
├──────────────────────────────────────────────────────────────────┤
│  [Pobierz dane]                                      [Zamknij]   │
├──────────────────────────────────────────────────────────────────┤
│  Status: Załadowano gier: 150                                    │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Nazwa gry              │ Łączna liczba │ Ostatnie 2 tyg.   │  │
│  │                        │ godzin        │ (h)               │  │
│  ├────────────────────────┼───────────────┼───────────────────┤  │
│  │ Counter-Strike 2       │ 1,234.5       │ 45.2              │  │
│  │ Dota 2                 │ 567.8         │ 12.5              │  │
│  │ Team Fortress 2        │ 234.1         │ 0.0               │  │
│  │ Cyberpunk 2077         │ 89.3          │ 5.7               │  │
│  │ The Witcher 3          │ 78.9          │ 0.0               │  │
│  │ ...                    │ ...           │ ...               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           (posortowane malejąco po łącznym       │
│                            czasie gry)                           │
└──────────────────────────────────────────────────────────────────┘
```

### Komponenty UI

1. **Nagłówek profilu**
   - Avatar (64x64 px)
   - Nazwa użytkownika (pogrubiona)

2. **Pole wejściowe**
   - QLineEdit z placeholder text
   - Akceptuje: SteamID64, vanity name, URL profilu

3. **Przyciski akcji**
   - "Pobierz dane" - rozpoczyna pobieranie
   - "Zamknij" - zamyka dialog

4. **Status**
   - QLabel z informacją o stanie operacji

5. **Tabela gier**
   - 3 kolumny (nazwa, łączny czas, ostatnie 2 tyg.)
   - Sortowanie po łącznym czasie (malejąco)
   - Alternating row colors
   - Read-only, selection by rows

---

## Funkcjonalności

### 1. **Rozwiązywanie Steam ID**

```python
async def _resolve_steam_id(self, raw_input: str) -> Optional[str]:
    """
    Rozwiązuje różne formaty Steam ID na Steam ID64.
    
    Akceptowane formaty:
    - SteamID64: 76561198012345678 (17 cyfr)
    - Vanity name: gaben
    - Profile URL: https://steamcommunity.com/id/gaben
    - Full URL: https://steamcommunity.com/profiles/76561198012345678
    
    Returns:
        Steam ID64 (string) lub None jeśli błąd
    """
    # Sprawdź czy to już SteamID64
    if raw_input.isdigit() and len(raw_input) == 17:
        return raw_input
    
    # Spróbuj rozwiązać przez serwer
    try:
        steamid = await self._server_client.resolve_vanity_url(raw_input)
        return steamid
    except Exception as e:
        logger.error(f"Error resolving Steam ID: {e}")
        return None
```

**Endpoint używany:** `GET /api/resolve-vanity/{vanity_url:path}`

### 2. **Pobieranie danych użytkownika**

```python
async def _on_fetch_clicked(self) -> None:
    """
    Pobiera dane użytkownika z serwera.
    
    Kroki:
    1. Walidacja input (min. 1 znak)
    2. Rozwiązanie Steam ID
    3. Pobranie profilu (GET /api/player-summary/{steamid})
    4. Pobranie biblioteki (GET /api/owned-games/{steamid})
    5. Pobranie ostatnio granych (GET /api/recently-played/{steamid})
    6. Połączenie danych i wyświetlenie
    """
    raw_input = self.steamid_input.text().strip()
    
    if not raw_input:
        QMessageBox.warning(
            self,
            "Brak SteamID",
            "Podaj SteamID64, vanity lub URL profilu."
        )
        return
    
    # Disable UI podczas pobierania
    self.fetch_btn.setEnabled(False)
    self.status_lbl.setText("Rozwiązywanie identyfikatora...")
    self.persona_lbl.setText("Ładowanie...")
    self.avatar_lbl.clear()
    self.table.setRowCount(0)
    
    # 1. Rozwiąż Steam ID
    steamid = await self._resolve_steam_id(raw_input)
    
    if not steamid:
        self.status_lbl.setText(
            "Nie udało się rozwiązać identyfikatora Steam. "
            "Sprawdź poprawność danych."
        )
        self.fetch_btn.setEnabled(True)
        return
    
    try:
        # 2. Pobierz profil
        self.status_lbl.setText("Pobieranie profilu...")
        summary = await self._server_client.get_player_summary(steamid)
        
        # 3. Pobierz bibliotekę
        self.status_lbl.setText("Pobieranie biblioteki...")
        owned_games = await self._server_client.get_owned_games(steamid)
        
        # 4. Pobierz ostatnio grane
        recently_played = await self._server_client.get_recently_played(steamid)
        
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        self.status_lbl.setText(
            f"Błąd: {e}\n\n"
            f"Upewnij się, że serwer działa na {self._server_client.base_url}"
        )
        self.fetch_btn.setEnabled(True)
        return
    
    # 5. Aktualizuj profil
    self._update_profile(summary)
    
    # 6. Aktualizuj tabelę
    self._populate_games_table(owned_games, recently_played)
    
    self.status_lbl.setText(f"Załadowano gier: {len(owned_games)}")
    self.fetch_btn.setEnabled(True)
```

### 3. **Aktualizacja profilu**

```python
def _update_profile(self, summary: Dict[str, Any]) -> None:
    """
    Aktualizuje wyświetlanie profilu użytkownika.
    
    Args:
        summary: Dane z /api/player-summary/{steamid}
    """
    if summary:
        # Nazwa użytkownika
        persona_name = summary.get('personaname', 'Nieznany użytkownik')
        self.persona_lbl.setText(persona_name)
        
        # Avatar
        avatar_url = (
            summary.get('avatarfull') or
            summary.get('avatarmedium') or
            summary.get('avatar')
        )
        
        if avatar_url:
            asyncio.create_task(self._load_avatar(avatar_url))
    else:
        self.persona_lbl.setText("(brak danych profilu)")
```

### 4. **Ładowanie avatara**

```python
async def _load_avatar(self, url: str) -> None:
    """
    Asynchronicznie pobiera i wyświetla avatar użytkownika.
    
    Args:
        url: URL do obrazka avatara (Steam CDN)
    """
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.avatar_lbl.setPixmap(pixmap)
                
    except Exception as e:
        logger.error(f"Error loading avatar: {e}")
```

### 5. **Wypełnianie tabeli gier**

```python
def _populate_games_table(
    self,
    owned_games: List[Dict],
    recently_played: List[Dict]
) -> None:
    """
    Wypełnia tabelę grami użytkownika.
    
    Args:
        owned_games: Lista posiadanych gier
        recently_played: Lista ostatnio granych gier
    """
    # Mapowanie appid -> playtime_2weeks
    recent_map = {
        g.get('appid'): g.get('playtime_2weeks', 0)
        for g in recently_played
        if g.get('appid')
    }
    
    # Sortowanie po łącznym czasie gry (malejąco)
    owned_sorted = sorted(
        owned_games,
        key=lambda g: g.get('playtime_forever', 0),
        reverse=True
    )
    
    # Wypełnij tabelę
    self.table.setRowCount(len(owned_sorted))
    
    for row, game in enumerate(owned_sorted):
        # Nazwa gry
        name = game.get('name', f"AppID {game.get('appid', 'Unknown')}")
        name_item = QTableWidgetItem(name)
        name_item.setFont(self.font())
        
        # Czasy gry (minuty -> godziny)
        total_min = game.get('playtime_forever', 0)
        last2w_min = recent_map.get(
            game.get('appid'),
            game.get('playtime_2weeks', 0)
        ) or 0
        
        # Korekta: jeśli last2w > total, ustaw total = last2w
        if total_min < last2w_min:
            total_min = last2w_min
        
        total_h = total_min / 60.0
        last2w_h = last2w_min / 60.0
        
        # Elementy tabeli
        total_item = QTableWidgetItem(f"{total_h:.1f}")
        last_item = QTableWidgetItem(f"{last2w_h:.1f}")
        
        # Wyrównanie do prawej
        total_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        last_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        
        # Dodaj do tabeli
        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, total_item)
        self.table.setItem(row, 2, last_item)
    
    self.table.resizeColumnsToContents()
```

---

## Rozwiązywanie Steam ID

### Obsługiwane formaty

| Format | Przykład | Opis |
|--------|----------|------|
| **SteamID64** | `76561198012345678` | 17-cyfrowy identyfikator |
| **Vanity Name** | `gaben` | Niestandardowa nazwa profilu |
| **Vanity URL** | `https://steamcommunity.com/id/gaben` | Pełny URL z vanity |
| **Profile URL** | `https://steamcommunity.com/profiles/76561198012345678` | Pełny URL z SteamID64 |

### Proces rozwiązywania

```
┌─────────────────────┐
│  User Input         │
│  "gaben"            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Is it SteamID64?   │  ──YES──> Use directly
│  (17 digits)        │
└──────┬──────────────┘
       │ NO
       ▼
┌─────────────────────┐
│  Extract from URL   │
│  (if URL format)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Call server API:   │
│  /api/resolve-      │
│  vanity/{input}     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Return SteamID64   │
│  or None on error   │
└─────────────────────┘
```

### Endpoint serwera

**GET /api/resolve-vanity/{vanity_url:path}**

Serwer obsługuje wszystkie formaty i zwraca SteamID64:

```python
# Server-side (server/app.py)
@app.get("/api/resolve-vanity/{vanity_url:path}")
async def resolve_vanity_url(vanity_url: str):
    """
    Rozwiązuje vanity URL lub Steam ID64 z URL.
    
    Obsługuje:
    - Vanity name: gaben
    - Vanity URL: https://steamcommunity.com/id/gaben
    - Profile URL: https://steamcommunity.com/profiles/76561198012345678
    """
    # ... implementacja w serverze
    return {"steamid": "76561198012345678"}
```

---

## Integracja z API

### Endpointy używane przez SteamUserInfoDialog

#### 1. GET /api/resolve-vanity/{vanity_url:path}

Rozwiązuje różne formaty Steam ID.

**Response:**
```json
{
  "steamid": "76561198012345678"
}
```

#### 2. GET /api/player-summary/{steamid}

Pobiera profil użytkownika Steam.

**Response:**
```json
{
  "steamid": "76561198012345678",
  "personaname": "GabeN",
  "profileurl": "https://steamcommunity.com/id/gaben",
  "avatar": "https://avatars.steamstatic.com/abc_small.jpg",
  "avatarmedium": "https://avatars.steamstatic.com/abc_medium.jpg",
  "avatarfull": "https://avatars.steamstatic.com/abc_full.jpg"
}
```

#### 3. GET /api/owned-games/{steamid}

Pobiera bibliotekę gier użytkownika.

**Response:**
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "playtime_forever": 74100,
      "playtime_2weeks": 2700
    }
  ]
}
```

#### 4. GET /api/recently-played/{steamid}

Pobiera ostatnio grane gry (ostatnie 2 tygodnie).

**Response:**
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "playtime_2weeks": 2700
    }
  ]
}
```

---

## Obsługa błędów

### 1. Nieprawidłowy Steam ID

```python
if not steamid:
    self.status_lbl.setText(
        "Nie udało się rozwiązać identyfikatora Steam. "
        "Sprawdź poprawność danych."
    )
    QMessageBox.warning(
        self,
        "Błąd",
        "Podany identyfikator nie został odnaleziony.\n\n"
        "Upewnij się, że:\n"
        "- Profil jest publiczny\n"
        "- SteamID/vanity name jest poprawny"
    )
```

### 2. Błąd sieciowy

```python
except httpx.RequestError as e:
    logger.error(f"Network error: {e}")
    self.status_lbl.setText(
        f"Błąd połączenia z serwerem.\n"
        f"Upewnij się, że serwer działa na {self._server_client.base_url}"
    )
```

### 3. Prywatny profil

```python
# Jeśli owned_games jest puste, może to oznaczać prywatny profil
if not owned_games:
    self.status_lbl.setText(
        "Brak gier w bibliotece lub profil jest prywatny"
    )
    QMessageBox.information(
        self,
        "Brak danych",
        "Nie znaleziono gier.\n\n"
        "Jeśli profil jest prywatny, zmień ustawienia "
        "prywatności w Steam."
    )
```

---

## Przykład użycia

### 1. Jako dialog z LibraryView

```python
# W LibraryView
from app.ui.user_info_dialog_server import SteamUserInfoDialog

# Utworzenie i wyświetlenie dialogu
dialog = SteamUserInfoDialog(
    server_url="http://localhost:8000",
    parent=self
)

# Modal - blokuje inne okna
dialog.exec()
```

### 2. Jako standalone

```python
# W MainWindow
from app.ui.user_info_dialog_server import SteamUserInfoDialog

# Action w menu lub toolbar
def show_user_info_dialog(self):
    dialog = SteamUserInfoDialog(parent=self)
    dialog.exec()
```

### 3. Przepływ użytkownika

```
1. Użytkownik otwiera dialog
2. Wpisuje: "gaben" lub "76561198012345678"
3. Klika "Pobierz dane"
4. Dialog:
   - Rozwiązuje Steam ID
   - Pobiera profil
   - Pobiera bibliotekę
   - Wyświetla dane w tabeli
5. Użytkownik przegląda bibliotekę
6. Klika "Zamknij" lub [X]
```

---

## Zależności

```python
# PySide6
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QPixmap, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)

# HTTP
import httpx  # Do pobierania avatara

# Custom
from app.core.services.server_client import ServerClient
from app.ui.styles import apply_style
```

---

## Uwagi implementacyjne

1. **Locale** - dialog ustawia polskie locale dla poprawnego formatowania
2. **Czcionki** - automatycznie wybiera czcionkę z polskimi znakami
3. **Avatar** - pobierany asynchronicznie, nie blokuje UI
4. **Sortowanie** - gry zawsze sortowane po łącznym czasie (malejąco)
5. **Korekta czasu** - jeśli playtime_2weeks > playtime_forever, koryguje total
6. **Modal dialog** - używa exec() zamiast show() dla blokowania

---

## Rozszerzenia (TODO)

- [ ] Eksport biblioteki do CSV/JSON
- [ ] Filtrowanie/wyszukiwanie gier w tabeli
- [ ] Kliknięcie na grę otwiera stronę Steam
- [ ] Wyświetlanie dodatk statistics (achievements, badges)
- [ ] Historia zmian czasu gry (wykres)
- [ ] Porównanie z innymi użytkownikami

---

**Ostatnia aktualizacja:** 2025-11-17  
**Autor:** Custom Steam Dashboard Team
