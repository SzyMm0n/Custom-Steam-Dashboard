# System motywów - Custom Steam Dashboard

**Data aktualizacji:** 2025-11-18  
**Wersja:** 2.0

## Przegląd

Aplikacja Custom Steam Dashboard posiada zaawansowany system motywów obsługujący:
- **2 tryby**: Ciemny (domyślny) i Jasny
- **5 palet kolorów**: Zielona (domyślna), Niebieska, Fioletowa, Pomarańczowa + **Własne**
- **Kreator własnych motywów** - CustomThemeDialog
- **Dynamiczne przełączanie** motywów na każdym widoku
- **Automatyczne odświeżanie** wszystkich komponentów UI
- **Trwałe przechowywanie** preferencji przez UserDataManager

## Tryby motywów

### Tryb ciemny (domyślny)
- Ciemne tło (#0b0b0b - #2b2b2b)
- Jasny tekst (#FFFFFF)
- Wysoki kontrast dla lepszej czytelności
- Idealny do pracy w nocy

### Tryb jasny
- Jasne tło (#FFFFFF - #F8F9FA)
- Ciemny tekst (#1a1a1a)
- Komfortowy dla oczu w dziennym świetle
- Profesjonalny wygląd

## Palety kolorów

### 1. Zielona (domyślna)
**Akcent**: #16a34a (zielony)
- Najlepsze dla standardowego użytku
- Wysoka czytelność
- Przyjazny dla oczu

### 2. Niebieska
**Akcent**: #3b82f6 (niebieski)
- Profesjonalny wygląd
- Idealny dla środowisk biznesowych
- Spokojny i elegancki

### 3. Fioletowa
**Akcent**: #a855f7 (fiolet)
- Kreatywny i nowoczesny
- Wyróżniający się
- Idealny dla indywidualnego stylu

### 4. Pomarańczowa
**Akcent**: #f97316 (pomarańczowy)
- Energetyczny i dynamiczny
- Wysoka widoczność
- Ciepły i przyjazny

### 5. Własna (Custom)
**Akcent**: Zdefiniowany przez użytkownika
- Kreator własnych palet kolorów - **CustomThemeDialog**
- Pełna personalizacja kolorystyki
- Automatyczne generowanie harmonijnych odcieni
- Osobne palety dla trybu ciemnego i jasnego
- Trwałe przechowywanie przez **UserDataManager**

Aby utworzyć własny motyw:
1. Kliknij na przełączniku palet: **"Stwórz własny..."**
2. Wybierz kolor bazowy w **CustomThemeDialog**
3. Podgląd na żywo dla trybu ciemnego i jasnego
4. Nazwij i zapisz motyw
5. Motyw pojawi się na liście palet

Szczegóły: [UI_CUSTOM_THEME_DIALOG.md](UI_CUSTOM_THEME_DIALOG.md)

## Użycie

### Przełącznik motywu

Na każdym widoku aplikacji znajduje się przełącznik motywu w prawym górnym rogu:

```
[🌙 Ciemny] Paleta: [Zielona ▼]
```

#### Przyciski:
- **🌙 Ciemny / ☀️ Jasny** - przełącza tryb
- **Paleta** - wybiera paletę kolorów (Zielona/Niebieska/Fioletowa/Pomarańczowa)

### Zmiany są natychmiastowe
- Wszystkie kolory aktualizują się automatycznie
- Wykresy i komponenty dostosowują się do nowego motywu
- Motyw jest współdzielony między wszystkimi widokami

## Architektura

### ThemeManager (Singleton)
Główny menedżer motywów zarządzający trybem i paletą:

```python
from app.ui.theme_manager import ThemeManager, ThemeMode, ColorPalette

theme_manager = ThemeManager()
theme_manager.set_mode(ThemeMode.LIGHT)
theme_manager.set_palette(ColorPalette.BLUE)
```

### ThemeSwitcher (Widget)
Widget UI do przełączania motywów:

```python
from app.ui.theme_switcher import ThemeSwitcher

theme_switcher = ThemeSwitcher()
layout.addWidget(theme_switcher)
```

### Obsługa zmian motywu

Każdy widok powinien implementować obsługę zmian:

```python
def __init__(self):
    self._theme_manager = ThemeManager()
    self._theme_manager.theme_changed.connect(self._on_theme_changed)

def _on_theme_changed(self, mode: str, palette: str):
    """Handle theme change event."""
    refresh_style(self)
    # Dodatkowo: odśwież wykresy, komponenty itp.
```

### Kolory motywu

Aby pobrać aktualne kolory motywu:

```python
from app.ui.styles import get_color

# Pobierz pojedynczy kolor
accent_color = get_color('accent')

# Lub pobierz wszystkie kolory
from app.ui.theme_manager import ThemeManager
colors = ThemeManager().get_colors()

# Dostępne klucze kolorów:
# - background, background_light, background_panel, background_group
# - foreground, foreground_dim
# - border, border_group
# - accent, accent_hover, accent_pressed, accent_light
# - danger, danger_hover, danger_pressed
# - chart_bg, chart_plot, chart_grid, chart_text
```

### Wykresy matplotlib

Wykresy automatycznie dostosowują się do motywu:

```python
def _update_chart(self):
    colors = self._theme_manager.get_colors()
    
    # Ustaw kolory tła
    self._figure.patch.set_facecolor(colors['chart_bg'])
    self._ax.set_facecolor(colors['chart_plot'])
    
    # Ustaw kolory tekstu
    self._ax.set_xlabel('Label', color=colors['chart_text'])
    self._ax.tick_params(colors=colors['chart_text'])
    
    # Siatka
    self._ax.grid(True, color=colors['chart_grid'], alpha=0.2)
```

## Przykład implementacji

### Dodanie przełącznika do nowego widoku

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from app.ui.theme_manager import ThemeManager
from app.ui.theme_switcher import ThemeSwitcher
from app.ui.styles import apply_style, refresh_style

class MyNewView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicjalizuj theme manager
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Nagłówek z przełącznikiem motywu
        title_layout = QHBoxLayout()
        
        title = QLabel("Mój nowy widok")
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        theme_switcher = ThemeSwitcher()
        title_layout.addWidget(theme_switcher)
        
        layout.addLayout(title_layout)
        
        # ... reszta UI ...
        
        # Zastosuj początkowy motyw
        apply_style(self)
    
    def _on_theme_changed(self, mode: str, palette: str):
        """Obsłuż zmianę motywu."""
        refresh_style(self)
        # Opcjonalnie: odśwież dodatkowe komponenty
```

## Opcjonalnie: odśwież dodatkowe komponenty
```

---

## Trwałość Preferencji

Preferencje motywów są automatycznie zapisywane i przywracane między sesjami aplikacji przez **UserDataManager**.

### Zapisywane Dane

```json
{
  "theme_preferences": {
    "mode": "dark",           // Aktualny tryb
    "palette": "green"        // Aktualna paleta
  },
  "custom_themes": {
    "Mój Motyw": {
      "dark": { /* kolory */ },
      "light": { /* kolory */ },
      "created_at": "2025-11-18T10:30:00Z"
    }
  }
}
```

### Automatyczne Zapisywanie

```python
# Przy zmianie motywu
def _on_mode_changed(self):
    data_manager = UserDataManager()
    data_manager.set_theme_preference(
        mode=self.current_mode.value,
        palette=self.current_palette.value
    )
```

### Przywracanie przy Starcie

```python
# W MainWindow.__init__()
data_manager = UserDataManager()
mode, palette = data_manager.get_theme_preference()

theme_manager = ThemeManager()
theme_manager.set_mode(ThemeMode(mode))
theme_manager.set_palette(ColorPalette(palette))
```

Szczegóły: [UI_USER_DATA_PERSISTENCE.md](UI_USER_DATA_PERSISTENCE.md)

---

## Kreator Własnych Motywów

**CustomThemeDialog** pozwala użytkownikom na tworzenie własnych palet kolorów.

### Funkcje
- Wybór koloru bazowego za pomocą color pickera
- Automatyczne generowanie 20+ odcieni
- Podgląd na żywo dla trybu ciemnego i jasnego
- Trwałe zapisywanie motywów
- Edycja istniejących motywów

### Uruchomienie

```python
from app.ui.custom_theme_dialog import CustomThemeDialog

dialog = CustomThemeDialog(parent=self)
dialog.theme_created.connect(self._on_custom_theme_created)
dialog.exec()
```

### Workflow
1. Użytkownik wybiera kolor bazowy (np. #16a34a)
2. Dialog automatycznie generuje pełną paletę
3. Użytkownik przełącza podgląd ciemny/jasny
4. Użytkownik nazywa motyw i zapisuje
5. Motyw jest dostępny od razu w przełączniku palet

Szczegóły: [UI_CUSTOM_THEME_DIALOG.md](UI_CUSTOM_THEME_DIALOG.md)

---

## Zobacz również

- [UI_CUSTOM_THEME_DIALOG.md](UI_CUSTOM_THEME_DIALOG.md) - Kreator własnych motywów
- [UI_USER_DATA_PERSISTENCE.md](UI_USER_DATA_PERSISTENCE.md) - Trwałość danych użytkownika
- [UI_STYLING.md](UI_STYLING.md) - Style i CSS
- [UI_COMPONENTS.md](UI_COMPONENTS.md) - Komponenty z obsługą motywów

---

## Testowanie
