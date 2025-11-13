# API Rate Limiting and Input Validation Documentation

## Overview

This document describes the rate limiting and input validation mechanisms implemented in the Custom Steam Dashboard API to protect against abuse, ensure data integrity, and maintain service availability.

## Rate Limiting

### Implementation

Rate limiting is implemented using the `slowapi` library, which provides a simple and effective way to limit the number of requests a client can make to the API within a specific time window.

### Configuration

- **Library**: `slowapi` (based on Flask-Limiter)
- **Key Function**: `get_remote_address` - limits are applied per client IP address
- **Default Limit**: 100 requests per minute (applied globally to all endpoints)

### Per-Endpoint Limits

| Endpoint | Rate Limit | Reason |
|----------|-----------|---------|
| `/` | 60/minute | Root endpoint - moderate traffic expected |
| `/health` | 120/minute | Health checks - high frequency allowed |
| `/api/games` | 30/minute | Database-heavy operation |
| `/api/games/{appid}` | 60/minute | Frequent individual game lookups |
| `/api/games/tags/batch` | 20/minute | Batch operation - more expensive |
| `/api/owned-games/{steamid}` | 20/minute | External API call - limited to prevent abuse |
| `/api/recently-played/{steamid}` | 20/minute | External API call - limited to prevent abuse |
| `/api/coming-soon` | 30/minute | External API call - cached data |
| `/api/player-summary/{steamid}` | 30/minute | External API call - moderate frequency |
| `/api/resolve-vanity/{vanity_url}` | 20/minute | External API call - limited to prevent abuse |
| `/api/current-players` | 30/minute | Database operation - moderate frequency |
| `/api/genres` | 30/minute | Database operation - cached data |
| `/api/categories` | 30/minute | Database operation - cached data |

### Rate Limit Response

When a client exceeds the rate limit, they receive a `429 Too Many Requests` HTTP status code with details about the limit and when they can retry.

Example response:
```json
{
  "detail": "Rate limit exceeded: 20 per 1 minute"
}
```

### Headers

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed in the time window
- `X-RateLimit-Remaining`: Number of requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit window resets (Unix timestamp)

## Input Validation

### Implementation

Input validation is implemented using Pydantic v2 models with custom validators. All user inputs are validated before processing to prevent:
- SQL injection
- Invalid data types
- Out-of-range values
- Malformed requests
- Directory traversal attacks

### Validation Models

#### 1. SteamIDValidator

Validates Steam ID inputs (ID64, vanity names, or profile URLs).

**Accepted Formats**:
- Steam ID64: 17-digit number starting with "7656119"
  - Example: `76561198000000000`
- Vanity name: 2-32 alphanumeric characters (underscore and hyphen allowed)
  - Example: `gaben`, `my_custom_name`
- Full profile URL: Steam community profile or ID URL
  - Example: `https://steamcommunity.com/id/gaben`

**Validation Rules**:
- Non-empty string
- Maximum length: 100 characters
- Whitespace is stripped
- For ID64: Must be exactly 17 digits starting with "7656119"
- For vanity names: 2-32 characters, alphanumeric + underscore + hyphen only
- For URLs: Must match Steam community URL pattern

**Error Messages**:
- "Steam ID cannot be empty"
- "Steam ID64 must be exactly 17 digits"
- "Invalid Steam ID64 format"
- "Vanity URL name must be between 2 and 32 characters"
- "Vanity URL name can only contain letters, numbers, underscores, and hyphens"

#### 2. AppIDValidator

Validates Steam application IDs.

**Validation Rules**:
- Must be a positive integer
- Range: 1 to 9,999,999
- No zero or negative values

**Error Messages**:
- "App ID must be positive"
- "App ID too large"

#### 3. AppIDListValidator

Validates lists of Steam application IDs for batch operations.

**Validation Rules**:
- Minimum 1 app ID
- Maximum 100 app IDs per request
- Each app ID must be valid (positive integer, in range)
- Duplicates are automatically removed while preserving order

**Error Messages**:
- "App ID list cannot be empty"
- "Maximum 100 app IDs allowed per request"
- "App ID must be an integer"
- "App ID must be positive"
- "App ID {appid} too large"

#### 4. VanityURLValidator

Validates Steam vanity URLs for resolution.

**Accepted Formats**:
- Vanity name: 2-32 alphanumeric characters
- Full URL: Steam community ID or profiles URL

**Validation Rules**:
- Non-empty string
- Maximum length: 200 characters
- Whitespace is stripped
- Must match vanity name or Steam URL pattern

**Error Messages**:
- "Vanity URL cannot be empty"
- "Vanity URL too long"
- "Invalid Steam community URL format"
- "Vanity name must be between 2 and 32 characters"

### Error Handling

#### Validation Errors (400 Bad Request)

When input validation fails, the API returns a `400 Bad Request` status with detailed error information:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "appid"],
      "msg": "App ID must be positive",
      "input": -1
    }
  ]
}
```

#### Unprocessable Entity (422)

For Pydantic validation errors that occur during request parsing:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "appids"],
      "msg": "Field required"
    }
  ],
  "body": "..."
}
```

### Sanitization Utility

The `sanitize_string()` function provides additional protection against injection attacks:

**Features**:
- Removes null bytes and control characters (except \\n, \\r, \\t)
- Truncates strings to maximum length (default: 1000 characters)
- Strips leading/trailing whitespace

**Usage**:
```python
from validation import sanitize_string

safe_input = sanitize_string(user_input, max_length=500)
```

## Security Best Practices

### 1. Always Validate User Input

All endpoints that accept user input use validation models:

```python
@app.get("/api/games/{appid}")
async def get_game(appid: int, request: Request):
    # Validate appid
    validator = AppIDValidator(appid=appid)
    validated_appid = validator.appid
    
    # Use validated_appid for database query
    game = await db.get_game(validated_appid)
    # ...
```

### 2. Handle Validation Errors Gracefully

```python
try:
    validator = SteamIDValidator(steamid=steamid)
    validated_steamid = validator.steamid
except ValidationError as e:
    raise HTTPException(status_code=400, detail=e.errors())
```

### 3. Use Type Hints

All validation models use proper type hints for IDE support and runtime type checking.

### 4. Test Validation Logic

Comprehensive unit tests are provided in `test_validation.py` to ensure validation rules work correctly.

## Testing

### Running Validation Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run validation tests
python server/test_validation.py

# Or use pytest directly
pytest server/test_validation.py -v
```

### Test Coverage

The test suite covers:
- Valid inputs (positive tests)
- Invalid inputs (negative tests)
- Edge cases (boundary conditions)
- Special characters and injection attempts
- Empty and null inputs
- Lists with duplicates
- Maximum length validations

## Monitoring

### Rate Limit Monitoring

Monitor rate limit hits in application logs:

```
WARNING - Rate limit exceeded for IP 192.168.1.1 on endpoint /api/games
```

### Validation Error Monitoring

Track validation errors to identify:
- Malicious activity patterns
- Client integration issues
- API usability problems

## Configuration

### Adjusting Rate Limits

To modify rate limits, edit the `@limiter.limit()` decorator on endpoints:

```python
@app.get("/api/games")
@limiter.limit("50/minute")  # Changed from 30 to 50
async def get_all_games(request: Request):
    # ...
```

### Adjusting Validation Rules

To modify validation rules, edit the validators in `server/validation.py`:

```python
class AppIDValidator(BaseModel):
    appid: int = Field(..., gt=0, lt=20000000)  # Increased upper limit
```

## Future Improvements

1. **Per-User Rate Limiting**: Implement authentication and track limits per user account
2. **Sliding Window**: Use sliding window rate limiting for more accurate control
3. **Distributed Rate Limiting**: Use Redis for rate limiting across multiple server instances
4. **Dynamic Rate Limits**: Adjust limits based on server load and user tier
5. **Custom Validation Messages**: Add localization support for validation error messages
6. **Rate Limit Exemptions**: Allow certain IPs or users to bypass rate limits

## References

- [slowapi Documentation](https://slowapi.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

