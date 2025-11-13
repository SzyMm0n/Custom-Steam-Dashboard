# Dokumentacja Serwera - Przegląd

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Wprowadzenie](#wprowadzenie)
2. [Architektura](#architektura)
3. [Struktura Projektu](#struktura-projektu)
4. [Quick Start](#quick-start)
5. [Zmienne Środowiskowe](#zmienne-środowiskowe)
6. [Dokumentacja Szczegółowa](#dokumentacja-szczegółowa)

---

## Wprowadzenie

**Custom Steam Dashboard Server** to backend oparty na **FastAPI**, który zapewnia:

- 🔒 **Bezpieczne REST API** z uwierzytelnianiem JWT + HMAC
- 📊 **Dane o grach Steam** - statystyki graczy, informacje o grach
- 💰 **Promocje** - integracja z IsThereAnyDeal API
- 📅 **Scheduler** - automatyczne zadania cykliczne (APScheduler)
- 🗄️ **PostgreSQL** - baza danych z historią
- 🚦 **Rate Limiting** - ochrona przed nadmiernym obciążeniem
- ✅ **Walidacja** - Pydantic modele dla wszystkich danych

---

## Architektura

```
┌─────────────────────────────────────────────────────────┐
│                  CLIENT (GUI / API)                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/HTTP + JWT + HMAC
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Middleware & Security Layer             │  │
│  │  • JWT Authentication                            │  │
│  │  • HMAC Signature Verification                   │  │
│  │  • Rate Limiting (slowapi)                       │  │
│  │  • CORS Policy                                   │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────┴──────────────────────────┐   │
│  │              REST API Endpoints                  │   │
│  │                                                  │   │
│  │  /health         - Health check                 │   │
│  │  /auth/*         - Authentication               │   │
│  │  /api/games/*    - Game data & statistics       │   │
│  │  /api/library/*  - User library                 │   │
│  │  /api/deals/*    - Game deals                   │   │
│  │  /api/upcoming/* - Upcoming releases            │   │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌──────────────┬───────┴────────┬───────────────┐     │
│  │   Scheduler  │   Services     │   Database    │     │
│  │              │                │               │     │
│  │ • Cron Jobs  │ • SteamClient  │ • PostgreSQL  │     │
│  │ • Data Sync  │ • DealsClient  │ • asyncpg     │     │
│  └──────────────┴────────────────┴───────────────┘     │
└─────────────────────────────────────────────────────────┘
                     │               │
                     ▼               ▼
          ┌──────────────┐  ┌──────────────┐
          │   Steam API  │  │  ITAD API    │
          └──────────────┘  └──────────────┘
```

---

## Struktura Projektu

```
server/
├── app.py                      # 🚀 Główna aplikacja FastAPI
├── auth_routes.py              # 🔐 Endpointy uwierzytelniania
├── security.py                 # 🛡️ JWT + HMAC + autentykacja
├── middleware.py               # 🔍 Middleware weryfikacji podpisów
├── scheduler.py                # ⏰ Zarządzanie zadaniami cyklicznymi
├── validation.py               # ✅ Walidatory Pydantic
│
├── database/
│   ├── __init__.py
│   └── database.py             # 🗄️ Manager PostgreSQL (asyncpg)
│
└── services/
    ├── __init__.py
    ├── models.py               # 📦 Modele danych Pydantic
    ├── steam_service.py        # 🎮 Klient Steam API
    ├── deals_service.py        # 💰 Klient IsThereAnyDeal API
    ├── parse_html.py           # 🔍 Parser HTML
    └── _base_http.py           # 🌐 Bazowy klient HTTP
```

---

## Quick Start

### 1. Wymagania

- **Python**: 3.11+ (zalecane 3.12)
- **PostgreSQL**: 13+ (lub Neon.tech w chmurze)
- **System**: Linux, macOS, Windows

### 2. Instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard

# Utworzenie wirtualnego środowiska
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalacja zależności
pip install -r requirements.txt
```

### 3. Konfiguracja Bazy Danych

#### Opcja A: Lokalna PostgreSQL

```bash
# Instalacja PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Utworzenie bazy
sudo -u postgres psql
CREATE DATABASE steam_dashboard;
CREATE USER steam_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE steam_dashboard TO steam_user;
\q
```

#### Opcja B: Neon.tech (Chmura)

1. Utwórz konto na [neon.tech](https://neon.tech)
2. Utwórz nową bazę danych
3. Skopiuj connection string

### 4. Konfiguracja .env

Utwórz plik `.env` w katalogu głównym:

```env
# PostgreSQL Configuration
PGHOST=localhost
PGPORT=5432
PGUSER=steam_user
PGPASSWORD=your_password
PGDATABASE=steam_dashboard

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_URL=http://localhost:8000

# JWT Configuration
JWT_SECRET=your-jwt-secret-min-32-bytes
JWT_TTL_SECONDS=1200

# Client Credentials
CLIENT_ID=desktop-main
CLIENT_SECRET=your-client-secret
CLIENTS_JSON={"desktop-main":"your-client-secret"}

# Steam API (opcjonalnie)
STEAM_API_KEY=your_steam_api_key
STEAM_ID=your_steam_id

# IsThereAnyDeal API
ITAD_CLIENT_ID=your_itad_client_id
ITAD_CLIENT_SECRET=your_itad_client_secret
```

**Generowanie sekretów:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Uruchomienie Serwera

```bash
cd server
python app.py
```

Serwer będzie dostępny pod adresem: **http://localhost:8000**

**Weryfikacja:**
```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

**Dokumentacja API:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Zmienne Środowiskowe

### Wymagane

| Zmienna | Opis | Przykład |
|---------|------|----------|
| `PGHOST` | Host PostgreSQL | `localhost` |
| `PGPORT` | Port PostgreSQL | `5432` |
| `PGUSER` | Użytkownik bazy | `steam_user` |
| `PGPASSWORD` | Hasło do bazy | `SecureP@ssw0rd` |
| `PGDATABASE` | Nazwa bazy | `steam_dashboard` |
| `JWT_SECRET` | Sekret JWT (min 32 bajty) | `wygenerowany_secret` |
| `CLIENTS_JSON` | Lista klientów (JSON) | `{"desktop-main":"secret"}` |

### Opcjonalne

| Zmienna | Opis | Domyślna | Przykład |
|---------|------|----------|----------|
| `SERVER_HOST` | Host serwera | `0.0.0.0` | `0.0.0.0` |
| `SERVER_PORT` | Port serwera | `8000` | `8000` |
| `JWT_TTL_SECONDS` | Czas życia tokena | `1200` | `600` |
| `STEAM_API_KEY` | Klucz Steam API | - | `ABC123...` |
| `STEAM_ID` | Steam ID (testy) | - | `76561198...` |
| `ITAD_CLIENT_ID` | ITAD Client ID | - | `abc123` |
| `ITAD_CLIENT_SECRET` | ITAD Secret | - | `secret123` |

---

## Dokumentacja Szczegółowa

Pełna dokumentacja podzielona na moduły:

| Dokument | Opis |
|----------|------|
| [📚 SERVER_API_ENDPOINTS.md](SERVER_API_ENDPOINTS.md) | Wszystkie endpointy API z przykładami |
| [🔐 SERVER_SECURITY.md](SERVER_SECURITY.md) | System bezpieczeństwa (JWT + HMAC) |
| [🗄️ SERVER_DATABASE.md](SERVER_DATABASE.md) | Baza danych i modele |
| [⏰ SERVER_SCHEDULER.md](SERVER_SCHEDULER.md) | Zadania cykliczne i scheduler |
| [🎮 SERVER_SERVICES.md](SERVER_SERVICES.md) | Serwisy (Steam, ITAD, HTTP) |
| [✅ SERVER_VALIDATION.md](SERVER_VALIDATION.md) | Walidacja i modele Pydantic |

---

## Kluczowe Zależności

| Biblioteka | Wersja | Zastosowanie |
|------------|--------|--------------|
| **FastAPI** | 0.115+ | REST API framework |
| **Uvicorn** | 0.32+ | Serwer ASGI |
| **PostgreSQL** | 13+ | Baza danych |
| **asyncpg** | 0.29+ | Async driver PostgreSQL |
| **APScheduler** | 3.10+ | Scheduler zadań |
| **slowapi** | 0.1.9+ | Rate limiting |
| **pydantic** | 2.7+ | Walidacja danych |
| **httpx** | 0.27+ | Klient HTTP/2 |
| **python-jose** | 3.3+ | JWT tokens |
| **tenacity** | 9.0+ | Retry logic |

---

## Następne Kroki

1. **Uruchom serwer** lokalnie (zobacz [Quick Start](#quick-start))
2. **Przeczytaj** [SERVER_API_ENDPOINTS.md](SERVER_API_ENDPOINTS.md) - poznaj dostępne endpointy
3. **Skonfiguruj** [SERVER_SECURITY.md](SERVER_SECURITY.md) - zabezpiecz produkcję
4. **Eksploruj** [SERVER_DATABASE.md](SERVER_DATABASE.md) - zrozum strukturę bazy danych

---

## Wsparcie

- **Dokumentacja JWT**: [docs/JWT_OVERVIEW.md](../JWT_OVERVIEW.md)
- **Dokumentacja autoryzacji**: [docs/AUTH_AND_SIGNING_README.md](../AUTH_AND_SIGNING_README.md)
- **Issues**: [GitHub Issues](https://github.com/SzyMm0n/Custom-Steam-Dashboard/issues)

