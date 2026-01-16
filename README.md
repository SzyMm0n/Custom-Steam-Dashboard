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
- ✅ **Zaawansowane filtry promocji** - filtrowanie według % zniżki, ceny, sklepów i treści
- ✅ **Kalendarz premier** - nie przegap nadchodzących wydań
- ✅ **Analiza biblioteki** - przegląd Twojej kolekcji Steam z czasem gry
- ✅ **System motywów** - Ciemny/Jasny tryb + 4 palety kolorów (Zielona, Niebieska, Fioletowa, Pomarańczowa)
- ✅ **Kreator własnych motywów** - twórz własne palety kolorów dopasowane do Twoich preferencji
- ✅ **Trwałość preferencji** - automatyczne zapisywanie ustawień motywów i ostatniej biblioteki
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
│   ├── __init__.py
│   ├── main_server.py               # Punkt wejścia aplikacji
│   ├── main_window.py               # Główne okno Qt
│   │
│   ├── ui/                          # Komponenty interfejsu
│   │   ├── __init__.py
│   │   ├── home_view_server.py      # Widok główny (statystyki)
│   │   ├── library_view_server.py   # Widok biblioteki
│   │   ├── comparison_view_server.py # Widok porównawczy (wykresy)
│   │   ├── deals_view_server.py     # Widok promocji
│   │   ├── components_server.py     # Reużywalne komponenty
│   │   ├── user_info_dialog_server.py # Dialog użytkownika
│   │   └── styles.py                # Style Qt
│   │
│   ├── core/                        # Logika biznesowa GUI
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── server_client.py     # Klient HTTP do backendu
│   │       └── deals_client.py      # Integracja z IsThereAnyDeal API
│   │
│   ├── helpers/                     # Narzędzia pomocnicze
│   │   ├── __init__.py
│   │   ├── api_client.py            # Bazowy klient API
│   │   └── signing.py               # HMAC signing dla żądań
│   │
│   └── icons/                       # Ikony aplikacji
│       ├── icon-16x16.png
│       ├── icon-32x32.png
│       ├── icon-128x128.png
│       ├── icon-256x256.png
│       └── icon.ico
│
├── ⚙️ server/                       # SERWER BACKEND
│   ├── __init__.py
│   ├── app.py                       # Główna aplikacja FastAPI
│   ├── auth_routes.py               # Endpointy uwierzytelniania JWT
│   ├── middleware.py                # Middleware (CORS, auth)
│   ├── scheduler.py                 # Zarządzanie zadaniami APScheduler
│   ├── security.py                  # JWT, HMAC, rate limiting
│   ├── validation.py                # Walidatory Pydantic
│   │
│   ├── database/                    # Warstwa danych
│   │   ├── __init__.py
│   │   └── database.py              # Manager PostgreSQL
│   │
│   └── services/                    # Logika biznesowa
│       ├── __init__.py
│       ├── steam_service.py         # Klient Steam API
│       ├── deals_service.py         # Logika IsThereAnyDeal API
│       ├── models.py                # Modele Pydantic
│       ├── parse_html.py            # Parser HTML
│       └── _base_http.py            # Bazowy klient HTTP
│
├── 📚 docs/                         # DOKUMENTACJA
│   ├── general/                     # Dokumentacja ogólna
│   │   ├── DEALS_API_MIGRATION.md
│   │   ├── DISTRIBUTION.md
│   │   └── README_USER.md
│   │
│   ├── jwt/                         # Dokumentacja JWT
│   │   ├── JWT_OVERVIEW.md
│   │   ├── JWT_TEORIA.md
│   │   ├── JWT_IMPLEMENTACJA.md
│   │   ├── JWT_ANALIZA_BEZPIECZENSTWA.md
│   │   ├── JWT_WPLYW_NA_WYDAJNOSC.md
│   │   ├── JWT_BEST_PRACTICES.md
│   │   ├── JWT_QUICK_REFERENCE.md
│   │   └── JWT_DOCUMENTATION_SUMMARY.md
│   │
│   ├── security/                    # Dokumentacja bezpieczeństwa
│   │   ├── AUTH_AND_SIGNING_README.md
│   │   └── RATE_LIMITING_VALIDATION.md
│   │
│   ├── server/                      # Dokumentacja serwera
│   │   ├── SERVER_OVERVIEW.md
│   │   ├── SERVER_API_ENDPOINTS.md
│   │   ├── SERVER_SECURITY.md
│   │   ├── SERVER_DATABASE.md
│   │   ├── SERVER_SCHEDULER.md
│   │   ├── SERVER_SERVICES.md
│   │   └── SERVER_VALIDATION.md
│   │
│   └── ui/                          # Dokumentacja UI
│       ├── UI_OVERVIEW.md
│       ├── UI_COMPONENTS.md
│       ├── UI_HOME_VIEW.md
│       ├── UI_LIBRARY_VIEW.md
│       ├── UI_COMPARISON_VIEW.md
│       ├── UI_DEALS_VIEW.md
│       ├── UI_USER_INFO_DIALOG.md
│       ├── UI_MAIN_WINDOW.md
│       ├── UI_AUTHENTICATION.md
│       └── UI_STYLING.md
│
│
├── 🔧 build/                        # Pliki buildu (PyInstaller)
│   └── steam_dashboard/
│
├── 📦 dist/                         # Skompilowane pliki wykonywalne
│
├── .env.example                     # Przykładowa konfiguracja
├── .gitignore                       # Ignorowane pliki Git
├── requirements.txt                 # Zależności Pythona
├── steam_dashboard.spec             # Specyfikacja PyInstaller
├── build_executable.sh              # Skrypt budowania (Linux/Mac)
├── build_executable.bat             # Skrypt budowania (Windows)
├── check_build_deps.py              # Weryfikacja zależności buildu
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

## 🎨 System Motywów

Aplikacja posiada zaawansowany system motywów z pełną personalizacją:

### Tryby
- **🌙 Ciemny** (domyślny) - Idealny do pracy w nocy
- **☀️ Jasny** - Komfortowy w dziennym świetle

### Palety Kolorów
1. **Zielona** 🟢 (domyślna) - Przyjazna dla oczu
2. **Niebieska** 🔵 - Profesjonalny wygląd
3. **Fioletowa** 🟣 - Kreatywny styl
4. **Pomarańczowa** 🟠 - Energetyczny wygląd
5. **Własna** 🎨 - Kreator własnych palet!

### Kreator Własnych Motywów

1. Kliknij przełącznik palet → **"Stwórz własny..."**
2. Wybierz kolor bazowy (color picker)
3. Podgląd na żywo dla trybu ciemnego i jasnego
4. Nazwij i zapisz motyw
5. Motyw jest dostępny natychmiast!

### Automatyczne Zapisywanie

Wszystkie preferencje są automatycznie zapisywane:
- Wybrany tryb (ciemny/jasny)
- Wybrana paleta kolorów
- Własne motywy
- Ostatnio używana biblioteka Steam

**Szczegóły:** [UI_THEME_SYSTEM.md](docs/ui/UI_THEME_SYSTEM.md)

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

#### 💰 **Widok Promocji (Deals)**
- Przeglądaj najlepsze promocje z wielu sklepów (Steam, GOG, Epic, Humble)
- Wyszukiwarka gier z promocjami
- **Zaawansowane filtry**:
  - Minimalny procent zniżki (0-99%)
  - Zakres cen (min/max)
  - Wybór sklepów (Steam, GOG, Epic, Humble)
  - Filtr treści dla dorosłych
  - Sortowanie (według zniżki, ceny, ocen)
- Kliknij przycisk **Filtry** aby otworzyć dialog zaawansowanych opcji filtrowania
- Szczegóły gry po kliknięciu w pozycję

#### 📊 **Widok Porównawczy (Comparison)**
- Porównuj liczbę graczy wielu gier jednocześnie
- Interaktywne wykresy matplotlib
- Analiza trendów i statystyk

#### 🔄 **Odświeżanie Danych**
- Przycisk **Refresh** w toolbar
- Automatyczne odświeżanie co 5 minut (scheduler)

#### ⚙️ **Filtrowanie**
- **Tagi**: filtruj gry po gatunkach (Action, RPG, Strategy, itp.)
- **Liczba graczy**: ustaw zakres min/max aktywnych graczy

---

## 📦 Tworzenie Pakietu Wykonywalnego

### ✨ Nowy System Budowania (Wbudowana Konfiguracja)

**Custom Steam Dashboard** używa nowoczesnego systemu budowania, który **wbudowuje konfigurację bezpośrednio w executable** podczas kompilacji. Oznacza to **zero konfiguracji dla użytkownika końcowego**!

### Przygotowanie

1. **Utwórz plik `.env` z konfiguracją produkcyjną:**

```bash
# .env - PRODUCTION CONFIGURATION
SERVER_URL=https://your-production-server.com
CLIENT_ID=desktop-main
CLIENT_SECRET=your-production-secret-here
```

2. **Zainstaluj zależności (jeśli jeszcze nie):**

```bash
pip install -r requirements.txt
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

### Co Się Dzieje Podczas Budowania?

```
1. Wczytaj konfigurację z .env
   ↓
2. Wygeneruj app/config.py z wbudowanymi wartościami
   ↓
3. Zbuduj executable z PyInstaller
   ↓
4. Przywróć oryginalny app/config.py (dla dev)
   ↓
5. ✨ Gotowy executable z wbudowaną konfiguracją!
```

### Rezultat

Plik wykonywalny znajdziesz w katalogu `dist/`:
- 🐧 Linux: `dist/CustomSteamDashboard`
- 🍎 macOS: `dist/CustomSteamDashboard.app`
- 🪟 Windows: `dist/CustomSteamDashboard.exe`

### 🎯 Kluczowe Zalety

- ✅ **Zero konfiguracji** - użytkownik po prostu uruchamia plik
- ✅ **Brak wrażliwych plików** - żadnych `.env` do dystrybucji
- ✅ **Jednorazowe budowanie** - dla każdego środowiska osobny build
- ✅ **Bezpieczne** - sekrety wbudowane w binary, trudniejsze do wydobycia

---

## 📖 Dokumentacja

Szczegółowa dokumentacja dostępna w katalogu `docs/`:

### 📘 Dokumentacja Ogólna

| Dokument | Opis |
|----------|------|
| 💰 [DEALS_API_MIGRATION.md](docs/general/DEALS_API_MIGRATION.md) | Migracja z CheapShark do IsThereAnyDeal API |
| 📦 [DISTRIBUTION.md](docs/general/DISTRIBUTION.md) | Przewodnik budowania i dystrybucji executable |
| 📖 [README_USER.md](docs/general/README_USER.md) | Instrukcja dla użytkownika końcowego |

> **ℹ️ Uwaga:** Dokumentacja techniczna została podzielona na moduły i znajduje się w sekcjach "Dokumentacja Serwera" i "Dokumentacja UI" poniżej.

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
| 📱 [UI_COMPONENTS.md](docs/ui/UI_COMPONENTS.md) | Komponenty i widgety reużywalne (GameDetailDialog, GameDetailPanel) |
| 🏠 [UI_HOME_VIEW.md](docs/ui/UI_HOME_VIEW.md) | Widok główny - statystyki i filtry |
| 📚 [UI_LIBRARY_VIEW.md](docs/ui/UI_LIBRARY_VIEW.md) | Przeglądarka biblioteki Steam |
| 📊 [UI_COMPARISON_VIEW.md](docs/ui/UI_COMPARISON_VIEW.md) | Widok porównawczy z wykresami matplotlib |
| 💰 [UI_DEALS_VIEW.md](docs/ui/UI_DEALS_VIEW.md) | Widok promocji i wyszukiwania okazji |
| 🔍 [UI_DEALS_FILTER_DIALOG.md](docs/ui/UI_DEALS_FILTER_DIALOG.md) | Dialog zaawansowanych filtrów promocji |
| 👤 [UI_USER_INFO_DIALOG.md](docs/ui/UI_USER_INFO_DIALOG.md) | Dialog profilu użytkownika Steam |
| 🪟 [UI_MAIN_WINDOW.md](docs/ui/UI_MAIN_WINDOW.md) | Główne okno i nawigacja |
| 🔐 [UI_AUTHENTICATION.md](docs/ui/UI_AUTHENTICATION.md) | System uwierzytelniania JWT |
| 🎨 [UI_STYLING.md](docs/ui/UI_STYLING.md) | Style Qt i system motywów |
| 🎨 [UI_THEME_SYSTEM.md](docs/ui/UI_THEME_SYSTEM.md) | System motywów - Ciemny/Jasny + palety |
| 🖌️ [UI_CUSTOM_THEME_DIALOG.md](docs/ui/UI_CUSTOM_THEME_DIALOG.md) | Kreator własnych motywów kolorystycznych |
| 💾 [UI_USER_DATA_PERSISTENCE.md](docs/ui/UI_USER_DATA_PERSISTENCE.md) | System trwałości preferencji użytkownika |

### 🔒 Dokumentacja Bezpieczeństwa

| Dokument | Opis |
|----------|------|
| 🔑 **[AUTH_AND_SIGNING_README.md](docs/security/AUTH_AND_SIGNING_README.md)** | **Pełny przewodnik po autoryzacji i podpisywaniu** |
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

## 🧪 Testy

Projekt implementuje **355 testów** w trzech kategoriach z różnymi strategiami mockowania.

### 📊 Statystyki

```
Testy jednostkowe:     229/232 passing (98.7%)
Testy integracyjne:    ~91/97 passing (94%)
Testy funkcjonalne:    26/26 passing (100%)
ŁĄCZNIE:               ~346/355 passing (97.5%)

Pokrycie kodu:         ~75% (backend + app core)
                       UI wykluczone (wymaga pytest-qt/E2E)
```

### 🎯 Typy Testów

#### **Unit Tests (232)** - Mock Everything
Logika w izolacji, wszystkie zależności mockowane.

#### **Integration Tests (97)** - Real Infrastructure  
Prawdziwa baza + FastAPI + AsyncClient.

#### **Functional Tests (26)** - End-to-End Scenarios
Kompletne scenariusze użytkownika (Happy + Sad paths):
- Authentication (5 testów) - HMAC + JWT flow
- Watchlist CRUD (4 testy) - Complete lifecycle
- Steam API (4 testy) - External integration
- Scheduler (2 testy) - Background jobs
- Rate Limiting (1 test) - Normal usage
- Concurrent Operations (2 testy) - Race conditions
- Data Validation (6 testów) - Input validation
- Error Handling (2 testy) - Graceful degradation

### 🚀 Uruchamianie

**ZALECANE:** Użyj skryptów wrapper (uruchamiają sekwencyjnie)

```bash
# Wszystkie testy z coverage
./run_tests.sh

# Unit (szybkie)
./run_tests.sh unit

# Integration (sekwencyjnie z opóźnieniami)
./run_tests.sh integration

# Functional scenarios (end-to-end)
pytest tests/functional/ -v
```

### 📚 Dokumentacja Testów

| Dokument                                                                   | Opis |
|----------------------------------------------------------------------------|------|
| 📖 **[README.md](tests/README.md)**                                        | **Główny przewodnik** - filozofia, infrastruktura, zasady |
| 📊 [SUMMARY.md](tests/docs/SUMMARY.md)                                     | Coverage, scenariusze, metryki z analizą |
| 🔬 [UNIT.md](tests/docs/UNIT.md)                                           | 5 przykładów unit testów ze scenariuszami |
| 🔗 [INTEGRATION.md](tests/docs/INTEGRATION.md)                   | 5 przykładów integration testów |
| 🎯 [FUNCTIONAL_TEST_PLAN.md](tests/docs/FUNCTIONAL_TEST_PLAN.md) | **26 testów funkcjonalnych** (szczegółowo opisane) |

**Kluczowe koncepty:**
- **Unit tests** - mockuj wszystko, szybkie (<100ms każdy), deterministyczne
- **Integration tests** - prawdziwa infrastruktura, unique schema per test, cleanup automatyczny
- **Functional tests** - end-to-end scenariusze użytkownika, real world user flows
- **Sekwencyjne uruchamianie** - eliminuje resource exhaustion (opóźnienia 1-3s między grupami)
- **UI wykluczone** z coverage - wymaga pytest-qt/E2E testów

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
## 🎨 Credits

### Ikony

Ikona aplikacji pochodzi z:
- **Marketing analysis icons** stworzone przez Fajrul Fitrianto - [Flaticon](https://www.flaticon.com/free-icons/marketing-analysis)
