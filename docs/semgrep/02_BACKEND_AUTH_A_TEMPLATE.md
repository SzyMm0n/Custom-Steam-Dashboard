# BACKEND_AUTH_A – raport Semgrep (SZABLON)
Autor: [Imię i nazwisko]
Data: [RRRR-MM-DD]

## 1. Zakres analizy

- Katalogi:
  - `server/`
- Pliki:
  - `server/app.py`
  - `server/auth_routes.py`
  - `server/middleware.py`
  - `server/security.py`
  - `server/validation.py`

Krótki opis:
- Ten fragment backendu odpowiada za logikę serwera HTTP (FastAPI), uwierzytelnianie (JWT/HMAC), middleware i walidację danych. To krytyczne miejsce z punktu widzenia bezpieczeństwa (auth, autoryzacja, sanityzacja danych wejściowych).

## 2. Konfiguracja Semgrepa

- Komenda bazowa używana w analizie:

  ```bash
  semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml server/app.py server/auth_routes.py server/middleware.py server/security.py server/validation.py
  ```

  Lub jeśli chcesz szybko tylko publiczne rulesets:

  ```bash
  semgrep scan --config=p/security-audit server/app.py server/auth_routes.py server/middleware.py server/security.py server/validation.py
  ```

- Użyte rulesety:
  - `p/python` (publiczny ruleset dla Pythona z Semgrep Registry)
  - `p/security-audit` (publiczny ruleset dla bezpieczeństwa z Semgrep Registry)
  - lokalne:
    - `semgrep/rules_backend_auth.yml`

- Wersja Semgrepa: (podaj wersję z `semgrep --version`, np. `1.144.0`)

## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings: X
- Kategorie (szacunkowo):
  - bezpieczeństwo: X1
  - poprawność: X2
  - styl / inne: X3

### 3.1. Najciekawsze przypadki (przykład 1)

1. **ID reguły:** `...`
2. **Plik i linia:** `server/security.py:NN`
3. **Opis Semgrepa (skrót):**  
   (np. "Semgrep wykrył potencjalnie niebezpieczne użycie funkcji X bez Y")
4. **Ocena:**
   - [ ] Prawdziwy problem
   - [ ] False positive / nieistotne
5. **Komentarz autora:**
   - Dlaczego jest / nie jest to problem,
   - ewentualna propozycja poprawki (fragment kodu lub opis słowny).

### 3.2. Najciekawsze przypadki (przykład 2)

*(analogicznie jak wyżej – łącznie 2–3 przypadki wystarczą)*

---

## 4. Własne reguły Semgrep – `semgrep/rules_backend_auth.yml`

Plik z regułami: `semgrep/rules_backend_auth.yml`

### 4.1. Lista reguł

Dla każdej reguły uzupełnij poniższe:

- **ID:** `...`
- **Cel:**  
  (np. "Wykrywanie `except Exception: pass` w kodzie backendu")
- **Pattern (skrót):**  
  (np. "Try/except, gdzie w except nie ma żadnej akcji")
- **Zakres działania:**  
  (np. tylko `server/` albo konkretne pliki).

Przykład (do wypełnienia i/lub modyfikacji):

- **ID:** `backend-auth-no-empty-except`
- **Cel:** Wymuszenie obsługi wyjątków zamiast ich ignorowania.
- **Pattern:** Wykrywanie `except Exception:` z pustym ciałem.
- **Zakres:** `server/`

### 4.2. Efekty działania reguł

Dla każdej reguły:

- Czy znaleziono dopasowania?
  - Jeśli tak – opisz minimum jeden przypadek:
    - plik, linia,
    - krótki opis,
    - czy to realny problem i jak go poprawić.
  - Jeśli nie – zanotuj, czy to wynika z tego, że kod jest OK, czy może pattern jest zbyt wąski.

---

## 5. Wnioski dla obszaru backend (auth/security)

- Co Semgrep realnie pomógł znaleźć w tym obszarze?
- Jakie były ograniczenia (np. false positives, brak wsparcia dla bardzo specyficznych patternów)?
- Jakie 1–2 rekomendacje dla dalszego rozwoju tej części aplikacji (np. "trzymać wszystkie operacje na JWT w jednym module i pilnować ich regułami Semgrepa", "pozbyć się pustych `except`").
