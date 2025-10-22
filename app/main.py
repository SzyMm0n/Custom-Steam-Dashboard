import sys
import asyncio
from PySide6.QtWidgets import QApplication

# POPRAWIONE: Teraz importujemy main_window bezpośrednio z katalogu 'app'
from app.core.data.db import AsyncDatabase as Database
from app.core.data.retention_job import seed_watchlist_top
from app.main_window import MainWindow 

from qasync import QEventLoop, run 


async def bootstrap(app) -> Database: 
    """Inicjalizuje bazę danych i zasiewa watchlistę."""
    # Używamy AsyncDatabase, aby zapewnić, że jest to klasa z wrapperami do asyncio.to_thread
    db = Database()
    try:
        db.init_schema() 
        # Zmieniamy limit na 30, aby przyspieszyć seeding podczas debugowania
        inserted_count = await seed_watchlist_top(db, limit=30) 
        print(f"Wstawiono/aktualizowano {inserted_count} pozycji w watchliście.")
    except Exception as e:
        print(f"Błąd podczas seedingu bazy danych: {e}")
        
    return db


async def main_coro(app, window):
    """Główna korutyna, która uruchamia i utrzymuje okno aplikacji."""
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
    # 1. Inicjalizacja aplikacji
    app = QApplication(sys.argv)
    
    # ZMIANA: Odbieramy instancję bazy danych z bootstrap
    # Nazwa klasy w 'db.py' to SyncDatabase i AsyncDatabase
    # Zwrócony typ to AsyncDatabase
    db_instance = asyncio.run(bootstrap(app)) 
    
    # 2. Utworzenie i ustawienie pętli zdarzeń QEventLoop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Utworzenie instancji okna
    # ZMIANA: Przekazujemy instancję db_instance do MainWindow
    window = MainWindow(db_instance)
    
    # 4. Uruchomienie głównej korutyny
    with loop:
        try:
            loop.run_until_complete(main_coro(app, window))
        except Exception as e:
            # Poprawna obsługa błędu, zamiast poprzedniego wywołania print
            print(f"Krytyczny błąd podczas uruchamiania aplikacji: {e}")


if __name__ == "__main__":
    main()