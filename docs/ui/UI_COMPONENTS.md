# Dokumentacja Komponentów UI

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [NumberValidator](#numbervalidator)
3. [GameDetailDialog](#gamedetaildialog)
4. [Helpers](#helpers)
5. [Style](#style)

---

## Przegląd

**Plik:** `app/ui/components_server.py`

Moduł zawiera reużywalne komponenty UI wykorzystywane w całej aplikacji:
- Walidatory wejścia
- Dialogi
- Pomocnicze widgety

---

## NumberValidator

**Klasa:** `NumberValidator(QRegularExpressionValidator)`

Walidator dla pól numerycznych z separatorami tysięcy.

### Funkcjonalność

- ✅ Akceptuje cyfry (0-9)
- ✅ Akceptuje spacje (separator tysięcy)
- ✅ Maksymalnie 15 znaków
- ✅ Regex: `^[0-9 ]{0,15}$`

### Inicjalizacja

```python
def __init__(self, parent=None):
    """
    Inicjalizuje walidator liczb.
    
    Args:
        parent: Widget rodzica
    """
    super().__init__(QRegularExpression(r"^[0-9 ]{0,15}$"), parent)
```

### Przykład Użycia

```python
from app.ui.components_server import NumberValidator

# Utwórz pole tekstowe z walidatorem
line_edit = QLineEdit()
line_edit.setValidator(NumberValidator())

# Użytkownik może wpisać:
# ✅ "1000000" -> OK
# ✅ "1 000 000" -> OK (z separatorami)
# ❌ "abc" -> Odrzucone
# ❌ "1000000000000000" -> Odrzucone (za długie)
```

---

## GameDetailDialog

**Klasa:** `GameDetailDialog(QDialog)`

Dialog wyświetlający szczegółowe informacje o grze.

### Funkcjonalność

- ✅ Wyświetla tytuł gry
- ✅ Pobiera obraz nagłówka ze Steam
- ✅ Pokazuje opis gry
- ✅ Wyświetla liczbę graczy (jeśli dostępna)
- ✅ Pokazuje tagi (gatunki/kategorie)
- ✅ Link do Steam Store
- ✅ Link do promocji (jeśli dostępna)
- ✅ **Pobiera dane z serwera backend**

### Inicjalizacja

```python
def __init__(
    self, 
    game_data: Any, 
    server_url: Optional[str] = None,
    parent: Optional[QWidget] = None
):
    """
    Inicjalizuje dialog szczegółów gry.
    
    Args:
        game_data: Dane gry (string lub dict)
            - String: nazwa gry
            - Dict: {name, appid, players, tags, deal_url, ...}
        server_url: URL serwera backend
        parent: Widget rodzica
    """
```

### Format game_data

#### Opcja 1: String (tylko nazwa)

```python
dialog = GameDetailDialog("Counter-Strike 2", server_url)
dialog.exec()
```

#### Opcja 2: Dict (pełne dane)

```python
game_data = {
    "name": "Counter-Strike 2",
    "appid": 730,
    "current_players": 1000000,
    "tags": {
        "genres": ["Action", "Free to Play"],
        "categories": ["Multi-player", "Steam Achievements"]
    },
    "deal_url": "https://isthereanydeal.com/...",  # Opcjonalnie
    "deal_id": "12345",  # Opcjonalnie
    "store_id": "steam",  # Opcjonalnie
    "store_name": "Steam"  # Opcjonalnie
}

dialog = GameDetailDialog(game_data, server_url)
dialog.exec()
```

### Struktura UI

```
┌─────────────────────────────────────────┐
│         Szczegóły gry                  │
├─────────────────────────────────────────┤
│  Counter-Strike 2                      │  <- Tytuł (bold, 14px)
│                                        │
│  ┌───────────────────────────────┐    │
│  │                               │    │
│  │    [Header Image]             │    │  <- Obraz ze Steam
│  │                               │    │
│  └───────────────────────────────┘    │
│                                        │
│  For over two decades, Counter-       │  <- Opis
│  Strike has offered an elite...       │
│                                        │
│  Obecna liczba graczy: 1,000,000      │  <- Statystyki
│                                        │
│  Gatunki: Action, Free to Play        │  <- Tagi
│  Kategorie: Multi-player, ...         │
│                                        │
│  [Zobacz w Steam Store]               │  <- Przyciski
│  [Zobacz promocję]                     │
│  [Zamknij]                             │
└─────────────────────────────────────────┘
```

### Metody Wewnętrzne

#### _parse_game_data(game_data)

Parsuje dane gry z różnych formatów.

```python
def _parse_game_data(self, game_data: Any) -> None:
    """
    Parsuje dane gry z dict lub string.
    
    Ustawia:
        - self._title (nazwa gry)
        - self._appid (Steam App ID)
        - self._players (liczba graczy)
        - self._tags (gatunki/kategorie)
        - self._deal_* (dane promocji)
    """
```

#### _create_title_section(layout)

Tworzy sekcję tytułu.

```python
def _create_title_section(self, layout: QVBoxLayout) -> None:
    """
    Tworzy label z tytułem gry (bold, 14px).
    """
    title_label = QLabel(self._title)
    font = title_label.font()
    font.setPointSize(14)
    font.setBold(True)
    title_label.setFont(font)
    layout.addWidget(title_label)
```

#### _create_image_section(layout)

Tworzy sekcję z obrazem nagłówka.

```python
def _create_image_section(self, layout: QVBoxLayout) -> None:
    """
    Tworzy QLabel dla obrazu nagłówka.
    Obraz jest ładowany asynchronicznie.
    """
    self._image_label = QLabel("Ładowanie obrazu...")
    self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self._image_label.setMinimumHeight(150)
    layout.addWidget(self._image_label)
```

#### _create_details_section(layout)

Tworzy sekcję ze szczegółami gry.

```python
def _create_details_section(self, layout: QVBoxLayout) -> None:
    """
    Tworzy sekcję z opisem, statystykami i tagami.
    
    Wyświetla:
        - Opis gry (short_description ze Steam)
        - Liczba graczy (jeśli dostępna)
        - Gatunki i kategorie
    """
```

#### _create_buttons_section(layout)

Tworzy sekcję z przyciskami akcji.

```python
def _create_buttons_section(self, layout: QVBoxLayout) -> None:
    """
    Tworzy przyciski:
        - "Zobacz w Steam Store"
        - "Zobacz promocję" (jeśli dostępna)
        - "Zamknij"
    """
```

#### _load_async_data()

Ładuje dodatkowe dane z serwera.

```python
def _load_async_data(self) -> None:
    """
    Asynchronicznie ładuje:
        1. Obraz nagłówka ze Steam
        2. Opis gry (jeśli brakuje)
        3. Tagi (gatunki/kategorie)
    
    Używa self._server_client do komunikacji z backend.
    """
```

### Przykład Pełnego Użycia

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
from app.ui.components_server import GameDetailDialog
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        button = QPushButton("Pokaż szczegóły gry", self)
        button.clicked.connect(self.show_game_details)
        self.setCentralWidget(button)
    
    def show_game_details(self):
        game_data = {
            "name": "Counter-Strike 2",
            "appid": 730,
            "current_players": 1234567
        }
        
        dialog = GameDetailDialog(
            game_data=game_data,
            server_url="http://localhost:8000",
            parent=self
        )
        dialog.exec()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
```

---

## Helpers

### Locale Formatting

Dialog używa polskiego locale do formatowania liczb:

```python
from PySide6.QtCore import QLocale

locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)

# Formatowanie liczby graczy
players = 1234567
formatted = locale.toString(players)  # "1 234 567"
```

### URL Encoding

Obsługa specjalnych znaków w nazwach gier:

```python
import urllib.parse

game_name = "Counter-Strike 2"
encoded = urllib.parse.quote(game_name)  # "Counter-Strike%202"
steam_url = f"https://store.steampowered.com/search/?term={encoded}"
```

### Image Loading

Asynchroniczne ładowanie obrazów:

```python
async def _load_header_image(self):
    """
    Pobiera obraz nagłówka ze Steam.
    
    URL Format: 
        https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg
    """
    if not self._appid:
        return
    
    url = f"https://cdn.akamai.steamstatic.com/steam/apps/{self._appid}/header.jpg"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        image_data = response.content
    
    pixmap = QPixmap()
    pixmap.loadFromData(image_data)
    
    # Skaluj obraz zachowując proporcje
    scaled = pixmap.scaled(
        400, 200,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    
    self._image_label.setPixmap(scaled)
```

---

## Style

**Plik:** `app/ui/styles.py`

### apply_style(widget)

Aplikuje ciemny motyw do widgetu.

```python
def apply_style(widget: QWidget) -> None:
    """
    Aplikuje ciemny motyw Qt do widgetu.
    
    Stylizuje:
        - Tło (ciemny szary)
        - Tekst (jasny)
        - Przyciski (hover effects)
        - Tabele (alternate row colors)
        - Scrollbary
    
    Args:
        widget: Widget do wystylizowania
    """
    widget.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555555;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        /* ... więcej stylów ... */
    """)
```

### Przykład Użycia

```python
from app.ui.styles import apply_style

dialog = GameDetailDialog(game_data)
apply_style(dialog)  # Aplikuje ciemny motyw
dialog.exec()
```

---

## Best Practices

### 1. Używaj Komponentów

```python
# ✅ Dobre - używaj reużywalnych komponentów
from app.ui.components_server import GameDetailDialog

dialog = GameDetailDialog(game_data, server_url)
dialog.exec()

# ❌ Złe - nie twórz własnych dialogów od zera
class MyGameDialog(QDialog):
    # ... duplikacja kodu ...
```

### 2. Waliduj Wejście

```python
# ✅ Dobre - waliduj pola numeryczne
from app.ui.components_server import NumberValidator

line_edit = QLineEdit()
line_edit.setValidator(NumberValidator())

# ❌ Złe - brak walidacji
line_edit = QLineEdit()  # Użytkownik może wpisać cokolwiek
```

### 3. Obsługuj Błędy

```python
# ✅ Dobre - obsłuż błędy ładowania
try:
    dialog = GameDetailDialog(game_data, server_url)
    dialog.exec()
except Exception as e:
    QMessageBox.critical(self, "Błąd", f"Nie można załadować szczegółów: {e}")

# ❌ Złe - ignoruj błędy
dialog = GameDetailDialog(game_data, server_url)  # Może rzucić wyjątek
dialog.exec()
```

### 4. Używaj Stylów

```python
# ✅ Dobre - spójny wygląd
from app.ui.styles import apply_style

widget = QWidget()
apply_style(widget)

# ❌ Złe - inconsistent styling
widget = QWidget()
widget.setStyleSheet("background-color: red;")  # Niespójne z resztą
```

---

## Podsumowanie

| Komponent | Przeznaczenie | Przykład |
|-----------|---------------|----------|
| **NumberValidator** | Walidacja pól numerycznych | Filtry liczby graczy |
| **GameDetailDialog** | Szczegóły gry | Kliknięcie na grę w liście |
| **apply_style** | Ciemny motyw Qt | Wszystkie widgety |

---

## Następne Kroki

- **Home View**: [UI_HOME_VIEW.md](UI_HOME_VIEW.md)
- **Library View**: [UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md)
- **Main Window**: [UI_MAIN_WINDOW.md](UI_MAIN_WINDOW.md)

