# Migracja z CheapShark API do IsThereAnyDeal API

## Przegląd zmian

Aplikacja Custom Steam Dashboard została zaktualizowana, aby korzystać z **IsThereAnyDeal API** zamiast CheapShark API do pobierania informacji o promocjach gier.

## Dlaczego IsThereAnyDeal?

IsThereAnyDeal API oferuje:
- ✅ Bardziej aktualne dane o cenach i promocjach
- ✅ Wsparcie dla większej liczby sklepów (Steam, GOG, Epic Games, Humble Bundle, itd.)
- ✅ Lepsze filtrowanie według platform (focus na Steam)
- ✅ Oficjalne API z dokumentacją
- ✅ OAuth2 authentication dla lepszego bezpieczeństwa

## Zmiany w architekturze

### Backend (Server)

#### Nowe pliki:
- **`server/services/deals_service.py`** - Nowy serwis do komunikacji z IsThereAnyDeal API
  - Klasa `IsThereAnyDealClient` implementuje `IDealsService`
  - OAuth2 authentication
  - Metody:
    - `get_best_deals()` - Pobiera najlepsze aktualne promocje
    - `get_game_prices()` - Pobiera informacje o cenach dla konkretnej gry (Steam AppID)
    - `search_game()` - Wyszukuje grę po tytule
    - `get_game_info_by_steam_id()` - Pobiera informacje o grze używając Steam AppID

#### Zaktualizowane pliki:
- **`server/services/models.py`** - Dodano nowe modele Pydantic:
  - `DealInfo` - Informacje o promocji
  - `GamePrice` - Informacje o cenie gry
  
- **`server/app.py`** - Dodano nowe endpointy API:
  - `GET /api/deals/best` - Pobiera najlepsze promocje
    - Query params: `limit` (1-50), `min_discount` (0-100)
  - `GET /api/deals/game/{appid}` - Pobiera informacje o promocjach dla konkretnej gry
    - Najpierw sprawdza bazę danych
    - Jeśli gry nie ma w DB, pobiera z Steam API i dodaje do bazy
    - Zwraca najlepszą dostępną promocję

### Frontend (Desktop App)

#### Nowe pliki:
- **`app/core/services/deals_api.py`** - Klient do komunikacji z backendem
  - Klasa `DealsApiClient`
  - Metody:
    - `get_current_deals()` - Pobiera aktualne promocje z serwera
    - `get_game_deal()` - Pobiera informacje o promocji dla konkretnej gry

#### Zaktualizowane pliki:
- **`app/ui/home_view_server.py`** - Zaktualizowano metodę `_fetch_deals()`
  - Nowy format danych z IsThereAnyDeal
  - Lepsze wyświetlanie informacji o promocjach (cena, zniżka, sklep)
  
- **`app/ui/components_server.py`** - Zaktualizowano `GameDetailDialog`
  - Przycisk "Przejdź do sklepu" teraz priorytetyzuje link do najlepszej promocji
  - Kolejność: Best deal URL > Steam page > Fallback search

## Konfiguracja

### Wymagane kroki:

1. **Zarejestruj aplikację w IsThereAnyDeal:**
   - Przejdź do: https://isthereanydeal.com/dev/app/
   - Utwórz nową aplikację
   - Otrzymasz: API Key, Client ID, Client Secret

2. **Dodaj credentials do pliku `.env`:**
   ```env
   ITAD_API_KEY=your_api_key_here
   ITAD_CLIENT_ID=your_client_id_here
   ITAD_CLIENT_SECRET=your_client_secret_here
   ```

3. **Uruchom serwer i aplikację:**
   ```bash
   # Uruchom backend server
   cd server
   python app.py
   
   # W osobnym terminalu uruchom desktop app
   cd ..
   python -m app.main_window
   ```

## Format danych

### IsThereAnyDeal API Response (DealInfo):
```json
{
  "steam_appid": 730,
  "game_title": "Counter-Strike 2",
  "store_name": "Steam",
  "store_url": "https://store.steampowered.com/app/730/",
  "current_price": 0.0,
  "regular_price": 0.0,
  "discount_percent": 0,
  "currency": "USD",
  "drm": "Steam"
}
```

### Stary format (CheapShark) - już nie używany:
```json
{
  "dealID": "...",
  "storeID": "1",
  "gameID": "...",
  "salePrice": "9.99",
  "normalPrice": "29.99",
  "title": "Game Name"
}
```

## Funkcje

### Backend Endpoints

#### GET `/api/deals/best`
Pobiera najlepsze aktualne promocje.

**Query Parameters:**
- `limit` (int, optional): Maksymalna liczba promocji (1-50, default: 20)
- `min_discount` (int, optional): Minimalna zniżka w % (0-100, default: 20)

**Response:**
```json
{
  "deals": [
    {
      "steam_appid": 123456,
      "game_title": "Example Game",
      "store_name": "Steam",
      "store_url": "https://...",
      "current_price": 9.99,
      "regular_price": 29.99,
      "discount_percent": 67,
      "currency": "USD",
      "drm": "Steam"
    }
  ],
  "count": 10
}
```

#### GET `/api/deals/game/{appid}`
Pobiera informacje o promocjach dla konkretnej gry.

**Path Parameters:**
- `appid` (int): Steam Application ID

**Response:**
```json
{
  "game": {
    "appid": 730,
    "name": "Counter-Strike 2",
    "price": 0.0,
    "is_free": true,
    ...
  },
  "deal": {
    "steam_appid": 730,
    "game_title": "Counter-Strike 2",
    "store_name": "Steam",
    "store_url": "https://...",
    "current_price": 0.0,
    "regular_price": 0.0,
    "discount_percent": 0,
    "currency": "USD",
    "drm": "Steam"
  }
}
```

Jeśli brak promocji:
```json
{
  "game": {...},
  "deal": null,
  "message": "No active deals found for this game"
}
```

## Cache i optymalizacja

### Caching w bazie danych
Gdy użytkownik zapyta o promocję dla gry:
1. System sprawdza czy gra istnieje w bazie danych
2. Jeśli nie - pobiera szczegóły z Steam API i zapisuje do DB
3. Następnie pobiera informacje o promocjach z IsThereAnyDeal

To zmniejsza liczbę zapytań do Steam API i przyspiesza działanie aplikacji.

### Rate Limiting
Backend ma wbudowany rate limiting:
- `/api/deals/best`: 20 zapytań/minutę
- `/api/deals/game/{appid}`: 30 zapytań/minutę

## Testowanie

### Test backendu:
```python
# W katalogu projektu
cd server
python -c "
from services.deals_service import IsThereAnyDealClient
import asyncio

async def test():
    async with IsThereAnyDealClient() as client:
        deals = await client.get_best_deals(limit=5, min_discount=30)
        for deal in deals:
            print(f'{deal.game_title}: \${deal.current_price} (-{deal.discount_percent}%) at {deal.store_name}')

asyncio.run(test())
"
```

### Test frontendu:
```python
# W katalogu projektu
python -c "
from app.core.services.deals_api import DealsApiClient
import asyncio

async def test():
    async with DealsApiClient() as client:
        deals = await client.get_current_deals(limit=5, min_discount=20)
        print(f'Znaleziono {len(deals)} promocji')

asyncio.run(test())
"
```

## Troubleshooting

### Problem: "IsThereAnyDeal credentials not found"
**Rozwiązanie:** Upewnij się, że plik `.env` zawiera poprawne credentials:
```env
ITAD_API_KEY=...
ITAD_CLIENT_ID=...
ITAD_CLIENT_SECRET=...
```

### Problem: "No deals returned"
**Możliwe przyczyny:**
1. Niepoprawne credentials
2. Limit zapytań API został przekroczony
3. Brak aktualnych promocji spełniających kryteria (min_discount)

**Rozwiązanie:** Sprawdź logi serwera i zmniejsz `min_discount`.

### Problem: "Error fetching deals"
**Możliwe przyczyny:**
1. Serwer backend nie działa
2. Problem z połączeniem do IsThereAnyDeal API
3. Timeout

**Rozwiązanie:** 
1. Sprawdź czy serwer działa: `http://localhost:8000/health`
2. Sprawdź logi serwera
3. Zwiększ timeout w konfiguracji

## Bezpieczeństwo

### OAuth2 Authentication
IsThereAnyDeal API używa OAuth2 do autentykacji:
- Token dostępu jest automatycznie odświeżany
- Token jest przechowywany tylko w pamięci (nie zapisywany na dysku)
- Credentials są wczytywane z pliku `.env` (nie hardcoded)

### Zmienne środowiskowe
⚠️ **WAŻNE:** Plik `.env` nie powinien być commitowany do repozytorium!
- Dodaj `.env` do `.gitignore`
- Używaj `.env.example` jako template

## Migracja z CheapShark

Jeśli masz stary kod używający CheapShark:

### Stary kod (CheapShark):
```python
deals = await cheapshark_client.get_deals()
for deal in deals:
    price = deal['salePrice']
    title = deal['title']
```

### Nowy kod (IsThereAnyDeal):
```python
deals = await deals_client.get_current_deals()
for deal in deals:
    price = deal.get('current_price')
    title = deal.get('game_title')
```

## Dokumentacja API

Pełna dokumentacja IsThereAnyDeal API:
- https://docs.isthereanydeal.com/

## Changelog

### v2.0.0 (2025-01-11)
- ✅ Migracja z CheapShark do IsThereAnyDeal API
- ✅ Nowy endpoint `/api/deals/best`
- ✅ Nowy endpoint `/api/deals/game/{appid}`
- ✅ Automatyczne cache'owanie gier w bazie danych
- ✅ Lepsze wyświetlanie promocji w UI
- ✅ Priorytetyzacja linku do najlepszej oferty w "Store Page"

## TODO / Przyszłe ulepszenia

- [ ] Dodać filtrowanie po sklepach
- [ ] Dodać historię cen
- [ ] Dodać wykresy cen w czasie
- [ ] Dodać porównanie cen między sklepami

---

**Autor:** AI Assistant  
**Data:** 2025-01-11  
**Wersja dokumentacji:** 1.0

