import sys
import asyncio
from PySide6.QtWidgets import QApplication

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


def main():
    """
    Main entry point for the Custom Steam Dashboard application.
    
    The application now fetches data from a backend server instead of
    maintaining a local database. Make sure the server is running at
    http://localhost:8000 before starting the application.
    """
    # 1. Initialize Qt application
    app = QApplication(sys.argv)
    
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

