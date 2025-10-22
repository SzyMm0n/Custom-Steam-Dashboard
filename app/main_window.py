import asyncio
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize
from .core.data.db import AsyncDatabase as Database # Import typu
from .ui.home_view import HomeView

class MainWindow(QMainWindow):
    """Główne okno aplikacji z paskiem narzędzi i widokami."""
    
    # ZMIANA 1: Konstruktor musi teraz przyjmować 'db'
    def __init__(self, db: Database): 
        super().__init__()
        self.setWindowTitle("Steam Dashboard")
        self.setMinimumSize(1000, 800)
        
        self._db = db # Zapisujemy instancję bazy danych

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # ZMIANA 2: Tworząc HomeView, przekazujemy instancję self._db
        self.home_view = HomeView(self._db)
        self.stack.addWidget(self.home_view)

        self._init_toolbar()

    def _init_toolbar(self):
        toolbar = QToolBar("Menu")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        home_action = QAction("Home", self)
        home_action.triggered.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        toolbar.addAction(home_action)

        refresh_action = QAction("Odśwież", self)
        refresh_action.triggered.connect(self.refresh_current_view)
        toolbar.addAction(refresh_action)

    def refresh_current_view(self):
        current_widget = self.stack.currentWidget()
        # Wymuś odświeżenie danych w aktywnym widoku (np. HomeView)
        if hasattr(current_widget, "refresh_data"):
            # Uruchomienie asynchronicznego zadania odświeżania
            asyncio.create_task(current_widget.refresh_data())