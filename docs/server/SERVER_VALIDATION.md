# Dokumentacja Walidacji

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Walidatory](#walidatory)
3. [Użycie w Endpointach](#użycie-w-endpointach)
4. [Obsługa Błędów](#obsługa-błędów)

---

## Przegląd

System walidacji wykorzystuje **Pydantic** do sprawdzania poprawności danych wejściowych.

**Plik:** `server/validation.py`

### Zalety

- ✅ Automatyczna konwersja typów
- ✅ Walidacja zakresu wartości
- ✅ Niestandardowe reguły walidacji
- ✅ Przyjazne komunikaty błędów
- ✅ Integracja z FastAPI

---

## Walidatory

### 1. **SteamIDValidator**

Waliduje Steam ID64.

```python
class SteamIDValidator(BaseModel):
    """
    Walidator Steam ID64.
    
    Steam ID64 to 17-cyfrowa liczba zaczynająca się od 765611...
    """
    steamid: str
    
    @field_validator("steamid")
    @classmethod
    def validate_steamid(cls, v: str) -> str:
        """
        Sprawdza poprawność Steam ID64.
        
        Raises:
            ValueError: Jeśli Steam ID jest nieprawidłowy
        """
        # Usuń białe znaki
        v = v.strip()
        
        # Sprawdź czy to liczba
        if not v.isdigit():
            raise ValueError("Steam ID must be numeric")
        
        # Sprawdź długość (17 cyfr)
        if len(v) != 17:
            raise ValueError("Steam ID must be 17 digits long")
        
        # Sprawdź prefix (765611...)
        if not v.startswith("765611"):
            raise ValueError("Invalid Steam ID format")
        
        return v
```

**Przykład użycia:**
```python
# Poprawne
validator = SteamIDValidator(steamid="76561198012345678")
print(validator.steamid)  # "76561198012345678"

# Niepoprawne
try:
    validator = SteamIDValidator(steamid="123")
except ValidationError as e:
    print(e)  # "Steam ID must be 17 digits long"
```

---

### 2. **AppIDValidator**

Waliduje Steam Application ID.

```python
class AppIDValidator(BaseModel):
    """
    Walidator Steam Application ID.
    
    AppID to dodatnia liczba całkowita (1-999999999).
    """
    appid: int
    
    @field_validator("appid")
    @classmethod
    def validate_appid(cls, v: int) -> int:
        """
        Sprawdza poprawność AppID.
        
        Raises:
            ValueError: Jeśli AppID jest nieprawidłowy
        """
        if v <= 0:
            raise ValueError("AppID must be positive")
        
        if v > 999999999:
            raise ValueError("AppID too large")
        
        return v
```

**Przykład użycia:**
```python
# Poprawne
validator = AppIDValidator(appid=730)
print(validator.appid)  # 730

# Niepoprawne
try:
    validator = AppIDValidator(appid=-1)
except ValidationError as e:
    print(e)  # "AppID must be positive"
```

---

### 3. **AppIDListValidator**

Waliduje listę AppID (batch operations).

```python
class AppIDListValidator(BaseModel):
    """
    Walidator listy AppID.
    
    Używany do operacji batch (np. pobieranie tagów wielu gier).
    """
    appids: List[int]
    
    @field_validator("appids")
    @classmethod
    def validate_appids(cls, v: List[int]) -> List[int]:
        """
        Sprawdza poprawność listy AppID.
        
        Raises:
            ValueError: Jeśli lista jest pusta lub zawiera nieprawidłowe AppID
        """
        if not v:
            raise ValueError("AppID list cannot be empty")
        
        if len(v) > 100:
            raise ValueError("Maximum 100 AppIDs per request")
        
        # Waliduj każdy AppID
        for appid in v:
            if appid <= 0:
                raise ValueError(f"Invalid AppID: {appid}")
        
        # Usuń duplikaty
        return list(set(v))
```

**Przykład użycia:**
```python
# Poprawne
validator = AppIDListValidator(appids=[730, 570, 440])
print(validator.appids)  # [730, 570, 440]

# Usuwa duplikaty
validator = AppIDListValidator(appids=[730, 730, 570])
print(validator.appids)  # [730, 570]

# Niepoprawne
try:
    validator = AppIDListValidator(appids=[])
except ValidationError as e:
    print(e)  # "AppID list cannot be empty"
```

---

### 4. **VanityURLValidator**

Waliduje Steam Vanity URL.

```python
class VanityURLValidator(BaseModel):
    """
    Walidator Steam Vanity URL.
    
    Akceptuje:
    - "gaben"
    - "my_custom_name"
    - "https://steamcommunity.com/id/gaben"
    """
    vanity_url: str
    
    @field_validator("vanity_url")
    @classmethod
    def validate_vanity_url(cls, v: str) -> str:
        """
        Sprawdza poprawność Vanity URL.
        
        Raises:
            ValueError: Jeśli URL jest nieprawidłowy
        """
        # Usuń białe znaki
        v = v.strip()
        
        if not v:
            raise ValueError("Vanity URL cannot be empty")
        
        # Wyodrębnij nazwę z pełnego URL
        if "steamcommunity.com" in v:
            parts = v.split("/")
            if len(parts) < 2:
                raise ValueError("Invalid Steam URL format")
            v = parts[-1] or parts[-2]
        
        # Sprawdź długość (3-32 znaki)
        if len(v) < 3:
            raise ValueError("Vanity URL too short (minimum 3 characters)")
        
        if len(v) > 32:
            raise ValueError("Vanity URL too long (maximum 32 characters)")
        
        # Sprawdź dozwolone znaki (alfanumeryczne + _ -)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Vanity URL contains invalid characters")
        
        return v
```

**Przykład użycia:**
```python
# Poprawne
validator = VanityURLValidator(vanity_url="gaben")
print(validator.vanity_url)  # "gaben"

# Wyodrębnia z pełnego URL
validator = VanityURLValidator(vanity_url="https://steamcommunity.com/id/gaben")
print(validator.vanity_url)  # "gaben"

# Niepoprawne
try:
    validator = VanityURLValidator(vanity_url="ab")
except ValidationError as e:
    print(e)  # "Vanity URL too short (minimum 3 characters)"
```

---

## Użycie w Endpointach

### Przykład 1: Path Parameter

```python
@app.get("/api/games/{appid}")
async def get_game(appid: int, ...):
    """Pobiera grę po AppID."""
    try:
        # Waliduj AppID
        validator = AppIDValidator(appid=appid)
        validated_appid = validator.appid
        
        # Pobierz grę
        game = await db.get_game(validated_appid)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        return game
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
```

### Przykład 2: Request Body

```python
@app.post("/api/games/tags/batch")
async def get_games_tags_batch(data: AppIDListValidator, ...):
    """Pobiera tagi dla wielu gier."""
    try:
        # data.appids jest już zwalidowana
        tags = await db.get_game_tags(data.appids)
        return {"tags": tags}
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
```

### Przykład 3: Query Parameter

```python
@app.get("/api/owned-games/{steamid}")
async def get_owned_games(steamid: str, ...):
    """Pobiera posiadane gry użytkownika."""
    try:
        # Waliduj Steam ID
        validator = SteamIDValidator(steamid=steamid)
        validated_steamid = validator.steamid
        
        # Pobierz gry
        games = await steam_client.get_player_owned_games(validated_steamid)
        return {"games": [game.model_dump() for game in games]}
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
```

---

## Obsługa Błędów

### Format Błędu Pydantic

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["appid"],
      "msg": "AppID must be positive",
      "input": -1
    }
  ]
}
```

### Custom Error Handler

**Plik:** `server/app.py`

```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Obsługuje błędy walidacji Pydantic.
    
    Zwraca:
        422 Unprocessable Entity z szczegółami błędów
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": str(exc)
        }
    )
```

### Przykładowe Odpowiedzi

#### Nieprawidłowy AppID

**Request:**
```http
GET /api/games/-1
```

**Response:** `400 Bad Request`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["appid"],
      "msg": "AppID must be positive",
      "input": -1
    }
  ]
}
```

#### Nieprawidłowy Steam ID

**Request:**
```http
GET /api/owned-games/123
```

**Response:** `400 Bad Request`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["steamid"],
      "msg": "Steam ID must be 17 digits long",
      "input": "123"
    }
  ]
}
```

#### Pusta lista AppID

**Request:**
```json
POST /api/games/tags/batch
{
  "appids": []
}
```

**Response:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["appids"],
      "msg": "AppID list cannot be empty",
      "input": []
    }
  ]
}
```

---

## Best Practices

### 1. Waliduj na Wejściu

```python
# ✅ Dobre
@app.get("/api/games/{appid}")
async def get_game(appid: int, ...):
    validator = AppIDValidator(appid=appid)  # Waliduj od razu
    game = await db.get_game(validator.appid)
    ...

# ❌ Złe
@app.get("/api/games/{appid}")
async def get_game(appid: int, ...):
    game = await db.get_game(appid)  # Brak walidacji
    ...
```

### 2. Używaj Pydantic Models

```python
# ✅ Dobre - automatyczna walidacja przez FastAPI
@app.post("/api/games/tags/batch")
async def get_tags(data: AppIDListValidator, ...):
    tags = await db.get_game_tags(data.appids)
    ...

# ❌ Złe - manualna walidacja
@app.post("/api/games/tags/batch")
async def get_tags(request: Request, ...):
    body = await request.json()
    appids = body.get("appids", [])
    if not appids:
        raise HTTPException(400, "Missing appids")
    ...
```

### 3. Zwracaj Przyjazne Błędy

```python
# ✅ Dobre
try:
    validator = SteamIDValidator(steamid=steamid)
except ValidationError as e:
    raise HTTPException(
        status_code=400,
        detail=f"Invalid Steam ID: {e.errors()[0]['msg']}"
    )

# ❌ Złe
validator = SteamIDValidator(steamid=steamid)  # Rzuci ValidationError
```

---

## Podsumowanie

| Walidator | Waliduje | Przykład |
|-----------|----------|----------|
| `SteamIDValidator` | Steam ID64 | `76561198012345678` |
| `AppIDValidator` | Steam AppID | `730` |
| `AppIDListValidator` | Lista AppID | `[730, 570, 440]` |
| `VanityURLValidator` | Vanity URL | `gaben` |

---

## Następne Kroki

- **API Endpoints**: [SERVER_API_ENDPOINTS.md](SERVER_API_ENDPOINTS.md)
- **Security**: [SERVER_SECURITY.md](SERVER_SECURITY.md)

