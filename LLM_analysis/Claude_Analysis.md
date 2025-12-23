# Custom Steam Dashboard - Security & Code Analysis Report

**Analysis Date:** 2025-12-23  
**Analyzer:** Claude (Static Code Analysis)  
**Scope:** `app/` and `server/` directories

---

## Executive Summary

This analysis covers the Custom Steam Dashboard application, a desktop GUI application with a FastAPI backend. The application uses JWT + HMAC signature-based authentication, PostgreSQL database, and integrates with Steam and IsThereAnyDeal APIs.

Overall security posture: **Moderate** - The codebase implements several security best practices but has some notable issues that should be addressed.

---

## Findings

### 1. [SECURITY] Insecure Default JWT Secret

**Location:** `server/security.py:35-37`

```python
if not JWT_SECRET or JWT_SECRET == "":
    logger.warning("JWT_SECRET not set! Using insecure default. Set JWT_SECRET in environment!")
    JWT_SECRET = "insecure-default-change-me"
```

**Classification:** Security  
**Confidence:** High  
**Status:** Definite Issue

**Explanation:**  
When `JWT_SECRET` is not set, the application falls back to a hardcoded, predictable secret. This allows an attacker who knows this default to forge valid JWT tokens and impersonate any client. While there's a warning log, the application continues to run with the insecure default.

**Recommendation:**  
The application should **refuse to start** if `JWT_SECRET` is not properly configured in production:
```python
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
```

---

### 2. [SECURITY] Insecure Default Client Secret

**Location:** `server/security.py:28`

```python
CLIENTS_JSON = os.getenv("CLIENTS_JSON", '{"desktop-main": "change-me-in-production"}')
```

**Classification:** Security  
**Confidence:** High  
**Status:** Definite Issue

**Explanation:**  
The default `CLIENTS_JSON` contains a predictable client secret `"change-me-in-production"`. If deployed without proper configuration, this allows attackers to:
1. Compute valid HMAC signatures
2. Authenticate as the desktop client
3. Access all protected API endpoints

**Recommendation:**  
Remove the default secret or fail-fast if the default is detected in production.

---

### 3. [SECURITY] Client Secret Embedded in Executable

**Location:** `app/config.py`

**Classification:** Security  
**Confidence:** High  
**Status:** Definite Issue

**Explanation:**  
The architecture embeds client secrets directly into the PyInstaller executable:

```python
_CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
```

The comments indicate that `generate_config.py` replaces this file with hardcoded values during build. Client secrets embedded in desktop applications can be extracted through:
- Decompilation of Python bytecode (pyinstxtractor + uncompyle6)
- Memory inspection at runtime
- Binary string analysis

**Impact:**  
Anyone with access to the executable can extract the client secret, allowing them to:
- Make authenticated API requests
- Potentially abuse rate limits under the legitimate client identity

**Recommendation:**  
Consider alternative authentication models for desktop applications:
- OAuth2 with device authorization flow
- Per-installation generated secrets
- Challenge-response protocols

---

### 4. [SECURITY] In-Memory Nonce Cache - Not Persistent Across Restarts

**Location:** `server/security.py:44-47`

```python
_nonce_cache: OrderedDict[str, float] = OrderedDict()
_nonce_cache_max_size = 10000
_nonce_ttl_seconds = 300  # 5 minutes
```

**Classification:** Security  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
The nonce cache is stored in memory and will be lost on server restart. This creates a window for replay attacks:
1. Attacker captures a signed request
2. Server restarts (clearing the nonce cache)
3. Attacker replays the captured request with the same nonce

The 60-second timestamp window partially mitigates this, but a quick restart within that window enables replay.

**Recommendation:**  
Consider using Redis or database-backed nonce storage for production deployments with high-security requirements.

---

### 5. [SECURITY] Potential Race Condition in Nonce Validation

**Location:** `server/security.py:56-70`

```python
def _check_and_store_nonce(nonce: str) -> bool:
    _cleanup_expired_nonces()
    
    if nonce in _nonce_cache:
        return False  # Nonce already used (replay attack)
    
    # Store nonce with expiry time
    _nonce_cache[nonce] = time.time() + _nonce_ttl_seconds
    ...
```

**Classification:** Security  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
In a multi-threaded/async environment, there's a potential TOCTOU (Time-of-check-time-of-use) race condition between checking if a nonce exists and storing it. Two concurrent requests with the same nonce could both pass the check before either stores the nonce.

**Note:** FastAPI with uvicorn typically runs in async mode with a single event loop, which may serialize these operations. However, this is not guaranteed in all deployment configurations.

**Recommendation:**  
Use atomic operations or a thread-safe data structure with atomic `setdefault` or similar operations.

---

### 6. [SECURITY] SQL Injection Mitigation - Partial Assessment

**Location:** `server/database/database.py`

**Classification:** Security  
**Confidence:** Medium  
**Status:** Heuristic Suspicion (Need More Context)

**Explanation:**  
The codebase uses asyncpg with parameterized queries (`$1`, `$2`, etc.), which is the correct approach for preventing SQL injection:

```python
await conn.execute("""
    INSERT INTO {self._table('watchlist')} (appid, name, last_count)
    VALUES ($1, $2, $3)
    ...
""", appid, name, last_count)
```

**However**, the `_table()` helper uses f-string interpolation for schema/table names:
```python
def _table(self, table_name: str) -> str:
    return f'"{self.schema}".{table_name}'
```

If `table_name` parameter were ever user-controlled, this would be vulnerable. Currently, all calls use hardcoded table names, so this is **not currently exploitable**.

**Recommendation:**  
Consider validating table names against an allowlist or using a constant enum.

---

### 7. [CORRECTNESS] Inconsistent Body Reading in Middleware

**Location:** `server/middleware.py:65-68`

```python
body = await request.body()

async def receive():
    return {"type": "http.request", "body": body}

request._receive = receive
```

**Classification:** Correctness  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
The middleware reads the request body for signature verification and then replaces `_receive` to allow the body to be read again by route handlers. This is a common pattern but:
1. Modifies private (`_`) attribute
2. May not work correctly with all body types (streaming, chunked)
3. Could cause issues with large request bodies (double memory consumption)

**Recommendation:**  
Consider using FastAPI's built-in `request.state` to store the body, or using a more robust body caching middleware.

---

### 8. [SECURITY] CORS Configuration - Wildcard Port Matching

**Location:** `server/app.py:146-151`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    ...
)
```

**Classification:** Security  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
The wildcard pattern `localhost:*` may not work as expected in all CORS implementations. Some browsers/implementations require exact origin matching. Additionally, this allows any local service on any port to make cross-origin requests.

For a desktop application meant to run locally, this is likely acceptable. However, if the server is exposed on a network, this could allow other local applications (potentially malicious) to make authenticated requests if they can access the user's JWT.

**Recommendation:**  
For local-only usage, consider using `allow_origins=["*"]` with proper authentication, or specify exact ports if known.

---

### 9. [MAINTAINABILITY] Global Mutable State

**Location:** `server/app.py:52-56`

```python
db: Optional[DatabaseManager] = None
steam_client: Optional[SteamClient] = None
deals_client: Optional[IsThereAnyDealClient] = None
scheduler_manager: Optional[SchedulerManager] = None
```

**Classification:** Maintainability  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
Using module-level global variables for state management:
- Makes testing difficult (need to mock globals)
- Can lead to unexpected behavior in multi-worker deployments
- Reduces code clarity about dependencies

**Recommendation:**  
Consider using FastAPI's dependency injection system or `app.state` for managing these instances.

---

### 10. [SECURITY] Error Messages May Leak Information

**Location:** `server/security.py:256-261`

```python
if time_diff > 60:
    logger.warning(f"Request timestamp too old: {time_diff}s difference")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Request timestamp too old (diff: {time_diff}s, max: 60s)"
    )
```

**Classification:** Security  
**Confidence:** Low  
**Status:** Heuristic Suspicion

**Explanation:**  
Error messages reveal exact time differences, which could help attackers fine-tune their attacks. While this specific leak is minimal, it's a pattern that should be avoided.

**Recommendation:**  
Use generic error messages in responses; detailed information should only go to logs.

---

### 11. [CORRECTNESS] Missing Error Handling in Token Refresh

**Location:** `app/helpers/api_client.py:98-105`

```python
async def ensure_authenticated(self):
    if not self.is_authenticated():
        logger.info("Token expired or not authenticated, logging in...")
        success = await self.login()
        if not success:
            raise Exception("Failed to authenticate with server")
```

**Classification:** Correctness  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
Using a generic `Exception` is not ideal for error handling. Callers cannot distinguish between authentication failures, network errors, or server errors.

**Recommendation:**  
Define specific exception types like `AuthenticationError`, `NetworkError`, etc.

---

### 12. [SECURITY] Steam API Key Handling

**Location:** `server/services/steam_service.py:57-60`

```python
self.api_key = os.getenv('STEAM_API_KEY', '')
if not self.api_key:
    logger.error("STEAM_API_KEY not found in environment variables.")
    raise ValueError("STEAM_API_KEY not found in environment variables.")
```

**Classification:** Security  
**Confidence:** Low (Positive Finding)  
**Status:** Good Practice

**Explanation:**  
Unlike JWT_SECRET, the Steam API key properly fails if not configured. This is the correct behavior.

---

### 13. [MAINTAINABILITY] Singleton Pattern with Manual State

**Location:** `app/core/user_data_manager.py:23-32`

```python
class UserDataManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserDataManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

**Classification:** Maintainability  
**Confidence:** Low  
**Status:** Heuristic Suspicion

**Explanation:**  
Manual singleton implementation with `_initialized` flag is fragile and makes testing harder.

**Recommendation:**  
Consider using Python's `functools.lru_cache` on a factory function or a dependency injection framework.

---

### 14. [CORRECTNESS] Potential File Operation Race Condition

**Location:** `app/core/user_data_manager.py:104-112`

```python
def save(self) -> bool:
    try:
        if self._data_file.exists():
            backup_file = self._data_file.with_suffix('.json.bak')
            self._data_file.rename(backup_file)  # Race condition window here
        
        with open(self._data_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
```

**Classification:** Correctness  
**Confidence:** Medium  
**Status:** Heuristic Suspicion

**Explanation:**  
There's a window between renaming the backup and writing the new file where neither file exists. If the application crashes during this window, data could be lost.

**Recommendation:**  
Write to a temporary file first, then atomically replace:
```python
temp_file = self._data_file.with_suffix('.tmp')
with open(temp_file, 'w') as f:
    json.dump(...)
temp_file.replace(self._data_file)
```

---

### 15. [SECURITY] HTML Parsing - ReDoS Potential

**Location:** `server/services/parse_html.py:5-16`

```python
async def parse_html_tags(html_string):
    clean = re.sub(r"<[^>]+>", "", html_string)
    clean = html.unescape(clean)
    clean = re.sub(r"[\r\n\t]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()
```

**Classification:** Security  
**Confidence:** Low  
**Status:** Heuristic Suspicion

**Explanation:**  
The regex patterns used are simple and not vulnerable to catastrophic backtracking. However:
1. The function is marked `async` but contains no async operations (unnecessary)
2. Processing untrusted HTML with regex can have edge cases

**Recommendation:**  
Consider using a proper HTML parser like `BeautifulSoup` with `lxml` for robustness. Remove `async` if not needed.

---

### 16. [CORRECTNESS] Async Function Without Await

**Location:** `server/services/parse_html.py:5`

```python
async def parse_html_tags(html_string):
```

**Classification:** Correctness  
**Confidence:** High  
**Status:** Definite Issue

**Explanation:**  
This function is declared as `async` but contains no `await` statements. This adds unnecessary overhead and is misleading.

**Recommendation:**  
Remove `async` keyword or document why it's needed.

---

### 17. [SECURITY] Clock Skew Leeway May Be Too Generous

**Location:** `server/security.py:131-135`

```python
payload = jwt.decode(
    token,
    JWT_SECRET,
    algorithms=[JWT_ALGORITHM],
    leeway=timedelta(minutes=2)
)
```

**Classification:** Security  
**Confidence:** Low  
**Status:** Heuristic Suspicion

**Explanation:**  
A 2-minute leeway on JWT validation combined with a separate 60-second timestamp window for HMAC creates overlapping time windows. While the intent is to handle clock skew, this extends the attack window for tokens.

**Recommendation:**  
Document the security implications and ensure monitoring for time-based attacks.

---

## Summary Table

| # | Type | Severity | Confidence | Issue |
|---|------|----------|------------|-------|
| 1 | Security | High | High | Insecure default JWT secret |
| 2 | Security | High | High | Insecure default client secret |
| 3 | Security | High | High | Client secret embedded in executable |
| 4 | Security | Medium | Medium | In-memory nonce cache |
| 5 | Security | Medium | Medium | Race condition in nonce validation |
| 6 | Security | Low | Medium | SQL injection (mitigated) |
| 7 | Correctness | Low | Medium | Middleware body reading |
| 8 | Security | Low | Medium | CORS wildcard ports |
| 9 | Maintainability | Low | Medium | Global mutable state |
| 10 | Security | Low | Low | Verbose error messages |
| 11 | Correctness | Low | Medium | Generic exception handling |
| 12 | Security | N/A | N/A | Good practice (Steam API key) |
| 13 | Maintainability | Low | Low | Manual singleton pattern |
| 14 | Correctness | Medium | Medium | File save race condition |
| 15 | Security | Low | Low | HTML parsing with regex |
| 16 | Correctness | Low | High | Async without await |
| 17 | Security | Low | Low | Clock skew leeway |

---

## Recommendations Priority

### Critical (Fix Before Production)
1. Remove insecure default for `JWT_SECRET` - fail if not set
2. Remove insecure default for `CLIENTS_JSON` - fail if not set
3. Reconsider client authentication model for desktop app

### High Priority
4. Implement persistent nonce storage (Redis/Database)
5. Add thread-safe nonce checking

### Medium Priority
6. Refactor global state to use dependency injection
7. Implement atomic file saves
8. Define specific exception types

### Low Priority
9. Clean up async/await usage
10. Reduce verbosity in error messages
11. Consider proper HTML parsing library

---

*Analysis complete. This report is based on static analysis without execution. Some findings may require additional context or runtime testing to confirm.*

