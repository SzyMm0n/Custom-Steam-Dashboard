"""
Authentication routes for Custom Steam Dashboard server.
Handles client login and JWT token issuance.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, Field

from security import create_jwt, verify_request_signature, CLIENTS_MAP, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    client_id: str = Field(..., min_length=1, max_length=100, description="Client identifier")


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request
):
    """
    Authenticate client and issue JWT token.
    
    This endpoint requires HMAC signature in headers:
    - X-Client-Id: Client identifier
    - X-Timestamp: Unix timestamp (must be within 60 seconds)
    - X-Nonce: Random nonce string (minimum 16 bytes, for anti-replay)
    - X-Signature: Base64-encoded HMAC-SHA256 signature
    
    Signature is computed as:
    HMAC-SHA256(client_secret, "METHOD|PATH|SHA256(body)|timestamp|nonce")
    
    Args:
        login_data: Login request with client_id
        request: FastAPI request object
        
    Returns:
        JWT access token with expiry information
        
    Raises:
        HTTPException: If client_id is invalid or signature verification fails
    """
    # Extract signature headers
    x_client_id = request.headers.get("X-Client-Id")
    x_timestamp = request.headers.get("X-Timestamp")
    x_nonce = request.headers.get("X-Nonce")
    x_signature = request.headers.get("X-Signature")
    
    # Get request body for signature verification
    body = await request.body()
    
    # Verify request signature (includes client_id validation)
    try:
        verified_client_id = verify_request_signature(
            method=request.method,
            path=request.url.path,
            body=body,
            x_client_id=x_client_id,
            x_timestamp=x_timestamp,
            x_nonce=x_nonce,
            x_signature=x_signature
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying request signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying request signature"
        )
    
    # Verify that client_id in body matches the one in signature headers
    if login_data.client_id != verified_client_id:
        logger.warning(f"Client ID mismatch: body={login_data.client_id}, header={verified_client_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID in body must match X-Client-Id header"
        )
    
    # Verify client exists in configuration
    if verified_client_id not in CLIENTS_MAP:
        logger.warning(f"Unknown client attempted login: {verified_client_id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid client credentials"
        )
    
    # Create JWT token
    token_data = create_jwt(verified_client_id)
    
    logger.info(f"Client logged in successfully: {verified_client_id[:8]}...")
    
    return LoginResponse(**token_data)


@router.get("/verify")
async def verify_token(payload: dict = Depends(require_auth)):
    """
    Verify that a JWT token is valid.
    
    This is a utility endpoint for clients to check if their token is still valid.
    Requires Authorization: Bearer <token> header.
    
    Returns:
        Token validity information
    """
    return {
        "valid": True,
        "client_id": payload.get("client_id"),
        "expires_at": payload.get("exp")
    }

