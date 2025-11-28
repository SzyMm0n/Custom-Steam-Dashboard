# COORDINATOR_D – zadania + raport zbiorczy (SZABLON)
Autor: [Imię i nazwisko]
Data: [RRRR-MM-DD]

## 1. Rola koordynatora

Koordynator (Osoba D) odpowiada za:

- przygotowanie konfiguracji Semgrepa (`.semgrep.yml`, katalog `semgrep/`),
- ustalenie standardu uruchamiania skanów,
- przygotowanie szablonów raportów dla wszystkich,
- integrację Semgrepa z pipeline CI (np. GitHub Actions),
- zebranie indywidualnych raportów i stworzenie raportu zbiorczego,
- przygotowanie prezentacji na zajęcia.

---

## 2. Zadania koordynatora – szczegółowo

### 2.1. Konfiguracja Semgrepa

- Utworzenie pliku `.semgrep.yml` z:
  - konfiguracją rulesetów `p/python`, `p/security-audit`,
  - podpiętymi plikami z własnymi regułami (`semgrep/rules_backend_auth.yml`, `semgrep/rules_backend_services.yml`, `semgrep/rules_frontend_client.yml`).
- Utworzenie katalogu `semgrep/` z pustymi lub częściowo wypełnionymi plikami reguł.

### 2.2. Standard uruchamiania skanów

- Opisanie w `SEMGREP_HOWTO.md`:
  - dokładnych komend dla backendu i frontendu,
  - podstawowego workflow: zainstaluj → uruchom skan → wybierz najciekawsze wyniki → opisz w `.md`.

### 2.3. Szablony raportów `.md`

- Stworzenie plików (szablonów):
  - `BACKEND_AUTH_A.md`
  - `BACKEND_SERVICES_B.md`
  - `FRONTEND_CLIENT_C.md`
  - niniejszego pliku `COORDINATOR_D...`

Szablony powinny zawierać:
- sekcje o zakresie analizy,
- sekcję o konfiguracji Semgrepa,
- opis najciekawszych wyników,
- sekcję o własnych regułach,
- wnioski.

### 2.4. Pipeline / CI

- Przygotowanie pliku `.github/workflows/semgrep.yml`, np.:

  ```yaml
  name: Semgrep

  on:
    pull_request:
    push:
      branches: [ main ]

  jobs:
    semgrep:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'

        - name: Install Semgrep
          run: pip install semgrep

        - name: Run Semgrep (server + app)
          run: |
            semgrep scan --config=.semgrep.yml server/ app/
  ```

- Opcjonalnie: ustawienie, aby krytyczne błędy powodowały fail joba.

### 2.5. Komunikacja i integracja wyników

- Ustalenie kanału komunikacji (issue / Discord / Teams).
- Zebranie od A/B/C:
  - wypełnionych plików `.md`,
  - ewentualnych logów / screenów,
- Ujednolicenie formatowania (nagłówki, code-blocki, język).

---

## 3. Raport zbiorczy – `SUMMARY_D.md` (SZABLON)

Poniżej szkielet raportu końcowego, który koordynator może wypełnić na podstawie indywidualnych raportów.

### 3.1. Wprowadzenie

- Krótki opis aplikacji (Custom-Steam-Dashboard, architektura client–server, Python).
- Krótki opis Semgrepa (SAST, reguły, dlaczego pasuje do Pythona i do naszego projektu).
- Cel projektu (jak w `00_SEMGREP_PROJECT_INTRO.md`).

### 3.2. Konfiguracja Semgrepa

- Podsumowanie:
  - jakie rulesety wykorzystaliśmy (p/python, p/security-audit, nasze reguły),
  - jak wygląda struktura `.semgrep.yml`,
  - jak podzieliliśmy pliki reguł na obszary projektu.

### 3.3. Zakres analizy

- Backend – auth/security (Osoba A):
  - pliki, za które odpowiadała,
  - 2–3 najważniejsze wnioski.
- Backend – services/scheduler/db (Osoba B):
  - pliki / obszary,
  - 2–3 najważniejsze wnioski.
- Frontend – klient HTTP / signing (Osoba C):
  - pliki / obszary,
  - 2–3 najważniejsze wnioski.

### 3.4. Najciekawsze znalezione problemy

- Lista 3–5 najciekawszych przypadków z całego projektu (wybrane z raportów A/B/C), każdy w formie:

  - **Obszar:** backend-auth / backend-services / frontend
  - **Plik i linia:** `...`
  - **ID reguły:** `...`
  - **Krótki opis:** co Semgrep zgłosił
  - **Nasza decyzja:** realny błąd / false positive
  - **Ewentualna poprawka:** opis lub fragment kodu po poprawie

### 3.5. Własne reguły – podsumowanie

- Ile własnych reguł powstało,
- Jakie główne cele miały te reguły (timeouty, logowanie sekretów, puste excepty, itp.),
- Czy znalazły realne problemy, czy były raczej zabezpieczeniem na przyszłość.

### 3.6. Integracja z pipeline / CI

- Jak wygląda nasz workflow z Semgrepem w GitHub Actions,
- Jak można by go rozszerzyć (np. różne progi severity, osobne joby dla backendu i frontendu).

### 3.7. Wnioski końcowe

- Co Semgrep wniósł do projektu?
- Jak oceniamy stosunek wysiłek → korzyść?
- Jakie mamy rekomendacje na przyszłość:
  - dla dalszego rozwoju tej konkretnej aplikacji,
  - dla ogólnego użycia Semgrepa w innych projektach.

---

## 4. Notatki końcowe dla koordynatora

- Pilnuj, żeby `.semgrep.yml` i pliki w `semgrep/` były spójne (ID reguł, ścieżki, itp.).
- Przed zebraniem raportów poproś każdego o:
  - uruchomienie skanu,
  - wybranie max. 2–3 najciekawszych przypadków,
  - opisanie min. 1 własnej reguły, która faktycznie *coś* sprawdza.
- W prezentacji warto pokazać:
  - ogólny schemat architektury aplikacji,
  - jak Semgrep wpięliśmy w projekt,
  - 2–3 konkretne case'y “przed/po” (kod przed poprawką i po niej).
