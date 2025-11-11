import sys
import asyncio
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

# Load environment variables before any other imports that use them
load_dotenv()

from app.main_window import MainWindow 
from app.core.services.server_client import ServerClient
from qasync import QEventLoop


async def authenticate_with_server(server_url: str) -> bool:
    """
    Authenticate with the server before starting the GUI.

    Args:
        server_url: Server URL

    Returns:
        True if authentication successful, False otherwise
    """
    try:
        client = ServerClient(server_url)
        success = await client.authenticate()
        if success:
            print("✓ Successfully authenticated with server")
            return True
        else:
            print("✗ Failed to authenticate with server")
            return False
    except Exception as e:
        print(f"✗ Error during authentication: {e}")
        return False


async def main_coro(app, server_url: str):
    """Main coroutine that authenticates and runs the application window."""

    # Step 1: Authenticate with server
    print("Authenticating with server...")
    auth_success = await authenticate_with_server(server_url)

    if not auth_success:
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Authentication Failed")
        msg.setText("Failed to authenticate with the server.")
        msg.setInformativeText(
            f"Please ensure:\n"
            f"1. The server is running at {server_url}\n"
            f"2. CLIENT_ID and CLIENT_SECRET are set correctly in environment\n"
            f"3. Server security configuration matches client credentials"
        )
        msg.exec()
        return False

    # Step 2: Create and show main window
    window = MainWindow(server_url)
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
    
    The application requires authentication with the backend server.
    Make sure:
    1. The server is running and accessible (configure via SERVER_URL environment variable)
    2. CLIENT_ID and CLIENT_SECRET environment variables are set
    3. Server CLIENTS_JSON configuration includes your client credentials
    """
    # 1. Initialize Qt application
    app = QApplication(sys.argv)
    
    # Set application icon (for taskbar, etc.)
    _set_app_icon(app)

    # 2. Setup event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Server URL (can be customized via environment variable)
    import os
    server_url = os.getenv("SERVER_URL", "http://localhost:8000")

    # 4. Authenticate and run main coroutine
    with loop:
        try:
            result = loop.run_until_complete(main_coro(app, server_url))
            if result is False:
                # Authentication failed, exit
                sys.exit(1)
        except Exception as e:
            print(f"Critical error while running application: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

