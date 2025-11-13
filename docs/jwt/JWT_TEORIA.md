# JWT - Teoria i Podstawy

## Co to jest JWT?

**JWT (JSON Web Token)** to kompaktowy, URL-safe token reprezentujący claims (roszczenia) przekazywane między dwiema stronami. Token jest zakodowany jako JSON object i podpisany cyfrowo, co zapewnia integralność i autentyczność danych.

## Struktura JWT

JWT składa się z trzech części oddzielonych kropkami (`.`):

```
header.payload.signature
```

### Przykład:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXNrdG9wLW1haW4iLCJjbGllbnRfaWQiOiJkZXNrdG9wLW1haW4iLCJpYXQiOjE3MzY2MjM0NDMsImV4cCI6MTczNjYyNDY0MywidHlwZSI6ImFjY2VzcyJ9.9kY7_Qb5RxJ_xP6vT8wK3mN1sL4oH2jC9aE0fG6iD8s
```

### 1. Header (Nagłówek)

Zawiera informacje o typie tokenu i algorytmie szyfrowania:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

- `alg` - Algorytm podpisu (np. HS256 = HMAC-SHA256)
- `typ` - Typ tokenu (zawsze "JWT")

### 2. Payload (Dane)

Zawiera claims - informacje o użytkowniku i metadane:

```json
{
  "sub": "desktop-main",           // Subject - identyfikator podmiotu
  "client_id": "desktop-main",     // Custom claim - ID klienta
  "iat": 1736623443,               // Issued At - czas wydania
  "exp": 1736624643,               // Expiration - czas wygaśnięcia
  "type": "access"                 // Custom claim - typ tokenu
}
```

**Standardowe claims (RFC 7519):**
- `iss` (issuer) - Wystawca tokenu
- `sub` (subject) - Podmiot tokenu (użytkownik/klient)
- `aud` (audience) - Odbiorca tokenu
- `exp` (expiration time) - Czas wygaśnięcia (Unix timestamp)
- `nbf` (not before) - Czas od którego token jest ważny
- `iat` (issued at) - Czas wydania tokenu
- `jti` (JWT ID) - Unikalny identyfikator tokenu

**Custom claims** - Dowolne dodatkowe dane (np. `client_id`, `permissions`)

### 3. Signature (Podpis)

Podpis cyfrowy zapewniający integralność i autentyczność:

```javascript
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

Podpis gwarantuje, że:
- Token nie został zmodyfikowany (integralność)
- Token został wydany przez zaufane źródło (autentyczność)

## Jak działa JWT?

### Przepływ autoryzacji:

```
┌──────────┐                               ┌──────────┐
│  Client  │                               │  Server  │
└──────────┘                               └──────────┘
     │                                           │
     │  1. Login (credentials)                   │
     ├──────────────────────────────────────────>│
     │                                           │
     │                      2. Weryfikacja       │
     │                         credentials       │
     │                                           │
     │  3. JWT Token                             │
     │<──────────────────────────────────────────┤
     │                                           │
     │  4. Request + JWT (Authorization header)  │
     ├──────────────────────────────────────────>│
     │                                           │
     │                      5. Weryfikacja JWT   │
     │                         (podpis + exp)    │
     │                                           │
     │  6. Response (jeśli JWT valid)            │
     │<──────────────────────────────────────────┤
     │                                           │
```

### Krok po kroku:

1. **Klient loguje się** - Wysyła credentials (login/hasło lub client_id/secret)
2. **Serwer weryfikuje** - Sprawdza credentials w bazie/konfiguracji
3. **Serwer generuje JWT** - Tworzy token z claims i podpisuje swoim sekretem
4. **Klient zapisuje JWT** - Przechowuje token (localStorage, memory, itp.)
5. **Klient używa JWT** - Dodaje token do każdego żądania w nagłówku `Authorization: Bearer <token>`
6. **Serwer weryfikuje JWT** - Sprawdza podpis, expiration, claims
7. **Serwer odpowiada** - Jeśli token valid, zwraca dane

## Zalety JWT

### 1. **Stateless**
Serwer nie musi przechowywać informacji o sesjach w bazie danych lub pamięci. Wszystkie potrzebne informacje są w tokenie.

**Tradycyjna sesja:**
```
Client → Session ID → Server → Database lookup → User data
```

**JWT:**
```
Client → JWT Token → Server → Verify signature → User data (z tokenu)
```

### 2. **Skalowalność**
Ponieważ JWT jest stateless, można łatwo skalować aplikację horyzontalnie:
- Nie wymaga sticky sessions
- Nie wymaga shared session storage
- Każdy serwer może zweryfikować JWT niezależnie

### 3. **Cross-domain**
JWT może być używany w różnych domenach i aplikacjach:
```
App A (app.example.com) ──┐
                           ├──> Auth Server ──> JWT
App B (api.example.com) ──┘
```

### 4. **Mobile-friendly**
Idealny dla aplikacji mobilnych i desktop:
- Nie wymaga cookies
- Może być przechowywany w secure storage
- Działa offline (verification cache)

### 5. **Zawiera dane**
Token może przenosić informacje o użytkowniku:
```json
{
  "user_id": 123,
  "username": "john",
  "roles": ["admin", "editor"],
  "permissions": ["read", "write"]
}
```

## Wady JWT

### 1. **Nie można unieważnić**
Raz wydany token jest ważny do czasu wygaśnięcia:
- Nie można "wylogować" użytkownika przed exp
- Kradzież tokenu = dostęp do końca ważności
- **Mitygacja**: Krótki TTL (np. 15-30 min) + refresh tokens

### 2. **Rozmiar**
JWT może być duży (200-1000 bytes):
- Każde żądanie przesyła cały token
- Overhead dla małych requestów
- **Mitygacja**: Minimalizuj claims, używaj kompresji

### 3. **Brak rewizji**
Nie można zmienić danych w aktywnym tokenie:
- Zmiana uprawnień wymaga nowego tokenu
- Użytkownik musi się wylogować i zalogować ponownie
- **Mitygacja**: Krótki TTL + weryfikacja dodatkowa

### 4. **Secret management**
Bezpieczeństwo zależy od tajności klucza:
- Wyciek klucza = kompromitacja wszystkich tokenów
- Rotacja klucza = unieważnienie wszystkich tokenów
- **Mitygacja**: HSM, Key rotation strategy, asymetryczne klucze (RS256)

## Algorytmy Podpisu

### Symetryczne (HMAC)

**HS256** (HMAC-SHA256) - Używany w naszej implementacji
- Ten sam klucz do podpisywania i weryfikacji
- Szybki
- Prosty w implementacji
- Wymaga bezpiecznego przechowywania klucza na obu stronach

```python
signature = HMAC-SHA256(
    base64(header) + "." + base64(payload),
    secret_key
)
```

### Asymetryczne (RSA, ECDSA)

**RS256** (RSA-SHA256)
- Para kluczy: prywatny (signing) i publiczny (verification)
- Wolniejszy niż HMAC
- Serwer może udostępnić publiczny klucz bez ryzyka
- Idealny dla mikrousług

**ES256** (ECDSA-SHA256)
- Krótsze klucze niż RSA
- Szybszy niż RSA
- Bardziej skomplikowany

## Bezpieczeństwo JWT

### ✅ CO ZAPEWNIA JWT:
- **Integralność** - Token nie może być zmodyfikowany bez wykrycia
- **Autentyczność** - Token pochodzi od zaufanego źródła
- **Non-repudiation** - Nie można zaprzeczyć wystawieniu tokenu

### ❌ CZEGO JWT NIE ZAPEWNIA:
- **Poufność** - Payload jest tylko zakodowany base64, nie szyfrowany
- **Ochrona przed kradzieżą** - Skradziony token działa jak oryginał
- **Automatyczne unieważnienie** - Token jest ważny do exp

### Zasady Bezpieczeństwa:

1. **Używaj HTTPS** - Token w plain text na HTTP = katastrofa
2. **Krótki TTL** - 15-30 minut dla access token
3. **Nie przechowuj wrażliwych danych** - Payload jest widoczny
4. **Waliduj wszystkie claims** - exp, iat, aud, iss
5. **Używaj silnych sekretów** - Minimum 256 bitów losowości
6. **Rotacja kluczy** - Planuj strategię wymiany kluczy

## JWT vs Session Cookies

| Aspekt | JWT | Session Cookie |
|--------|-----|----------------|
| **Storage** | Stateless (w tokenie) | Stateful (w bazie/redis) |
| **Skalowalność** | ⭐⭐⭐⭐⭐ Doskonała | ⭐⭐⭐ Wymaga sticky sessions |
| **Wydajność** | ⭐⭐⭐⭐ Szybka weryfikacja | ⭐⭐⭐ Lookup w bazie |
| **Rozmiar** | ⭐⭐ Duży (200-1000B) | ⭐⭐⭐⭐⭐ Mały (16-32B) |
| **Unieważnienie** | ⭐⭐ Trudne | ⭐⭐⭐⭐⭐ Natychmiastowe |
| **Cross-domain** | ⭐⭐⭐⭐⭐ Tak | ⭐⭐ Ograniczone |
| **Mobile** | ⭐⭐⭐⭐⭐ Idealne | ⭐⭐⭐ Wymaga cookies |
| **Bezpieczeństwo** | ⭐⭐⭐⭐ Dobre | ⭐⭐⭐⭐ Dobre |

## Kiedy używać JWT?

### ✅ UŻYJ JWT gdy:
- Budujesz stateless API
- Masz mikrousługi
- Potrzebujesz cross-domain auth
- Tworzysz mobile/desktop app
- Chcesz wysokiej skalowalności

### ❌ NIE UŻYWAJ JWT gdy:
- Potrzebujesz natychmiastowego unieważnienia
- Masz wrażliwe dane w payload
- Aplikacja ma krótkie sesje (< 5 min)
- Chcesz prostoty (session cookie prostsze)

## Podsumowanie

JWT to potężne narzędzie do autoryzacji, szczególnie w architekturach mikrousługowych i aplikacjach mobilnych. Kluczowe jest zrozumienie jego ograniczeń i stosowanie odpowiednich mitygacji (krótki TTL, HTTPS, validation).

W naszej implementacji łączymy JWT z HMAC-SHA256 request signing, co daje **dual-layer security** i eliminuje wiele wad samego JWT.

---
**Następny dokument**: [Implementacja w Custom Steam Dashboard](./JWT_IMPLEMENTACJA.md)

