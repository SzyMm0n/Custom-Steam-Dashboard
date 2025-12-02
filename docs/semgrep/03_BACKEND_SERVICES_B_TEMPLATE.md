# BACKEND_SERVICES_B – raport Semgrep (SZABLON)
Autor: [Imię i nazwisko]
Data: [RRRR-MM-DD]

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
  semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_services.yml server/services/ server/database/database.py server/scheduler.py
  ```

  Lub szybko tylko publiczne rulesets:

  ```bash
  semgrep scan --config=p/security-audit server/services/ server/database/database.py server/scheduler.py
  ```

- Użyte rulesety:
  - `p/python` (publiczny ruleset dla Pythona z Semgrep Registry)
  - `p/security-audit` (publiczny ruleset dla bezpieczeństwa z Semgrep Registry)
  - lokalne:
    - `semgrep/rules_backend_services.yml`

- Wersja Semgrepa: (podaj wersję z `semgrep --version`, np. `1.144.0`)

## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings: X
- Kategorie (szacunkowo):
  - bezpieczeństwo: X1
  - poprawność: X2
  - styl / inne: X3

### 3.1. Najciekawsze przypadki (przykład 1)

1. **ID reguły:** `...`
2. **Plik i linia:** `server/services/steam_service.py:NN`
3. **Opis Semgrepa (skrót):**
4. **Ocena:**
   - [ ] Prawdziwy problem
   - [ ] False positive / nieistotne
5. **Komentarz autora:**  
   (czemu to problem / nie problem, propozycja poprawki)

### 3.2. Najciekawsze przypadki (przykład 2)

*(analogicznie – minimum 2 przykłady)*

---

## 4. Własne reguły Semgrep – `semgrep/rules_backend_services.yml`

Plik z regułami: `semgrep/rules_backend_services.yml`

### 4.1. Lista reguł

Dla każdej reguły:

- **ID:** `...`
- **Cel:**  
  (np. "Wymuszenie podawania `timeout` przy wywołaniach HTTP w usługach backendu")
- **Pattern (skrót):**
- **Zakres działania:**  
  (np. tylko pliki w `server/services/`).

Pomysły (do zaadaptowania):

- **ID:** `backend-services-http-no-timeout`
  - **Cel:** Zapobieganie wywołaniom HTTP bez `timeout=...`.
  - **Zakres:** `server/services/`, `_base_http.py`.

- **ID:** `backend-scheduler-no-empty-except`
  - **Cel:** Zakaz pustych bloków `except` w zadaniach okresowych.

### 4.2. Efekty działania reguł

- Czy reguły złapały jakieś dopasowania?
- Dla każdego dopasowania podaj:
  - plik, linia,
  - krótki opis,
  - ocena, czy faktycznie trzeba coś poprawić, czy reguła jest zbyt agresywna.

---

## 5. Wnioski dla obszaru backend (services/scheduler/database)

- Jakie problemy udało się zidentyfikować dzięki Semgrepowi?
- Czy pojawiły się false positives – jakie i dlaczego?
- Jakie rekomendacje na przyszłość (np. "ustandaryzować klienta HTTP i pilnować go regułami Semgrepa", "dopilnować, żeby wszystkie zapytania do bazy były parametryzowane").
