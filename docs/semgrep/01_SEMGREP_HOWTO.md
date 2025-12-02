# SEMGREP_HOWTO – jak uruchamiać Semgrep w projekcie

## 1. Struktura plików dla Semgrepa

W katalogu głównym repozytorium zakładamy:

```text
Custom-Steam-Dashboard/
  semgrep/
    rules_backend_auth.yml
    rules_backend_services.yml
    rules_frontend_client.yml
    # opcjonalnie:
    # rules_common.yml
  .semgrep.yml
```

- `.semgrep.yml` – główna konfiguracja, z której wszyscy korzystamy.
- `semgrep/*.yml` – nasze własne reguły dla poszczególnych obszarów.

---

## 2. Zawartość `.semgrep.yml`

```yaml
# .semgrep.yml
# Główny plik konfiguracji – puste reguły
# Konkretne reguły będą ładowane z flagami --config w linii poleceń

rules: []

# Uwaga: to jest strukturą bazową. Reguły ładujemy za pośrednictwem flag --config
```

> **Ważne:** W Semgrepie 1.x reguły są ładowane za pośrednictwem **flag `--config`** w linii poleceń, a nie z pliku `.semgrep.yml`.
> Nazwy `p/python`, `p/security-audit` to publiczne pakiety reguł z Semgrep Registry.
> Każdy plik z lokalnymi regułami musi zawierać `rules: [...]` na górnym poziomie YAML.

---

## 3. Standardowe komendy skanowania

### 3.1. Backend – Osoby A i B

Pełny skan backendu (z publicznych rulesetów i własnymi regułami):

```bash
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml --config=semgrep/rules_backend_services.yml server/
```

Jeśli chcesz tylko publiczne rulesets:

```bash
semgrep scan --config=p/python --config=p/security-audit server/
```

Wstępny, zawężony skan (np. tylko auth z publicznych rulesetów):

```bash
semgrep scan --config=p/security-audit server/app.py server/auth_routes.py server/security.py
```

### 3.2. Frontend – Osoba C

Skan klienta i helperów:

```bash
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/helpers/ app/core/services/
```

Można też skanować całe `app/`:

```bash
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/
```

---

## 4. Jak czytać wyniki

Po uruchomieniu komendy w terminalu pojawią się wpisy podobne do:

```text
server/security.py:42: warning: <id_reguły>
  opis problemu wygenerowany przez Semgrep
```

Dla każdego wyniku w raporcie warto zanotować:

1. ID reguły
2. Plik i linia
3. Krótki opis (co Semgrep zgadza)
4. Czy to:
   - realny problem,
   - false positive,
   - kwestia stylu / estetyki.

Najciekawsze przypadki (2–3) opisujemy dokładniej w indywidualnym `.md`.

---

## 5. Jak dopisywać własne reguły

### 5.1. Gdzie dopisywać?

- Osoba A – plik: `semgrep/rules_backend_auth.yml`
- Osoba B – plik: `semgrep/rules_backend_services.yml`
- Osoba C – plik: `semgrep/rules_frontend_client.yml`

**Każdy plik musi zawierać `rules: [...]` na górnym poziomie YAML.**

### 5.2. Minimalny szkielet reguły

```yaml
# semgrep/rules_backend_auth.yml
rules:
  - id: example-rule-id
    message: Krótki opis, co jest problemem i dlaczego
    severity: WARNING  # INFO / WARNING / ERROR
    languages: [python]
    patterns:
      - pattern: |
          print($X)
    paths:
      include:
        - server/
```

**Ważne elementy:**

- `id` – unikalny identyfikator reguły w projekcie (zamiast kropek używaj myślników: `backend-auth-no-empty-except`),
- `message` – opis, który użytkownik zobaczy w wyniku skanu,
- `severity` – poziom istotności (`INFO` / `WARNING` / `ERROR`),
- `languages` – w naszym projekcie zawsze `[python]`,
- `patterns` / `pattern` / `pattern-either` – wzorce kodu, jakie chcemy wykryć,
- `paths` – można ograniczyć regułę tylko do części repo (np. tylko `server/` albo tylko `app/`).

**Jak zainkludować nową regułę w skanowaniu:**

Po dodaniu reguły do pliku (np. `semgrep/rules_backend_auth.yml`), musisz ją podać w flagach `--config`:

```bash
semgrep scan --config=p/python --config=semgrep/rules_backend_auth.yml server/
```

---

## 6. Standard używania Semgrepa w projekcie

1. **Nie edytujemy `.semgrep.yml` bez uzgodnienia z koordynatorem (Osoba D).** (Zwykle to plik pusty, główne komendy definiujemy w CLI)
2. **Własne reguły** dopisujemy tylko we właściwych plikach (`semgrep/rules_backend_*`, `semgrep/rules_frontend_*`).  
3. Każdy plik z regułami musi zawierać `rules: [...]` na górnym poziomie YAML.
4. Przed zrobieniem PR/merge:
   - uruchamiamy odpowiedni skan:
     - backend: `semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml --config=semgrep/rules_backend_services.yml server/`
     - frontend: `semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/`
5. Wyniki, które wykorzystamy w raporcie, przenosimy do swojego pliku `.md` (wg szablonu).

---

## 7. Instalacja i przygotowanie (szczegółowo)

### 7.1. Warunki wstępne

- Python 3.8+
- Git (do klonowania repozytorium)
- Dostęp do terminala / wiersza poleceń

### 7.2. Kroki instalacji

**Krok 1: Klonowanie repozytorium**

```bash
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard
```

**Krok 2: Instalacja Semgrepa**

Na systemach Linux/macOS:

```bash
pip install semgrep
```

Lub używając Homebrew (macOS):

```bash
brew install semgrep
```

Na Windows (via pip):

```bash
pip install semgrep
```

**Krok 3: Weryfikacja instalacji**

```bash
semgrep --version
```

Powinna pojawić się wersja, np. `1.144.0` lub nowsza.

**Uwaga:** Ten projekt został przetestowany z Semgrep w wersji `1.144.0`. Jeśli używasz starszej lub nowszej wersji, niektóre opcje lub składnia mogą się różnić.

### 7.3. Opcjonalnie: środowisko wirtualne

Aby nie zanieczyszczać globalnego środowiska Python:

```bash
# Utworzenie
python -m venv .venv

# Aktywacja (Linux/macOS)
source .venv/bin/activate

# Aktywacja (Windows)
.\.venv\Scripts\activate

# Instalacja Semgrepa w venv
pip install semgrep
```

---

## 8. Uruchamianie skanów – praktyczne przykłady

### 8.1. Skan pełny (całe repozytorium)

```bash
semgrep scan --config=p/python --config=p/security-audit
```

### 8.2. Skan backendu (Backend Team – Osoby A & B)

```bash
# Pełny skan backendu ze wszystkimi regułami
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml --config=semgrep/rules_backend_services.yml server/

# Lub tylko publiczne rulesets (szybciej)
semgrep scan --config=p/python --config=p/security-audit server/

# Lub bardziej zawężony (tylko auth)
semgrep scan --config=p/security-audit server/app.py server/auth_routes.py server/security.py
```

### 8.3. Skan frontendu (Frontend Team – Osoba C)

```bash
# Skan klienta z własnymi regułami
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/helpers/ app/core/services/

# Lub całe `app/` (będzie więcej wyników)
semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/
```

### 8.4. Eksportowanie wyników do pliku

```bash
# JSON
semgrep scan --config=p/python --config=p/security-audit --json > results.json

# SARIF
semgrep scan --config=p/python --config=p/security-audit --sarif > results.sarif

# Tekst (domyślnie)
semgrep scan --config=p/python --config=p/security-audit > results.txt
```

---

## 9. Troubleshooting – rozwiązywanie problemów

### 9.1. Błąd: "Config not found" lub "Invalid rule schema"

**Przyczyna:** Plik z regułami (np. `semgrep/rules_backend_auth.yml`) nie istnieje, lub ma niepoprawny format.

**Rozwiązanie:**

1. Sprawdź, czy plik istnieje:
   ```bash
   ls -la semgrep/rules_backend_auth.yml
   ```

2. Sprawdź format – plik **musi** zawierać `rules:` na górnym poziomie:
   ```bash
   head -1 semgrep/rules_backend_auth.yml
   # Powinno być: rules:
   ```

3. Jeśli plik jest pusty, dodaj minimalną strukturę:
   ```yaml
   rules: []
   ```

### 9.2. Błąd: "semgrep: command not found"

**Przyczyna:** Semgrep nie jest zainstalowany lub nie jest w PATH.

**Rozwiązanie:**

```bash
# Ponowna instalacja
pip install semgrep --upgrade

# Lub sprawdzenie, czy jest zainstalowany
pip show semgrep
```

### 9.3. Brak wyników (zero findings)

**Przyczyna:** Kod może być czysty, lub używasz zbyt wąskich reguł.

**Rozwiązanie:**

1. Spróbuj skanować z publicznym rulesetem (bez lokalnych reguł):
   ```bash
   semgrep scan --config=p/security-audit server/
   ```

2. Lub dodaj flagę `-v` (verbose) aby zobaczyć co się dzieje:
   ```bash
   semgrep scan --config=p/python -v server/
   ```

3. Sprawdź konkretne pliki:
   ```bash
   semgrep scan --config=p/security-audit server/app.py
   ```

### 9.4. Błąd: "Empty rules in config file"

**Przyczyna:** Plik z regułami zawiera `rules: []` lub reguły są źle sformatowane.

**Rozwiązanie:**

1. Jeśli plik ma być pusty (właściwy dla lokalnych reguł, które nie zostały jeszcze napisane) – to jest w porządku.
2. Jeśli chcesz dodać reguły, zapoznaj się z sekcją "5. Jak dopisywać własne reguły".

---

## 10. Zaawansowane opcje

### 10.1. Filtrowanie wyników po wadze (severity)

Tylko ostrzeżenia i błędy (bez info):

```bash
semgrep scan --config=p/python --config=p/security-audit --min-severity=WARNING server/
```

### 10.2. Zapamiętywanie wyników dla porównania

Przy rozwijaniu reguł może być przydatne porównanie wyników "wcześniej" vs "teraz":

```bash
# Zapis baseline'u
semgrep scan --config=p/python --config=p/security-audit --json > baseline.json

# Później po zmianach:
semgrep scan --config=p/python --config=p/security-audit --json > current.json

# Porównanie (ręczne lub narzędziem - np. diff)
diff baseline.json current.json
```

### 10.3. Pomoc w Semgrepie

```bash
semgrep --help
semgrep scan --help

# Lub szybka dokumentacja online:
# https://semgrep.dev/docs/running-rules/
```

### 10.4. Szybka komenda "gotowa do użytku"

Jeśli chcesz mieć szybko dostępne komendy, można stworzyć aliasy w `.bashrc` lub `.zshrc`:

```bash
# Dodaj do ~/.bashrc lub ~/.zshrc:
alias semgrep-backend='semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_backend_auth.yml --config=semgrep/rules_backend_services.yml server/'
alias semgrep-frontend='semgrep scan --config=p/python --config=p/security-audit --config=semgrep/rules_frontend_client.yml app/'

# Potem możesz uruchomić po prostu:
semgrep-backend
semgrep-frontend
```

