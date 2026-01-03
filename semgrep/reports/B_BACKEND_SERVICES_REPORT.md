# BACKEND_SERVICES_B – raport Semgrep (SZABLON)
Autor: Jakub Gąsiorowski<br>
Data: 2025-12-04

## 1. Zakres analizy

- Katalogi:
  - `server/services/`
  - `server/database/`
- Pliki:
  - `server/scheduler.py`
  - `server/services/__init__.py`
  - `server/services/steam_service.py`
  - `server/services/deals_service.py`
  - `server/services/models.py`
  - `server/services/parse_html.py`
  - `server/services/_base_http.py`
  - `server/database/database.py`

Krótki opis:
- Ten fragment backendu odpowiada za komunikację z zewnętrznymi API (Steam, IsThereAnyDeal itp.), harmonogram zadań (scheduler) oraz dostęp do bazy danych. Z punktu widzenia bezpieczeństwa ważne są: poprawne obchodzenie się z danymi zewnętrznymi, timeouty, obsługa błędów i bezpieczne zapytania do bazy.

## 2. Konfiguracja Semgrepa

- Komenda bazowa:

  ```bash
  semgrep scan --config=./semgrep/rules_backend_services.yml server/services/ server/database/database.py server/scheduler.py
  ```

- Użyte rulesety:
  - `p/python`
  - `p/security-audit`
  - lokalne:
    - `semgrep/rules_backend_services.yml`

- Wersja Semgrepa:

  ```bash
  1.144.0
  ```


## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings z publicznych rulesetów (`p/python` + `p/security-audit`): 0
- Uwaga: W ramach tego raportu skupiono się na analizie własnych reguł (sekcja 4). Publiczne rulesety zostały uruchomione, ale nie wykryły dodatkowych problemów wykraczających poza te zidentyfikowane przez własne reguły.

---

## 4. Własne reguły Semgrep – `semgrep/rules_backend_services.yml`

Plik z regułami: `semgrep/rules_backend_services.yml`

### 4.1. Lista reguł

 - **ID:** `backend-services-http-require-timeout`
 - **Cel:**  
   Wymuszenie podawania `timeout` przy wywołaniach HTTP w usługach backendu.
 - **Pattern (skrót):**  
   `requests.get|post|put|delete|head|patch(...)` lub wywołania klienta HTTP bez argumentu `timeout=...`.
 - **Zakres działania:**  
   `server/services/**`, `server/services/_base_http.py`.

 - **ID:** `scheduler-empty-except-blocks`
 - **Cel:**  
   Zakaz pustych bloków `except` w zadaniach okresowych (scheduler).
 - **Pattern (skrót):**  
   `try: ... except Exception: pass` lub `try: ... except: ...` bez obsługi (brak logowania / brak reakcji).
 - **Zakres działania:**  
   `server/scheduler.py`, oraz miejsca w `server/services/**` wywoływane w kontekście zadań.

 - **ID:** `database-raw-sql-unparameterized`
 - **Cel:**  
   Wykrywanie nieparametryzowanych zapytań SQL (łączenie stringów, f-stringi, `.format`) w warstwie DB.
 - **Pattern (skrót):**  
   `cursor.execute($SQL)` gdzie `$SQL` powstaje przez konkatenację / f-string / `format`; dozwolone gdy użyto placeholderów (`?`, `%s`) z parametrami: `cursor.execute($SQL, $params)`.
 - **Zakres działania:**  
   `server/database/database.py`.


### 4.2. Efekty działania reguł

- Czy reguły złapały jakieś dopasowania?

   **Nie**

---

## 5. Wnioski dla obszaru backend (services/scheduler/database)

- Jakie problemy udało się zidentyfikować dzięki Semgrepowi?

  **Żadne**
- Czy pojawiły się false positives – jakie i dlaczego?

  **Nie**
- Jakie rekomendacje na przyszłość (np. "ustandaryzować klienta HTTP i pilnować go regułami Semgrepa", "dopilnować, żeby wszystkie zapytania do bazy były parametryzowane").

  **Kod jest super napisany, serio Szymon starałem się wspólnie z kolegą coś wymyślić**
