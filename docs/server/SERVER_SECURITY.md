# Dokumentacja Bezpieczeństwa Serwera

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd Systemu](#przegląd-systemu)
2. [JWT (JSON Web Tokens)](#jwt-json-web-tokens)
3. [HMAC Signature](#hmac-signature)
4. [Middleware](#middleware)
5. [Rate Limiting](#rate-limiting)
6. [Konfiguracja](#konfiguracja)
7. [Best Practices](#best-practices)

---

## Przegląd Systemu

System bezpieczeństwa Custom Steam Dashboard wykorzystuje **dwuwarstwowy mechanizm autoryzacji**:

### Warstwa 1: JWT (Session Token)
- ✅ Uwierzytelnia klienta i tworzy sesję
- ✅ Krótki czas życia (domyślnie 20 minut)
- ✅ Zawiera informacje o kliencie (client_id)
- ✅ Podpisany kluczem JWT_SECRET

### Warstwa 2: HMAC Signature
- ✅ Weryfikuje integralność każdego żądania
- ✅ Chroni przed manipulacją danych
- ✅ Zapobiega atakom replay (nonce + timestamp)
- ✅ Podpisuje metodę, ścieżkę, treść i metadane

```
┌─────────────────────────────────────────────────────┐
│                    Client Request                   │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐         ┌────────────────┐
│ JWT Token    │         │ HMAC Signature │
│              │         │                │
│ • client_id  │         │ • Method       │
│ • exp        │         │ • Path         │
│ • iat        │         │ • Body hash    │
│              │         │ • Timestamp    │
│              │         │ • Nonce        │
└──────┬───────┘         └────────┬───────┘
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │  Server Verification  │
      │                       │
      │ 1. Verify JWT         │
      │ 2. Verify HMAC        │
      │ 3. Check nonce        │
      │ 4. Check timestamp    │
      └───────────────────────┘
```

---

## JWT (JSON Web Tokens)

### Struktura Tokena

```json
{
  "sub": "desktop-main",
  "client_id": "desktop-main",
  "iat": 1699876543,
  "exp": 1699877743,
  "type": "access"
}
```

### Generowanie Tokena

**Plik:** `server/security.py`

```python
def create_jwt(client_id: str, extra_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tworzy JWT token dla uwierzytelnionego klienta.
    
    Returns:
        {
            "access_token": "eyJ0eXAi...",
            "token_type": "bearer",
            "expires_in": 1200
        }
    """
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(seconds=JWT_TTL_SECONDS)
    
    claims = {
        "sub": client_id,
        "client_id": client_id,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "type": "access"
    }
    
    token = jwt.encode(claims, JWT_SECRET, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_TTL_SECONDS
    }
```

### Weryfikacja Tokena

```python
def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Weryfikuje JWT token i zwraca payload.
    
    Raises:
        HTTPException: 401 jeśli token jest nieprawidłowy lub wygasł
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
```

### Dependency: require_auth

FastAPI dependency do wymuszenia uwierzytelnienia JWT:

```python
async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """
    Wymusza uwierzytelnienie JWT.
    
    Usage:
        @app.get("/protected")
        async def protected_route(payload: dict = Depends(require_auth)):
            client_id = payload["client_id"]
            return {"message": f"Hello {client_id}"}
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token"
        )
    
    token = credentials.credentials
    return verify_jwt(token)
```

---

## HMAC Signature

### Format Wiadomości

Podpis HMAC jest generowany na podstawie:

```
MESSAGE = METHOD|PATH|BODY_SHA256|TIMESTAMP|NONCE
```

**Przykład:**
```
GET|/api/games|e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|1699876543|a1b2c3d4e5f6
```

### Wymagane Nagłówki

| Nagłówek | Opis | Przykład |
|----------|------|----------|
| `X-Client-Id` | Identyfikator klienta | `desktop-main` |
| `X-Timestamp` | Unix timestamp (sekundy) | `1699876543` |
| `X-Nonce` | Losowy ciąg (min 16 bajtów) | `a1b2c3d4e5f6...` |
| `X-Signature` | Base64 HMAC-SHA256 | `dGVzdHNpZ25hdHVyZQ==` |

### Generowanie Podpisu (Klient)

**Plik:** `app/helpers/signing.py`

```python
def sign_request(
    method: str,
    path: str,
    body: Union[bytes, dict, str],
    client_id: str,
    client_secret: str
) -> Dict[str, str]:
    """
    Generuje nagłówki HMAC dla żądania.
    
    Returns:
        {
            "X-Client-Id": "desktop-main",
            "X-Timestamp": "1699876543",
            "X-Nonce": "a1b2c3d4e5f6...",
            "X-Signature": "base64-signature"
        }
    """
    # Normalizuj body
    if isinstance(body, dict):
        body_bytes = json.dumps(body, separators=(',', ':')).encode('utf-8')
    elif isinstance(body, str):
        body_bytes = body.encode('utf-8')
    else:
        body_bytes = body
    
    # Hash body
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Timestamp i nonce
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    
    # Utwórz wiadomość
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    
    # Podpisz HMAC-SHA256
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

### Weryfikacja Podpisu (Serwer)

**Plik:** `server/security.py`

```python
def verify_signature(
    client_id: str,
    timestamp: str,
    nonce: str,
    signature: str,
    method: str,
    path: str,
    body: bytes
) -> bool:
    """
    Weryfikuje podpis HMAC żądania.
    
    Raises:
        HTTPException: 403 jeśli podpis jest nieprawidłowy
    """
    # 1. Sprawdź czy klient istnieje
    client_secret = CLIENTS_MAP.get(client_id)
    if not client_secret:
        raise HTTPException(
            status_code=403,
            detail=f"Unknown client_id: {client_id}"
        )
    
    # 2. Sprawdź timestamp (±60 sekund)
    try:
        request_time = int(timestamp)
        now = int(time.time())
        if abs(now - request_time) > 60:
            raise HTTPException(
                status_code=403,
                detail="Request timestamp out of acceptable range"
            )
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Invalid timestamp format"
        )
    
    # 3. Sprawdź nonce (anty-replay)
    if not _check_and_store_nonce(nonce):
        raise HTTPException(
            status_code=403,
            detail="Nonce already used (replay attack?)"
        )
    
    # 4. Hash body
    body_hash = hashlib.sha256(body).hexdigest()
    
    # 5. Odtwórz wiadomość
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    
    # 6. Oblicz oczekiwany podpis
    expected_signature = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
    
    # 7. Porównaj (constant-time comparison)
    if not hmac.compare_digest(signature, expected_signature_b64):
        raise HTTPException(
            status_code=403,
            detail="Invalid signature"
        )
    
    return True
```

### Ochrona Anty-Replay

System wykorzystuje **cache nonce** do zapobiegania atakom powtórzenia:

```python
# In-memory cache z TTL
_nonce_cache: OrderedDict[str, float] = OrderedDict()
_nonce_cache_max_size = 10000  # Max nonces
_nonce_ttl_seconds = 300  # 5 minut

def _check_and_store_nonce(nonce: str) -> bool:
    """
    Sprawdza czy nonce był użyty i zapisuje go.
    
    Returns:
        True jeśli nonce jest nowy, False jeśli był już użyty
    """
    if nonce in _nonce_cache:
        return False  # Replay attack!
    
    _nonce_cache[nonce] = time.time() + _nonce_ttl_seconds
    
    # Ogranicz rozmiar cache (LRU)
    if len(_nonce_cache) > _nonce_cache_max_size:
        _nonce_cache.popitem(last=False)
    
    return True
```

---

## Middleware

### SignatureVerificationMiddleware

Middleware weryfikuje podpisy HMAC dla wszystkich żądań do `/api/*`.

**Plik:** `server/middleware.py`

```python
class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware weryfikujący podpisy HMAC dla endpointów /api/*.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Pomiń weryfikację dla endpointów publicznych
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Pobierz nagłówki
        client_id = request.headers.get("X-Client-Id")
        timestamp = request.headers.get("X-Timestamp")
        nonce = request.headers.get("X-Nonce")
        signature = request.headers.get("X-Signature")
        
        # Sprawdź czy wszystkie nagłówki są obecne
        if not all([client_id, timestamp, nonce, signature]):
            return JSONResponse(
                status_code=403,
                content={"detail": "Missing signature headers"}
            )
        
        # Odczytaj body
        body = await request.body()
        
        # Weryfikuj podpis
        try:
            verify_signature(
                client_id=client_id,
                timestamp=timestamp,
                nonce=nonce,
                signature=signature,
                method=request.method,
                path=request.url.path,
                body=body
            )
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        # Przekaż żądanie dalej
        return await call_next(request)
```

---

## Rate Limiting

### Konfiguracja

System używa **slowapi** do rate limitingu:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limit per client_id (not IP)
def rate_limit_key(request: Request) -> str:
    """
    Klucz rate limitingu bazowany na client_id z JWT.
    Fallback do IP jeśli JWT nie jest dostępny.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return f"client:{payload['client_id']}"
    except Exception:
        pass
    
    return get_remote_address(request)

limiter = Limiter(key_func=rate_limit_key, default_limits=["100/minute"])
```

### Użycie w Endpointach

```python
@app.get("/api/games")
@limiter.limit("30/minute")  # Limit specyficzny dla endpointu
async def get_games(request: Request, ...):
    ...
```

---

## Konfiguracja

### Zmienne Środowiskowe

```env
# JWT Configuration
JWT_SECRET=your-jwt-secret-min-32-bytes-recommended-64
JWT_TTL_SECONDS=1200

# Client Credentials (JSON)
CLIENTS_JSON={"desktop-main":"client-secret-here"}
```

### Generowanie Sekretów

```bash
# JWT Secret (64 bajty)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Client Secret (32 bajty)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Best Practices

### Produkcja

1. ✅ **HTTPS Only** - Zawsze używaj TLS/SSL
2. ✅ **Silne sekrety** - Min 32 bajty (zalecane 64)
3. ✅ **Rotacja sekretów** - Regularnie zmieniaj JWT_SECRET
4. ✅ **CORS** - Ogranicz origins do zaufanych domen
5. ✅ **Firewall** - Ogranicz dostęp do portu serwera
6. ✅ **Monitoring** - Loguj nieudane próby uwierzytelnienia

### Development

1. ✅ Używaj `.env` (nigdy nie commituj)
2. ✅ Różne sekrety dla dev/prod
3. ✅ Test rate limiting lokalnie

### Bezpieczeństwo

1. ✅ **Nonce cache** - Chroni przed replay attacks
2. ✅ **Timestamp validation** - ±60 sekund tolerance
3. ✅ **Constant-time comparison** - `hmac.compare_digest()`
4. ✅ **JWT expiry** - Krótki TTL (20 minut)
5. ✅ **Client secrets** - Przechowywane bezpiecznie w ENV

---

## Pełna Dokumentacja

- [AUTH_AND_SIGNING_README.md](../security/AUTH_AND_SIGNING_README.md) - Pełny przewodnik
- [JWT_OVERVIEW.md](../jwt/JWT_OVERVIEW.md) - Przegląd JWT
- [JWT_BEST_PRACTICES.md](../jwt/JWT_BEST_PRACTICES.md) - Best practices

