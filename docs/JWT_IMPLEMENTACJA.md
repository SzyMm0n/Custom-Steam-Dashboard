# Implementacja JWT + HMAC w Custom Steam Dashboard

## Architektura Systemu

Nasz system używa **dwuwarstwowej autoryzacji**:

1. **JWT (Warstwa Sesji)** - Zarządzanie stanem autoryzacji
2. **HMAC-SHA256 (Warstwa Żądań)** - Weryfikacja integralności każdego request

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL-LAYER SECURITY                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: JWT (Session Management)                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ • Krótkotrwałe tokeny (20 min)                 │         │
│  │ • Stateless authentication                     │         │
│  │ • Client identification                        │         │
│  │ • Automatic expiration                         │         │
│  └────────────────────────────────────────────────┘         │
│                         ↓                                   │
│  Layer 2: HMAC Request Signing                              │
│  ┌────────────────────────────────────────────────┐         │
│  │ • Każde żądanie podpisane                      │         │
│  │ • Anti-replay (nonce + timestamp)              │         │
│  │ • Request integrity verification               │         │
│  │ • Protection against tampering                 │         │
│  └────────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Dlaczego JWT + HMAC?

### Samodzielny JWT nie wystarcza, ponieważ:
- ❌ Brak ochrony przed replay attacks (można przechwycić i wielokrotnie użyć)
- ❌ Nie weryfikuje integralności request body
- ❌ Nie chroni przed man-in-the-middle (jeśli nie HTTPS)
- ❌ Długi TTL = większe okno ataku

### HMAC signing dodaje:
- ✅ Weryfikację każdego żądania (nie tylko sesji)
- ✅ Anti-replay protection (nonce)
- ✅ Timestamp validation (żądania max 60s stare)
- ✅ Body integrity (hash SHA-256 body w podpisie)

## Komponenty Implementacji

### Serwer

#### 1. `server/security.py` - Core Security Logic

**Funkcje JWT:**

```python
def create_jwt(client_id: str, extra_claims: Optional[Dict] = None) -> Dict:
    """
    Generuje JWT token dla uwierzytelnionego klienta.
    
    Proces:
    1. Tworzy payload z claims (sub, client_id, iat, exp, type)
    2. Podpisuje za pomocą HMAC-SHA256 i JWT_SECRET
    3. Zwraca token + metadata (expires_in)
    
    TTL: 20 minut (JWT_TTL_SECONDS)
    Algorytm: HS256 (HMAC-SHA256)
    """
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(seconds=JWT_TTL_SECONDS)
    
    payload = {
        "sub": client_id,           # Subject - identyfikator klienta
        "client_id": client_id,     # Custom claim
        "iat": now,                 # Issued at
        "exp": expiry,              # Expiration
        "type": "access"            # Token type
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_TTL_SECONDS
    }
```

**Funkcje HMAC:**

```python
def compute_signature(
    client_secret: str,
    method: str,
    path: str,
    body_hash: str,
    timestamp: str,
    nonce: str
) -> str:
    """
    Oblicza HMAC-SHA256 podpis żądania.
    
    Format podpisu:
    HMAC-SHA256(secret, "METHOD|PATH|SHA256(body)|timestamp|nonce")
    
    Przykład message:
    "GET|/api/games|e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|1736623443|a1b2c3d4..."
    """
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    signature = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')
```

**Anti-Replay Protection:**

```python
# In-memory nonce cache (OrderedDict dla LRU)
_nonce_cache: OrderedDict[str, float] = OrderedDict()

def _check_and_store_nonce(nonce: str) -> bool:
    """
    Sprawdza czy nonce był już użyty (replay attack).
    
    Mechanizm:
    1. Sprawdza czy nonce w cache
    2. Jeśli TAK → zwraca False (replay!)
    3. Jeśli NIE → dodaje do cache z TTL 5 min
    4. Limit cache: 10,000 entries (LRU eviction)
    """
    _cleanup_expired_nonces()
    
    if nonce in _nonce_cache:
        return False  # Replay attack!
    
    _nonce_cache[nonce] = time.time() + _nonce_ttl_seconds
    
    if len(_nonce_cache) > _nonce_cache_max_size:
        _nonce_cache.popitem(last=False)  # Remove oldest
    
    return True
```

**Weryfikacja Request:**

```python
def verify_request_signature(
    method: str,
    path: str,
    body: bytes,
    x_client_id: Optional[str],
    x_timestamp: Optional[str],
    x_nonce: Optional[str],
    x_signature: Optional[str]
) -> str:
    """
    Kompleksowa weryfikacja HMAC signature.
    
    Kroki:
    1. ✓ Wszystkie wymagane nagłówki obecne
    2. ✓ Client_id istnieje w CLIENTS_MAP
    3. ✓ Timestamp w oknie ±60 sekund
    4. ✓ Nonce nie był użyty (anti-replay)
    5. ✓ Podpis HMAC pasuje
    
    Rzuca HTTPException jeśli cokolwiek się nie zgadza.
    """
    # 1. Check headers
    if not all([x_client_id, x_timestamp, x_nonce, x_signature]):
        raise HTTPException(401, "Missing signature headers")
    
    # 2. Verify client exists
    if x_client_id not in CLIENTS_MAP:
        raise HTTPException(403, "Unknown client_id")
    
    # 3. Verify timestamp (±60s window)
    request_timestamp = int(x_timestamp)
    now = int(time.time())
    time_diff = abs(now - request_timestamp)
    
    if time_diff > 60:
        raise HTTPException(401, f"Timestamp too old: {time_diff}s")
    
    # 4. Verify nonce (anti-replay)
    if not _check_and_store_nonce(x_nonce):
        raise HTTPException(401, "Nonce already used")
    
    # 5. Verify HMAC signature
    body_hash = hashlib.sha256(body).hexdigest()
    client_secret = CLIENTS_MAP[x_client_id]
    expected_signature = compute_signature(
        client_secret, method, path, body_hash, x_timestamp, x_nonce
    )
    
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(401, "Invalid signature")
    
    return x_client_id
```

**FastAPI Dependencies:**

```python
async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """
    Dependency: Wymaga tylko JWT (bez HMAC).
    Używane dla /docs, /redoc, /openapi.json
    """
    if not credentials:
        raise HTTPException(401, "Missing token")
    
    payload = verify_jwt(credentials.credentials)
    return payload


async def require_session_and_signed_request(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_client_id: Optional[str] = Header(None, alias="X-Client-Id"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> str:
    """
    Dependency: Wymaga JWT + HMAC.
    Używane dla wszystkich /api/** endpointów.
    
    Weryfikuje:
    1. JWT token obecny i ważny
    2. X-Client-Id w nagłówku pasuje do client_id w JWT
    3. HMAC signature (w middleware)
    """
    if not credentials:
        raise HTTPException(401, "Missing token")
    
    jwt_payload = verify_jwt(credentials.credentials)
    jwt_client_id = jwt_payload.get("client_id")
    
    if x_client_id != jwt_client_id:
        raise HTTPException(401, "Client ID mismatch")
    
    return jwt_client_id
```

#### 2. `server/auth_routes.py` - Authentication Endpoint

```python
@router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """
    Endpoint logowania - wydaje JWT token.
    
    Proces:
    1. Odbiera client_id w body
    2. Weryfikuje HMAC signature (X-* headers)
    3. Sprawdza czy client_id istnieje w CLIENTS_MAP
    4. Generuje JWT token
    5. Zwraca token + expires_in
    
    Wymagane nagłówki:
    - X-Client-Id: desktop-main
    - X-Timestamp: 1736623443
    - X-Nonce: a1b2c3d4e5f6...
    - X-Signature: base64(HMAC-SHA256(...))
    """
    # Extract signature headers
    x_client_id = request.headers.get("X-Client-Id")
    x_timestamp = request.headers.get("X-Timestamp")
    x_nonce = request.headers.get("X-Nonce")
    x_signature = request.headers.get("X-Signature")
    
    # Get request body for signature verification
    body = await request.body()
    
    # Verify HMAC signature
    verified_client_id = verify_request_signature(
        method=request.method,
        path=request.url.path,
        body=body,
        x_client_id=x_client_id,
        x_timestamp=x_timestamp,
        x_nonce=x_nonce,
        x_signature=x_signature
    )
    
    # Verify body client_id matches header client_id
    if login_data.client_id != verified_client_id:
        raise HTTPException(400, "Client ID mismatch")
    
    # Create JWT token
    token_data = create_jwt(verified_client_id)
    
    return LoginResponse(**token_data)
```

#### 3. `server/middleware.py` - Automatic HMAC Verification

```python
class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware weryfikujący HMAC podpisy na chronionych endpointach.
    
    Chronione ścieżki: /api/**
    Wykluczone: /auth/, /docs, /redoc, /openapi.json, /, /health
    
    Dla chronionych endpointów:
    1. Ekstraktuje nagłówki X-*
    2. Cache'uje request body
    3. Wywołuje verify_request_signature()
    4. Przechowuje verified_client_id w request.state
    """
    
    PROTECTED_PATHS = ["/api/"]
    EXEMPT_PATHS = ["/auth/", "/docs", "/redoc", "/openapi.json", "/", "/health"]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Check if requires signature
        requires_signature = any(path.startswith(p) for p in self.PROTECTED_PATHS)
        is_exempt = any(path.startswith(p) for p in self.EXEMPT_PATHS)
        
        if is_exempt or not requires_signature:
            return await call_next(request)
        
        # Verify signature
        try:
            x_client_id = request.headers.get("X-Client-Id")
            x_timestamp = request.headers.get("X-Timestamp")
            x_nonce = request.headers.get("X-Nonce")
            x_signature = request.headers.get("X-Signature")
            
            body = await request.body()
            
            # Store body for later use (FastAPI może czytać tylko raz)
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
            
            # Verify
            verified_client_id = verify_request_signature(
                method=request.method,
                path=path,
                body=body,
                x_client_id=x_client_id,
                x_timestamp=x_timestamp,
                x_nonce=x_nonce,
                x_signature=x_signature
            )
            
            request.state.verified_client_id = verified_client_id
            
            return await call_next(request)
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
```

#### 4. `server/app.py` - Integration

```python
# Load .env BEFORE imports (critical!)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from security import require_auth, require_session_and_signed_request, rate_limit_key
from middleware import SignatureVerificationMiddleware
import auth_routes

# Create app
app = FastAPI(...)

# Add middleware (порядок ważny!)
app.add_middleware(SignatureVerificationMiddleware)

# Register auth router
app.include_router(auth_routes.router)

# Protect documentation
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(payload: dict = Depends(require_auth)):
    # Only accessible with valid JWT
    return get_swagger_ui_html(...)

# Protect API endpoints
@app.get("/api/games")
async def get_games(
    request: Request,
    client_id: str = Depends(require_session_and_signed_request)
):
    # Requires JWT + HMAC signature
    games = await db.get_all_games()
    return {"games": games}

# Rate limiting per client_id
limiter = Limiter(key_func=rate_limit_key, default_limits=["100/minute"])
```

### Klient (GUI)

#### 1. `app/helpers/signing.py` - HMAC Signature Generation

```python
def sign_request(
    method: str,
    path: str,
    body: Optional[bytes] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Dict[str, str]:
    """
    Generuje nagłówki podpisu HMAC dla żądania.
    
    Proces:
    1. Pobiera credentials z ENV (jeśli nie podane)
    2. Generuje timestamp (Unix seconds)
    3. Generuje nonce (32 bytes hex)
    4. Oblicza hash SHA-256 body
    5. Tworzy message: METHOD|PATH|body_hash|timestamp|nonce
    6. Oblicza HMAC-SHA256(message, client_secret)
    7. Koduje base64
    
    Zwraca nagłówki:
    - X-Client-Id
    - X-Timestamp
    - X-Nonce
    - X-Signature
    """
    if client_id is None or client_secret is None:
        client_id, client_secret = get_client_credentials()
    
    if body is None:
        body = b""
    
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(32)  # 64 chars hex = 32 bytes
    
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    
    signature = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    return {
        "X-Client-Id": client_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature_b64
    }
```

#### 2. `app/helpers/api_client.py` - Authenticated HTTP Client

```python
class AuthenticatedAPIClient:
    """
    HTTP client z automatyczną autoryzacją JWT + HMAC.
    
    Features:
    - Automatyczny login przy pierwszym żądaniu
    - Przechowywanie i refresh JWT token
    - Automatyczne podpisywanie HMAC każdego żądania
    - Transparentna obsługa wygasłych tokenów
    """
    
    async def login(self) -> bool:
        """
        Uwierzytelnia klienta i otrzymuje JWT token.
        
        Proces:
        1. Przygotowuje body: {"client_id": "desktop-main"}
        2. Serializuje JSON (dokładne bajty!)
        3. Generuje HMAC signature
        4. POST /auth/login z body + signature headers
        5. Otrzymuje JWT token
        6. Przechowuje token + expiry time
        """
        path = "/auth/login"
        body_data = {"client_id": self._client_id}
        body_bytes = json.dumps(body_data).encode('utf-8')
        
        # Sign request
        signature_headers = sign_request(
            method="POST",
            path=path,
            body=body_bytes,
            client_id=self._client_id,
            client_secret=self._client_secret
        )
        
        signature_headers["Content-Type"] = "application/json"
        
        # CRITICAL: Wysyłamy dokładnie te same bajty co podpisane!
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                urljoin(self.base_url, path),
                content=body_bytes,  # NIE json=body_data!
                headers=signature_headers
            )
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data["access_token"]
            
            expires_in = data.get("expires_in", 1200)
            self._token_expires_at = int(time.time()) + expires_in - 60  # Buffer 60s
            
            return True
    
    async def ensure_authenticated(self):
        """Automatycznie loguje jeśli token wygasł."""
        if not self.is_authenticated():
            success = await self.login()
            if not success:
                raise Exception("Failed to authenticate")
    
    def _build_headers(self, method: str, path: str, body: Optional[bytes] = None) -> Dict[str, str]:
        """
        Buduje nagłówki z JWT + HMAC signature.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        
        signature_headers = sign_request(
            method=method,
            path=path,
            body=body if body else b"",
            client_id=self._client_id,
            client_secret=self._client_secret
        )
        headers.update(signature_headers)
        
        return headers
    
    async def get(self, path: str) -> Optional[Dict[str, Any]]:
        """GET request z auto-auth."""
        await self.ensure_authenticated()
        headers = self._build_headers("GET", path)
        # ... httpx.get(url, headers=headers)
    
    async def post(self, path: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """POST request z auto-auth."""
        await self.ensure_authenticated()
        body_bytes = json.dumps(data).encode('utf-8') if data else b""
        headers = self._build_headers("POST", path, body_bytes)
        # ... httpx.post(url, content=body_bytes, headers=headers)
```

#### 3. `app/core/services/server_client.py` - High-Level API

```python
class ServerClient:
    """
    Wysokopoziomowy wrapper dla API z autoryzacją.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        # Każdy ServerClient ma swoją instancję AuthenticatedAPIClient
        self._api_client = AuthenticatedAPIClient(base_url)
    
    async def authenticate(self) -> bool:
        """Must be called before using API."""
        return await self._api_client.login()
    
    async def get_current_players(self) -> List[Dict[str, Any]]:
        """Transparentnie używa uwierzytelnionego klienta."""
        data = await self._api_client.get("/api/current-players")
        return data.get("games", []) if data else []
    
    async def get_best_deals(self, limit: int = 20, min_discount: int = 20) -> List[Dict[str, Any]]:
        """Deals endpoint - również chroniony."""
        data = await self._api_client.get(
            f"/api/deals/best?limit={limit}&min_discount={min_discount}"
        )
        return data.get("deals", []) if data else []
```

#### 4. `app/main_server.py` - Application Entry Point

```python
async def authenticate_with_server(server_url: str) -> bool:
    """
    Uwierzytelnia PRZED pokazaniem GUI.
    Jeśli fail → pokazuje error dialog i wychodzi.
    """
    try:
        client = ServerClient(server_url)
        success = await client.authenticate()
        if success:
            print("✓ Successfully authenticated")
            return True
        else:
            print("✗ Failed to authenticate")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main_coro(app, server_url: str):
    """Main coroutine z pre-auth."""
    
    # Step 1: Authenticate FIRST
    auth_success = await authenticate_with_server(server_url)
    
    if not auth_success:
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Authentication Failed")
        msg.setText("Failed to authenticate with server.")
        msg.exec()
        return False
    
    # Step 2: Create and show window
    window = MainWindow(server_url)
    window.show()
    
    # ... event loop
```

## Przepływ Autoryzacji - Kompletny Przykład

### 1. Startup GUI

```
GUI Start
  ↓
load_dotenv()  # Załaduj CLIENT_ID, CLIENT_SECRET
  ↓
ServerClient.__init__()
  ↓
AuthenticatedAPIClient.__init__()  # Nie loguje jeszcze!
  ↓
authenticate_with_server()  # Wywołuje login()
  ↓
POST /auth/login + HMAC signature
  ↓
Serwer: verify_request_signature() ✓
  ↓
Serwer: create_jwt() → return token
  ↓
Klient: Store token + expiry
  ↓
Show MainWindow ✓
```

### 2. API Request (np. get games)

```
GUI: get_current_players()
  ↓
ServerClient.get_current_players()
  ↓
AuthenticatedAPIClient.get("/api/current-players")
  ↓
ensure_authenticated()  # Sprawdza czy token valid
  ├─ Token OK → continue
  └─ Token expired → login() → continue
  ↓
_build_headers("GET", "/api/current-players", body=b"")
  ├─ Authorization: Bearer eyJ0eXAiOiJKV1Qi...
  ├─ X-Client-Id: desktop-main
  ├─ X-Timestamp: 1736623443
  ├─ X-Nonce: a1b2c3d4e5f6...
  └─ X-Signature: base64(HMAC-SHA256(...))
  ↓
httpx.get(url, headers=headers)
  ↓
Serwer: Middleware → verify_request_signature() ✓
  ↓
Serwer: Dependency → verify_jwt() ✓
  ↓
Serwer: Rate limiter (per client_id) ✓
  ↓
Serwer: Execute endpoint → return data
  ↓
Klient: Receive response
  ↓
GUI: Display data ✓
```

## Konfiguracja (Environment Variables)

### Serwer `.env`:
```env
# JWT Configuration
JWT_SECRET=<32+ bytes random>              # KRYTYCZNE!
JWT_TTL_SECONDS=1200                       # 20 minut

# Client Credentials Map
CLIENTS_JSON={"desktop-main": "<secret>"}  # JSON map client_id → secret
```

### Klient `.env`:
```env
# Must match server configuration
CLIENT_ID=desktop-main
CLIENT_SECRET=<ten sam secret co w CLIENTS_JSON>
SERVER_URL=http://localhost:8000
```

### Generowanie Sekretów:

```bash
# JWT Secret (32+ bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Client Secret (32+ bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Monitoring i Debugging

### Logi Serwera:

```python
# Sukces
logger.info(f"JWT created for client: {client_id[:8]}...")
logger.debug(f"Signature verified for client: {client_id[:8]}...")

# Błędy
logger.warning("JWT token expired")
logger.warning(f"Request timestamp too old: {time_diff}s")
logger.warning(f"Nonce replay detected: {nonce[:16]}...")
logger.warning(f"Signature verification failed for client: {client_id[:8]}...")
```

### Logi Klienta:

```python
logger.info(f"Successfully authenticated with server (token expires in {expires_in}s)")
logger.error(f"Login failed with status {status_code}: {response.text}")
logger.error(f"GET {path} failed: {error}")
```

## Podsumowanie Implementacji

### Co zostało zaimplementowane:

✅ **Dual-layer security** (JWT + HMAC)  
✅ **Stateless authentication** (brak sesji w bazie)  
✅ **Auto token refresh** (transparentny dla użytkownika)  
✅ **Anti-replay protection** (nonce cache + timestamp)  
✅ **Rate limiting per client** (nie per IP)  
✅ **Pre-authentication** (GUI nie startuje bez auth)  
✅ **Comprehensive logging** (security events)  
✅ **Environment-based config** (brak hardcoded secrets)  

### Kluczowe Decyzje Projektowe:

1. **JWT + HMAC zamiast samego JWT** - Dual layer eliminuje wiele ataków
2. **Krótki TTL (20 min)** - Minimalizuje okno ataku po kradzieży tokenu
3. **In-memory nonce cache** - Szybkie, wystarczające dla desktop app
4. **HMAC HS256** - Prostsze niż RSA, wystarczające dla trusted client
5. **Middleware verification** - Centralizacja logiki bezpieczeństwa
6. **Pre-authentication GUI** - User nie widzi GUI bez valid auth

---
**Następny dokument**: [Analiza Bezpieczeństwa i Słabe Strony](./JWT_ANALIZA_BEZPIECZENSTWA.md)

