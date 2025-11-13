# Dystrybucja Aplikacji Custom Steam Dashboard

## 📦 Budowanie Executable

### Linux/macOS:
```bash
./build_executable.sh
```

### Windows:
```bash
build_executable.bat
```

Po pomyślnym zbudowaniu, w folderze `dist/` znajdziesz:
- **Executable** (`CustomSteamDashboard` lub `CustomSteamDashboard.exe`)
- **Plik .env** (skopiowany z `.env.example`)
- **Dodatkowe pliki** (biblioteki, ikony)

---

## 🚀 Uruchamianie Zbudowanej Aplikacji

### Wymagania:
1. **Serwer backend** musi być uruchomiony i dostępny
2. **Plik .env** musi być skonfigurowany

### Struktura folderów:
```
dist/
├── CustomSteamDashboard       # Executable
├── .env                       # Konfiguracja (WYMAGANE!)
└── [inne pliki...]            # Biblioteki systemowe
```

### Konfiguracja .env:

**MUSISZ** edytować plik `dist/.env` przed uruchomieniem aplikacji:

```bash
# ===== WYMAGANE DLA KLIENTA GUI =====

# URL serwera backend (gdzie działa FastAPI)
SERVER_URL=http://localhost:8000          # Lokalny serwer
# SERVER_URL=http://192.168.1.100:8000   # Serwer w sieci LAN
# SERVER_URL=https://api.example.com     # Serwer zdalny

# Dane uwierzytelniające klienta
CLIENT_ID=desktop-main
CLIENT_SECRET=Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0

# ===== OPCJONALNE (dla deweloperów) =====
# STEAM_API_KEY, ITAD_API_KEY, itp. - NIE są potrzebne w kliencie GUI
# Te zmienne są używane tylko przez serwer backend
```

### Ważne uwagi:

1. **Plik .env MUSI być w tym samym folderze co executable**
   - ✅ `dist/CustomSteamDashboard` + `dist/.env`
   - ❌ `dist/CustomSteamDashboard` + `/home/user/.env`

2. **CLIENT_SECRET musi pasować do konfiguracji serwera**
   - Wartość `CLIENT_SECRET` w kliencie musi być taka sama jak w `CLIENTS_JSON` na serwerze

3. **SERVER_URL musi wskazywać na działający serwer**
   - Sprawdź: `curl http://localhost:8000/health` (powinno zwrócić `{"status":"healthy"}`)

---

## 🌍 Dystrybucja dla Użytkowników Końcowych

### Opcja 1: Cały folder `dist/`

**Najlepsze dla większości przypadków**

```bash
# Spakuj cały folder
zip -r SteamDashboard.zip dist/

# Lub tar.gz
tar -czf SteamDashboard.tar.gz dist/
```

**Instrukcje dla użytkownika:**
1. Rozpakuj archiwum
2. Edytuj plik `.env`:
   - Ustaw `SERVER_URL` (adres serwera backend)
   - Wpisz `CLIENT_ID` i `CLIENT_SECRET` (otrzymane od administratora)
3. Uruchom executable

### Opcja 2: Installer z konfiguratorem

**Dla bardziej profesjonalnej dystrybucji**

Możesz stworzyć installer, który:
- Instaluje aplikację w wybranym katalogu
- Pyta o `SERVER_URL`, `CLIENT_ID`, `CLIENT_SECRET`
- Automatycznie tworzy plik `.env`

Przykładowe narzędzia:
- **Windows**: Inno Setup, NSIS
- **macOS**: create-dmg
- **Linux**: AppImage, .deb/.rpm packages

### Opcja 3: Zmienne środowiskowe systemowe

**Dla zaawansowanych użytkowników**

Zamiast pliku `.env`, użytkownik może ustawić zmienne systemowe:

**Linux/macOS:**
```bash
export SERVER_URL=http://192.168.1.100:8000
export CLIENT_ID=desktop-main
export CLIENT_SECRET=your-secret-here
./CustomSteamDashboard
```

**Windows:**
```cmd
set SERVER_URL=http://192.168.1.100:8000
set CLIENT_ID=desktop-main
set CLIENT_SECRET=your-secret-here
CustomSteamDashboard.exe
```

---

## 🔐 Bezpieczeństwo

### ⚠️ NIE DYSTRYBUUJ `.env` z sekretami!

**NIE rób tego:**
```bash
# ❌ ZŁE - zawiera twoje sekrety!
cp .env dist/.env
zip -r SteamDashboard.zip dist/
```

**Zrób to zamiast:**
```bash
# ✅ DOBRE - zawiera tylko przykładową konfigurację
cp .env.example dist/.env
# Edytuj dist/.env i usuń sekrety, zostaw tylko placeholdery
zip -r SteamDashboard.zip dist/
```

### Najlepsze praktyki:

1. **Każdy użytkownik powinien mieć swój CLIENT_SECRET**
   - Generuj: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Dodaj do `CLIENTS_JSON` na serwerze

2. **Nie commituj `.env` do Git**
   - `.env` jest w `.gitignore`
   - Commituj tylko `.env.example`

3. **Dokumentuj wymagania**
   - Jasno opisz, co użytkownik musi skonfigurować
   - Podaj przykładowe wartości

---

## 🐛 Rozwiązywanie Problemów

### Problem: "Authentication Failed"

**Przyczyna:** Nieprawidłowa konfiguracja uwierzytelniania

**Rozwiązanie:**
1. Sprawdź czy serwer działa: `curl http://localhost:8000/health`
2. Sprawdź `SERVER_URL` w `.env` (czy wskazuje na właściwy adres)
3. Sprawdź czy `CLIENT_ID` i `CLIENT_SECRET` są prawidłowe
4. Sprawdź czy `CLIENT_SECRET` w kliencie pasuje do `CLIENTS_JSON` na serwerze

### Problem: "Cannot connect to server"

**Przyczyna:** Serwer jest niedostępny lub zły URL

**Rozwiązanie:**
1. Sprawdź czy serwer jest uruchomiony
2. Sprawdź `SERVER_URL` w `.env`
3. Sprawdź firewall/porty
4. Sprawdź czy adres IP/domena są poprawne

### Problem: ".env not found"

**Przyczyna:** Plik `.env` nie jest w tym samym katalogu co executable

**Rozwiązanie:**
1. Upewnij się, że `.env` jest w folderze `dist/` obok executable
2. Sprawdź uprawnienia do odczytu pliku
3. Nie przenoś executable bez pliku `.env`

### Problem: "Invalid SERVER_URL format"

**Przyczyna:** Błędny format URL w `.env`

**Rozwiązanie:**
Poprawne formaty:
- ✅ `http://localhost:8000`
- ✅ `http://192.168.1.100:8000`
- ✅ `https://api.example.com`
- ❌ `localhost:8000` (brak protokołu)
- ❌ `http://localhost:8000/` (końcowy slash - zostanie usunięty automatycznie)

---

## 📝 Checklist dla Dystrybucji

Przed wysłaniem aplikacji użytkownikowi:

- [ ] Zbudowano executable (`./build_executable.sh` lub `build_executable.bat`)
- [ ] Skopiowano `.env.example` jako `dist/.env`
- [ ] Usunięto sekrety z `dist/.env` (zostawiono placeholdery)
- [ ] Przetestowano executable lokalnie
- [ ] Przygotowano instrukcje konfiguracji dla użytkownika
- [ ] Wygenerowano unikalne `CLIENT_ID` i `CLIENT_SECRET` dla użytkownika
- [ ] Dodano te credentials do `CLIENTS_JSON` na serwerze
- [ ] Przekazano użytkownikowi:
  - Archiwum z aplikacją
  - Adres serwera (`SERVER_URL`)
  - Credentials (`CLIENT_ID`, `CLIENT_SECRET`)
  - Instrukcje instalacji i konfiguracji

---

## 🎯 Przykładowy Email dla Użytkownika

```
Temat: Custom Steam Dashboard - Instrukcje Instalacji

Cześć!

Przesyłam aplikację Custom Steam Dashboard.

INSTALACJA:
1. Rozpakuj załączony plik SteamDashboard.zip
2. Otwórz plik .env w edytorze tekstu
3. Wpisz następujące dane:

   SERVER_URL=http://192.168.1.100:8000
   CLIENT_ID=user-jan-kowalski
   CLIENT_SECRET=ABC123XYZ789...

4. Zapisz plik .env
5. Uruchom CustomSteamDashboard (lub CustomSteamDashboard.exe na Windows)

WYMAGANIA:
- Serwer backend musi być uruchomiony i dostępny
- Musisz mieć połączenie z serwerem

POMOC:
Jeśli masz problemy, sprawdź plik DISTRIBUTION.md w projekcie.

Pozdrawiam!
```

