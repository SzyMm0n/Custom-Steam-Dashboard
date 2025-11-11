"""
Request signing utilities for Custom Steam Dashboard client.
Handles HMAC-SHA256 signature generation for authenticated requests.
"""
import os
import hmac
import hashlib
import time
import secrets
import base64
from typing import Dict, Optional


def get_client_credentials() -> tuple[str, str]:
    """
    Get client credentials from environment.
    
    Returns:
        Tuple of (client_id, client_secret)
    """
    client_id = os.getenv("CLIENT_ID", "desktop-main")
    client_secret = os.getenv("CLIENT_SECRET", "change-me-in-production")
    
    if client_secret == "change-me-in-production":
        print("WARNING: Using default CLIENT_SECRET. Set CLIENT_ID and CLIENT_SECRET environment variables!")
    
    return client_id, client_secret


def generate_nonce(length: int = 32) -> str:
    """
    Generate a random nonce for request signing.
    
    Args:
        length: Length of nonce in bytes (default: 32)
        
    Returns:
        Random nonce string (hex encoded)
    """
    return secrets.token_hex(length)


def compute_signature(
    client_secret: str,
    method: str,
    path: str,
    body: bytes,
    timestamp: str,
    nonce: str
) -> str:
    """
    Compute HMAC-SHA256 signature for request.
    
    Signature format: HMAC-SHA256(secret, "METHOD|PATH|SHA256(body)|timestamp|nonce")
    
    Args:
        client_secret: Client secret key
        method: HTTP method (GET, POST, etc.)
        path: Request path (e.g., "/api/games")
        body: Request body bytes (empty for GET requests)
        timestamp: Unix timestamp as string
        nonce: Random nonce string
        
    Returns:
        Base64-encoded signature
    """
    # Compute body hash
    body_hash = hashlib.sha256(body).hexdigest()
    
    # Create message to sign
    message = f"{method}|{path}|{body_hash}|{timestamp}|{nonce}"
    
    # Compute HMAC
    signature = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Encode as base64
    return base64.b64encode(signature).decode('utf-8')


def sign_request(
    method: str,
    path: str,
    body: Optional[bytes] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate signature headers for a request.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path (e.g., "/api/games")
        body: Request body bytes (None or empty for GET requests)
        client_id: Client ID (if None, gets from env)
        client_secret: Client secret (if None, gets from env)
        
    Returns:
        Dictionary of headers to add to request
    """
    # Get credentials if not provided
    if client_id is None or client_secret is None:
        client_id, client_secret = get_client_credentials()
    
    # Use empty body if None
    if body is None:
        body = b""
    
    # Generate timestamp and nonce
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    
    # Compute signature
    signature = compute_signature(
        client_secret=client_secret,
        method=method,
        path=path,
        body=body,
        timestamp=timestamp,
        nonce=nonce
    )
    
    # Return headers
    return {
        "X-Client-Id": client_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature
    }

