# BACKEND_AUTH_A – raport Semgrep (SZABLON)
Autor: Jakub Gilewski <br>
Data: 2025-11-29

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
  semgrep scan --config semgrep/rules_backend_auth.yml server/app.py server/auth_routes.py server/middleware.py server/security.py server/validation.py

  ```

- Użyte rulesety:
  - `p/python`
  - `p/security-audit`
  - lokalne:
    - `semgrep/rules_backend_auth.yml`

- Wersja Semgrepa:

  ```bash
  1.144.0
  ```

## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings: 0

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

- **ID:** `hardcoded-jwt-secret`
- **Cel:** Wykrywanie domyślnego, niebezpiecznego sekretu JWT (`"insecure-default-change-me"`) w kodzie. Używanie domyślnych sekretów w środowisku produkcyjnym jest krytyczną luką w zabezpieczeniach.
- **Pattern (skrót):** `'"insecure-default-change-me"'`
- **Zakres działania:** `server/`

- **ID:** `broad-exception-disclosure`
- **Cel:** Identyfikacja bloków `except Exception as e:`, które następnie zwracają `str(e)` w odpowiedzi HTTP. Może to prowadzić do wycieku wrażliwych informacji o wewnętrznym działaniu aplikacji.
- **Pattern (skrót):** `except Exception as $E:` ... `HTTPException(..., detail=str($E), ...)`
- **Zakres działania:** `server/`

- **ID:** `insecure-dependency-require-auth`
- **Cel:** Wykrywanie użycia zależności `require_auth`, która weryfikuje tylko token JWT, ale nie sprawdza podpisu HMAC żądania. Może to być niebezpieczne w przypadku endpointów API, które powinny używać `require_session_and_signed_request` do pełnej weryfikacji.
- **Pattern (skrót):** `fastapi.Depends(server.security.require_auth)`
- **Zakres działania:** `server/`

### 4.2. Efekty działania reguł

**Reguła: `hardcoded-jwt-secret`**

-   **Czy znaleziono dopasowania?** Tak, 1.
    -   **Plik i linia:** `server/security.py:39`
    -   **Opis:** W kodzie na stałe zaszyty jest domyślny sekret JWT: `"insecure-default-change-me"`.
    -   **Ocena:** Jest to false positve. Błąd został znaleziony w funkcji która waliduje tokeny JWT, ale w rzeczywistości aplikacja ładuje sekret z bezpiecznego źródła (np. zmiennej środowiskowej) w innym miejscu kodu.

**Reguła: `broad-exception-disclosure`**

-   **Czy znaleziono dopasowania?** Tak, 15.
    -   **Plik i linia:** `server/app.py` (wielokrotnie, m.in. w liniach 235, 257, 279, 299, 316, 327, 345, 378, 392, 404, 416, 519, 585, 637, 693).
    -   **Opis:** Wiele endpointów API łapie ogólny wyjątek `Exception as e` i zwraca jego treść (`str(e)`) bezpośrednio w odpowiedzi HTTP.
    -   **Ocena:** Jest to **realny problem** (CWE-209). Ujawnianie szczegółów błędów (np. ścieżek plików, zapytań SQL, nazw bibliotek) może dostarczyć atakującemu cennych informacji o wewnętrznej strukturze aplikacji, ułatwiając dalsze ataki. Poprawka polega na logowaniu szczegółowego błędu po stronie serwera i zwracaniu użytkownikowi ogólnego, nic niemówiącego komunikatu o błędzie.

**Reguła: `insecure-dependency-require-auth`**

-   **Czy znaleziono dopasowania?** Tak, 4.
    -   **Plik i linia:** `server/app.py` (linie 165, 176, 185) oraz `server/auth_routes.py` (linia 109).
    -   **Opis:** W kilku miejscach, w tym w endpointach dokumentacji (`/docs`, `/redoc`) oraz w endpointach odświeżania tokenu, używana jest zależność `require_auth`. Weryfikuje ona jedynie poprawność tokenu JWT, ale nie sprawdza podpisu HMAC całego żądania.
    -   **Ocena:** Jest to **częściowo realny problem, a częściowo false positive**.
        -   W przypadku endpointów `/docs` i `/redoc` jest to **akceptowalne**, ponieważ dostęp do dokumentacji nie wymaga pełnego zabezpieczenia HMAC – wystarczy ważna sesja JWT.
        -   W przypadku endpointu odświeżania tokenu (`/api/auth/refresh-token`) jest to **potencjalne ryzyko**. Chociaż odświeżenie tokenu nie modyfikuje danych, poleganie tylko na JWT otwiera teoretyczną możliwość (choć mało prawdopodobną) wykorzystania skradzionego tokenu bez konieczności podpisywania żądania. Lepszą praktyką byłoby użycie `require_session_and_signed_request` również tutaj, dla spójności i maksymalnego bezpieczeństwa.

---

## 5. Wnioski dla obszaru backend (auth/security)

-   **Co Semgrep realnie pomógł znaleźć w tym obszarze?**
    Semgrep okazał się bardzo skuteczny w automatycznym wykrywaniu krytycznych i częstych błędów bezpieczeństwa. Zidentyfikował:
    1. **Systemowy problem:** Wielokrotne przypadki potencjalnego wycieku informacji poprzez nieprawidłową obsługę wyjątków. Pokazuje to brak spójnego wzorca obsługi błędów w aplikacji.
    2. **Niespójne zabezpieczenia:** Wykryto, że niektóre endpointy (nawet jeśli mniej krytyczne, jak dokumentacja API) używają słabszej formy uwierzytelniania (`require_auth` zamiast `require_session_and_signed_request`), co może prowadzić do niejednolitego poziomu bezpieczeństwa w całej aplikacji.

-   **Jakie były ograniczenia?**
    Głównym ograniczeniem pozostaje potrzeba precyzyjnego dostosowania reguł, aby unikać fałszywych alarmów (false positives). Reguła `insecure-dependency-require-auth` zidentyfikowała przypadki, które są zarówno uzasadnione (dokumentacja API), jak i potencjalnie ryzykowne (odświeżanie tokenu). Wymaga to ręcznej analizy i kontekstowego zrozumienia, czego automatyczne narzędzie nie jest w stanie w pełni zapewnić.

-   **Rekomendacje:**
    1. **Wprowadzenie centralnego mechanizmu obsługi wyjątków:** Należy zaimplementować w FastAPI middleware, który będzie przechwytywał wszystkie nieobsłużone wyjątki, logował ich pełną treść do wewnętrznego systemu monitoringu i zwracał klientowi ustandaryzowaną, ogólną odpowiedź o błędzie (np. `{"detail": "Internal Server Error"}`).
    2. **Ujednolicenie polityki bezpieczeństwa endpointów:** Należy dokonać przeglądu wszystkich endpointów i świadomie zdecydować, które z nich mogą korzystać z `require_auth`, a które bezwzględnie wymagają `require_session_and_signed_request`. Rekomenduje się, aby wszystkie endpointy API modyfikujące dane lub zwracające wrażliwe informacje używały pełnego zabezpieczenia HMAC. Warto dodać komentarze w kodzie uzasadniające użycie `require_auth` w dozwolonych przypadkach.
