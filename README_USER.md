# Custom Steam Dashboard - Instrukcja Użytkownika

## 🚀 Pierwsze Uruchomienie

### 1. Konfiguracja

Przed uruchomieniem aplikacji **MUSISZ** skonfigurować plik `.env`:

1. Otwórz plik `.env` w edytorze tekstu (np. Notepad, nano, vim)
2. Wypełnij wymagane pola:

```bash
# Adres serwera backend (otrzymasz od administratora)
SERVER_URL=http://localhost:8000

# Dane uwierzytelniające (otrzymasz od administratora)
CLIENT_ID=desktop-main
CLIENT_SECRET=twój-sekretny-klucz-tutaj
```

3. Zapisz plik

### 2. Uruchomienie

**Linux/macOS:**
```bash
./CustomSteamDashboard
```

**Windows:**
```
Kliknij dwukrotnie: CustomSteamDashboard.exe
```

---

## ⚙️ Konfiguracja

### Wymagane zmienne w .env:

| Zmienna | Opis | Przykład |
|---------|------|----------|
| `SERVER_URL` | Adres serwera backend | `http://192.168.1.100:8000` |
| `CLIENT_ID` | Twój identyfikator klienta | `desktop-main` |
| `CLIENT_SECRET` | Sekretny klucz (od administratora) | `ABC123XYZ...` |

### Jak uzyskać dane konfiguracyjne?

Skontaktuj się z administratorem serwera. Otrzymasz:
- Adres serwera (`SERVER_URL`)
- Identyfikator (`CLIENT_ID`)
- Sekretny klucz (`CLIENT_SECRET`)

---

## 🐛 Rozwiązywanie Problemów

### ❌ "Authentication Failed"

**Problem:** Nie można uwierzytelnić z serwerem

**Rozwiązanie:**
1. Sprawdź czy `SERVER_URL` w `.env` jest prawidłowy
2. Sprawdź czy serwer działa (pytaj administratora)
3. Sprawdź czy `CLIENT_ID` i `CLIENT_SECRET` są poprawne
4. Sprawdź czy `.env` jest w tym samym folderze co aplikacja

### ❌ "Cannot connect to server"

**Problem:** Aplikacja nie może połączyć się z serwerem

**Rozwiązanie:**
1. Sprawdź połączenie internetowe / sieciowe
2. Sprawdź czy `SERVER_URL` jest prawidłowy
3. Skontaktuj się z administratorem serwera
4. Sprawdź firewall / blokady sieci

### ❌ Aplikacja się nie uruchamia

**Problem:** Nic się nie dzieje po kliknięciu

**Rozwiązanie:**
1. Sprawdź czy plik `.env` istnieje w tym samym folderze
2. Uruchom z konsoli/terminala, aby zobaczyć błędy:
   - **Linux/macOS:** `./CustomSteamDashboard`
   - **Windows:** Otwórz cmd, przejdź do folderu, uruchom `CustomSteamDashboard.exe`
3. Sprawdź uprawnienia do wykonania (Linux/macOS): `chmod +x CustomSteamDashboard`

### ❌ "File .env not found"

**Problem:** Aplikacja nie może znaleźć pliku .env

**Rozwiązanie:**
1. Upewnij się, że `.env` jest w tym samym katalogu co executable
2. Sprawdź nazwę pliku (dokładnie `.env`, nie `.env.txt`)
3. Na Windows: włącz wyświetlanie rozszerzeń plików

---

## 📁 Struktura Plików

Poprawna struktura folderów:

```
SteamDashboard/
├── CustomSteamDashboard        # Executable (lub .exe na Windows)
├── .env                         # Konfiguracja (WYMAGANE!)
├── README_USER.md              # Ten plik
└── [inne pliki...]             # Biblioteki (nie usuwaj!)
```

**WAŻNE:** Nie przenoś samego executable - zawsze przenoś cały folder!

---

## 🔐 Bezpieczeństwo

### ⚠️ Chroń swój `.env`!

Plik `.env` zawiera sekretny klucz (`CLIENT_SECRET`):
- ❌ **NIE udostępniaj** tego pliku innym osobom
- ❌ **NIE wysyłaj** go przez email/chat
- ❌ **NIE wrzucaj** go na publiczne repozytoria (GitHub itp.)
- ✅ **TRZYMAJ** go tylko na swoim komputerze

Jeśli ktoś zdobędzie twój `CLIENT_SECRET`, może:
- Udawać ciebie w systemie
- Uzyskać dostęp do twoich danych
- Wykonywać operacje w twoim imieniu

### Co zrobić jeśli ujawnisz sekret?

1. Natychmiast skontaktuj się z administratorem
2. Poproś o wygenerowanie nowego `CLIENT_SECRET`
3. Zaktualizuj `.env` z nowym kluczem

---

## 📞 Pomoc

Jeśli masz problemy:

1. Sprawdź tę instrukcję
2. Skontaktuj się z administratorem serwera
3. Podaj dokładny komunikat błędu

---

## ℹ️ Informacje Techniczne

- **Framework:** PySide6 (Qt)
- **Platforma:** Windows, Linux, macOS
- **Wymagania:** Połączenie z serwerem backend
- **Licencja:** Zobacz plik LICENSE

---

**Wersja dokumentacji:** 1.0  
**Data:** 2025-01-11

