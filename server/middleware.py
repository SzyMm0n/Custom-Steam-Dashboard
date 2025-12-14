"""
Middleware for signature verification.
Verifies HMAC signatures on protected endpoints.
"""
import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from server.security import verify_request_signature

logger = logging.getLogger(__name__)


# Paths that require signature verification
PROTECTED_PATHS = [
    "/api/",  # All API endpoints
]

# Paths that are exempt from signature verification
EXEMPT_PATHS = [
    "/auth/",  # Auth endpoints handle their own verification
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
    "/health"
]


def should_verify_signature(path: str) -> bool:
    """
    Check if a path requires signature verification.

    Args:
        path: Request path

    Returns:
        True if signature verification is required, False otherwise
    """
    # Check exact matches for single paths
    if path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        return False

    # Check if path starts with exempt prefixes
    if path.startswith("/auth/"):
        return False

    # Check if path requires protection
    if path.startswith("/api/"):
        return True

    # All other paths don't require verification
    return False


class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify HMAC signatures on protected endpoints.

    Only verifies signatures for endpoints that require both JWT and HMAC.
    Skips verification for:
    - /auth/login (requires signature but handled in route)
    - /docs, /redoc, /openapi.json (only require JWT)
    - / and /health (public endpoints)
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and verify signature if needed.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler or error response
        """
        path = request.url.path

        # Skip signature verification for exempt paths or non-protected paths
        if not should_verify_signature(path):
            return await call_next(request)

        # Verify signature for protected paths
        try:
            # Extract signature headers
            x_client_id = request.headers.get("X-Client-Id")
            x_timestamp = request.headers.get("X-Timestamp")
            x_nonce = request.headers.get("X-Nonce")
            x_signature = request.headers.get("X-Signature")

            # Get request body (we need to cache it for later use)
            body = await request.body()

            # Store body in request state so it can be read again by the route handler
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

            # Verify signature
            verified_client_id = verify_request_signature(
                method=request.method,
                path=path,
                body=body,
                x_client_id=x_client_id,
                x_timestamp=x_timestamp,
                x_nonce=x_nonce,
                x_signature=x_signature
            )

            # Store verified client_id in request state for use in dependencies
            request.state.verified_client_id = verified_client_id

            # Continue to next handler
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Return proper HTTP error response
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers
            )
        except Exception as e:
            logger.error(f"Unexpected error in signature verification: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during signature verification"}
            )

