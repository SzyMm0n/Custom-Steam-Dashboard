# JWT + HMAC - Quick Reference Card

## 📌 Kluczowe Informacje

### Architektura
```
┌─────────────────────────────────────────┐
│         DUAL-LAYER SECURITY             │
├─────────────────────────────────────────┤
│  Layer 1: JWT (Session - 20 min)        │
│  Layer 2: HMAC (Request Signing)        │
└─────────────────────────────────────────┘
```

### Wymagane Nagłówki (Request)
```
Authorization: Bearer eyJ0eXAiOiJKV1Qi...
X-Client-Id: desktop-main
X-Timestamp: 1736623443
X-Nonce: a1b2c3d4e5f6...
X-Signature: YWJjZGVmZ2hpams=
```

## 🔧 Konfiguracja

### Environment Variables
```bash
# Server
JWT_SECRET=<32+ bytes random>
JWT_TTL_SECONDS=1200
CLIENTS_JSON={"desktop-main": "<secret>"}

# Client  
CLIENT_ID=desktop-main
CLIENT_SECRET=<secret>
SERVER_URL=http://localhost:8000
```

### Generowanie Sekretów
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🚀 Quick Start

### Client (Python)
```python
from app.helpers.api_client import AuthenticatedAPIClient

client = AuthenticatedAPIClient('http://localhost:8000')
await client.login()  # Get JWT

# All requests auto-signed
games = await client.get('/api/games')
```

### Server (FastAPI)
```python
from security import require_session_and_signed_request

@app.get("/api/games")
async def get_games(
    client_id: str = Depends(require_session_and_signed_request)
):
    return {"games": [...]}
```

## 📊 Performance Impact

| Metric | Impact |
|--------|--------|
| **Latency** | +1-2ms (+1-4%) |
| **Throughput** | -18% RPS |
| **CPU** | +60% compute, +9% total |
| **Memory** | +2MB (+1.6%) |

**Verdict:** ✅ Nieznaczący wpływ na UX

## 🔒 Security Rating

**Overall: 8.5/10** ⭐⭐⭐⭐

### Chronione przed:
- ✅ Replay attacks (nonce + timestamp)
- ✅ Token theft (krótki TTL + dual-layer)
- ✅ Tampering (HMAC signature)
- ✅ Brute force (256-bit secrets)
- ✅ Timing attacks (constant-time comparison)

### Wymagane:
- ⚠️ HTTPS w produkcji (mandatory!)
- ⚠️ Secrets w secrets manager
- ⚠️ Regular rotation (quarterly)

## 🔍 Troubleshooting

### "Invalid signature"
```bash
# Check secrets match
echo $CLIENT_SECRET  # Client
echo $CLIENTS_JSON   # Server

# Check timestamp sync
date +%s  # Should be same ±60s
```

### "Token expired"
```python
# Token expires after 20 min
# Client auto-refreshes transparently
# If fails → check credentials
```

### "Nonce already used"
```bash
# Replay attack detected!
# Each nonce can only be used once
# Generate new nonce per request
```

## 📈 Monitoring

### Key Metrics
```
auth_requests_total{status="success"}
auth_requests_total{status="failure"}
signature_verification_failures_total
auth_duration_seconds
```

### Alerts
```
rate(auth_requests_total{status='failure'}[5m]) > 10
rate(signature_verification_failures_total[1m]) > 5
```

## 🧪 Testing

### Manual Test
```bash
# 1. Start server
cd server && python app.py

# 2. Run auth test
python scripts/test_auth.py

# 3. Test deals
python scripts/test_deals.py
```

### Generate Signature (curl)
```bash
python scripts/generate_signature.py GET /api/games ""
# Copy curl command from output
```

## 📚 Full Documentation

1. [Overview](./JWT_OVERVIEW.md) - Start here
2. [Teoria](./JWT_TEORIA.md) - How JWT works
3. [Implementacja](./JWT_IMPLEMENTACJA.md) - Technical details
4. [Bezpieczeństwo](./JWT_ANALIZA_BEZPIECZENSTWA.md) - Security analysis
5. [Wydajność](./JWT_WPLYW_NA_WYDAJNOSC.md) - Performance impact
6. [Best Practices](./JWT_BEST_PRACTICES.md) - Production guide

## 🆘 Quick Fixes

### Reset Everything
```bash
# 1. Generate new secrets
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CLIENT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Update .env
echo "JWT_SECRET=$JWT_SECRET" >> .env
echo "CLIENT_SECRET=$CLIENT_SECRET" >> .env
echo "CLIENTS_JSON={\"desktop-main\": \"$CLIENT_SECRET\"}" >> .env

# 3. Restart server & client
```

### Emergency Disable Auth (dev only!)
```python
# server/app.py
# Comment out middleware
# app.add_middleware(SignatureVerificationMiddleware)

# Comment out dependencies
# @app.get("/api/games")
# async def get_games():  # Remove Depends(...)
```

## 🎯 Decision Matrix

### Use JWT + HMAC when:
- ✅ Desktop/mobile app
- ✅ Microservices
- ✅ Need stateless auth
- ✅ Cross-domain required

### Consider alternatives when:
- ❌ Need immediate revocation
- ❌ Very short sessions (<5 min)
- ❌ Ultra-low latency critical
- ❌ Simple single-server app

---
**Version:** 1.0.0  
**Last Updated:** 2025-01-11  
**Status:** ✅ Production Ready

