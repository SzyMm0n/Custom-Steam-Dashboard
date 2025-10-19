import asyncio
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QFrame
from PySide6.QtCore import QTimer, Qt
from app.core.services.steam_api import SteamStoreClient

# Statyczna lista popularnych AppID do sprawdzenia liczby graczy
TOP_GAME_APP_IDS = [
    730,    # Counter-Strike 2
    570,    # Dota 2
    252490, # Rust
    271590, # Grand Theft Auto V
    1172470, # Apex Legends
    1091500, # Cyberpunk 2077
    1245620, # Elden Ring
    304930, # Unturned
    440,    # Team Fortress 2
    582010, # Monster Hunter: World
    238960, # Path of Exile
    1174180, # Red Dead Redemption 2
    892970, # Valheim
    546560, # Half-Life: Alyx
    420,    # Half-Life 2: Deathmatch
]


class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self) 

        # === Sekcja 1: Live Games Count (Gracze Online) ===
        self.top_live_title = QLabel("Live Games Count")
        self.top_live_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.top_live_list = QListWidget()

        # Separator 1
        self.separator_1 = QFrame()
        self.separator_1.setFrameShape(QFrame.HLine)
        self.separator_1.setFrameShadow(QFrame.Sunken)

        # === Sekcja 2: Best Deals (Największe Promocje) ===
        self.trending_title = QLabel("Best Deals")
        self.trending_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.trending_list = QListWidget()

        # Separator 2
        self.separator_2 = QFrame()
        self.separator_2.setFrameShape(QFrame.HLine)
        self.separator_2.setFrameShadow(QFrame.Sunken)

        # === Sekcja 3: Best Upcoming Releases (Nadchodzące) ===
        self.top_title = QLabel("Best Upcoming Releases")
        self.top_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.top_list = QListWidget()

        # Dodanie do layoutu
        self.layout.addWidget(self.top_live_title)
        self.layout.addWidget(self.top_live_list)
        self.layout.addWidget(self.separator_1)
        self.layout.addWidget(self.trending_title)
        self.layout.addWidget(self.trending_list)
        self.layout.addWidget(self.separator_2)
        self.layout.addWidget(self.top_title)
        self.layout.addWidget(self.top_list)

        # Odśwież dane po załadowaniu GUI
        QTimer.singleShot(100, self.refresh)

    def refresh(self):
        """Odświeża dane we wszystkich sekcjach asynchronicznie."""
        self.top_live_list.clear() 
        self.trending_list.clear()
        self.top_list.clear()

        self.top_live_list.addItem("Ładowanie danych...")
        self.trending_list.addItem("Ładowanie danych...")
        self.top_list.addItem("Ładowanie danych...")
        
        asyncio.create_task(self._load_data_async())

    async def _load_data_async(self):
        """Asynchroniczne pobieranie danych z API."""
        self.top_live_list.clear()
        self.trending_list.clear()
        self.top_list.clear()
        
        try:
            async with SteamStoreClient(timeout=15.0) as client:
                
                # --- 1. LIVE GAMES COUNT (Gracze Online) ---
                await self._load_top_live_games(client)

                # --- 2. BEST DEALS (Największe Promocje) ---
                best_deals = await client._get_featured_category_items("specials", cc="pl", lang="pl", limit=15)
                
                if not best_deals:
                    self.trending_list.addItem("Brak danych o promocjach lub błąd połączenia z API.")
                for g in best_deals:
                    name = g.name or "Nieznana gra"
                    price_pln = f"{(g.final_price or 0) / 100:.2f} zł"
                    # Usunięto emotkę '💸'
                    discount = f" ({g.discount_percent}% ZNIŻKI)" if g.discount_percent else ""
                    self.trending_list.addItem(f"{name} — {price_pln}{discount}") 

                # --- 3. BEST UPCOMING RELEASES (Nadchodzące) ---
                top = await client.get_coming_soon(limit=15) 
                if not top:
                    self.top_list.addItem("Brak danych o nadchodzących grach lub błąd połączenia z API.")
                for g in top:
                    name = g.name or "Nieznana gra"
                    # Usunięto datę wydania
                    self.top_list.addItem(f"{name}") 
                    
        except Exception as e:
            error_msg = f"Błąd krytyczny pobierania danych: {e}"
            self.top_live_list.addItem(error_msg)
            self.trending_list.addItem(error_msg)
            self.top_list.addItem(error_msg)
            
    async def _load_top_live_games(self, client: SteamStoreClient):
        """Pobiera dane o liczbie graczy dla predefiniowanych gier i nazwach."""
        
        # 1. Tworzymy zadania do jednoczesnego pobrania statystyk i nazw
        player_tasks = [client.get_number_of_current_players(appid) for appid in TOP_GAME_APP_IDS]
        detail_tasks = [client.get_app_details(appid, cc="pl", lang="pl") for appid in TOP_GAME_APP_IDS]
            
        player_counts = await asyncio.gather(*player_tasks, return_exceptions=True)
        game_details = await asyncio.gather(*detail_tasks, return_exceptions=True)

        # 2. Łączymy wyniki i sortujemy
        results = []
        
        for i, appid in enumerate(TOP_GAME_APP_IDS):
            count_result = player_counts[i]
            details_result = game_details[i]
            
            if isinstance(count_result, Exception):
                continue 
            
            name = f"AppID {appid}"
            if not isinstance(details_result, Exception) and details_result is not None:
                name = details_result.name
            
            if count_result.player_count > 0:
                results.append({
                    "name": name,
                    "players": count_result.player_count,
                })

        results.sort(key=lambda x: x["players"], reverse=True)

        # 3. Wyświetlanie
        if not results:
             self.top_live_list.addItem("Brak danych lub błąd API statystyk graczy.")
        else:
            for item in results[:15]: 
                players_formatted = f'{item["players"]:,}'.replace(",", " ") 
                self.top_live_list.addItem(f'{item["name"]} — Graczy online: {players_formatted}')
