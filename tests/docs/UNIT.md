# 🔬 UNIT - Testy Jednostkowe

**Przykłady testów jednostkowych z szczegółowym opisem scenariuszy**

---

## 📋 Przegląd

Testy jednostkowe testują **logikę w izolacji** z mockowanymi zależnościami.
- **232 testy** w kategorii unit
- **Czas wykonania:** <1s total
- **Wszystkie I/O:** mockowane (HTTP, DB, filesystem)

---

## 🎯 Scenariusz 1: JWT Authentication Flow

### **Test:** `test_verify_request_signature_old_timestamp`
**Plik:** `tests/unit/server/test_security.py`

#### **Cel:**
Weryfikacja ochrony przed **replay attacks** poprzez sprawdzanie timestamp requestu.

#### **Scenariusz:**
```python
def test_verify_request_signature_old_timestamp(self):
    """Test że stare requesty są odrzucane (ochrona przed replay attacks)."""
    
    # 1. Przygotowanie: Request z timestamp sprzed 10 minut
    client_id = "test-client"
    client_secret = "test-secret"
    method = "GET"
    path = "/api/test"
    body_hash = hashlib.md5(b"").hexdigest()
    timestamp = str(int(time.time()) - 601)  # 10 min 1 sec temu
    nonce = "nonce-123"
    
    # 2. Generowanie sygnatury (która jest technicznie poprawna)
    signature = compute_signature(...)
    
    # 3. Próba weryfikacji starego requestu
    with pytest.raises(HTTPException) as exc_info:
        verify_request_signature(...)
    
    # 4. Oczekiwanie: 401 Unauthorized - timestamp zbyt stary
    assert exc_info.value.status_code == 401
    assert "timestamp" in str(exc_info.value.detail).lower()
```

#### **Co testujemy:**
- ✅ System odrzuca requesty starsze niż 10 minut
- ✅ Zapobiegamy replay attacks (przechwycony request nie działa ponownie)
- ✅ Proper error message w response
- ✅ Correct HTTP status code (401)

#### **Mockowanie:**
- **Time:** Używamy `int(time.time())` ale kontrolujemy timestamp w teście
- **Brak external dependencies** - pure logic

#### **Znaczenie:**
Kluczowe dla bezpieczeństwa - nawet jeśli atakujący przechwyci signed request, nie może go użyć ponownie po 10 minutach.

---

## 🎯 Scenariusz 2: Steam API Client z Retry Logic

### **Test:** `test_handles_network_errors`
**Plik:** `tests/unit/server/test_steam_service_extended.py`

#### **Cel:**
Weryfikacja że client **gracefully handles** błędy sieciowe i nie crashuje aplikacji.

#### **Scenariusz:**
```python
@respx.mock
@pytest.mark.asyncio
async def test_handles_network_errors(self):
    """Test że błędy sieciowe są obsługiwane gracefully."""
    
    # 1. Setup: Mock Steam API aby rzucał network error
    respx.get(re.compile(r".*steampowered\.com.*")).mock(
        side_effect=httpx.ConnectError("Network unreachable")
    )
    
    # 2. Wykonanie: Próba pobrania liczby graczy
    result = await steam_client.get_player_count(730)
    
    # 3. Oczekiwanie: Zwraca None zamiast crashować
    assert result is None  # Graceful degradation
```

#### **Co testujemy:**
- ✅ Client nie crashuje przy network errors
- ✅ Zwraca `None` (graceful degradation)
- ✅ Calling code może obsłużyć brak danych
- ✅ Logging errors (weryfikowane przez caplog)

#### **Mockowanie:**
- **respx.mock** - mockuje httpx requests
- **side_effect** - symuluje network error zamiast response
- **Steam API** - nie wysyłamy prawdziwych requestów

#### **Znaczenie:**
Aplikacja musi działać nawet gdy Steam API jest niedostępny. Zamiast crashować, pokazujemy cached data lub komunikat o błędzie.

---

## 🎯 Scenariusz 3: Concurrent API Requests

### **Test:** `test_concurrent_player_count_requests`
**Plik:** `tests/unit/server/test_steam_service_extended.py`

#### **Cel:**
Weryfikacja że client **bezpiecznie obsługuje** wiele równoczesnych requestów bez race conditions.

#### **Scenariusz:**
```python
@respx.mock
@pytest.mark.asyncio
async def test_concurrent_player_count_requests(self):
    """Test że client obsługuje concurrent requests poprawnie."""
    
    # 1. Setup: Mock różne odpowiedzi dla różnych appid
    respx.get(re.compile(r".*appid=730.*")).mock(
        return_value=Response(200, json={"response": {"player_count": 500000}})
    )
    respx.get(re.compile(r".*appid=440.*")).mock(
        return_value=Response(200, json={"response": {"player_count": 30000}})
    )
    respx.get(re.compile(r".*appid=570.*")).mock(
        return_value=Response(200, json={"response": {"player_count": 400000}})
    )
    
    # 2. Wykonanie: 3 równoczesne requesty
    results = await asyncio.gather(
        steam_client.get_player_count(730),
        steam_client.get_player_count(440),
        steam_client.get_player_count(570)
    )
    
    # 3. Weryfikacja: Każdy request otrzymał właściwą odpowiedź
    assert results[0] == 500000  # CS2
    assert results[1] == 30000   # TF2
    assert results[2] == 400000  # Dota 2
```

#### **Co testujemy:**
- ✅ Concurrent requests nie mieszają danych
- ✅ Każdy request dostaje właściwą odpowiedź
- ✅ Brak race conditions
- ✅ asyncio.gather() działa poprawnie z klientem

#### **Mockowanie:**
- **respx.mock z regex** - różne mocki dla różnych appid
- **asyncio.gather** - testuje concurrent execution
- **Deterministic results** - każdy test daje te same wyniki

#### **Znaczenie:**
Frontend często wysyła wiele requestów naraz (lista gier). Musimy zapewnić że dane nie są pomieszane.

---

## 🎯 Scenariusz 4: HMAC Signature Generation

### **Test:** `test_compute_signature_consistent`
**Plik:** `tests/unit/server/test_security.py`

#### **Cel:**
Weryfikacja że **signature generation jest deterministyczna** - te same inputy zawsze dają ten sam output.

#### **Scenariusz:**
```python
def test_compute_signature_consistent(self):
    """Test że signature computation jest consistent (deterministyczna)."""
    
    # 1. Setup: Identyczne parametry dla obu wywołań
    client_secret = "test-secret"
    method = "POST"
    path = "/api/test"
    body_hash = "abc123"
    timestamp = "1234567890"
    nonce = "nonce-456"
    
    # 2. Wykonanie: Dwa niezależne wywołania z tymi samymi parametrami
    signature1 = compute_signature(
        client_secret, method, path, body_hash, timestamp, nonce
    )
    signature2 = compute_signature(
        client_secret, method, path, body_hash, timestamp, nonce
    )
    
    # 3. Weryfikacja: Obie sygnatury są identyczne
    assert signature1 == signature2
    assert isinstance(signature1, str)
    assert len(signature1) > 0
```

#### **Co testujemy:**
- ✅ Funkcja jest **deterministyczna** (pure function)
- ✅ HMAC-SHA256 działa poprawnie
- ✅ String canonicalization jest consistent
- ✅ Brak losowości w algorytmie

#### **Mockowanie:**
- **Brak** - to jest pure function, nie wymaga mocków

#### **Znaczenie:**
Kluczowe dla security - client i server muszą generować identyczne sygnatury dla tych samych parametrów. Jeśli signature generation jest non-deterministic, authentication nie zadziała.

---

## 🎯 Scenariusz 5: Database Connection Pool Management (Mock)

### **Test:** `test_acquire_connection_context_manager`
**Plik:** `tests/unit/server/test_database_unit.py`

#### **Cel:**
Weryfikacja że **connection pool properly manages resources** i zamyka connections po użyciu.

#### **Scenariusz:**
```python
@pytest.mark.asyncio
async def test_acquire_connection_context_manager(self):
    """Test że connection context manager properly manages resources."""
    
    # 1. Setup: Mock pool z mock connection
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    
    # Mock pool.acquire() jako async context manager
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()
    
    db_manager = DatabaseManager(...)
    db_manager.pool = mock_pool
    
    # 2. Wykonanie: Użycie connection przez context manager
    async with db_manager.pool.acquire() as conn:
        assert conn == mock_conn
    
    # 3. Weryfikacja: Context manager został properly wywołany
    mock_pool.acquire.assert_called_once()
    mock_pool.acquire.return_value.__aenter__.assert_called_once()
    mock_pool.acquire.return_value.__aexit__.assert_called_once()
```

#### **Co testujemy:**
- ✅ Pool.acquire() działa jako async context manager
- ✅ Connection jest properly returned do pool
- ✅ `__aexit__` jest wywoływane (cleanup)
- ✅ Brak resource leaks

#### **Mockowanie:**
- **AsyncMock dla pool** - nie używamy prawdziwej bazy
- **Context manager protocol** - mockujemy `__aenter__` i `__aexit__`
- **Verification** - assert_called_once() sprawdza wywołania

#### **Znaczenie:**
Resource leaks (nie zamknięte connections) mogą prowadzić do exhaustion pool. Context manager pattern zapewnia proper cleanup nawet przy exceptions.

---

## 🔑 Kluczowe Zasady Unit Testów

### **1. Mock All I/O:**
```python
# ✅ Dobre
@respx.mock
def test_api_call():
    respx.get("https://api.com").mock(return_value=Response(200, json={}))
    
# ❌ Złe
def test_api_call():
    result = httpx.get("https://api.com")  # Prawdziwy request!
```

### **2. Deterministyczne:**
```python
# ✅ Dobre - ten sam result zawsze
def test_signature():
    sig = compute_signature("secret", "GET", "/api", "hash", "123", "nonce")
    assert sig == "expected_value"
    
# ❌ Złe - losowy result
def test_signature():
    sig = compute_signature("secret", "GET", "/api", random_hash(), ...)
```

### **3. Szybkie (<100ms każdy):**
```python
# ✅ Dobre
def test_validation():
    assert validate_steam_id("76561198012345678")
    
# ❌ Złe
def test_validation():
    time.sleep(1)  # Niepotrzebne opóźnienie
```

### **4. Testuj Jeden Unit:**
```python
# ✅ Dobre - testuje tylko compute_signature
def test_compute_signature():
    result = compute_signature(...)
    assert result == expected
    
# ❌ Złe - testuje wiele funkcji
def test_full_auth_flow():
    sig = compute_signature(...)
    jwt = create_jwt(...)
    response = verify_request(...)  # Za dużo!
```

### **5. Descriptive Names:**
```python
# ✅ Dobre
def test_verify_request_signature_old_timestamp_rejected():
    ...
    
# ❌ Złe
def test_1():
    ...
```

---

## 📊 Struktura Unit Testów

```
tests/unit/
├── app/                     # 72 testy - frontend logic
│   ├── test_api_client.py            # Authentication, token mgmt
│   ├── test_signing.py               # HMAC signature generation
│   ├── test_user_data_manager.py     # JSON persistence
│   ├── test_config.py                # Config loading
│   └── test_deals_client_mocked.py   # Deals API client
│
└── server/                  # 160 testów - backend logic
    ├── test_security.py              # JWT, HMAC, nonce mgmt
    ├── test_steam_service.py         # Steam API client
    ├── test_steam_service_extended.py # Extended scenarios
    ├── test_models.py                # Pydantic models
    ├── test_validation.py            # Input validation
    ├── test_database_unit.py         # DB logic (mocked)
    └── test_auth_routes_unit.py      # Auth endpoints logic
```

---

## 🎓 Lessons Learned

### **Co działa dobrze:**

1. ✅ **respx.mock** - excellent dla mockowania httpx
2. ✅ **AsyncMock** - proper async/await support
3. ✅ **pytest.raises** - clean way to test exceptions
4. ✅ **Fixtures** - DRY principle dla common setups
5. ✅ **Markers** - `@pytest.mark.unit` dla kategoryzacji

### **Częste pułapki:**

1. ❌ Mieszanie Mock i AsyncMock
2. ❌ Nie mockowanie time.time() w testach timestamp
3. ❌ Testing implementation zamiast behavior
4. ❌ Zbyt skomplikowane setup (fixture hell)
5. ❌ Brak cleanup po testach z side effects

---

**Ostatnia aktualizacja:** 14 grudnia 2025

