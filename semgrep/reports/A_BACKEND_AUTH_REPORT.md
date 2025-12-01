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

- **ID:** `missing-api-authentication`
- **Cel:** Sprawdzenie, czy endpointy zdefiniowane pod ścieżką `/api/` używają zależności `require_session_and_signed_request` w celu zapewnienia, że są one prawidłowo zabezpieczone.
- **Pattern (skrót):** `@app.$METHOD("/api/...")` bez `fastapi.Depends(server.security.require_session_and_signed_request)`
- **Zakres działania:** `server/`

### 4.2. Efekty działania reguł

**Reguła: `hardcoded-jwt-secret`**

-   **Czy znaleziono dopasowania?** Tak, 1.
    -   **Plik i linia:** `server/security.py:39`
    -   **Opis:** W kodzie na stałe zaszyty jest domyślny sekret JWT: `"insecure-default-change-me"`.
    -   **Ocena:** Jest to **krytyczny, realny problem**. Użycie domyślnego, publicznie znanego sekretu w środowisku produkcyjnym całkowicie podważa bezpieczeństwo tokenów JWT. Atakujący może z łatwością fałszować tokeny, uzyskując nieautoryzowany dostęp do systemu. Należy natychmiastowo przenieść sekret do zmiennych środowiskowych.

**Reguła: `broad-exception-disclosure`**

-   **Czy znaleziono dopasowania?** Tak, 15.
    -   **Plik i linia:** `server/app.py` (wielokrotnie, m.in. w liniach 235, 257, 279, 299, 316, 327, 345, 378, 392, 404, 416, 519, 585, 637, 693).
    -   **Opis:** Wiele endpointów API łapie ogólny wyjątek `Exception as e` i zwraca jego treść (`str(e)`) bezpośrednio w odpowiedzi HTTP.
    -   **Ocena:** Jest to **realny problem** (CWE-209). Ujawnianie szczegółów błędów (np. ścieżek plików, zapytań SQL, nazw bibliotek) może dostarczyć atakującemu cennych informacji o wewnętrznej strukturze aplikacji, ułatwiając dalsze ataki. Poprawka polega na logowaniu szczegółowego błędu po stronie serwera i zwracaniu użytkownikowi ogólnego, nic niemówiącego komunikatu o błędzie.

**Reguła: `missing-api-authentication`**

-   **Czy znaleziono dopasowania?** Nie.
    -   **Opis:** Reguła nie znalazła żadnych dopasowań, ponieważ wystąpił błąd parsowania jej wzorca.
    -   **Ocena:** Błąd składni w definicji reguły uniemożliwił jej wykonanie. Wzorzec `def $FUNC(..., request: fastapi.Request, ...):` jest niepoprawny. Należy go poprawić, aby Semgrep mógł prawidłowo analizować kod w poszukiwaniu brakującego uwierzytelnienia. To pokazuje, jak ważne jest testowanie własnych reguł.

---

## 5. Wnioski dla obszaru backend (auth/security)

-   **Co Semgrep realnie pomógł znaleźć w tym obszarze?**
    Semgrep okazał się bardzo skuteczny w automatycznym wykrywaniu krytycznych i częstych błędów bezpieczeństwa. Zidentyfikował:
    1.  **Krytyczną lukę:** Użycie domyślnego, publicznie znanego sekretu JWT, co jest jednym z najpoważniejszych możliwych błędów w implementacji uwierzytelniania.
    2.  **Systemowy problem:** Wielokrotne przypadki potencjalnego wycieku informacji poprzez nieprawidłową obsługę wyjątków. Pokazuje to brak spójnego wzorca obsługi błędów w aplikacji.

-   **Jakie były ograniczenia?**
    Głównym ograniczeniem okazała się złożoność tworzenia poprawnych składniowo i logicznie reguł niestandardowych. Reguła `missing-api-authentication` nie zadziałała z powodu błędu w składni wzorca, co uniemożliwiło weryfikację zabezpieczenia endpointów. Podkreśla to konieczność dokładnego testowania własnych reguł przed wdrożeniem ich do procesu CI/CD.

-   **Rekomendacje:**
    1.  **Natychmiastowa refaktoryzacja zarządzania sekretami:** Sekret JWT musi być ładowany ze zmiennej środowiskowej lub innego bezpiecznego systemu zarządzania sekretami (np. HashiCorp Vault). Nigdy nie powinien znajdować się w kodzie źródłowym.
    2.  **Wprowadzenie centralnego mechanizmu obsługi wyjątków:** Należy zaimplementować w FastAPI middleware, który będzie przechwytywał wszystkie nieobsłużone wyjątki, logował ich pełną treść do wewnętrznego systemu monitoringu i zwracał klientowi ustandaryzowaną, ogólną odpowiedź o błędzie (np. `{"detail": "Internal Server Error"}`).
    3.  **Naprawa i rozwój reguł niestandardowych:** Należy poprawić składnię reguły `missing-api-authentication` i kontynuować rozbudowę zestawu reguł, aby automatycznie enforce'ować polityki bezpieczeństwa specyficzne dla tej aplikacji (np. walidacja uprawnień, kontrola dostępu do zasobów).
