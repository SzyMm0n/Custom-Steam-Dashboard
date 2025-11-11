"""
Security module for Custom Steam Dashboard server.
Handles JWT generation, HMAC signature verification, and authentication.
"""
import os
import hmac
import hashlib
import time
import json
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security bearer scheme for JWT
security_bearer = HTTPBearer(auto_error=False)

# Configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "1200"))  # 20 minutes default
CLIENTS_JSON = os.getenv("CLIENTS_JSON", '{"desktop-main": "change-me-in-production"}')

# Parse clients configuration
try:
    CLIENTS_MAP: Dict[str, str] = json.loads(CLIENTS_JSON)
except json.JSONDecodeError:
    logger.error("Failed to parse CLIENTS_JSON environment variable")
    CLIENTS_MAP = {}

# Validate that JWT_SECRET is set
if not JWT_SECRET or JWT_SECRET == "":
    logger.warning("JWT_SECRET not set! Using insecure default. Set JWT_SECRET in environment!")
    JWT_SECRET = "insecure-default-change-me"

# In-memory nonce cache with TTL (OrderedDict for LRU behavior)
# Format: {nonce: expiry_timestamp}
_nonce_cache: OrderedDict[str, float] = OrderedDict()
_nonce_cache_max_size = 10000
_nonce_ttl_seconds = 300  # 5 minutes

# JWT algorithm
JWT_ALGORITHM = "HS256"


# ===== Nonce Management =====

def _cleanup_expired_nonces():
    """Remove expired nonces from cache."""
    now = time.time()
    # Create list of expired nonces to remove
    expired = [nonce for nonce, expiry in _nonce_cache.items() if expiry < now]
    for nonce in expired:
        del _nonce_cache[nonce]


def _check_and_store_nonce(nonce: str) -> bool:
    """
    Check if nonce was used before and store it if not.
    
    Args:
        nonce: Nonce string to check
        
    Returns:
        True if nonce is new (not used before), False if already used
    """
    _cleanup_expired_nonces()
    
    if nonce in _nonce_cache:
        return False  # Nonce already used (replay attack)
    
    # Store nonce with expiry time
    _nonce_cache[nonce] = time.time() + _nonce_ttl_seconds
    
    # Limit cache size (remove oldest if too large)
    if len(_nonce_cache) > _nonce_cache_max_size:
        _nonce_cache.popitem(last=False)  # Remove oldest (FIFO)
    
    return True


# ===== JWT Functions =====

def create_jwt(client_id: str, extra_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a JWT token for authenticated client.
    
    Args:
        client_id: Client identifier
        extra_claims: Optional additional claims to include in JWT
        
    Returns:
        Dictionary with access_token, token_type, expires_in
    """
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(seconds=JWT_TTL_SECONDS)
    
    payload = {
        "sub": client_id,
        "client_id": client_id,
        "iat": now,
        "exp": expiry,
        "type": "access"
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    logger.info(f"JWT created for client: {client_id[:8]}...")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_TTL_SECONDS
    }


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token with clock skew tolerance.

    Args:
        token: JWT token string
        
    Returns:
        Decoded JWT payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Add 5 minutes leeway for clock skew between client and server
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            leeway=timedelta(minutes=5)
        )

        # Debug logging for time differences
        if 'iat' in payload:
            token_iat = datetime.fromtimestamp(payload['iat'], tz=timezone.utc)
            server_time = datetime.now(timezone.utc)
            time_diff = (server_time - token_iat).total_seconds()

            logger.debug(f"Token issued at: {token_iat}, Server time: {server_time}, Diff: {time_diff:.2f}s")

            if abs(time_diff) > 300:  # More than 5 minutes
                logger.warning(f"Large time difference detected: {time_diff:.2f}s")

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ===== HMAC Signature Verification =====

def compute_signature(
    client_secret: str,
    method: str,
    path: str,
    body_hash: str,
    timestamp: str,
    nonce: str
) -> str:
    """
    Compute HMAC-SHA256 signature for request.
    
    Signature format: HMAC-SHA256(secret, "METHOD|PATH|SHA256(body)|timestamp|nonce")
    
    Args:
        client_secret: Client secret key
        method: HTTP method (GET, POST, etc.)
        path: Request path
        body_hash: SHA256 hash of request body (hex string)
        timestamp: Unix timestamp as string
        nonce: Random nonce string
        
    Returns:
        Base64-encoded signature
    """
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    signature = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    import base64
    return base64.b64encode(signature).decode('utf-8')


def verify_request_signature(
    method: str,
    path: str,
    body: bytes,
    x_client_id: Optional[str],
    x_timestamp: Optional[str],
    x_nonce: Optional[str],
    x_signature: Optional[str]
) -> str:
    """
    Verify HMAC signature of incoming request.
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body bytes
        x_client_id: Client ID from header
        x_timestamp: Timestamp from header
        x_nonce: Nonce from header
        x_signature: Signature from header
        
    Returns:
        client_id if verification successful
        
    Raises:
        HTTPException: If verification fails
    """
    # Check all required headers are present
    if not all([x_client_id, x_timestamp, x_nonce, x_signature]):
        logger.warning("Missing required signature headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature headers (X-Client-Id, X-Timestamp, X-Nonce, X-Signature)"
        )
    
    # Verify client exists
    if x_client_id not in CLIENTS_MAP:
        logger.warning(f"Unknown client_id: {x_client_id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unknown client_id"
        )
    
    # Verify timestamp (must be within 60 seconds)
    try:
        request_timestamp = int(x_timestamp)
        now = int(time.time())
        time_diff = abs(now - request_timestamp)
        
        if time_diff > 60:
            logger.warning(f"Request timestamp too old: {time_diff}s difference")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Request timestamp too old (diff: {time_diff}s, max: 60s)"
            )
    except ValueError:
        logger.warning(f"Invalid timestamp format: {x_timestamp}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp format"
        )
    
    # Verify nonce (anti-replay)
    if not _check_and_store_nonce(x_nonce):
        logger.warning(f"Nonce replay detected: {x_nonce[:16]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nonce already used (replay attack detected)"
        )
    
    # Compute body hash
    body_hash = hashlib.sha256(body).hexdigest()
    
    # Get client secret
    client_secret = CLIENTS_MAP[x_client_id]
    
    # Compute expected signature
    expected_signature = compute_signature(
        client_secret=client_secret,
        method=method,
        path=path,
        body_hash=body_hash,
        timestamp=x_timestamp,
        nonce=x_nonce
    )
    
    # Compare signatures (constant-time comparison)
    if not hmac.compare_digest(expected_signature, x_signature):
        logger.warning(f"Signature verification failed for client: {x_client_id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    logger.debug(f"Signature verified for client: {x_client_id[:8]}...")
    return x_client_id


# ===== FastAPI Dependencies =====

async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """
    FastAPI dependency: Require valid JWT token (without HMAC signature).
    
    Use this for endpoints that only need JWT authentication (like /docs).
    
    Returns:
        JWT payload with client_id
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = verify_jwt(credentials.credentials)
    return payload


async def require_session_and_signed_request(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_client_id: Optional[str] = Header(None, alias="X-Client-Id"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> str:
    """
    FastAPI dependency: Require valid JWT token AND valid HMAC signature.
    
    Use this for all data endpoints that need both session (JWT) and request signing (HMAC).
    
    Returns:
        client_id from JWT
        
    Raises:
        HTTPException: If JWT or signature verification fails
    """
    # First verify JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    jwt_payload = verify_jwt(credentials.credentials)
    jwt_client_id = jwt_payload.get("client_id")
    
    if not jwt_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing client_id"
        )
    
    # Verify that X-Client-Id matches JWT client_id
    if x_client_id != jwt_client_id:
        logger.warning(f"Client ID mismatch: JWT={jwt_client_id[:8]}..., Header={x_client_id[:8] if x_client_id else 'None'}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client ID mismatch between token and headers"
        )
    
    # Note: HMAC signature verification happens in middleware (see below)
    # because we need access to request body
    
    return jwt_client_id


def rate_limit_key(request) -> str:
    """
    Extract rate limiting key from request.
    
    Uses client_id from JWT if available, otherwise falls back to IP address.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Key string for rate limiting
    """
    # Try to get client_id from JWT in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            client_id = payload.get("client_id")
            if client_id:
                return f"client:{client_id}"
        except jwt.InvalidTokenError:
            pass
    
    # Fallback to IP address
    return f"ip:{request.client.host}"


# ===== Validation Helper =====

def validate_client_credentials(client_id: str, client_secret: str) -> bool:
    """
    Validate client credentials.
    
    Args:
        client_id: Client identifier
        client_secret: Client secret
        
    Returns:
        True if credentials are valid
    """
    return client_id in CLIENTS_MAP and CLIENTS_MAP[client_id] == client_secret

