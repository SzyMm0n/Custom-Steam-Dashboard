# Dokumentacja Systemu Autentykacji JWT + HMAC

## 📚 Spis Treści

### 1. [Podstawy JWT - Teoria](./JWT_TEORIA.md)
**Czego się dowiesz:**
- Czym jest JWT i jak działa
- Struktura JWT (header, payload, signature)
- Przepływ autoryzacji krok po kroku
- Zalety i wady JWT
- Algorytmy podpisu (HMAC, RSA)
- JWT vs Session Cookies
- Kiedy używać JWT

**Czas czytania:** ~15 minut  
**Poziom:** Początkujący

---

### 2. [Implementacja w Custom Steam Dashboard](./JWT_IMPLEMENTACJA.md)
**Czego się dowiesz:**
- Architektura dual-layer (JWT + HMAC)
- Szczegóły implementacji serwera (security.py, auth_routes.py, middleware.py)
- Szczegóły implementacji klienta (signing.py, api_client.py)
- Przepływ autoryzacji w aplikacji
- Konfiguracja ENV variables
- Monitoring i debugging

**Czas czytania:** ~25 minut  
**Poziom:** Średniozaawansowany

---

### 3. [Analiza Bezpieczeństwa i Słabe Strony](./JWT_ANALIZA_BEZPIECZENSTWA.md)
**Czego się dowiesz:**
- 8 głównych zagrożeń bezpieczeństwa
- Mitygacje zastosowane w implementacji
- Token theft i jak się przed nim bronić
- Replay attacks i anti-replay protection
- In-memory cache vs Redis
- Client secret exposure
- MITM attacks
- Timing attacks

**Czas czytania:** ~20 minut  
**Poziom:** Zaawansowany

**Ocena bezpieczeństwa:** 8.5/10 ⭐⭐⭐⭐

---

### 4. [Wpływ na Wydajność Aplikacji](./JWT_WPLYW_NA_WYDAJNOSC.md)
**Czego się dowiesz:**
- Latency analysis (+1-2ms, +1-4%)
- Throughput impact (-18% RPS)
- CPU usage (+60% computation)
- Memory footprint (+2MB)
- Scalability implications
- Real-world performance tests
- Optimization opportunities

**Czas czytania:** ~15 minut  
**Poziom:** Średniozaawansowany

**Verdict:** ✅ Performance impact akceptowalny

---

### 5. [Best Practices i Rekomendacje](./JWT_BEST_PRACTICES.md)
**Czego się dowiesz:**
- Secrets management (AWS, Docker, Kubernetes)
- Monitoring & alerting (Prometheus, Grafana)
- Production deployment checklist
- Rate limiting strategies
- Health checks
- Backup & disaster recovery
- Rekomendacje dla różnych scenariuszy (desktop, mobile, web, microservices)

**Czas czytania:** ~20 minut  
**Poziom:** DevOps / Production

---

## 🎯 Szybki Start

### Dla Deweloperów
**Chcę szybko zrozumieć jak to działa:**
1. Przeczytaj: [Teoria](./JWT_TEORIA.md) → [Implementacja](./JWT_IMPLEMENTACJA.md)
2. Poświęć: ~40 minut
3. Następnie: Eksperymentuj z kodem

### Dla Security Auditors
**Chcę ocenić bezpieczeństwo:**
1. Przeczytaj: [Analiza Bezpieczeństwa](./JWT_ANALIZA_BEZPIECZENSTWA.md)
2. Sprawdź: Mitygacje vs known attacks
3. Review: `server/security.py`, `middleware.py`

### Dla DevOps
**Chcę wdrożyć na produkcję:**
1. Przeczytaj: [Best Practices](./JWT_BEST_PRACTICES.md)
2. Użyj: Production checklist
3. Setup: Monitoring & secrets manager

### Dla Product Managers
**Chcę wiedzieć czy to wpływa na UX:**
1. Przeczytaj: [Wpływ na Wydajność](./JWT_WPLYW_NA_WYDAJNOSC.md)
2. Kluczowe: +1-2ms latency, nieznaczący wpływ
3. Verdict: ✅ User experience nie ucierpi

---

### Czym jest JWT?

**JWT (JSON Web Token)** to otwarty standard (RFC 7519) definiujący kompaktowy i samowystarczalny sposób bezpiecznego przesyłania informacji między stronami jako obiekt JSON. Informacje te mogą być zweryfikowane i zaufane, ponieważ są podpisane cyfrowo.

### Architektura Naszego Rozwiązania

Implementacja w Custom Steam Dashboard używa **dwuwarstwowego systemu bezpieczeństwa**:

1. **JWT (Session Layer)** - Zarządzanie sesją użytkownika
   - Krótkotrwałe tokeny (20 minut)
   - Stateless authentication
   - Zawiera `client_id` i metadata

2. **HMAC-SHA256 (Request Layer)** - Weryfikacja każdego żądania
   - Podpis cyfrowy każdego request
   - Anti-replay protection (nonce)
   - Timestamp validation (±60s)

```
┌─────────────┐                    ┌─────────────┐
│   Client    │                    │   Server    │
│   (GUI)     │                    │   (API)     │
└─────────────┘                    └─────────────┘
       │                                  │
       │  1. POST /auth/login             │
       │     + HMAC Signature             │
       ├─────────────────────────────────>│
       │                                  │
       │  2. JWT Token (20 min)           │
       │<─────────────────────────────────┤
       │                                  │
       │  3. GET /api/games               │
       │     + JWT (Authorization)        │
       │     + HMAC (X-* headers)         │
       ├─────────────────────────────────>│
       │                                  │
       │  4. Response Data                │
       │<─────────────────────────────────┤
       │                                  │
```

### Komponenty Systemu

**Serwer (`server/`):**
- `security.py` - Core JWT i HMAC logic
- `auth_routes.py` - Endpoint `/auth/login`
- `middleware.py` - Automatyczna weryfikacja HMAC
- `app.py` - Integracja z FastAPI

**Klient (`app/`):**
- `helpers/signing.py` - Generowanie podpisów HMAC
- `helpers/api_client.py` - Uwierzytelniony klient HTTP
- `core/services/server_client.py` - High-level API wrapper

### Kluczowe Cechy

✅ **Stateless** - Serwer nie przechowuje sesji  
✅ **Bezpieczne** - Dual-layer (JWT + HMAC)  
✅ **Skalowalne** - Rate limiting per client_id  
✅ **Odporne na replay** - Nonce cache + timestamp  
✅ **Automatyczne** - Refresh tokena transparentny dla użytkownika  

### Szybki Start

```python
# Klient - Automatyczna autoryzacja
from app.helpers.api_client import AuthenticatedAPIClient

client = AuthenticatedAPIClient('http://localhost:8000')
await client.login()  # Otrzymuje JWT

# Każde żądanie jest automatycznie podpisane
games = await client.get('/api/games')  # JWT + HMAC
```

```python
# Serwer - Ochrona endpointu
from security import require_session_and_signed_request

@app.get("/api/games")
async def get_games(client_id: str = Depends(require_session_and_signed_request)):
    # Endpoint dostępny tylko z ważnym JWT + HMAC
    return {"games": [...]}
```

### Dalsze Kroki

Przeczytaj szczegółowe dokumenty aby zrozumieć:
- **Teorię** - Jak działa JWT i HMAC
- **Implementację** - Szczegóły techniczne naszego rozwiązania
- **Bezpieczeństwo** - Słabe strony i mitygacje
- **Wydajność** - Wpływ na performance aplikacji
- **Best Practices** - Rekomendacje dla produkcji

---
**Dokumentacja wygenerowana**: 2025-01-11  
**Wersja systemu**: 1.0.0

