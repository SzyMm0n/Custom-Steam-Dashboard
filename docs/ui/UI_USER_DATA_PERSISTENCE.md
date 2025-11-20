# System Trwałości Danych Użytkownika - UserDataManager

**Data aktualizacji:** 2025-11-18  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Architektura](#architektura)
3. [Zapisywane Dane](#zapisywane-dane)
4. [Użycie](#użycie)
5. [Struktura Pliku](#struktura-pliku)
6. [Przykłady](#przykłady)

---

## Przegląd

**UserDataManager** to singleton zarządzający trwałością preferencji użytkownika w aplikacji Custom Steam Dashboard. Zapewnia centralne miejsce do zapisywania i odczytywania ustawień, które przetrwają między sesjami aplikacji.

### Lokalizacja
```
app/core/user_data_manager.py
```

### Klasa
```python
class UserDataManager
```

### Wzorzec Projektowy
Singleton - jedna instancja w całej aplikacji

---

## Architektura

```
┌───────────────────────────────────────────────────────────┐
│                   UserDataManager                         │
│                     (Singleton)                           │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Zarządzanie Preferencjami                          │  │
│  │                                                     │  │
│  │  • Motywy (theme_mode, theme_palette)               │  │
│  │  • Własne motywy (custom_themes)                    │  │
│  │  • Ostatnio użyta biblioteka (last_library_steamid) │  │
│  │  • Ustawienia aplikacji (app_preferences)           │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Operacje na Plikach                                │  │
│  │                                                     │  │
│  │  • Ładowanie (load_data)                            │  │
│  │  • Zapisywanie (save_data)                          │  │
│  │  • Backup (create_backup)                           │  │
│  │  • Walidacja (validate_data)                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                               │
└───────────────────────────┼───────────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │   user_data.json        │
                │                         │
                │   (persistent storage)  │
                └─────────────────────────┘
```

---

## Zapisywane Dane

### 1. Preferencje Motywów

```json
{
  "theme_preferences": {
    "mode": "dark",           // "dark" | "light"
    "palette": "green"        // "green" | "blue" | "purple" | "orange" | "custom"
  }
}
```

### 2. Własne Motywy

```json
{
  "custom_themes": {
    "Mój Motyw": {
      "dark": {
        "background": "#0b0b0b",
        "surface": "#1a1a1a",
        "accent": "#16a34a",
        // ... więcej kolorów
      },
      "light": {
        "background": "#ffffff",
        "surface": "#f8f9fa",
        "accent": "#16a34a",
        // ... więcej kolorów
      },
      "created_at": "2025-11-18T10:30:00Z",
      "modified_at": "2025-11-18T12:00:00Z"
    }
  }
}
```

### 3. Ostatnia Biblioteka

```json
{
  "last_library": {
    "steam_id": "76561198012345678",
    "loaded_at": "2025-11-18T14:30:00Z"
  }
}
```

### 4. Preferencje Aplikacji

```json
{
  "app_preferences": {
    "auto_refresh_interval": 300,    // sekundy
    "enable_notifications": true,
    "compact_mode": false,
    "language": "pl"
  }
}
```

---

## Użycie

### Inicjalizacja (Singleton)

```python
from app.core.user_data_manager import UserDataManager

# Zawsze zwraca tę samą instancję
data_manager = UserDataManager()
```

### Motywy

#### Zapisz preferencje motywu
```python
data_manager = UserDataManager()

# Zapisz tryb i paletę
data_manager.set_theme_preference(
    mode="dark",           # "dark" | "light"
    palette="blue"         # "green" | "blue" | "purple" | "orange"
)
```

#### Odczytaj preferencje motywu
```python
mode, palette = data_manager.get_theme_preference()
# Zwraca: ("dark", "blue") lub domyślne ("dark", "green")
```

#### Zapisz własny motyw
```python
dark_colors = {
    "background": "#0b0b0b",
    "surface": "#1a1a1a",
    "accent": "#16a34a",
    # ... więcej kolorów
}

light_colors = {
    "background": "#ffffff",
    "surface": "#f8f9fa",
    "accent": "#16a34a",
    # ... więcej kolorów
}

data_manager.save_custom_theme(
    name="Mój Zielony Motyw",
    dark_colors=dark_colors,
    light_colors=light_colors
)
```

#### Pobierz własny motyw
```python
theme_data = data_manager.get_custom_theme("Mój Zielony Motyw")
# Zwraca: {"dark": {...}, "light": {...}, "created_at": "..."}
```

#### Lista własnych motywów
```python
custom_themes = data_manager.list_custom_themes()
# Zwraca: ["Mój Zielony Motyw", "Motyw Niebieski", ...]
```

#### Usuń własny motyw
```python
success = data_manager.delete_custom_theme("Mój Zielony Motyw")
```

### Biblioteka Steam

#### Zapisz ostatnio używany Steam ID
```python
data_manager.set_last_library("76561198012345678")
```

#### Pobierz ostatnio używany Steam ID
```python
steam_id = data_manager.get_last_library()
# Zwraca: "76561198012345678" lub None
```

### Preferencje Aplikacji

#### Zapisz preferencję
```python
data_manager.set_preference("auto_refresh_interval", 600)
data_manager.set_preference("enable_notifications", False)
```

#### Pobierz preferencję
```python
interval = data_manager.get_preference("auto_refresh_interval", default=300)
notifications = data_manager.get_preference("enable_notifications", default=True)
```

---

## Struktura Pliku

### Lokalizacja pliku

#### Tryb deweloperski
```
/home/user/PycharmProjects/Custom-Steam-Dashboard/user_data.json
```

#### Tryb wykonywalny (frozen)
```
/path/to/executable/user_data.json
```

### Pełna struktura

```json
{
  "version": "1.0",
  "last_modified": "2025-11-18T14:30:00Z",
  
  "theme_preferences": {
    "mode": "dark",
    "palette": "green"
  },
  
  "custom_themes": {
    "Theme Name": {
      "dark": { /* colors */ },
      "light": { /* colors */ },
      "created_at": "2025-11-18T10:30:00Z",
      "modified_at": "2025-11-18T12:00:00Z"
    }
  },
  
  "last_library": {
    "steam_id": "76561198012345678",
    "loaded_at": "2025-11-18T14:30:00Z"
  },
  
  "app_preferences": {
    "auto_refresh_interval": 300,
    "enable_notifications": true,
    "compact_mode": false,
    "language": "pl"
  }
}
```

---

## Przykłady

### Przykład 1: Pierwszy start aplikacji

```python
def first_time_setup():
    """Inicjalizacja przy pierwszym uruchomieniu."""
    data_manager = UserDataManager()
    
    # Ustaw domyślne preferencje
    data_manager.set_theme_preference("dark", "green")
    data_manager.set_preference("auto_refresh_interval", 300)
    data_manager.set_preference("enable_notifications", True)
    
    logger.info("First time setup completed")
```

### Przykład 2: Przywracanie stanu aplikacji

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._data_manager = UserDataManager()
        
        # Przywróć motyw
        self._restore_theme()
        
        # Przywróć ostatnią bibliotekę
        self._restore_last_library()
    
    def _restore_theme(self):
        """Przywróć zapisany motyw."""
        mode, palette = self._data_manager.get_theme_preference()
        theme_manager = ThemeManager()
        theme_manager.set_mode(ThemeMode(mode))
        theme_manager.set_palette(ColorPalette(palette))
    
    async def _restore_last_library(self):
        """Przywróć ostatnio używaną bibliotekę."""
        steam_id = self._data_manager.get_last_library()
        if steam_id:
            await self._load_library(steam_id)
```

### Przykład 3: Zapisywanie przy zamykaniu

```python
class MainWindow(QMainWindow):
    def closeEvent(self, event):
        """Obsłuż zamknięcie aplikacji."""
        # Zapisz aktualny Steam ID
        if self._current_steam_id:
            self._data_manager.set_last_library(self._current_steam_id)
        
        # Zapisz preferencje motywu (jeśli zmienione)
        theme_manager = ThemeManager()
        self._data_manager.set_theme_preference(
            mode=theme_manager.current_mode.value,
            palette=theme_manager.current_palette.value
        )
        
        event.accept()
```

### Przykład 4: Tworzenie i używanie własnego motywu

```python
async def create_and_apply_custom_theme():
    """Utwórz i zastosuj własny motyw."""
    data_manager = UserDataManager()
    
    # Utwórz palety kolorów
    dark_colors = generate_dark_palette(base_color)
    light_colors = generate_light_palette(base_color)
    
    # Zapisz motyw
    data_manager.save_custom_theme(
        name="Mój Motyw",
        dark_colors=dark_colors,
        light_colors=light_colors
    )
    
    # Zastosuj motyw
    theme_manager = ThemeManager()
    theme_manager.set_custom_theme("Mój Motyw")
    
    # Zapisz jako aktualny
    data_manager.set_theme_preference(
        mode=theme_manager.current_mode.value,
        palette="custom"
    )
```

---

## Bezpieczeństwo i Backup

### Automatyczny Backup

```python
def _create_backup(self):
    """Utwórz backup przed zapisem."""
    if self._data_file.exists():
        backup_file = self._data_file.with_suffix('.json.bak')
        shutil.copy2(self._data_file, backup_file)
        logger.info(f"Backup created: {backup_file}")
```

### Walidacja Danych

```python
def _validate_data(self, data: dict) -> bool:
    """
    Waliduj strukturę danych.
    
    Returns:
        True jeśli dane są poprawne
    """
    try:
        # Sprawdź wymagane klucze
        if "version" not in data:
            return False
        
        # Waliduj theme_preferences
        if "theme_preferences" in data:
            prefs = data["theme_preferences"]
            if prefs.get("mode") not in ["dark", "light"]:
                return False
        
        return True
    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        return False
```

### Obsługa Błędów

```python
def _load_data(self) -> dict:
    """Załaduj dane z pliku z obsługą błędów."""
    try:
        if not self._data_file.exists():
            return self._get_default_data()
        
        with open(self._data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not self._validate_data(data):
            logger.warning("Invalid data, using defaults")
            return self._get_default_data()
        
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        # Spróbuj odzyskać z backupu
        return self._restore_from_backup()
    
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return self._get_default_data()
```

---

## Migracja Danych

### Wersjonowanie

```python
CURRENT_VERSION = "1.0"

def _migrate_data(self, data: dict) -> dict:
    """Migruj dane do aktualnej wersji."""
    data_version = data.get("version", "0.0")
    
    if data_version == "0.0":
        # Migracja z wersji bez wersjonowania
        data = self._migrate_from_0_0(data)
        data_version = "1.0"
    
    data["version"] = CURRENT_VERSION
    return data
```

---

## API Reference

### Metody Publiczne

#### Theme Management
- `set_theme_preference(mode: str, palette: str) -> None`
- `get_theme_preference() -> tuple[str, str]`
- `save_custom_theme(name: str, dark_colors: dict, light_colors: dict) -> None`
- `get_custom_theme(name: str) -> Optional[dict]`
- `list_custom_themes() -> List[str]`
- `delete_custom_theme(name: str) -> bool`
- `custom_theme_exists(name: str) -> bool`

#### Library Management
- `set_last_library(steam_id: str) -> None`
- `get_last_library() -> Optional[str]`

#### Preferences
- `set_preference(key: str, value: Any) -> None`
- `get_preference(key: str, default: Any = None) -> Any`

#### Data Operations
- `save() -> bool`
- `reload() -> bool`
- `reset_to_defaults() -> None`

---

## Zobacz również

- [UI_THEME_SYSTEM.md](UI_THEME_SYSTEM.md) - System motywów
- [UI_CUSTOM_THEME_DIALOG.md](UI_CUSTOM_THEME_DIALOG.md) - Kreator motywów
- [UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md) - Widok biblioteki

---

**Plik źródłowy:** `app/core/user_data_manager.py`  
**Używane przez:** ThemeManager, MainWindow, wszystkie widoki  
**Wymagania:** Python 3.11+, json, pathlib

