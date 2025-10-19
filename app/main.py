import sys
import asyncio
from PySide6.QtWidgets import QApplication
from app.core.data.db import Database
from app.core.data.retention_job import seed_watchlist_top
from main_window import MainWindow
from qasync import QEventLoop, run

async def bootstrap(app):
    db = Database()
    try:
        # Upewnij się, że schemat istnieje
        db.init_schema()
        inserted_count = await seed_watchlist_top(db, limit=150)
        print(f"Wstawiono/aktualizowano {inserted_count} pozycji w watchliście.")
    except Exception as e:
        print(f"Seeding failed: {e}")

async def main_coro(app, window):
    """Główna korutyna, która uruchamia i utrzymuje okno."""
    window.show()
    
    future = asyncio.Future()
    
    def on_quit():
        # Ustawienie wyniku Future (kończy await future)
        if not future.done():
            future.set_result(True)

    # KLUCZOWE: Łączymy sygnał o zamykaniu aplikacji (QApplication) z naszą funkcją
    app.aboutToQuit.connect(on_quit)

    # Czekamy, aż future zostanie zakończone (czyli aplikacja się zamknie)
    try:
        await future
    except asyncio.CancelledError:
        pass
    
    return None

def main():
    # 1. Inicjalizacja aplikacji
    app = QApplication(sys.argv)
    asyncio.run(bootstrap(app))
    
    # 2. Utworzenie i ustawienie pętli zdarzeń QEventLoop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Utworzenie instancji okna
    # ZAKŁADAMY, że MainWindow jest importowane poprawnie z main_window
    window = MainWindow() 

    # 4. Użycie qasync.run()
    try:
        # Przekazujemy app i window do main_coro
        sys.exit(run(main_coro(app, window)))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Wystąpił błąd podczas uruchamiania: {e}")
        
if __name__ == "__main__":
    main()
