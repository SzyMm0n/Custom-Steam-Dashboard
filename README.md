<div align="center">

# 🎮 Custom Steam Dashboard

### Nowoczesny, interaktywny dashboard do monitorowania gier Steam

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.7%2B-green.svg)](https://pypi.org/project/PySide6/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Funkcjonalności](#-funkcjonalności) • [Architektura](#-architektura) • [Instalacja](#-instalacja) • [Dokumentacja](#-dokumentacja)

![Dashboard Preview](https://img.shields.io/badge/Status-Active-success)

</div>

---

## 📋 Spis Treści

- [O Projekcie](#-o-projekcie)
- [Funkcjonalności](#-funkcjonalności)
- [Architektura](#-architektura)
- [Struktura Projektu](#-struktura-projektu)
- [Instalacja](#-instalacja)
  - [Aplikacja GUI](#aplikacja-gui-desktopowa)
  - [Serwer Backend](#serwer-backend)
- [Uruchamianie](#-uruchamianie)
  - [Uruchomienie Serwera](#1-uruchomienie-serwera-backend)
  - [Uruchomienie GUI](#2-uruchomienie-aplikacji-gui)
- [Konfiguracja](#-konfiguracja)
- [Użytkowanie](#-użytkowanie)
- [Tworzenie Pakietu Wykonywalnego](#-tworzenie-pakietu-wykonywalnego)
- [Dokumentacja](#-dokumentacja)
- [Stack Technologiczny](#-stack-technologiczny)
- [Bezpieczeństwo](#-bezpieczeństwo)
- [Rozwój](#-rozwój)
- [Troubleshooting](#-troubleshooting)
- [Credits](#-credits)
- [Licencja](#-licencja)

---

## 🎯 O Projekcie

**Custom Steam Dashboard** to aplikacja wykonana na potrzeby przedmiotu, Dynamiczna Analiza Oprogramowania, na studiach informatycznych.
Celem było stworzenie oprogramowania do dynamicznej analizy kodu. Dlatego aplikacja nie jest gotowym produktem komercyjnym, ale raczej przykładem zaawansowanego projektu edukacyjnego.
Aplikacja umożliwia monitorowanie popularności gier na platformie Steam, oferując interaktywny interfejs użytkownika zbudowany w PySide6 oraz wydajny serwer backend oparty na FastAPI i PostgreSQL.
Projekt demonstruje nowoczesne podejście do tworzenia aplikacji klient-serwer z wykorzystaniem asynchronicznego programowania w Pythonie, zapewniając responsywny interfejs użytkownika oraz skalowalny backend.


### 🖥️ **Aplikacja GUI** (Desktopowa)
Nowoczesny interfejs użytkownika zbudowany w **PySide6** z asynchronicznym wsparciem (`qasync`), który komunikuje się z backendem i wyświetla:
- 📊 **Statystyki graczy na żywo** - liczba aktywnych graczy w wybranych grach
- 💰 **Najlepsze promocje** - aktualne okazje cenowe
- 🚀 **Nadchodzące premiery** - kalendarz najciekawszych wydań
- 📚 **Przeglądarka biblioteki** - Twoja kolekcja gier ze statystykami

### ⚙️ **Serwer Backend**
Wydajny serwer **FastAPI** z PostgreSQL, który:
- 🔄 Automatycznie zbiera dane ze Steam API
- 💾 Zarządza bazą danych z historią aktywności graczy
- 📅 Wykonuje zadania cykliczne (scheduler)
- 🛡️ Implementuje rate limiting i walidację
- 🌐 Udostępnia REST API dla aplikacji klienckiej

---

## ✨ Funkcjonalności

### Dla Użytkowników

- ✅ **Monitorowanie popularności gier** - śledź liczbę graczy online w czasie rzeczywistym
- ✅ **Filtrowanie po tagach** - znajdź gry według gatunków i kategorii
- ✅ **Zakres liczby graczy** - filtruj po min/max liczbie aktywnych graczy
- ✅ **Promocje i okazje** - najlepsze ceny z IsThereAnyDeal API (Steam, GOG, Epic Games, Humble Bundle)
- ✅ **Kalendarz premier** - nie przegap nadchodzących wydań
- ✅ **Analiza biblioteki** - przegląd Twojej kolekcji Steam z czasem gry
- ✅ **Responsywny interfejs** - płynne działanie dzięki asyncio

### Dla Deweloperów

- ✅ **Architektura klient-serwer** - rozdzielenie logiki UI od backendu
- ✅ **Asynchroniczne operacje** - httpx, asyncpg, asyncio
- ✅ **Walidacja danych** - Pydantic modele z pełną typizacją
- ✅ **Rate limiting** - ochrona przed nadmiernym obciążeniem API
- ✅ **Retry logic** - automatyczne ponowne próby przy błędach
- ✅ **PostgreSQL** - wydajna baza danych z historią
- ✅ **Scheduler** - automatyczne zadania cykliczne (APScheduler)
- ✅ **Testowalne** - struktura gotowa pod unit testy

---

## 🏗️ Architektura

Aplikacja wykorzystuje **architekturę klient-serwer** z wyraźnym podziałem odpowiedzialności:

```
┌─────────────────────────────────────────────────────────────┐
│                    APLIKACJA GUI (PySide6)                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Home View   │  │ Library View │  │   Dialogs    │       │
│  │              │  │              │  │              │       │
│  │ • Live Stats │  │ • User Games │  │ • User Info  │       │
│  │ • Deals      │  │ • Playtime   │  │ • Filters    │       │
│  │ • Upcoming   │  │ • Stats      │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│              ▲                                              │
│              │  HTTP REST API (httpx)                       │
│              │                                              │
└──────────────┼──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                   SERWER BACKEND (FastAPI)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              REST API Endpoints                      │   │
│  │  /health  /games  /library  /deals  /upcoming        │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌───────────────┐  ┌───┴────────────┐  ┌──────────────┐    │
│  │   Scheduler   │  │  Steam Service │  │  Validation  │    │
│  │               │  │                │  │              │    │
│  │ • Cron Jobs   │  │ • API Client   │  │ • Input      │    │
│  │ • Data Sync   │  │ • Parser       │  │ • Rate Limit │    │
│  └───────┬───────┘  └───────┬────────┘  └──────────────┘    │
│          │                  │                               │
│          ▼                  ▼                               │
│  ┌─────────────────────────────────────┐                    │
│  │      PostgreSQL Database            │                    │
│  │  • game_apps                        │                    │
│  │  • player_counts (historical)       │                    │
│  │  • watchlist                        │                    │
│  └─────────────────────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│               ZEWNĘTRZNE API                                │
│  • Steam Store API  • Steam Web API  • IsThereAnyDeal API   │
└─────────────────────────────────────────────────────────────┘
```

### Przepływ Danych

1. **Aplikacja GUI** → wysyła żądanie HTTP do serwera backend
2. **Serwer Backend** → waliduje żądanie, sprawdza rate limiting
3. **Steam Service** → pobiera dane z zewnętrznych API (z retry logic)
4. **Database** → zapisuje/odczytuje dane historyczne
5. **Serwer** → zwraca sformatowane dane do GUI
6. **GUI** → renderuje dane w responsywnym interfejsie

---

## 📁 Struktura Projektu

```
Custom-Steam-Dashboard/
│
├── 🖥️ app/                          # APLIKACJA GUI
│   ├── main_server.py               # Punkt wejścia aplikacji
│   ├── main_window.py               # Główne okno Qt
│   │
│   ├── ui/                          # Komponenty interfejsu
│   │   ├── home_view_server.py      # Widok główny (statystyki)
│   │   ├── library_view_server.py   # Widok biblioteki
│   │   ├── components_server.py     # Reużywalne komponenty
│   │   ├── user_info_dialog_server.py # Dialog użytkownika
│   │   └── styles.py                # Style Qt
│   │
│   └── core/                        # Logika biznesowa GUI
│       └── services/
│           ├── server_client.py     # Klient HTTP do backendu
│           └── deals_client.py      # Integracja z IsThereAnyDeal API
│
├── ⚙️ server/                       # SERWER BACKEND
│   ├── app.py                       # Główna aplikacja FastAPI
│   ├── scheduler.py                 # Zarządzanie zadaniami
│   ├── validation.py                # Walidatory Pydantic
│   │
│   ├── database/                    # Warstwa danych
│   │   └── database.py              # Manager PostgreSQL
│   │
│   └── services/                    # Logika biznesowa
│       ├── steam_service.py         # Klient Steam API
│       ├── deals_service.py         # Logika IsThereAnyDeal API
│       ├── models.py                # Modele Pydantic
│       ├── parse_html.py            # Parser HTML
│       └── _base_http.py            # Bazowy klient HTTP
│
├── 📚 docs/                         # DOKUMENTACJA
│   ├── SERVER_DOCUMENTATION_PL.md
│   └── UI_DOCUMENTATION_PL.md
│
├── 🔧 build/                        # Pliki buildu (PyInstaller)
├── requirements.txt                 # Zależności Pythona
├── steam_dashboard.spec             # Specyfikacja PyInstaller
├── build_executable.sh              # Skrypt budowania (Linux/Mac)
├── build_executable.bat             # Skrypt budowania (Windows)
├── check_build_deps.py              # Weryfikacja zależności
└── LICENSE                          # Licencja MIT
```

---

## 🚀 Instalacja

### Wymagania Systemowe

- **Python**: 3.11 lub nowszy (zalecane 3.12)
- **PostgreSQL**: 13+ (dla serwera backend)
- **System**: Linux, macOS, Windows
- **RAM**: minimum 2GB
- **Miejsce na dysku**: ~500MB (z zależnościami)

### Klonowanie Repozytorium

```bash
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard
```

---

## 📦 Instalacja Zależności

### Aplikacja GUI (Desktopowa)

Aplikacja GUI wymaga następujących zależności:

```bash
# Utwórz wirtualne środowisko (opcjonalnie, ale zalecane)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate     # Windows

# Zainstaluj zależności
pip install -r requirements.txt
```

**Kluczowe zależności GUI:**
- `PySide6>=6.7` - Framework Qt dla Pythona
- `qasync>=0.26` - Mostek Qt ↔ asyncio
- `httpx[http2]>=0.27` - Klient HTTP do komunikacji z serwerem
- `tenacity>=9.0` - Retry logic
- `pydantic>=2.7` - Walidacja danych

---

### Serwer Backend

Serwer wymaga PostgreSQL oraz dodatkowych zależności:

```bash
# Instalacja zależności serwera (jeśli nie zainstalowane)
pip install -r requirements.txt
```

**Kluczowe zależności serwera:**
- `fastapi>=0.115` - Framework REST API
- `uvicorn[standard]>=0.32` - Serwer ASGI
- `asyncpg>=0.29` - Driver PostgreSQL
- `APScheduler>=3.10` - Scheduler zadań
- `slowapi>=0.1.9` - Rate limiting

---

## 🔧 Konfiguracja

### 1. Konfiguracja PostgreSQL (Serwer)

#### Opcja A: Lokalna instalacja PostgreSQL

```bash
# Zainstaluj PostgreSQL (przykład dla Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Utwórz bazę danych
sudo -u postgres psql
CREATE DATABASE steam_dashboard;
CREATE USER steam_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE steam_dashboard TO steam_user;
\q
```

#### Opcja B: PostgreSQL w chmurze (Neon.tech, AWS RDS, itp.)

Utwórz bazę danych w wybranym serwisie i skopiuj dane dostępowe.

### 2. Zmienne Środowiskowe

Utwórz plik `.env` w katalogu głównym projektu:

```bash
# PostgreSQL Configuration (SERWER)
PGHOST=localhost              # lub adres zdalnej bazy
PGPORT=5432
PGUSER=steam_user
PGPASSWORD=your_password
PGDATABASE=steam_dashboard

# Steam API Configuration (OPCJONALNE)
STEAM_API_KEY=your_steam_api_key    # Zdobądź na: https://steamcommunity.com/dev/apikey
STEAM_ID=your_steam_id              # Twój Steam ID (dla testów biblioteki)

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_URL=http://localhost:8000    # URL serwera dla aplikacji GUI

# Authentication (wymagane dla GUI)
CLIENT_ID=desktop-main              # ID klienta
CLIENT_SECRET=your-client-secret    # Sekret klienta (generuj: python -c "import secrets; print(secrets.token_urlsafe(32))")

# JWT Configuration (SERWER)
JWT_SECRET=your-jwt-secret          # Sekret JWT (min 32 bajty)
JWT_TTL_SECONDS=1200                # Czas życia tokenu (20 minut)
CLIENTS_JSON={"desktop-main": "your-client-secret"}  # Lista klientów
```

### 3. Inicjalizacja Bazy Danych

Przy pierwszym uruchomieniu serwer automatycznie utworzy wymagane tabele:
- `games` - informacje o grach
- `game_genres` - gatunki gier
- `game_categories` - kategorie gier
- `player_counts_raw` - surowe dane liczby graczy
- `player_counts_hourly` - zarchiwizowane dane godzinowe
- `player_counts_daily` - zarchiwizowane dane dzienne
- `watchlist` - lista obserwowanych gier

---

## ▶️ Uruchamianie

### 1. Uruchomienie Serwera Backend

```bash
# Z katalogu głównego projektu
cd server
python app.py
```

**Alternatywnie z uvicorn:**
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Serwer będzie dostępny domyślnie pod adresem: **`http://localhost:8000`**

(URL serwera można skonfigurować przez zmienną środowiskową `SERVER_URL`)

#### Weryfikacja działania serwera:
```bash
curl http://localhost:8000/health
# Odpowiedź: {"status":"healthy"}
```

#### Dostęp do interaktywnej dokumentacji API:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

### 2. Uruchomienie Aplikacji GUI

**W nowym terminalu** (przy działającym serwerze):

```bash
# Z katalogu głównego projektu
python -m app.main_server
```

#### Możliwe parametry (opcjonalnie):
```bash
# Niestandardowy adres serwera
python -m app.main_server --server-url http://192.168.1.100:8000
```

Aplikacja GUI automatycznie połączy się z serwerem i wyświetli główne okno.

---

## 🎮 Użytkowanie

### Nawigacja w Aplikacji GUI

#### 🏠 **Widok Główny (Home)**
1. **Live Games Count** - Statystyki graczy online
   - Domyślna lista popularnych gier
   - Odświeżanie co 5 minut przez scheduler
   
2. **Best Deals** - Najlepsze promocje
   - Źródło: IsThereAnyDeal API
   - Kliknij grę aby zobaczyć szczegóły
   
3. **Best Upcoming Releases** - Nadchodzące premiery
   - Kalendarz premier z Steam
   - Data wydania i informacje o grze

#### 📚 **Widok Biblioteki (Library)**
- Wymaga skonfigurowania `STEAM_ID` w `.env`
- Wyświetla Twoją kolekcję gier
- Pokazuje czas gry i ostatnią aktywność

#### 🔄 **Odświeżanie Danych**
- Przycisk **Refresh** w toolbar
- Automatyczne odświeżanie co 5 minut (scheduler)

#### ⚙️ **Filtrowanie**
- **Tagi**: filtruj gry po gatunkach (Action, RPG, Strategy, itp.)
- **Liczba graczy**: ustaw zakres min/max aktywnych graczy

---

## 📦 Tworzenie Pakietu Wykonywalnego

Możesz zbudować standalone aplikację bez wymagania instalacji Pythona:

### Przygotowanie
```bash
# Zainstaluj wszystkie zależności
pip install -r requirements.txt

# Opcjonalnie: Weryfikacja zależności
python check_build_deps.py
```

### Budowanie

**Linux / macOS:**
```bash
chmod +x build_executable.sh
./build_executable.sh
```

**Windows:**
```cmd
build_executable.bat
```

Plik wykonywalny znajdziesz w katalogu `dist/`:
- 🐧 Linux: `dist/CustomSteamDashboard`
- 🍎 macOS: `dist/CustomSteamDashboard.app`
- 🪟 Windows: `dist/CustomSteamDashboard.exe` (z ikoną ICO)

### Konfiguracja i dystrybucja

**Automatycznie tworzone pliki w `dist/`:**
- `.env` - Plik konfiguracji (skopiowany z `.env.example`)
- `README_USER.md` - Instrukcja dla użytkownika końcowego

**⚠️ WAŻNE przed dystrybucją:**

Jeżeli planujesz udostępnić aplikację innym użytkownikom:
1. Edytuj `dist/.env` i usuń swoje sekrety (zostaw tylko placeholdery)
2. Użytkownik końcowy musi wypełnić `dist/.env` swoimi danymi:
   - `SERVER_URL` - adres serwera backend
   - `CLIENT_ID` i `CLIENT_SECRET` - credentials od administratora

**Dokumentacja:**
- 📦 [DISTRIBUTION.md](DISTRIBUTION.md) - Kompletny przewodnik dystrybucji
- 📖 [README_USER.md](README_USER.md) - Instrukcja dla użytkownika końcowego

---

## 📖 Dokumentacja

Szczegółowa dokumentacja dostępna w katalogu `docs/`:

### 📘 Dokumentacja Ogólna

| Dokument | Opis |
|----------|------|
| 🔧 [TECHNICAL_DOCUMENTATION_PL.md](docs/general/TECHNICAL_DOCUMENTATION_PL.md) | Kompletna dokumentacja techniczna projektu |
| 💰 [DEALS_API_MIGRATION.md](docs/general/DEALS_API_MIGRATION.md) | Migracja z CheapShark do IsThereAnyDeal API |
| 📦 [DISTRIBUTION.md](DISTRIBUTION.md) | Przewodnik budowania i dystrybucji executable |
| 📖 [README_USER.md](README_USER.md) | Instrukcja dla użytkownika końcowego |

### 🌐 Dokumentacja Serwera

| Dokument | Opis |
|----------|------|
| 📖 **[SERVER_OVERVIEW.md](docs/server/SERVER_OVERVIEW.md)** | **Przegląd, quick start, konfiguracja** |
| 🔌 [SERVER_API_ENDPOINTS.md](docs/server/SERVER_API_ENDPOINTS.md) | Wszystkie endpointy API z przykładami |
| 🔐 [SERVER_SECURITY.md](docs/server/SERVER_SECURITY.md) | JWT + HMAC, middleware, rate limiting |
| 🗄️ [SERVER_DATABASE.md](docs/server/SERVER_DATABASE.md) | PostgreSQL, tabele, operacje |
| ⏰ [SERVER_SCHEDULER.md](docs/server/SERVER_SCHEDULER.md) | Zadania cykliczne, APScheduler |
| 🎮 [SERVER_SERVICES.md](docs/server/SERVER_SERVICES.md) | Steam API, ITAD, HTTP client |
| ✅ [SERVER_VALIDATION.md](docs/server/SERVER_VALIDATION.md) | Pydantic validators, obsługa błędów |

### 📱 Dokumentacja UI

| Dokument | Opis |
|----------|------|
| 📖 **[UI_OVERVIEW.md](docs/ui/UI_OVERVIEW.md)** | **Przegląd, quick start, architektura** |
| 📱 [UI_COMPONENTS.md](docs/ui/UI_COMPONENTS.md) | Komponenty i widgety reużywalne |
| 🏠 [UI_HOME_VIEW.md](docs/ui/UI_HOME_VIEW.md) | Widok główny - statystyki i filtry |
| 📚 [UI_LIBRARY_VIEW.md](docs/ui/UI_LIBRARY_VIEW.md) | Przeglądarka biblioteki Steam |
| 🪟 [UI_MAIN_WINDOW.md](docs/ui/UI_MAIN_WINDOW.md) | Główne okno i nawigacja |
| 🔐 [UI_AUTHENTICATION.md](docs/ui/UI_AUTHENTICATION.md) | System uwierzytelniania JWT |
| 🎨 [UI_STYLING.md](docs/ui/UI_STYLING.md) | Style Qt i ciemny motyw |

### 🔒 Dokumentacja Bezpieczeństwa

| Dokument | Opis |
|----------|------|
| 🔑 **[AUTH_AND_SIGNING_README.md](docs/security/AUTH_AND_SIGNING_README.md)** | **Pełny przewodnik po autoryzacji i podpisywaniu** |
| 🛡️ [PROPOZYCJE_ZABEZPIECZEN.md](docs/security/PROPOZYCJE_ZABEZPIECZEN.md) | Plan implementacji zabezpieczeń |
| 🚦 [RATE_LIMITING_VALIDATION.md](docs/security/RATE_LIMITING_VALIDATION.md) | Rate limiting i walidacja danych |

### 🔐 Dokumentacja JWT (JSON Web Tokens)

Kompleksowy przewodnik po systemie JWT:

| Dokument | Opis | Czas | Poziom |
|----------|------|------|--------|
| 📖 [JWT_OVERVIEW.md](docs/jwt/JWT_OVERVIEW.md) | Przegląd i quick start | 5 min | Wszyscy |
| 🎓 [JWT_TEORIA.md](docs/jwt/JWT_TEORIA.md) | Podstawy JWT - teoria | 15 min | Początkujący |
| 💻 [JWT_IMPLEMENTACJA.md](docs/jwt/JWT_IMPLEMENTACJA.md) | Szczegóły techniczne implementacji | 25 min | Średnio |
| 🔒 [JWT_ANALIZA_BEZPIECZENSTWA.md](docs/jwt/JWT_ANALIZA_BEZPIECZENSTWA.md) | Analiza zagrożeń i zabezpieczeń | 20 min | Zaawansowany |
| ⚡ [JWT_WPLYW_NA_WYDAJNOSC.md](docs/jwt/JWT_WPLYW_NA_WYDAJNOSC.md) | Wpływ JWT na wydajność aplikacji | 15 min | Średnio |
| ✅ [JWT_BEST_PRACTICES.md](docs/jwt/JWT_BEST_PRACTICES.md) | Best practices & DevOps | 20 min | Production |
| ⚡ [JWT_QUICK_REFERENCE.md](docs/jwt/JWT_QUICK_REFERENCE.md) | Quick reference card | 2 min | Quick lookup |
| 📋 [JWT_DOCUMENTATION_SUMMARY.md](docs/jwt/JWT_DOCUMENTATION_SUMMARY.md) | Podsumowanie dokumentacji JWT | 5 min | Wszyscy |

**🎯 Szybki start:**  
- **Serwer:** [SERVER_OVERVIEW.md](docs/server/SERVER_OVERVIEW.md) → poznaj backend  
- **GUI:** [UI_OVERVIEW.md](docs/ui/UI_OVERVIEW.md) → poznaj interfejs użytkownika  
- **Autoryzacja:** [AUTH_AND_SIGNING_README.md](docs/security/AUTH_AND_SIGNING_README.md) → zrozum bezpieczeństwo  
- **JWT:** [JWT_OVERVIEW.md](docs/jwt/JWT_OVERVIEW.md) → podstawy tokenów

---

## 🛠️ Stack Technologiczny

### Frontend (GUI)
| Technologia  | Wersja | Zastosowanie            |
|--------------|--------|-------------------------|
| **PySide6**  | 6.7+   | Framework Qt dla GUI    |
| **qasync**   | 0.26+  | Integracja Qt z asyncio |
| **httpx**    | 0.27+  | Klient HTTP/2           |
| **Pydantic** | 2.7+   | Walidacja modeli danych |

### Backend (Serwer)
| Technologia     | Wersja | Zastosowanie            |
|-----------------|--------|-------------------------|
| **FastAPI**     | 0.115+ | REST API framework      |
| **Uvicorn**     | 0.32+  | Serwer ASGI             |
| **PostgreSQL**  | 13+    | Baza danych             |
| **asyncpg**     | 0.29+  | Async driver PostgreSQL |
| **APScheduler** | 3.10+  | Scheduler zadań         |
| **slowapi**     | 0.1.9+ | Rate limiting           |

### Utilities
| Technologia       | Zastosowanie                         |
|-------------------|--------------------------------------|
| **tenacity**      | Retry logic z exponential backoff    |
| **python-dotenv** | Zarządzanie zmiennymi środowiskowymi |
| **loguru**        | Zaawansowane logowanie               |
| **platformdirs**  | Ścieżki specyficzne dla OS           |
| **PyInstaller**   | Budowanie plików wykonywalnych       |

---

## 🔒 Bezpieczeństwo

### Zaimplementowane Zabezpieczenia

#### Serwer Backend
- ✅ **Rate Limiting** - ograniczenie zapytań (100/minutę domyślnie)
- ✅ **Input Validation** - walidacja wszystkich danych wejściowych (Pydantic)
- ✅ **CORS** - konfiguracja dozwolonych origin
- ✅ **SQL Injection Protection** - parametryzowane zapytania (asyncpg)
- ✅ **Environment Variables** - wrażliwe dane w `.env`
- ✅ **Error Handling** - generyczne komunikaty błędów
- ✅ **Logging** - szczegółowe logi operacji

#### Aplikacja GUI
- ✅ **HTTPS Support** - możliwość połączenia przez TLS
- ✅ **Timeout Handling** - limity czasu żądań HTTP
- ✅ **Retry Logic** - automatyczne ponowne próby z backoff
- ✅ **Data Sanitization** - oczyszczanie danych przed wyświetleniem

### Zalecenia Produkcyjne

Przed wdrożeniem w środowisku produkcyjnym:

1. **Użyj HTTPS** - skonfiguruj certyfikat SSL/TLS
2. **Zmień hasła domyślne** - w PostgreSQL i `.env`
3. **Firewall** - ogranicz dostęp do portu 8000
4. **Reverse Proxy** - użyj nginx/Apache przed FastAPI
5. **Monitoring** - skonfiguruj Sentry lub podobne
6. **Backupy** - regularne kopie zapasowe bazy danych


---

## 🔮 Rozwój

### Planowane Funkcjonalności

- [ ] **Wykresy i wizualizacje** - interaktywne wykresy liczby graczy (matplotlib/pyqtgraph)
- [ ] **Heatmapa aktywności** - wizualizacja godzin szczytu
- [ ] **Multi-user support** - obsługa wielu profili Steam
- [ ] **Motywy** - ciemny/jasny motyw interfejsu
- [ ] **Rozszerzone filtry** - więcej opcji filtrowania
- [ ] **PWA/Web UI** - interfejs webowy obok GUI

### Architektura Docelowa

Planowana migracja do pełnej chmury:
- **AWS EC2** - hosting serwera FastAPI
- **AWS RDS** - PostgreSQL w chmurze

---

## 🐛 Troubleshooting

### Problemy z Serwerem

#### ❌ Błąd: "Connection to PostgreSQL failed"
```bash
# Sprawdź czy PostgreSQL działa
sudo systemctl status postgresql

# Sprawdź połączenie
psql -h localhost -U steam_user -d steam_dashboard

# Zweryfikuj dane w .env
cat .env | grep PG
```

#### ❌ Błąd: "Port 8000 already in use"
```bash
# Znajdź proces na porcie 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Zatrzymaj proces lub użyj innego portu
uvicorn server.app:app --port 8001
```

#### ❌ Błąd: "Steam API rate limit exceeded"
- Steam API ma limit ~200 żądań na 5 minut
- Scheduler automatycznie przestrzega limitów
- Możesz zwiększyć interwał w `scheduler.py`

---

### Problemy z GUI

#### ❌ Błąd: "Cannot connect to server"
```bash
# Sprawdź czy serwer działa
curl http://localhost:8000/health

# Sprawdź URL w zmiennej środowiskowej SERVER_URL
# Domyślnie używa http://localhost:8000
echo $SERVER_URL
```

#### ❌ Błąd: "Qt platform plugin not found"
```bash
# Linux - zainstaluj Qt dependencies
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Reinstall PySide6
pip uninstall PySide6
pip install PySide6
```

#### ❌ Okno się nie wyświetla
```bash
# Sprawdź display (Linux)
echo $DISPLAY

# Możliwe konflikty z Wayland - użyj X11
export QT_QPA_PLATFORM=xcb
python -m app.main_server
```

---

### Logi i Debugowanie

#### Włączenie szczegółowych logów
```python
# W server/app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Lokalizacja logów
- **Serwer**: stdout/stderr (lub plik konfigurowany w `app.py`)
- **GUI**: stdout aplikacji
- **PostgreSQL**: `/var/log/postgresql/` (Linux)

---

## 🤝 Contributing

Zapraszamy do współpracy! Aby wnieść swój wkład:

1. **Fork** repozytorium
2. Utwórz branch dla swojej funkcjonalności (`git checkout -b feature/AmazingFeature`)
3. Commit zmian (`git commit -m 'Add some AmazingFeature'`)
4. Push do brancha (`git push origin feature/AmazingFeature`)
5. Otwórz **Pull Request**

### Development Setup

```bash
# Klonuj repo
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard

# Zainstaluj zależności dev
pip install -r requirements.txt
```

---

## 📝 Licencja

Projekt jest dostępny na licencji **MIT** - szczegóły w pliku [LICENSE](LICENSE).

```
MIT License

Copyright (c) 2025 Custom Steam Dashboard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 🎨 Credits

### Ikony

Ikona aplikacji pochodzi z:
- **Marketing analysis icons** stworzone przez Fajrul Fitrianto - [Flaticon](https://www.flaticon.com/free-icons/marketing-analysis)

---

## 📧 Kontakt

Masz pytania lub sugestie? Skontaktuj się z nami!

- 🐛 **Issues**: [GitHub Issues](https://github.com/SzyMm0n/Custom-Steam-Dashboard/issues)
- 💬 **Dyskusje**: [GitHub Discussions](https://github.com/SzyMm0n/Custom-Steam-Dashboard/discussions)

---

<div align="center">

**⭐ Jeśli projekt Ci się podoba, zostaw gwiazdkę! ⭐**

Made with ❤️ using Python, Qt, and FastAPI

[⬆ Powrót do góry](#-custom-steam-dashboard)

</div>

