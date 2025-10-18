from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize
from views.home_view import HomeView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Dashboard")
        self.setMinimumSize(1000, 800)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.home_view = HomeView()
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
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()
