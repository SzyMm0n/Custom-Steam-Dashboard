# Authentication & Request Signing

This document describes the authentication and authorization system implemented in Custom Steam Dashboard.

## Overview

The system uses a dual-layer security approach:
1. **Session Authentication**: JWT tokens for session management
2. **Request Signing**: HMAC-SHA256 signatures on all requests to prevent tampering

## Architecture

### Server Side

- **JWT Authentication**: Short-lived JWT tokens (default: 20 minutes)
- **HMAC Signature Verification**: Every request to `/api/**` endpoints must include valid HMAC signature
- **Rate Limiting**: Per client_id (not per IP)
- **Protected Documentation**: `/docs`, `/redoc`, `/openapi.json` require JWT authentication

### Client Side

- **Automatic Authentication**: Client authenticates on startup before showing main window
- **Automatic Token Refresh**: Tokens are refreshed automatically when expired
- **Transparent Signing**: All API requests are automatically signed with HMAC

## Security Components

### 1. JWT (Session Token)

**Purpose**: Establish authenticated session with the server

**Format**:
```json
{
  "sub": "client_id",
  "client_id": "desktop-main",
  "iat": 1234567890,
  "exp": 1234568090,
  "type": "access"
}
```

**Lifetime**: Configurable via `JWT_TTL_SECONDS` (default: 1200s = 20 minutes)

### 2. HMAC Signature

**Purpose**: Verify request integrity and authenticity

**Algorithm**: HMAC-SHA256

**Message Format**:
```
METHOD|PATH|SHA256(body)|timestamp|nonce
```

**Example**:
```
GET|/api/games|e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|1699876543|a1b2c3d4e5f6...
```

**Required Headers**:
- `X-Client-Id`: Client identifier
- `X-Timestamp`: Unix timestamp (must be within 60 seconds of server time)
- `X-Nonce`: Random string (minimum 16 bytes, used for replay protection)
- `X-Signature`: Base64-encoded HMAC-SHA256 signature

### 3. Anti-Replay Protection

**Mechanism**: Nonce tracking with TTL

- Each nonce can only be used once
- Nonces are cached for 5 minutes
- Cache size limited to 10,000 entries (LRU eviction)

**Timestamp Validation**:
- Request timestamp must be within ±60 seconds of server time
- Prevents replay attacks with old requests

## Configuration

### Environment Variables

#### Server (Required):

```bash
# JWT Secret (CRITICAL - MUST BE CHANGED IN PRODUCTION!)
JWT_SECRET="your-secret-key-here-min-32-bytes"

# JWT Token TTL in seconds
JWT_TTL_SECONDS=1200

# Client Credentials (JSON format)
CLIENTS_JSON='{"desktop-main": "your-client-secret-here"}'
```

#### Client (Required):

```bash
# Client Credentials (must match server configuration)
CLIENT_ID="desktop-main"
CLIENT_SECRET="your-client-secret-here"

# Server URL
SERVER_URL="http://localhost:8000"
```

### Generating Secrets

Use Python to generate secure random secrets:

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate client secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Endpoints

### Authentication Endpoints

#### `POST /auth/login`

Authenticate client and receive JWT token.

**Request**:
```json
{
  "client_id": "desktop-main"
}
```

**Headers** (HMAC signature required):
```
X-Client-Id: desktop-main
X-Timestamp: 1699876543
X-Nonce: a1b2c3d4e5f6...
X-Signature: base64-encoded-signature
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1200
}
```

### Protected Endpoints

All endpoints under `/api/**` require:
1. Valid JWT token in `Authorization: Bearer <token>` header
2. Valid HMAC signature in `X-*` headers

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/games" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "X-Client-Id: desktop-main" \
  -H "X-Timestamp: 1699876543" \
  -H "X-Nonce: a1b2c3d4e5f6..." \
  -H "X-Signature: base64-encoded-signature"
```

## Client Implementation

### Python Client Example

```python
from app.helpers.api_client import get_api_client

# Initialize client
client = get_api_client("http://localhost:8000")

# Authenticate (happens automatically on first request)
await client.login()

# Make authenticated requests
games = await client.get("/api/games")
tags = await client.post("/api/games/tags/batch", {"appids": [730, 440]})
```

### Manual Request Signing (Advanced)

```python
from app.helpers.signing import sign_request
import httpx

# Sign request
headers = sign_request(
    method="GET",
    path="/api/games",
    body=b"",
    client_id="desktop-main",
    client_secret="your-secret"
)

# Add JWT token
headers["Authorization"] = "Bearer your-jwt-token"

# Make request
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/games",
        headers=headers
    )
```

## Testing

### Test Script (Python)

```python
import asyncio
from app.helpers.api_client import AuthenticatedAPIClient

async def test_auth():
    client = AuthenticatedAPIClient("http://localhost:8000")
    
    # Login
    success = await client.login()
    print(f"Login: {'✓' if success else '✗'}")
    
    # Test API call
    games = await client.get("/api/games")
    print(f"Fetch games: {'✓' if games else '✗'}")

asyncio.run(test_auth())
```

### Test with curl

1. **Login** (get JWT token):
```bash
# Generate signature first (use provided script)
python scripts/generate_signature.py POST /auth/login '{"client_id":"desktop-main"}'

# Make request with signature
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: desktop-main" \
  -H "X-Timestamp: 1699876543" \
  -H "X-Nonce: a1b2c3d4..." \
  -H "X-Signature: base64sig..." \
  -d '{"client_id":"desktop-main"}'
```

2. **Access protected endpoint**:
```bash
# Use token from login response
export TOKEN="your-jwt-token"

# Generate signature for GET request
python scripts/generate_signature.py GET /api/games ""

# Make request
curl -X GET "http://localhost:8000/api/games" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Client-Id: desktop-main" \
  -H "X-Timestamp: 1699876544" \
  -H "X-Nonce: b2c3d4e5..." \
  -H "X-Signature: base64sig..."
```

## Security Best Practices

### Development

1. **Never commit secrets** to version control
2. Use `.env` file for local development (copy from `.env.example`)
3. Use default credentials only for local testing

### Production

1. **Generate strong secrets**: Use cryptographically secure random generators
2. **Use HTTPS**: Always use TLS/SSL in production (e.g., Cloudflare Full/Strict mode)
3. **Rotate secrets**: Regularly rotate JWT_SECRET and client secrets
4. **Monitor logs**: Watch for suspicious authentication attempts
5. **Restrict origins**: Configure CORS to allow only trusted origins
6. **Use firewall**: Restrict server port access (e.g., EC2 Security Groups)

### Future Enhancements (Optional)

1. **mTLS**: Add mutual TLS authentication at reverse proxy level
2. **Client ban list**: Implement mechanism to revoke/ban specific client_ids
3. **Database-backed clients**: Move client credentials from ENV to database
4. **Audit logging**: Log all authentication and authorization events
5. **Rate limit per endpoint**: Fine-grained rate limiting rules

## Troubleshooting

### Client can't authenticate

1. Check server is running: `curl http://localhost:8000/health`
2. Verify environment variables are set correctly
3. Check client_id exists in server's CLIENTS_JSON
4. Verify client_secret matches server configuration
5. Check system time synchronization (timestamp validation)

### Signature verification fails

1. Ensure client and server use same secret
2. Check system clocks are synchronized (±60s tolerance)
3. Verify nonce is unique (not reused)
4. Check body encoding (must be identical on client and server)

### Token expired

- Tokens expire after JWT_TTL_SECONDS (default: 20 minutes)
- Client automatically refreshes token on next request
- If refresh fails, client will show authentication error

## Files Reference

### Server

- `server/security.py`: JWT and HMAC signature verification
- `server/auth_routes.py`: Authentication endpoints
- `server/middleware.py`: Signature verification middleware
- `server/app.py`: Main FastAPI application with protected endpoints

### Client

- `app/helpers/signing.py`: HMAC signature generation
- `app/helpers/api_client.py`: Authenticated API client
- `app/core/services/server_client.py`: High-level API wrapper
- `app/main_server.py`: Application entry point with authentication

## License

This authentication system is part of Custom Steam Dashboard and follows the same license.

