# ?? Testy Jednostkowe - Custom Steam Dashboard

## ?? Spis Tre?ci
- [Przegl?d](#przegl?d)
- [Struktura Testów](#struktura-testów)
- [Instalacja](#instalacja)
- [Uruchamianie Testów](#uruchamianie-testów)
- [Pokrycie Kodu](#pokrycie-kodu)
- [Typy Testów](#typy-testów)

---

## ?? Przegl?d

Projekt zawiera kompleksowy zestaw testów jednostkowych i integracyjnych dla aplikacji Custom Steam Dashboard. Testy pokrywaj? nast?puj?ce obszary:

- ? **Walidacja danych** - testy dla modeli Pydantic
- ? **Bezpiecze?stwo** - testy JWT i HMAC signature
- ? **Modele danych** - testy wszystkich modeli Steam i Deals
- ? **Parsowanie HTML** - testy utility do czyszczenia HTML
- ? **Serwis Steam** - testy (z mockami) dla Steam API
- ? **Integracja API** - podstawowe testy endpointów FastAPI

---

## ?? Struktura Testów

```
tests/
??? __init__.py              # Inicjalizacja pakietu testów
??? conftest.py              # Konfiguracja pytest i fixture'y
??? test_validation.py       # Testy walidacji (Steam ID, App ID)
??? test_security.py         # Testy JWT, HMAC, nonce
??? test_models.py           # Testy modeli Pydantic
??? test_parse_html.py       # Testy parsowania HTML
??? test_steam_service.py    # Testy Steam Client (mock)
??? test_api_integration.py  # Testy integracyjne API
```

---

## ?? Instalacja

### 1. Zainstaluj zale?no?ci testowe

```bash
pip install -r requirements-test.txt
```

Lub zainstaluj wymagane pakiety r?cznie:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 2. Opcjonalnie - narz?dzia do jako?ci kodu

```bash
pip install ruff mypy
```

---

## ?? Uruchamianie Testów

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

### Uruchom konkretn? klas? testow?

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

### Uruchom testy z pomini?ciem wolnych testów

```bash
pytest -m "not slow"
```

---

## ?? Pokrycie Kodu

### Uruchom testy z raportem pokrycia

```bash
pytest --cov=server --cov=app --cov-report=html --cov-report=term-missing
```

### Zobacz raport w przegl?darce

Po uruchomieniu testów z opcj? `--cov-report=html`, otwórz:

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

## ?? Typy Testów

### 1. **Testy Walidacji** (`test_validation.py`)

Testuj? walidacj? danych wej?ciowych:
- Steam ID (ID64, vanity URL, profile URL)
- App ID (zakres, format)

```python
# Przyk?ad uruchomienia
pytest tests/test_validation.py -v
```

### 2. **Testy Bezpiecze?stwa** (`test_security.py`)

Testuj? mechanizmy bezpiecze?stwa:
- Generowanie i weryfikacja JWT
- HMAC signature verification
- Zarz?dzanie nonce

```python
# Przyk?ad uruchomienia
pytest tests/test_security.py -v
```

### 3. **Testy Modeli** (`test_models.py`)

Testuj? modele danych Pydantic:
- `SteamGameDetails`
- `PlayerCountResponse`
- `DealInfo`
- `GamePrice`

```python
# Przyk?ad uruchomienia
pytest tests/test_models.py -v
```

### 4. **Testy Parsowania HTML** (`test_parse_html.py`)

Testuj? funkcj? czyszczenia HTML:
- Usuwanie tagów HTML
- Dekodowanie encji HTML
- Normalizacja bia?ych znaków

```python
# Przyk?ad uruchomienia
pytest tests/test_parse_html.py -v
```

### 5. **Testy Serwisu Steam** (`test_steam_service.py`)

Testuj? Steam Client z mockami:
- Pobieranie liczby graczy
- Pobieranie szczegó?ów gier
- Konfiguracja timeout

```python
# Przyk?ad uruchomienia
pytest tests/test_steam_service.py -v
```

### 6. **Testy Integracyjne API** (`test_api_integration.py`)

Testuj? endpointy FastAPI:
- Health check
- Endpointy autoryzacji

```python
# Przyk?ad uruchomienia
pytest tests/test_api_integration.py -m integration -v
```

---

## ?? Konfiguracja

### pytest.ini

Podstawowa konfiguracja pytest znajduje si? w pliku `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### pyproject.toml

Zaawansowana konfiguracja (je?li u?ywasz):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--verbose", "--cov=server", "--cov=app"]
```

---

## ?? Continuous Integration

### Przyk?ad dla GitHub Actions

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

## ?? Troubleshooting

### Problem: `ModuleNotFoundError`

**Rozwi?zanie**: Upewnij si?, ?e ?cie?ka projektu jest w PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest
```

Lub w Windows:

```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)"
pytest
```

### Problem: Testy asynchroniczne nie dzia?aj?

**Rozwi?zanie**: Zainstaluj `pytest-asyncio`:

```bash
pip install pytest-asyncio
```

### Problem: Import errors dla zmiennych ?rodowiskowych

**Rozwi?zanie**: Ustaw zmienne ?rodowiskowe przed uruchomieniem testów lub upewnij si?, ?e `conftest.py` je ustawia.

---

## ?? Dodawanie Nowych Testów

### 1. Utwórz nowy plik testowy

```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_something(self):
        assert True
```

### 2. U?yj fixtures z conftest.py

```python
def test_with_fixture(event_loop):
    # U?yj fixture event_loop
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

## ?? Dodatkowe Zasoby

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## ? Checklist przed Commitem

- [ ] Wszystkie testy przechodz?: `pytest`
- [ ] Pokrycie kodu > 80%: `pytest --cov`
- [ ] Kod sformatowany: `ruff format .`
- [ ] Brak b??dów lintingu: `ruff check .`
- [ ] Type checking OK: `mypy server/ app/`

---

## ?? Wk?ad w Testy

Aby doda? nowe testy:

1. Zidentyfikuj nieprzetestowany kod
2. Utwórz odpowiedni plik testowy w `tests/`
3. Napisz testy zgodnie z konwencj? `test_*`
4. Uruchom testy: `pytest`
5. Sprawd? pokrycie: `pytest --cov`
6. Utwórz Pull Request

---

## ?? Licencja

Testy s? cz??ci? projektu Custom Steam Dashboard i obj?te t? sam? licencj? MIT.
