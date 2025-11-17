# Dokumentacja API Endpoints

**Data aktualizacji:** 2025-11-17  
**Wersja:** 3.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Uwierzytelnianie](#uwierzytelnianie)
3. [Endpointy Publiczne](#endpointy-publiczne)
4. [Endpointy Chronionych](#endpointy-chronionych)
5. [Kody Błędów](#kody-błędów)
6. [Przykłady Użycia](#przykłady-użycia)

---

## Przegląd

Wszystkie endpointy API wymagają:
- ✅ **JWT Token** w nagłówku `Authorization: Bearer <token>`
- ✅ **HMAC Signature** w nagłówkach `X-*` (dla endpointów `/api/*`)
- ✅ **Rate Limiting** - domyślnie 100 żądań/minutę

**Base URL:** `http://localhost:8000` (lub wartość z `SERVER_URL`)

---

## Uwierzytelnianie

### POST /auth/login

Uwierzyteln ienie klienta i otrzymanie tokena JWT.

**Request:**
```json
{
  "client_id": "desktop-main"
}
```

**Headers:**
```
Content-Type: application/json
X-Client-Id: desktop-main
X-Timestamp: 1699876543
X-Nonce: a1b2c3d4e5f6...
X-Signature: base64-encoded-hmac-signature
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1200
}
```

**Rate Limit:** 20/minutę

---

## Endpointy Publiczne

### GET /

Główny endpoint informacyjny.

**Response:** `200 OK`
```json
{
  "message": "Custom Steam Dashboard API",
  "version": "1.0.0",
  "status": "running"
}
```

**Rate Limit:** 60/minutę

---

### GET /health

Health check serwera.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running"
}
```

**Rate Limit:** 120/minutę

---

## Endpointy Chronionych

> ⚠️ Wszystkie endpointy `/api/*` wymagają uwierzytelnienia (JWT + HMAC)

---

### 📊 **Gry**

#### GET /api/games

Pobierz wszystkie gry z bazy danych.

**Headers:**
```
Authorization: Bearer <jwt_token>
X-Client-Id: desktop-main
X-Timestamp: 1699876543
X-Nonce: unique-nonce
X-Signature: hmac-signature
```

**Response:** `200 OK`
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "current_players": 1234567,
      "peak_players": 1400000,
      "header_image": "https://...",
      "short_description": "...",
      "last_updated": "2025-11-13T10:00:00Z"
    }
  ]
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/games/{appid}

Pobierz szczegóły pojedynczej gry.

**Path Parameters:**
- `appid` (int) - Steam Application ID

**Response:** `200 OK`
```json
{
  "appid": 730,
  "name": "Counter-Strike 2",
  "current_players": 1234567,
  "peak_players": 1400000,
  "header_image": "https://cdn.akamai.steamstatic.com/...",
  "short_description": "For over two decades...",
  "genres": ["Action", "Free to Play"],
  "categories": ["Multi-player", "Steam Achievements"],
  "last_updated": "2025-11-13T10:00:00Z"
}
```

**Błędy:**
- `400` - Nieprawidłowy appid
- `404` - Gra nie znaleziona

**Rate Limit:** 60/minutę

---

#### POST /api/games/tags/batch

Pobierz gatunki i kategorie dla wielu gier jednocześnie.

**Request:**
```json
{
  "appids": [730, 570, 440]
}
```

**Response:** `200 OK`
```json
{
  "tags": {
    "730": {
      "genres": ["Action", "Free to Play"],
      "categories": ["Multi-player", "Steam Achievements"]
    },
    "570": {
      "genres": ["Action", "Strategy"],
      "categories": ["Multi-player", "Steam Trading Cards"]
    }
  }
}
```

**Rate Limit:** 20/minutę

---

### 🎮 **Steam API**

#### GET /api/owned-games/{steamid}

Pobierz posiadane gry użytkownika Steam.

**Path Parameters:**
- `steamid` (string) - Steam ID64

**Response:** `200 OK`
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "playtime_forever": 12345,
      "playtime_2weeks": 120,
      "img_icon_url": "...",
      "img_logo_url": "..."
    }
  ]
}
```

**Błędy:**
- `400` - Nieprawidłowy Steam ID
- `500` - Błąd Steam API

**Rate Limit:** 20/minutę

---

#### GET /api/recently-played/{steamid}

Pobierz ostatnio grane gry użytkownika.

**Path Parameters:**
- `steamid` (string) - Steam ID64

**Response:** `200 OK`
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "playtime_2weeks": 120,
      "playtime_forever": 12345,
      "img_icon_url": "...",
      "img_logo_url": "..."
    }
  ]
}
```

**Rate Limit:** 20/minutę

---

#### GET /api/coming-soon

Pobierz nadchodzące premiery gier.

**Response:** `200 OK`
```json
{
  "games": [
    {
      "appid": 123456,
      "name": "Upcoming Game",
      "header_image": "https://...",
      "release_date": "2025-12-01",
      "short_description": "..."
    }
  ]
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/player-summary/{steamid}

Pobierz podsumowanie profilu Steam.

**Path Parameters:**
- `steamid` (string) - Steam ID64

**Response:** `200 OK`
```json
{
  "steamid": "76561198...",
  "personaname": "Player Name",
  "profileurl": "https://steamcommunity.com/...",
  "avatar": "https://...",
  "avatarmedium": "https://...",
  "avatarfull": "https://...",
  "personastate": 1,
  "communityvisibilitystate": 3,
  "profilestate": 1,
  "lastlogoff": 1699876543,
  "timecreated": 1234567890
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/resolve-vanity/{vanity_url}

Rozwiąż vanity URL na Steam ID64.

**Path Parameters:**
- `vanity_url` (string) - Vanity name, custom URL lub pełny URL profilu

**Przykłady:**
```
/api/resolve-vanity/gaben
/api/resolve-vanity/my_custom_name
/api/resolve-vanity/https://steamcommunity.com/id/gaben
```

**Response:** `200 OK`
```json
{
  "success": true,
  "steamid": "76561197960287930",
  "vanity_url": "gaben"
}
```

**Błędy:**
- `404` - Nie można rozwiązać URL

**Rate Limit:** 20/minutę

---

### 📈 **UI / Statystyki**

#### GET /api/current-players

Pobierz aktualną liczbę graczy dla gier z watchlisty.

**Response:** `200 OK`
```json
{
  "games": [
    {
      "appid": 730,
      "name": "Counter-Strike 2",
      "current_players": 1234567,
      "last_updated": "2025-11-13T10:00:00Z"
    }
  ]
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/genres

Pobierz wszystkie unikalne gatunki gier.

**Response:** `200 OK`
```json
{
  "genres": ["Action", "Adventure", "Strategy", "RPG", "Simulation"]
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/categories

Pobierz wszystkie unikalne kategorie gier.

**Response:** `200 OK`
```json
{
  "categories": [
    "Single-player",
    "Multi-player",
    "Steam Achievements",
    "Steam Trading Cards"
  ]
}
```

**Rate Limit:** 30/minutę

---

### 💰 **Promocje (IsThereAnyDeal)**

#### GET /api/deals/best

Pobierz najlepsze promocje na gry z watchlist.

**Query Parameters:**
- `limit` (int, optional) - Maksymalna liczba wyników (domyślnie: 20, max: 50)
- `min_discount` (int, optional) - Minimalna zniżka w procentach (domyślnie: 20)

**Response:** `200 OK`
```json
{
  "deals": [
    {
      "game_name": "Counter-Strike 2",
      "appid": 730,
      "discount_percent": 80,
      "price_new": 9.99,
      "price_old": 49.99,
      "shop_name": "Steam",
      "url": "https://store.steampowered.com/app/730"
    }
  ],
  "count": 1
}
```

**Rate Limit:** 20/minutę

---

#### GET /api/deals/game/{appid}

Pobierz informacje o promocjach dla konkretnej gry.

**Path Parameters:**
- `appid` (int) - Steam Application ID

**Response:** `200 OK`
```json
{
  "game": {
    "appid": 730,
    "name": "Counter-Strike 2",
    "current_players": 1234567
  },
  "deal": {
    "game_name": "Counter-Strike 2",
    "discount_percent": 0,
    "price_new": 0,
    "price_old": 0,
    "shop_name": "Steam",
    "url": "https://store.steampowered.com/app/730"
  },
  "message": "No active deals found for this game"
}
```

**Rate Limit:** 30/minutę

---

#### GET /api/deals/search

Wyszukaj promocje dla gry po tytule.

**Query Parameters:**
- `title` (str) - Tytuł gry do wyszukania (min. 2 znaki)

**Response:** `200 OK`
```json
{
  "found": true,
  "game": {
    "title": "Counter-Strike 2",
    "id": "counterstrike2",
    "steam_appid": 730
  },
  "deal": {
    "game_name": "Counter-Strike 2",
    "discount_percent": 0,
    "price_new": 0,
    "price_old": 0,
    "shop_name": "Steam",
    "url": "https://store.steampowered.com/app/730"
  }
}
```

**Response (nie znaleziono):** `200 OK`
```json
{
  "found": false,
  "message": "No game found matching 'xyz'"
}
```

**Rate Limit:** 30/minutę

---

### 📊 **Historia i Porównywanie**

#### POST /api/player-history/compare

Pobierz historię liczby graczy dla wielu gier do porównania.

**Request Body:**
```json
{
  "appids": [730, 570, 440]
}
```

**Query Parameters:**
- `days` (float, optional) - Liczba dni historii (domyślnie: 7, zakres: 0.04-30)
  - 0.04 = 1 godzina
  - 0.125 = 3 godziny
  - 0.25 = 6 godzin
  - 0.5 = 12 godzin
  - 1 = 1 dzień
  - 7 = 7 dni (domyślnie)
- `limit` (int, optional) - Max rekordów na grę (domyślnie: 1000, zakres: 10-5000)

**Response:** `200 OK`
```json
{
  "games": {
    "730": {
      "name": "Counter-Strike 2",
      "history": [
        {
          "time_stamp": 1699876543,
          "player_count": 1234567
        },
        {
          "time_stamp": 1699880143,
          "player_count": 1240000
        }
      ]
    },
    "570": {
      "name": "Dota 2",
      "history": [
        {
          "time_stamp": 1699876543,
          "player_count": 567890
        }
      ]
    }
  }
}
```

**Rate Limit:** 20/minutę

---

## Kody Błędów

| Kod | Znaczenie | Przykład |
|-----|-----------|----------|
| `200` | OK | Sukces |
| `400` | Bad Request | Nieprawidłowe dane wejściowe |
| `401` | Unauthorized | Brak lub nieprawidłowy token JWT |
| `403` | Forbidden | Nieprawidłowy podpis HMAC |
| `404` | Not Found | Zasób nie znaleziony |
| `422` | Unprocessable Entity | Błąd walidacji Pydantic |
| `429` | Too Many Requests | Przekroczenie rate limit |
| `500` | Internal Server Error | Błąd serwera |

---

## Przykłady Użycia

### Python (httpx)

```python
import httpx
from app.helpers.signing import sign_request

# Konfiguracja
SERVER_URL = "http://localhost:8000"
CLIENT_ID = "desktop-main"
CLIENT_SECRET = "your-secret"

async def get_games():
    async with httpx.AsyncClient() as client:
        # 1. Uwierzytelnij się
        login_body = {"client_id": CLIENT_ID}
        login_headers = sign_request(
            method="POST",
            path="/auth/login",
            body=login_body,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        
        response = await client.post(
            f"{SERVER_URL}/auth/login",
            json=login_body,
            headers=login_headers
        )
        token = response.json()["access_token"]
        
        # 2. Pobierz gry
        headers = sign_request(
            method="GET",
            path="/api/games",
            body=b"",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        headers["Authorization"] = f"Bearer {token}"
        
        response = await client.get(
            f"{SERVER_URL}/api/games",
            headers=headers
        )
        return response.json()
```

### curl

```bash
# 1. Uwierzytelnij się
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: desktop-main" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Nonce: $(openssl rand -hex 16)" \
  -H "X-Signature: $(python scripts/generate_signature.py)" \
  -d '{"client_id":"desktop-main"}' | jq -r '.access_token')

# 2. Pobierz gry
curl "http://localhost:8000/api/games" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Client-Id: desktop-main" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Nonce: $(openssl rand -hex 16)" \
  -H "X-Signature: $(python scripts/generate_signature.py)"
```

---

## Następne Kroki

- **Bezpieczeństwo**: [SERVER_SECURITY.md](SERVER_SECURITY.md)
- **Baza danych**: [SERVER_DATABASE.md](SERVER_DATABASE.md)
- **Scheduler**: [SERVER_SCHEDULER.md](SERVER_SCHEDULER.md)

