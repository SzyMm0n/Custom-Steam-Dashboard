import sys
import asyncio
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.main_window import MainWindow 
from qasync import QEventLoop


async def main_coro(app, window):
    """Main coroutine that runs and maintains the application window."""
    window.show()
    
    future = asyncio.Future()
    
    def on_quit():
        if not future.done():
            future.set_result(True)

    app.aboutToQuit.connect(on_quit)

    try:
        await future
    except asyncio.CancelledError:
        pass
        
    return None


def _set_app_icon(app: QApplication):
    """
    Set the application icon globally.
    This affects the taskbar icon and window decorations.

    Args:
        app: QApplication instance
    """
    # Possible icon paths (in order of preference)
    icon_paths = [
        # For bundled executable (PyInstaller)
        Path(sys._MEIPASS) / "icons" / "icon-128x128.png" if hasattr(sys, '_MEIPASS') else None,
        # For development - relative to this file
        Path(__file__).parent / "icons" / "icon-128x128.png",
        # Alternative sizes
        Path(__file__).parent / "icons" / "icon-32x32.png",
        Path(__file__).parent / "icons" / "icon-16x16.png",
    ]

    # Try each path until we find a valid icon
    for icon_path in icon_paths:
        if icon_path and icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                app.setWindowIcon(icon)
                return

    # If no icon found, log a warning but continue
    print("Warning: Could not find application icon")


def main():
    """
    Main entry point for the Custom Steam Dashboard application.
    
    The application now fetches data from a backend server instead of
    maintaining a local database. Make sure the server is running at
    http://localhost:8000 before starting the application.
    """
    # 1. Initialize Qt application
    app = QApplication(sys.argv)
    
    # Set application icon (for taskbar, etc.)
    _set_app_icon(app)

    # 2. Setup event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Create main window (connects to server)
    # You can pass a custom server URL as: MainWindow(server_url="http://your-server:8000")
    window = MainWindow()
    
    # 4. Run main coroutine
    with loop:
        try:
            loop.run_until_complete(main_coro(app, window))
        except Exception as e:
            print(f"Critical error while running application: {e}")


if __name__ == "__main__":
    main()

