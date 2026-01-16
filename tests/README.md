# 🧪 Testy - README

**Custom Steam Dashboard** - System testowy

---

## 📋 Przegląd

Projekt implementuje **355 testów** w trzech kategoriach:

### **Testy Jednostkowe (Unit Tests)** - 232 testy
Izolowane testy logiki biznesowej z **mockowanymi** zależnościami.

### **Testy Integracyjne (Integration Tests)** - 97 testów
Testy komunikacji między komponentami z **prawdziwą** infrastrukturą.

### **Testy Funkcjonalne (Functional Tests)** - 26 testów
End-to-end scenariusze użytkownika (Happy + Sad paths) testujące kompletne user flows.

---

## 🎯 Filozofia Testowania

### **Unit Tests - Mockuj Wszystko**

**Cel:** Testować logikę w izolacji, szybko (<1s), deterministycznie.

**Co mockujemy:**
- ✅ **HTTP requests** (respx, httpx.Mock)
- ✅ **Database connections** (AsyncMock dla DatabaseManager)
- ✅ **External APIs** (Steam API, IsThereAnyDeal)
- ✅ **File I/O** (patches dla filesystem operations)
- ✅ **Time/Date** (freezegun)

**Przykład:**
```python
# tests/unit/server/test_steam_service.py
@respx.mock
def test_get_player_count():
    # Mock Steam API response
    respx.get("https://api.steampowered.com/...").mock(
        return_value=Response(200, json={"response": {"player_count": 50000}})
    )
    
    # Test logic without real API call
    result = steam_client.get_player_count(730)
    assert result == 50000
```

### **Integration Tests - Prawdziwa Infrastruktura**

**Cel:** Testować rzeczywistą komunikację między komponentami.

**Czego NIE mockujemy:**
- ✅ **Database** - prawdziwa PostgreSQL (Neon) z test schema
- ✅ **FastAPI app** - rzeczywisty backend
- ✅ **AsyncClient** - prawdziwy HTTP client
- ✅ **Async fixtures** - prawdziwy event loop

**Co mockujemy (minimalnie):**
- ⚠️ **External APIs** - tylko Steam/ITAD API (aby nie przekroczyć rate limits)
- ⚠️ **Database instance** - patch do test schema (izolacja)

**Przykład:**
```python
# tests/integration/app/test_async_real_integration.py
async def test_login_and_fetch_players_from_database(test_db_manager, async_test_client):
    # Prawdziwa baza danych
    await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=500000)
    
    # Prawdziwy FastAPI + AsyncClient
    async with async_test_client(app) as client:
        response = await client.post("/auth/login", ...)
        
    # Weryfikacja: dane z prawdziwej bazy przez prawdziwy backend
    assert response.status_code == 200
```

### **Functional Tests - End-to-End Scenarios**

**Cel:** Testować kompletne scenariusze użytkownika (Happy + Sad paths).

**26 testów w 8 kategoriach:**
1. **Authentication** (5 testów) - HMAC + JWT + replay attacks
2. **Watchlist CRUD** (4 testy) - Complete lifecycle
3. **Steam API** (4 testy) - External integration
4. **Scheduler** (2 testy) - Background jobs
5. **Rate Limiting** (1 test) - Normal usage
6. **Concurrent** (2 testy) - Race conditions
7. **Validation** (6 testów) - Input validation
8. **Error Handling** (2 testy) - Graceful degradation

**Przykład:**
```python
# tests/functional/test_scenarios.py
async def test_complete_authentication_flow_happy_path(...):
    # 1. Generate HMAC signature
    # 2. Login and get JWT
    # 3. Access protected endpoint
    # 4. Verify data integrity
    # Complete end-to-end flow verification
```

**Dokumentacja:** [tests/docs/FUNCTIONAL_TEST_PLAN.md](docs/FUNCTIONAL_TEST_PLAN.md)

---

## 🏗️ Infrastruktura Testowa

### **Fixtures (tests/conftest.py)**

#### **1. test_db_manager** (async)
```python
@pytest.fixture(scope="function")
async def test_db_manager():
    # Tworzy unique schema: test_custom_steam_dashboard_{uuid}
    # Inicjalizuje prawdziwe tabele w Neon PostgreSQL
    # Cleanup po teście (DROP SCHEMA CASCADE)
```

**Użycie:** Testy integracyjne wymagające bazy danych

#### **2. async_test_client** (async)
```python
@pytest.fixture
async def async_test_client():
    # Tworzy httpx.AsyncClient z ASGITransport
    # Dla testów FastAPI z async database operations
```

**Użycie:** Testy integracyjne API

#### **3. Mocki HTTP (unit)**
```python
# respx automatycznie mockuje httpx requests
@pytest.fixture
def mock_steam_api():
    with respx.mock:
        yield respx
```

---

## 📊 Statystyki

```
Kategoria               Testy    Passing    Coverage
─────────────────────────────────────────────────────
Unit - App              72       69 (96%)   ~85%
Unit - Server           160      160 (100%) ~90%
Integration - App       13       9 (69%)    -
Integration - Server    84       82 (98%)   -
Functional - All        26       26 (100%)  -
Utils                   1        1 (100%)   -
─────────────────────────────────────────────────────
TOTAL                   355      ~347 (98%) ~75%*

* UI wykluczone z coverage (wymaga pytest-qt/E2E)
```

---

## 🚀 Uruchamianie

### **Zalecane (sekwencyjnie):**
```bash
./run_tests.sh              # Wszystkie testy z coverage
./run_tests.sh unit         # Tylko unit (szybkie)
./run_tests.sh integration  # Tylko integration (sekwencyjnie)
```

### **Dlaczego sekwencyjnie?**
Integration testy uruchamiane razem powodują resource exhaustion:
- Async fixtures saturation
- Database connection pool exhaustion
- Event loop conflicts

**Rozwiązanie:** Skrypty uruchamiają testy z opóźnieniami (1-3s) między grupami.

---

## 📁 Struktura

```
tests/
├── unit/                   # 232 testy jednostkowe
│   ├── app/                # 72 - GUI logic, clients, signing
│   └── server/             # 160 - Backend logic, services
│
├── integration/            # 97 testów integracyjnych
│   ├── app/                # 13 - End-to-end flows z AsyncClient
│   └── server/             # 84 - API endpoints, database, scheduler
│
├── functional/             # 26 testów funkcjonalnych ✅
│   └── test_scenarios.py   # End-to-end user scenarios
│
├── conftest.py             # Shared fixtures
├── README.md               # Ten plik
└── docs/                   # Dokumentacja testów
    ├── SUMMARY.md          # Coverage i scenariusze
    ├── UNIT.md             # Przykłady unit testów
    ├── INTEGRATION.md      # Przykłady integration testów
    └── FUNCTIONAL_TEST_PLAN.md  # 26 testów funkcjonalnych (szczegółowo)
```

---

## 🔑 Kluczowe Zasady

### **Unit Tests:**
1. ✅ Mock wszystkie I/O operations
2. ✅ Każdy test < 100ms
3. ✅ Deterministyczne (zawsze ten sam wynik)
4. ✅ Testuj jeden "unit" (function/method)
5. ✅ Używaj `@pytest.mark.unit`

### **Integration Tests:**
1. ✅ Prawdziwa baza danych (unique test schema)
2. ✅ Prawdziwy FastAPI app
3. ✅ AsyncClient dla async operations
4. ✅ Cleanup po każdym teście
5. ✅ Używaj `@pytest.mark.integration`

### **Czego NIE robić:**
- ❌ TestClient z async fixtures (konflikt sync/async)
- ❌ Mockowanie w integration tests (poza external APIs)
- ❌ Dzielenie state między testami
- ❌ Uruchamianie integration testów wszystkich razem (resource exhaustion)

---

## 📚 Więcej Informacji

- **[SUMMARY.md](docs/SUMMARY.md)** - Szczegółowe coverage i scenariusze
- **[UNIT.md](docs/UNIT.md)** - Przykłady testów jednostkowych
- **[INTEGRATION.md](docs/INTEGRATION.md)** - Przykłady testów integracyjnych
- **[FUNCTIONAL_TEST_PLAN.md](docs/FUNCTIONAL_TEST_PLAN.md)** - 26 testów funkcjonalnych (Happy + Sad paths)

---

**Ostatnia aktualizacja:** 14 grudnia 2025

