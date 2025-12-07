# Dokumentacja UI - Przegląd

**Data aktualizacji:** 2025-11-18  
**Wersja:** 4.0

## Spis Treści

1. [Wprowadzenie](#wprowadzenie)
2. [Architektura](#architektura)
3. [Struktura Projektu](#struktura-projektu)
4. [Quick Start](#quick-start)
5. [Dokumentacja Szczegółowa](#dokumentacja-szczegółowa)

---

## Wprowadzenie

**Custom Steam Dashboard GUI** to nowoczesna aplikacja desktopowa zbudowana w **PySide6** (Qt for Python) z asynchronicznym wsparciem przez **qasync**.

### Funkcjonalności

- 🏠 **Home View** - Statystyki graczy, promocje, nadchodzące premiery
- 📚 **Library View** - Przeglądarka biblioteki Steam użytkownika
- 📊 **Comparison View** - Porównywanie liczby graczy między grami z wykresami
- 💰 **Deals View** - Przeglądanie i wyszukiwanie promocji na gry
- 👤 **User Info Dialog** - Szczegóły profilu Steam i biblioteki użytkownika
- 🎨 **Theme System** - Ciemny/Jasny + 4 palety kolorów + własne motywy
- 🎨 **Custom Theme Creator** - Kreator własnych palet kolorów
- 🔍 **Deals Filter Dialog** - Zaawansowane filtrowanie promocji
- 💾 **User Data Persistence** - Automatyczne zapisywanie preferencji
- 🔐 **Automatyczne uwierzytelnianie** - JWT + HMAC z serwerem
- 🔄 **Automatyczne odświeżanie** - Co 5-10 minut (konfigurowalny timer)
- 🎨 **Nowoczesny UI** - Responsywny interfejs Qt z pełną obsługą motywów
- ⚡ **Asynchroniczne** - Płynne działanie dzięki qasync

---

## Architektura

```
┌──────────────────────────────────────────────────────────┐
│                   APLIKACJA GUI (PySide6)                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              MainWindow (QMainWindow)              │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │   Toolbar    │  │   QStacked   │                │  │
│  │  │              │  │    Widget    │                │  │
│  │  │ • Home       │  │              │                │  │
│  │  │ • Library    │  │ ┌──────────┐ │                │  │
│  │  │ • Comparison │  │ │ HomeView │ │                │  │
│  │  │ • Deals      │  │ └──────────┘ │                │  │
│  │  │ • Refresh    │  │ ┌──────────┐ │                │  │
│  │  └──────────────┘  │ │ Library  │ │                │  │
│  │                    │ │   View   │ │                │  │
│  │                    │ └──────────┘ │                │  │
│  │                    │ ┌──────────┐ │                │  │
│  │                    │ │Comparison│ │                │  │
│  │                    │ │   View   │ │                │  │
│  │                    │ └──────────┘ │                │  │
│  │                    │ ┌──────────┐ │                │  │
│  │                    │ │  Deals   │ │                │  │
│  │                    │ │   View   │ │                │  │
│  │                    │ └──────────┘ │                │  │
│  │                    └──────────────┘                │  │
│  │                                                    │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │  Dialogs & Widgets                         │    │  │
│  │  │  • SteamUserInfoDialog                     │    │  │
│  │  │  • DealsFilterDialog                       │    │  │
│  │  │  • CustomThemeDialog                       │    │  │
│  │  │  • ThemeSwitcher                           │    │  │
│  │  │  • GameDetailDialog                        │    │  │
│  │  │  • GameDetailPanel                         │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │           Core Services & Managers                 │  │
│  │                                                    │  │
│  │  • ServerClient (HTTP + JWT + HMAC)                │  │
│  │  • ThemeManager (Singleton)                        │  │
│  │  • UserDataManager (Persistence)                   │  │
│  │  • Automatic Retry Logic                           │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
└──────────────────────────┼───────────────────────────────┘
                           │ HTTPS/HTTP + JWT + HMAC
                           ▼
                ┌──────────────────────┐
                │   FastAPI Server     │
                │   (Backend)          │
                └──────────────────────┘
```

---

## Struktura Projektu

```
app/
├── main_server.py                   # 🚀 Punkt wejścia aplikacji
├── main_window.py                   # 🪟 Główne okno (toolbar + navigation)
│
├── ui/                              # 🎨 Komponenty UI
│   ├── __init__.py
│   ├── home_view_server.py          # 🏠 Widok główny
│   ├── library_view_server.py       # 📚 Widok biblioteki
│   ├── comparison_view_server.py    # 📊 Widok porównawczy (wykresy)
│   ├── deals_view_server.py         # 💰 Widok promocji
│   ├── components_server.py         # 🧩 Reużywalne komponenty (GameDetailDialog, GameDetailPanel)
│   ├── user_info_dialog_server.py   # 💬 Dialog informacji użytkownika
│   ├── deals_filter_dialog.py       # 🔍 Dialog filtrów promocji
│   ├── custom_theme_dialog.py       # 🎨 Kreator własnych motywów
│   ├── theme_manager.py             # 🎨 Menedżer motywów (Singleton)
│   ├── theme_switcher.py            # 🔀 Widget przełącznika motywów
│   └── styles.py                    # 🎨 Style Qt (CSS)
│
├── core/                            # 🔧 Logika biznesowa
│   ├── user_data_manager.py         # 💾 Manager trwałości danych
│   └── services/
│       ├── server_client.py         # 🌐 Klient HTTP do serwera
│       └── deals_client.py          # 💰 Klient IsThereAnyDeal
│
└── helpers/                         # 🛠️ Narzędzia pomocnicze
    ├── api_client.py                # 🔐 Authenticated API client
    └── signing.py                   # ✍️ HMAC signature generation
```

---

## Quick Start

### 1. Wymagania

- **Python**: 3.11+ (zalecane 3.12)
- **System**: Linux, macOS, Windows
- **Serwer**: Uruchomiony backend (zobacz [SERVER_OVERVIEW.md](server/SERVER_OVERVIEW.md))

### 2. Instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard

# Utworzenie wirtualnego środowiska
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalacja zależności
pip install -r requirements.txt
```

### 3. Konfiguracja .env

Utwórz plik `.env` w katalogu głównym:

```env
# Server Configuration
SERVER_URL=http://localhost:8000

# Client Credentials (muszą zgadzać się z serwerem)
CLIENT_ID=desktop-main
CLIENT_SECRET=your-client-secret

# Steam API (opcjonalnie - dla testów)
STEAM_API_KEY=your_steam_api_key
STEAM_ID=your_steam_id
```

### 4. Uruchomienie

```bash
# Upewnij się, że serwer jest uruchomiony
cd server
python app.py
# W drugim terminalu:

# Uruchom GUI
python -m app.main_server
```

**Aplikacja:**
1. Automatycznie uwierzytelni się z serwerem
2. Otworzy główne okno z widokiem Home
3. Rozpocznie automatyczne odświeżanie (co 5 minut)

---

## Kluczowe Zależności

| Biblioteka | Wersja | Zastosowanie |
|------------|--------|--------------|
| **PySide6** | 6.7+ | Framework Qt dla GUI |
| **qasync** | 0.26+ | Integracja Qt ↔ asyncio |
| **httpx** | 0.27+ | Klient HTTP/2 |
| **pydantic** | 2.7+ | Walidacja danych |
| **tenacity** | 9.0+ | Retry logic |
| **python-dotenv** | 1.0+ | Zmienne środowiskowe |

---

## Dokumentacja Szczegółowa

Pełna dokumentacja podzielona na moduły:

| Dokument | Opis |
|----------|------|
| [📱 UI_COMPONENTS.md](UI_COMPONENTS.md) | Komponenty i widgety (NumberValidator, GameDetailDialog) |
| [🏠 UI_HOME_VIEW.md](UI_HOME_VIEW.md) | Widok główny (statystyki, filtry, promocje) |
| [📚 UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md) | Widok biblioteki Steam użytkownika |
| [📊 UI_COMPARISON_VIEW.md](UI_COMPARISON_VIEW.md) | Widok porównawczy z wykresami matplotlib |
| [💰 UI_DEALS_VIEW.md](UI_DEALS_VIEW.md) | Widok promocji i wyszukiwania okazji |
| [👤 UI_USER_INFO_DIALOG.md](UI_USER_INFO_DIALOG.md) | Dialog profilu użytkownika Steam |
| [🪟 UI_MAIN_WINDOW.md](UI_MAIN_WINDOW.md) | Główne okno aplikacji (toolbar, nawigacja) |
| [🔐 UI_AUTHENTICATION.md](UI_AUTHENTICATION.md) | System uwierzytelniania (JWT + HMAC) |
| [🎨 UI_STYLING.md](UI_STYLING.md) | Style i motywy Qt (ciemny motyw) |

---

## Przepływ Aplikacji

### Startup Sequence

```
1. main_server.py
   ├─> Ładowanie .env
   ├─> Utworzenie QApplication
   ├─> Utworzenie asyncio event loop (qasync)
   └─> authenticate_with_server()
       ├─> ServerClient.authenticate()
       │   ├─> POST /auth/login (z HMAC signature)
       │   └─> Zapisanie JWT token
       └─> Jeśli sukces:
           ├─> MainWindow.show()
           └─> exec() event loop
```

### Navigation Flow

```
MainWindow
├─> Toolbar Actions
│   ├─> "Home" → navigate_to_home()
│   ├─> "Biblioteka gier" → navigate_to_library()
│   ├─> "Porównanie" → navigate_to_comparison()
│   ├─> "Promocje" → navigate_to_deals()
│   └─> "Odśwież" → refresh_current_view()
│
└─> QStackedWidget
    ├─> HomeView (index 0)
    │   ├─> refresh_data() co 5 minut
    │   ├─> Fetch /api/current-players
    │   ├─> Fetch /api/deals/best
    │   └─> Fetch /api/coming-soon
    │
    ├─> LibraryView (index 1)
    │   ├─> Resolve Steam ID
    │   ├─> Fetch /api/player-summary/{steamid}
    │   ├─> Fetch /api/owned-games/{steamid}
    │   └─> Wyświetl tabelę gier
    │
    ├─> ComparisonView (index 2)
    │   ├─> refresh_data() co 5 minut
    │   ├─> Fetch /api/current-players (lista gier)
    │   ├─> POST /api/player-history/compare (dane historyczne)
    │   ├─> Rysuj wykres matplotlib
    │   └─> Oblicz statystyki (min, max, średnia)
    │
    └─> DealsView (index 3)
        ├─> refresh_data() co 10 minut
        ├─> Fetch /api/deals/best (najlepsze okazje)
        └─> GET /api/deals/search?title={query} (wyszukiwanie)
```

---

## Uwierzytelnianie

### Automatyczne Logowanie

```python
# app/main_server.py
async def authenticate_with_server(server_url: str) -> bool:
    """
    Uwierzytelnia się z serwerem przed uruchomieniem GUI.
    """
    client = ServerClient(server_url)
    success = await client.authenticate()
    
    if success:
        print("✓ Successfully authenticated with server")
        return True
    else:
        print("✗ Failed to authenticate with server")
        return False
```

### Token Management

- **Token** jest automatycznie odświeżany gdy wygaśnie
- **HMAC signature** jest dodawany do każdego żądania
- **Retry logic** automatycznie ponawia nieudane żądania

---

## Asynchroniczność

### qasync Event Loop

```python
# app/main_server.py
def main():
    app = QApplication(sys.argv)
    
    # Utwórz asyncio event loop dla Qt
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Uwierzytelnij asynchronicznie
    authenticated = loop.run_until_complete(
        authenticate_with_server(server_url)
    )
    
    if not authenticated:
        sys.exit(1)
    
    # Utwórz okno
    window = MainWindow(server_url)
    window.show()
    
    # Uruchom event loop
    with loop:
        loop.run_forever()
```

### Async w Qt Widgets

```python
# app/ui/home_view_server.py
class HomeView(QWidget):
    async def refresh_data(self):
        """Asynchroniczne odświeżanie danych."""
        try:
            # Wszystkie operacje są asynchroniczne
            games = await self.server_client.get_current_players()
            deals = await self.server_client.get_deals()
            upcoming = await self.server_client.get_coming_soon()
            
            # Aktualizuj UI (synchronicznie, w głównym wątku Qt)
            self._update_ui(games, deals, upcoming)
            
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
```

---

## Error Handling

### Network Errors

```python
# Automatyczne retry (tenacity)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def make_request(self, ...):
    ...
```

### Authentication Errors

```python
# Automatyczne odświeżanie tokena
if response.status_code == 401:
    # Token wygasł
    await self.authenticate()
    # Ponów żądanie
    response = await self.make_request(...)
```

### User-Friendly Messages

```python
# Wyświetl błąd w UI
QMessageBox.critical(
    self,
    "Błąd połączenia",
    f"Nie można połączyć z serwerem:\n{error_message}"
)
```

---

## Następne Kroki

1. **Komponenty UI**: [UI_COMPONENTS.md](UI_COMPONENTS.md)
2. **Home View**: [UI_HOME_VIEW.md](UI_HOME_VIEW.md)
3. **Library View**: [UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md)
4. **Comparison View**: [UI_COMPARISON_VIEW.md](UI_COMPARISON_VIEW.md)
5. **Deals View**: [UI_DEALS_VIEW.md](UI_DEALS_VIEW.md)
6. **User Info Dialog**: [UI_USER_INFO_DIALOG.md](UI_USER_INFO_DIALOG.md)
7. **Main Window**: [UI_MAIN_WINDOW.md](UI_MAIN_WINDOW.md)

---

## Wsparcie

- **Dokumentacja Serwera**: [SERVER_OVERVIEW.md](server/SERVER_OVERVIEW.md)
- **Dokumentacja JWT**: [JWT_OVERVIEW.md](../jwt/JWT_OVERVIEW.md)
- **Issues**: [GitHub Issues](https://github.com/SzyMm0n/Custom-Steam-Dashboard/issues)

