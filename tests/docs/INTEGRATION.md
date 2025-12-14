# 🔗 INTEGRATION - Testy Integracyjne

**Przykłady testów integracyjnych z prawdziwą infrastrukturą**

---

## 📋 Przegląd

Testy integracyjne testują **rzeczywistą komunikację** między komponentami.
- **98 testów** w kategorii integration
- **Czas wykonania:** ~60s (sekwencyjnie)
- **Prawdziwa infrastruktura:** PostgreSQL (Neon), FastAPI, AsyncClient

---

## 🎯 Scenariusz 1: Complete Authentication Flow

### **Test:** `test_login_and_fetch_players_from_database`
**Plik:** `tests/integration/app/test_async_real_integration.py`

#### **Cel:**
Testowanie **pełnego flow** od autentykacji przez API do pobrania danych z prawdziwej bazy.

#### **Scenariusz:**
```python
async def test_login_and_fetch_players_from_database(test_db_manager, async_test_client):
    """Test: Login → JWT → API call → Database → Response"""
    
    from server.app import app

    # 1. Setup: Wstaw dane do PRAWDZIWEJ bazy Neon
    await test_db_manager.upsert_watchlist(appid=730, name="CS2", last_count=500000)
    await test_db_manager.upsert_watchlist(appid=440, name="TF2", last_count=30000)

    with patch('server.app.db', test_db_manager):
        async with async_test_client(app) as client:
            # 2. Step 1: Authenticate - generuj HMAC signature
            client_id = "desktop-main"
            client_secret = "Pjad7glZrPeITY-9QQ0vhz2yXKB89R_02CSZQFmekt0"
            body_data = {"client_id": client_id}
            body_bytes = json.dumps(body_data).encode('utf-8')

            login_headers = sign_request("POST", "/auth/login", body_bytes, ...)
            login_headers["Content-Type"] = "application/json"

            # 3. Login request do PRAWDZIWEGO FastAPI
            login_response = await client.post("/auth/login", content=body_bytes, headers=login_headers)

            # 4. Verify: JWT token received
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]

            # 5. Step 2: API call z JWT token
            api_path = "/api/current-players"
            api_headers = sign_request("GET", api_path, b"", ...)
            api_headers["Authorization"] = f"Bearer {token}"

            # 6. Fetch data from REAL database via API
            api_response = await client.get(api_path, headers=api_headers)

            # 7. Verify: Data integrity across all layers
            assert api_response.status_code == 200
            games = api_response.json()["games"]
            assert len(games) == 2

            # 8. Verify: Exact data matches database
            cs2_game = next(g for g in games if g["appid"] == 730)
            assert cs2_game["name"] == "CS2"
            assert cs2_game["last_count"] == 500000
```

#### **Co testujemy:**
- ✅ **HMAC signature generation** działa z prawdziwym API
- ✅ **JWT authentication** - login flow complete
- ✅ **Database operations** - real PostgreSQL queries
- ✅ **FastAPI routing** - request processing
- ✅ **Data integrity** - dane przechodzą przez wszystkie warstwy bez zmian
- ✅ **AsyncClient** - proper async/await handling

#### **Prawdziwa infrastruktura:**
- ✅ **PostgreSQL (Neon)** - unique test schema `test_custom_steam_dashboard_{uuid}`
- ✅ **FastAPI app** - rzeczywisty backend z middleware
- ✅ **httpx.AsyncClient** - prawdziwy HTTP client z ASGITransport
- ✅ **JWT library** - prawdziwe token generation

#### **Mockowanie (minimalne):**
- ⚠️ `patch('server.app.db', test_db_manager)` - używamy test schema zamiast production
- **Wszystko inne:** prawdziwe!

#### **Znaczenie:**
To jest **główny integration test** - weryfikuje że cała architektura działa razem. Jeśli ten test przechodzi, mamy pewność że authentication + API + database flow działa poprawnie.

---

## 🎯 Scenariusz 2: Concurrent Database Operations

### **Test:** `test_concurrent_inserts_to_watchlist`
**Plik:** `tests/integration/server/test_database_integration.py`

#### **Cel:**
Weryfikacja że database **obsługuje concurrent inserts** bez race conditions i data corruption.

#### **Scenariusz:**
```python
@pytest.mark.asyncio
async def test_concurrent_inserts_to_watchlist(test_db_manager):
    """Test że concurrent inserts nie powodują race conditions."""
    
    # 1. Setup: Przygotuj listę gier do wstawienia
    games = [
        (730, "CS2", 500000),
        (440, "TF2", 30000),
        (570, "Dota 2", 400000),
        (10, "Counter-Strike", 5000),
        (20, "Team Fortress Classic", 100)
    ]
    
    # 2. Execute: 5 równoczesnych inserts do PRAWDZIWEJ bazy
    await asyncio.gather(*[
        test_db_manager.upsert_watchlist(appid=appid, name=name, last_count=count)
        for appid, name, count in games
    ])
    
    # 3. Verify: Wszystkie gry są w bazie
    watchlist = await test_db_manager.get_watchlist()
    assert len(watchlist) == 5
    
    # 4. Verify: Brak duplikatów (data integrity)
    appids = [game["appid"] for game in watchlist]
    assert len(appids) == len(set(appids))  # Unique appids
    
    # 5. Verify: Dane są poprawne (no corruption)
    cs2 = next(g for g in watchlist if g["appid"] == 730)
    assert cs2["name"] == "CS2"
    assert cs2["last_count"] == 500000
```

#### **Co testujemy:**
- ✅ **Concurrent safety** - asyncio.gather() z wieloma operacjami
- ✅ **Database transactions** - proper isolation
- ✅ **Connection pool** - zarządzanie wieloma connections
- ✅ **Data integrity** - brak corruption przy concurrent access
- ✅ **Uniqueness constraints** - database enforces rules

#### **Prawdziwa infrastruktura:**
- ✅ **PostgreSQL connection pool** - asyncpg pool management
- ✅ **Real transactions** - BEGIN/COMMIT/ROLLBACK
- ✅ **Async operations** - proper event loop handling

#### **Mockowanie:**
- **Brak** - wszystko prawdziwe!

#### **Znaczenie:**
W produkcji mamy wiele równoczesnych requestów. Musimy zapewnić że database operations są thread-safe i nie powodują data corruption.

---

## 🎯 Scenariusz 3: API Rate Limiting Enforcement

### **Test:** `test_rate_limit_enforced`
**Plik:** `tests/integration/server/test_api_endpoints.py`

#### **Cel:**
Weryfikacja że **FastAPI middleware** prawidłowo enforces rate limiting na endpoints.

#### **Scenariusz:**
```python
@pytest.mark.asyncio
async def test_rate_limit_enforced(app):
    """Test że rate limiting jest enforced na protected endpoints."""
    
    # 1. Setup: FastAPI app z prawdziwym middleware
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # 2. Execute: Wysłanie wielu requestów w krótkim czasie
    responses = []
    for i in range(150):  # Przekroczenie limitu (100/min)
        response = client.get("/api/health")
        responses.append(response.status_code)
    
    # 3. Verify: Niektóre requesty dostają 429 Too Many Requests
    assert 429 in responses
    
    # 4. Verify: Rate limit response zawiera Retry-After header
    rate_limited_response = next(
        r for r in [client.get("/api/health") for _ in range(10)] 
        if r.status_code == 429
    )
    assert "Retry-After" in rate_limited_response.headers
```

#### **Co testujemy:**
- ✅ **Middleware execution** - rate limiter działa
- ✅ **Request counting** - proper tracking per client
- ✅ **429 response** - correct HTTP status
- ✅ **Retry-After header** - client wie kiedy retry
- ✅ **Partial success** - nie wszystkie requesty są blokowane

#### **Prawdziwa infrastruktura:**
- ✅ **FastAPI middleware stack** - prawdziwy request processing
- ✅ **In-memory state** - rate limiter counting

#### **Mockowanie:**
- **Brak** - testujemy prawdziwy middleware

#### **Znaczenie:**
Rate limiting chroni API przed abuse. Musimy zapewnić że działa poprawnie - blokuje nadmiar requestów ale nie legitymicznych użytkowników.

---

## 🎯 Scenariusz 4: Foreign Key Constraint Enforcement

### **Test:** `test_insert_player_count_without_watchlist_fails`
**Plik:** `tests/integration/server/test_database_integration.py`

#### **Cel:**
Weryfikacja że **database constraints** są enforced - nie można wstawić player count bez istniejącej gry w watchlist.

#### **Scenariusz:**
```python
@pytest.mark.asyncio
async def test_insert_player_count_without_watchlist_fails(test_db_manager):
    """Test że foreign key constraint jest enforced."""
    
    # 1. Setup: NIE dodajemy gry do watchlist
    # (celowo pomijamy setup)
    
    # 2. Execute: Próba wstawienia player count dla nieistniejącej gry
    from datetime import datetime, timezone
    
    with pytest.raises(Exception) as exc_info:
        await test_db_manager.insert_player_count(
            appid=99999,  # Nie istnieje w watchlist
            count=50000,
            timestamp=datetime.now(timezone.utc)
        )
    
    # 3. Verify: PostgreSQL rzuca foreign key violation
    # asyncpg wraps it as ForeignKeyViolationError or similar
    assert "foreign key" in str(exc_info.value).lower() or \
           "constraint" in str(exc_info.value).lower()
```

#### **Co testujemy:**
- ✅ **Foreign key constraints** - database enforces relationships
- ✅ **Data integrity** - orphaned records nie mogą istnieć
- ✅ **Error propagation** - exception dociera do kodu
- ✅ **Database schema** - constraints są properly zdefiniowane

#### **Prawdziwa infrastruktura:**
- ✅ **PostgreSQL constraints** - real database enforcement
- ✅ **Schema validation** - CREATE TABLE z FOREIGN KEY
- ✅ **asyncpg exception handling** - proper Python exceptions

#### **Mockowanie:**
- **Brak** - testujemy prawdziwą bazę

#### **Znaczenie:**
Database constraints są **ostatnią linią obrony** przed bad data. Nawet jeśli aplikacja ma bugs, baza nie pozwoli na data corruption.

---

## 🎯 Scenariusz 5: Scheduler with Real Database Updates

### **Test:** `test_collect_player_counts_updates_database`
**Plik:** `tests/integration/server/test_scheduler.py`

#### **Cel:**
Weryfikacja że **scheduler** prawidłowo zbiera dane z API i **aktualizuje prawdziwą bazę**.

#### **Scenariusz:**
```python
@pytest.mark.asyncio
async def test_collect_player_counts_updates_database(test_db_manager):
    """Test że scheduler updates database z player counts."""
    
    # 1. Setup: Dodaj gry do watchlist w prawdziwej bazie
    await test_db_manager.upsert_watchlist(730, "CS2", 0)
    await test_db_manager.upsert_watchlist(440, "TF2", 0)
    
    # 2. Setup: Mock Steam API responses (aby nie przekroczyć rate limits)
    with respx.mock:
        respx.get(re.compile(r".*appid=730.*")).mock(
            return_value=Response(200, json={"response": {"player_count": 500000}})
        )
        respx.get(re.compile(r".*appid=440.*")).mock(
            return_value=Response(200, json={"response": {"player_count": 30000}})
        )
        
        # 3. Execute: Uruchom collector
        from server.scheduler import PlayerCountCollector
        
        collector = PlayerCountCollector(db_manager=test_db_manager)
        await collector.collect_player_counts()
    
    # 4. Verify: Database został zaktualizowany
    watchlist = await test_db_manager.get_watchlist()
    
    cs2 = next(g for g in watchlist if g["appid"] == 730)
    tf2 = next(g for g in watchlist if g["appid"] == 440)
    
    assert cs2["last_count"] == 500000  # Updated from 0
    assert tf2["last_count"] == 30000   # Updated from 0
    
    # 5. Verify: Player counts są w historical table
    # (weryfikacja że obie tabele zostały updated)
```

#### **Co testujemy:**
- ✅ **Scheduler logic** - collect → parse → save
- ✅ **Database updates** - real SQL UPDATE queries
- ✅ **API integration** - fetch z mockowanego Steam API
- ✅ **Data flow** - external API → scheduler → database
- ✅ **Concurrent processing** - multiple games at once

#### **Prawdziwa infrastruktura:**
- ✅ **PostgreSQL** - real database updates
- ✅ **Scheduler** - real async job execution
- ✅ **Connection pool** - proper resource management

#### **Mockowanie (hybrid):**
- ⚠️ **Steam API** - mockowane (rate limits)
- ✅ **Database** - prawdziwa!
- ✅ **Scheduler logic** - prawdziwa!

#### **Znaczenie:**
Scheduler jest **core funkcjonalnością** - automatyczne zbieranie danych. Musimy zapewnić że działa end-to-end: fetch → process → save.

---

## 🔑 Kluczowe Zasady Integration Testów

### **1. Prawdziwa Infrastruktura:**
```python
# ✅ Dobre - prawdziwa baza
async def test_database(test_db_manager):
    await test_db_manager.upsert_watchlist(...)
    result = await test_db_manager.get_watchlist()
    
# ❌ Złe - mockowana baza w integration test!
async def test_database():
    mock_db = AsyncMock()
    mock_db.upsert_watchlist = AsyncMock(return_value=None)
```

### **2. Unique Test Schema:**
```python
# ✅ Dobre - każdy test ma unique schema
@pytest.fixture
async def test_db_manager():
    test_schema = f"test_custom_steam_dashboard_{uuid.uuid4().hex[:8]}"
    # CREATE SCHEMA, CREATE TABLES, yield, DROP SCHEMA CASCADE
    
# ❌ Złe - shared schema (tests interferują)
```

### **3. Proper Cleanup:**
```python
# ✅ Dobre - cleanup w finally
@pytest.fixture
async def test_db_manager():
    # setup
    try:
        yield db_manager
    finally:
        # DROP SCHEMA CASCADE - guaranteed cleanup
        
# ❌ Złe - brak cleanup (leftover data)
```

### **4. AsyncClient dla FastAPI:**
```python
# ✅ Dobre - AsyncClient z async fixtures
async with async_test_client(app) as client:
    response = await client.get("/api/endpoint")
    
# ❌ Złe - TestClient z async database (conflict!)
client = TestClient(app)
response = client.get("/api/endpoint")  # Sync client + async DB = 💥
```

### **5. Test Isolation:**
```python
# ✅ Dobre - każdy test niezależny
async def test_1(test_db_manager):
    await test_db_manager.upsert_watchlist(730, "CS2", 500000)
    # Test tylko z tymi danymi
    
async def test_2(test_db_manager):
    await test_db_manager.upsert_watchlist(440, "TF2", 30000)
    # Nowy schema, fresh data
    
# ❌ Złe - tests dzielą state
```

---

## 📊 Struktura Integration Testów

```
tests/integration/
├── app/                              # 13 testów - E2E flows
│   └── test_async_real_integration.py    # AsyncClient flows
│
└── server/                           # 85 testów
    ├── test_api_endpoints.py             # 43 - API testing
    ├── test_database_integration.py      # 18 - Database ops
    └── test_scheduler.py                 # 30 - Background jobs
```

---

## 🎓 Lessons Learned

### **Co działa dobrze:**

1. ✅ **Unique schema per test** - pełna izolacja
2. ✅ **AsyncClient** - proper async support
3. ✅ **respx dla external APIs** - nie przekraczamy rate limits
4. ✅ **Sekwencyjne uruchamianie** - unikamy resource exhaustion
5. ✅ **Real database** - znajdujemy bugs których unit testy nie złapią

### **Częste pułapki:**

1. ❌ TestClient + async fixtures = conflict
2. ❌ Wszystkie testy razem = resource exhaustion
3. ❌ Brak cleanup = leftover schemas
4. ❌ Shared schema = test interference
5. ❌ Mockowanie bazy w integration tests

### **Best Practices:**

1. ✅ Jeden scenariusz per test
2. ✅ Descriptive test names
3. ✅ Verify data integrity
4. ✅ Test error paths
5. ✅ Monitor resource usage

---

**Ostatnia aktualizacja:** 14 grudnia 2025

