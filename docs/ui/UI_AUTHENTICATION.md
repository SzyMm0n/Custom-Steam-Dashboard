# Dokumentacja Uwierzytelniania UI

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Przegląd

**Plik:** `app/core/services/server_client.py`

System uwierzytelniania GUI z serwerem backend używając JWT + HMAC.

---

## ServerClient

```python
class ServerClient:
    """
    Klient HTTP do komunikacji z serwerem backend.
    
    Features:
        - Automatyczne uwierzytelnianie (JWT)
        - HMAC signing wszystkich żądań
        - Automatic token refresh
        - Retry logic
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client_id = os.getenv("CLIENT_ID", "desktop-main")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self._token = None
        self._session = httpx.AsyncClient()
```

---

## Proces Uwierzytelniania

### 1. Login (przed startem GUI)

```python
async def authenticate(self) -> bool:
    """
    Uwierzytelnia się z serwerem i otrzymuje JWT token.
    
    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        # Prepare login request body
        body = {"client_id": self.client_id}
        
        # Sign request with HMAC
        headers = sign_request(
            method="POST",
            path="/auth/login",
            body=body,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # Send request
        response = await self._session.post(
            f"{self.base_url}/auth/login",
            json=body,
            headers=headers
        )
        
        # Store token
        data = response.json()
        self._token = data["access_token"]
        
        return True
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False
```

### 2. Authenticated Requests

```python
async def get(self, path: str, **kwargs) -> dict:
    """
    Wykonuje GET request z JWT + HMAC.
    
    Automatycznie:
        - Dodaje Authorization header (JWT)
        - Podpisuje request (HMAC)
        - Refresh token jeśli wygasł
    """
    # Add JWT token
    headers = kwargs.get("headers", {})
    headers["Authorization"] = f"Bearer {self._token}"
    
    # Sign request (HMAC)
    signature_headers = sign_request(
        method="GET",
        path=path,
        body=b"",
        client_id=self.client_id,
        client_secret=self.client_secret
    )
    headers.update(signature_headers)
    
    # Send request
    response = await self._session.get(
        f"{self.base_url}{path}",
        headers=headers,
        **kwargs
    )
    
    # Auto-refresh token if expired
    if response.status_code == 401:
        await self.authenticate()
        return await self.get(path, **kwargs)  # Retry
    
    return response.json()
```

---

## HMAC Signing

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
            "X-Nonce": "random-hex",
            "X-Signature": "base64-hmac"
        }
    """
    # Normalize body
    if isinstance(body, dict):
        body_bytes = json.dumps(body, separators=(',', ':')).encode()
    elif isinstance(body, str):
        body_bytes = body.encode()
    else:
        body_bytes = body
    
    # Hash body
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Generate timestamp and nonce
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    
    # Create message
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    
    # Sign with HMAC-SHA256
    signature = hmac.new(
        client_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    
    signature_b64 = base64.b64encode(signature).decode()
    
    return {
        "X-Client-Id": client_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature_b64
    }
```

---

## Startup Sequence

**Plik:** `app/main_server.py`

```python
async def authenticate_with_server(server_url: str) -> bool:
    """
    Uwierzytelnia przed uruchomieniem GUI.
    """
    client = ServerClient(server_url)
    success = await client.authenticate()
    
    if success:
        print("✓ Successfully authenticated")
        return True
    else:
        print("✗ Authentication failed")
        return False

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Authenticate BEFORE showing GUI
    server_url = os.getenv("SERVER_URL", "http://localhost:8000")
    authenticated = loop.run_until_complete(
        authenticate_with_server(server_url)
    )
    
    if not authenticated:
        QMessageBox.critical(None, "Błąd", "Nie można połączyć z serwerem")
        sys.exit(1)
    
    # Show GUI after successful authentication
    window = MainWindow(server_url)
    window.show()
    
    with loop:
        loop.run_forever()
```

---

## Error Handling

### Token Expired

```python
# Automatyczne odświeżanie
if response.status_code == 401:
    logger.warning("Token expired, refreshing...")
    await self.authenticate()
    return await self.get(path, **kwargs)  # Retry
```

### Network Error

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def get(self, path: str, **kwargs):
    # Automatyczne retry (3 próby)
    ...
```

---

## Konfiguracja .env

```env
# Server
SERVER_URL=http://localhost:8000

# Client Credentials (muszą zgadzać się z serwerem)
CLIENT_ID=desktop-main
CLIENT_SECRET=your-client-secret-from-server
```

---

## Bezpieczeństwo

### ✅ Zaimplementowane

- JWT tokens (session management)
- HMAC signatures (request integrity)
- Nonce (anti-replay)
- Timestamp validation (±60 seconds)
- Automatic token refresh
- HTTPS support (produkcja)

### ❌ Nie Przechowuj

- Nie zapisuj tokenów na dysku
- Nie loguj client_secret
- Nie commituj .env do repo

---

## Następne Kroki

- **Security (Server)**: [../server/SERVER_SECURITY.md](../server/SERVER_SECURITY.md)
- **JWT Documentation**: [../JWT_OVERVIEW.md](../JWT_OVERVIEW.md)

