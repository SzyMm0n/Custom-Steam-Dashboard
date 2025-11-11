"""
Authenticated API client for Custom Steam Dashboard.
Handles JWT authentication and request signing with HMAC.
"""
import logging
import json
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import httpx

from .signing import sign_request, get_client_credentials

logger = logging.getLogger(__name__)


class AuthenticatedAPIClient:
    """
    API client with JWT authentication and HMAC request signing.
    
    Handles:
    - Initial login to obtain JWT token
    - Automatic JWT token refresh
    - HMAC signature on all requests
    - Token storage and management
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the authenticated API client.
        
        Args:
            base_url: Base URL of the server API
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None
        
        # Client credentials
        self._client_id, self._client_secret = get_client_credentials()
    
    # ===== Authentication =====
    
    async def login(self) -> bool:
        """
        Authenticate with the server and obtain JWT token.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Prepare login request
            path = "/auth/login"
            body_data = {"client_id": self._client_id}
            body_bytes = json.dumps(body_data).encode('utf-8')
            
            # Sign request
            signature_headers = sign_request(
                method="POST",
                path=path,
                body=body_bytes,
                client_id=self._client_id,
                client_secret=self._client_secret
            )
            
            # Add Content-Type header
            signature_headers["Content-Type"] = "application/json"

            # Make request - IMPORTANT: use content=body_bytes to send exact bytes used for signature
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    urljoin(self.base_url, path),
                    content=body_bytes,  # Send exact bytes we signed
                    headers=signature_headers
                )
                response.raise_for_status()
                
                # Store token
                data = response.json()
                self._access_token = data["access_token"]
                
                # Calculate expiry time (subtract 60s buffer)
                import time
                expires_in = data.get("expires_in", 1200)
                self._token_expires_at = int(time.time()) + expires_in - 60
                
                logger.info(f"Successfully authenticated with server (token expires in {expires_in}s)")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed with status {e.response.status_code}: {e.response.text}")
            return False
        except httpx.HTTPError as e:
            logger.error(f"Login failed with error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if client is currently authenticated.
        
        Returns:
            True if authenticated and token is not expired
        """
        if not self._access_token:
            return False
        
        if self._token_expires_at:
            import time
            return time.time() < self._token_expires_at
        
        return True
    
    async def ensure_authenticated(self):
        """
        Ensure client is authenticated, login if needed.
        
        Raises:
            Exception: If login fails
        """
        if not self.is_authenticated():
            logger.info("Token expired or not authenticated, logging in...")
            success = await self.login()
            if not success:
                raise Exception("Failed to authenticate with server")
    
    def _build_headers(self, method: str, path: str, body: Optional[bytes] = None) -> Dict[str, str]:
        """
        Build headers for authenticated request (JWT + HMAC signature).
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body bytes
            
        Returns:
            Dictionary of headers
        """
        # JWT Authorization header
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        
        # Add HMAC signature headers
        signature_headers = sign_request(
            method=method,
            path=path,
            body=body if body else b"",
            client_id=self._client_id,
            client_secret=self._client_secret
        )
        headers.update(signature_headers)
        
        return headers
    
    # ===== HTTP Methods =====
    
    async def get(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Make authenticated GET request.
        
        Args:
            path: Request path (e.g., "/api/games")
            
        Returns:
            Response JSON data or None on error
        """
        await self.ensure_authenticated()
        
        try:
            headers = self._build_headers("GET", path)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    urljoin(self.base_url, path),
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"GET {path} failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GET {path}: {e}")
            return None
    
    async def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make authenticated POST request.
        
        Args:
            path: Request path (e.g., "/api/games/tags/batch")
            data: Request body data (will be JSON encoded)
            
        Returns:
            Response JSON data or None on error
        """
        await self.ensure_authenticated()
        
        try:
            # Encode body
            body_bytes = json.dumps(data).encode('utf-8') if data else b""
            
            headers = self._build_headers("POST", path, body_bytes)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    urljoin(self.base_url, path),
                    content=body_bytes,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"POST {path} failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in POST {path}: {e}")
            return None


# Singleton instance
_api_client: Optional[AuthenticatedAPIClient] = None


def get_api_client(base_url: str = "http://localhost:8000") -> AuthenticatedAPIClient:
    """
    Get singleton API client instance.
    
    Args:
        base_url: Base URL of the server API
        
    Returns:
        AuthenticatedAPIClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = AuthenticatedAPIClient(base_url)
    return _api_client

