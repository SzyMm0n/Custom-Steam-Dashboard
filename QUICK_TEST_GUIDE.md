# 🧪 System Testów Jednostkowych - Custom Steam Dashboard


## 📊 Status

**Faza 1 Zakończona!** 198 passed, 4 failed, 1 skipped

**Backend Coverage: 48%** | **Total Coverage: 15%**


---


## 🚀 Szybki Start


### 1. Instalacja zależności testowych


```bash
pip install -r requirements-test.txt
```


### 2. Uruchomienie testów


**Windows:**

```bash
run_tests.bat
```


**Linux/Mac:**

```bash
chmod +x run_tests.sh
./run_tests.sh
```


**Python (cross-platform):**

```bash
python run_tests.py
```


**Bezpośrednio pytest:**

```bash
pytest tests/ -v
```


---


## 📈 Uruchomienie z Coverage


### Podstawowy raport coverage:

```bash
pytest tests/ --cov=server --cov-report=term
```


### Coverage z raportem HTML:

```bash
pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term
```


Następnie otwórz: `htmlcov/index.html` w przeglądarce


### Coverage tylko dla backend:

```bash
pytest tests/ --cov=server --cov-report=term-missing
```


---


## 🎯 Uruchomienie Konkretnych Testów


### Tylko nowe testy (Faza 1):

```bash
pytest tests/test_database.py tests/test_deals_service.py tests/test_steam_service_extended.py tests/test_api_endpoints.py tests/test_scheduler.py -v
```


### Tylko testy backend services:

```bash
pytest tests/test_steam_service.py tests/test_deals_service.py tests/test_database.py -v
```


### Tylko testy security:

```bash
pytest tests/test_security.py tests/test_validation.py -v
```


### Testy z pattern matching:

```bash
pytest tests/ -k "database or scheduler" -v
pytest tests/ -k "steam" -v
pytest tests/ -k "not integration" -v
```


---


## 📋 Co zostało przetestowane?


### ✅ Komponenty z testami (Faza 1 Complete):


1. **Walidacja danych** (16 testów) - 54% coverage
   - Steam ID validation (ID64, vanity URL, profile URL)
   - App ID validation (range, format)


2. **Bezpieczeństwo** (12 testów) - 65% coverage
   - JWT token generation & verification
   - HMAC signature verification
   - Nonce management (anti-replay)


3. **Modele danych** (13 testów) - **100% coverage** ✅
   - SteamGameDetails, PlayerCountResponse
   - DealInfo, GamePrice


4. **Parsowanie HTML** (11 testów) - **100% coverage** ✅
   - Tag removal, entity decoding
   - Whitespace normalization


5. **Steam Service** (31 testów) - **82% coverage** ✅
   - Basic client (8 testów)
   - Extended API (23 testy):
     - Player owned games
     - Recently played games
     - Badges & achievements
     - Player summaries
     - Vanity URL resolution
     - Coming soon & most played games


6. **Database Operations** (25 testów) - 43% coverage
   - Connection management
   - Watchlist CRUD
   - Player count operations
   - Game details storage
   - Transactions


7. **Deals Service** (44 testy) - 35% coverage
   - ITAD API client
   - OAuth2 authentication
   - Best deals retrieval
   - Game price lookup
   - Deal search functionality


8. **API Endpoints** (49 testów) - 34% coverage
   - Root & health endpoints
   - Game endpoints
   - Watchlist management
   - Player count endpoints
   - Deals endpoints
   - Authentication
   - Rate limiting
   - Error handling


9. **Scheduler** (32 testy) - 37% coverage
   - Player count collection
   - Concurrent processing
   - Error handling
   - Job statistics
   - Semaphore control


---


## 📊 Statystyki Coverage


### Backend (Server) Coverage:

```
Module                          Coverage
----------------------------------------
models.py                         100% ✅
parse_html.py                     100% ✅
_base_http.py                      87% ✅
steam_service.py                   82% ✅
security.py                        65% ⚠️
validation.py                      54% ⚠️
middleware.py                      45% ⚠️
database.py                        43% ⚠️
auth_routes.py                     42% ⚠️
scheduler.py                       37% ⚠️
deals_service.py                   35% ⚠️
app.py                             34% ⚠️
----------------------------------------
TOTAL BACKEND                      48%
```


### Total (z UI):

```
TOTAL                              15%
```


**Dlaczego 15% total?**

- Backend (32% kodu): **48% pokryte** ✅
- Frontend/UI (68% kodu): **0% pokryte** ❌


---


## ⚡ Quick Commands


### Najczęściej używane:


```bash
# Szybkie testy (wszystkie):
pytest tests/ -v

# Z pokryciem:
pytest tests/ --cov=server --cov-report=html

# Tylko passing tests:
pytest tests/ -v --tb=no

# Z timerem:
pytest tests/ -v --durations=10

# Parallel execution (faster):
pytest tests/ -n auto

# Stop at first failure:
pytest tests/ -x

# Tylko failed z ostatniego uruchomienia:
pytest tests/ --lf

# Verbose z output:
pytest tests/ -v -s
```


---


## 🔧 Troubleshooting


### Problem: Testy trwają zbyt długo

```bash
# Użyj parallel execution:
pip install pytest-xdist
pytest tests/ -n auto
```


### Problem: Brak modułu

```bash
# Reinstall dependencies:
pip install -r requirements-test.txt
```


### Problem: Database connection errors

```bash
# Testy używają mocków, nie wymagają prawdziwej bazy
# Sprawdź czy asyncpg jest zainstalowany:
pip install asyncpg
```


### Problem: Coverage nie generuje raportu

```bash
# Sprawdź instalację:
pip install pytest-cov

# Uruchom ponownie:
pytest tests/ --cov=server --cov-report=html
```


---


## 📚 Dokumentacja


- **Pełny raport:** `TEST_REPORT.md`
- **Coverage HTML:** `htmlcov/index.html`  
- **Pytest docs:** https://docs.pytest.org
- **Coverage docs:** https://coverage.readthedocs.io


---


## 🏆 Osiągnięcia


### Metryki Sukcesu:


| Metryka | Start | Teraz | Wzrost |
|---------|-------|-------|--------|
| Testy | 63 | **203** | +140 🎉 |
| Backend Coverage | ~20% | **48%** | +28% 📈 |
| Total Coverage | 10% | **15%** | +5% |
| Passing Rate | 98% | **97.5%** | ✅ |
| Moduły >80% | 2 | **5** | +3 🚀 |
