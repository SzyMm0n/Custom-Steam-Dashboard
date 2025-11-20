# Dialog Filtrów Promocji - DealsFilterDialog

**Data aktualizacji:** 2025-11-18  
**Wersja:** 1.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Funkcjonalności](#funkcjonalności)
3. [Architektura](#architektura)
4. [Użycie](#użycie)
5. [Filtry](#filtry)
6. [Przykłady](#przykłady)

---

## Przegląd

**DealsFilterDialog** to zaawansowany dialog do filtrowania promocji gier w widoku Deals. Umożliwia precyzyjne określenie kryteriów wyszukiwania najlepszych okazji.

### Lokalizacja
```
app/ui/deals_filter_dialog.py
```

### Klasa
```python
class DealsFilterDialog(QDialog)
```

---

## Funkcjonalności

### Filtry Cenowe
- ✅ **Minimalny procent zniżki** - tylko promocje powyżej określonego progu (0-99%)
- ✅ **Maksymalna cena** - górny limit ceny po zniżce
- ✅ **Minimalna cena** - dolny limit ceny po zniżce

### Filtry Sklepów
- ✅ **Steam** - promocje w Steam Store
- ✅ **GOG** - promocje w GOG.com
- ✅ **Epic Games** - promocje w Epic Games Store
- ✅ **Humble Bundle** - promocje w Humble Store

### Dodatkowe Opcje
- ✅ **Filtr treści dla dorosłych** - ukrywa/pokazuje gry z mature content
- ✅ **Sortowanie** - według zniżki, ceny lub metascores

### Interfejs
- ✅ **Podgląd na żywo** - licznik aktywnych filtrów
- ✅ **Resetowanie** - szybki powrót do domyślnych ustawień
- ✅ **Integracja z motywami** - pełne wsparcie dla systemu motywów

---

## Architektura

```
┌──────────────────────────────────────────────────────────┐
│              DealsFilterDialog (QDialog)                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Discount Group                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  [─────●────────] Min Discount: 50%          │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Price Group                                       │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Min Price: [  5.00] USD                     │  │  │
│  │  │  Max Price: [ 50.00] USD                     │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Shops                                             │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  [✓] Steam     [✓] GOG                       │  │  │
│  │  │  [✓] Epic      [✓] Humble                    │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Other Options                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  [✓] Include mature content                  │  │  │
│  │  │  Sort by: [Discount ▼]                       │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Active filters: 3                                 │  │
│  │                                                    │  │
│  │  [Apply Filters]  [Reset]  [Cancel]                │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
           │
           │ filters_applied (Signal)
           ▼
     DealsView (parent)
```

---

## Użycie

### Inicjalizacja

```python
from app.ui.deals_filter_dialog import DealsFilterDialog

# Tworzenie dialogu z aktualnymi filtrami
current_filters = {
    "min_discount": 50,
    "max_price": 20.0,
    "shops": ["steam", "gog"],
    "include_mature": False
}

dialog = DealsFilterDialog(current_filters, parent=self)
dialog.filters_applied.connect(self._on_filters_applied)
dialog.exec()
```

### Obsługa Sygnałów

```python
def _on_filters_applied(self, filters: Dict[str, Any]):
    """
    Obsługa zastosowania filtrów.
    
    Args:
        filters: Słownik z wartościami filtrów
    """
    logger.info(f"Applying filters: {filters}")
    
    # Przykładowa struktura filters:
    # {
    #     "min_discount": 50,           # int (0-99)
    #     "min_price": 5.0,             # float
    #     "max_price": 50.0,            # float
    #     "shops": ["steam", "gog"],    # list[str]
    #     "include_mature": True,       # bool
    #     "sort_by": "discount"         # str
    # }
    
    # Przeładuj listę promocji z nowymi filtrami
    await self._load_deals(filters)
```

### Integracja z DealsView

```python
class DealsView(QWidget):
    def _show_filter_dialog(self):
        """Wyświetl dialog filtrów."""
        dialog = DealsFilterDialog(self._current_filters, parent=self)
        dialog.filters_applied.connect(self._apply_filters)
        dialog.exec()
    
    async def _apply_filters(self, filters: Dict[str, Any]):
        """Zastosuj nowe filtry i przeładuj promocje."""
        self._current_filters = filters
        await self._load_deals()
```

---

## Filtry

### Discount Filter
**Widget:** `QSlider` + `QSpinBox`  
**Zakres:** 0-99%  
**Domyślnie:** 0% (wszystkie promocje)

Filtruje promocje według minimalnego procentu zniżki.

```python
# Przykład: tylko promocje >= 50%
filters["min_discount"] = 50
```

### Price Filters
**Widgets:** `QDoubleSpinBox` × 2  
**Zakres:** 0.0 - 999.99 USD  
**Domyślnie:** Min: 0.0, Max: 999.99

Określa zakres cenowy po zniżce.

```python
# Przykład: cena między $5 a $20
filters["min_price"] = 5.0
filters["max_price"] = 20.0
```

### Shop Filters
**Widget:** `QCheckBox` × 4  
**Opcje:** steam, gog, epic, humble  
**Domyślnie:** wszystkie zaznaczone

Wybór sklepów do przeszukania.

```python
# Przykład: tylko Steam i GOG
filters["shops"] = ["steam", "gog"]
```

### Mature Content Filter
**Widget:** `QCheckBox`  
**Domyślnie:** True (pokazuj wszystko)

Ukrywa/pokazuje gry z treściami dla dorosłych.

```python
filters["include_mature"] = False  # Ukryj mature content
```

### Sort Options
**Widget:** `QComboBox`  
**Opcje:**
- `discount` - Sortuj według % zniżki (malejąco)
- `price` - Sortuj według ceny (rosnąco)
- `metacritic` - Sortuj według ocen Metacritic (malejąco)

```python
filters["sort_by"] = "discount"
```

---

## Przykłady

### Przykład 1: Szukanie super okazji

```python
filters = {
    "min_discount": 75,        # Zniżka >= 75%
    "max_price": 10.0,         # Cena <= $10
    "shops": ["steam"],        # Tylko Steam
    "sort_by": "discount"      # Najwyższe zniżki pierwsze
}
```

### Przykład 2: Promocje AAA w GOG

```python
filters = {
    "min_discount": 30,        # Zniżka >= 30%
    "min_price": 10.0,         # AAA games (> $10)
    "shops": ["gog"],          # Tylko GOG
    "sort_by": "metacritic"    # Najlepiej oceniane pierwsze
}
```

### Przykład 3: Family-friendly w każdym sklepie

```python
filters = {
    "min_discount": 0,         # Wszystkie zniżki
    "include_mature": False,   # Bez treści dla dorosłych
    "shops": ["steam", "gog", "epic", "humble"],
    "sort_by": "price"         # Najtańsze pierwsze
}
```

---

## Resetowanie Filtrów

Przycisk **Reset** przywraca domyślne wartości:

```python
DEFAULT_FILTERS = {
    "min_discount": 0,
    "min_price": 0.0,
    "max_price": 999.99,
    "shops": ["steam", "gog", "epic", "humble"],
    "include_mature": True,
    "sort_by": "discount"
}
```

---

## Integracja z Motywami

Dialog automatycznie dostosowuje się do aktywnego motywu aplikacji:

```python
def __init__(self, current_filters, parent=None):
    super().__init__(parent)
    
    # Theme manager
    self._theme_manager = ThemeManager()
    self._theme_manager.theme_changed.connect(self._on_theme_changed)
    
    # Zastosuj aktualny motyw
    self._apply_current_theme()

def _on_theme_changed(self, mode: str, palette: str):
    """Reaguj na zmiany motywu."""
    self._apply_current_theme()
```

---

## Zobacz również

- [UI_DEALS_VIEW.md](UI_DEALS_VIEW.md) - Główny widok promocji
- [UI_THEME_SYSTEM.md](UI_THEME_SYSTEM.md) - System motywów
- [UI_COMPONENTS.md](UI_COMPONENTS.md) - Reużywalne komponenty

---

**Plik źródłowy:** `app/ui/deals_filter_dialog.py`  
**Używane przez:** `DealsView`  
**Wymagania:** PySide6, ThemeManager

