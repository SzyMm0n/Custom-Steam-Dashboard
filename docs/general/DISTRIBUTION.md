# Dystrybucja Aplikacji Custom Steam Dashboard

**Data aktualizacji:** 2025-11-19  
**Wersja:** 2.0

## 📦 Budowanie Executable

### Nowy Proces Budowania (z Wbudowaną Konfiguracją)

**Custom Steam Dashboard** używa nowego systemu budowania, który wbudowuje konfigurację bezpośrednio w executable podczas kompilacji. To oznacza **zero konfiguracji dla użytkownika końcowego**.

### Przygotowanie do Budowania

1. **Utwórz plik `.env` z konfiguracją produkcyjną:**

```bash
# .env - PRODUCTION CONFIGURATION
SERVER_URL=https://your-production-server.com
CLIENT_ID=desktop-main
CLIENT_SECRET=your-production-secret-here
```

2. **Skrypt automatycznie:**
   - Wczyta wartości z `.env`
   - Wygeneruje `app/config.py` z wbudowanymi wartościami
   - Zbuduje executable z PyInstaller
   - Przywróci oryginalny `app/config.py`

### Linux/macOS:
```bash
./build_executable.sh
```

### Windows:
```bash
build_executable.bat
```

### Co Się Dzieje Podczas Budowania?

```
┌─────────────────────────────────────────────┐
│ 1. Wczytaj .env                             │
│    ✓ SERVER_URL                             │
│    ✓ CLIENT_ID                              │
│    ✓ CLIENT_SECRET                          │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ 2. Generuj app/config.py                    │
│    (generate_config.py)                     │
│    ✓ Wartości wbudowane w kod               │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ 3. Zbuduj executable                        │
│    (PyInstaller)                            │
│    ✓ Config wbudowany w binary              │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ 4. Przywróć app/config.py                   │
│    (restore_config.py)                      │
│    ✓ Kod deweloperski zachowany             │
└─────────────────────────────────────────────┘
```

### Po Pomyślnym Zbudowaniu

W folderze `dist/` znajdziesz:
- **Executable** (`CustomSteamDashboard` lub `CustomSteamDashboard.exe`)
- **Żadnych dodatkowych plików konfiguracyjnych!** ✨

---

## 🚀 Uruchamianie Zbudowanej Aplikacji

### ✨ Zero Konfiguracji!

Aplikacja jest **gotowa do uruchomienia od razu** - wszystkie wartości są wbudowane podczas kompilacji.

### Linux/macOS:
```bash
./dist/CustomSteamDashboard
```

### Windows:
```cmd
dist\CustomSteamDashboard.exe
```

### Struktura folderów:
```
dist/
├── CustomSteamDashboard       # Executable (standalone!)
└── [inne pliki...]            # Biblioteki systemowe (jeśli potrzebne)
```

### Co Jest Wbudowane?

Podczas budowania, następujące wartości są **hardcoded** w executable:

```python
# Wbudowane podczas kompilacji z .env
SERVER_URL = "https://your-production-server.com"
CLIENT_ID = "desktop-main"
CLIENT_SECRET = "your-production-secret"
```

### Opcjonalne: Nadpisywanie Konfiguracji

Jeśli użytkownik **chce** zmienić serwer, może użyć zmiennych środowiskowych:

**Linux/macOS:**
```bash
export SERVER_URL=http://custom-server.com
./CustomSteamDashboard
```

**Windows:**
```cmd
set SERVER_URL=http://custom-server.com
CustomSteamDashboard.exe
```

---

## 🌍 Dystrybucja dla Użytkowników Końcowych

### ✅ Nowy Sposób: Pojedynczy Plik

**Najprostszy dla użytkowników!**

Dystrybucja sprowadza się do **jednego pliku executable**:

```bash
# Spakuj tylko executable
zip SteamDashboard.zip dist/CustomSteamDashboard

# Lub po prostu skopiuj plik
cp dist/CustomSteamDashboard /path/to/destination/
```

**Instrukcje dla użytkownika:**
1. Pobierz plik
2. Uruchom
3. Gotowe! 🎉

### Dla Różnych Środowisk

#### Development Build (localhost)
```bash
# .env
SERVER_URL=http://localhost:8000
CLIENT_ID=desktop-main
CLIENT_SECRET=dev-secret-123

./build_executable.sh
# → Executable działa z localhost
```

#### Production Build (remote server)
```bash
# .env
SERVER_URL=https://api.production.com
CLIENT_ID=desktop-main
CLIENT_SECRET=prod-secret-xyz

./build_executable.sh
# → Executable działa z production server
```

#### Internal Network Build
```bash
# .env
SERVER_URL=http://192.168.1.100:8000
CLIENT_ID=desktop-main
CLIENT_SECRET=internal-secret-abc

./build_executable.sh
# → Executable działa w sieci LAN
```

---

## 🔐 Bezpieczeństwo

### ✅ Zalety Nowego Podejścia

1. **Brak wrażliwych plików** - żadnych `.env` do dystrybucji
2. **Zero konfiguracji** - użytkownik nie widzi sekretów
3. **Trudniejsze reverse engineering** - wartości w skompilowanym binary
4. **Jednolita konfiguracja** - wszystkie kopie mają tę samą wersję

### ⚠️ Ważne: Zarządzanie Sekretami

1. **Nigdy nie commituj `.env` z produkcyjnymi sekretami**
   ```bash
   # .gitignore zawiera:
   .env
   ```

2. **Każde środowisko = osobny build**
   - Development build → dev secrets
   - Production build → production secrets
   - Test build → test secrets

3. **Secure build environment**
   ```bash
   # Buduj na bezpiecznej maszynie
   # Nie buduj na współdzielonych systemach
   # Usuń .env po zbudowaniu (jeśli zawiera produkcyjne sekrety)
   ```

### 🔄 Rotacja Sekretów

Jeśli `CLIENT_SECRET` się zmieni:
1. Zaktualizuj `.env` z nowym sekretem
2. Przebuduj executable: `./build_executable.sh`
3. Dystrybuuj nową wersję do użytkowników

---

## 🛠️ Zaawansowane: Build Pipeline
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

