# FRONTEND_CLIENT_C – raport Semgrep (SZABLON)
Autor: [Imię i nazwisko]
Data: [RRRR-MM-DD]

## 1. Zakres analizy

- Katalogi:
  - `app/helpers/`
  - `app/core/services/`
- Pliki:
  - `app/helpers/api_client.py`
  - `app/helpers/signing.py`
  - `app/core/services/server_client.py`
  - `app/core/services/deals_client.py`
  - (opcjonalnie) wybrane pliki z `app/ui/`, jeśli używają bezpośrednio klienta HTTP.

Krótki opis:
- Ten fragment aplikacji to część klienta (GUI), odpowiedzialna za komunikację z backendem (HTTP), podpisywanie zapytań (HMAC / inne mechanizmy) oraz obsługę odpowiedzi. Istotne są tu: bezpieczeństwo (nie logowanie sekretów, poprawne użycie podpisów), sensowne timeouty, obsługa błędów.

## 2. Konfiguracja Semgrepa

- Komenda bazowa:

  ```bash
  semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/helpers/ app/core/services/
  ```

  Lub szybko tylko publiczne rulesets:

  ```bash
  semgrep scan --config=p/security-audit app/helpers/ app/core/services/
  ```

- Użyte rulesety:
  - `p/python` (publiczny ruleset dla Pythona z Semgrep Registry)
  - `p/security-audit` (publiczny ruleset dla bezpieczeństwa z Semgrep Registry)
  - lokalne:
    - `semgrep/rules_frontend_client.yml`

- Wersja Semgrepa: (podaj wersję z `semgrep --version`, np. `1.144.0`)

## 3. Wyniki z gotowych rulesetów

- Łączna liczba findings: X
- Kategorie (szacunkowo):
  - bezpieczeństwo: X1
  - poprawność: X2
  - styl / inne: X3

### 3.1. Najciekawsze przypadki (przykład 1)

1. **ID reguły:** `...`
2. **Plik i linia:** `app/helpers/api_client.py:NN`
3. **Opis Semgrepa (skrót):**
4. **Ocena:**
   - [ ] Prawdziwy problem
   - [ ] False positive / nieistotne
5. **Komentarz autora:**  
   (czy to faktycznie błąd, jak można go naprawić)

### 3.2. Najciekawsze przypadki (przykład 2)

*(analogicznie – minimum 2 przykłady)*

---

## 4. Własne reguły Semgrep – `semgrep/rules_frontend_client.yml`

Plik z regułami: `semgrep/rules_frontend_client.yml`

### 4.1. Lista reguł

Dla każdej reguły:

- **ID:** `...`
- **Cel:**  
  (np. "Wymuszenie ustawiania `timeout` przy wywołaniach HTTP po stronie klienta")
- **Pattern (skrót):**
- **Zakres działania:**  
  (np. tylko `app/helpers/` i `app/core/services/`).

Pomysły (do zaadaptowania):

- **ID:** `frontend-http-no-timeout`
  - **Cel:** Wykrywanie wywołań HTTP bez `timeout`.
  - **Zakres:** klient HTTP.

- **ID:** `frontend-no-secret-logging`
  - **Cel:** Zakaz logowania wartości podpisu / sekretów w logach (np. w `logger.debug`).

### 4.2. Efekty działania reguł

- Czy reguły coś znalazły?
- Jeśli tak – opisz przykłady:
  - plik, linia,
  - krótki opis,
  - decyzja, co z tym zrobić (poprawić kod? zmienić regułę?).

---

## 5. Wnioski dla obszaru frontend (klient HTTP / signing)

- Jakie problemy udało się zauważyć dzięki Semgrepowi?
- Czy były false positives? Jakie?
- Jakie masz rekomendacje na przyszłość (np. "centrala funkcja do tworzenia requestów + reguły pilnujące jej użycia", "przegląd loggingu pod kątem wrażliwych danych").
