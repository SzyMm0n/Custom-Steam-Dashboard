# ?? Testy Jednostkowe - Custom Steam Dashboard

## Spis Treści
- [Przegląd](#przegląd)
- [Struktura Testów](#struktura-testów)
- [Instalacja](#instalacja)
- [Uruchamianie Testów](#uruchamianie-testów)
- [Pokrycie Kodu](#pokrycie-kodu)
- [Typy Testów](#typy-testów)

---

## Przegląd

Projekt zawiera kompleksowy zestaw testów jednostkowych i integracyjnych dla aplikacji Custom Steam Dashboard. Testy pokrywają następujące obszary:

- **Walidacja danych** - testy dla modeli Pydantic
- **Bezpieczeństwo** - testy JWT i HMAC signature
- **Modele danych** - testy wszystkich modeli Steam i Deals
- **Parsowanie HTML** - testy utility do czyszczenia HTML
- **Serwis Steam** - testy (z mockami) dla Steam API
- **Integracja API** - podstawowe testy endpointów FastAPI

---

## Struktura Testów

```
tests/
├── __init__.py              # Inicjalizacja pakietu testów
├── conftest.py              # Konfiguracja pytest i fixture'y
├── test_validation.py       # Testy walidacji (Steam ID, App ID)
├── test_security.py         # Testy JWT, HMAC, nonce
├── test_models.py           # Testy modeli Pydantic
├── test_parse_html.py       # Testy parsowania HTML
├── test_steam_service.py    # Testy Steam Client (mock)
└── test_api_integration.py  # Testy integracyjne API
```

---

## Instalacja

### 1. Zainstaluj zależności testowe

```bash
pip install -r requirements-test.txt
```

Lub zainstaluj wymagane pakiety ręcznie:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 2. Opcjonalnie - narzędzia do jakości kodu

```bash
pip install ruff mypy
```

---

## Uruchamianie Testów

### Uruchom wszystkie testy

```bash
pytest
```

### Uruchom z verbose output

```bash
pytest -v
```

### Uruchom konkretny plik testowy

```bash
pytest tests/test_validation.py
```

### Uruchom konkretną klasę testową

```bash
pytest tests/test_validation.py::TestSteamIDValidator
```

### Uruchom konkretny test

```bash
pytest tests/test_validation.py::TestSteamIDValidator::test_valid_steam_id64
```

### Uruchom tylko testy jednostkowe

```bash
pytest -m unit
```

### Uruchom tylko testy integracyjne

```bash
pytest -m integration
```

### Uruchom testy z pominięciem wolnych testów

```bash
pytest -m "not slow"
```

---

## Pokrycie Kodu

### Uruchom testy z raportem pokrycia

```bash
pytest --cov=server --cov=app --cov-report=html --cov-report=term-missing
```

### Zobacz raport w przeglądarce

Po uruchomieniu testów z opcją `--cov-report=html`, otwórz:

```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

### Wygeneruj raport w formacie XML (dla CI/CD)

```bash
pytest --cov=server --cov=app --cov-report=xml
```

---

## Typy Testów

### 1. **Testy Walidacji** (`test_validation.py`)

Testują walidację danych wejściowych:
- Steam ID (ID64, vanity URL, profile URL)
- App ID (zakres, format)

```python
# Przykład uruchomienia
pytest tests/test_validation.py -v
```

### 2. **Testy Bezpieczeństwa** (`test_security.py`)

Testują mechanizmy bezpieczeństwa:
- Generowanie i weryfikacja JWT
- HMAC signature verification
- Zarządzanie nonce

```python
# Przykład uruchomienia
pytest tests/test_security.py -v
```

### 3. **Testy Modeli** (`test_models.py`)

Testują modele danych Pydantic:
- `SteamGameDetails`
- `PlayerCountResponse`
- `DealInfo`
- `GamePrice`

```python
# Przykład uruchomienia
pytest tests/test_models.py -v
```

### 4. **Testy Parsowania HTML** (`test_parse_html.py`)

Testują funkcję czyszczenia HTML:
- Usuwanie tagów HTML
- Dekodowanie encji HTML
- Normalizacja białych znaków

```python
# Przykład uruchomienia
pytest tests/test_parse_html.py -v
```

### 5. **Testy Serwisu Steam** (`test_steam_service.py`)

Testują Steam Client z mockami:
- Pobieranie liczby graczy
- Pobieranie szczegółów gier
- Konfiguracja timeout

```python
# Przykład uruchomienia
pytest tests/test_steam_service.py -v
```

### 6. **Testy Integracyjne API** (`test_api_integration.py`)

Testują endpointy FastAPI:
- Health check
- Endpointy autoryzacji

```python
# Przykład uruchomienia
pytest tests/test_api_integration.py -m integration -v
```

---

## Konfiguracja

### pytest.ini

Podstawowa konfiguracja pytest znajduje się w pliku `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### pyproject.toml

Zaawansowana konfiguracja (jeśli używasz):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--verbose", "--cov=server", "--cov=app"]
```

---

## Continuous Integration

### Przykład dla GitHub Actions

Utwórz plik `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=server --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Problem: `ModuleNotFoundError`

**Rozwiązanie**: Upewnij się, że ścieżka projektu jest w PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest
```

Lub w Windows:

```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)"
pytest
```

### Problem: Testy asynchroniczne nie działają

**Rozwiązanie**: Zainstaluj `pytest-asyncio`:

```bash
pip install pytest-asyncio
```

### Problem: Import errors dla zmiennych środowiskowych

**Rozwiązanie**: Ustaw zmienne środowiskowe przed uruchomieniem testów lub upewnij się, że `conftest.py` je ustawia.

---

## Dodawanie Nowych Testów

### 1. Utwórz nowy plik testowy

```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_something(self):
        assert True
```

### 2. Użyj fixtures z conftest.py

```python
def test_with_fixture(event_loop):
    # Użyj fixture event_loop
    pass
```

### 3. Dodaj markery dla kategoryzacji

```python
@pytest.mark.unit
def test_unit_feature():
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_slow_integration():
    pass
```

---

## Dodatkowe Zasoby

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Checklist przed Commitem

- [ ] Wszystkie testy przechodzą: `pytest`
- [ ] Pokrycie kodu > 80%: `pytest --cov`
- [ ] Kod sformatowany: `ruff format .`
- [ ] Brak błędów lintingu: `ruff check .`
- [ ] Type checking OK: `mypy server/ app/`

---

## Wkład w Testy

Aby dodać nowe testy:

1. Zidentyfikuj nieprzetestowany kod
2. Utwórz odpowiedni plik testowy w `tests/`
3. Napisz testy zgodnie z konwencją `test_*`
4. Uruchom testy: `pytest`
5. Sprawdź pokrycie: `pytest --cov`
6. Utwórz Pull Request

---

## Licencja

Testy są częścią projektu Custom Steam Dashboard i objęte tą samą licencją MIT.
