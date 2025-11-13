# Dokumentacja Main Window

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Przegląd

**Plik:** `app/main_window.py`

**MainWindow** to główne okno aplikacji z toolbarem i nawigacją między widokami.

---

## Klasa MainWindow

```python
class MainWindow(QMainWindow):
    """
    Główne okno aplikacji.
    
    Features:
        - Toolbar z akcjami nawigacji
        - QStackedWidget do przełączania widoków
        - HomeView i LibraryView
        - Refresh functionality
    """
    
    def __init__(self, server_url: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Steam Dashboard")
        self.setMinimumSize(1000, 800)
        
        if server_url is None:
            server_url = os.getenv("SERVER_URL", "http://localhost:8000")
        self._server_url = server_url
        
        self._set_window_icon()
        self._init_ui()
        self._init_toolbar()
```

---

## Struktura UI

```
┌────────────────────────────────────────────────┐
│  [Home] [Biblioteka] [Odśwież]                 │ <- Toolbar
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │                                          │  │
│  │          QStackedWidget                  │  │
│  │                                          │  │
│  │  • HomeView (index 0)                    │  │
│  │  • LibraryView (index 1)                 │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                │
└────────────────────────────────────────────────┘
```

---

## Główne Metody

### Nawigacja

```python
def navigate_to_home(self):
    """Przełącza na HomeView."""
    self.stacked_widget.setCurrentIndex(0)

def navigate_to_library(self):
    """Przełącza na LibraryView."""
    self.stacked_widget.setCurrentIndex(1)
```

### Odświeżanie

```python
def refresh_current_view(self):
    """
    Odświeża aktualny widok.
    Wywołuje refresh_data() jeśli dostępne.
    """
    current_widget = self.stacked_widget.currentWidget()
    if hasattr(current_widget, 'refresh_data'):
        asyncio.create_task(current_widget.refresh_data())
```

---

## Toolbar Actions

```python
def _init_toolbar(self):
    """Tworzy toolbar z akcjami."""
    toolbar = self.addToolBar("Main")
    toolbar.setMovable(False)
    
    # Home action
    home_action = QAction("Home", self)
    home_action.triggered.connect(self.navigate_to_home)
    toolbar.addAction(home_action)
    
    # Library action
    library_action = QAction("Biblioteka gier", self)
    library_action.triggered.connect(self.navigate_to_library)
    toolbar.addAction(library_action)
    
    # Refresh action
    refresh_action = QAction("Odśwież", self)
    refresh_action.triggered.connect(self.refresh_current_view)
    toolbar.addAction(refresh_action)
```

---

## Przykład Użycia

```python
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
import sys

app = QApplication(sys.argv)
window = MainWindow(server_url="http://localhost:8000")
window.show()
sys.exit(app.exec())
```

---

## Następne Kroki

- **Home View**: [UI_HOME_VIEW.md](UI_HOME_VIEW.md)
- **Library View**: [UI_LIBRARY_VIEW.md](UI_LIBRARY_VIEW.md)
- **Authentication**: [UI_AUTHENTICATION.md](UI_AUTHENTICATION.md)

