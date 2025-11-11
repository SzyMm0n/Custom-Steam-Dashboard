# Best Practices i Rekomendacje

## Dla Deweloperów

### 1. Secrets Management

#### ❌ NIGDY:
```python
# Hardcoded secrets
JWT_SECRET = "my-secret-key"
CLIENT_SECRET = "abc123"

# Commited to git
git add .env
git commit -m "Add configuration"
```

#### ✅ ZAWSZE:
```python
# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET")

# .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore

# Generate strong secrets
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Secret Rotation Strategy

```python
# server/security.py

# Support multiple JWT secrets for rotation
JWT_SECRETS = [
    os.getenv("JWT_SECRET_CURRENT"),      # Active
    os.getenv("JWT_SECRET_PREVIOUS"),     # Being phased out
]

def verify_jwt(token: str) -> Dict:
    """Try each secret (current first, then previous)"""
    for secret in JWT_SECRETS:
        if not secret:
            continue
        try:
            return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        except jwt.InvalidTokenError:
            continue
    
    raise HTTPException(401, "Invalid token")

# Rotation process:
# 1. Add new secret as JWT_SECRET_CURRENT
# 2. Move old to JWT_SECRET_PREVIOUS
# 3. Wait for all tokens to expire (20 min)
# 4. Remove JWT_SECRET_PREVIOUS
```

### 3. Logging Best Practices

#### ❌ NIGDY loguj secrets:
```python
# BAD!
logger.info(f"Client secret: {client_secret}")
logger.debug(f"JWT token: {token}")
logger.info(f"Signature: {signature}")
```

#### ✅ Log tylko metadata:
```python
# GOOD
logger.info(f"JWT created for client: {client_id[:8]}...")  # First 8 chars only
logger.debug(f"Signature verified for client: {client_id[:8]}...")
logger.warning(f"Invalid signature from client: {client_id[:8]}...")
```

### 4. Error Messages

#### ❌ Zbytnio szczegółowe (info leak):
```python
# BAD - reveals too much
raise HTTPException(401, "Expected signature: ABC123..., got: XYZ789...")
raise HTTPException(401, "Client secret incorrect for client_id=desktop-main")
```

#### ✅ Ogólne i bezpieczne:
```python
# GOOD
raise HTTPException(401, "Invalid signature")
raise HTTPException(401, "Authentication failed")
raise HTTPException(403, "Unknown client_id")
```

### 5. Testing

```python
# tests/test_auth.py

import pytest
from fastapi.testclient import TestClient

def test_login_success():
    """Test successful login with valid credentials"""
    client = TestClient(app)
    
    # Generate valid signature
    signature_headers = sign_request("POST", "/auth/login", body)
    
    response = client.post(
        "/auth/login",
        json={"client_id": "test-client"},
        headers=signature_headers
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_signature():
    """Test login fails with invalid signature"""
    response = client.post(
        "/auth/login",
        json={"client_id": "test-client"},
        headers={"X-Signature": "invalid"}
    )
    
    assert response.status_code == 401

def test_replay_attack():
    """Test nonce prevents replay attacks"""
    headers = sign_request("GET", "/api/games", b"")
    
    # First request succeeds
    response1 = client.get("/api/games", headers=headers)
    assert response1.status_code == 200
    
    # Second request with same nonce fails
    response2 = client.get("/api/games", headers=headers)
    assert response2.status_code == 401
    assert "Nonce already used" in response2.json()["detail"]
```

---

## Dla DevOps / Production

### 1. HTTPS is MANDATORY

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Modern TLS only
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Environment Variables Management

#### Development:
```bash
# .env (local)
JWT_SECRET=dev-secret-not-for-production
CLIENT_SECRET=dev-client-secret
```

#### Production (use Secrets Manager):

**AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
    --name /prod/steam-dashboard/jwt-secret \
    --secret-string "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Retrieve in app
import boto3

secrets_client = boto3.client('secretsmanager')
response = secrets_client.get_secret_value(SecretId='/prod/steam-dashboard/jwt-secret')
JWT_SECRET = response['SecretString']
```

**Docker Secrets:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    image: steam-dashboard:latest
    secrets:
      - jwt_secret
      - client_secrets
    environment:
      JWT_SECRET_FILE: /run/secrets/jwt_secret
      CLIENTS_JSON_FILE: /run/secrets/client_secrets

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  client_secrets:
    file: ./secrets/clients.json
```

**Kubernetes Secrets:**
```bash
# Create secret
kubectl create secret generic steam-dashboard-secrets \
    --from-literal=jwt-secret=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))') \
    --from-file=clients-json=./clients.json

# Use in pod
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: api
    envFrom:
    - secretRef:
        name: steam-dashboard-secrets
```

### 3. Monitoring & Alerting

```python
# server/monitoring.py

from prometheus_client import Counter, Histogram

# Metrics
auth_requests_total = Counter(
    'auth_requests_total',
    'Total authentication requests',
    ['status', 'client_id']
)

auth_duration_seconds = Histogram(
    'auth_duration_seconds',
    'Time spent in authentication',
    ['operation']
)

signature_verification_failures = Counter(
    'signature_verification_failures_total',
    'Failed signature verifications',
    ['reason']
)

# Usage
@auth_duration_seconds.time()
def verify_request_signature(...):
    try:
        # ... verification logic
        auth_requests_total.labels(status='success', client_id=client_id).inc()
    except HTTPException as e:
        reason = e.detail
        signature_verification_failures.labels(reason=reason).inc()
        auth_requests_total.labels(status='failure', client_id='unknown').inc()
        raise
```

**Grafana Dashboard:**
```yaml
# dashboard.json
{
  "title": "Authentication Metrics",
  "panels": [
    {
      "title": "Auth Success Rate",
      "targets": [{
        "expr": "rate(auth_requests_total{status='success'}[5m]) / rate(auth_requests_total[5m])"
      }]
    },
    {
      "title": "Signature Verification Failures",
      "targets": [{
        "expr": "rate(signature_verification_failures_total[5m])"
      }]
    }
  ]
}
```

**Alerts:**
```yaml
# alerts.yml
groups:
- name: auth
  rules:
  - alert: HighAuthFailureRate
    expr: rate(auth_requests_total{status='failure'}[5m]) > 10
    for: 5m
    annotations:
      summary: "High authentication failure rate"
      description: "{{ $value }} failed auth requests per second"
  
  - alert: PossibleReplayAttack
    expr: rate(signature_verification_failures_total{reason=~'.*Nonce.*'}[1m]) > 5
    for: 1m
    annotations:
      summary: "Possible replay attack detected"
```

### 4. Rate Limiting Configuration

```python
# Production rate limits (stricter)
RATE_LIMITS = {
    "login": "5/minute",           # Max 5 login attempts per minute
    "api_read": "100/minute",      # Max 100 GET requests per minute
    "api_write": "30/minute",      # Max 30 POST/PUT/DELETE per minute
}

@app.post("/auth/login")
@limiter.limit(RATE_LIMITS["login"])
async def login(...):
    ...

@app.get("/api/games")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_games(...):
    ...
```

### 5. Database for Nonce Cache (Production)

```python
# server/security_production.py

import redis.asyncio as redis

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

async def _check_and_store_nonce(nonce: str) -> bool:
    """
    Redis-based nonce check (distributed, persistent).
    
    Uses SET NX (set if not exists) with expiry in one atomic operation.
    """
    result = await redis_client.set(
        f"nonce:{nonce}",
        "1",
        nx=True,        # Only set if doesn't exist
        ex=300          # Expire after 5 minutes
    )
    return result is True  # True if new, False if existed

# Cleanup not needed - Redis TTL handles it automatically!
```

### 6. Health Checks

```python
@app.get("/health")
async def health_check():
    """
    Comprehensive health check.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database
    try:
        await db.execute("SELECT 1")
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Redis (nonce cache)
    try:
        await redis_client.ping()
        health["checks"]["redis"] = "ok"
    except Exception as e:
        health["checks"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"  # Can work without Redis
    
    # JWT secret configured
    if not JWT_SECRET or JWT_SECRET == "insecure-default-change-me":
        health["checks"]["jwt_secret"] = "not configured"
        health["status"] = "unhealthy"
    else:
        health["checks"]["jwt_secret"] = "ok"
    
    # Nonce cache size (if in-memory)
    if not redis_client:
        health["checks"]["nonce_cache_size"] = len(_nonce_cache)
    
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(health, status_code=status_code)
```

### 7. Backup & Disaster Recovery

```bash
#!/bin/bash
# backup_secrets.sh

# Backup secrets to encrypted archive
tar czf secrets-backup-$(date +%Y%m%d).tar.gz \
    .env \
    /path/to/jwt_secret \
    /path/to/client_secrets

# Encrypt backup
gpg --encrypt --recipient admin@example.com secrets-backup-*.tar.gz

# Upload to S3 (or other secure storage)
aws s3 cp secrets-backup-*.tar.gz.gpg s3://backups/secrets/

# Cleanup local copies
rm secrets-backup-*.tar.gz*
```

---

## Dla Użytkowników / Administratorów

### 1. Bezpieczne Przechowywanie Credentials

#### Desktop App:

**macOS (Keychain):**
```python
import keyring

# Store
keyring.set_password("steam_dashboard", "client_secret", secret)

# Retrieve
secret = keyring.get_password("steam_dashboard", "client_secret")
```

**Windows (Credential Manager):**
```python
import keyring

# Same API works across platforms
keyring.set_password("steam_dashboard", "client_secret", secret)
secret = keyring.get_password("steam_dashboard", "client_secret")
```

**Linux (Secret Service):**
```bash
# Install
sudo apt-get install gnome-keyring libsecret-1-0

# Python uses same keyring library
```

### 2. Wykrywanie Kompromitacji

#### Symptomy:
- 🚨 Nieznane żądania API w logach
- 🚨 Rate limit exceeded bez użycia app
- 🚨 Logowanie z nieznanych lokalizacji
- 🚨 Nietypowy wzorzec requestów

#### Działania:
1. **Natychmiast zmień credentials:**
   ```bash
   # Generate new secret
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Update .env
   CLIENT_SECRET=<new-secret>
   
   # Restart app
   ```

2. **Sprawdź system na malware:**
   ```bash
   # Linux
   sudo rkhunter --check
   sudo chkrootkit
   
   # Windows
   # Use Windows Defender / Malwarebytes
   
   # macOS
   # Use XProtect / Malwarebytes
   ```

3. **Skontaktuj się z administratorem API**

### 3. Regularne Audyty

```bash
#!/bin/bash
# security_audit.sh

echo "=== Security Audit ==="
echo

# Check .env permissions
echo "1. Checking .env file permissions:"
if [ -f .env ]; then
    perms=$(stat -c "%a" .env)
    if [ "$perms" != "600" ]; then
        echo "   ⚠️  WARNING: .env has permissions $perms (should be 600)"
        echo "   Fix: chmod 600 .env"
    else:
        echo "   ✓ .env permissions OK"
    fi
else
    echo "   ⚠️  .env file not found"
fi

# Check for committed secrets
echo
echo "2. Checking for secrets in git:"
if git log --all --full-history --source -- .env | grep -q .; then
    echo "   ⚠️  WARNING: .env has been committed to git!"
    echo "   Fix: git rm --cached .env && git commit"
else
    echo "   ✓ No secrets in git history"
fi

# Check JWT_SECRET strength
echo
echo "3. Checking JWT_SECRET strength:"
source .env
if [ ${#JWT_SECRET} -lt 32 ]; then
    echo "   ⚠️  WARNING: JWT_SECRET too short (${#JWT_SECRET} chars, min 32)"
else
    echo "   ✓ JWT_SECRET length OK"
fi

echo
echo "=== Audit Complete ==="
```

---

## Dla Różnych Scenariuszy

### 1. Desktop App (Current Use Case)

**Recommended Setup:**
- ✅ In-memory nonce cache (sufficient)
- ✅ Shared CLIENT_SECRET per app (acceptable)
- ✅ JWT TTL: 20 minutes
- ✅ Rate limit: 100/minute per client

```python
# Optimal for desktop
JWT_TTL_SECONDS = 1200  # 20 min
NONCE_CACHE_TYPE = "memory"
RATE_LIMIT = "100/minute"
```

### 2. Mobile App

**Recommended Setup:**
- ✅ Per-device secrets (better than shared)
- ✅ Token refresh mechanism (longer sessions)
- ✅ Biometric authentication (if available)

```python
# Mobile-optimized
JWT_TTL_SECONDS = 900   # 15 min (shorter for mobile)
REFRESH_TOKEN_TTL = 30 * 24 * 3600  # 30 days
REQUIRE_BIOMETRIC = True
```

### 3. Web Browser (SPA)

**Recommended Setup:**
- ⚠️ **HttpOnly cookies** zamiast localStorage (XSS protection)
- ⚠️ **CSRF tokens** (additional layer)
- ⚠️ **SameSite=Strict** cookies

```python
# Web-specific
@app.post("/auth/login")
async def login(response: Response, ...):
    token = create_jwt(client_id)
    
    # Set HttpOnly cookie (can't be accessed by JavaScript)
    response.set_cookie(
        key="access_token",
        value=token["access_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=JWT_TTL_SECONDS
    )
    
    return {"status": "logged in"}
```

### 4. Microservices (Service-to-Service)

**Recommended Setup:**
- ✅ mTLS (strongest auth)
- ✅ Service mesh (Istio, Linkerd)
- ✅ Longer token TTL (internal network)

```python
# Microservices
JWT_TTL_SECONDS = 3600  # 1 hour (internal network)
USE_MTLS = True
SERVICE_MESH = "istio"
```

### 5. Public API (Third-party Developers)

**Recommended Setup:**
- ✅ API keys (nie JWT dla public API)
- ✅ OAuth2 (standard for public APIs)
- ✅ Stricter rate limiting
- ✅ Usage tracking & billing

```python
# Public API
from fastapi_oauth2 import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/public/games")
@limiter.limit("1000/hour")  # Per API key
async def get_games(api_key: str = Depends(oauth2_scheme)):
    # Track usage for billing
    await track_api_usage(api_key, endpoint="/api/public/games")
    ...
```

---

## Checklist Wdrożeniowy

### Pre-Production:

- [ ] JWT_SECRET min 32 bytes random
- [ ] All secrets in env variables (not hardcoded)
- [ ] .env in .gitignore
- [ ] HTTPS enabled (TLS 1.2+)
- [ ] Rate limiting configured
- [ ] Monitoring & alerts setup
- [ ] Health check endpoint
- [ ] Logging configured (no secrets logged)
- [ ] Error messages generic (no info leak)
- [ ] Security audit completed

### Production:

- [ ] Secrets in secrets manager (not .env)
- [ ] HTTPS with valid certificate
- [ ] Redis for nonce cache (if multi-server)
- [ ] Database backups configured
- [ ] Monitoring dashboard live
- [ ] Alert notifications configured
- [ ] Load balancer configured
- [ ] Firewall rules applied
- [ ] Regular security audits scheduled
- [ ] Incident response plan documented

### Post-Production:

- [ ] Monitor auth failure rate
- [ ] Monitor latency metrics
- [ ] Review logs weekly
- [ ] Rotate secrets quarterly
- [ ] Update dependencies monthly
- [ ] Security penetration test annually

---

## Podsumowanie Rekomendacji

### Must-Have (Mandatory):

1. ✅ **HTTPS w produkcji** - Non-negotiable
2. ✅ **Silne sekrety (32+ bytes)** - Generate with `secrets` module
3. ✅ **Secrets w ENV, nie kod** - Never hardcode
4. ✅ **Rate limiting** - Protect against abuse
5. ✅ **Monitoring** - Know when something's wrong

### Should-Have (Recommended):

1. ✅ **Redis dla nonce cache** - If multi-server
2. ✅ **Secrets manager** - AWS/Vault for production
3. ✅ **Regular rotation** - Quarterly secret rotation
4. ✅ **Health checks** - Comprehensive status endpoint
5. ✅ **Alerting** - Automated notifications

### Nice-to-Have (Optional):

1. ⚠️ **mTLS** - Highest security for enterprise
2. ⚠️ **Token refresh** - Better UX for long sessions
3. ⚠️ **Biometric auth** - Mobile/desktop apps
4. ⚠️ **Response signing** - Additional integrity layer
5. ⚠️ **Per-user secrets** - Granular access control

---

## Dalsze Zasoby

### Dokumentacja:
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [jwt.io - JWT Debugger](https://jwt.io/)

### Książki:
- "OAuth 2 in Action" - Justin Richer, Antonio Sanso
- "API Security in Action" - Neil Madden

### Kursy:
- OWASP Top 10 API Security
- Cloud Security Professional (CCSP)

---

**Koniec dokumentacji JWT + HMAC**

Masz teraz kompleksowy przewodnik po systemie autoryzacji! 🎉

