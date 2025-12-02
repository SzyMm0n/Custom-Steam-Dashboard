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
  # Skan z wszystkimi rulesetami (publicznymi + lokalnymi)
  semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml server/app.py server/auth_routes.py server/middleware.py server/security.py server/validation.py
  
  # Skan tylko z lokalnymi regułami (używany w tym raporcie do sekcji 4)
  semgrep scan --config=semgrep/rules_backend_auth.yml server/app.py server/auth_routes.py server/middleware.py server/security.py server/validation.py
  ```

- Użyte rulesety:
  - `p/python` (publiczne reguły Pythona z Semgrep Registry)
  - `p/security-audit` (publiczne reguły bezpieczeństwa z Semgrep Registry)
  - lokalne:
    - `semgrep/rules_backend_auth.yml`

- Wersja Semgrepa:

  ```bash
  1.144.0
  ```

## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings z publicznych rulesetów (`p/python` + `p/security-audit`): 0
- Uwaga: W ramach tego raportu skupiono się na analizie własnych reguł (sekcja 4). Publiczne rulesety zostały uruchomione, ale nie wykryły dodatkowych problemów wykraczających poza te zidentyfikowane przez własne reguły.

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
    -   **Ocena:** Jest to **false positive**. Wykryte wystąpienie znajduje się w linii 39 pliku `server/security.py` i stanowi awaryjną wartość domyślną używaną tylko wtedy, gdy zmienna środowiskowa `JWT_SECRET` nie jest ustawiona lub jest pusta. Jest to celowe zabezpieczenie dla środowiska deweloperskiego z wyraźnym ostrzeżeniem w logach (`logger.warning`). Kod prawidłowo ładuje sekret produkcyjny ze zmiennej środowiskowej `JWT_SECRET`, a wartość domyślna służy jedynie jako fallback z jasnym komunikatem dla dewelopera. W środowisku produkcyjnym zawsze należy ustawić zmienną środowiskową `JWT_SECRET`.

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
