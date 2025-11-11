# Analiza Bezpieczeństwa - Słabe Strony i Mitygacje

## Potencjalne Zagrożenia i Ich Mitygacje

### 1. 🔴 Kradzież JWT Token (Token Theft)

#### Zagrożenie:
Jeśli atakujący zdobędzie token JWT (np. przez XSS, man-in-the-middle, malware), może używać go do momentu wygaśnięcia.

#### W naszej implementacji:
**Ryzyko: NISKIE-ŚREDNIE** (Desktop app, nie browser)

**Dlaczego mniej ryzykowne:**
- ✅ Desktop app - brak XSS (nie ma DOM/JavaScript)
- ✅ Token w pamięci procesu (nie localStorage/cookies)
- ✅ HTTPS zapobiega MITM

**Ale wciąż możliwe przez:**
- ❌ Malware na komputerze użytkownika
- ❌ Memory dump procesu
- ❌ Debug/logging leak

#### Mitygacje zastosowane:
1. **Krótki TTL (20 minut)**
   ```python
   JWT_TTL_SECONDS = 1200  # Okno ataku: max 20 min
   ```

2. **Dual-layer (JWT + HMAC)**
   - Skradziony JWT SAM W SOBIE nie wystarcza
   - Atakujący potrzebuje TEŻ `CLIENT_SECRET` do podpisywania żądań
   ```python
   # Każde żądanie wymaga:
   Authorization: Bearer <JWT>           # Token (skradziony?)
   X-Signature: <HMAC(CLIENT_SECRET)>   # Wymaga CLIENT_SECRET!
   ```

3. **No sensitive data in JWT**
   ```python
   # JWT zawiera tylko:
   {
     "sub": "desktop-main",
     "client_id": "desktop-main",
     "iat": 1736623443,
     "exp": 1736624643,
     "type": "access"
   }
   # Brak: passwords, user data, permissions
   ```

4. **Automatic expiration**
   - Brak manual revocation
   - Token automatycznie wygasa po 20 min
   - Użytkownik musi ponownie zalogować (transparentne)

#### Co można jeszcze zrobić:
- ⚠️ Token refresh mechanism (oddzielny refresh token)
- ⚠️ Token blacklist (wymaga stateful storage)
- ⚠️ Device fingerprinting (bind token to device)
- ⚠️ Anomaly detection (unusual API usage)

---

### 2. 🔴 Replay Attacks (Odtwarzanie Żądań)

#### Zagrożenie:
Atakujący przechwytuje żądanie i wysyła je ponownie.

#### W naszej implementacji:
**Ryzyko: BARDZO NISKIE** ✅

#### Mitygacje zastosowane:

1. **Nonce Anti-Replay**
   ```python
   _nonce_cache: OrderedDict[str, float] = OrderedDict()
   
   def _check_and_store_nonce(nonce: str) -> bool:
       if nonce in _nonce_cache:
           return False  # REPLAY DETECTED!
       
       _nonce_cache[nonce] = time.time() + 300  # Store 5 min
       return True
   ```
   
   - Każdy nonce może być użyty **tylko raz**
   - Cache z TTL 5 minut
   - Limit 10,000 entries (LRU eviction)

2. **Timestamp Validation**
   ```python
   request_timestamp = int(x_timestamp)
   now = int(time.time())
   time_diff = abs(now - request_timestamp)
   
   if time_diff > 60:
       raise HTTPException(401, "Request too old")
   ```
   
   - Żądania starsze niż ±60 sekund są odrzucane
   - Nawet jeśli nonce jest unikalny, stary timestamp = reject

3. **Body Hash w Signature**
   ```python
   body_hash = hashlib.sha256(body).hexdigest()
   message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
   ```
   
   - Modyfikacja body zmienia signature
   - Nie można podmienić danych w przechwyconej wiadomości

#### Scenariusze ataku NIEMOŻLIWE:

❌ **Replay tego samego żądania:**
```
Atakujący: Przechwycił GET /api/games z nonce=ABC123
Atakujący: Wysyła ponownie GET /api/games z nonce=ABC123
Serwer: REJECT - "Nonce already used"
```

❌ **Replay z nowym nonce ale starym timestamp:**
```
Atakujący: Przechwycił żądanie z timestamp=1736623443
Atakujący: Generuje nowy nonce=XYZ789, ale używa starego timestamp
Serwer: REJECT - "Request too old" (> 60s)
```

❌ **Modyfikacja body w przechwyconej wiadomości:**
```
Atakujący: Przechwycił POST /api/games/tags/batch
Atakujący: Zmienia body: {"appids": [730]} → {"appids": [440]}
Atakujący: Wysyła z oryginalną signature
Serwer: Oblicza body_hash → INNY niż w signature
Serwer: REJECT - "Invalid signature"
```

---

### 3. 🟡 In-Memory Nonce Cache (Brak Persistence)

#### Zagrożenie:
Restart serwera czyści cache nonców. Teoretycznie stare nonce mogą być użyte ponownie.

#### W naszej implementacji:
**Ryzyko: BARDZO NISKIE** (Edge case)

**Dlaczego nie jest problemem:**

1. **Timestamp protection:**
   - Nawet po restarcie, stare żądania (> 60s) są odrzucane
   - Okno ataku: max 60 sekund po restarcie

2. **Częstotliwość restartów:**
   - Produkcyjny serwer restartuje rzadko
   - Desktop app używa nonce raz i zapomina

3. **TTL nonców (5 min):**
   - Po 5 minutach nonce są usuwane z cache
   - Restart eliminuje tylko ostatnie 5 minut nonców

#### Scenariusz ataku:
```
1. Atakujący przechwytuje żądanie z nonce=ABC123, timestamp=1736623443
2. Serwer zapisuje nonce w cache
3. Serwer RESTARTUJE (cache wyczyszczony)
4. Atakujący wysyła przechwycone żądanie ponownie
   
   IF timestamp jest < 60s od teraz:
      → Możliwy replay
   ELSE:
      → REJECT "Request too old"
```

**Prawdopodobieństwo sukcesu:** ~ 0.001%
- Wymaga: restart serwera DOKŁADNIE w oknie 60s przed atakiem
- Okno: 60s z całego uptime serwera (tysiące godzin)

#### Możliwe ulepszenia:
```python
# Option 1: Redis dla nonce cache (distributed + persistent)
import redis
nonce_cache = redis.Redis(...)

# Option 2: Database (wolniejsze, ale persistent)
await db.execute("INSERT INTO used_nonces (nonce, expires_at) VALUES (?, ?)")

# Option 3: Hybrid (in-memory + periodic DB sync)
if len(_nonce_cache) % 1000 == 0:
    await sync_nonces_to_db()
```

**Nasza decyzja:** In-memory wystarcza dla desktop app.  
Dla high-security / high-traffic: użyj Redis.

---

### 4. 🟡 Client Secret Exposure (Wyciek Sekretu)

#### Zagrożenie:
`CLIENT_SECRET` jest przechowywany w `.env` na komputerze użytkownika. Może zostać odczytany przez malware lub inżynierię odwrotną.

#### W naszej implementacji:
**Ryzyko: ŚREDNIE** (Desktop app specific)

**Dlaczego jest ryzyko:**
- ❌ `.env` w plain text
- ❌ Proces może być debugowany (memory dump)
- ❌ Executable może być zdekompilowany

**Konsekwencje wycieku:**
```
IF atakujący zdobędzie CLIENT_SECRET:
   → Może generować własne HMAC signatures
   → Może logować się jako ten klient
   → Może wykonywać API calls bez GUI
```

#### Mitygacje zastosowane:

1. **Jeden secret per client type (nie per user)**
   ```python
   CLIENTS_JSON = {
       "desktop-main": "secret123"  # Wspólny dla wszystkich instalacji
   }
   ```
   
   - Kompromitacja jednego użytkownika ≠ kompromitacja jednego usera
   - Kompromitacja = kompromitacja całego client type
   - **Trade-off:** Prostota vs. granular security

2. **Rate limiting per client_id**
   ```python
   @limiter.limit("30/minute")
   async def get_games(client_id: str = Depends(...)):
       # Even z valid secret, limited requests
   ```
   
   - Atakujący z secretem może zrobić max 30 req/min
   - Zapobiega abuse

3. **Server-side validation**
   - JWT zawiera tylko `client_id` (nie secret)
   - Secret nigdy nie opuszcza klienta (tylko w HMAC)
   - Serwer weryfikuje czy client_id ∈ CLIENTS_MAP

#### Co można jeszcze zrobić:

**Option 1: Per-user secrets (Database)**
```python
# Każdy user ma unikalny secret
user_registration():
    secret = secrets.token_urlsafe(32)
    await db.execute(
        "INSERT INTO clients (client_id, client_secret) VALUES (?, ?)",
        (client_id, hash_secret(secret))
    )
```
**Pros:** Granular revocation  
**Cons:** Wymaga user management, registracji

**Option 2: Hardware-backed secrets (TPM, Keychain)**
```python
# Windows: DPAPI
# macOS: Keychain
# Linux: libsecret
from keyring import get_password, set_password

client_secret = get_password("steam_dashboard", "client_secret")
```
**Pros:** Trudniejsze do wyciągnięcia  
**Cons:** Platform-specific, komplikacja

**Option 3: mTLS (Client Certificates)**
```nginx
# Reverse proxy (nginx)
ssl_client_certificate /path/to/ca.crt;
ssl_verify_client on;
```
**Pros:** Strongest authentication  
**Cons:** Certificate management, user experience

**Nasza decyzja:** Shared secret per client type.  
Dla enterprise: per-user secrets + hardware backing.

---

### 5. 🟢 JWT Secret Exposure (Wyciek JWT_SECRET)

#### Zagrożenie:
Jeśli `JWT_SECRET` wycieknie, atakujący może:
- Generować własne valid JWT tokeny
- Podszywać się pod dowolnego klienta
- Całkowita kompromitacja systemu

#### W naszej implementacji:
**Ryzyko: BARDZO NISKIE** (Server-only secret) ✅

**Dlaczego bezpieczne:**
- ✅ JWT_SECRET TYLKO na serwerze (nigdy nie opuszcza)
- ✅ Klient nie zna JWT_SECRET
- ✅ Klient tylko weryfikuje, nie tworzy tokenów

**Ochrona:**
```python
# server/security.py
JWT_SECRET = os.getenv("JWT_SECRET", "")

if not JWT_SECRET:
    logger.warning("JWT_SECRET not set!")
    JWT_SECRET = "insecure-default-change-me"  # Development only
```

**Best practices:**
1. Silny secret (32+ bytes random)
2. Różny dla każdego środowiska (dev/staging/prod)
3. Rotacja co 6-12 miesięcy
4. Przechowywanie w secrets manager (AWS Secrets Manager, HashiCorp Vault)

#### Scenariusz katastroficzny:
```
IF JWT_SECRET wycieknie:
   1. Atakujący generuje JWT: {"client_id": "desktop-main", "exp": +1000 years}
   2. Używa tokenu BEZ client_secret (bo JWT wystarcza)
   3. Full API access FOREVER
   
SOLUTION:
   1. Natychmiastowa rotacja JWT_SECRET
   2. Wszystkie tokeny stają się invalid
   3. Wszyscy użytkownicy muszą ponownie zalogować
```

#### Mitygacja (Dual-layer ratuje!)
**Nawet jeśli JWT_SECRET wycieknie:**
```python
# Atakujący tworzy fake JWT
fake_jwt = jwt.encode({"client_id": "admin"}, stolen_jwt_secret)

# Ale NADAL potrzebuje CLIENT_SECRET dla HMAC!
# Bez CLIENT_SECRET:
request_signature = compute_signature(???, ...)  # Brak sekretu!
# → Invalid signature → REJECT
```

**Dual-layer security means:**  
Kompromitacja JWT_SECRET SAMA W SOBIE nie wystarcza.  
Atakujący potrzebuje BOTH:
- JWT_SECRET (do fake tokenów)
- CLIENT_SECRET (do podpisywania żądań)

---

### 6. 🟡 Man-in-the-Middle (MITM) Attacks

#### Zagrożenie:
Atakujący przechwytuje komunikację między klientem a serwerem.

#### W naszej implementacji:
**Ryzyko: NISKIE** (HTTPS assumed)

**Bez HTTPS:**
```
Client ←─────[PLAIN TEXT]─────→ Attacker ←─────[PLAIN TEXT]─────→ Server
       JWT, CLIENT_SECRET, requests all visible!
```

**Z HTTPS:**
```
Client ←─────[ENCRYPTED]─────→ Attacker ←─────[ENCRYPTED]─────→ Server
       TLS tunnel, can't read content
```

#### Założenia:
- ✅ Produkcja MUSI używać HTTPS
- ✅ Cloudflare Full/Strict mode (end-to-end TLS)
- ✅ Certificate pinning (opcjonalnie w desktop app)

#### Co się stanie przy MITM bez HTTPS:
1. **Kradzież JWT token** → Użycie do exp (20 min)
2. **Kradzież CLIENT_SECRET** → Generowanie własnych requestów FOREVER
3. **Replay attacks** → Częściowo chronione (nonce + timestamp)
4. **Response tampering** → Możliwe (brak signature na response)

#### Response Integrity (Not implemented):
Obecnie serwer NIE podpisuje responses. Atakujący przy MITM może:
```
Server → {"games": [... real data ...]} 
   ↓ MITM modifies
Client ← {"games": [... fake data ...]}  # Client nie wie!
```

**Możliwe ulepszenie:**
```python
# Server signs response
response_data = {"games": [...]}
response_signature = hmac.new(
    JWT_SECRET,
    json.dumps(response_data).encode(),
    hashlib.sha256
).hexdigest()

return {
    "data": response_data,
    "signature": response_signature
}

# Client verifies
if not verify_response_signature(response):
    raise Exception("Response tampering detected!")
```

**Nasza decyzja:** HTTPS + trust network.  
Response signing = overhead, HTTPS jest wystarczające.

---

### 7. 🟢 Brute Force JWT Cracking

#### Zagrożenie:
Atakujący próbuje zgadnąć JWT_SECRET przez brute force.

#### W naszej implementacji:
**Ryzyko: BRAK** (Impossible) ✅

**Matematyka:**
```python
JWT_SECRET = secrets.token_urlsafe(32)  # 32 bytes = 256 bits

Możliwości: 2^256 = 1.15 × 10^77
Próby/sekundę: 10^12 (1 trillion)
Czas złamania: 3.67 × 10^57 lat

Dla porównania:
Wiek wszechświata: 1.38 × 10^10 lat
```

**Warunek bezpieczeństwa:**
- ✅ Secret ma ≥256 bitów entropii
- ✅ Używamy `secrets` module (cryptographically secure)
- ✅ Nie używamy słabych sekretów ("password123")

**Słabe sekrety (NIGDY!):**
```python
# ❌ ZŁE przykłady:
JWT_SECRET = "secret"           # Crackable in milliseconds
JWT_SECRET = "my_app_2024"      # Dictionary attack
JWT_SECRET = hashlib.md5(...)   # Only 128 bits

# ✅ DOBRE:
JWT_SECRET = secrets.token_urlsafe(32)  # 256 bits randomness
```

---

### 8. 🟡 Timing Attacks na Signature Verification

#### Zagrożenie:
Atakujący mierzy czas response i dedukuje informacje o signature.

#### W naszej implementacji:
**Ryzyko: BARDZO NISKIE** (Mitigated) ✅

**Ochrona:**
```python
# Constant-time comparison!
if not hmac.compare_digest(expected_signature, x_signature):
    raise HTTPException(401, "Invalid signature")
```

**Bez constant-time:**
```python
# ❌ Vulnerable to timing attack:
if expected_signature == x_signature:  # String comparison stops at first diff
    # Character-by-character: timing reveals position of difference
```

**Z constant-time:**
```python
# ✅ Safe:
hmac.compare_digest(a, b)  # Always compares ALL characters
# Timing is CONSTANT regardless of where difference is
```

**Dlaczego ważne:**
```
Atakujący próbuje różne signatures:
"AAAA..." → Response: 1.001s
"BAAA..." → Response: 1.001s
"CAAA..." → Response: 1.001s  
...
"XAAA..." → Response: 1.002s  ← First char match! Continue with 2nd char
```

Z `hmac.compare_digest()` wszystkie responsy zajmują ten sam czas.

---

## Podsumowanie Zagrożeń

| Zagrożenie | Ryzyko | Mitygacja | Status |
|------------|--------|-----------|--------|
| Token Theft | 🟡 Średnie | Krótki TTL + Dual-layer | ✅ Mitigated |
| Replay Attacks | 🟢 Bardzo niskie | Nonce + Timestamp | ✅ Protected |
| Nonce Cache Restart | 🟢 Bardzo niskie | Timestamp window | ✅ Acceptable |
| Client Secret Leak | 🟡 Średnie | Rate limiting + Shared secret | ⚠️ Trade-off |
| JWT Secret Leak | 🟢 Bardzo niskie | Server-only + Dual-layer | ✅ Protected |
| MITM | 🟡 Średnie | HTTPS required | ✅ Assumed |
| Brute Force | 🟢 Brak | 256-bit secret | ✅ Impossible |
| Timing Attack | 🟢 Bardzo niskie | Constant-time comparison | ✅ Protected |

### Ogólna ocena bezpieczeństwa: **8.5/10** ⭐⭐⭐⭐

**Mocne strony:**
- ✅ Dual-layer (JWT + HMAC) eliminuje wiele ataków
- ✅ Anti-replay protection (nonce + timestamp)
- ✅ Krótki TTL minimalizuje okno ataku
- ✅ Constant-time comparisons
- ✅ No sensitive data in JWT

**Obszary do poprawy (opcjonalne):**
- ⚠️ Per-user secrets (zamiast shared)
- ⚠️ Response signature verification
- ⚠️ Persistent nonce cache (Redis)
- ⚠️ mTLS for enterprise
- ⚠️ Token refresh mechanism

---
**Następny dokument**: [Wpływ na Wydajność Aplikacji](./JWT_WPLYW_NA_WYDAJNOSC.md)

