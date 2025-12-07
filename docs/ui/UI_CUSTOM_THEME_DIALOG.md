# Kreator Własnych Motywów - CustomThemeDialog

**Data aktualizacji:** 2025-11-18  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Funkcjonalności](#funkcjonalności)
3. [Architektura](#architektura)
4. [Użycie](#użycie)
5. [Generowanie Palety](#generowanie-palety)
6. [Podgląd na Żywo](#podgląd-na-żywo)
7. [Zapisywanie Motywu](#zapisywanie-motywu)

---

## Przegląd

**CustomThemeDialog** to interaktywny kreator motywów pozwalający użytkownikom na tworzenie własnych palet kolorów. Dialog automatycznie generuje kompletny zestaw kolorów na podstawie jednego koloru bazowego.

### Lokalizacja
```
app/ui/custom_theme_dialog.py
```

### Klasa
```python
class CustomThemeDialog(QDialog)
```

---

## Funkcjonalności

### Kreator Kolorów
- ✅ **Wybór koloru bazowego** - picker z pełną paletą kolorów
- ✅ **Automatyczne generowanie** - tworzy 20+ odcieni na podstawie koloru bazowego
- ✅ **Tryb ciemny/jasny** - osobne palety dla każdego trybu
- ✅ **Podgląd na żywo** - natychmiastowa wizualizacja zmian

### Algorytm Generowania
- ✅ **HSL color space** - precyjna kontrola jasności i nasycenia
- ✅ **Gradient kolorów** - płynne przejścia między odcieniami
- ✅ **Dostępność** - wysoki kontrast dla czytelności
- ✅ **Spójność** - harmonijny układ kolorów

### Podgląd
- ✅ **Kolory podstawowe** - background, surface, border
- ✅ **Kolory tekstu** - primary, secondary, muted
- ✅ **Kolory akcentujące** - accent, hover, pressed
- ✅ **Elementy UI** - przyciski, inputy, etykiety

### Zapisywanie
- ✅ **Walidacja nazwy** - sprawdzanie unikalności
- ✅ **Trwałe przechowywanie** - via UserDataManager
- ✅ **Natychmiastowe zastosowanie** - motyw aktywny od razu
- ✅ **Edycja** - możliwość modyfikacji istniejących motywów

---

## Architektura

```
┌──────────────────────────────────────────────────────────────┐
│            CustomThemeDialog (QDialog)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Title: "Kreator własnego motywu"                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Color Selection                                       │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Kolor bazowy: [████] [Wybierz kolor...]         │  │  │
│  │  │  RGB: 22, 163, 74  |  HEX: #16a34a               │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Preview Mode                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  ◉ Podgląd ciemny   ○ Podgląd jasny              │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Live Preview                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │  │
│  │  │  │ Button 1 │  │ Button 2 │  │ Button 3 │        │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘        │  │  │
│  │  │                                                  │  │  │
│  │  │  Primary Text                                    │  │  │
│  │  │  Secondary Text                                  │  │  │
│  │  │  Muted Text                                      │  │  │
│  │  │                                                  │  │  │
│  │  │  [Input field example]                           │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Theme Name                                            │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Nazwa motywu: [Mój Zielony Motyw_____________]  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  [Zapisz i zastosuj]  [Anuluj]                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                     │
                     │ theme_created (Signal)
                     ▼
            ThemeManager (apply custom theme)
                     │
                     ▼
            UserDataManager (save preferences)
```

---

## Użycie

### Otwieranie Dialogu

```python
from app.ui.custom_theme_dialog import CustomThemeDialog

# Z ThemeSwitcher lub menu aplikacji
def _show_custom_theme_creator(self):
    """Pokaż kreator własnego motywu."""
    dialog = CustomThemeDialog(parent=self)
    dialog.theme_created.connect(self._on_custom_theme_created)
    dialog.exec()
```

### Obsługa Utworzenia Motywu

```python
def _on_custom_theme_created(self, dark_colors: Dict, light_colors: Dict):
    """
    Obsłuż utworzenie nowego motywu.
    
    Args:
        dark_colors: Słownik kolorów dla trybu ciemnego
        light_colors: Słownik kolorów dla trybu jasnego
    """
    logger.info("Custom theme created")
    
    # Motyw zostanie automatycznie zastosowany przez ThemeManager
    # i zapisany przez UserDataManager
    
    # Przykładowa struktura dark_colors/light_colors:
    # {
    #     "background": "#0b0b0b",
    #     "surface": "#1a1a1a",
    #     "text_primary": "#ffffff",
    #     "text_secondary": "#e5e5e5",
    #     "accent": "#16a34a",
    #     "accent_hover": "#22c55e",
    #     "accent_pressed": "#15803d",
    #     ...
    # }
```

### Integracja z ThemeSwitcher

```python
# W ThemeSwitcher dodaj przycisk "Custom"
custom_button = QPushButton("Stwórz własny...")
custom_button.clicked.connect(self._show_custom_theme_creator)
```

---

## Generowanie Palety

### Algorytm

Dialog wykorzystuje **HSL color space** do generowania spójnej palety:

1. **Kolor bazowy** → konwersja RGB → HSL
2. **Generowanie odcieni**:
   - Jasność (Lightness): 10% - 95%
   - Nasycenie (Saturation): 60% - 100%
   - Odcień (Hue): bazowy ± warianty

### Tryb Ciemny

```python
def _generate_dark_palette(base_color: QColor) -> Dict[str, str]:
    """
    Generuj paletę dla trybu ciemnego.
    
    Cechy:
    - Ciemne tła (L: 5-15%)
    - Jasny tekst (L: 90-98%)
    - Średnie accent (L: 50-60%)
    - Wysoki kontrast
    """
    h, s, l, _ = base_color.getHslF()
    
    return {
        "background": QColor.fromHslF(h, s * 0.2, 0.05),     # Bardzo ciemny
        "surface": QColor.fromHslF(h, s * 0.3, 0.10),        # Ciemny
        "text_primary": QColor.fromHslF(h, 0.0, 0.98),       # Prawie biały
        "accent": QColor.fromHslF(h, s * 0.9, 0.55),         # Nasycony
        # ... więcej kolorów
    }
```

### Tryb Jasny

```python
def _generate_light_palette(base_color: QColor) -> Dict[str, str]:
    """
    Generuj paletę dla trybu jasnego.
    
    Cechy:
    - Jasne tła (L: 95-100%)
    - Ciemny tekst (L: 10-20%)
    - Żywy accent (L: 45-55%)
    - Subtelne cienie
    """
    h, s, l, _ = base_color.getHslF()
    
    return {
        "background": QColor.fromHslF(h, s * 0.05, 0.99),    # Prawie biały
        "surface": QColor.fromHslF(h, s * 0.1, 0.96),        # Bardzo jasny
        "text_primary": QColor.fromHslF(h, s * 0.3, 0.12),   # Bardzo ciemny
        "accent": QColor.fromHslF(h, s * 0.95, 0.50),        # Saturated
        # ... więcej kolorów
    }
```

---

## Podgląd na Żywo

### Elementy Podglądu

Dialog pokazuje następujące elementy w wybranym motywie:

#### Przyciski
```
[Normal Button]  [Hover]  [Pressed]  [Disabled]
```

#### Tekst
```
Primary text - główny tekst aplikacji
Secondary text - tekst pomocniczy
Muted text - tekst wyblakły
```

#### Pola Wejściowe
```
[Normal input field______]
[Focused input field_____]
[Disabled input field____]
```

#### Panele
```
╔═══════════════════════╗
║  Panel example        ║
║  with border          ║
╚═══════════════════════╝
```

### Przełączanie Trybów

Radio buttons pozwalają przełączać się między podglądem ciemnym a jasnym:

```python
def _on_preview_mode_changed(self):
    """Zmień tryb podglądu."""
    if self._dark_preview_radio.isChecked():
        self._preview_mode = "dark"
    else:
        self._preview_mode = "light"
    
    self._update_preview()
```

---

## Zapisywanie Motywu

### Walidacja Nazwy

```python
def _validate_theme_name(self, name: str) -> tuple[bool, str]:
    """
    Waliduj nazwę motywu.
    
    Returns:
        (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Nazwa nie może być pusta"
    
    if len(name) < 3:
        return False, "Nazwa musi mieć co najmniej 3 znaki"
    
    if len(name) > 50:
        return False, "Nazwa może mieć maksymalnie 50 znaków"
    
    # Sprawdź czy nazwa już istnieje
    data_manager = UserDataManager()
    if data_manager.custom_theme_exists(name):
        return False, f"Motyw '{name}' już istnieje"
    
    return True, ""
```

### Zapis do UserDataManager

```python
def _save_theme(self):
    """Zapisz motyw i zastosuj."""
    theme_name = self._name_input.text().strip()
    
    # Waliduj
    is_valid, error = self._validate_theme_name(theme_name)
    if not is_valid:
        QMessageBox.warning(self, "Błąd", error)
        return
    
    # Zapisz przez UserDataManager
    data_manager = UserDataManager()
    data_manager.save_custom_theme(
        name=theme_name,
        dark_colors=self._dark_colors,
        light_colors=self._light_colors
    )
    
    # Emituj sygnał
    self.theme_created.emit(self._dark_colors, self._light_colors)
    
    # Zastosuj natychmiast przez ThemeManager
    theme_manager = ThemeManager()
    theme_manager.set_custom_theme(theme_name)
    
    self.accept()
```

---

## Przykłady Kolorów Bazowych

### Popularne Kombinacje

#### Zielony (domyślny)
```python
base_color = QColor("#16a34a")  # Green-600
# Idealny dla: uniwersalnego użytku
```

#### Niebieski
```python
base_color = QColor("#3b82f6")  # Blue-500
# Idealny dla: profesjonalnego wyglądu
```

#### Fioletowy
```python
base_color = QColor("#a855f7")  # Purple-500
# Idealny dla: kreatywnego stylu
```

#### Czerwony
```python
base_color = QColor("#ef4444")  # Red-500
# Idealny dla: energetycznego wyglądu
```

#### Pomarańczowy
```python
base_color = QColor("#f97316")  # Orange-500
# Idealny dla: ciepłego wyglądu
```

#### Cyan
```python
base_color = QColor("#06b6d4")  # Cyan-500
# Idealny dla: technologicznego wyglądu
```

---

## Struktura Zapisanego Motywu

```json
{
  "custom_themes": {
    "Mój Zielony Motyw": {
      "dark": {
        "background": "#0b0b0b",
        "surface": "#1a1a1a",
        "surface_variant": "#2b2b2b",
        "border": "#3a3a3a",
        "text_primary": "#ffffff",
        "text_secondary": "#e5e5e5",
        "text_muted": "#a3a3a3",
        "accent": "#16a34a",
        "accent_hover": "#22c55e",
        "accent_pressed": "#15803d",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6"
      },
      "light": {
        "background": "#ffffff",
        "surface": "#f8f9fa",
        "surface_variant": "#e5e7eb",
        "border": "#d1d5db",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4b5563",
        "text_muted": "#9ca3af",
        "accent": "#16a34a",
        "accent_hover": "#15803d",
        "accent_pressed": "#166534",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6"
      },
      "created_at": "2025-11-18T10:30:00Z"
    }
  }
}
```

---

## Edycja Istniejącego Motywu

```python
def _edit_custom_theme(self, theme_name: str):
    """Edytuj istniejący motyw."""
    data_manager = UserDataManager()
    theme_data = data_manager.get_custom_theme(theme_name)
    
    if not theme_data:
        return
    
    # Otwórz dialog z istniejącymi kolorami
    dialog = CustomThemeDialog(parent=self)
    dialog.load_existing_theme(theme_name, theme_data)
    dialog.exec()
```

---

## Zobacz również

- [UI_THEME_SYSTEM.md](UI_THEME_SYSTEM.md) - System motywów
- [UI_USER_DATA_PERSISTENCE.md](UI_USER_DATA_PERSISTENCE.md) - Trwałość danych
- [UI_COMPONENTS.md](UI_COMPONENTS.md) - Komponenty UI

---

**Plik źródłowy:** `app/ui/custom_theme_dialog.py`  
**Używane przez:** ThemeSwitcher, MainWindow  
**Wymagania:** PySide6, ThemeManager, UserDataManager, QColorDialog

